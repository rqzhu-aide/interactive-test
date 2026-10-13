"""Adaptive consultation adapter. A user actor supplies replies; a separate reviewer grades."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import uuid

from claude_transport import capture, invoke, validate_loading_config
from consultation_observer import (CAPABILITY as LOOP_CAPABILITY, PRESENTATION_CAPABILITY, AGENT_REPLY_CAPABILITY, evaluate_frames,
                                   retained_frames, public_reply_correspondence, public_presentation_check)
from consultation_v8 import (FORMAT as V8_FORMAT, PROFILE as V8_LOOP_PROFILE, decode_journal,
                             prepared_reply, prepared_path, status_state)
from source_release import validate_source_prerequisite, validate_release_receipts, source_release_observations
from package_evidence import export_package, check_package, candidate_loading_check

ACTOR_UPDATES = ("knowledge_updates", "belief_updates", "decision_updates")
TESTER_VERSION = "8.3.7"
CONSULTANT_VERSIONS = ("7.0.0", "7.0.1", "7.0.2", "7.0.4", "7.0.5", "7.0.6", "7.0.7", "7.0.8", "7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6", "8.0.0", "8.0.1", "8.0.2", "8.0.3", "8.0.4", "8.0.5", "8.0.6", "8.0.7")
EXCHANGE_CAPABILITY = "durable-exchanges-v1"
USER_QUESTION_CAPABILITY = "user-question-routing-v1"
V8_CAPABILITIES = {"canonical-memory-v8", "content-authoring-v8", "six-section-brief-v8", "exact-record-read-v8",
                   "agent-recorded-reply-v1", "actual-reply-reconciliation-v1", "four-section-responses-v1"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def member(root, relative):
    """Portable fixture paths, without traversal, alternate streams or link escapes."""
    rel = PurePosixPath(relative)
    require(isinstance(relative, str) and relative and "\\" not in relative and ":" not in relative
            and not rel.is_absolute() and all(p not in ("..", ".") for p in relative.split("/")),
            "invalid relative path: " + str(relative))
    root = Path(root).resolve()
    target = root.joinpath(*rel.parts)
    require(target.resolve().is_relative_to(root), "path escapes root")
    current = target
    while current != root:
        require(not current.is_symlink() and not (hasattr(current, "is_junction") and current.is_junction()),
                "links are not fixture/evidence files: " + str(current))
        current = current.parent
    return target


def inventory(root):
    root = Path(root)
    require(root.is_dir(), "missing directory: " + str(root))
    result = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        member(root, name)
        if path.is_file():
            # Imports create ambient bytecode, not new fixture or review evidence.
            if "__pycache__" in Path(name).parts and path.suffix == ".pyc":
                continue
            result[name] = digest(path)
    return result


def validate_reply_bounds(case, actor=None, config=None):
    if "minimum_consultant_replies" not in case:
        require(case.get("edition") != "case-specific-continuity-stress-v1",
                "bounded stress case requires minimum_consultant_replies: 8")
        return
    limits = case.get("run_limits")
    require(type(case["minimum_consultant_replies"]) is int
            and case["minimum_consultant_replies"] == 8
            and isinstance(limits, dict)
            and type(limits.get("consultant_turns")) is int
            and limits["consultant_turns"] == 12,
            "bounded stress case requires 8 to 12 consultant replies")
    if actor is not None:
        bounds = actor.get("consultant_reply_bounds")
        require(isinstance(bounds, dict) and set(bounds) == {"minimum", "maximum"}
                and all(type(bounds[key]) is int for key in bounds)
                and bounds == {"minimum": 8, "maximum": 12},
                "actor bounds differ from frozen stress case")
    if config is not None:
        limits = config.get("limits")
        require(isinstance(limits, dict)
                and type(limits.get("consultant_turns")) is int
                and limits["consultant_turns"] == 12,
                "actual run configuration must use the frozen 12-reply cap")


def delivered_reply_count(attempt):
    count = 0
    for path in sorted((attempt / "events").glob("*/public.json")):
        public = read(path)
        transport_path = path.parent / "transport/transport.json"
        if not transport_path.is_file():
            continue
        transport = read(transport_path)
        message = public.get("assistant")
        if (isinstance(message, str) and message.strip()
                and "error" in transport and transport["error"] is None
                and transport.get("message") == message):
            count += 1
    return count


def validate_case(case):
    manifest = read(case / "case.json")
    require(manifest["schema_version"] == 1, "unsupported case schema")
    require(manifest.get("completion_contract", "focused") in ("focused", "full_report"),
            "unsupported completion contract")
    actual = inventory(case)
    del actual["case.json"]
    require(actual == manifest["files"], "case file identity mismatch (including unexpected files)")
    actor = read(member(case, manifest["actor"]))
    reviewer = read(member(case, manifest["reviewer"]))
    validate_reply_bounds(manifest, actor)
    reply_limits = manifest.get("reply_limits")
    if manifest.get("suite_version") in ("7.0.14", "7.3.0", "7.3.3", "7.3.4", "8.0.0", "8.1.0", "8.1.1", "8.2.0"):
        require(reply_limits == {"max_words": 50, "max_items": 2},
                "current suite requires 50-word and two-item limits")
    if reply_limits is not None:
        require(reply_limits == actor.get("reply_limits") == actor.get("persona_profile", {}).get("reply_limits"),
                "reply limits differ across case and actor")
    persona_fields = {"world", "world_id", "world_version", "persona_id"}
    if persona_fields & manifest.keys():
        require(persona_fields <= manifest.keys(), "incomplete persona/world identity")
        require(all(isinstance(manifest[key], str) and manifest[key].strip() for key in persona_fields),
                "persona/world identity must be nonempty strings")
        require(manifest["world"] in actual and not manifest["world"].startswith("public/"),
                "world dossier must be private and bound to manifest")
        world = read(member(case, manifest["world"]))
        require(all(world.get(key) == manifest[key] for key in ("world_id", "world_version")),
                "world identity mismatch")
        require(actor.get("persona_id") == manifest["persona_id"], "actor persona identity mismatch")
    source_ids, destinations = set(), set()
    problem_sources = ({s["id"]: s for s in read(case / "problem.json")["sources"]}
                       if "problem.json" in actual else None)
    actor_sources = {s["source_id"]: s for s in actor["sources"]}
    protected_files = {s["file"]: s["release_prerequisite"] for s in (problem_sources or {}).values()
                       if "release_prerequisite" in s}
    for source in manifest["sources"]:
        require(source["id"] not in source_ids, "duplicate source ID")
        require(source["destination"].casefold() not in destinations, "duplicate public destination")
        source_ids.add(source["id"])
        destinations.add(source["destination"].casefold())
        require(source["file"].startswith("public/"), "source must be explicitly public")
        require(source["file"] in actual, "source not bound to manifest")
        member(case, source["destination"])
        require(source["destination"].split("/")[0] not in (".claude", "consultation"), "reserved destination")
        require(source["availability"] in ("initial", "on_request"), "invalid availability")
        validate_source_prerequisite(source)
        if source["file"] in protected_files:
            require(source.get("release_prerequisite") == protected_files[source["file"]],
                    "protected source file cannot bypass its release prerequisite")
        for declared in (actor_sources.get(source["id"], {}),
                         problem_sources.get(source["id"], {}) if problem_sources is not None else source):
            require(("release_prerequisite" in source) == ("release_prerequisite" in declared)
                    and source.get("release_prerequisite") == declared.get("release_prerequisite"),
                    "source prerequisite differs across frozen case, actor or problem")
    require(set(protected_files) <= {s["file"] for s in manifest["sources"]}, "protected problem source is missing")
    require({s["source_id"] for s in actor["sources"]} == source_ids, "actor/source mismatch")
    for field, key in (("facts", "fact_id"), ("rules", "rule_id")):
        ids = [item[key] for item in actor[field]]
        require(len(ids) == len(set(ids)), "duplicate actor IDs")
    criteria = [item["id"] for item in reviewer["criteria"]]
    require(criteria and len(criteria) == len(set(criteria)), "missing or duplicate criteria")
    request = member(case, manifest["initial_message"]).read_text(encoding="utf-8")
    require("causal-consultant" in request, "initial request must invoke consultant")
    if reply_limits is not None:
        require(len(request.split()) <= reply_limits["max_words"], "initial request exceeds word limit")
    oracle = subprocess.run([sys.executable, str(member(case, manifest["oracle_check"]))],
                            cwd=case, capture_output=True, timeout=30)
    require(oracle.returncode == 0, "independent fixture self-check failed: " + oracle.stderr.decode(errors="replace"))
    return manifest


def candidate_inventory(candidate):
    package = read(candidate / "package.json")  # Required even though absent from npm's explicit files list.
    require(package["version"] in CONSULTANT_VERSIONS,
            "this observation profile requires consultant " + ", ".join(CONSULTANT_VERSIONS))
    result = {"package.json": digest(candidate / "package.json")}
    for entry in package["files"]:
        path = member(candidate, entry)
        if path.is_dir():
            result.update({entry + "/" + name: sha for name, sha in inventory(path).items()})
        else:
            result[entry] = digest(path)
    return dict(sorted(result.items()))


def validate_config(config):
    allowed = {"claude_command", "node_command", "model", "allowed_tools", "forward_subagent_text",
               "max_agent_turns_per_call", "call_timeout_seconds", "limits", "mode", "host_evidence", "project_root",
               "reviewer_model", "actor_runtime", "actor_model", "candidate_loading"}
    require(not set(config) - allowed, "unknown configuration keys")
    if "reviewer_model" in config:
        require(isinstance(config["reviewer_model"], str) and config["reviewer_model"].strip(),
                "reviewer_model must identify the reviewer's model")
    if {"actor_runtime", "actor_model"} & set(config):
        require("actor_runtime" in config and "actor_model" in config,
                "actor binding needs both actor_runtime and actor_model")
        require(config["actor_runtime"] in ("claude", "kimi", "pi"), "unknown actor_runtime")
        require(isinstance(config["actor_model"], str) and config["actor_model"].strip(),
                "actor_model must identify the CLI actor's model")
    for key in ("claude_command", "node_command"):
        require(isinstance(config[key], list) and config[key] and
                all(isinstance(x, str) and x for x in config[key]), key + " must be an argv prefix")
    validate_loading_config(config)
    # An isolation wrapper is permitted, but it cannot smuggle in Claude identity/permission flags.
    forbidden = ("--continue", "--resume", "--session-id", "--fork-session", "--no-session-persistence",
                 "--dangerously-skip-permissions", "--allow-dangerously-skip-permissions", "--permission-mode")
    require(not any(x.split("=")[0] in forbidden for x in config["claude_command"]), "unsafe transport override")
    require(config["mode"] in ("diagnostic", "verified_host"), "unknown mode")
    for value in (config["call_timeout_seconds"], config["max_agent_turns_per_call"], *config["limits"].values()):
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, "limits must be positive finite numbers")
    require(set(config["limits"]) == {"consultant_turns", "active_seconds", "elapsed_seconds"}, "wrong whole-run limits")
    require(type(config["limits"]["consultant_turns"]) is int and type(config["max_agent_turns_per_call"]) is int,
            "turn limits must be integers")
    if "project_root" in config:
        require(isinstance(config["project_root"], str) and config["project_root"],
                "project_root must be a work-relative path, or . for the work root")
        if config["project_root"] != ".":
            root = config["project_root"]
            require("\\" not in root and ":" not in root and not PurePosixPath(root).is_absolute()
                    and all(part not in ("", ".", "..") for part in root.split("/")),
                    "project_root must be a canonical contained relative path")
    if config["mode"] == "verified_host":
        require(config.get("host_evidence"), "verified_host requires existing host smoke/isolation evidence directory")


def candidate_observation_profile(candidate, config):
    profile = {"consultant_version": read(candidate / "package.json")["version"],
               "enforcement": "observational_only", "capabilities": [], "user_question_routing": False,
               "consultation_loop": False, "intact_reply_recovery": False, "source_attributed_memory": False,
               "deferred_release": False, "assisted_authoring": False, "claude_transcript_capture": False, "agent_recorded_reply": False}
    if profile["consultant_version"] in ("8.0.0", "8.0.1", "8.0.2", "8.0.3", "8.0.4", "8.0.5", "8.0.6", "8.0.7"):
        version = profile["consultant_version"]
        probe = subprocess.run(config["node_command"] + [str(candidate / "scripts/project.cjs"), "capabilities"],
                               cwd=candidate, capture_output=True, timeout=30)
        require(probe.returncode == 0, version + " consultant capability probe failed")
        capability = json.loads(probe.stdout)
        require(isinstance(capability, dict) and capability.get("ok") is True
                and capability.get("version") == version and capability.get("journal_schema") == 8
                and capability.get("default_journal_format") == V8_FORMAT,
                version + " consultant does not declare the v8 journal profile")
        declared = capability.get("capabilities")
        require(isinstance(declared, list) and all(isinstance(item, str) for item in declared)
                and V8_CAPABILITIES <= set(declared), version + " consultant lacks required v8 capabilities")
        # The nested legacy declaration describes old journals, not cumulative v8 requirements.
        return {"consultant_version": version, "enforcement": "observational_only",
                "profile": V8_LOOP_PROFILE, "journal_format": V8_FORMAT,
                "capabilities": declared, "capability_probe": capability,
                "consultation_loop": True, "agent_recorded_reply": True,
                "public_presentation": "four-section-responses-v1",
                "public_presentation_renderer": "lead-markdown-v11",
                "public_presentation_option_max_words": 50 if version in ("8.0.1", "8.0.2", "8.0.3", "8.0.4", "8.0.5", "8.0.6", "8.0.7") else 100}
    if profile["consultant_version"] in ("7.0.5", "7.0.6", "7.0.7", "7.0.8", "7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
        probe = subprocess.run(config["node_command"] + [str(candidate / "scripts/project.cjs"), "capabilities"],
                               cwd=candidate, capture_output=True, timeout=30)
        require(probe.returncode == 0, profile["consultant_version"] + " consultant capability probe failed")
        capability = json.loads(probe.stdout)
        require(isinstance(capability, dict) and isinstance(capability.get("capabilities"), list)
                and all(isinstance(item, str) for item in capability["capabilities"])
                and EXCHANGE_CAPABILITY in capability["capabilities"],
                profile["consultant_version"] + " consultant lacks " + EXCHANGE_CAPABILITY)
        profile["capabilities"] = capability["capabilities"]
        profile["capability_probe"] = capability
        profile["user_question_routing"] = USER_QUESTION_CAPABILITY in capability["capabilities"]
        profile["consultation_loop"] = LOOP_CAPABILITY in capability["capabilities"]
        profile["captured_delivery"] = "captured-delivery-v1" in capability["capabilities"]
        profile["proposal_preflight"] = "proposal-preflight-v1" in capability["capabilities"]
        profile["intact_reply_recovery"] = "intact-reply-recovery-v1" in capability["capabilities"]
        profile["source_attributed_memory"] = "source-attributed-memory-v1" in capability["capabilities"]
        profile["reply_reconciliation"] = "reply-reconciliation-v1" in capability["capabilities"]
        profile["case_brief"] = "case-brief-v1" in capability["capabilities"]
        profile["compact_proposals"] = "compact-proposals-v1" in capability["capabilities"]
        profile["concise_authoring"] = "concise-authoring-v1" in capability["capabilities"]
        profile["conversational_responses"] = "conversational-responses-v1" in capability["capabilities"]
        profile["deferred_release"] = "deferred-release-v1" in capability["capabilities"]
        profile["assisted_authoring"] = "assisted-authoring-v1" in capability["capabilities"]
        profile["claude_transcript_capture"] = "claude-transcript-capture-v1" in capability["capabilities"]
        for name in ("operational-summary", "report-deliverables", "report-presentation-adjustment"):
            profile[name.replace("-", "_")] = name + "-v1" in capability["capabilities"]
        if profile["consultant_version"] in ("7.0.7", "7.0.8", "7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["consultation_loop"], profile["consultant_version"] + " consultant lacks " + LOOP_CAPABILITY)
        if profile["consultant_version"] in ("7.0.8", "7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["captured_delivery"], profile["consultant_version"] + " consultant lacks captured-delivery-v1")
            require(profile["proposal_preflight"], profile["consultant_version"] + " consultant lacks proposal-preflight-v1")
        if profile["consultant_version"] in ("7.0.9", "7.0.10", "7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["intact_reply_recovery"], profile["consultant_version"] + " consultant lacks intact-reply-recovery-v1")
            require(profile["source_attributed_memory"], profile["consultant_version"] + " consultant lacks source-attributed-memory-v1")
        if profile["consultant_version"] in ("7.0.11", "7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["reply_reconciliation"], profile["consultant_version"] + " consultant lacks reply-reconciliation-v1")
            require(profile["compact_proposals"], profile["consultant_version"] + " consultant lacks compact-proposals-v1")
            require(isinstance(capability.get("renderers"), list)
                    and "lead-markdown-v5" in capability["renderers"], profile["consultant_version"] + " consultant lacks lead-markdown-v5")
        if profile["consultant_version"] in ("7.0.12", "7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["concise_authoring"], profile["consultant_version"] + " consultant lacks concise-authoring-v1")
        if profile["consultant_version"] in ("7.0.13", "7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["conversational_responses"], profile["consultant_version"] + " consultant lacks conversational-responses-v1")
            require(isinstance(capability.get("renderers"), list)
                    and "lead-markdown-v6" in capability["renderers"], profile["consultant_version"] + " consultant lacks lead-markdown-v6")
        if profile["consultant_version"] in ("7.2.0", "7.3.0", "7.3.1", "7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["deferred_release"], profile["consultant_version"] + " consultant lacks deferred-release-v1")
        if profile["consultant_version"] in ("7.4.0", "7.4.1", "7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require(profile["assisted_authoring"], profile["consultant_version"] + " consultant lacks assisted-authoring-v1")
            require(profile["claude_transcript_capture"], profile["consultant_version"] + " consultant lacks claude-transcript-capture-v1")
        if profile["consultant_version"] in ("7.5.0", "7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            for name in ("operational-summary", "report-deliverables", "report-presentation-adjustment"):
                require(profile[name.replace("-", "_")], profile["consultant_version"] + " consultant lacks " + name + "-v1")
        if profile["consultant_version"] in ("7.5.1", "7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require("lead-markdown-v7" in capability["renderers"],
                    profile["consultant_version"] + " consultant lacks lead-markdown-v7")
        if profile["consultant_version"] in ("7.5.2", "7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            require("lead-markdown-v8" in capability["renderers"],
                    profile["consultant_version"] + " consultant lacks lead-markdown-v8")
        if profile["consultant_version"] in ("7.5.3", "7.5.4", "7.5.5", "7.5.6"):
            for name in (PRESENTATION_CAPABILITY, "message-bound-delivery-v2", "pending-intake-v1"):
                require(name in capability["capabilities"], profile["consultant_version"] + " consultant lacks " + name)
            require("lead-markdown-v9" in capability["renderers"],
                    profile["consultant_version"] + " consultant lacks lead-markdown-v9")
            profile["public_presentation"] = PRESENTATION_CAPABILITY
            profile["public_presentation_renderer"] = "lead-markdown-v9"
        if profile["consultant_version"] in ("7.5.4", "7.5.5", "7.5.6"):
            require("visible-scope-answers-v1" in capability["capabilities"],
                    profile["consultant_version"] + " consultant lacks visible-scope-answers-v1")
            require("lead-markdown-v10" in capability["renderers"],
                    profile["consultant_version"] + " consultant lacks lead-markdown-v10")
            profile["public_presentation_renderer"] = "lead-markdown-v10"
        if profile["consultant_version"] in ("7.5.5", "7.5.6"):
            require("section-item-labels-v1" in capability["capabilities"],
                    profile["consultant_version"] + " consultant lacks section-item-labels-v1")
            require("lead-markdown-v11" in capability["renderers"],
                    profile["consultant_version"] + " consultant lacks lead-markdown-v11")
            profile["public_presentation_renderer"] = "lead-markdown-v11"
        if profile["consultant_version"] == "7.5.6":
            require(AGENT_REPLY_CAPABILITY in capability["capabilities"], "7.5.6 consultant lacks " + AGENT_REPLY_CAPABILITY)
            profile["agent_recorded_reply"] = True
    return profile


def preflight(case, candidate, config):
    require(sys.version_info >= (3, 10), "shared Python 3.10+ required")
    validate_config(config)
    require("candidate_loading" in config,
            "new attempts require candidate_loading: claude_explicit for native Claude, "
            "diagnostic_discovery for deliberate discovery, or adapter for an explicitly selected wrapper contract")
    node_probe = subprocess.run(config["node_command"] + ["-p", "process.versions.node"],
                                capture_output=True, timeout=15)
    require(node_probe.returncode == 0, "shared Node cannot run")
    node_version = node_probe.stdout.decode().strip()
    require(tuple(int(part) for part in node_version.split(".")[:3]) >= (18, 18, 0), "shared Node 18.18+ required")
    manifest = validate_case(case)
    validate_reply_bounds(manifest, config=config)
    files = candidate_inventory(candidate)
    checked = subprocess.run(config["node_command"] + [str(candidate / "scripts/validate.cjs")],
                             cwd=candidate, capture_output=True, timeout=60)
    require(checked.returncode == 0, "consultant package validation failed: " + checked.stdout.decode(errors="replace"))
    validation = json.loads(checked.stdout)
    package_sha = hashlib.sha256("".join(name + "\t" + sha + "\n" for name, sha in files.items()).encode()).hexdigest()
    require(validation["ok"] and validation["package_sha256"] == package_sha, "candidate inventory mismatch")
    help_result = subprocess.run(config["node_command"] + [str(candidate / "scripts/project.cjs"), "help"],
                                 cwd=candidate, capture_output=True, timeout=30)
    require(help_result.returncode == 0, "consultant project helper cannot load")
    return {"tester_version": TESTER_VERSION, "case_manifest": manifest, "case_sha256": digest(case / "case.json"),
            "candidate_files": files, "candidate_validation": validation,
            "observation_profile": candidate_observation_profile(candidate, config),
            "configuration": config, "loading_setup": loading_setup(config),
            "python": sys.version, "node": node_version}


def loading_setup(config):
    mode = config["candidate_loading"]
    return {"candidate_loading": mode, "qualification": {
        "claude_explicit": "Staged entry bound on fresh and resumed calls; actual helper/reference paths and host isolation still need evidence.",
        "diagnostic_discovery": "Discovery is deliberately diagnostic; staging alone does not establish which skill executes.",
        "adapter": "The selected wrapper owns loading; its actual candidate, resume and isolation evidence must be reviewed.",
    }[mode]}


@contextmanager
def locked(attempt):
    lock = attempt / "operator.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValueError("another operation or interrupted operator holds the lock; inspect before recovery")
    try:
        stream.write(str(time.time()))
        stream.close()
        yield
    finally:
        lock.unlink()


def start(case, candidate, config, attempt, work):
    require(not attempt.exists() and not work.exists(), "attempt and work must both be fresh paths")
    roots = [attempt, work, case, candidate]
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots) for b in roots[i + 1:]), "case, candidate, attempt and work must not overlap")
    attempt.mkdir(parents=True)
    try:
        frozen = preflight(case, candidate, config)
        if config.get("host_evidence"):
            host = Path(config["host_evidence"]).resolve()
            require(not any(host.is_relative_to(p) or p.is_relative_to(host) for p in (work, attempt)), "host evidence overlaps run")
            frozen["host_files"] = inventory(host)
            require(frozen["host_files"], "empty host evidence")
            shutil.copytree(host, attempt / "host")
        shutil.copytree(case, attempt / "case")
        work.mkdir(parents=True)
        skill = work / ".claude/skills/causal-consultant"
        for name in frozen["candidate_files"]:
            destination = member(skill, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate / name, destination)
        public = {}
        for source in frozen["case_manifest"]["sources"]:
            if source["availability"] == "initial":
                destination = member(work, source["destination"])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(case / source["file"], destination)
                public[source["destination"]] = digest(destination)
        frozen["adapter_files"] = {
            name: digest(Path(__file__).parent / name) for name in ("session_driver.py", "claude_transport.py", "consultation_observer.py", "consultation_v8.py", "source_release.py", "package_evidence.py", "room_actor.py", "room_reviewer.py")}
        testing_root = Path(__file__).resolve().parents[1]
        testing_files = [testing_root / "SKILL.md", testing_root / "README.md"]
        testing_files += list((testing_root / "references").glob("*"))
        testing_files += [testing_root / "scripts" / name for name in frozen["adapter_files"]]
        frozen["testing_files"] = {}
        for source in testing_files:
            name = source.relative_to(testing_root).as_posix()
            destination = member(attempt / "testing", name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            frozen["testing_files"][name] = digest(destination)
        frozen["initial_public_files"] = public
        frozen["review_package_profile"] = "review-observations-v1"
        frozen["created_at"] = time.time()
        frozen["no_token_or_cost_cap_reason"] = "Exploratory utility test; preserve raw provider usage without assumed aggregation."
        write(attempt / "freeze.json", frozen)
        (attempt / "events").mkdir()
        write(attempt / "state.json", {"status": "ready", "session_id": str(uuid.uuid4()), "work": str(work),
                                       "turns": 0, "active_seconds": 0, "started_at": None,
                                       "public_files": public, "released_sources": [], "breaches": []})
        # Cheap capability evidence only; does not establish loading, isolation or resume.
        probe = capture(config["claude_command"] + ["--version"], work, "", 15, attempt / "claude-version")
        require(not probe["error"] and probe["exit_code"] == 0, "Claude command version probe failed; inspect retained startup evidence")
        capture(config["claude_command"] + ["--help"], work, "", 15, attempt / "claude-help")
        return {"attempt": str(attempt), "work": str(work), "status": "ready", "initial_message_sent": False,
                "loading_setup": frozen["loading_setup"]}
    except Exception as exc:
        write(attempt / "startup-error.json", {"error": str(exc), "time": time.time()})
        if (attempt / "state.json").exists():
            state = read(attempt / "state.json")
            state["status"] = "execution_error"
            write(attempt / "state.json", state)
        raise


def integrity(attempt, state, frozen):
    require(digest(attempt / "case/case.json") == frozen["case_sha256"], "frozen case changed")
    require(inventory(attempt / "case") == {"case.json": frozen["case_sha256"], **frozen["case_manifest"]["files"]}, "frozen inputs changed")
    skill = Path(state["work"]) / ".claude/skills/causal-consultant"
    require(inventory(skill) == frozen["candidate_files"], "staged consultant changed")
    for name, sha in state["public_files"].items():
        path = member(Path(state["work"]), name)
        require(path.is_file() and digest(path) == sha, "released public input changed: " + name)
    require(all(digest(Path(__file__).parent / name) == sha for name, sha in frozen["adapter_files"].items()), "adapter changed during attempt")


def project_binding(files, config):
    """Bind observations to an explicit root or a unique captured journal, never a guessed folder."""
    candidates = sorted({str(PurePosixPath(name).parent) for name in files
                         if PurePosixPath(name).name == "journal.jsonl"
                         and PurePosixPath(name).parts[0] != ".claude"})
    explicit = config.get("project_root")
    selected = explicit if explicit is not None else (candidates[0] if len(candidates) == 1 else None)
    return {"status": "bound" if selected in candidates else ("ambiguous" if len(candidates) > 1 else "missing"),
            "method": "explicit" if explicit is not None else "unique_journal",
            "project_root": selected, "candidate_roots": candidates,
            "scope": "Captured work tree excluding the staged .claude runtime; no project mutation."}


def observe_v8_exchange(event, observation_profile=None):
    """Retain public text first; saved drafts and later recordings are private comparison evidence."""
    result = {"profile": V8_LOOP_PROFILE, "enforcement": "observational_only", "status": "unobserved",
              "evidence_kind": "independent_public_transcript", "native_identity_verified": False,
              "agent_recording_status": "evaluated_retrospectively_in_consultation_loop",
              "scope": "Actual public text is primary. Drafts and optional recordings do not establish delivery, permission or scientific validity."}
    frame = {"event": event.name, "journal_format": V8_FORMAT, "journal": []}
    try:
        frame["public"] = read(event / "public.json")
        message = frame["public"].get("assistant")
        require(isinstance(message, str), "No successful final response was returned.")
        result.update(status="public_reply_observed", actual_response_sha256=hashlib.sha256(message.encode("utf-8")).hexdigest(),
                      reason="Actual public text is retained independently of prepared or recorded replies.")
        process = read(event / "project-status/process.json")
        require(process["exit_code"] == 0 and not process["error"], "project status did not succeed")
        status = read(event / "project-status/stdout.txt")
        project = status_state(status)
        require(project.get("state_meta", {}).get("format") == V8_FORMAT, "project status does not describe a v8 case")
        frame["project_state"] = project
        binding = read(event / "project-binding.json")
        require(binding["status"] == "bound", "No bound v8 project was captured.")
        prefix = "" if binding["project_root"] == "." else binding["project_root"] + "/"
        frame["root_prefix"] = prefix
        journal_path = member(event / "work-snapshot", prefix + "journal.jsonl")
        rows = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        decoded = decode_journal(rows)
        frame["journal"] = rows
        result["retained_reply_recordings"] = [
            {"ref": entry["id"], "source_kind": entry["data"].get("source", {}).get("kind"),
             **{key: entry["data"][key] for key in ("before_user", "prepared", "capture_ref", "supersedes_recording_ref")
                if key in entry["data"]}}
            for entry in decoded["entries"] if entry["type"] == "reply_recorded"]
        indexes = project.get("exchanges", [])
        exchange = prepared_reply(rows, indexes[-1]["ref"] if indexes else None)
        require(exchange is not None, "No prepared reply was captured; the public reply remains available.")
        result.update(prepared_ref=exchange["ref"], responds_to=exchange.get("responds_to"), renderer=exchange.get("renderer"),
                      user_questions=exchange.get("response", {}).get("user_questions"),
                      explanations=exchange.get("response", {}).get("explanations"))
        prior = event.parent / f"{int(event.name) - 1:03d}" / "project-status/stdout.txt"
        if prior.is_file():
            prior_exchanges = status_state(read(prior)).get("exchanges", [])
            result["new_since_previous_observation"] = not any(item.get("ref") == exchange["ref"] for item in prior_exchanges)
        try:
            relative = prefix + prepared_path(exchange["ref"])
            body = member(event / "work-snapshot", relative).read_bytes().decode("utf-8")
            exported_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            correspondence = public_reply_correspondence(message, exported_hash, body)
            # v8 exports add one final newline to the renderer's returned text.
            if correspondence["status"] == "body_changed" and body.endswith("\n"):
                rendered = body[:-1]
                rendered_match = public_reply_correspondence(message, hashlib.sha256(rendered.encode("utf-8")).hexdigest(), rendered)
                if rendered_match["status"] in ("exact", "wrapped", "ambiguous_body"):
                    correspondence = {**rendered_match, "export_final_newline_omitted": True}
            result.update(prepared_body_path=relative, retained_export_sha256=exported_hash,
                          draft_body_correspondence=correspondence)
        except (ValueError, OSError, UnicodeError) as exc:
            result["draft_body_correspondence"] = {"status": "unobserved", "reason": str(exc), "semantic_review_required": True}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result["prepared_observation_reason"] = str(exc)
        if result["status"] == "unobserved":
            result["reason"] = str(exc)
    result["public_presentation_check"] = public_presentation_check([frame], "lead-markdown-v11", agent_recorded_reply=True,
        option_max_words=(observation_profile or {}).get("public_presentation_option_max_words", 100))
    return result


def observe_exchange(event, observation_profile=None):
    """Compare actual final bytes with a prepared exchange; do not write delivery or grade science."""
    if (observation_profile or {}).get("journal_format") == V8_FORMAT:
        write(event / "exchange-observation.json", observe_v8_exchange(event, observation_profile))
        return
    result = {"profile": EXCHANGE_CAPABILITY, "enforcement": "observational_only", "status": "unobserved",
              "reason": "No successful durable-exchange observation is available.",
              "scope": "Actual public reply/body correspondence; wrappers need semantic review. Not delivery/read proof or scientific validation."}
    try:
        process = read(event / "project-status/process.json")
        require(process["exit_code"] == 0 and not process["error"], "project status did not succeed")
        status = read(event / "project-status/stdout.txt")
        if status.get("journal_format") == V8_FORMAT:
            write(event / "exchange-observation.json", observe_v8_exchange(event, observation_profile))
            return
        work = status.get("views", {}).get("work", {})
        exchange = next((item for item in work.get("exchanges", [])
                         if item["exchange_id"] == work.get("current_exchange_ref")), None)
        require(exchange is not None, "No current durable exchange was captured.")
        result.update(renderer=exchange.get("renderer"),
                      user_questions=exchange.get("response", {}).get("user_questions"),
                      explanations=exchange.get("response", {}).get("explanations"),
                      pending_user_question_refs=work.get("pending_user_question_refs"))
        message = read(event / "public.json")["assistant"]
        require(isinstance(message, str), "No successful final response was returned.")
        agent_recorded_reply = bool((observation_profile or {}).get("agent_recorded_reply"))
        result["public_presentation_check"] = public_presentation_check([{
            "event": event.name, "public": read(event / "public.json"),
            "journal": [{"sequence": 1, "payload": {"exchange": exchange}}]}], agent_recorded_reply=agent_recorded_reply)
        actual = hashlib.sha256(message.encode("utf-8")).hexdigest()
        canonical_body = None
        try:
            binding = read(event / "project-binding.json")
            prefix = "" if binding["project_root"] == "." else binding["project_root"] + "/"
            relative = prefix + "exchanges/" + exchange["exchange_id"] + "/response.md"
            if binding["status"] == "bound":
                canonical_body = member(event / "work-snapshot", relative).read_bytes().decode("utf-8")
        except (ValueError, OSError, KeyError, TypeError):
            pass  # Older snapshots retain the bounded header/hash comparison.
        correspondence = public_reply_correspondence(message, exchange["response_sha256"], canonical_body)
        prior = event.parent / f"{int(event.name) - 1:03d}" / "project-status/stdout.txt"
        new_exchange = None
        if prior.is_file():
            prior_work = read(prior).get("views", {}).get("work", {})
            new_exchange = exchange["exchange_id"] != prior_work.get("current_exchange_ref")
        result.update(exchange_id=exchange["exchange_id"], exchange_turn_id=exchange["turn_id"],
                      exchange_event_ref=exchange["event_ref"], expected_response_sha256=exchange["response_sha256"],
                      actual_response_sha256=actual, new_since_previous_observation=new_exchange,
                      body_correspondence=correspondence,
                      status={"exact": "matched", "wrapped": "wrapped", "body_changed": "mismatch",
                              "ambiguous_body": "mismatch"}.get(correspondence["status"], "unobserved"),
                      reason="Compared actual UTF-8 public reply and intact body with the prepared hash; surrounding prose is not automatically endorsed.")
        if agent_recorded_reply:
            result.update(status="public_reply_observed", evidence_kind="independent_public_transcript", native_identity_verified=False,
                          draft_body_correspondence=correspondence, agent_recording_status="evaluated_retrospectively_in_consultation_loop",
                          reason="Actual public text is retained independently. The prepared hash identifies a draft; later agent records are associated and reviewed across complete public turns.")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result["reason"] = str(exc)
    write(event / "exchange-observation.json", result)


def observe_project(event, state, config, observation_profile=None):
    """Retain each turn's files and read-only observations, including failed turns."""
    work = Path(state["work"])
    before = inventory(work)
    shutil.copytree(work, event / "work-snapshot")
    require(inventory(event / "work-snapshot") == before == inventory(work), "work changed while capturing evidence")
    write(event / "work-files.json", before)
    binding = project_binding(before, config)
    binding["observed_work_root"] = work.resolve().as_posix()
    if binding["status"] == "bound":
        root = work if binding["project_root"] == "." else member(work, binding["project_root"])
        binding["observed_project_root"] = root.resolve().as_posix()
    write(event / "project-binding.json", binding)
    if binding["status"] != "bound":
        write(event / "observation-skipped.json", {"reason": "project root is " + binding["status"],
                                                   "binding_ref": "project-binding.json"})
        observe_exchange(event, observation_profile)
        return
    root = work if binding["project_root"] == "." else member(work, binding["project_root"])
    helper = work / ".claude/skills/causal-consultant/scripts/project.cjs"
    for command in ("status", "context", "history", "verify"):
        remaining = config["limits"]["elapsed_seconds"] - (time.time() - state["started_at"])
        if remaining <= 0:
            write(event / "observation-skipped.json", {"reason": "elapsed limit reached", "next_command": command})
            break
        capture(config["node_command"] + [str(helper), command, "--project-root", str(root)],
                work, "", min(30, remaining), event / ("project-" + command))
    if (observation_profile or {}).get("journal_format") == V8_FORMAT:
        after = inventory(work)
        binding["observation_inventory"] = {"before_sha256": identity(before), "after_sha256": identity(after)}
        write(event / "project-binding.json", binding)
        require(after == before, "work changed during read-only project observations")
    observe_exchange(event, observation_profile)


