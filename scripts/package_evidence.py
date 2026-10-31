"""Export retained review evidence without repairing or rewriting the source attempt."""
import hashlib
import json
import ntpath
import os
import posixpath
from pathlib import Path, PurePosixPath
import stat
import zipfile


MANIFEST = "package-manifest.json"
NOTICE = "PACKAGE-STATUS.txt"
CAPTURE_FILES = ("command.json", "request.txt", "stdout.txt", "stderr.txt", "process.json")
PACKAGE_FORMAT = "interactive-test-review-package"
LEGACY_PACKAGE_FORMAT = "interactive-test-cc-review-package"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _name(name):
    _require(isinstance(name, str) and name and "\\" not in name and ":" not in name
             and not PurePosixPath(name).is_absolute()
             and all(part not in ("", ".", "..") for part in name.split("/")),
             "unsafe package path: " + str(name))
    return name


def _no_links(path):
    path = Path(os.path.abspath(path))
    for current in (path, *path.parents):
        _require(not current.is_symlink() and not (hasattr(current, "is_junction") and current.is_junction()),
                 "links are not package paths: " + str(current))
    return path


def _inventory(root, prefix):
    result = {}
    folded = set()
    if not root.exists():
        return result
    _require(root.is_dir(), "evidence root is not a directory: " + str(root))
    for folder, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = _no_links(Path(folder) / name)
            _require(path.is_dir() or path.is_file(), "unsupported evidence entry: " + str(path))
        for name in files:
            path = Path(folder) / name
            reference = _name(prefix + "/" + path.relative_to(root).as_posix())
            _require(reference.casefold() not in folded,
                     "case-colliding evidence paths: " + reference)
            result[reference] = path
            folded.add(reference.casefold())
    return result


def _sha_file(path):
    with path.open("rb") as stream:
        return _sha_stream(stream)


def _sha_stream(stream):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(chunk)
    return result.hexdigest()


