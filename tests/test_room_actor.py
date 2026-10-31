"""Unit tests for the CLI actor driver (scripts/room_actor.py).

Covers extraction, validation and private capture with bounded fake subprocesses.
No live CLI is invoked.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import room_actor


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


class NativeCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cwd = self.root / "actor-cwd"
        self.cwd.mkdir()
        self.out = self.root / "private/proposal.json"
        self.sidecar = self.out.with_name(self.out.name + ".capture")
        self.bundle = self.root / "bundle.json"
        self.bundle.write_text(json.dumps({"actor_packet": {"reply_limits": {"max_words": 50}}}), encoding="utf-8")

    def fake(self, stdout, stderr=b"", code=0):
        script = self.root / "fake_actor.py"
        script.write_text("import os\nos.write(1, " + repr(stdout) + ")\nos.write(2, " + repr(stderr)
                          + ")\nraise SystemExit(" + str(code) + ")\n", encoding="utf-8")
        return [sys.executable, "-B", str(script)]

    def run_main(self, argv):
        options = ["room_actor.py", "--bundle", str(self.bundle), "--out", str(self.out),
                   "--runtime", "pi", "--model", "fake", "--context-id", "current-context",
                   "--input-sha256", "allowed-input-digest", "--actor-cwd", str(self.cwd)]
        with patch.object(sys, "argv", options), patch.object(room_actor, "actor_argv", return_value=argv):
            room_actor.main()

    def test_success_keeps_native_bytes_and_process_identity_outside_child_input(self):
        reply = {"message": "Café", "fact_ids": [], "rule_ids": [], "attachments": [],
                 "unanswered_questions": [], "fixture_gaps": [], "stop": False}
        native = (json.dumps(reply, ensure_ascii=False) + "\r\n").encode("utf-8")
        stderr = b"native warning\xff\r\n"
        argv = self.fake(native, stderr)
        self.run_main(argv)
        self.assertEqual((self.sidecar / "stdout.txt").read_bytes(), native)
        self.assertEqual((self.sidecar / "stderr.txt").read_bytes(), stderr)
        process = json.loads((self.sidecar / "process.json").read_text())
        self.assertEqual(process["argv"], argv)
        self.assertGreater(process["pid"], 0)
        self.assertEqual(process["exit_code"], 0)
        self.assertIsNone(process["error"])
        self.assertNotIn(str(self.sidecar), json.dumps(process["argv"]))
        self.assertNotIn(str(self.sidecar), (self.cwd / "prompt.txt").read_text(encoding="utf-8"))
        stored = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(stored, {**reply, "actor_context": {"context_id": "current-context", "input_sha256": "allowed-input-digest"}})
        self.assertEqual(json.loads((self.sidecar / "status.json").read_text())["status"], "ok")

    def test_nonzero_native_retains_full_bytes_before_error(self):
        stdout, stderr = b"partial\xff\n", b"error " + b"x" * 100000
        self.sidecar.mkdir(parents=True)
        with patch.object(room_actor, "actor_argv", return_value=self.fake(stdout, stderr, 7)):
            with self.assertRaisesRegex(RuntimeError, "pi actor failed"):
                room_actor.run_runtime("pi", "fake", self.cwd, self.sidecar)
        self.assertEqual((self.sidecar / "stdout.txt").read_bytes(), stdout)
        self.assertEqual((self.sidecar / "stderr.txt").read_bytes(), stderr)
        self.assertEqual(json.loads((self.sidecar / "process.json").read_text())["exit_code"], 7)

    def test_malformed_claude_envelope_retains_bytes_before_parsing(self):
        self.sidecar.mkdir(parents=True)
        with patch.object(room_actor, "actor_argv", return_value=self.fake(b"\xffnot JSON")):
            with self.assertRaises(json.JSONDecodeError):
                room_actor.run_runtime("claude", "fake", self.cwd, self.sidecar)
        self.assertEqual((self.sidecar / "stdout.txt").read_bytes(), b"\xffnot JSON")
        self.assertEqual(json.loads((self.sidecar / "process.json").read_text())["exit_code"], 0)

    def test_word_limit_rejection_keeps_native_success_and_current_response(self):
        reply = {"message": "word " * 51, "fact_ids": [], "rule_ids": [], "attachments": [],
                 "unanswered_questions": [], "fixture_gaps": [], "stop": False}
        raw = json.dumps(reply)
        with self.assertRaisesRegex(ValueError, "word limit"):
            self.run_main(self.fake(raw.encode("utf-8")))
        self.assertFalse(self.out.exists())
        self.assertEqual((self.sidecar / "response.txt").read_text(), raw)
        status = json.loads((self.sidecar / "status.json").read_text())
        self.assertEqual((status["phase"], status["status"]), ("validation", "error"))
        self.assertEqual(json.loads((self.sidecar / "process.json").read_text())["exit_code"], 0)

    def test_launch_failure_never_reuses_previous_response(self):
        (self.cwd / "last-raw-output.txt").write_text('{"message":"stale"}', encoding="utf-8")
        with self.assertRaises(OSError):
            self.run_main([str(self.root / "nonexistent-executable")])
        self.assertFalse(self.out.exists())
        self.assertFalse((self.sidecar / "response.txt").exists())
        self.assertEqual((self.sidecar / "stdout.txt").read_bytes(), b"")
        process = json.loads((self.sidecar / "process.json").read_text())
        self.assertIsNone(process["pid"])
        self.assertIsNone(process["exit_code"])
        self.assertTrue(process["error"])
        status = json.loads((self.sidecar / "status.json").read_text())
        self.assertEqual((status["phase"], status["status"]), ("runtime", "error"))

    def test_capture_cannot_be_placed_in_actor_working_directory(self):
        self.out = self.cwd / "proposal.json"
        with self.assertRaisesRegex(ValueError, "outside actor working directory"):
            self.run_main(["unused"])
        self.assertFalse((self.cwd / "prompt.txt").exists())


if __name__ == "__main__":
    unittest.main()