def record_time_limits(state, config, now):
    limits = config["limits"]
    exceeded = state["active_seconds"] > limits["active_seconds"] or (
        state["started_at"] is not None and now - state["started_at"] > limits["elapsed_seconds"])
    if exceeded and "whole_run_time_limit" not in state["breaches"]:
        state["breaches"].append("whole_run_time_limit")


def validate_actor_input(attempt, state, reply):
    """Bind a declared actor invocation to retained allowed input, not proof of isolation."""
    if not state["turns"]:
        require(not reply.get("actor_context") and not reply.get("action_intents"),
                "initial dispatch has no actor invocation or selected action")
        return
    receipt = reply.get("actor_context", {})
    require(isinstance(receipt, dict) and set(receipt) == {"input_sha256", "context_id"}
            and isinstance(receipt["context_id"], str) and receipt["context_id"].strip(),
            "later replies require the actor input digest and actual actor context ID")
    require(receipt["context_id"] != state["session_id"], "actor and consultant contexts must be separate")
    sha = receipt["input_sha256"]
    require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha),
            "invalid actor input digest")
    path = attempt / "actor-inputs" / (sha + ".json")
    require(path.is_file() and digest(path) == sha, "actor input was not retained; inspect actor first")
    context = read(path)
    current = actor_view(attempt, state)
    require(context == current, "actor input is stale; inspect actor again")
    require(isinstance(reply.get("action_intents", []), list), "action_intents must be a list")
    for item in reply.get("action_intents", []):
        require(isinstance(item, dict) and item.get("kind") in ("selection", "goal_request", "decline", "defer")
                and isinstance(item.get("message_quote"), str) and item["message_quote"].strip()
                and item["message_quote"] in reply["message"], "action intent must cite actual reply text")
        fields = {"kind", "message_quote"}
        if item["kind"] == "selection":
            fields |= {"public_turn", "option_quote"}
            require(type(item.get("public_turn")) is int and 0 < item["public_turn"] <= state["turns"],
                    "a selection must name an earlier completed public turn")
            public = read(attempt / "events" / f"{item['public_turn']:03d}" / "public.json")
            require(isinstance(item.get("option_quote"), str) and item["option_quote"].strip()
                    and item["option_quote"] in (public.get("assistant") or ""),
                    "selection must quote an actually presented option")
        require(set(item) == fields, "unexpected action intent fields")


