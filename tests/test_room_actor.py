"""Unit tests for the CLI actor driver (scripts/room_actor.py).

Covers JSON extraction from raw model output, the actor contract text, and
required-field validation. No live CLI is invoked; run_runtime subprocess
behavior is not covered here.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import room_actor
import room_reviewer


class ExtractJsonTests(unittest.TestCase):
    def test_bare_object(self):
        self.assertEqual(room_actor.extract_json('{"stop": false}'), {"stop": False})

    def test_fenced_object_with_prose_around(self):
        raw = 'Here you go:\n```json\n{"message": "hi", "stop": true}\n```\nThanks.'
        self.assertEqual(room_actor.extract_json(raw), {"message": "hi", "stop": True})

    def test_object_with_trailing_prose(self):
        raw = '{"message": "hi"}\nThat is my reply.'
        self.assertEqual(room_actor.extract_json(raw), {"message": "hi"})

    def test_nested_braces_inside_strings(self):
        raw = '{"message": "curly } braces { inside", "stop": false}'
        self.assertEqual(room_actor.extract_json(raw)["message"], "curly } braces { inside")

    def test_escaped_quotes_inside_strings(self):
        raw = '{"message": "she said \\"hi\\" }", "stop": false}'
        self.assertEqual(room_actor.extract_json(raw)["message"], 'she said "hi" }')

    def test_no_json_raises(self):
        with self.assertRaises(ValueError):
            room_actor.extract_json("no object here")

    def test_unbalanced_json_raises(self):
        with self.assertRaises(ValueError):
            room_actor.extract_json('{"message": "open')


class ContractTests(unittest.TestCase):
    def test_contract_carries_bundle_markers_and_placeholder(self):
        self.assertIn("<<BUNDLE>>", room_actor.CONTRACT)
        self.assertIn("<<END BUNDLE>>", room_actor.CONTRACT)
        self.assertIn("{bundle}", room_actor.CONTRACT)

    def test_contract_does_not_hardcode_a_persona(self):
        # Persona-specific rules (word caps, item caps) must come from the
        # bundle's frozen persona packet, not from this contract.
        self.assertNotIn("novice", room_actor.CONTRACT.lower())
        self.assertIn("packet wins", room_actor.CONTRACT)

    def test_contract_keeps_mechanical_stop_and_quote_rules(self):
        self.assertIn("`message` to null", room_actor.CONTRACT)
        self.assertIn("`message_quote` must be an exact substring of your own new `message`", room_actor.CONTRACT)
        self.assertIn("`option_quote` must be an exact substring of the earlier consultant message named by `public_turn`", room_actor.CONTRACT)
        self.assertIn("copy its characters exactly from the bundle", room_actor.CONTRACT)
        self.assertIn("Never leak fact IDs", room_actor.CONTRACT)

    def test_required_fields_match_contract(self):
        for field in ("message", "fact_ids", "rule_ids", "attachments",
                      "unanswered_questions", "fixture_gaps", "stop"):
            self.assertIn(field, room_actor.REQUIRED)


class ValidationTests(unittest.TestCase):
    def test_missing_required_fields_detected(self):
        reply = {"message": "hi", "fact_ids": [], "rule_ids": [], "attachments": [],
                 "unanswered_questions": [], "fixture_gaps": []}  # stop missing
        missing = [key for key in room_actor.REQUIRED if key not in reply]
        self.assertEqual(missing, ["stop"])

    def test_instruction_points_at_prompt_file(self):
        self.assertIn("prompt.txt", room_actor.INSTRUCTION)
        self.assertIn("JSON object", room_actor.INSTRUCTION)

    def test_word_limit_is_checked_before_actor_reply_is_written(self):
        bundle = {"actor_packet": {"reply_limits": {"max_words": 50, "max_items": 2}}}
        with self.assertRaisesRegex(ValueError, "word limit"):
            room_actor.check_reply_limits({"message": "word " * 51, "stop": False}, bundle)
        room_actor.check_reply_limits({"message": "word " * 50, "stop": False}, bundle)


class ActorArgvTests(unittest.TestCase):
    """Actor agents must run with skills mechanically disabled on every runtime;
    the actor's only world is the bundle protocol in prompt.txt."""

    def setUp(self):
        self.resolve = patch.object(room_actor, "resolve", lambda binary: ["X-" + binary])
        self.resolve.start()
        self.addCleanup(self.resolve.stop)
        self.cwd = Path("actor-cwd")

    def test_claude_actor_disables_skills(self):
        argv = room_actor.actor_argv("claude", None, self.cwd)
        self.assertEqual(argv[0], "X-claude")
        self.assertIn("--disable-slash-commands", argv)
        self.assertIn(room_actor.INSTRUCTION, argv)
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read")

    def test_kimi_actor_points_skills_dir_at_empty_dir(self):
        argv = room_actor.actor_argv("kimi", "kimi-k3-256k", self.cwd)
        self.assertEqual(argv[0], "X-kimi")
        self.assertIn("--skills-dir", argv)
        self.assertEqual(argv[argv.index("--skills-dir") + 1], str(self.cwd / "no-skills"))
        self.assertIn(room_actor.INSTRUCTION, argv)
        self.assertEqual(argv[argv.index("-m") + 1], "kimi-k3-256k")

    def test_pi_actor_disables_skills(self):
        argv = room_actor.actor_argv("pi", None, self.cwd)
        self.assertEqual(argv[0], "X-pi")
        self.assertIn("--no-skills", argv)
        self.assertIn("--no-session", argv)
        self.assertEqual(argv[-1], room_actor.INSTRUCTION)

    def test_unknown_runtime_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown runtime"):
            room_actor.actor_argv("gemini", None, self.cwd)


