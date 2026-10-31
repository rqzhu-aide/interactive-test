"""Native candidate binding without live agent calls."""
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
from session_driver import validate_config


class CandidateLoading(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="candidate-loading-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / "work"
        self.skill = self.work / ".claude/skills/causal-consultant/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.content = "---\r\nname: causal-consultant\r\n---\r\nExact caf\u00e9 instructions.\n".encode("utf-8")
        self.skill.write_bytes(self.content)
        self.config = {"claude_command": ["claude"], "node_command": ["node"],
                       "candidate_loading": "claude_explicit", "max_agent_turns_per_call": 120,
                       "call_timeout_seconds": 3600, "mode": "diagnostic",
                       "limits": {"consultant_turns": 40, "active_seconds": 14400, "elapsed_seconds": 43200}}
        self.calls = []

    def capture(self, argv, cwd, message, timeout, output):
        self.calls.append({"argv": argv, "cwd": cwd, "message": message})
        output = Path(output)
        output.mkdir()
        (output / "request.txt").write_bytes(message.encode("utf-8"))
        (output / "command.json").write_text(json.dumps({"argv": argv}), encoding="utf-8")
        result = {"type": "result", "subtype": "success", "session_id": "test-session",
                  "is_error": False, "result": "Unchanged response."}
        (output / "stdout.txt").write_text(json.dumps(result) + "\n", encoding="utf-8")
        return {"exit_code": 0, "error": None, "active_seconds": 0.01}

    def invoke(self, fresh=True, output="capture", message="Original user request.\r\nSecond line.\n"):
        with patch.object(transport, "capture", side_effect=self.capture):
            return transport.invoke(self.config, self.work, "test-session", fresh, message, 60, self.root / output)

    def test_exact_staged_entry_and_base_directory_are_bound_without_changing_stdin(self):
        validate_config(self.config)
        result = self.invoke()
        argv = self.calls[0]["argv"]
        expected = ("Base directory for this skill: " + str(self.skill.parent.resolve()) + "\n\n").encode("utf-8") + self.content
        self.assertIn("--disable-slash-commands", argv)
        self.assertEqual(argv[argv.index("--append-system-prompt") + 1].encode("utf-8"), expected)
        self.assertEqual((self.root / "capture/candidate-system-prompt.txt").read_bytes(), expected)
        self.assertEqual((self.root / "capture/request.txt").read_bytes(), b"Original user request.\r\nSecond line.\n")
        loading = json.loads((self.root / "capture/candidate-loading.json").read_text(encoding="utf-8"))
        self.assertEqual(loading, result["candidate_loading"])
        self.assertEqual(loading["skill_sha256"], hashlib.sha256(self.content).hexdigest())
        self.assertEqual(loading["system_prompt_sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(loading["skill_path"], str(self.skill.resolve()))
        self.assertEqual(len(loading["loading_id"]), 64)

    def test_resume_reuses_exact_binding_and_identity(self):
        first = self.invoke(output="first")
        resumed = self.invoke(fresh=False, output="resumed", message="A real follow-up.")
        self.assertIn("--session-id", self.calls[0]["argv"])
        self.assertNotIn("--session-id", self.calls[1]["argv"])
        self.assertIn("--resume", self.calls[1]["argv"])
        self.assertEqual(first["candidate_loading"], resumed["candidate_loading"])
        self.assertEqual((self.root / "first/candidate-system-prompt.txt").read_bytes(),
                         (self.root / "resumed/candidate-system-prompt.txt").read_bytes())
        self.assertEqual(self.calls[1]["message"], "A real follow-up.")

    def test_missing_entry_rejects_before_dispatch(self):
        self.skill.unlink()
        with patch.object(transport, "capture") as capture:
            with self.assertRaises(FileNotFoundError):
                transport.invoke(self.config, self.work, "test-session", True, "Request", 60, self.root / "capture")
            capture.assert_not_called()

    def test_invalid_utf8_rejects_before_dispatch(self):
        self.skill.write_bytes(b"\xff")
        with patch.object(transport, "capture") as capture:
            with self.assertRaises(UnicodeDecodeError):
                transport.invoke(self.config, self.work, "test-session", True, "Request", 60, self.root / "capture")
            capture.assert_not_called()

    def test_missing_mode_keeps_historical_discovery_and_wrapper_config(self):
        del self.config["candidate_loading"]
        self.config["claude_command"] = ["python", "cli_transport.py", "--runtime", "kimi"]
        self.skill.unlink()
        validate_config(self.config)
        result = self.invoke()
        self.assertNotIn("--append-system-prompt", self.calls[0]["argv"])
        self.assertNotIn("--disable-slash-commands", self.calls[0]["argv"])
        self.assertNotIn("candidate_loading", result)
        self.assertFalse((self.root / "capture/candidate-loading.json").exists())

    def test_unknown_modes_are_rejected(self):
        for mode in (None, "discovery", "kimi_explicit", True):
            with self.subTest(mode=mode):
                self.config["candidate_loading"] = mode
                with self.assertRaisesRegex(ValueError, "unsupported candidate_loading"):
                    validate_config(self.config)

    def test_explicit_adapter_choice_preserves_its_own_loading_flags(self):
        self.config.update(candidate_loading="adapter", claude_command=["python", "cli_transport.py", "--runtime", "kimi"])
        self.skill.unlink()
        validate_config(self.config)
        self.invoke()
        self.assertNotIn("--append-system-prompt", self.calls[0]["argv"])
        self.assertNotIn("--disable-slash-commands", self.calls[0]["argv"])

    def test_explicit_native_mode_rejects_wrapper_arguments(self):
        self.config["claude_command"] = ["python", "arbitrary-name.py", "--runtime", "pi"]
        with self.assertRaisesRegex(ValueError, "native Claude executable"):
            validate_config(self.config)
        with patch.object(transport, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "native Claude executable"):
                transport.invoke(self.config, self.work, "test-session", True, "Request", 60, self.root / "capture")
            capture.assert_not_called()

    def test_loading_evidence_survives_provider_failure(self):
        def failed_capture(*args):
            result = self.capture(*args)
            result.update(exit_code=1, error="timeout")
            return result
        with patch.object(transport, "capture", side_effect=failed_capture):
            result = transport.invoke(self.config, self.work, "test-session", True, "Request", 60, self.root / "capture")
        self.assertEqual(result["error"], "timeout")
        self.assertIsNone(result["message"])
        self.assertTrue((self.root / "capture/candidate-loading.json").exists())
        self.assertTrue((self.root / "capture/candidate-system-prompt.txt").exists())


if __name__ == "__main__":
    unittest.main()