def original_release(attempt, state, sources, source_id, sha):
    """Verify the one original acquisition; a resend cannot create another."""
    source = sources[source_id]
    def retained_document(path):
        try:
            document = read(path)
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError("resend original release evidence unreadable: "
                             + path.relative_to(attempt).as_posix()) from exc
        require(isinstance(document, dict), "resend original release evidence must be a JSON object: "
                + path.relative_to(attempt).as_posix())
        return document
    originals = []
    for turn in range(1, state["turns"] + 1):
        event = attempt / "events" / f"{turn:03d}"
        entry = retained_document(event / "releases.json").get(source_id)
        if entry is not None:
            require(entry == {"path": source["destination"], "sha256": sha},
                    "original source release differs from frozen bytes")
            originals.append((turn, event))
    require(len(originals) == 1, "resend requires exactly one retained original release")
    turn, event = originals[0]
    snapshot = member(event / "work-snapshot", source["destination"])
    try:
        require(snapshot.is_file() and digest(snapshot) == sha,
                "resend original source snapshot changed or missing")
    except OSError as exc:
        raise ValueError("resend original source snapshot unreadable: "
                         + snapshot.relative_to(attempt).as_posix()) from exc
    if "release_prerequisite" in source:
        checks = retained_document(event / "source-release-check.json").get("verified_receipts")
        require(isinstance(checks, list) and all(isinstance(item, dict) for item in checks),
                "resend original gated receipt list is invalid")
        originals = [item for item in checks if item.get("source_id") == source_id]
        require(len(originals) == 1, "resend requires the original gated receipt")
        receipt = originals[0].get("receipt")
        require(isinstance(receipt, dict), "resend original gated receipt is invalid")
        public_turn = receipt.get("public_turn")
        require(type(public_turn) is int and 0 < public_turn < turn,
                "original gated receipt has invalid chronology")
        # Reinspect the receipt's cited evidence, not the post-response plan.
        # Its successful original check already records acquisition-time validation.
        checked = validate_release_receipts(attempt, {"turns": turn - 1,
            "work": str(attempt / "events" / f"{public_turn:03d}" / "work-snapshot")},
            sources, [source_id], [receipt])
        require(checked == originals, "original gated receipt changed")


