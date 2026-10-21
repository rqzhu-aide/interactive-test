"""Check the real-source case and evidence boundaries, not live actor quality."""
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compose_case as composer
from session_driver import digest, inventory, read, validate_case
from source_release import source_release_observations, validate_release_receipts

PROBLEM = "rggvy-electrification"
PERSONAS = (composer.COORDINATOR_PERSONA_ID,)
DATA_MEMBERS = {"villages.dta", "households.tsv", "village_variables.csv",
                "household_variables.csv"}


def csv_rows(data, delimiter=","):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=delimiter))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class RggvyCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="rggvy-case-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.cases = {}
        for persona in PERSONAS:
            directory = cls.root / persona
            cls.cases[persona] = (directory, composer.compose_case(PROBLEM, persona, directory))
        cls.case, cls.manifest = cls.cases[composer.COORDINATOR_PERSONA_ID]
        cls.definition = read(cls.case / "problem.json")
        cls.sources = {source["id"]: source for source in cls.manifest["sources"]}
        cls.archive = cls.case / cls.sources["s-data"]["file"]
        with zipfile.ZipFile(cls.archive) as archive:
            cls.households = csv_rows(archive.read("households.tsv"), "\t")
            cls.village_dictionary = csv_rows(archive.read("village_variables.csv"))
            cls.household_dictionary = csv_rows(archive.read("household_variables.csv"))

    def test_fixed_coordinator_validates_and_preserves_scientific_evidence(self):
        self.assertEqual(len(self.cases), 1)
        baseline = self.manifest
        scientific = {name: sha for name, sha in baseline["files"].items()
                      if name in {"world.json", "oracle.json", "check_oracle.py", "problem.json", "reviewer.json"}
                      or name.startswith("public/") and name != baseline["initial_message"]}
        for persona, (directory, manifest) in self.cases.items():
            with self.subTest(persona=persona):
                self.assertEqual(validate_case(directory), manifest)
                self.assertEqual(manifest["suite_version"], "8.2.0")
                self.assertEqual(manifest["problem_version"], "1.2.0")
                self.assertEqual(manifest["completion_contract"], "full_report")
                self.assertEqual(manifest["sources"], baseline["sources"])
                self.assertEqual({name: manifest["files"][name] for name in scientific}, scientific)
                self.assertEqual(manifest["world_id"], baseline["world_id"])
                actor = read(directory / manifest["actor"])
                self.assertEqual(actor["persona_profile"], read(composer.RGGVY_ROOT / "persona.json"))
                self.assertEqual(actor["reply_limits"], {"max_words": 50, "max_items": 2})
                self.assertEqual(actor["goal"], self.definition["goal"])
                self.assertNotIn("target_turns", actor)
                self.assertFalse({"world", "oracle", "reviewer", "scientific_truth"} & actor.keys())
                request = (directory / manifest["initial_message"]).read_text(encoding="utf-8")
                self.assertLessEqual(len(request.split()), 50)
                self.assertIn("causal-consultant", request)
                self.assertIn("report", request.lower())
                self.assertIn("c-report", {criterion["id"] for criterion in read(directory / manifest["reviewer"])["criteria"]})

    def test_initial_archive_contains_only_authentic_data_and_original_labels(self):
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(set(archive.namelist()), DATA_MEMBERS)
            self.assertEqual(len(archive.namelist()), len(DATA_MEMBERS))
            self.assertIsNone(archive.testzip())
            with archive.open("villages.dta") as stream:
                header = stream.read(109)
                self.assertEqual(header[:4], bytes([115, 2, 1, 0]))
                columns, rows = struct.unpack("<Hi", header[4:10])
                self.assertEqual((rows, columns), (19353, 943))
                stream.read(columns)  # One storage-type byte per original variable.
                names = [stream.read(33).split(b"\0", 1)[0].decode("latin-1")
                         for _ in range(columns)]
        self.assertEqual(names, [row["variable"] for row in self.village_dictionary])
        self.assertEqual(list(self.households[0]), [row["variable"] for row in self.household_dictionary])
        self.assertEqual(len(self.households[0]), 61)
        # The exact member allowlist excludes the annotated subset README,
        # profile, oracle, design note, and evaluator documents from the upload.

    def test_documentation_is_obtainable_without_an_analysis_commitment_gate(self):
        initial = {key for key, source in self.sources.items() if source["availability"] == "initial"}
        self.assertEqual(initial, {"s-data"})
        documents = {"s-paper", "s-appendix", "s-merge-code", "s-analysis-code",
                     "s-output-code", "s-master-code", "s-decision"}
        self.assertTrue(documents <= set(self.sources))
        for key in documents:
            with self.subTest(source=key):
                self.assertEqual(self.sources[key]["availability"], "on_request")
                self.assertNotIn("release_prerequisite", self.sources[key])
        # Ordinary source requests must not acquire the policy-holdout gate.
        self.assertEqual(validate_release_receipts(self.root, {"turns": 1}, self.sources,
                                                  sorted(documents), []), [])
        for persona, (directory, manifest) in self.cases.items():
            actor = read(directory / manifest["actor"])
            source_map = {item["source_id"]: item for item in actor["sources"]}
            self.assertEqual(set(source_map), set(self.sources))
            for key in documents:
                self.assertTrue(source_map[key]["release"].strip())
                self.assertEqual(source_map[key]["file"], self.sources[key]["destination"])
            rules = {rule["rule_id"]: rule for rule in actor["rules"]}
            self.assertTrue(documents <= set(rules["r-rggvy-source-disclosure"]["source_ids"]))

    def test_actor_starts_with_client_preferences_and_access_not_collection_answers(self):
        expected = {"f-rggvy-goal", "f-rggvy-access", "f-rggvy-decision",
                    "f-rggvy-model-preference", "f-rggvy-claim-preference", "f-rggvy-report"}
        self.assertEqual({fact["fact_id"] for fact in self.definition["actor_facts"]}, expected)
        self.assertTrue(all(fact["knowledge_tier"] == "practical"
                            for fact in self.definition["actor_facts"]))
        for persona, (directory, manifest) in self.cases.items():
            with self.subTest(persona=persona):
                actor = read(directory / manifest["actor"])
                actor_expected = expected | {"f-coordinator-briefing", "f-coordinator-audience"}
                self.assertEqual({fact["fact_id"] for fact in actor["facts"]}, actor_expected)
                # Private data-handling findings must be learned from released
                # records. Every persona gets the same accessible original sources.
                facts = json.dumps(actor["facts"])
                for private_key in ("duplicate_source_id_rows", "stdt_cluster_groups",
                                    "legacy_rf_sample_150", "main_tables_unrestricted",
                                    "oracle.json", "profile.json", "SOURCE-AUDIT.md"):
                    self.assertNotIn(private_key, facts)
                rules = {rule["rule_id"]: rule for rule in actor["rules"]}
                self.assertTrue({"r-rggvy-source-disclosure", "r-rggvy-scope"} <= set(rules))
                self.assertFalse({"r-rggvy-agenda", "r-rggvy-method-choice",
                                  "r-rggvy-pressure-certainty", "r-rggvy-pressure-transfer",
                                  "r-rggvy-truth", "r-rggvy-report-selection", "r-rggvy-finish"}
                                 & set(rules))
                for rule in rules.values():
                    self.assertTrue(set(rule["fact_ids"]) <= actor_expected)
                    self.assertTrue(set(rule["source_ids"]) <= set(self.sources))
                for update in ("knowledge_updates", "belief_updates", "decision_updates"):
                    self.assertIn(update, actor["reply_record"]["optional"])
                # The rule bodies and actual trigger/retirement behavior require
                # semantic review; passing this test does not qualify an LLM actor.

    def test_oracle_checks_real_data_and_sample_semantics_without_causal_ground_truth(self):
        oracle = read(self.case / "oracle.json")
        self.assertIs(oracle["specification"]["known_causal_truth"], False)
        namespace = runpy.run_path(str(self.case / "check_oracle.py"))
        actual = namespace["check_data"](self.case)
        self.assertEqual(actual, oracle["expected"])
        village = actual["villages"]
        self.assertEqual((village["rows"], village["columns"]), (19353, 943))
        self.assertEqual(village["legacy_rf_sample_150"],
                         {"rows": 414, "below": 187, "at": 0, "above": 227,
                          "population_mismatch": 50, "population_mismatch_unknown": 0,
                          "after_excluding_flagged_mismatches": 364})
        self.assertEqual((village["cutoff_300_rows"], village["cutoff_300_instrument_one"]), (8, 8))
        self.assertIs(village["has_shrug_consumption"], False)
        self.assertNotIn("secc11_rural_cons_pc", {row["variable"] for row in self.village_dictionary})
        self.assertNotIn("pca01_id", self.households[0])
        household = actual["households"]
        self.assertEqual((household["unique_nss_hh_id"], household["duplicate_source_id_rows"]), (5113, 2400))
        self.assertEqual((household["stdt_cluster_groups"], household["sample_1011_groups"]), (6, 5))
        self.assertEqual(actual["source_semantics"], {
            "main_tables_unrestricted": {"3": True, "5": True, "7": True},
            "table_B9_uses_sample_1011": True, "known_causal_truth": False})

    def test_household_duplicates_are_historical_copies_not_a_three_wave_panel(self):
        rows = self.households
        self.assertEqual(len(rows), 7513)
        self.assertEqual(Counter(row["year"] for row in rows), {"2000": 4020, "2005": 1997, "2010": 1496})
        by_id = defaultdict(list)
        for row in rows:
            by_id[row["nss_hh_id"]].append(row)
        self.assertEqual(len(by_id), 5113)
        copied = [group for group in by_id.values() if len(group) > 1]
        self.assertTrue(copied)
        self.assertEqual(sum(len(group) - 1 for group in copied), 2400)
        self.assertTrue(all({row["year"] for row in group} == {"2000"} for group in copied))
        self.assertEqual(len({row["nss_hh_id"] for row in rows if row["year"] == "2000"}), 1620)
        self.assertTrue(all(row["frame_population"] == "" for row in rows if row["year"] == "2000"))

    def test_main_and_sensitivity_samples_have_distinct_dependence_and_treatment(self):
        rows = self.households
        self.assertEqual(len({row["district"] for row in rows}), 16)
        self.assertEqual(len({row["stdt_cluster"] for row in rows}), 6)
        restricted = [row for row in rows if row["sample_1011"] == "1"]
        self.assertEqual(len(restricted), 6101)
        self.assertEqual(len({row["stdt_cluster"] for row in restricted}), 5)
        treated = {row["district"] for row in rows
                   if row["year"] == "2010" and row["treat_x_post"] == "1"}
        sensitivity_treated = {row["district"] for row in restricted
                               if row["year"] == "2010" and row["treat_x_post"] == "1"}
        self.assertEqual(treated, {"JANJGIR - CHAMPA", "KAWARDHA", "DURG"})
        self.assertEqual(sensitivity_treated, {"JANJGIR - CHAMPA"})

    def test_household_population_is_district_scale_and_weights_have_fixed_group_mass(self):
        self.assertEqual(min(float(row["tot_p01"]) for row in self.households), 377171)
        self.assertEqual(max(float(row["tot_p01"]) for row in self.households), 1894355)
        groups = defaultdict(list)
        for row in self.households:
            groups[row["district"], row["year"]].append(float(row["weight_normalized"]))
        self.assertEqual(len(groups), 48)
        for key, weights in groups.items():
            with self.subTest(group=key):
                self.assertTrue(all(weight > 0 for weight in weights))
                self.assertAlmostEqual(sum(weights), 1e6, delta=0.1)

    def test_initial_archive_extraction_does_not_hide_an_unreleased_document(self):
        # Replay only source-observer evidence, without a model or live session.
        with tempfile.TemporaryDirectory(prefix="rggvy-release-") as temporary:
            attempt = Path(temporary)
            snapshot = attempt / "events/001/work-snapshot"
            snapshot.mkdir(parents=True)
            with zipfile.ZipFile(self.archive) as archive:
                member_bytes = archive.read("households.tsv")
            (snapshot / "households.tsv").write_bytes(member_bytes)
            save(attempt / "events/001/work-files.json", {"households.tsv": digest(snapshot / "households.tsv")})
            save(attempt / "events/001/releases.json", {})

            def index():
                return {"files": {"private/" + name: sha for name, sha in inventory(attempt).items()}}

            frozen = {"case_manifest": self.manifest}
            self.assertEqual(source_release_observations(attempt, frozen, index()), [])
            # An actual on-request source copied before release remains visible.
            paper = self.sources["s-paper"]
            saved = attempt / "case" / paper["file"]
            saved.parent.mkdir(parents=True)
            shutil.copyfile(self.case / paper["file"], saved)
            shutil.copyfile(saved, snapshot / "reading.pdf")
            save(attempt / "events/001/work-files.json", {
                "households.tsv": digest(snapshot / "households.tsv"),
                "reading.pdf": digest(snapshot / "reading.pdf")})
            findings = source_release_observations(attempt, frozen, index())
            self.assertEqual([(item["source_id"], item["status"]) for item in findings],
                             [("s-paper", "acquisition_unverified")])

    def test_postcomposition_data_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="rggvy-tamper-") as temporary:
            copied = Path(temporary) / "case"
            shutil.copytree(self.case, copied)
            with (copied / self.sources["s-data"]["file"]).open("ab") as stream:
                stream.write(b"changed after freeze")
            with self.assertRaisesRegex(ValueError, "case file identity mismatch"):
                validate_case(copied)

    def test_an_incorrect_reference_cannot_pass_by_refreshing_its_checksum(self):
        with tempfile.TemporaryDirectory(prefix="rggvy-reference-") as temporary:
            copied = Path(temporary) / "case"
            shutil.copytree(self.case, copied)
            oracle = read(copied / "oracle.json")
            oracle["expected"]["households"]["stdt_cluster_groups"] = 7
            save(copied / "oracle.json", oracle)
            problem = read(copied / "problem.json")
            problem["files"]["oracle.json"] = digest(copied / "oracle.json")
            save(copied / "problem.json", problem)
            result = subprocess.run([sys.executable, "-B", str(copied / "check_oracle.py")],
                                    cwd=copied, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("data handling or source metadata differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
