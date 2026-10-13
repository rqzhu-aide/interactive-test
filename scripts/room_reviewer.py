"""CLI reviewer driver: one fresh model process for a room's end-of-run review.

Complements room_actor.py. The reviewer is a separate agent from the operator
session: a fresh CLI process with an explicit review prompt. Fresh invocation
alone does not establish isolation from other instructions or files.
It reads the case's reviewer packet, world/oracle ground truth and evaluation
rules, reads the attempt evidence, may run python (check_oracle.py, recomputing
published figures), dispositions every machine finding, and returns the
assessment JSON that `session_driver.py finish` validates. Prompt and raw
output are retained for the record.

Usage:
    python room_reviewer.py --attempt <abs attempt dir> --case <abs case dir>
        --evaluation-md <abs references/evaluation.md> --runtime {pi,claude,kimi}
        --model <model id> --reviewer <reviewer label> --context-id <id>
        --out <review json path> --cwd <scratch dir>
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from room_actor import extract_json, resolve  # shared CLI plumbing
from session_driver import digest, member, read, require

CONTRACT = """You are the independent reviewer of a completed interactive test of a \
causal-consulting assistant. You are a fresh context: judge only from the files listed here.

Inputs (read them as needed):
- Reviewer packet (frozen criteria and rules): {reviewer_packet}
- Ground truth (private to the grading side): {case}/world.json and {case}/oracle.json
- Independent fixture self-check you may run: python {case}/check_oracle.py
- Evaluation rules: {evaluation_md}, including its linked private observation
  profiles for the frozen candidate. These rules must not be passed to the actor.
- Attempt evidence: everything under {attempt} (state.json, freeze.json,
  review-index.json, review-observations.json, events/, work snapshot trees).
- Bind your review to the digests in {attempt}/review-index.json:
  evidence_sha256 and observations_sha256 must be quoted from that file.

Duties:
1. Disposition every machine finding listed in {attempt}/review-observations.json
   (status confirmed / false_positive / unresolved, with reason and bound evidence).
2. Judge every frozen criterion from the selected reviewer packet (status observed / unobserved /
   not_applicable, with reason and evidence_refs bound to review-index files).
3. Independently verify what is verifiable: recompute headline numbers from the
   retained data with python, run check_oracle.py, re-hash load-bearing artifacts.
4. Record findings (owner: consultant / simulator / harness / fixture / environment /
   undetermined; severity: minor / material / fundamental) with description,
   consequence and bound evidence_refs. Never pad, never hide.
5. test_validity must follow the evaluation rules; state why it holds in
   test_validity_reason. If you are grading a consultant of your own model family,
   say so in test_validity_reason as a recorded consideration.
6. For a verified_host attempt, a claim of valid requires host_checks for
   candidate_loading, exact_resume, private_isolation and role_separation. Each
   check has verified (boolean), reason and evidence_refs, including retained
   private/host/ evidence. Supply actual evidence and reasoning, never a boilerplate
   pass. Unsupported checks mean unverified or invalid validity as appropriate.
   For claude_explicit loading, inspect candidate_loading_check and each event's
   command.json, candidate-loading.json, candidate-system-prompt.txt and stdout.txt.
   Missing or conflicting loading evidence cannot be waived by reviewer assertion.
   Matched hashes and flags establish that the staged entry was supplied, not that
   every later guide or helper came from that candidate. Inspect actual native tool
   paths, explain what they establish and cite relevant actual-attempt
   transport/stdout.txt evidence in the candidate_loading host check, in addition
   to host evidence. Loading evidence does not prove isolation or scientific
   understanding. Diagnostic mode cannot establish a qualified pass or comparative
   model-performance claim; retain supported scientific findings.

Return ONLY a JSON object with these required fields: evidence_sha256,
observations_sha256, stop_reason, test_validity, test_validity_reason, outcome,
coverage, findings, machine_finding_dispositions, reviewer. Also include host_checks
when claiming valid for verified_host; otherwise include it only for checks you
actually reviewed. If outcome is useful_stop, include useful_stop_basis explaining
how it satisfies the case's permitted stopping rule. A full-report case still
requires its report completion evidence. No prose outside the JSON.
"""

REQUIRED = ["evidence_sha256", "observations_sha256", "stop_reason", "test_validity",
            "test_validity_reason", "outcome", "coverage", "findings",
            "machine_finding_dispositions", "reviewer"]
INSTRUCTION = ("Read the file prompt.txt in the current directory and follow its "
               "instructions exactly. Your entire response must be only the JSON "
               "object it defines.")


def reviewer_argv(runtime, model, cwd):
    """Fresh reviewer process; read + code execution for independent verification."""
    if runtime == "claude":
        argv = ["-p", INSTRUCTION, "--allowedTools", "Read,Bash", "--output-format", "json",
                "--disable-slash-commands"]
        if model:
            argv += ["--model", model]
        return resolve("claude") + argv
    if runtime == "kimi":
        argv = ["-p", INSTRUCTION, "--skills-dir", str(cwd / "no-skills")]
        if model:
            argv += ["-m", model]
        return resolve("kimi") + argv
    if runtime == "pi":
        argv = ["--print", "--no-session", "--no-skills", "--tools", "read,bash"]
        if model:
            argv += ["--model", model]
        return resolve("pi") + argv + [INSTRUCTION]
    raise ValueError("unknown runtime: " + runtime)


def run_runtime(runtime, model, cwd):
    argv = reviewer_argv(runtime, model, cwd)
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(cwd))
    if runtime == "claude":
        envelope = json.loads(proc.stdout)
        if envelope.get("is_error"):
            raise RuntimeError("claude reviewer error: " + str(envelope)[:300])
        return envelope["result"]
    if proc.returncode != 0:
        raise RuntimeError(runtime + " reviewer failed: " + proc.stderr.strip()[:300])
    return proc.stdout


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    for flag in ("attempt", "case", "evaluation-md", "runtime", "reviewer", "context-id", "out", "cwd"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    case = Path(args.case).resolve()
    manifest = read(case / "case.json")
    reviewer_packet = member(case, manifest["reviewer"])
    require(digest(reviewer_packet) == manifest["files"].get(manifest["reviewer"]),
            "reviewer packet identity mismatch")
    prompt = CONTRACT.format(case=case, reviewer_packet=reviewer_packet,
                             attempt=Path(args.attempt).resolve(),
                             evaluation_md=Path(args.evaluation_md).resolve())
    cwd = Path(args.cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / "no-skills").mkdir(exist_ok=True)
    (cwd / "prompt.txt").write_text(prompt, encoding="utf-8")

    raw = run_runtime(args.runtime, args.model, cwd)
    (cwd / "last-raw-output.txt").write_text(raw, encoding="utf-8")
    review = extract_json(raw)
    missing = [key for key in REQUIRED if key not in review]
    if missing:
        raise ValueError("review missing fields: " + ", ".join(missing))
    review["reviewer_context"] = {"runtime": args.runtime, "model": args.model,
                                  "context_id": args.context_id, "reviewer": args.reviewer}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(review, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "test_validity": review.get("test_validity"),
                      "outcome": review.get("outcome"),
                      "findings": len(review.get("findings", []))}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"error": repr(exc)}), file=sys.stderr)
        sys.exit(1)