def step(attempt, reply):
    with locked(attempt):
        state, frozen = read(attempt / "state.json"), read(attempt / "freeze.json")
        require(state["status"] == "ready", "attempt cannot send: " + state["status"])
        integrity(attempt, state, frozen)
        config, case = frozen["configuration"], frozen["case_manifest"]
        actor = read(attempt / "case" / case["actor"])
        validate_reply_bounds(case, actor, config)
        required = {"message", "fact_ids", "rule_ids", "attachments", "unanswered_questions", "fixture_gaps", "stop"}
        optional = set(ACTOR_UPDATES) | {"actor_context", "action_intents", "source_release_receipts"}
        require(required <= reply.keys() and not reply.keys() - required - optional,
                "reply record fields do not match actor contract")
        for field in required - {"message", "stop"}:
            require(isinstance(reply[field], list), field + " must be a list")
        for field in ACTOR_UPDATES:
            require(isinstance(reply.get(field, []), list), field + " must be a list")
            for change in reply.get(field, []):
                require(isinstance(change, dict) and set(change) == {"subject", "before", "after", "evidence"}
                        and all(isinstance(value, str) and value.strip() for value in change.values()),
                        "actor update needs subject, before, after and visible evidence")
        require(type(reply["stop"]) is bool, "stop must be boolean")
        for field, key, packet in (("fact_ids", "fact_id", "facts"), ("rule_ids", "rule_id", "rules")):
            require(set(reply[field]) <= {item[key] for item in actor[packet]}, "unknown " + field)
        if reply["stop"]:
            if "minimum_consultant_replies" in case:
                require(delivered_reply_count(attempt) >= case["minimum_consultant_replies"],
                        "stress actor cannot stop before 8 delivered replies; human cancellation can finalize incomplete")
            require(reply["message"] is None and not reply["attachments"], "stop sends no message or attachments")
            require(not reply.get("action_intents") and not reply.get("source_release_receipts"),
                    "stop does not select or release work")
            validate_actor_input(attempt, state, reply)
            write(attempt / "events" / (f"{state['turns'] + 1:03d}-stop.json"), reply)
            state["status"] = "awaiting_review"
            state["ended_at"] = time.time()
            record_time_limits(state, config, state["ended_at"])
            write(attempt / "state.json", state)
            return {"status": state["status"]}
        message = reply["message"]
        require(isinstance(message, str) and message.strip(), "empty actor message")
        if case.get("reply_limits") is not None:
            require(len(message.split()) <= case["reply_limits"]["max_words"],
                    "actor message exceeds word limit")
        initial = (attempt / "case" / case["initial_message"]).read_text(encoding="utf-8")
        if not state["turns"]:
            require(message == initial and not reply["fact_ids"] and not reply["attachments"], "first step must use exact frozen public request")
            require(not any(reply.get(field) for field in ACTOR_UPDATES), "initial dispatch cannot claim learned updates")
        private_markers = [str(attempt), str(attempt).replace("\\", "/"), case["actor"], case["reviewer"], "oracle.json"]
        if case.get("world"):
            private_markers.append(case["world"])
        require(not any(marker.casefold() in message.casefold() for marker in private_markers), "private path leaked into public text")
        validate_actor_input(attempt, state, reply)
        limits = config["limits"]
        remaining_elapsed = limits["elapsed_seconds"] - (time.time() - state["started_at"] if state["started_at"] else 0)
        remaining_active = limits["active_seconds"] - state["active_seconds"]
        if state["turns"] >= limits["consultant_turns"] or min(remaining_elapsed, remaining_active) <= 0:
            state["status"] = "limit_reached"
            state["ended_at"] = time.time()
            state["breaches"].append("whole_run_limit")
            write(attempt / "state.json", state)
            return {"status": state["status"]}
        sources = {item["id"]: item for item in case["sources"]}
        require(len(reply["attachments"]) == len(set(reply["attachments"])), "duplicate release")
        try:
            for source_id in reply["attachments"]:
                require(source_id in sources and sources[source_id]["availability"] == "on_request", "unauthorized source release")
                source = sources[source_id]
                destination = member(Path(state["work"]), source["destination"])
                if source_id in state["released_sources"]:
                    sha = case["files"][source["file"]]
                    require(state["public_files"].get(source["destination"]) == sha,
                            "resend source identity differs from frozen bytes")
                    original_release(attempt, state, sources, source_id, sha)
                    require(destination.is_file() and digest(destination) == sha,
                            "resend requires existing identical source bytes")
                else:
                    require(not destination.exists(), "release would overwrite a file")
            first_releases = [source_id for source_id in reply["attachments"]
                              if source_id not in state["released_sources"]]
            release_receipts = validate_release_receipts(attempt, state, sources, first_releases,
                                                        reply.get("source_release_receipts"))
        except ValueError as exc:
            rejected = attempt / "rejected-releases"
            rejected.mkdir(exist_ok=True)
            write(rejected / (str(uuid.uuid4()) + ".json"),
                  {"after_turn": state["turns"], "reply": reply, "reason": str(exc), "dispatched": False})
            raise
        event = attempt / "events" / f"{state['turns'] + 1:03d}"
        event.mkdir()  # Refuse an existing/uncertain attempt, never overwrite it.
        write(event / "actor.json", reply)
        write(event / "source-release-check.json", {"verified_receipts": release_receipts})
        state["status"] = "pending"  # Persist before staging or dispatch; interrupted delivery cannot be retried.
        state["started_at"] = state["started_at"] or time.time()
        state["turns"] += 1
        write(attempt / "state.json", state)
        try:
            released = {}
            for source_id in reply["attachments"]:
                source = sources[source_id]
                destination = member(Path(state["work"]), source["destination"])
                destination.parent.mkdir(parents=True, exist_ok=True)
                sha = case["files"][source["file"]]
                if source_id not in state["released_sources"]:
                    with destination.open("xb") as stream:
                        stream.write((attempt / "case" / source["file"]).read_bytes())
                require(destination.is_file() and digest(destination) == sha,
                        "attachment differs from frozen source bytes")
                if source_id not in state["released_sources"]:
                    state["public_files"][source["destination"]] = sha
                    state["released_sources"].append(source_id)
                    released[source_id] = {"path": source["destination"], "sha256": sha}
            write(event / "releases.json", released)
            result = invoke(config, state["work"], state["session_id"], state["turns"] == 1, message,
                            min(config["call_timeout_seconds"], remaining_active, remaining_elapsed), event / "transport")
            state["active_seconds"] += result["active_seconds"]
            state["status"] = "execution_error" if result["error"] else "ready"
            if result["error"] == "timeout":
                state["breaches"].append("call_or_remaining_time_limit")
            write(event / "public.json", {"user": message, "assistant": result["message"],
                                          "attachments": [sources[source_id]["destination"] for source_id in reply["attachments"]]})
            write(attempt / "state.json", state)
            observe_project(event, state, config, frozen.get("observation_profile"))
            if frozen.get("observation_profile", {}).get("consultation_loop"):
                write(event / "consultation-loop-observation.json", consultation_loop_check(attempt, frozen))
            state["last_activity_at"] = time.time()
            record_time_limits(state, config, state["last_activity_at"])
            if state["status"] == "ready" and state["breaches"]:
                state["status"] = "limit_reached"
            if state["status"] == "execution_error" or state["breaches"]:
                state["ended_at"] = state["last_activity_at"]
            write(attempt / "state.json", state)
            return {"status": state["status"], "message": result["message"], "error": result["error"]}
        except Exception as exc:
            write(event / "operator-error.json", {"error": str(exc), "time": time.time()})
            state["status"] = "execution_error"
            state["ended_at"] = time.time()
            record_time_limits(state, config, state["ended_at"])
            write(attempt / "state.json", state)
            # Delivery may be uncertain. Preserve the attempt and do not permit another dispatch.
            raise


