"""Exercise standalone selection, frozen disclosure contracts and input isolation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compose_case as composer
from session_driver import assess, digest, inventory, read, validate_case, write


class StandaloneCases(unittest.TestCase):
    def test_all_five_freeze_and_validate_without_a_persona_choice(self):
        with tempfile.TemporaryDirectory(prefix="standalone-cases-") as temporary:
            for identity in composer.STANDALONE_IDS:
                with self.subTest(case=identity):
                    output = Path(temporary) / identity
                    manifest = composer.standalone_case(identity, output)
                    self.assertEqual(validate_case(output), manifest)
                    actor = read(output / manifest["actor"])
                    if identity == composer.RGGVY_ID:
                        self.assertEqual(manifest["persona_id"], composer.COORDINATOR_PERSONA_ID)
                        self.assertEqual(manifest["minimum_consultant_replies"], 8)
                        self.assertEqual(manifest["completion_contract"], "full_report")
                    else:
                        self.assertEqual(inventory(output), inventory(ROOT / "standalone" / identity))
                        self.assertEqual(manifest["persona_id"], "single-question-planner")
                        self.assertEqual(manifest["completion_contract"], "focused")
                        self.assertEqual(manifest["reply_limits"], {"max_words": 50, "max_items": 1})
                        self.assertEqual(manifest["sources"], [])
                        self.assertNotIn("minimum_consultant_replies", manifest)
                        self.assertEqual(actor["reply_limits"], manifest["reply_limits"])

    def test_planning_fixture_rejects_missing_or_nonboolean_conditional_marker(self):
        with tempfile.TemporaryDirectory(prefix="planning-conditional-fixture-") as temporary:
            case = Path(temporary) / "forest"
            manifest = composer.standalone_case("forest-planning", case)
            original = read(case / manifest["reviewer"])
            for marker in (None, False, "true"):
                with self.subTest(marker=marker):
                    reviewer = copy.deepcopy(original)
                    criterion = next(c for c in reviewer["criteria"] if c["id"] == "j-staggered-comparison")
                    if marker is None:
                        criterion.pop("conditional")
                    else:
                        criterion["conditional"] = marker
                    write(case / manifest["reviewer"], reviewer)
                    manifest["files"][manifest["reviewer"]] = digest(case / manifest["reviewer"])
                    write(case / "case.json", manifest)
                    result = subprocess.run([sys.executable, "-B", str(case / manifest["oracle_check"])],
                                            capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Conditional criterion lacks its Boolean declaration", result.stderr)

    def test_generated_conditional_coverage_reaches_actual_assessment(self):
        # Synthetic evidence exercises finalization semantics, not consultant or
        # host quality. Use actual shipped declarations, not copied criteria.
        untriggered = {
            "masks-planning": {"m-comparison": "The accepted endpoint is checking available illness records; no comparison analysis was selected."},
            "forest-planning": {
                "j-staggered-comparison": "Only an inventory check was chosen; staggered analysis was not proposed or selected.",
                "j-household-path": "A household-effect route was not proposed or selected."},
            "medication-planning": {"j-questionnaire-route": "The accepted plan uses existing records and does not propose questionnaire collection."},
            "surgery-planning": {
                "followup-and-selection": "This narrow allocation-scoping endpoint has not reached follow-up, linkage or cohort-selection claims.",
                "appropriate-analysis-and-uncertainty": "No analysis has been proposed at this allocation-scoping endpoint."},
        }
        public, host = "private/events/001/public.json", "private/host/synthetic.json"
        index = {"sha256": "synthetic-index", "files": {public: "synthetic", host: "synthetic"}}
        state = {"status": "awaiting_review", "turns": 3, "active_seconds": 0,
                 "started_at": 1, "ended_at": 2, "breaches": []}
        for identity, reasons in untriggered.items():
            with self.subTest(case=identity):
                case = ROOT / "standalone" / identity
                reviewer = read(case / "reviewer.json")
                self.assertEqual({c["id"] for c in reviewer["criteria"] if c.get("conditional") is True}, set(reasons))
                frozen = {"case_manifest": read(case / "case.json"), "reviewer_packet": reviewer,
                          "configuration": {"mode": "verified_host", "limits": {"consultant_turns": 12}}}
                review = {"evidence_sha256": index["sha256"], "test_validity": "valid",
                          "test_validity_reason": "Synthetic unit fixture; not a live host qualification.",
                          "outcome": "useful_stop", "useful_stop_basis": "The synthetic user accepts a narrower preparation endpoint.",
                          "stop_reason": "Synthetic accepted planning endpoint.", "reviewer": "unit-test",
                          "coverage": {c["id"]: {"status": "observed", "reason": "Synthetic bound evidence supplies this judgment.",
                                                   "evidence_refs": [public]} for c in reviewer["criteria"]}, "findings": [],
                          "host_checks": {key: {"verified": True, "reason": "Synthetic host evidence for the unit fixture only.",
                                                "evidence_refs": [host]}
                                          for key in ("candidate_loading", "exact_resume", "private_isolation", "role_separation")}}
                for criterion, reason in reasons.items():
                    review["coverage"][criterion] = {"status": "not_applicable", "reason": reason, "evidence_refs": [public]}
                result = assess(review, state, frozen, index)
                self.assertEqual(result["quality_rating"], "pass")
                self.assertEqual(result["coverage"], review["coverage"])

                waived = copy.deepcopy(review)
                waived["coverage"]["planning-usefulness"]["status"] = "not_applicable"
                with self.assertRaisesRegex(ValueError, "unconditional criterion cannot be waived"):
                    assess(waived, state, frozen, index)
                missing = copy.deepcopy(review)
                missing["coverage"]["planning-usefulness"] = {"status": "unobserved", "reason": "Final planning advice is missing from this synthetic evidence."}
                result = assess(missing, state, frozen, index)
                self.assertEqual(result["quality_rating"], "inconclusive")
                self.assertEqual(result["coverage"]["planning-usefulness"]["status"], "unobserved")

                if identity == "forest-planning":
                    triggered = copy.deepcopy(review)
                    triggered["coverage"]["j-staggered-comparison"] = {
                        "status": "observed", "reason": "A staggered comparison was proposed without addressing disclosed concurrent rollout differences.",
                        "evidence_refs": [public]}
                    triggered["findings"] = [{"owner": "consultant", "severity": "material", "criterion": "j-staggered-comparison",
                                              "description": "Synthetic proposed analysis omits a consequential concurrent-change explanation.",
                                              "consequence": "Its causal conclusion is unsupported.", "evidence_refs": [public]}]
                    result = assess(triggered, state, frozen, index)
                    self.assertEqual(result["quality_rating"], "fail")
                    self.assertEqual(result["coverage"]["j-staggered-comparison"]["status"], "observed")
                    self.assertEqual(result["findings"], triggered["findings"])

    def test_frozen_cases_reject_changed_cap_and_existing_output(self):
        with tempfile.TemporaryDirectory(prefix="standalone-reject-") as temporary:
            root = Path(temporary)
            for identity in composer.STANDALONE_IDS:
                for cap in (11, True):
                    output = root / (identity + str(cap))
                    with self.subTest(case=identity, cap=cap), self.assertRaises(ValueError):
                        composer.standalone_case(identity, output, cap)
                    self.assertFalse(output.exists())
            output = root / "already-there"
            output.mkdir()
            (output / "retain.txt").write_text("retain", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                composer.standalone_case("masks-planning", output)
            self.assertEqual((output / "retain.txt").read_text(), "retain")

    def test_output_cannot_modify_any_canonical_bank(self):
        for output in (ROOT / "standalone/forest-planning/unexpected-case",
                       ROOT / "problems/study-design/unexpected-case",
                       ROOT / "personas/unexpected-case"):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "overlaps definition bank"):
                    composer.standalone_case("masks-planning", output)
                with self.assertRaisesRegex(ValueError, "overlaps definition bank"):
                    composer.compose_case("observational-did", output=output)
                self.assertFalse(output.exists())

    def test_cli_selectors_and_forbidden_persona_overlays(self):
        script = ROOT / "scripts/compose_case.py"
        with tempfile.TemporaryDirectory(prefix="standalone-cli-") as temporary:
            root = Path(temporary)
            for identity in composer.STANDALONE_IDS:
                output = root / identity
                result = subprocess.run([sys.executable, "-B", str(script), "--standalone", identity,
                                         "--output", str(output)], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["case_id"], read(output / "case.json")["case_id"])
                for persona in (*composer.GENERAL_PERSONA_IDS, composer.COORDINATOR_PERSONA_ID):
                    rejected = root / (identity + "-" + persona)
                    result = subprocess.run([sys.executable, "-B", str(script), "--standalone", identity,
                                             "--persona", persona, "--output", str(rejected)],
                                            capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("fixed actor", result.stderr)
                    self.assertFalse(rejected.exists())
            for persona in composer.GENERAL_PERSONA_IDS:
                output = root / ("legacy-general-" + persona)
                result = subprocess.run([sys.executable, "-B", str(script), "--problem", composer.RGGVY_ID,
                                         "--persona", persona, "--output", str(output)],
                                        capture_output=True, text=True, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("standalone and supports only", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