class ReviewerArgvTests(unittest.TestCase):
    """CLI reviewers are fresh processes with read+code tools and no skills."""

    def setUp(self):
        self.resolve = patch.object(room_reviewer, "resolve", lambda binary: ["X-" + binary])
        self.resolve.start()
        self.addCleanup(self.resolve.stop)
        self.cwd = Path("reviewer-cwd")

    def test_pi_reviewer_argv(self):
        argv = room_reviewer.reviewer_argv("pi", "zai/glm-5.3-flash", self.cwd)
        self.assertEqual(argv[0], "X-pi")
        self.assertIn("--no-skills", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "read,bash")
        self.assertEqual(argv[argv.index("--model") + 1], "zai/glm-5.3-flash")
        self.assertEqual(argv[-1], room_reviewer.INSTRUCTION)

    def test_claude_reviewer_argv(self):
        argv = room_reviewer.reviewer_argv("claude", "claude-opus-4-8", self.cwd)
        self.assertEqual(argv[0], "X-claude")
        self.assertIn("--disable-slash-commands", argv)
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,Bash")
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-4-8")

    def test_unknown_runtime_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown runtime"):
            room_reviewer.reviewer_argv("gemini", None, self.cwd)

    def test_contract_binds_ground_truth_and_digests(self):
        for fragment in ("{reviewer_packet}", "world.json", "oracle.json", "check_oracle.py",
                         "review-index.json", "evidence_sha256", "test_validity_reason",
                         "machine_finding_dispositions"):
            self.assertIn(fragment, room_reviewer.CONTRACT)
        self.assertEqual(room_reviewer.REQUIRED[0], "evidence_sha256")

    def test_reviewer_schema_accepts_evidenced_host_checks_without_inventing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "case"
            case.mkdir()
            packet = case / "reviewer.json"
            packet.write_text('{"criteria": [{"id": "c-original"}]}', encoding="utf-8")
            (case / "case.json").write_text(json.dumps({"reviewer": packet.name,
                "files": {packet.name: room_reviewer.digest(packet)}}), encoding="utf-8")
            review = {key: None for key in room_reviewer.REQUIRED}
            review.update(test_validity="valid", findings=[], host_checks={"candidate_loading": {
                "verified": True, "reason": "Actual helper path is bound to the staged candidate.",
                "evidence_refs": ["private/host/smoke.txt", "private/events/001/transport/stdout.txt"]}})
            argv = ["room_reviewer.py", "--attempt", str(root / "attempt"), "--case", str(root / "case"),
                    "--evaluation-md", str(root / "evaluation.md"), "--runtime", "claude",
                    "--reviewer", "test-reviewer", "--context-id", "test-context", "--out", str(root / "review.json"),
                    "--cwd", str(root / "scratch")]
            for has_checks in (True, False):
                if not has_checks:
                    del review["host_checks"]
                    review["test_validity"] = "unverified"
                with patch.object(sys, "argv", argv), patch.object(room_reviewer, "run_runtime", return_value=json.dumps(review)), patch("builtins.print"):
                    room_reviewer.main()
                saved = json.loads((root / "review.json").read_text(encoding="utf-8"))
                self.assertEqual(saved.get("host_checks"), review.get("host_checks"))
            prompt = (root / "scratch/prompt.txt").read_text(encoding="utf-8")
            self.assertIn("Also include host_checks", prompt)
            self.assertIn("when claiming valid for verified_host", prompt)
            self.assertIn("never a boilerplate", prompt)
            self.assertIn("Inspect actual native tool", prompt)

    def test_reviewer_prompt_uses_manifest_selected_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "case"
            case.mkdir()
            original = case / "reviewer.json"
            continuity = case / "continuity-reviewer.json"
            original.write_text('{"criteria": [{"id": "c-original"}]}', encoding="utf-8")
            continuity.write_text('{"criteria": [{"id": "c-original"}, {"id": "c-continuity"}]}',
                                  encoding="utf-8")
            review = {key: None for key in room_reviewer.REQUIRED}
            review.update(findings=[])
            argv = ["room_reviewer.py", "--attempt", str(root / "attempt"), "--case", str(case),
                    "--evaluation-md", str(root / "evaluation.md"), "--runtime", "claude",
                    "--reviewer", "test-reviewer", "--context-id", "test-context",
                    "--out", str(root / "review.json"), "--cwd", str(root / "scratch")]
            files = {packet.name: room_reviewer.digest(packet) for packet in (original, continuity)}
            for selected in (original, continuity):
                with self.subTest(packet=selected.name):
                    (case / "case.json").write_text(json.dumps({"reviewer": selected.name, "files": files}),
                                                   encoding="utf-8")
                    with patch.object(sys, "argv", argv), patch.object(room_reviewer, "run_runtime", return_value=json.dumps(review)), patch("builtins.print"):
                        room_reviewer.main()
                    prompt = (root / "scratch/prompt.txt").read_text(encoding="utf-8")
                    self.assertIn("Reviewer packet (frozen criteria and rules): " + str(selected.resolve()), prompt)
                    other = continuity if selected == original else original
                    self.assertNotIn(str(other.resolve()), prompt)

    def test_reviewer_rejects_missing_changed_or_escaping_packet_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "case"
            case.mkdir()
            packet = case / "continuity-reviewer.json"
            packet.write_text('{"criteria": [{"id": "c-continuity"}]}', encoding="utf-8")
            argv = ["room_reviewer.py", "--attempt", str(root / "attempt"), "--case", str(case),
                    "--evaluation-md", str(root / "evaluation.md"), "--runtime", "claude",
                    "--reviewer", "test-reviewer", "--context-id", "test-context",
                    "--out", str(root / "review.json"), "--cwd", str(root / "scratch")]
            invalid = [("missing.json", {}, FileNotFoundError, None),
                       (packet.name, {packet.name: "0" * 64}, ValueError, "identity mismatch"),
                       ("../outside.json", {}, ValueError, "invalid relative path")]
            for selected, files, error, message in invalid:
                with self.subTest(packet=selected):
                    (case / "case.json").write_text(json.dumps({"reviewer": selected, "files": files}),
                                                   encoding="utf-8")
                    with patch.object(sys, "argv", argv), patch.object(room_reviewer, "run_runtime") as runtime:
                        with self.assertRaisesRegex(error, message or ".*"):
                            room_reviewer.main()
                        runtime.assert_not_called()
                    self.assertFalse((root / "scratch").exists())

    def test_shared_extraction(self):
        self.assertEqual(room_reviewer.extract_json('{"outcome": "x"} '), {"outcome": "x"})


if __name__ == "__main__":
    unittest.main()