def evidence(attempt, state):
    files = {"private/" + name: sha for name, sha in inventory(attempt).items()
             if name not in ("operator.lock", "review-index.json", "review-observations.json", "assessment.json", "state.json")}
    files.update({"work/" + name: sha for name, sha in inventory(Path(state["work"])).items()})
    files["state_at_review"] = identity(state)
    return {"sha256": identity(files), "files": files}


def actor_view(attempt, state):
    frozen = read(attempt / "freeze.json")
    conversation = [read(path) for path in sorted((attempt / "events").glob("*/public.json"))]
    result = {"conversation": conversation, "public_files": list(state["public_files"]),
              "actor_packet": read(attempt / "case" / frozen["case_manifest"]["actor"]),
              "reply_policy": (attempt / "testing/references/user-simulator.md").read_text(encoding="utf-8"),
              "public_file_hashes": state["public_files"]}
    if "minimum_consultant_replies" in frozen["case_manifest"]:
        result["delivered_consultant_replies"] = delivered_reply_count(attempt)
        result["remaining_consultant_replies"] = max(0, 12 - state["turns"])
    updates, disclosures = [], []
    for path in sorted((attempt / "events").glob("*/public.json")):
        record = read(path.parent / "actor.json")
        disclosures.append({"event": path.parent.name, "fact_ids": record["fact_ids"],
                            "attachments": record["attachments"],
                            "unanswered_questions": record["unanswered_questions"],
                            "action_intents": record.get("action_intents", [])})
        changes = {field: record[field] for field in ACTOR_UPDATES if record.get(field)}
        if changes:
            updates.append({"event": path.parent.name, **changes})
    if updates:
        result["actor_updates"] = updates
    if disclosures:
        result["actor_disclosures"] = disclosures
    return result


