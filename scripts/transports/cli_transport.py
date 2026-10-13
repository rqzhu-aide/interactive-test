"""Adapter shim: let session_driver.invoke() talk to kimi/pi CLIs via the Claude transport contract.

session_driver builds:
    <this shim> --runtime {kimi,pi} --print --output-format stream-json --verbose
        --max-turns N (--session-id|--resume) <driver-uuid> [--model M] [--allowedTools a,b]
with the user message on stdin and cwd = the room's work directory. The shim translates to the
native CLI, then prints exactly one Claude-style stream-json result line on stdout:

    {"type":"result","subtype":"success","is_error":false,"result": "...",
     "session_id": <driver-uuid>, "duration_ms": ..., "total_cost_usd": null, "usage": ...}

Diagnostics and the driver-uuid-to-native-session mapping go to stderr (retained by capture()).
The mapping itself is operational state in the OS temp dir; it is reconstructible from the
retained stderr logs.

Resume semantics:
- kimi: no create-with-id API. Turn 1 runs without -S; the native session id is taken from the
  session.resume_hint meta event and stored; later turns resume with `kimi -S <native id>`.
  The synthetic result line always carries the driver uuid, which is what the driver checks.
- pi: native `--session-id <id>` creates the session if missing, so the driver uuid is used
  directly as the pi session id.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

CLAUDE_VALUE_FLAGS = {"--max-turns", "--model", "--allowedTools"}


def resolve(binary):
    """Windows npm shims are .cmd files that CreateProcess cannot run directly."""
    path = shutil.which(binary)
    if path is None:
        raise RuntimeError("runtime not on PATH: " + binary)
    if path.lower().endswith((".cmd", ".bat")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", path]
    return [path]


def log(*args):
    print("[cli-transport]", *args, file=sys.stderr, flush=True)


def parse_driver_argv(argv):
    opts = {"fresh": None, "session_id": None, "model": None, "allowed_tools": None,
            "passthrough": None}
    if "--version" in argv:
        opts["passthrough"] = "--version"
        return opts
    if "--help" in argv:
        opts["passthrough"] = "--help"
        return opts
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag in ("--session-id", "--resume"):
            opts["fresh"] = flag == "--session-id"
            opts["session_id"] = argv[i + 1]
            i += 2
        elif flag in CLAUDE_VALUE_FLAGS:
            if flag == "--model":
                opts["model"] = argv[i + 1]
            elif flag == "--allowedTools":
                opts["allowed_tools"] = argv[i + 1].split(",")
            i += 2
        else:
            i += 1  # --print, --output-format stream-json (pair), --verbose, ...
    return opts


def mapping_path(driver_uuid):
    return Path(tempfile.gettempdir()) / ("consultant-room-transport-" + driver_uuid + ".json")


def load_native_id(driver_uuid):
    try:
        return json.loads(mapping_path(driver_uuid).read_text(encoding="utf-8"))["native_session_id"]
    except Exception:
        return None


def save_native_id(driver_uuid, native_id):
    mapping_path(driver_uuid).write_text(
        json.dumps({"driver_uuid": driver_uuid, "native_session_id": native_id}, indent=1),
        encoding="utf-8")


def text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content
                       if isinstance(part, dict) and part.get("type") in (None, "text"))
    return ""


def parse_kimi_stream(stdout):
    reply, native_id, usage = "", None, None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("role") == "assistant":
            text = text_from_content(event.get("content"))
            if text.strip():
                reply = text
        if event.get("type") == "session.resume_hint" and event.get("session_id"):
            native_id = event["session_id"]
        if isinstance(event.get("usage"), dict):
            usage = event["usage"]
    return reply, native_id, usage


def parse_pi_json(stdout):
    final = None
    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        if event.get("type") == "message_start":
            final = None
        elif event.get("type") == "message_end":
            # An empty completed message supersedes earlier progress text too.
            final = message
    if final is None:
        return "", None, None
    if final.get("stopReason") != "stop":
        raise RuntimeError("Pi response did not complete: " +
                           str(final.get("errorMessage") or final.get("stopReason") or "unknown stop reason"))
    reply = "".join(part["text"] for part in (final.get("content") or [])
                    if isinstance(part, dict) and part.get("type") == "text"
                    and isinstance(part.get("text"), str))
    usage = final.get("usage") if isinstance(final.get("usage"), dict) else None
    return reply, None, usage


def build_native(runtime, opts, message, cwd):
    """Consultant-agent argv. The consultant sees exactly the staged candidate
    skill and nothing else: kimi --skills-dir replaces user/project discovery;
    pi --no-skills drops discovery while the explicit --skill path (verified in
    pi's loader: noSkills keeps cliEnabledSkills/additionalSkillPaths) still
    loads. Native Claude discovery can select a personal skill over a staged
    project skill with the same name. Use the native transport's explicit
    loading mode and verify the actual host; version checks do not bind the
    installed personal copy. That native-only mode does not apply to this shim."""
    model = opts["model"]
    if runtime == "kimi":
        argv = resolve("kimi") + ["-p", message, "--output-format", "stream-json",
                                  "--skills-dir", str(cwd / ".claude" / "skills")]
        if model:
            argv += ["-m", model]
        native_id = None if opts["fresh"] else load_native_id(opts["session_id"])
        if not opts["fresh"]:
            if not native_id:
                raise RuntimeError("no native kimi session mapped for driver uuid "
                                   + str(opts["session_id"]))
            argv += ["-S", native_id]
        return argv, parse_kimi_stream
    if runtime == "pi":
        argv = resolve("pi") + ["--print", "--no-skills", "--mode", "json", "--session-id", opts["session_id"],
                                "--skill", str(cwd / ".claude" / "skills" / "causal-consultant")]
        if model:
            argv += ["--model", model]
        tools = [t.lower() for t in (opts["allowed_tools"] or [])]
        if tools:
            argv += ["--tools", ",".join(tools)]
        # The message MUST go on stdin, not argv: on Windows the npm pi.CMD shim
        # routes through cmd.exe, whose argument parsing truncates at the first
        # newline (verified 2026-09-30: multi-line user messages arrived cut).
        # pi prepends piped stdin to the first prompt (docs/cli.md).
        return argv, parse_pi_json
    raise RuntimeError("unknown runtime: " + runtime)


def run_native(native_argv, parser, runtime, message, cwd):
    """Run the native CLI; pi receives the user message on stdin."""
    proc = subprocess.run(native_argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(cwd),
                          input=message if runtime == "pi" else None)
    return proc


def ensure_utf8_stdio():
    """Force UTF-8 on this shim's stdout/stderr regardless of console codepage.

    The driver reads our stdout as strict UTF-8; on Windows a piped Python
    stdout defaults to the locale codepage (e.g. cp1252), which corrupts any
    non-ASCII byte in the reply (an em-dash becomes 0x97) and fails the
    driver's strict read. Reconfigure before any print.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def main():
    ensure_utf8_stdio()
    argv = sys.argv[1:]
    if "--runtime" not in argv:
        log("missing --runtime")
        sys.exit(2)
    runtime = argv[argv.index("--runtime") + 1]
    driver_argv = argv[:argv.index("--runtime")] + argv[argv.index("--runtime") + 2:]
    opts = parse_driver_argv(driver_argv)
    if opts["passthrough"]:
        proc = subprocess.run(resolve(runtime) + [opts["passthrough"]],
                              capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)
    message = sys.stdin.read()
    cwd = Path.cwd()
    started = time.time()
    try:
        native_argv, parser = build_native(runtime, opts, message, cwd)
        log("native argv:", json.dumps(native_argv)[:600])
        proc = run_native(native_argv, parser, runtime, message, cwd)
        reply, native_id, usage = parser(proc.stdout)
        if proc.stderr.strip():
            log("native stderr:", proc.stderr.strip()[:2000])
        if native_id:
            save_native_id(opts["session_id"], native_id)
            log("session mapping:", opts["session_id"], "->", native_id)
        ok = proc.returncode == 0 and reply.strip()
        result = {"type": "result", "subtype": "success" if ok else "error_during_execution",
                  "is_error": not ok, "result": reply if ok else "",
                  "session_id": opts["session_id"],
                  "duration_ms": int((time.time() - started) * 1000),
                  "total_cost_usd": None, "usage": usage,
                  "native_exit_code": proc.returncode, "transport_runtime": runtime}
        if not ok:
            result["error_detail"] = (proc.stderr.strip() or "empty reply")[:500]
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if ok else 1)
    except Exception as exc:
        log("shim error:", repr(exc))
        result = {"type": "result", "subtype": "error_during_execution", "is_error": True,
                  "result": "", "session_id": opts["session_id"],
                  "duration_ms": int((time.time() - started) * 1000),
                  "total_cost_usd": None, "usage": None,
                  "transport_runtime": runtime, "error_detail": repr(exc)[:500]}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