def candidate_loading_check(frozen, state, files, read_bytes):
    """Reconcile indexed explicit-loading captures, not model adherence or isolation."""
    if frozen.get("configuration", {}).get("candidate_loading") != "claude_explicit":
        return None  # Historical discovery has no explicit-loading contract.
    calls = []
    work, session = state.get("work"), state.get("session_id")
    skill_sha = frozen.get("candidate_files", {}).get("SKILL.md")
    # Use lexical paths so archived Windows evidence is also checkable elsewhere.
    def same_path(actual, expected):
        if not isinstance(actual, str) or not isinstance(expected, str):
            return False
        paths = ntpath if ntpath.splitdrive(expected)[0] else posixpath
        return paths.normcase(paths.normpath(actual)) == paths.normcase(paths.normpath(expected))

    turns = state.get("turns")
    valid_turn_count = type(turns) is int and turns >= 0
    event_ids = {ref.split("/")[2] for ref in files if ref.startswith("private/events/")
                 and len(ref.split("/")) > 3 and ref.split("/")[2].isdigit()}
    if valid_turn_count and turns > 0:
        event_ids.update(f"{turn:03d}" for turn in range(1, turns + 1))
    for event_id in sorted(event_ids):
        prefix = "private/events/" + event_id + "/transport/"
        issues, refs = [], []

        def issue(name, reason, status="conflict"):
            item = {"evidence_ref": prefix + name if name else "private/freeze.json",
                    "reason": reason, "status": status}
            if item not in issues:
                issues.append(item)

        def retained(name, document=False):
            ref = prefix + name
            if ref not in files:
                issue(name, "missing_indexed_capture", "unobserved")
                return None
            refs.append(ref)
            try:
                content = read_bytes(ref)
                if hashlib.sha256(content).hexdigest() != files[ref]:
                    issue(name, "capture_hash_mismatch")
                    return None
                value = json.loads(content.decode("utf-8-sig")) if document else content.decode("utf-8")
                if document and not isinstance(value, dict):
                    raise ValueError("expected object")
                return value
            except (OSError, KeyError):
                issue(name, "unreadable_capture", "unobserved")
            except (ValueError, UnicodeError):
                issue(name, "invalid_capture")
            return None

        receipt = retained("candidate-loading.json", True)
        prompt = retained("candidate-system-prompt.txt")
        command = retained("command.json", True)
        transport = retained("transport.json", True)
        raw = retained("stdout.txt")
        if not isinstance(work, str) or not work or not isinstance(session, str) or not session:
            issue("", "missing_work_or_session_identity", "unobserved")
        if not isinstance(skill_sha, str) or len(skill_sha) != 64:
            issue("", "missing_frozen_skill_hash", "unobserved")
        if receipt is not None:
            keys = {"mode", "skill_path", "base_directory", "skill_sha256", "system_prompt_sha256", "loading_id"}
            paths = ntpath if isinstance(work, str) and ntpath.splitdrive(work)[0] else posixpath
            base = paths.join(work if isinstance(work, str) else "", ".claude", "skills", "causal-consultant")
            if (set(receipt) != keys or receipt.get("mode") != "claude_explicit"
                    or (isinstance(work, str) and work and (not same_path(receipt.get("base_directory"), base)
                        or not same_path(receipt.get("skill_path"), paths.join(base, "SKILL.md"))))
                    or (skill_sha is not None and receipt.get("skill_sha256") != skill_sha)):
                issue("candidate-loading.json", "frozen_candidate_mismatch")
            binding = {key: value for key, value in receipt.items() if key != "loading_id"}
            if receipt.get("loading_id") != hashlib.sha256(json.dumps(binding, sort_keys=True).encode("utf-8")).hexdigest():
                issue("candidate-loading.json", "loading_identity_mismatch")
            if prompt is not None:
                header = "Base directory for this skill: " + str(receipt.get("base_directory")) + "\n\n"
                if (not prompt.startswith(header)
                        or (skill_sha is not None and hashlib.sha256(prompt[len(header):].encode("utf-8")).hexdigest() != skill_sha)
                        or hashlib.sha256(prompt.encode("utf-8")).hexdigest() != receipt.get("system_prompt_sha256")):
                    issue("candidate-system-prompt.txt", "frozen_prompt_mismatch")
        if command is not None:
            argv = command.get("argv")
            if not isinstance(argv, list) or not all(isinstance(value, str) for value in argv):
                issue("command.json", "invalid_argv")
            else:
                if argv[:1] != frozen.get("configuration", {}).get("claude_command"):
                    issue("command.json", "frozen_executable_mismatch")
                def flag_value(flag):
                    positions = [i for i, value in enumerate(argv) if value == flag or value.startswith(flag + "=")]
                    if len(positions) != 1 or argv[positions[0]] != flag or positions[0] + 1 >= len(argv):
                        return None
                    return argv[positions[0] + 1]
                if prompt is not None and flag_value("--append-system-prompt") != prompt:
                    issue("command.json", "prompt_argument_mismatch")
                if argv.count("--disable-slash-commands") != 1:
                    issue("command.json", "discovery_not_disabled")
                expected_flag, forbidden_flag = (("--session-id", "--resume") if int(event_id) == 1
                                                  else ("--resume", "--session-id"))
                if (flag_value(expected_flag) != session or any(value == forbidden_flag or value.startswith(forbidden_flag + "=")
                                                               for value in argv)):
                    issue("command.json", "fresh_resume_identity_mismatch")
            if not same_path(command.get("cwd"), work):
                issue("command.json", "work_directory_mismatch")
        if transport is not None:
            if receipt is not None and transport.get("candidate_loading") != receipt:
                issue("transport.json", "receipt_mismatch")
            if command is not None and (transport.get("argv") != command.get("argv")
                                        or transport.get("cwd") != command.get("cwd")):
                issue("transport.json", "command_mismatch")
            if transport.get("session_id") != session:
                issue("transport.json", "session_identity_mismatch", "unobserved" if not transport.get("session_id") else "conflict")
        if raw is not None:
            try:
                events = [json.loads(line) for line in raw.splitlines() if line.strip()]
                results = [item for item in events if isinstance(item, dict) and item.get("type") == "result"]
                if len(results) != 1:
                    issue("stdout.txt", "missing_unique_native_result", "unobserved")
                elif results[0].get("session_id") != session:
                    issue("stdout.txt", "native_session_identity_mismatch",
                          "unobserved" if not results[0].get("session_id") else "conflict")
            except ValueError:
                issue("stdout.txt", "invalid_native_stream")
        status = "conflict" if any(item["status"] == "conflict" for item in issues) else "unobserved" if issues else "matched"
        calls.append({"event": event_id, "status": status, "issues": issues, "evidence_refs": refs})
    status = ("conflict" if any(item["status"] == "conflict" for item in calls)
              else "unobserved" if not valid_turn_count or not calls or any(item["status"] == "unobserved" for item in calls) else "matched")
    return {"mode": "claude_explicit", "status": status, "calls": calls,
            **({"reason": "Missing or invalid retained turn count; complete call coverage is unobserved."} if not valid_turn_count else {}),
            "scope": "Bound staged entry instructions and fresh/resume session evidence; later tool-path adherence and isolation require review."}