def review_observations(attempt, state, frozen, index):
    completion = (full_report_completion(attempt, state, index)
                  if frozen["case_manifest"].get("completion_contract") == "full_report" else None)
    loop = consultation_loop_check(attempt, frozen, index)
    findings = [{"id": "loop-" + identity(item),
                 "check": ("artifact_provenance" if item.get("code") == "report_output_content_role" else
                           "delivery_correspondence" if item.get("owner") == "undetermined" else "consultation_loop"),
                 "observation": item}
                for item in loop.get("findings", [])]
    for key in ("unobserved", "response_correspondence"):
        findings += [{"id": key + "-" + identity(item), "check": key, "observation": item}
                     for item in loop.get(key, []) if key != "response_correspondence" or item.get("status") != "exact"]
    presentation = loop.get("public_presentation_check", {})
    findings += [{"id": "presentation-" + identity(item), "check": "public_presentation",
                  "observation": item} for item in presentation.get("findings", [])]
    expected = [f"private/events/{turn:03d}/{name}" for turn in range(1, state["turns"] + 1)
                for name in ("public.json", "actor.json", "work-files.json", "project-binding.json",
                             "transport/command.json", "transport/request.txt", "transport/stdout.txt",
                             "transport/stderr.txt", "transport/process.json", "transport/transport.json")]
    missing = [ref for ref in expected if ref not in index["files"]]
    loading = candidate_loading_check(frozen, state, index["files"],
                                      lambda ref: (attempt / ref.removeprefix("private/")).read_bytes())
    if loading is not None:
        if loading["status"] != "matched":
            findings.append({"id": "loading-" + identity(loading), "check": "candidate_loading",
                             "observation": loading})
        missing += [item["evidence_ref"] for call in loading["calls"] for item in call["issues"]
                    if item["reason"] == "missing_indexed_capture" and item["evidence_ref"] not in missing]
    if missing:
        findings.append({"id": "capture-" + identity(missing), "check": "capture_completeness",
                         "observation": {"missing": missing, "meaning": "Unobserved evidence, not proof of consultant misconduct."}})
    for ref in sorted(index["files"]):
        if ref.startswith("private/rejected-releases/") and ref.endswith(".json"):
            findings.append({"id": "release-" + identity(ref), "check": "source_release_rejected",
                             "observation": {"evidence_ref": ref, "dispatched": False}})
    findings += [{"id": "source-" + identity(item), "check": "source_release_trace", "observation": item}
                 for item in source_release_observations(attempt, frozen, index)]
    if completion and not completion["satisfied"]:
        findings.append({"id": "completion-" + identity(completion), "check": "completion", "observation": completion})
    return {"schema_version": 1, "tester_version": TESTER_VERSION,
            "evidence_sha256": index["sha256"], "completion_check": completion,
            **({"candidate_loading_check": loading} if loading is not None else {}),
            "public_presentation_check": presentation,
            "consultation_loop_check": loop, "missing_captures": missing, "machine_findings": findings}


def inspect(attempt, view):
    with locked(attempt):
        state = read(attempt / "state.json")
        if view == "actor":
            require(state["status"] == "ready", "actor input requires a ready attempt")
            result = actor_view(attempt, state)
            folder = attempt / "actor-inputs"
            folder.mkdir(exist_ok=True)
            # The exact JSON handed to the actor is retained separately from its receipt.
            payload = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            sha = hashlib.sha256(payload).hexdigest()
            target = folder / (sha + ".json")
            if not target.exists():
                target.write_bytes(payload)
            require(digest(target) == sha, "retained actor input changed")
            return {**result, "input_sha256": sha}
        require(state["status"] != "finished", "review already finalized")
        index = evidence(attempt, state)
        observations = review_observations(attempt, state, read(attempt / "freeze.json"), index)
        write(attempt / "review-observations.json", observations)
        index["observations_sha256"] = digest(attempt / "review-observations.json")
        write(attempt / "review-index.json", index)
        return {"state": state, "evidence_sha256": index["sha256"], "index": str(attempt / "review-index.json"),
                "observations_sha256": index["observations_sha256"], "observations": observations}


