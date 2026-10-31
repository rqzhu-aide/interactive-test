"""Freeze a reusable problem/persona pair or one standalone consultation case."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

from session_driver import digest, inventory, member, read, require, validate_case
from source_release import validate_source_prerequisite


ROOT = Path(__file__).resolve().parents[1]
PROBLEM_IDS = ("study-design", "observational-did", "cate-policy", "data-quality-edge")
GENERAL_PERSONA_IDS = ("standard", "novice-adversarial", "expert")
COORDINATOR_PERSONA_ID = "rggvy-research-coordinator"
PERSONA_IDS = GENERAL_PERSONA_IDS
RGGVY_ID = "rggvy-electrification"
STANDALONE_IDS = (RGGVY_ID, "masks-planning", "forest-planning", "medication-planning", "surgery-planning")
RGGVY_ROOT = ROOT / "standalone" / RGGVY_ID
CONTINUITY_RESOURCE = RGGVY_ROOT / "continuity-variant.json"
REPLY_LIMITS = {"max_words": 50, "max_items": 2}
INTERACTION_CHALLENGES = {
    "study-design": [
        {"id": "partial-design-intake",
         "trigger": "A compound question asks about allocation and recruitment or follow-up operations together.",
         "behavior": "Answer one part you understand from your available facts. A natural reply may leave the other part unmentioned; retain it privately.",
         "recovery": "Answer the omitted part from legitimate knowledge or records when the consultant follows up."},
        {"id": "clarify-design-scope",
         "trigger": "A proposed next step leaves unclear whether agreeing would start real allocation or only prepare a design report.",
         "behavior": "Ask what the agreement would authorize before choosing. Do not imply that a study has begun.",
         "recovery": "Once the scope is clear, make an ordinary choice under the problem goal."},
    ],
    "observational-did": [
        {"id": "partial-rollout-account",
         "trigger": "A compound question asks both when sites adopted and how adopters were chosen.",
         "behavior": "Answer one part you know without a public list of everything left open; retain the omitted part privately.",
         "recovery": "Supply the other part or its accessible record on a focused follow-up."},
        {"id": "clarify-population-target",
         "trigger": "The consultant uses shorthand that makes it unclear whether the proposed result covers adopters or all listed sites.",
         "behavior": "Ask which sites the result would describe, in your own level of statistical language.",
         "recovery": "Use the explanation to choose or qualify the proposed target without certifying its assumptions."},
    ],
    "cate-policy": [
        {"id": "partial-policy-intake",
         "trigger": "A compound question asks about decision-time fields and delivery cost or capacity together.",
         "behavior": "Answer one operational part you know and leave the other unlisted in the public message; retain it privately.",
         "recovery": "Provide the omitted fact or relevant decision note on a focused follow-up."},
        {"id": "clarify-offer-versus-attendance",
         "trigger": "The consultant uses 'treatment' or 'benefit' ambiguously between an offer and actual attendance.",
         "behavior": "Ask which action the proposed result concerns or answer a clearly labeled nearby interpretation; do not invent assignment facts.",
         "recovery": "After clarification, keep offer and attendance distinct in later answers."},
    ],
    "data-quality-edge": [
        {"id": "partial-extract-account",
         "trigger": "A compound question asks about repeated rows and blank completion entries together.",
         "behavior": "Answer one part from what you understand and retain the omitted part privately without reciting a pending list.",
         "recovery": "Answer the missing part or supply its record when the consultant asks again."},
        {"id": "clarify-blank-status",
         "trigger": "The consultant's wording leaves unclear whether a blank completion entry means failure or unknown status.",
         "behavior": "Ask what the blank means or state your tentative interpretation as a question; do not assert an unsupported data correction.",
         "recovery": "Use the actual dictionary or explanation to update and retain the distinction."},
    ],
}


def interaction_challenge(problem_id, persona_id, seed):
    require(type(seed) is int and seed >= 0, "interaction seed must be a nonnegative integer")
    choices = INTERACTION_CHALLENGES[problem_id]
    key = f"{problem_id}:{persona_id}:{seed}".encode("utf-8")
    index = int(hashlib.sha256(key).hexdigest(), 16) % len(choices)
    return copy.deepcopy(choices[index])
COMMON_RULES = [
    {"rule_id": "r-initial", "condition": "This is the initial dispatch.",
     "action": "Send exactly the frozen initial request. Do not add private profile, benchmark or expected-answer information.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-known-facts", "condition": "The consultant asks a factual question you can answer from your packet or legitimately learned information.",
     "action": "Answer the current question or a closely connected part from what you actually understand, following your persona's disclosure_policy. Keep a short necessary answer together. A compound question may receive a partial or nearby answer without a public inventory of omissions; retain the exact remainder in unanswered_questions and answer a focused follow-up. Do not recite every known fact or treat a broad request as permission to complete the whole intake at once. Cite visible learning in knowledge_updates; preserve qualifications.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-records", "condition": "The consultant asks for records or information covered by the source inventory.",
     "action": "Source conditions establish eligibility, not an instruction to attach everything eligible. Supply the record or coherent bundle needed for the current issue, with a brief explanation of its relevance. For a broad request covering several topics, start with a relevant topic; do not send the entire dossier or recite every pending record in one reply. Retain unsupplied requests privately and follow up when the discussion returns to them, without requiring private filenames. Honor a specific request for a necessary bundle and keep a requested file intact. Do not invent retrieval delays, claim accessible records are unavailable or repeat an attachment. Preserve genuine evaluation-data prerequisites.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-clarify", "condition": "An explanation, request or decision is unclear at your persona's current understanding.",
     "action": "Ask a natural focused question about its practical meaning. Still answer clear parts you know. Retain what you learn and do not repeat a resolved misunderstanding.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-proceed", "condition": "The consultant proposes useful work within the requested study and deliverable.",
     "action": "Respond to the actual offered scope and choices using your documented decision constraints. The initial report request states a goal, not standing permission for analysis or reporting. Ask about unclear implications; otherwise choose supported bounded work in ordinary language. An extension selection authorizes that extension only. Do not prescribe internal routing or a preferred result.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-persona", "condition": "The visible exchange warrants a belief update, method discussion or a permitted presentation-pressure event.",
     "action": "Use only the selected persona's behavior and finite pressure policy. Record the visible basis and retain learning. Persona preferences cannot change study facts or replace the problem's endpoint.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-report", "condition": "The substantive work is settled but the requested saved report has not yet been delivered, or an actual visible omission needs correction.",
     "action": "Use the actual findings and offered directions to choose useful further work or the saved report. Complete any explicit persona requirement for methodological proposals before selecting the report; optional pressure opportunities remain optional. If no report option has been offered, you may naturally ask about the deliverable, without treating that request as permission to skip discussion. Ask for a concrete correction when needed. Do not force completion while material questions remain. A recap does not substitute for the saved report.",
     "fact_ids": [], "source_ids": []},
    {"rule_id": "r-stop", "condition": "The requested saved report has been visibly delivered, the stated scope is addressed, any explicit persona requirement for methodological proposals is satisfied, and no accepted correction or outstanding user question remains.",
     "action": "Stop without manufacturing another recap or an unused pressure event. Judge completion from information a user can actually see; do not read private helper observations or certify hidden scientific truth. Independent review checks actual artifact integrity and scientific quality.",
     "fact_ids": [], "source_ids": []},
]


def save(file, value):
    Path(file).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fresh_output(output, *sources):
    require(output is not None, "output is required")
    output = Path(output).resolve()
    require(not output.exists(), "output already exists; compose into a fresh directory")
    protected = (*sources, ROOT / "problems", ROOT / "personas", ROOT / "standalone")
    require(not any(output.is_relative_to(Path(source).resolve()) or Path(source).resolve().is_relative_to(output)
                    for source in protected), "output overlaps definition bank")
    return output


def problem_definition(problem_id, bank_root):
    require(problem_id in (*PROBLEM_IDS, RGGVY_ID), "unknown problem selector")
    directory = member(bank_root, "problem" if problem_id == RGGVY_ID else problem_id)
    definition = read(directory / "problem.json")
    require(definition.get("schema_version") == 1 and definition.get("problem_id") == problem_id,
            "problem identity mismatch")
    actual = inventory(directory)
    del actual["problem.json"]
    require(actual == definition["files"], "problem file identity mismatch")
    require(type(definition.get("target_turns")) is int and definition["target_turns"] > 0,
            "problem target must be a positive descriptive count")
    require(set(definition["initial_requests"]) == set(GENERAL_PERSONA_IDS), "missing persona request wording")
    require("public/initial-message.txt" not in actual,
            "initial message must be composed from private wording templates")
    for source in definition["sources"]:
        validate_source_prerequisite(source)
    world = read(member(directory, definition["world"]))
    require(world.get("world_id") and world.get("world_version"), "missing world identity")
    for key in ("world", "reviewer", "oracle_check"):
        require(definition[key] in actual and not definition[key].startswith("public/"),
                "private problem material must remain private")
    return directory, definition, world


def persona_definition(persona_id, personas_root):
    require(persona_id in (*PERSONA_IDS, COORDINATOR_PERSONA_ID), "unknown persona selector")
    file = (RGGVY_ROOT / "persona.json" if persona_id == COORDINATOR_PERSONA_ID
            else member(personas_root, persona_id + ".json"))
    persona = read(file)
    require(persona.get("schema_version") == 1 and persona.get("persona_id") == persona_id,
            "persona identity mismatch")
    require(persona.get("persona_version"), "missing persona version")
    tiers = persona.get("initial_knowledge_tiers")
    require(isinstance(tiers, list) and tiers and set(tiers) <= {"practical", "domain", "statistical"},
            "unsupported knowledge tiers")
    require(not any(key in persona for key in ("goal", "sources", "world", "target_turns", "completion_contract")),
            "persona cannot override the problem, access, endpoint or duration")
    require(persona.get("reply_limits") == REPLY_LIMITS,
            "every persona must use the suite's 50-word and two-item limits")
    for key in ("behavior", "disclosure_policy", "learning_policy", "pressure_policy", "forbidden"):
        require(isinstance(persona.get(key), list) and all(isinstance(x, str) and x.strip() for x in persona[key]),
                "invalid persona behavior field: " + key)
    require(bool(persona["disclosure_policy"]), "persona disclosure policy must not be empty")
    return file, persona


def compose_case(problem_id, persona_id=None, output=None, bank_root=None, personas_root=None,
                 max_consultant_turns=None, interaction_seed=0):
    require(problem_id in (*PROBLEM_IDS, RGGVY_ID), "unknown problem selector")
    if persona_id is None:
        persona_id = COORDINATOR_PERSONA_ID if problem_id == RGGVY_ID else "standard"
    require(persona_id != COORDINATOR_PERSONA_ID or problem_id == RGGVY_ID,
            "rggvy-research-coordinator is supported only with rggvy-electrification")
    require(problem_id != RGGVY_ID or persona_id == COORDINATOR_PERSONA_ID,
            "rggvy-electrification is standalone and supports only rggvy-research-coordinator")
    require(type(interaction_seed) is int and interaction_seed >= 0,
            "interaction seed must be a nonnegative integer")
    variant = None
    if persona_id == COORDINATOR_PERSONA_ID:
        variant = read(CONTINUITY_RESOURCE)
        require(variant.get("schema_version") == 1
                and variant.get("problem_id") == problem_id
                and variant.get("persona_id") == persona_id
                and variant.get("variant_id") == "rggvy-continuity-coordinator"
                and variant.get("variant_version"), "continuity variant identity mismatch")
        require(type(variant.get("target_turns")) is int and variant["target_turns"] > 0,
                "variant target must be a positive descriptive count")
        interaction_seed = None
    stress = bool(variant and variant["variant_version"] == "1.1.0")
    if stress:
        require(max_consultant_turns in (None, 12) and not isinstance(max_consultant_turns, bool),
                "RGGVY stress edition has a fixed maximum of 12 consultant replies")
    if max_consultant_turns is None:
        max_consultant_turns = variant["default_max_consultant_turns"] if variant else 40
    require(problem_id != RGGVY_ID or bank_root is None,
            "standalone RGGVY uses its fixed scientific source bank")
    bank_root = Path(bank_root or (RGGVY_ROOT if problem_id == RGGVY_ID else ROOT / "problems")).resolve()
    personas_root = Path(personas_root or ROOT / "personas").resolve()
    directory, problem, world = problem_definition(problem_id, bank_root)
    persona_file, persona = persona_definition(persona_id, personas_root)
    require(type(max_consultant_turns) is int and max_consultant_turns > 0,
            "operational maximum must be a positive integer")
    output = fresh_output(output, bank_root, personas_root)
    facts = []
    for entry in problem["actor_facts"]:
        require(entry.get("knowledge_tier") in ("practical", "domain", "statistical"),
                "actor fact lacks a knowledge tier")
        if entry["knowledge_tier"] in persona["initial_knowledge_tiers"]:
            facts.append({key: copy.deepcopy(value) for key, value in entry.items() if key != "knowledge_tier"})
    if variant:
        facts.extend(copy.deepcopy(variant["actor_facts"]))
    fact_ids = {entry["fact_id"] for entry in facts}
    require(len(fact_ids) == len(facts), "duplicate composed actor fact ID")
    rules = copy.deepcopy(COMMON_RULES) + copy.deepcopy(problem.get("actor_rules", []))
    if variant:
        rules.extend(copy.deepcopy(variant["actor_rules"]))
        next(rule for rule in rules if rule["rule_id"] == "r-records")["action"] = variant["record_rule_action"]
    if stress:
        for rule in rules:
            if rule["rule_id"] in ("r-report", "r-stop"):
                rule.update(copy.deepcopy(variant["completion_rule_overrides"][rule["rule_id"]]))
    require(len({entry["rule_id"] for entry in rules}) == len(rules), "duplicate composed actor rule ID")
    for rule in rules:
        rule["fact_ids"] = [ref for ref in rule.get("fact_ids", []) if ref in fact_ids]
    rules[1]["fact_ids"] = sorted(fact_ids)
    sources = [{"source_id": entry["id"], "file": entry["destination"],
                "availability": entry["availability"], "release": entry["release_when"],
                **({"release_prerequisite": copy.deepcopy(entry["release_prerequisite"])}
                   if "release_prerequisite" in entry else {})}
               for entry in problem["sources"]]
    rules[2]["source_ids"] = [entry["source_id"] for entry in sources]
    actor = {
        "role": "Simulated user only. Read this packet and the user-simulator policy, visible conversation and legitimately received material. Do not read the private problem definition, world, numerical oracle, reviewer packet or consultant internal state. Explicit required participation in the persona profile qualifies all generic case report-selection and finish rules; it cannot be waived as an unused optional challenge. An explicit user or operator stop still ends an incomplete attempt. Stay in character: the persona, this packet and their rules are internal and are never mentioned, implied or paraphrased in messages; the same content is expressed naturally in the user's own voice.",
        "persona_id": persona_id, "persona_version": persona["persona_version"],
        "persona_profile": persona, "goal": problem["goal"], "fluency": persona["fluency"],
        "reply_limits": copy.deepcopy(REPLY_LIMITS),
        "interaction_challenges": [] if variant else [interaction_challenge(problem_id, persona_id, interaction_seed)],
        "facts": facts, "sources": sources, "rules": rules,
        "unknown_policy": problem["unknown_policy"] + (" " + variant["unknown_policy_suffix"] if variant else ""),
        "reply_record": {"required": ["message", "fact_ids", "rule_ids", "attachments", "unanswered_questions", "fixture_gaps", "stop"],
                         "optional": ["knowledge_updates", "belief_updates", "decision_updates", "actor_context",
                                      "action_intents", "source_release_receipts"]},
        "pacing": "Share information around the current issue, using your persona's disclosure and correction policies. A public reply may omit part of a compound request without a checklist, while unanswered_questions privately retains the exact remainder. Apply a frozen interaction challenge only when visible wording and your fluency make its trigger plausible; retire it after recovery and never force it to fill turns. Keep necessary answers and requested bundles intact and do not invent delays. No turn number, target or operational limit determines disclosure or completion. Operational stopping is the operator's responsibility."
    }
    if stress:
        actor["consultant_reply_bounds"] = {"minimum": 8, "maximum": 12}
        actor["pacing"] = variant["actor_pacing"]
        actor["role"] = actor["role"].replace("in the persona profile", "in the persona profile or frozen case")
    request = variant["initial_request"] if variant else problem["initial_requests"][persona_id]
    require("causal-consultant" in request, "initial request must invoke consultant")
    require("report" in request.lower(), "initial request must retain the saved report objective")
    require(len(request.split()) <= REPLY_LIMITS["max_words"], "initial request exceeds 50 words")
    output.mkdir(parents=True)
    # The source bank remains immutable; each run receives a fresh frozen composition.
    for name in ("problem.json", *problem["files"]):
        destination = member(output, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(member(directory, name), destination)
    shutil.copyfile(persona_file, output / "persona.json")
    if variant:
        shutil.copyfile(CONTINUITY_RESOURCE, output / "continuity-variant.json")
        reviewer = read(directory / problem["reviewer"])
        reviewer["criteria"].extend(copy.deepcopy(variant["reviewer_criteria"]))
        require(len({item["id"] for item in reviewer["criteria"]}) == len(reviewer["criteria"]),
                "duplicate continuity reviewer criterion ID")
        reviewer["required_observations"].extend(variant["reviewer_required_observations"])
        reviewer["continuity_coverage"] = copy.deepcopy(variant["continuity_coverage"])
        # The original reviewer remains byte-identical for the source-bound oracle.
        save(output / "continuity-reviewer.json", reviewer)
    (output / "public/initial-message.txt").write_text(request.rstrip() + "\n", encoding="utf-8")
    save(output / "actor.json", actor)
    save(output / "composition.json", {
        "schema_version": 1, "problem_id": problem_id, "problem_version": problem["problem_version"],
        "problem_sha256": digest(directory / "problem.json"), "persona_id": persona_id,
        "persona_version": persona["persona_version"], "persona_sha256": digest(persona_file),
        "composer_sha256": digest(Path(__file__)),
        "target_turns": variant["target_turns"] if variant else problem["target_turns"],
        "interaction_seed": interaction_seed,
        **({"variant_id": variant["variant_id"], "variant_version": variant["variant_version"],
            "variant": "continuity-variant.json", "variant_sha256": digest(CONTINUITY_RESOURCE)} if variant else {}),
        "target_semantics": ("target_turns remains descriptive; this stress edition separately requires eight public client events and 8 to 12 delivered consultant replies." if stress else
                             "Descriptive expectation only. Never exposed as an actor instruction, deadline, quota or success criterion."),
        "science_boundary": "Persona changes initial understanding and interaction, not the problem's world, source access, data, scientific criteria or report endpoint."
    })
    manifest = {
        "schema_version": 1, "case_id": problem_id + "--" + persona_id,
        "case_version": variant["variant_version"] if variant else problem["problem_version"],
        "suite_version": problem.get("suite_version", "8.2.0"),
        "edition": "case-specific-continuity-stress-v1" if stress else ("case-specific-continuity-v1" if variant else "modular-problem-persona-bounded-friction-v1"),
        **({"minimum_consultant_replies": 8} if stress else {}),
        **({"variant_id": variant["variant_id"], "variant_version": variant["variant_version"],
            "variant": "continuity-variant.json"} if variant else {}),
        "interaction_seed": interaction_seed, "reply_limits": copy.deepcopy(REPLY_LIMITS),
        "problem_id": problem_id, "problem_version": problem["problem_version"],
        "persona_id": persona_id, "persona_version": persona["persona_version"],
        "world": problem["world"], "world_id": world["world_id"], "world_version": world["world_version"],
        "author": "Versioned modular test composition", "completion_contract": "full_report",
        "target_turns": variant["target_turns"] if variant else problem["target_turns"],
        "run_limits": {"consultant_turns": max_consultant_turns, "active_seconds": 14400, "elapsed_seconds": 43200},
        "requirements": "Shared Python 3.10+ stdlib and Node 18.18+. Freeze independent operational limits and verified host boundaries before a scored run.",
        "initial_message": "public/initial-message.txt", "actor": "actor.json",
        "reviewer": "continuity-reviewer.json" if variant else problem["reviewer"],
        "oracle_check": problem["oracle_check"],
        "sources": [{key: copy.deepcopy(value) for key, value in entry.items() if key != "release_when"}
                    for entry in problem["sources"]], "files": inventory(output)
    }
    save(output / "case.json", manifest)
    return manifest


def standalone_case(case_id, output, max_consultant_turns=None):
    """Freeze a named case without introducing a selectable persona dimension."""
    require(case_id in STANDALONE_IDS, "unknown standalone selector")
    if case_id == RGGVY_ID:
        return compose_case(case_id, output=output, max_consultant_turns=max_consultant_turns)
    source = member(ROOT / "standalone", case_id)
    output = fresh_output(output)
    manifest = validate_case(source)
    require(max_consultant_turns is None or (type(max_consultant_turns) is int
            and max_consultant_turns == manifest["run_limits"]["consultant_turns"]),
            "standalone planning cases retain their frozen operational maximum")
    shutil.copytree(source, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return validate_case(output)


def catalog():
    standalone = []
    for key in STANDALONE_IDS:
        if key == RGGVY_ID:
            problem = read(RGGVY_ROOT / "problem" / "problem.json")
            variant = read(CONTINUITY_RESOURCE)
            standalone.append({"id": key, "label": problem["label"],
                               "fixed_actor": COORDINATOR_PERSONA_ID,
                               "target_turns": variant["target_turns"],
                               "completion_contract": "full_report"})
        else:
            manifest = read(ROOT / "standalone" / key / "case.json")
            standalone.append({"id": key, "fixed_actor": manifest["persona_id"],
                               "target_turns": manifest["target_turns"],
                               "completion_contract": manifest["completion_contract"]})
    return {"problems": [{"id": key, "label": (item := read(ROOT / "problems" / key / "problem.json"))["label"],
                           "target_turns": item["target_turns"]} for key in PROBLEM_IDS],
            "personas": [{"id": key, "label": read(ROOT / "personas" / (key + ".json"))["label"],
                          "supported_problems": list(PROBLEM_IDS)} for key in PERSONA_IDS],
            "standalone_cases": standalone, "matrix_combinations": len(PROBLEM_IDS) * len(PERSONA_IDS),
            "standalone_count": len(STANDALONE_IDS),
            "combinations": len(PROBLEM_IDS) * len(PERSONA_IDS) + len(STANDALONE_IDS)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List the reusable matrix and five standalone cases")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--problem", choices=(*PROBLEM_IDS, RGGVY_ID),
                           help="Reusable problem; the legacy RGGVY spelling selects its fixed coordinator")
    selection.add_argument("--standalone", choices=STANDALONE_IDS)
    parser.add_argument("--persona", choices=(*PERSONA_IDS, COORDINATOR_PERSONA_ID),
                        help="Reusable persona (default: standard); RGGVY has a fixed coordinator")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-consultant-turns", type=int,
                        help="Operational maximum: fixed 12 for standalone cases, default 40 for reusable pairs")
    parser.add_argument("--interaction-seed", type=int, default=0,
                        help="Freeze a communication challenge for general personas; unused for the RGGVY coordinator")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(catalog(), indent=2))
        return
    if not (args.output and (args.problem or args.standalone)):
        parser.error("--problem or --standalone, and --output are required")
    if args.standalone and args.persona is not None:
        parser.error("--standalone cases have a fixed actor; do not pass --persona")
    if args.standalone and args.interaction_seed != 0:
        parser.error("--standalone cases do not select interaction challenges")
    manifest = (standalone_case(args.standalone, args.output, args.max_consultant_turns)
                if args.standalone else compose_case(args.problem, args.persona, args.output,
                    max_consultant_turns=args.max_consultant_turns, interaction_seed=args.interaction_seed))
    print(json.dumps({"case_id": manifest["case_id"], "output": str(args.output.resolve()),
                      "target_turns": manifest["target_turns"], "completion_contract": manifest["completion_contract"]}, indent=2))


if __name__ == "__main__":
    main()