def _analyze(files, read_bytes):
    """The same expectation checks run on original files and archived bytes."""
    omissions = []

    def issue(path, reason, **details):
        item = {"path": path, "reason": reason, **details}
        if item not in omissions:
            omissions.append(item)

    def required(path, expected=None):
        _name(path)
        if path not in files:
            issue(path, "missing", **({"expected_sha256": expected} if expected else {}))
            return False
        if expected is not None and files[path] != expected:
            issue(path, "hash_mismatch", expected_sha256=expected, actual_sha256=files[path])
            return False
        return True

    def document(path):
        if not required(path):
            return {}
        try:
            value = json.loads(read_bytes(path).decode("utf-8-sig"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (ValueError, UnicodeError) as exc:
            issue(path, "invalid_json", detail=str(exc))
            return {}

    def mapping(value, path):
        if not isinstance(value, dict):
            issue(path, "invalid_file_inventory")
            return {}
        for name, sha in value.items():
            _name(name)
            _require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha),
                     "invalid SHA256 in " + path + ": " + name)
        return value

    state = document("private/state.json")
    frozen = document("private/freeze.json")
    index = document("private/review-index.json")
    expected = mapping(index.get("files", {}), "private/review-index.json")
    if not expected or index.get("sha256") != _identity(expected):
        issue("private/review-index.json", "invalid_review_index_identity")
    for path, sha in expected.items():
        if path == "state_at_review":
            continue
        _require(path.startswith(("private/", "work/")), "unsupported review evidence reference: " + path)
        required(path, sha)
    loading = candidate_loading_check(frozen, state, expected, read_bytes)
    if loading is not None:
        if "private/freeze.json" not in expected:
            issue("private/freeze.json", "not_bound_to_review_index")
        if not loading["calls"]:
            issue("private/state.json", "candidate_loading_unobserved")
        for call in loading["calls"]:
            for item in call["issues"]:
                issue(item["evidence_ref"], "candidate_loading_" + item["reason"])
    state_hash = expected.get("state_at_review")
    candidates = [state]
    if state.get("status") == "finished":
        # finish changes only this field after the reviewer-bound state was hashed.
        candidates += [{**state, "status": status} for status in
                       ("ready", "awaiting_review", "execution_error", "limit_reached", "pending")]
    if not state_hash or not any(_identity(value) == state_hash for value in candidates):
        issue("state_at_review", "review_state_mismatch")
    if state.get("status") == "finished" or "private/assessment.json" in files:
        assessment = document("private/assessment.json")
        if assessment.get("evidence_sha256") != index.get("sha256"):
            issue("private/assessment.json", "review_index_mismatch")
    if (frozen.get("review_package_profile") == "review-observations-v1"
            or "observations_sha256" in index or "private/review-observations.json" in files):
        if not index.get("observations_sha256"):
            issue("private/review-index.json", "missing_observations_identity")
        required("private/review-observations.json", index.get("observations_sha256"))
        observations = document("private/review-observations.json")
        if observations.get("evidence_sha256") != index.get("sha256"):
            issue("private/review-observations.json", "review_index_mismatch")
        if state.get("status") == "finished" and assessment.get("observations_sha256") != index.get("observations_sha256"):
            issue("private/assessment.json", "review_observations_mismatch")

    required("private/case/case.json", frozen.get("case_sha256"))
    case = frozen.get("case_manifest", {})
    if not isinstance(case, dict):
        case = {}
        issue("private/freeze.json", "invalid_case_manifest")
    for name, sha in mapping(case.get("files", {}), "private/freeze.json:case_manifest").items():
        required("private/case/" + name, sha)
    for name, sha in mapping(frozen.get("testing_files", {}), "private/freeze.json:testing_files").items():
        required("private/testing/" + name, sha)
    for name in ("SKILL.md", "README.md", "scripts/session_driver.py", "scripts/claude_transport.py"):
        required("private/testing/" + name)
    for name, sha in mapping(frozen.get("candidate_files", {}), "private/freeze.json:candidate_files").items():
        required("work/.claude/skills/causal-consultant/" + name, sha)
    for name, sha in mapping(frozen.get("host_files", {}), "private/freeze.json:host_files").items():
        required("private/host/" + name, sha)
    for name, sha in mapping(state.get("public_files", {}), "private/state.json:public_files").items():
        required("work/" + name, sha)
    for command in ("claude-version", "claude-help"):
        for name in CAPTURE_FILES:
            required("private/" + command + "/" + name)

    turns = state.get("turns")
    if type(turns) is not int or turns < 0:
        issue("private/state.json", "invalid_turn_count")
        turns = 0
    event_ids = {path.split("/")[2] for path in set(files) | set(expected)
                 if path.startswith("private/events/") and len(path.split("/")) > 3
                 and path.split("/")[2].isdigit()}
    event_ids.update(f"{turn:03d}" for turn in range(1, turns + 1))
    for event_id in sorted(event_ids):
        event = "private/events/" + event_id + "/"
        for name in ("actor.json", "releases.json", "exchange-observation.json"):
            required(event + name)
        public = document(event + "public.json")
        transport = document(event + "transport/transport.json")
        for name in CAPTURE_FILES:
            required(event + "transport/" + name)
        for name in ("public.json", "transport/transport.json", *("transport/" + item for item in CAPTURE_FILES)):
            if event + name in files and event + name not in expected:
                issue(event + name, "not_bound_to_review_index")
        public_text, transport_text = public.get("assistant"), transport.get("message")
        if event + "public.json" in files and ("assistant" not in public
                or (public_text is not None and not isinstance(public_text, str))
                or (public_text is None and isinstance(transport_text, str))):
            issue(event + "public.json", "invalid_public_capture")
        if event + "transport/transport.json" in files and ("message" not in transport
                or (transport_text is not None and not isinstance(transport_text, str))
                or (transport_text is None and isinstance(public_text, str))):
            issue(event + "transport/transport.json", "invalid_transport_capture")
        if isinstance(public_text, str) and isinstance(transport_text, str) and public_text != transport_text:
            issue(event + "public.json", "public_transport_mismatch")
        raw_path = event + "transport/stdout.txt"
        if not transport.get("error") and isinstance(transport.get("message"), str) and raw_path in files:
            try:
                events = [json.loads(line) for line in read_bytes(raw_path).decode("utf-8").splitlines()
                          if line.strip()]
                results = [item for item in events if isinstance(item, dict) and item.get("type") == "result"]
                if len(results) != 1 or not isinstance(results[0].get("result"), str):
                    issue(raw_path, "invalid_raw_capture")
                elif results[0]["result"] != transport["message"]:
                    issue(raw_path, "raw_public_mismatch")
            except (KeyError, OSError):
                issue(raw_path, "unreadable_raw_capture")
            except (ValueError, UnicodeError):
                issue(raw_path, "invalid_raw_capture")
        captured = document(event + "work-files.json")
        for name, sha in mapping(captured, event + "work-files.json").items():
            required(event + "work-snapshot/" + name, sha)
        binding = document(event + "project-binding.json")
        observed = {path.split("/")[3] for path in set(files) | set(expected)
                    if path.startswith(event + "project-") and len(path.split("/")) > 4}
        if binding.get("status") == "bound":
            observed.update("project-" + command for command in ("status", "context", "history", "verify"))
        elif binding:
            required(event + "observation-skipped.json")
        for command in sorted(observed):
            for name in CAPTURE_FILES:
                required(event + command + "/" + name)
    return {"completeness": "partial" if omissions else "complete", "omissions": omissions,
            "review_index_sha256": index.get("sha256"), "expected_files": expected,
            "turns": turns, "attempt_status": state.get("status")}