def full_report_completion(attempt, state, index):
    """Check retained verification and report bytes under their journal format."""
    result = {"contract": "full_report", "satisfied": False, "reason": "", "evidence_refs": []}
    latest = f"events/{state['turns']:03d}"

    def retained(relative):
        path = member(attempt, relative)
        reference = "private/" + relative
        require(reference in index["files"] and digest(path) == index["files"][reference],
                "missing or changed completion evidence: " + relative)
        result["evidence_refs"].append(reference)
        return path

    try:
        binding = read(retained(latest + "/project-binding.json"))
        require(binding["status"] == "bound" and binding["project_root"] in binding["candidate_roots"],
                "latest project observation has no unambiguous bound root")
        project_prefix = "" if binding["project_root"] == "." else binding["project_root"] + "/"
        result["project_root"] = binding["project_root"]
        observations, processes = {}, {}
        for command in ("status", "verify"):
            prefix = latest + "/project-" + command
            process = read(retained(prefix + "/process.json"))
            processes[command] = process
            require(process["exit_code"] == 0 and not process["error"],
                    "latest project " + command + " did not succeed")
            observations[command] = read(retained(prefix + "/stdout.txt"))
            require(observations[command]["ok"] is True, "latest project " + command + " is not valid")
        project = status_state(observations["status"])
        v8 = project.get("state_meta", {}).get("format") == V8_FORMAT
        verified = observations["verify"]
        if not v8:
            require(verified["project_id"] == project["state_meta"]["project_id"] and
                    verified["last_event_id"] == project["state_meta"]["last_event_id"],
                    "project status and verification describe different journal states")
        require(verified["source_check"] in ("originals", "snapshots"), "verification mode is missing")
        result["source_check"] = verified["source_check"]

        captured_files = read(retained(latest + "/work-files.json"))
        snapshot = member(attempt, latest + "/work-snapshot")
        require(isinstance(captured_files, dict) and captured_files and inventory(snapshot) == captured_files,
                "latest work snapshot changed")
        require(inventory(Path(state["work"])) == captured_files,
                "current project differs from its latest captured verification")
        journal_path = retained(latest + "/work-snapshot/" + project_prefix + "journal.jsonl")
        project_path = retained(latest + "/work-snapshot/" + project_prefix + "project.yaml")
        if v8:
            decoded = decode_journal([json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line.strip()])
            head = decoded["entries"][-1]["id"] if decoded["entries"] else "e0"
            require(project == read(project_path) and decoded["header"]["case"] == project["state_meta"]["project_id"]
                    and head == project["state_meta"]["last_event_id"]
                    and observations["status"]["project_id"] == decoded["header"]["case"]
                    and observations["status"]["last_event_id"] == head,
                    "v8 status does not match the retained project and journal")
            observed_inventory = binding.get("observation_inventory", {})
            require(observed_inventory.get("before_sha256") == observed_inventory.get("after_sha256") == identity(captured_files),
                    "v8 verification lacks unchanged before/after inventory evidence")
            expected_work = Path(binding["observed_work_root"]).resolve()
            expected_root = expected_work if binding["project_root"] == "." else member(expected_work, binding["project_root"])
            require(Path(binding["observed_project_root"]).resolve() == expected_root,
                    "v8 captured project root does not match its work binding")
            for command in ("status", "verify"):
                command_capture = read(retained(latest + "/project-" + command + "/command.json"))
                argv = command_capture.get("argv")
                require(isinstance(argv, list) and len(argv) >= 4 and argv[-3:-1] == [command, "--project-root"]
                        and Path(argv[-1]).resolve() == expected_root
                        and Path(argv[-4]).resolve() == expected_work / ".claude/skills/causal-consultant/scripts/project.cjs"
                        and Path(command_capture["cwd"]).resolve() == expected_work
                        and processes[command].get("argv") == argv and processes[command].get("cwd") == command_capture["cwd"],
                        "v8 " + command + " capture does not bind to the retained project root")
            require(verified.get("checked_runs") == len(project["runs"]), "v8 verification run inventory differs from status")
            result["verification_binding"] = "retained_command_root_and_unchanged_work_inventory"

        reports = [run for run in project["runs"] if run["kind"] == "report"]
        require(reports, "no report run was captured")
        # Project run order is journal start order; a newer unfinished revision cannot be hidden.
        report = reports[-1]
        run_id = report["ref"] if v8 else report["run_id"]
        result["run_id"] = run_id
        require(report["status"] == "completed", "latest report run is " + report["status"])
        prefix = "runs/" + run_id + "/"
        require(report["manifest_ref"] == prefix + "manifest.json", "report manifest path does not match its run")
        manifest_path = retained(latest + "/work-snapshot/" + project_prefix + report["manifest_ref"])
        require(digest(manifest_path) == report["manifest_sha256"], "report manifest does not match its committed hash")
        manifest = read(manifest_path)
        require(manifest["kind"] == "report" and manifest["run_id"] == run_id,
                "manifest is not the completed report")
        retained(latest + "/work-snapshot/" + project_prefix + report["plan_ref"])
        require(manifest["output_paths"], "report has no manifested output")
        files = {item["path"]: item for item in manifest["files"]}
        for relative in manifest["output_paths"]:
            output = retained(latest + "/work-snapshot/" + project_prefix + prefix + relative)
            require(relative in files and output.stat().st_size > 0 and digest(output) == files[relative]["sha256"],
                    "report output is empty or does not match its manifest: " + relative)
            result["evidence_refs"].append("work/" + project_prefix + prefix + relative)
        require(all(ref in index["files"] for ref in result["evidence_refs"]), "report evidence is not bound")
        result.update(satisfied=True, reason="Latest report run is completed, verified and retained with nonempty manifested outputs.")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result["reason"] = str(exc)
    return result


def consultation_loop_check(attempt, frozen, index=None):
    profile = frozen.get("observation_profile", {})
    loop_profile = profile.get("profile", LOOP_CAPABILITY)
    if not profile.get("consultation_loop"):
        return {"profile": loop_profile, "status": "not_applicable", "findings": [], "evidence_refs": [],
                "reason": "The frozen candidate uses an older observation profile."}
    frames = retained_frames(attempt, read, inventory)
    public_paths = [source["destination"] for source in frozen["case_manifest"]["sources"]]
    for frame in frames:
        frame["public_paths"] = public_paths
        if profile.get("journal_format") == V8_FORMAT:
            frame.setdefault("journal_format", V8_FORMAT)
    agent_recorded_reply = bool(profile.get("agent_recorded_reply"))
    result = evaluate_frames(frames, agent_recorded_reply=agent_recorded_reply)
    if not frames:
        result["profile"] = loop_profile
    result["public_presentation_check"] = public_presentation_check(frames,
        frozen.get("observation_profile", {}).get("public_presentation_renderer", "lead-markdown-v9")
        if frozen.get("observation_profile", {}).get("public_presentation") else None, agent_recorded_reply=agent_recorded_reply,
        option_max_words=profile.get("public_presentation_option_max_words", 100))
    result["evidence_refs"] = list(dict.fromkeys(result["evidence_refs"] + result["public_presentation_check"]["evidence_refs"]))
    if index is not None:
        require(all(ref in index["files"] for ref in result["evidence_refs"]),
                "consultation loop observation has unbound evidence")
    return result


def assess(review, state, frozen, index, completion_check=None, loop_check=None, loading_check=None, delivered_replies=None):
    validate_reply_bounds(frozen["case_manifest"], config=frozen["configuration"])
    require(review["evidence_sha256"] == index["sha256"], "review evidence changed; inspect and review again")
    require(review["test_validity"] in ("valid", "invalid", "unverified"), "invalid test validity")
    require(isinstance(review.get("test_validity_reason"), str) and review["test_validity_reason"].strip(),
            "test validity reason required")
    require(review["outcome"] in ("objective_met", "useful_stop", "incomplete", "execution_error"), "invalid outcome")
    require(isinstance(review.get("stop_reason"), str) and review["stop_reason"].strip(), "stop reason required")
    require(isinstance(review.get("reviewer"), str) and review["reviewer"].strip(), "identify independent reviewer")

    def references(item):
        require(item.get("evidence_refs") and all(ref in index["files"] for ref in item["evidence_refs"]), "missing or unbound evidence references")

    packet = frozen["reviewer_packet"]
    criteria = {item["id"]: item for item in packet["criteria"]}
    require(set(review["coverage"]) == set(criteria), "coverage must address every frozen criterion")
    missing = False
    for key, item in review["coverage"].items():
        require(item["status"] in ("observed", "unobserved", "not_applicable"), "invalid coverage status")
        require(item.get("reason"), "coverage reason required")
        if item["status"] == "observed":
            references(item)
        if item["status"] == "not_applicable":
            require(criteria[key].get("conditional"), "unconditional criterion cannot be waived")
        missing |= criteria[key].get("required", True) and item["status"] == "unobserved"
    for finding in review["findings"]:
        require(finding["owner"] in ("consultant", "simulator", "harness", "fixture", "environment", "undetermined"), "invalid finding owner")
        require(finding["severity"] in ("minor", "material", "fundamental"), "invalid severity")
        require(finding["criterion"] in criteria and finding.get("description") and finding.get("consequence"), "incomplete finding")
        references(finding)
    validity = review["test_validity"]
    overrides = []
    explicit_loading = frozen["configuration"].get("candidate_loading") == "claude_explicit"
    if explicit_loading:
        loading_check = loading_check or {"mode": "claude_explicit", "status": "unobserved", "calls": []}
        if loading_check["status"] != "matched":
            overrides.append("explicit candidate loading " + loading_check["status"] + ": retained instruction/session evidence cannot qualify this test")
            if loading_check["status"] == "conflict":
                validity = "invalid"
            elif validity != "invalid":
                validity = "unverified"
    if frozen["configuration"]["mode"] == "diagnostic":
        if validity != "invalid":
            overrides.append("diagnostic mode: no verified private-file isolation; validity forced to invalid")
        validity = "invalid"
    elif validity == "valid":
        for key in ("candidate_loading", "exact_resume", "private_isolation", "role_separation"):
            check = review.get("host_checks", {}).get(key, {})
            require(check.get("verified") is True and check.get("reason"), "missing reviewed host check: " + key)
            references(check)
            require(any(ref.startswith("private/host/") for ref in check["evidence_refs"]), "host checks require captured host evidence")
            if explicit_loading and key == "candidate_loading":
                native_refs = {f"private/events/{call['event']}/transport/stdout.txt" for call in loading_check["calls"]}
                require(native_refs & set(check["evidence_refs"]),
                        "explicit candidate host review must cite actual native evidence for tool-path review")
    if any(f["owner"] in ("simulator", "fixture", "harness", "environment")
           and f["severity"] in ("material", "fundamental") for f in review["findings"]):
        if validity != "invalid":
            overrides.append("material non-consultant finding; validity forced to invalid")
        validity = "invalid"
    outcome = review["outcome"]
    if state["status"] in ("pending", "execution_error"):
        outcome = "execution_error"
    elif state["status"] == "limit_reached":
        outcome = "incomplete"
    if frozen["case_manifest"].get("completion_contract", "focused") == "full_report":
        completion_check = completion_check or {"contract": "full_report", "satisfied": False,
                                                 "reason": "Report completion evidence was not checked.", "evidence_refs": []}
        if outcome in ("objective_met", "useful_stop") and not completion_check["satisfied"]:
            outcome = "incomplete"
    else:
        completion_check = None
    if "minimum_consultant_replies" in frozen["case_manifest"]:
        bounds_met = type(delivered_replies) is int and 8 <= delivered_replies <= 12
        if outcome in ("objective_met", "useful_stop") and not bounds_met:
            outcome = "incomplete"
    if outcome == "useful_stop":
        require(packet.get("useful_stop") and review.get("useful_stop_basis"), "case does not permit this useful stop")
    defects = [f for f in review["findings"] if f["owner"] == "consultant"]
    unresolved_cause = any(f["owner"] == "undetermined" and f["severity"] in ("material", "fundamental")
                           for f in review["findings"])
    loop_required = frozen.get("observation_profile", {}).get("consultation_loop", False)
    if loop_required and loop_check is None:
        loop_check = {"profile": frozen.get("observation_profile", {}).get("profile", LOOP_CAPABILITY), "status": "unobserved", "findings": [],
                      "reason": "Actual consultation chronology was not checked.", "evidence_refs": []}
    if any(f["severity"] in ("material", "fundamental") for f in defects) or (loop_check or {}).get("status") == "breach":
        rating = "fail"
    elif validity != "valid" or missing or unresolved_cause or state["breaches"] or outcome not in ("objective_met", "useful_stop") or (
            loop_required and loop_check["status"] != "no_structural_breach"):
        rating = "inconclusive"
    else:
        rating = "weak" if defects else "pass"
    return {**review, "tester_version": TESTER_VERSION, "test_validity": validity, "validity_overrides": overrides,
            **({"candidate_loading_check": loading_check} if explicit_loading else {}),
            "outcome": outcome, "quality_rating": rating,
            "completion_check": completion_check,
            "consultation_loop_check": loop_check,
            "resources": {"consultant_turns": state["turns"],
                          "active_seconds": None if state["status"] == "pending" else state["active_seconds"],
                          "recorded_active_seconds": state["active_seconds"],
                          "elapsed_seconds": None if state["status"] == "pending" else (
                              state.get("ended_at", state.get("last_activity_at", state["started_at"])) - state["started_at"] if state["started_at"] else 0),
                          "limits": frozen["configuration"]["limits"],
                          "active_time_scope": "Consultant subprocess only; harness observations and reviewer effort excluded.",
                          "elapsed_time_scope": "First dispatch through stop/failure/limit, or last captured turn when finalized directly; reviewer effort excluded.",
                          "breaches": state["breaches"], "aggregate_tokens": None, "aggregate_cost_usd": None,
                          "usage_scope": "Raw per-call result usage in transport.json; aggregation not established."}}


