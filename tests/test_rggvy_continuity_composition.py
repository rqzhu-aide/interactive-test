"""Check the named continuity composition without running a consultation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compose_case as composer
from session_driver import digest, inventory, read, validate_case

PROBLEM = "rggvy-electrification"
PERSONA = "rggvy-research-coordinator"


class RggvyContinuityComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="rggvy-continuity-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.bank = composer.RGGVY_ROOT / "problem"
        cls.original_bank = inventory(cls.bank)
        cls.default = cls.root / "default"
        cls.default_manifest = composer.compose_case(PROBLEM, output=cls.default)
        cls.case = cls.root / "coordinator"
        cls.manifest = composer.compose_case(PROBLEM, PERSONA, cls.case)

    def test_named_case_validates_and_preserves_all_scientific_source_bytes(self):
        self.assertEqual(validate_case(self.case), self.manifest)
        self.assertEqual(inventory(self.bank), self.original_bank)
        for name, sha in self.original_bank.items():
            with self.subTest(file=name):
                self.assertEqual(digest(self.case / name), sha)
        self.assertEqual(self.manifest["sources"], self.default_manifest["sources"])
        self.assertEqual(self.manifest["completion_contract"], "full_report")
        self.assertEqual(self.manifest["world_id"], self.default_manifest["world_id"])
        self.assertEqual(self.manifest["world_version"], self.default_manifest["world_version"])

    def test_manifest_selects_added_review_without_replacing_original(self):
        self.assertEqual(self.manifest["reviewer"], "continuity-reviewer.json")
        original = read(self.case / "reviewer.json")
        selected = read(self.case / self.manifest["reviewer"])
        self.assertEqual(selected["criteria"][:len(original["criteria"])], original["criteria"])
        self.assertEqual(selected["required_observations"][:len(original["required_observations"])],
                         original["required_observations"])
        self.assertEqual(len(selected["criteria"]), len(original["criteria"]) + 4)
        self.assertIn("continuity_coverage", selected)
        for name, value in original.items():
            if name not in ("criteria", "required_observations"):
                self.assertEqual(selected[name], value)

    def test_identity_and_private_resources_are_bound_without_actor_leakage(self):
        composition = read(self.case / "composition.json")
        self.assertEqual(self.manifest["case_id"], PROBLEM + "--" + PERSONA)
        self.assertEqual(self.manifest["variant_id"], "rggvy-continuity-coordinator")
        self.assertEqual(self.manifest["variant_version"], "1.1.0")
        self.assertEqual(self.manifest["case_version"], "1.1.0")
        self.assertEqual(self.manifest["persona_version"], "1.1.0")
        self.assertEqual(self.manifest["edition"], "case-specific-continuity-stress-v1")
        for identity in ("variant_id", "variant_version", "variant"):
            self.assertEqual(composition[identity], self.manifest[identity])
        self.assertEqual(composition["variant_sha256"], digest(composer.CONTINUITY_RESOURCE))
        self.assertEqual(composition["variant_sha256"], self.manifest["files"]["continuity-variant.json"])
        self.assertEqual(composition["persona_sha256"], digest(composer.RGGVY_ROOT / "persona.json"))
        self.assertEqual(composition["composer_sha256"], digest(ROOT / "scripts/compose_case.py"))
        self.assertEqual(composition["problem_sha256"], digest(self.bank / "problem.json"))
        actor = read(self.case / "actor.json")
        actor_text = json.dumps(actor)
        self.assertEqual(actor["persona_profile"], read(self.case / "persona.json"))
        self.assertEqual(actor["interaction_challenges"], [])
        self.assertEqual(actor["sources"], read(self.default / "actor.json")["sources"])
        self.assertEqual(actor["reply_limits"], {"max_words": 50, "max_items": 2})
        self.assertEqual(actor["consultant_reply_bounds"], {"minimum": 8, "maximum": 12})
        for private in ("target_turns", "default_max_consultant_turns", "continuity_coverage",
                        "reviewer_criteria", "c-coordinator-", "continuity-variant.json"):
            self.assertNotIn(private, actor_text)
        request = (self.case / self.manifest["initial_message"]).read_text(encoding="utf-8")
        self.assertLessEqual(len(request.split()), 50)
        self.assertIn("causal-consultant", request)
        self.assertIn("report", request)
        private_files = {"continuity-variant.json", "continuity-reviewer.json", "persona.json"}
        for source in self.manifest["sources"]:
            self.assertNotIn(source["destination"], private_files)
            self.assertNotIn(source["file"].removeprefix("public/"), private_files)

    def test_cap_override_and_seed_do_not_change_coordinator_interaction(self):
        self.assertEqual(self.manifest["run_limits"]["consultant_turns"], 12)
        self.assertEqual(self.manifest["minimum_consultant_replies"], 8)
        self.assertEqual(self.manifest["target_turns"], 10)
        self.assertIsNone(self.manifest["interaction_seed"])
        alternate = self.root / "alternate-cap-seed"
        manifest = composer.compose_case(PROBLEM, PERSONA, alternate,
                                         max_consultant_turns=12, interaction_seed=7)
        self.assertEqual(manifest["run_limits"]["consultant_turns"], 12)
        self.assertEqual(manifest["target_turns"], 10)
        self.assertIsNone(manifest["interaction_seed"])
        for name in ("actor.json", "composition.json", "public/initial-message.txt"):
            self.assertEqual((self.case / name).read_bytes(), (alternate / name).read_bytes())
        for cap in (7, 8, 11, 13, 23, True):
            with self.subTest(cap=cap):
                output = self.root / ("invalid-cap-" + str(cap))
                with self.assertRaisesRegex(ValueError, "fixed maximum of 12"):
                    composer.compose_case(PROBLEM, PERSONA, output, max_consultant_turns=cap)
                self.assertFalse(output.exists())

    def test_required_participation_overrides_generic_completion_and_pacing(self):
        actor = read(self.case / "actor.json")
        rules = {rule["rule_id"]: rule for rule in actor["rules"]}
        participation = rules["r-coordinator-participation"]["action"]
        for event in range(1, 9):
            self.assertIn(str(event) + ". ", participation)
        self.assertIn("f-rggvy-access", rules["r-coordinator-participation"]["fact_ids"])
        self.assertIn("without selecting computational work", participation)
        self.assertIn("do not preemptively recite their details", participation)
        self.assertIn("two substantive intervening", participation)
        self.assertIn("early report does not waive", rules["r-report"]["action"])
        self.assertIn("All eight ordered public events", rules["r-stop"]["condition"])
        self.assertIn("incomplete", rules["r-stop"]["action"])
        self.assertNotIn("No turn number", actor["pacing"])
        self.assertIn("Prioritize requested accessible records without delay", actor["pacing"])
        review = read(self.case / self.manifest["reviewer"])
        self.assertIn("Missing required events", review["continuity_coverage"]["interpretation"])
        self.assertIn("not a pass", review["continuity_coverage"]["interpretation"])
        self.assertNotIn("descriptive_target", review["continuity_coverage"])

    def test_legacy_variant_keeps_optional_minimum_and_overridable_cap(self):
        legacy = read(composer.CONTINUITY_RESOURCE)
        legacy["variant_version"] = "1.0.0"
        legacy["default_max_consultant_turns"] = 14
        legacy_file = self.root / "legacy-variant.json"
        legacy_file.write_text(json.dumps(legacy), encoding="utf-8")
        with patch.object(composer, "CONTINUITY_RESOURCE", legacy_file):
            manifest = composer.compose_case(PROBLEM, PERSONA, self.root / "legacy-default")
            overridden = composer.compose_case(PROBLEM, PERSONA, self.root / "legacy-override",
                                              max_consultant_turns=23)
        self.assertEqual(manifest["edition"], "case-specific-continuity-v1")
        self.assertNotIn("minimum_consultant_replies", manifest)
        self.assertEqual(manifest["run_limits"]["consultant_turns"], 14)
        self.assertEqual(overridden["run_limits"]["consultant_turns"], 23)
        self.assertNotIn("consultant_reply_bounds", read(self.root / "legacy-default/actor.json"))

    def test_other_problems_reject_named_persona_before_creating_output(self):
        for problem in composer.PROBLEM_IDS:
            if problem == PROBLEM:
                continue
            with self.subTest(problem=problem):
                output = self.root / ("invalid-" + problem)
                with self.assertRaisesRegex(ValueError, "supported only with rggvy-electrification"):
                    composer.compose_case(problem, PERSONA, output)
                self.assertFalse(output.exists())
        output = self.root / "invalid-cli"
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/compose_case.py"),
                                 "--problem", "study-design", "--persona", PERSONA,
                                 "--output", str(output)], capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("supported only with rggvy-electrification", result.stderr)
        self.assertFalse(output.exists())

    def test_catalog_separates_fixed_cases_from_reusable_personas(self):
        catalog = composer.catalog()
        self.assertEqual(catalog["combinations"], 17)
        self.assertEqual(catalog["matrix_combinations"], 12)
        self.assertEqual(catalog["standalone_count"], 5)
        personas = {item["id"]: item for item in catalog["personas"]}
        self.assertEqual(set(personas), set(composer.GENERAL_PERSONA_IDS))
        self.assertEqual(sum(len(item["supported_problems"]) for item in personas.values()), 12)
        self.assertNotIn(PROBLEM, {item["id"] for item in catalog["problems"]})
        standalone = {item["id"]: item for item in catalog["standalone_cases"]}
        self.assertEqual(standalone[PROBLEM]["fixed_actor"], PERSONA)
        self.assertEqual(self.default_manifest["persona_id"], PERSONA)
        self.assertEqual(self.default_manifest["run_limits"]["consultant_turns"], 12)
        self.assertEqual(self.default_manifest["reviewer"], "continuity-reviewer.json")
        for name in ("actor.json", "composition.json", "public/initial-message.txt"):
            self.assertEqual((self.default / name).read_bytes(), (self.case / name).read_bytes())

    def test_general_personas_rejected_for_rggvy_before_output_creation(self):
        for persona in composer.GENERAL_PERSONA_IDS:
            output = self.root / ("rejected-" + persona)
            with self.subTest(persona=persona), self.assertRaisesRegex(ValueError, "standalone and supports only"):
                composer.compose_case(PROBLEM, persona, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