def export_package(attempt, output, *, allow_partial=False, work=None):
    """Create a fresh ZIP; incomplete evidence requires explicit allow_partial=True."""
    attempt, output = _no_links(attempt), _no_links(output)
    _require(attempt.is_dir(), "attempt does not exist: " + str(attempt))
    _require(not (attempt / "operator.lock").exists(), "attempt has an active or interrupted operator lock")
    _require(not output.exists(), "package output already exists: " + str(output))
    _require(output.parent.is_dir(), "package output parent must already exist")
    state_path = attempt / "state.json"
    _no_links(state_path)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError("cannot locate retained work; state.json is missing or invalid: " + str(exc)) from exc
    work_root = _no_links(work if work is not None else state["work"])
    _require(not attempt.is_relative_to(work_root) and not work_root.is_relative_to(attempt),
             "attempt and work roots overlap")
    _require(not any(output.is_relative_to(root) for root in (attempt, work_root)),
             "package output must be outside attempt and work roots")
    sources = {**_inventory(attempt, "private"), **_inventory(work_root, "work")}
    files = {name: _sha_file(path) for name, path in sorted(sources.items())}
    analysis = _analyze(files, lambda name: sources[name].read_bytes())
    if not work_root.is_dir() and not any(item["path"].startswith("work/") for item in analysis["omissions"]):
        analysis["omissions"].append({"path": "work/", "reason": "missing"})
        analysis["completeness"] = "partial"
    _require(allow_partial or analysis["completeness"] == "complete",
             "complete package refused; missing or changed evidence: " +
             "; ".join(item["path"] + " (" + item["reason"] + ")" for item in analysis["omissions"]))
    notice = (("PARTIAL REVIEW PACKAGE\n" if analysis["omissions"] else "COMPLETE REVIEW PACKAGE\n") +
              "Completeness concerns retained evidence, not scientific validity or a successful outcome.\n" +
              "All discovered regular files are retained, including raw logs and unexpected content.\n" +
              "SHA256 verifies agreement with retained inventories, not independent authenticity.\n" +
              "".join(item["path"] + ": " + item["reason"] + "\n" for item in analysis["omissions"]))
    notice_bytes = notice.encode("utf-8")
    packaged_files = {**files, NOTICE: hashlib.sha256(notice_bytes).hexdigest()}
    manifest = {"schema_version": 1, "format": PACKAGE_FORMAT, **analysis,
                "source_attempt": str(attempt), "source_work": str(work_root),
                "recorded_work": state.get("work"), "work_override": work is not None,
                "files": packaged_files, "files_sha256": _identity(packaged_files)}
    created = False
    try:
        # Mode x claims the name atomically and refuses races with other exporters.
        with output.open("xb") as destination:
            created = True
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(MANIFEST, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
                archive.writestr(NOTICE, notice_bytes)
                for name, path in sorted(sources.items()):
                    _no_links(path)
                    archive.write(path, name)
        # Recompute archive checks before declaring success, including concurrent file changes.
        result = check_package(output, require_complete=not allow_partial)
        current = {**_inventory(attempt, "private"), **_inventory(work_root, "work")}
        _require(set(current) == set(sources) and all(_sha_file(path) == files[name] for name, path in current.items()),
                 "source evidence changed during packaging")
        _require(not (attempt / "operator.lock").exists(), "attempt became active during packaging")
        return result
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise


def check_package(package, *, require_complete=True):
    """Check every ZIP member and independently re-evaluate completeness without extraction."""
    package = _no_links(package)
    try:
        with zipfile.ZipFile(package) as archive:
            names = []
            for info in archive.infolist():
                _name(info.filename)
                _require(not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16),
                         "package contains a directory or symbolic link entry: " + info.filename)
                names.append(info.filename)
            _require(len(names) == len(set(name.casefold() for name in names)), "package contains duplicate member names")
            _require(MANIFEST in names, "package manifest is missing")
            manifest = json.loads(archive.read(MANIFEST).decode("utf-8-sig"))
            _require(manifest.get("schema_version") == 1
                     and manifest.get("format") in (PACKAGE_FORMAT, LEGACY_PACKAGE_FORMAT),
                     "unsupported review package format")
            expected_files = manifest["files"]
            _require(isinstance(expected_files, dict) and set(expected_files) == set(names) - {MANIFEST},
                     "package member inventory differs from manifest")
            _require(manifest.get("files_sha256") == _identity(expected_files), "package manifest inventory hash differs")
            files = {}
            for name, expected in expected_files.items():
                with archive.open(name) as stream:
                    actual = _sha_stream(stream)
                _require(actual == expected, "packaged file hash mismatch: " + name)
                files[name] = actual
            analysis = _analyze(files, archive.read)
            # Missing work roots cannot be inferred from empty ZIP directories; all
            # nonempty work expectations are independently checked above.
            if {"path": "work/", "reason": "missing"} in manifest.get("omissions", []):
                analysis["omissions"].append({"path": "work/", "reason": "missing"})
                analysis["completeness"] = "partial"
            for key in ("completeness", "omissions", "review_index_sha256", "expected_files", "turns", "attempt_status"):
                _require(manifest.get(key) == analysis[key], "package completeness declaration differs: " + key)
            notice = archive.read(NOTICE).decode("utf-8")
            _require(notice.startswith(analysis["completeness"].upper() + " REVIEW PACKAGE\n"),
                     "package status notice differs from manifest")
            _require(not require_complete or analysis["completeness"] == "complete",
                     "package is explicitly partial; inspect package-manifest.json omissions")
            return {"package": str(package), "completeness": analysis["completeness"],
                    "file_count": len(expected_files), "files_sha256": manifest["files_sha256"],
                    "review_index_sha256": analysis["review_index_sha256"], "omissions": analysis["omissions"]}
    except (zipfile.BadZipFile, KeyError, UnicodeError) as exc:
        raise ValueError("invalid review package: " + str(exc)) from exc
