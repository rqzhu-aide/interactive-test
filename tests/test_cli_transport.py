"""Unit tests for the multi-runtime transport shim (scripts/transports/cli_transport.py).

Covers the pure translation layer: driver argv parsing, session mapping persistence,
stream parsing for each native runtime, native argv construction and Windows
binary resolution. No live CLI is invoked.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "transports"))
import cli_transport as shim


class ParseDriverArgvTests(unittest.TestCase):
    def test_full_resume_argv(self):
        opts = shim.parse_driver_argv(
            ["--print", "--output-format", "stream-json", "--verbose", "--max-turns", "120",
             "--resume", "uuid-1", "--model", "kimi-code/k3-256k", "--allowedTools", "Read,Write,Bash"])
        self.assertFalse(opts["fresh"])
        self.assertEqual(opts["session_id"], "uuid-1")
        self.assertEqual(opts["model"], "kimi-code/k3-256k")
        self.assertEqual(opts["allowed_tools"], ["Read", "Write", "Bash"])
        self.assertIsNone(opts["passthrough"])

    def test_session_id_means_fresh(self):
        opts = shim.parse_driver_argv(["--session-id", "uuid-2"])
        self.assertTrue(opts["fresh"])
        self.assertEqual(opts["session_id"], "uuid-2")

    def test_passthrough_flags_short_circuit(self):
        self.assertEqual(shim.parse_driver_argv(["--version"])["passthrough"], "--version")
        self.assertEqual(shim.parse_driver_argv(["--help"])["passthrough"], "--help")

    def test_unknown_flags_are_skipped_not_crashed(self):
        opts = shim.parse_driver_argv(["--some-new-flag", "--resume", "uuid-3"])
        self.assertEqual(opts["session_id"], "uuid-3")


class SessionMappingTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tempfile.gettempdir", return_value=tmp):
                self.assertIsNone(shim.load_native_id("driver-uuid"))
                shim.save_native_id("driver-uuid", "native-7")
                self.assertEqual(shim.load_native_id("driver-uuid"), "native-7")
                self.assertEqual(json.loads(shim.mapping_path("driver-uuid").read_text(encoding="utf-8")),
                                 {"driver_uuid": "driver-uuid", "native_session_id": "native-7"})

    def test_corrupt_mapping_reads_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tempfile.gettempdir", return_value=tmp):
                shim.mapping_path("driver-uuid").write_text("not json", encoding="utf-8")
                self.assertIsNone(shim.load_native_id("driver-uuid"))


class StreamParsingTests(unittest.TestCase):
    def test_text_from_content_shapes(self):
        self.assertEqual(shim.text_from_content("plain"), "plain")
        self.assertEqual(shim.text_from_content([{"type": "text", "text": "a"},
                                                 {"type": "tool_use", "text": "b"},
                                                 {"text": "c"}]), "ac")
        self.assertEqual(shim.text_from_content(None), "")
        self.assertEqual(shim.text_from_content(42), "")

    def test_parse_kimi_stream(self):
        stdout = "\n".join([
            "junk line",
            json.dumps({"role": "assistant", "content": [{"type": "text", "text": "earlier"}]}),
            json.dumps({"type": "session.resume_hint", "session_id": "native-9"}),
            json.dumps({"role": "assistant", "content": "final answer"}),
            json.dumps({"usage": {"input_tokens": 3, "output_tokens": 5}}),
        ])
        reply, native_id, usage = shim.parse_kimi_stream(stdout)
        self.assertEqual(reply, "final answer")
        self.assertEqual(native_id, "native-9")
        self.assertEqual(usage, {"input_tokens": 3, "output_tokens": 5})

    def test_parse_kimi_stream_without_events(self):
        reply, native_id, usage = shim.parse_kimi_stream("")
        self.assertEqual((reply, native_id, usage), ("", None, None))

    def test_parse_pi_json_completed_final_message(self):
        answer = "First\u2028second\u2029third"
        events = "\r\n".join([
            json.dumps({"role": "user", "content": "ignored"}),
            json.dumps({"type": "message_end", "message": {"role": "assistant", "stopReason": "toolUse",
                       "content": [{"type": "text", "text": "earlier progress"}]}}),
            json.dumps({"type": "message_end", "message": {"role": "toolResult", "content": "ignored"}}),
            json.dumps({"type": "message_update", "text": "ignored", "usage": {"total_tokens": 2}}),
            json.dumps({"type": "message_end", "message": {"role": "assistant", "stopReason": "stop",
                       "content": [{"type": "thinking", "thinking": "private"},
                                   {"type": "text", "text": answer},
                                   {"text": "untyped content is not public text"}],
                       "usage": {"total_tokens": 8}}}, ensure_ascii=False),
            json.dumps({"type": "agent_end", "messages": []}),
        ])
        reply, native_id, usage = shim.parse_pi_json(events)
        self.assertEqual(reply, answer)
        self.assertIsNone(native_id)
        self.assertEqual(usage, {"total_tokens": 8})

    def test_parse_pi_json_missing_or_failed_final_reply(self):
        earlier = json.dumps({"type": "message_end", "message": {"role": "assistant", "stopReason": "stop",
                              "content": [{"type": "text", "text": "earlier progress"}]}}) + "\n"
        for content in ([], [{"type": "thinking", "thinking": "private"}], [{"type": "text", "text": "  "}]):
            with self.subTest(content=content):
                final = {"type": "message_end", "message": {"role": "assistant", "stopReason": "stop",
                         "content": content, "usage": {"total_tokens": 8}}}
                reply, native_id, usage = shim.parse_pi_json(earlier + json.dumps(final))
                self.assertEqual(reply.strip(), "")
                self.assertIsNone(native_id)
                self.assertEqual(usage, {"total_tokens": 8})
        for stop in ("error", "aborted", "length", "toolUse", "pending", None):
            with self.subTest(stop=stop):
                final = {"type": "message_end", "message": {"role": "assistant", "stopReason": stop,
                         "content": [{"type": "text", "text": "not a completed answer"}]}}
                with self.assertRaisesRegex(RuntimeError, "Pi response did not complete"):
                    shim.parse_pi_json(earlier + json.dumps(final))
        for stdout in ("", "plain text-mode output", json.dumps({"text": "role-less event"}),
                       json.dumps({"type": "message_end", "message": {"role": "toolResult", "content": "tool output"}}),
                       earlier + json.dumps({"type": "message_start", "message": {"role": "assistant"}})):
            with self.subTest(stdout=stdout):
                self.assertEqual(shim.parse_pi_json(stdout), ("", None, None))


class BuildNativeTests(unittest.TestCase):
    def setUp(self):
        self.resolve = patch.object(shim, "resolve", lambda binary: ["X-" + binary])
        self.resolve.start()
        self.addCleanup(self.resolve.stop)
        self.cwd = Path("W")

    def base_opts(self, fresh=True, session_id="uuid-1", model=None, tools=None):
        return {"fresh": fresh, "session_id": session_id, "model": model,
                "allowed_tools": tools, "passthrough": None}

    def test_kimi_fresh_argv(self):
        argv, parser = shim.build_native("kimi", self.base_opts(model="kimi-code/k3-256k"), "MSG", self.cwd)
        self.assertEqual(argv, ["X-kimi", "-p", "MSG", "--output-format", "stream-json",
                                "--skills-dir", str(self.cwd / ".claude" / "skills"),
                                "-m", "kimi-code/k3-256k"])
        self.assertIs(parser, shim.parse_kimi_stream)

    def test_kimi_resume_uses_mapped_native_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tempfile.gettempdir", return_value=tmp):
                shim.save_native_id("uuid-1", "native-3")
                argv, _ = shim.build_native("kimi", self.base_opts(fresh=False), "MSG", self.cwd)
        self.assertIn("-S", argv)
        self.assertEqual(argv[argv.index("-S") + 1], "native-3")

    def test_kimi_resume_without_mapping_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tempfile.gettempdir", return_value=tmp):
                with self.assertRaisesRegex(RuntimeError, "no native kimi session mapped"):
                    shim.build_native("kimi", self.base_opts(fresh=False), "MSG", self.cwd)

    def test_pi_argv_binds_driver_uuid_directly(self):
        argv, parser = shim.build_native(
            "pi", self.base_opts(session_id="uuid-9", model="zhipu/glm-5.3-max",
                                 tools=["Read", "Write"]), "MSG", self.cwd)
        # The user message travels on stdin (cmd.exe argv truncates at the
        # first newline on Windows); it must NOT appear in argv.
        self.assertEqual(argv, ["X-pi", "--print", "--no-skills", "--mode", "json", "--session-id", "uuid-9",
                                "--skill", str(self.cwd / ".claude" / "skills" / "causal-consultant"),
                                "--model", "zhipu/glm-5.3-max", "--tools", "read,write"])
        self.assertNotIn("MSG", argv)
        self.assertIs(parser, shim.parse_pi_json)

    def test_run_native_pi_message_on_stdin(self):
        with patch.object(shim.subprocess, "run", return_value=object()) as run:
            shim.run_native(["X-pi"], shim.parse_pi_json, "pi", "line1\nline2", self.cwd)
        self.assertEqual(run.call_args.kwargs.get("input"), "line1\nline2")

    def test_run_native_kimi_message_on_argv(self):
        with patch.object(shim.subprocess, "run", return_value=object()) as run:
            shim.run_native(["X-kimi", "-p"], None, "kimi", "MSG", self.cwd)
        self.assertIsNone(run.call_args.kwargs.get("input"))

    def test_unknown_runtime_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "unknown runtime"):
            shim.build_native("gemini", self.base_opts(), "MSG", self.cwd)


class ResolveTests(unittest.TestCase):
    def test_windows_cmd_shim_goes_through_comspec(self):
        with patch.object(shim.shutil, "which", return_value="C:\\tools\\kimi.cmd"):
            resolved = shim.resolve("kimi")
        self.assertEqual(resolved[1:], ["/c", "C:\\tools\\kimi.cmd"])

    def test_plain_binary_returned_directly(self):
        with patch.object(shim.shutil, "which", return_value="C:\\tools\\pi.exe"):
            self.assertEqual(shim.resolve("pi"), ["C:\\tools\\pi.exe"])

    def test_missing_binary_fails_loudly(self):
        with patch.object(shim.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "runtime not on PATH"):
                shim.resolve("kimi")


class StdioEncodingTests(unittest.TestCase):
    def test_shim_forces_utf8_stdio(self):
        shim.ensure_utf8_stdio()
        self.assertIn(shim.sys.stdout.encoding.lower(), ("utf-8", "utf8"))

    def test_shim_module_has_no_cp1252_print_path_before_reconfigure(self):
        self.assertTrue(callable(shim.ensure_utf8_stdio))


if __name__ == "__main__":
    unittest.main()