def adjudicate_observations(observations, dispositions, index):
    """Apply two evidence-bound review resolutions; retain the raw observations."""
    resolved, notes = set(), []
    for finding in observations["machine_findings"]:
        item = dispositions[finding["id"]]
        resolution = item.get("resolution")
        if resolution is None:
            continue  # Historical dispositions keep their conservative meaning.
        candidate = finding.get("observation", {}).get("adjudication_candidate", {})
        kind = candidate.get("kind")
        require(isinstance(resolution, dict) and item["status"] == "confirmed"
                and kind in ("delivery_terminal_newlines", "authorized_diagnostic_reuse")
                and resolution.get("kind") == kind,
                "resolution requires a confirmed, eligible delivery-format or artifact-provenance observation")
        require(isinstance(resolution.get("review"), str) and resolution["review"].strip()
                and candidate.get("evidence_refs")
                and set(candidate["evidence_refs"]) <= set(item["evidence_refs"])
                and all(ref in index["files"] for ref in candidate["evidence_refs"]),
                "resolution requires the complete counterpart and provenance evidence and a content review")
        if kind == "delivery_terminal_newlines":
            require(finding["check"] == "delivery_correspondence"
                    and finding["observation"].get("code") == "delivery_public_mismatch"
                    and candidate.get("session_id") and candidate.get("public_event")
                    and resolution.get("severity") == "minor"
                    and resolution.get("meaning_permission_timing_unchanged") is True,
                    "formatting resolution must preserve message identity, meaning, permission and timing")
        else:
            require(finding["check"] == "artifact_provenance" and candidate.get("origins")
                    and resolution.get("content_role") == "diagnostic",
                    "artifact resolution requires review of authorized diagnostic reuse")
        resolved.add(finding["id"])
        notes.append({"finding_id": finding["id"], "kind": kind,
                      "resolution": resolution, "evidence_refs": item["evidence_refs"]})
    raw = observations["consultation_loop_check"]
    cleared = [finding["observation"] for finding in observations["machine_findings"] if finding["id"] in resolved]
    effective = {**raw, "findings": [finding for finding in raw.get("findings", []) if finding not in cleared]}
    if resolved and raw.get("status") in ("breach", "unobserved"):
        effective["status"] = ("breach" if any(f.get("owner") == "consultant" for f in effective["findings"])
                               else "unobserved" if effective["findings"] or raw.get("unobserved")
                               else "no_structural_breach")
    return effective, resolved, notes


def finish(attempt, review):
    with locked(attempt):
        state, frozen = read(attempt / "state.json"), read(attempt / "freeze.json")
        require(state["status"] != "finished", "already finalized")
        index = evidence(attempt, state)
        require((attempt / "review-index.json").is_file() and (attempt / "review-observations.json").is_file(),
                "inspect reviewer first; final checks must precede assessment writing")
        prepared = read(attempt / "review-index.json")
        require(prepared["sha256"] == index["sha256"] and prepared["files"] == index["files"],
                "review evidence changed; inspect and review again")
        observations = read(attempt / "review-observations.json")
        sha = digest(attempt / "review-observations.json")
        require(sha == prepared.get("observations_sha256") == review.get("observations_sha256"),
                "review must bind the final observation snapshot")
        require(observations == review_observations(attempt, state, frozen, index),
                "final observations changed; inspect and review again")
        dispositions = review.get("machine_finding_dispositions", {})
        require(isinstance(dispositions, dict) and set(dispositions) == {f["id"] for f in observations["machine_findings"]},
                "review must disposition every final machine finding")
        for item in dispositions.values():
            require(isinstance(item, dict) and item.get("status") in ("confirmed", "false_positive", "unresolved")
                    and isinstance(item.get("reason"), str) and item["reason"].strip()
                    and isinstance(item.get("evidence_refs"), list) and item["evidence_refs"]
                    and all(ref in index["files"] for ref in item["evidence_refs"]),
                    "each machine finding disposition needs status, reason and bound evidence")
        frozen["reviewer_packet"] = read(attempt / "case" / frozen["case_manifest"]["reviewer"])
        completion_check = observations["completion_check"]
        loop_check = observations["consultation_loop_check"]
        effective_loop, resolved, adjudications = adjudicate_observations(observations, dispositions, index)
        result = assess(review, state, frozen, index, completion_check, effective_loop,
                        observations.get("candidate_loading_check"),
                        delivered_reply_count(attempt) if "minimum_consultant_replies" in frozen["case_manifest"] else None)
        result["consultation_loop_check"] = loop_check
        result["public_presentation_check"] = observations.get("public_presentation_check")
        result["adjudicated_consultation_loop_status"] = effective_loop.get("status")
        result["machine_finding_adjudications"] = adjudications
        # Retain raw checks. Disputed structural flags need correction/retest,
        # not an automatic pass or an unsupported consultant failure.
        loop_dispositions = [dispositions[f["id"]]["status"] for f in observations["machine_findings"]
                             if f["check"] == "consultation_loop"]
        if loop_check.get("status") == "breach" and loop_dispositions and "confirmed" not in loop_dispositions:
            if not any(f["owner"] == "consultant" and f["severity"] in ("material", "fundamental") for f in review["findings"]):
                result["quality_rating"] = "inconclusive"
        if any(item["status"] == "unresolved" for item in dispositions.values()) and result["quality_rating"] in ("pass", "weak"):
            result["quality_rating"] = "inconclusive"
        if observations["missing_captures"] and result["quality_rating"] in ("pass", "weak"):
            result["quality_rating"] = "inconclusive"
        if any(f["check"] in ("source_release_trace", "delivery_correspondence")
               and f["id"] not in resolved and dispositions[f["id"]]["status"] != "false_positive"
               for f in observations["machine_findings"]):
            if result["quality_rating"] in ("pass", "weak"):
                result["quality_rating"] = "inconclusive"
        write(attempt / "assessment.json", result)
        state["status"] = "finished"
        write(attempt / "state.json", state)
        return result


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "start"):
        p = commands.add_parser(name)
        for argument in ("case", "candidate", "config"):
            p.add_argument("--" + argument, required=True, type=Path)
        if name == "start":
            p.add_argument("--attempt", required=True, type=Path)
            p.add_argument("--work", required=True, type=Path)
    for name in ("step", "inspect", "finish"):
        p = commands.add_parser(name)
        p.add_argument("--attempt", required=True, type=Path)
        if name == "step":
            p.add_argument("--reply", required=True, type=Path)
        if name == "inspect":
            p.add_argument("--view", required=True, choices=("actor", "reviewer"))
        if name == "finish":
            p.add_argument("--assessment", required=True, type=Path)
    p = commands.add_parser("export")
    p.add_argument("--attempt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--work", type=Path, help="explicit relocated work directory")
    p.add_argument("--allow-partial", action="store_true")
    p = commands.add_parser("check-package")
    p.add_argument("--package", required=True, type=Path)
    p.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    try:
        if args.command in ("preflight", "start"):
            common = (args.case.resolve(), args.candidate.resolve(), read(args.config))
            result = preflight(*common) if args.command == "preflight" else start(*common, args.attempt.resolve(), args.work.resolve())
        elif args.command == "step":
            result = step(args.attempt.resolve(), read(args.reply))
        elif args.command == "inspect":
            result = inspect(args.attempt.resolve(), args.view)
        elif args.command == "export":
            result = export_package(args.attempt, args.output, allow_partial=args.allow_partial, work=args.work)
        elif args.command == "check-package":
            result = check_package(args.package, require_complete=not args.allow_partial)
        else:
            result = finish(args.attempt.resolve(), read(args.assessment))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
