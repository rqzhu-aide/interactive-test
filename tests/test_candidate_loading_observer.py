"""Retained loading evidence and final review gates, without live model calls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import claude_transport as transport
import package_evidence as package
import session_driver as driver


class CandidateLoadingObservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.attempt = Path(temporary.name) / "private"
        self.work = Path(temporary.name) / "work"
        skill = self.work / ".claude/skills/causal-consultant/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes("Exact caf\u00e9 instructions.\r\n".encode("utf-8"))
        self.config = {"claude_command": ["claude"], "candidate_loading": "claude_explicit",
                       "max_agent_turns_per_call": 10, "mode": "verified_host", "limits": {}}
        self.state = {"work": str(self.work), "session_id": "test-session", "turns": 2,
                      "status": "awaiting_review", "active_seconds": 0, "started_at": None, "breaches": []}
        self.frozen = {"configuration": self.config, "candidate_files": {"SKILL.md": driver.digest(skill)},
                       "case_manifest": {"reviewer": "reviewer.json", "completion_contract": "focused"}}
        self.attempt.mkdir()
        driver.write(self.attempt / "freeze.json", self.frozen)
        driver.write(self.attempt / "state.json", self.state)
        (self.attempt / "host").mkdir()
        (self.attempt / "host/smoke.txt").write_text("Synthetic evidence, not a live host qualification.")
        (self.attempt / "case").mkdir()
        driver.write(self.attempt / "case/reviewer.json", {"criteria": [{"id": "science"}]})
        for turn in (1, 2):
            event = self.attempt / f"events/{turn:03d}"
            event.mkdir(parents=True)
            with patch.object(transport, "capture", side_effect=self.capture):
                transport.invoke(self.config, self.work, "test-session", turn == 1, "User request", 1, event / "transport")
            for name in ("public.json", "actor.json", "work-files.json", "project-binding.json"):
                driver.write(event / name, {})

    def capture(self, argv, cwd, message, timeout, output):
        output.mkdir()
        report = {"argv": argv, "cwd": str(cwd), "exit_code": 0, "error": None, "active_seconds": 0}
        driver.write(output / "command.json", report)
        driver.write(output / "process.json", report)
        (output / "request.txt").write_text(message, encoding="utf-8")
        (output / "stderr.txt").write_text("", encoding="utf-8")
        result = {"type": "result", "subtype": "success", "session_id": "test-session",
                  "is_error": False, "result": "Reply"}
        (output / "stdout.txt").write_text(json.dumps(result) + "\n", encoding="utf-8")
        return report

    def check(self, files=None, state=None):
        return package.candidate_loading_check(self.frozen, state or self.state,
            files or driver.evidence(self.attempt, self.state)["files"],
            lambda ref: (self.attempt / ref.removeprefix("private/")).read_bytes())

    def mutate(self, name, transform, turn=2):
        target = self.attempt / f"events/{turn:03d}/transport/{name}"
        value = driver.read(target)
        transform(value)
        if name == "stdout.txt":
            target.write_text(json.dumps(value) + "\n", encoding="utf-8")
        else:
            driver.write(target, value)

    def test_actual_transport_captures_match_fresh_and_resumed_binding(self):
        result = self.check()
        self.assertEqual(result["status"], "matched")
        self.assertEqual([call["event"] for call in result["calls"]], ["001", "002"])

    def test_missing_or_unindexed_receipt_is_unobserved_even_when_command_contains_prompt(self):
        ref = "private/events/002/transport/candidate-loading.json"
        files = driver.evidence(self.attempt, self.state)["files"]
        del files[ref]
        result = self.check(files)
        self.assertEqual(result["status"], "unobserved")
        self.assertIn("missing_indexed_capture", [item["reason"] for item in result["calls"][1]["issues"]])
        self.assertTrue((self.attempt / ref.removeprefix("private/")).is_file())

    def test_receipt_command_prompt_and_session_conflicts_survive_reindexing(self):
        mutations = [
            ("candidate-loading.json", lambda x: x.update(loading_id="0" * 64), "loading_identity_mismatch"),
            ("candidate-loading.json", lambda x: x.update(skill_sha256="0" * 64), "frozen_candidate_mismatch"),
            ("command.json", lambda x: x["argv"].__setitem__(-1, "Wrong supplied entry"), "prompt_argument_mismatch"),
            ("command.json", lambda x: x["argv"].__setitem__(x["argv"].index("--resume"), "--session-id"), "fresh_resume_identity_mismatch"),
            ("command.json", lambda x: x["argv"].remove("--disable-slash-commands"), "discovery_not_disabled"),
            ("transport.json", lambda x: x.update(session_id="different-session"), "session_identity_mismatch"),
            ("stdout.txt", lambda x: x.update(session_id="different-session"), "native_session_identity_mismatch"),
        ]
        for name, change, reason in mutations:
            with self.subTest(reason=reason):
                target = self.attempt / ("events/002/transport/" + name)
                original = target.read_bytes()
                self.mutate(name, change)
                result = self.check()
                self.assertEqual(result["status"], "conflict")
                self.assertIn(reason, [item["reason"] for item in result["calls"][1]["issues"]])
                target.write_bytes(original)

    def test_coherent_wrong_entry_still_conflicts_with_frozen_candidate(self):
        skill = self.work / ".claude/skills/causal-consultant/SKILL.md"
        skill.write_text("A different candidate", encoding="utf-8")
        prompt, receipt = transport.explicit_candidate(self.work)
        folder = self.attempt / "events/002/transport"
        (folder / "candidate-system-prompt.txt").write_bytes(prompt.encode("utf-8"))
        driver.write(folder / "candidate-loading.json", receipt)
        self.mutate("command.json", lambda x: x["argv"].__setitem__(-1, prompt))
        self.mutate("transport.json", lambda x: (x["argv"].__setitem__(-1, prompt), x.update(candidate_loading=receipt)))
        self.assertEqual(self.check()["status"], "conflict")

    def test_post_review_tampering_and_partial_native_capture_are_visible(self):
        files = driver.evidence(self.attempt, self.state)["files"]
        target = self.attempt / "events/002/transport/candidate-system-prompt.txt"
        target.write_bytes(target.read_bytes() + b" ")
        self.assertEqual(self.check(files)["status"], "conflict")
        target = self.attempt / "events/002/transport/stdout.txt"
        target.write_text("", encoding="utf-8")
        self.mutate("transport.json", lambda x: x.update(session_id=None))
        result = self.check()
        self.assertIn("missing_unique_native_result", [item["reason"] for item in result["calls"][1]["issues"]])

    def test_historical_mode_and_empty_or_malformed_turn_count(self):
        for turns in (0, None, "two"):
            result = package.candidate_loading_check(self.frozen, {**self.state, "turns": turns}, {}, lambda ref: b"")
            self.assertEqual(result["status"], "unobserved")
        for turns in (None, "two", -1, True):
            result = self.check(state={**self.state, "turns": turns})
            self.assertEqual(result["status"], "unobserved")
            self.assertIn("turn count", result["reason"])
            self.assertEqual(len(result["calls"]), 2)
            self.assertTrue(all(call["status"] == "matched" for call in result["calls"]))
        historical = copy.deepcopy(self.frozen)
        del historical["configuration"]["candidate_loading"]
        self.assertIsNone(package.candidate_loading_check(historical, self.state, {}, lambda ref: b""))

    def test_archived_posix_path_comparison_remains_case_sensitive(self):
        # Keep all receipt, prompt and argv evidence mutually consistent at /tmp/A;
        # state binds /tmp/a. No live filesystem access should be needed to reject it.
        blobs = {}
        for ref in driver.evidence(self.attempt, self.state)["files"]:
            if ref.startswith("private/events/") and "/transport/" in ref:
                blobs[ref] = (self.attempt / ref.removeprefix("private/")).read_bytes()
        old_base = str(self.work / ".claude/skills/causal-consultant")
        for turn in (1, 2):
            prefix = f"private/events/{turn:03d}/transport/"
            receipt = json.loads(blobs[prefix + "candidate-loading.json"])
            receipt.update(base_directory="/tmp/A/.claude/skills/causal-consultant",
                           skill_path="/tmp/A/.claude/skills/causal-consultant/SKILL.md")
            prompt = blobs[prefix + "candidate-system-prompt.txt"].decode().replace(old_base, receipt["base_directory"])
            receipt["system_prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
            receipt.pop("loading_id")
            receipt["loading_id"] = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
            blobs[prefix + "candidate-system-prompt.txt"] = prompt.encode()
            blobs[prefix + "candidate-loading.json"] = json.dumps(receipt).encode()
            for name in ("command.json", "transport.json"):
                record = json.loads(blobs[prefix + name])
                record["cwd"] = "/tmp/A"
                record["argv"][-1] = prompt
                if name == "transport.json":
                    record["candidate_loading"] = receipt
                blobs[prefix + name] = json.dumps(record).encode()
        files = {ref: hashlib.sha256(blob).hexdigest() for ref, blob in blobs.items()}
        matching = {**self.state, "work": "/tmp/A"}
        self.assertEqual(package.candidate_loading_check(self.frozen, matching, files, blobs.__getitem__)["status"], "matched")
        matching["work"] = "/tmp/a"
        self.assertEqual(package.candidate_loading_check(self.frozen, matching, files, blobs.__getitem__)["status"], "conflict")

    def finish(self, defect=None, include_native=True):
        if defect == "missing":
            (self.attempt / "events/002/transport/candidate-loading.json").unlink()
        elif defect == "conflict":
            self.mutate("command.json", lambda x: x["argv"].__setitem__(-1, "Different instructions"))
        elif defect == "diagnostic":
            self.frozen["configuration"]["mode"] = "diagnostic"
            driver.write(self.attempt / "freeze.json", self.frozen)
        loop = {"status": "no_structural_breach", "findings": [], "unobserved": [], "evidence_refs": []}
        with patch.object(driver, "consultation_loop_check", return_value=loop), patch.object(driver, "source_release_observations", return_value=[]):
            view = driver.inspect(self.attempt, "reviewer")
            refs = ["private/host/smoke.txt"]
            host = {key: {"verified": True, "reason": "Synthetic independent evidence review", "evidence_refs": refs.copy()}
                    for key in ("candidate_loading", "exact_resume", "private_isolation", "role_separation")}
            if include_native:
                host["candidate_loading"]["evidence_refs"] += ["private/events/001/transport/stdout.txt"]
            review = {"evidence_sha256": view["evidence_sha256"], "observations_sha256": view["observations_sha256"],
                      "test_validity": "valid", "test_validity_reason": "Synthetic test, not live qualification.",
                      "outcome": "objective_met", "stop_reason": "Synthetic endpoint", "reviewer": "test-double",
                      "coverage": {"science": {"status": "observed", "reason": "Synthetic coverage", "evidence_refs": refs}},
                      "findings": [], "host_checks": host,
                      "machine_finding_dispositions": {item["id"]: {"status": "false_positive", "reason": "Generic reviewer assertion",
                          "evidence_refs": refs} for item in view["observations"]["machine_findings"]}}
            return driver.finish(self.attempt, review)

    def test_matched_loading_still_requires_actual_native_evidence_in_host_review(self):
        with self.assertRaisesRegex(ValueError, "actual native evidence"):
            self.finish(include_native=False)
        self.assertEqual(self.finish()["quality_rating"], "pass")

    def test_false_positive_assertion_cannot_qualify_missing_loading(self):
        result = self.finish("missing", include_native=False)
        self.assertEqual(result["candidate_loading_check"]["status"], "unobserved")
        self.assertEqual(result["test_validity"], "unverified")
        self.assertEqual(result["quality_rating"], "inconclusive")

    def test_false_positive_assertion_cannot_qualify_conflicting_loading(self):
        result = self.finish("conflict", include_native=False)
        self.assertEqual(result["test_validity"], "invalid")
        self.assertEqual(result["quality_rating"], "inconclusive")

    def test_matched_loading_does_not_promote_diagnostic_mode(self):
        result = self.finish("diagnostic")
        self.assertEqual(result["candidate_loading_check"]["status"], "matched")
        self.assertEqual(result["test_validity"], "invalid")
        self.assertEqual(result["quality_rating"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
