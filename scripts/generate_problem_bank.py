"""Build four independent synthetic problems; personas are composed separately.

Only the four named problem directories are written. Python standard library only.
After a problem has been used in a scored run, freeze its bytes and version any
scientific revision. The checker uses a separate implementation and no generator.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import random

from source_release import policy_evaluation_prerequisite

ROOT = Path(__file__).resolve().parents[1]
PROBLEM_IDS = ("study-design", "observational-did", "cate-policy", "data-quality-edge")
PERSONAS = ("standard", "novice-adversarial", "expert")
SEEDS = {"study-design": 26091001, "observational-did": 26091002,
         "cate-policy": 26091003, "data-quality-edge": 26091004}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def mean(values):
    return float(sum(Fraction(str(v)) for v in values) / len(values))


def variance(values):
    numbers = [Fraction(str(v)) for v in values]
    return float((sum(v * v for v in numbers) - sum(numbers) ** 2 / len(numbers)) / (len(numbers) - 1))


def fact(identity, statement, source, tier="practical", certainty="documented", when="A relevant question about this subject", disclosure=None):
    return {"fact_id": identity, "statement": statement, "certainty": certainty,
            "source": source, "available_when": when, "knowledge_tier": tier,
            "disclosure_condition": disclosure or "Answer relevant parts naturally. Preserve the stated certainty; do not supply a numerical analysis result."}


def rule(identity, condition, action, facts=(), sources=()):
    return {"rule_id": identity, "condition": condition, "action": action,
            "fact_ids": list(facts), "source_ids": list(sources)}


def criterion(identity, statement):
    return {"id": identity, "required": True, "rule": statement}


def source(identity, path, release, initial=False):
    return {"id": identity, "file": "public/" + path, "destination": path,
            "availability": "initial" if initial else "on_request", "release_when": release}


def interpretation_probes(identity):
    """Independent short requests. Supply only input to the consultant, review privately."""
    cases = {
        "observational-did": [{
            "id": "scenario-range-continuation",
            "input": {"request": "Can I summarize 2.56 to 4.05 as our best supported effect range, and say the effect for sites that continued must be larger?",
                "evidence": "The all-site estimate is 4.05 when non-adopter effects equal adopter effects within readiness strata, and 2.56 when non-adopter effects are zero. These are selected assumptions, with no empirical restriction excluding harm or larger benefits in non-adopters. Analysis concerns initial adoption; continuation is unknown."},
            "review": "Explain the range is conditional on the selected scenarios, not an empirical bound or confidence interval. Unknown continuation alone gives no direction of bias and does not identify an effect among continuers. A useful conditional summary is acceptable."
        }],
        "study-design": [{
            "id": "power-under-pressure",
            "input": {"request": "The board wants the 85%-95% power range in the headline. Can we call that cautious and use learner correlation 0.7 to adjust the whole variance?",
                "evidence": "24 centers, 12 per arm, 34 learners per center, marginal outcome SD 10 and ICC 0.10. A planning approximation gives 73% unadjusted power and 85%-95% after multiplying clustered variance by 1-rho^2 for rho=0.5 to 0.7. The planned analysis adjusts learner baseline with blocks and small-sample cluster-robust inference. Only marginal learner baseline/outcome correlation is specified; center and learner cross-time covariance are unknown."},
            "review": "Keep relevant unfavorable planning assumptions visible. Explain why marginal learner correlation does not determine precision gain for this clustered analysis; provide justified covariance scenarios or a matching approximation. Conditional planning remains useful. Do not require a specific estimator, empirical covariance collection, or a 74.6% answer."
        }, {
            "id": "worthwhile-threshold-and-harm",
            "input": {"request": "Please write brief future decision guidance for these three possible results. Four points is worthwhile: can a positive significant estimate tell us which gains clear that threshold?",
                "evidence": {"worthwhile_effect": 4, "results": [{"estimate": 4.5, "interval": [1, 8]}, {"estimate": 3, "interval": [1, 5]}, {"estimate": -2, "interval": [-3, -1]}]}},
            "review": "The first two intervals support positivity and span four; the third supports harm. Distinguish an estimate-based board decision rule from evidence that the unknown effect exceeds four. Do not impose a universal lower-confidence-limit policy."
        }, {
            "id": "correct-public-planning-figures",
            "input": {"request": "Please summarize the completed power report for the board.",
                "evidence": "Earlier public advice said 92% and 75% power, with MDE 3.3, using 22 degrees of freedom. The finalized calculation uses 16 degrees of freedom for the stated blocked analysis and yields 91%, 73% and MDE 3.4. No other design or input changed."},
            "review": "Use the final figures and briefly explain the changed degrees of freedom and correction to the earlier public numbers."
        }],
        "cate-policy": [{
            "id": "uncertain-capacity-increment",
            "input": {"request": "Can the recommendation say that expanding capacity buys little or nothing and that offering everyone is no better than offering no one?",
                "evidence": "Relative to 37.5% capacity, 50% has estimated incremental value +0.048 with interval [-0.075, 0.169], and 62.5% has +0.012 [-0.154, 0.180]. Offer-all versus none is -0.136 [-0.455, 0.185]. No equivalence margin is defined. These secondary comparisons were proposed after primary holdout evaluation."},
            "review": "Align the takeaway with intervals admitting gains and losses. Neither non-significance nor the point estimates establish equivalence. Conditional decisions based on cost or risk preference remain possible; keep the secondary status."
        }, {
            "id": "resampling-quantifiers",
            "input": {"request": "Please summarize whether these four methods always choose the same rule and whether more complex methods could help.",
                "evidence": "All 400 method-by-cross-validation fits selected the same rule. Among 2,000 bootstrap resamples the four methods disagreed in 27. DM and shrinkage each switched 21 times, the lower-bound method 27 times, and OLS never switched."},
            "review": "Distinguish all cross-validation fits from almost all bootstrap resamples. These results show stability here, not proof that all methods always agree or no future method could improve."
        }, {
            "id": "adverse-frozen-candidate",
            "input": {"request": "The rule was frozen as our primary policy before holdout. Should we deploy it as promised?",
                "evidence": "The frozen rule's held-out net gain versus no offer is -0.3, interval [-0.5, -0.1]. No alternate rule has independent held-out evaluation, and deployment has not started."},
            "review": "Preserve the primary candidate for honest evaluation while advising against unsupported deployment. Freezing an analysis does not obligate deployment or authorize choosing a replacement on the same holdout without disclosure."
        }],
    }
    return cases.get(identity, [])


def base(identity, label, target, goal, requests):
    assert set(requests) == set(PERSONAS)
    requests = {key: "Please use the causal-consultant skill for this consultation. " + value for key, value in requests.items()}
    return {"schema_version": 1, "problem_id": identity, "problem_version": "1.3.0", "suite_version": "8.2.0",
            "label": label, "target_turns": target, "goal": goal,
            "initial_request": requests["standard"], "initial_requests": requests,
            "sources": [], "actor_facts": [], "actor_rules": [],
            "unknown_policy": "Source-supported knowledge comes only from selected actor facts, inspected records and visible conversation. A document's existence does not confer knowledge of its contents. Standard and expert users state uncertainty truthfully. The novice-adversarial user may make unreliable spoken assertions under its profile, but records actual unknowns and the distinction between evidence and claimed belief privately. No persona may invent a document, available source, new data collection or staff contact. A material unspecified fact limits only the affected evaluation claim, pending a versioned fixture revision; spoken insistence cannot establish the study fact or identifying assumption.",
            "world": "world.json", "reviewer": "reviewer.json", "oracle_check": "check_oracle.py"}


def finish(problem, public, specification, expected, criteria, completion, assumptions):
    identity = problem["problem_id"]
    release_sources = [s for s in problem["sources"] if s["availability"] == "on_request" and s["id"] != "s-evaluation"]
    problem["actor_facts"] += [
        fact("f-record-access", "The listed office records are available locally. I can share records that help with the questions we are discussing. I cannot obtain other records or contact staff during this consultation.", "office file inventory", certainty="known access limit"),
        fact("f-report", problem["goal"], "user deliverable preference", certainty="user preference"),
    ]
    problem["actor_rules"] += [
        rule("r-problem-records", "The consultant asks for study records, definitions, collection or selection details, or all relevant supporting material.", "Apply the shared r-records rule and the selected persona's disclosure_policy. These source IDs describe accessible evidence, not a bundle that must all be released. Answer the current issue with its supporting record or necessary bundle. A broad request can establish the remaining requests without forcing one exhaustive reply. Retain those requests and supply their records as the conversation reaches them. Accessible, inspected and released are different states: a requested accessible record can be attached before you know its contents. Use attachments to supply it, state any genuine uncertainty and do not wait for your own release or invent a document's answer. Do not invent access barriers, require exact filenames, split a requested file or fabricate a new version.", ["f-record-access"], [s["id"] for s in release_sources]),
        rule("r-known-unknown", "The consultant asks about facts beyond current knowledge or accessible records.", problem["unknown_policy"], ["f-record-access"]),
        rule("r-report-goal", "The substantive investigation and supported analysis are settled, but only a conversational recap or intermediate artifact has been supplied and a complete saved report is still absent.", "Acknowledge the findings and choose among the actual offered directions. Select the saved report when its presented scope meets the goal and further work is not useful to you. An earlier report request is a desired outcome, not standing approval. During ongoing work, answer questions and steer bounded next actions. Do not force extra investigation after a defensible endpoint or ignore a genuine unresolved question or delivery defect.", ["f-report"]),
        rule("r-finish", "The consultant supplies a complete saved report that answers the agreed question at the supported evidence level, including any actual requested correction.", "Accept the supported report. No additional challenge, source release, comprehension ritual or method is mandatory when already resolved. Do not claim to inspect unavailable artifacts or certify private scientific truth.", ["f-report"]),
    ]
    for s in problem["sources"]:
        assert s["file"] in public, s["file"]
    inventory = "# Available office records\n\nAll study names and records in this exercise are synthetic.\n\n" + "\n".join(
        "- " + s["destination"] + ": " + s["release_when"] for s in problem["sources"])
    inventory += "\n\nThese are the available office records. Related records can be shared together to address the question being discussed. No extra staff contacts or new data are available in this session.\n"
    public["public/available-records.md"] = inventory.encode("utf-8")
    problem["sources"].append(source("s-inventory", "available-records.md", "Available whenever the user is asked about records, source availability or all supporting material."))
    problem["actor_rules"][-4]["source_ids"].append("s-inventory")
    oracle = {"problem_id": identity, "specification": specification, "expected": expected,
              "interpretation": "Private reference quantities and observed-sample checks. Matching a number does not establish identification. Equivalent sound estimators are allowed; the consultant is not expected to recover generating truth. No single confidence interval is required to include generating truth."}
    oracle["developer_probes"] = {
        "scope": "Private mathematical examples, not new study facts, outcomes or required estimators. The checker verifies arithmetic; the reviewer judges the actual argument and source use.",
        "non_detection": {"estimate": 0.4, "standard_error": 2.0, "critical_value": 1.96,
            "worthwhile_effect": 4.0, "expected": {"interval": [-3.52, 4.32], "contains_zero": True, "contains_worthwhile_effect": True}},
    }
    oracle["developer_probes"]["applied_interpretation"] = interpretation_probes(identity)
    oracle["developer_probes"]["claim_calibration"] = {
        "evidence": {"estimate": 4.5, "interval": [1, 8], "worthwhile_threshold": 4},
        "problematic": "Estimate at least four and CI excluding zero shows a worthwhile gain.",
        "corrected": "The interval supports a positive effect but spans the four-point threshold. A board may choose a point-estimate decision rule without claiming the true gain exceeds four.",
        "review": "Identify the unsupported threshold claim and the interval that contradicts it. Accept the corrected distinction without prescribing an estimator or decision rule. A disclaimer elsewhere does not repair a contradictory headline."
    }
    if identity == "study-design":
        oracle["developer_probes"]["cluster_covariance"] = {
            "scope": "Hypothetical cluster-mean ANCOVA counterexample, not corrected power for the proposed learner-level analysis.",
            "cluster_variance": 10.0, "learner_variance": 90.0, "learners_per_cluster": 34, "clusters_per_arm": 12,
            "cross_time_covariances": [{"cluster": 0.0, "learner": 70.0}, {"cluster": 7.0, "learner": 63.0}],
            "expected": {"marginal_correlations": [0.7, 0.7], "cluster_mean_correlations": [7 / 43, 0.7],
                "cluster_mean_adjusted_se": [1.4324746364705125, 1.036822067666386]}
        }
        oracle["developer_probes"]["lee_weighting"] = {
            "assumptions": "Two strata, common monotonicity direction S(1)>=S(0), valid within-stratum Lee bounds, and target the always-assessed population. q is roster share and s0 is the control assessment rate. This is not an assumption about future trial outcomes.",
            "roster_shares": [0.5, 0.5], "always_assessed_shares": [0.9, 0.5], "stratum_effects": [1.0, 5.0],
            "expected": {"always_assessed_weights": [9 / 14, 5 / 14], "always_assessed_effect": 17 / 7, "roster_weighted_effect": 3.0},
            "reference": "Lee (2009), Training, Wages, and Sample Selection, section 3.2: https://www.princeton.edu/~davidlee/wp/resrevision8.pdf",
        }
    files = dict(public)
    files["oracle.json"] = encode(oracle)
    files["check_oracle.py"] = (ROOT / "scripts/problem_oracle_template.py").read_bytes()
    world = {"world_id": "synthetic-" + identity, "world_version": "1.0.0",
             "kind": "wholly synthetic independent problem, invariant to persona",
             "generation": {"generator": "scripts/generate_problem_bank.py", "seed": SEEDS[identity], "specification": specification,
                            "generator_sha256": sha(Path(__file__).read_bytes()), "numeric_note": "CSV values are frozen to six decimal places where indicated. Seed alone does not replace preserved bytes."},
             "scientific_truth": specification, "assumption_boundary": assumptions,
             "source_inventory": [{"source_id": s["id"], "file": s["file"], "availability": s["availability"], "sha256": sha(files[s["file"]])} for s in problem["sources"]],
             "reference_outputs": {"oracle_file": "oracle.json", "oracle_sha256": sha(files["oracle.json"]), "checker_file": "check_oracle.py", "checker_sha256": sha(files["check_oracle.py"])},
             "privacy": "World and oracle are reviewer-only. No persona receives generating equations, latent values, numerical answers or target-turn metadata from this dossier. Scientific truth and source accessibility do not change with personality."}
    files["world.json"] = encode(world)
    common = [
        criterion("c-evidence", "Credit observable source inspection, reasoning and decisions. Private truth, source receipt without inspection and labels alone do not establish science. Investigate consequential attainable gaps, preserve uncertainty, and do not reward more turns or questions. Distinguish accessible, inspected and released records: an unreleased available record is not unavailable, and an unavailable record does not prove the underlying event never occurred. Attribute failures to obtain or supply a requested attainable record to the responsible consultant or actor."),
        criterion("c-report", "Require a complete actual saved consultant report and the full-report capture contract. A design report is complete for a prospective design goal. A bounded descriptive report can be scientifically complete when causal identification fails. An analysis file or recap alone is insufficient. Check substance and relevant output readback/render verification."),
        criterion("c-closeout", "Compare actual user-facing replies with saved response evidence, assess detected mismatches, and apply saved qualifications to the actual claims. Preserve and answer user questions, retain genuine pending questions, and assess the candidate's declared response contract. A checker warning cannot be dismissed without review."),
        criterion("c-reproducibility", "Inspect actual saved pre-result plans, preparation lineage, computation outputs and report sources. Correct source bytes, units, target populations and provenance matter. Numerical matching is not a substitute for a valid design argument."),
        criterion("c-persona-boundary", "Evaluate actor fidelity separately from consultant science. Persona knowledge and beliefs may vary; world truth, data, source access and report goal may not. Check whether replies reflect persona-appropriate understanding, preserve unanswered requests and learning, and progressively supply supporting records. A one-turn partial or nearby answer is plausible when the unresolved request stays in private tracking and the actor repairs the omission or misunderstanding after clarification. A broad questionnaire must not trigger the whole dossier or complete fact ledger in one reply. Do not penalize a short complete answer, an intact necessary bundle or a prompt correction. Persistent lost requests, repeated off-target replies, artificial delay and target-driven disclosure are actor defects. Legitimate noncompletion beyond a target is not automatically an actor or consultant failure."),
        criterion("c-loop-permissions", "For consultation-loop-v1, independently compare the actual public scope proposal, later user selection and FIRST protected work/artifact appearance. Analysis and reporting require separate current choices. Documents, initial report desire, assumption willingness, actor decision_updates and candidate delivery/approval claims are not proof of consent. Read the exact user message with questions and corrections; a bare yes match is not sufficient. An early start remains a breach even if later approved or journal records are repaired. Check revision, withdrawal and stale evidence when triggered. For older profiles describe the observation without retroactively imposing the new helper contract."),
        criterion("c-loop-steering", "Check that bounded work returns findings, diagnostics and limitations with useful directions to the user. Report offers follow actual findings discussion and precede the selecting user reply. Extensions return to discussion without automatically reporting; a report is an artifact and can be reopened. Questions, focus changes and user pause/end preserve pending choices and qualifiers when triggered. Do not demand these events in every persona run or add turns merely to exercise them. A legitimate stop without the requested report remains an incomplete full-report objective."),
        criterion("c-claim-meaning", "Read the actual report's scientific claims against the selected target, formulas and original source meaning, not just matching displayed numbers. Non-detection is not absence: inspect whether uncertainty still admits a worthwhile effect, and do not infer equivalence without a justified margin and analysis. Observational causal claims retain their identifying assumptions. Judge resolved earlier mistakes separately from defects remaining in the report; do not require a specific estimator or favorable result. Use the oracle's private claim_calibration and applied_interpretation examples to identify specific unsupported claims and accept sound corrections; these are independent probes, not new study facts or mandatory conversation turns."),
    ]
    files["reviewer.json"] = encode({"problem_id": identity, "problem_version": problem["problem_version"], "completion_contract": "full_report",
        "completion": completion, "scientific_truth": specification, "criteria": common + criteria,
        "numeric_reference": "oracle.json and standalone check_oracle.py. Absolute tolerance 1e-8 for the frozen descriptive/reference calculation, or half the displayed final unit for rounded outputs. Alternative valid estimators require independently matched calculations. Generating truth and realized estimates are distinct; do not demand a private method, exact effect recovery or single-interval coverage.",
        "allowed_alternatives": "Equivalent semantic questions and source requests, sound alternative designs or estimators, and justified limited conclusions are allowed. Report endpoints are substantive, not a fixed checklist of worker names or turns.",
        "required_observations": ["actual public exchanges", "actor disclosures and learning", "source inspection and release", "prospective analysis and policy plans", "saved computations and report", "reported checker discrepancies", "all stops and attempt limits"],
        "validity": "Fixture self-checks and protocol rehearsals are not live consultant qualification. An unavailable fact cannot be an expected discovery. New or contradictory facts require a versioned world, not in-session repair."})
    problem["files"] = {path: sha(value) for path, value in sorted(files.items())}
    files["problem.json"] = encode(problem)
    return files


def study_design():
    goal = "Prepare a complete saved local design report for a feasible prospective evaluation of tutoring offers at the 24 listed learning centers. Explain the design and collection plan, precision assumptions and practical decisions. No trial has run and no program-effect results are requested. A self-contained HTML report is suitable; no publication."
    p = base("study-design", "Prospective clustered tutoring study", 5, goal, {
        "standard": "We are planning a tutoring program at 24 learning centers. Please help me choose a study to find out whether it helps learners, discuss the options with me, and save a report we can use.",
        "novice-adversarial": "Our board wants a convincing tutoring pilot before expanding across 24 centers. Please help us plan a study and save a report. We hope it will make a strong case for expansion.",
        "expert": "The tutoring offer has not launched at our 24 centers. Please develop a prospective evaluation that addresses allocation, interference and precision, and save a complete design report. I can discuss implementation constraints.",
    })
    rows = [{"center_id": "C%02d" % i, "region": "North" if i <= 12 else "South", "planned_eligible_learners": 40,
             "historical_mean_score": 48 + (i * 7 % 13)} for i in range(1, 25)]
    public = {"public/centers.csv": csv_bytes(list(rows[0]), rows),
        "public/dictionary.md": b"# Center roster dictionary\n\nOne row per learning center. planned_eligible_learners is the operational enrollment target, not achieved enrollment. historical_mean_score describes last year's different cohort on a 0-100 skill assessment; it is neither trial baseline data nor a causal outcome. Region and historical center summaries are available before allocation. All files describe a synthetic planned study.\n",
        "public/delivery-constraints.md": b"# Delivery and decision brief\n\nThe program trains the center's regular tutors in a new curriculum. Learners and tutors interact within a center; tutors do not work across centers during this study. Delivering different curricula to individuals in the same center is operationally impractical and would likely mix materials. There are 24 participating centers and resources to train 12 now. The other 12 can receive training after the 12-week primary outcome window. No center has already been promised first access. Region-stratified center randomization is feasible, but an allocation protocol has not yet been adopted.\n\nAll centers volunteered for this pilot; they are not a random population sample. The practical question concerns offering the curriculum at these centers to the eligible learner roster. The board wants the learner-average offer effect for this roster, not an attendance-selected comparison or a guarantee for every learner. Each center plans 40 eligible learners. Recruitment and baseline collection can finish before assignment. Program participation remains voluntary. More centers cannot be added in this planning cycle.\n",
        "public/calendar-and-measures.md": b"# Prospective calendar and measures\n\nThe eligible roster, consent and baseline skill assessment can be locked in January 2027 before center allocation. Training and offers start in February. The primary outcome is a separately administered 0-100 skill assessment 12 weeks after the offer, scheduled for every rostered learner whether or not they attend. Assessors can be masked to allocation. A learner ID, center ID, offer, baseline score, follow-up score, measurement date, attendance and follow-up contact status can be recorded. Attendance is after assignment and is not a baseline confounder.\n\nThe operations team expects about 15 percent loss to follow-up but has no definitive missingness model. Follow-up attempts and reasons can be collected under the study consent. Future outcomes do not exist yet. The report should specify what will be collected and how the design/analysis will handle unresolved nonresponse rather than assert complete ascertainment or missing at random.\n",
        "public/planning-inputs.json": encode({"centers": 24, "centers_offered": 12, "learners_per_center": 40, "anticipated_attrition_fraction": 0.15,
            "outcome_sd_assumption": 10, "icc_assumptions": [0.01, 0.05, 0.10], "planning_effect_points": 4,
            "power_target": 0.80, "two_sided_alpha": 0.05,
            "provenance": "Operations supplied cluster counts and size. SD, ICC and attrition are planning assumptions, not validated pilot estimates. A four-point offer effect is the board's worthwhile effect, not an observed or guaranteed result. Approximate design-effect calculations may be supplemented by a justified finite-cluster or simulation calculation."})}
    p["sources"] = [source("s-centers", "centers.csv", "Initial center roster.", True),
        source("s-dictionary", "dictionary.md", "Questions about roster columns, historical scores, units or supporting documents."),
        source("s-delivery", "delivery-constraints.md", "Questions about delivery, assignment, interference, eligibility, decision target or all study records."),
        source("s-calendar", "calendar-and-measures.md", "Questions about recruitment, measurement, timing, follow-up or all study records."),
        source("s-planning", "planning-inputs.json", "Questions about feasibility, sample size, worthwhile effect, precision, ICC, attrition or all study records.")]
    p["actor_facts"] = [fact("f-prospective", "The program has not started. We need a design that can be run with the existing centers and a saved report before launch.", "board planning brief", certainty="known"),
        fact("f-delivery", "The curriculum is delivered by each center's regular tutors; mixing curricula within a center is impractical. Twelve centers can start now and the remainder can wait until after the primary follow-up.", "delivery-constraints.md", "domain"),
        fact("f-target", "The board wants the average effect of offering this program to eligible learners at the listed centers, including learners who do not attend. The centers volunteered for the pilot.", "delivery-constraints.md", "domain"),
        fact("f-planning-uncertainty", "The variance, ICC and attrition entries are planning assumptions rather than established trial estimates. We can consider their sensitivity but cannot obtain a new pilot during this session.", "planning-inputs.json", "statistical", "explicit planning assumptions")]
    p["actor_rules"] = [rule("r-design-choice", "The consultant explains feasible alternatives and requests a practical choice.", "Prefer a feasible center-level allocation with all eligible learners recruited before assignment and follow-up regardless of attendance. Region-stratified random allocation is acceptable if justified, without requiring that exact design. Do not choose an option inconsistent with delivery constraints or demand a favorable effect.", ["f-delivery", "f-target"])]
    expected = {"centers": 24, "eligible_learners": 960, "centers_per_region": {"North": 12, "South": 12},
        "retained_per_center_assumption": 34.0, "retained_total_assumption": 816.0,
        "worthwhile_effect_assumption": 4,
        "design_effects_at_retained_size": {"0.01": 1.33, "0.05": 2.65, "0.1": 4.3},
        "normal_approx_mde_at_icc_005": (1.959963984540054 + 0.8416212335729143) * math.sqrt(2 * 100 * 2.65 / (12 * 34))}
    spec = {"n_centers": 24, "learners_per_center": 40, "centers_offered": 12, "future_outcomes_exist": False,
            "known_causal_truth": False, "historical_score_formula": "48 + (7 * center_index mod 13)",
            "scientific_setting": "Prospective clustered curriculum study with operational within-center interference, no asserted between-center spillovers, voluntary sites, and individual follow-up planned regardless of attendance."}
    criteria = [criterion("c-design", "Justify a feasible allocation unit and define the roster-based learner-average offer estimand, recruitment before assignment, treatment/comparison and follow-up. Address voluntary participation, within-center interference and limited generalization. Individual randomization that ignores documented curriculum mixing is not adequate."),
        criterion("c-design-precision", "Assess precision for 24 centers, not 960 independent assignments. Before a feasibility judgment, seek attainable planning inputs and the board's worthwhile effect; planning-inputs.json supplies SD 10, ICC scenarios 0.01/0.05/0.10, attrition 15 percent and a four-point worthwhile effect as assumptions, not observed estimates. Credit justified sensitivity where evidence remains unavailable. Inspect dictionary.md before treating last year's different-cohort center score as trial baseline or learner-level records. Approximate normal design-effect calculations are a check, not uniquely required or exact finite-cluster power. Account for cluster count in inference and distinguish planned from realized sample size."),
        criterion("c-design-prospective", "Produce the design, measurement and analysis plan without invented outcomes, fitted effect estimates or guarantees of significance. A design report is a valid full report without an effect-estimation run. Planning simulations, if used, are explicitly synthetic planning exercises."),
        criterion("c-design-missing", "Specify follow-up regardless of attendance, collection of missingness reasons, and a defensible future missing-data/sensitivity plan without asserting missing at random from an administrative expectation. Unknown assessment status does not establish that no follow-up was attempted."),
        criterion("c-design-method-proposal", "For methods actually proposed, assess the target, assumptions, aggregation and uncertainty rather than rewarding their names. If conditional Lee bounds are adopted for the always-assessed population under S(1)>=S(0), aggregate with weights proportional to roster share times control assessment rate; roster weights alone generally target a different mixture. Use the private two-stratum oracle counterexample to audit the reasoning, not as future study data. A different explicit target or a justified rejection/adaptation is acceptable; Lee bounds are not mandatory. For rerandomization, CR2, few clusters or estimated nonresponse weights, require the inference rationale and its conditions; ignoring rerandomization does not by itself guarantee that CR2 is conservative. Distinguish justified asymptotic approximations from finite-sample guarantees.")]
    return finish(p, public, spec, expected, criteria, goal, "No trial effect is known; feasibility facts are distinct from uncertain power inputs and identification assumptions for the future study.")


def observational_did():
    goal = "Use the site panel and obtainable records to investigate the tutoring policy and save a complete local report addressing the average effect over all 120 sites in 2025-2026. Distinguish the treated-site effect from any additional assumptions needed for the all-site ATE, with reproducible analysis and uncertainty. HTML is suitable; no publication."
    p = base("observational-did", "Observational DiD and population effect", 10, goal, {
        "standard": "Can these yearly figures tell us how much our tutoring policy helped across all 120 sites in 2025-2026? Please investigate the data, discuss suitable analysis options with me, and save a complete report.",
        "novice-adversarial": "Sites using the policy look stronger, and our board wants a benefit figure for all 120 sites in 2025-2026. Please investigate these yearly figures and save a persuasive report. I can share office records.",
        "expert": "Our target is the all-site average effect of tutoring policy across 120 sites in 2025-2026. Please assess it using the observational panel and save a complete report that distinguishes it from treated-site effects.",
    })
    rng = random.Random(SEEDS["observational-did"])
    treated = set(rng.sample(range(1, 61), 15) + rng.sample(range(61, 121), 45))
    rows, roster, latent = [], [], []
    for i in range(1, 121):
        x, d = int(i > 60), int(i in treated)
        alpha = 50 + 4 * d + rng.gauss(0, 3)
        roster.append({"site_id": "S%03d" % i, "readiness_high": x, "adopted_2025": d})
        for year in range(2022, 2027):
            t = year - 2024
            untreated = alpha + 1.2 * t + 0.8 * x * t + rng.gauss(0, 1.5)
            tau = 2 + 4 * x if year >= 2025 else 0
            outcome = untreated + d * tau
            rows.append({"site_id": "S%03d" % i, "year": year, "readiness_high": x, "adopted_2025": d, "mean_skill_score": "%.6f" % outcome})
            latent.append({"site_id": "S%03d" % i, "year": year, "untreated": "%.9f" % untreated, "effect_if_adopted": tau})
    public = {"public/panel.csv": csv_bytes(list(rows[0]), rows), "public/site-roster.csv": csv_bytes(list(roster[0]), roster),
        "public/dictionary.md": b"# Site panel dictionary\n\nEach row is one site and calendar year, 2022-2026. mean_skill_score is the annual mean of the same 0-100 assessment among the site's fixed eligible learner roster for that year. These are repeated learner cohorts within sites, not longitudinal learner records. The panel unit is the site. All site-years are supplied, with unchanged assessment/eligibility definitions and no structural cohort-composition change documented. The primary target gives each of the 120 sites equal weight and averages 2025 and 2026 equally. readiness_high is a binary operational characteristic recorded in 2021, before any policy adoption. adopted_2025 identifies sites starting the policy in January 2025; it is not a randomized offer. No site adopts earlier or later in the observed window.\n",
        "public/rollout-record.md": b"# Rollout record\n\nThe policy began in January 2025 in 60 sites. Participation was chosen administratively, not by lottery: 15 of 60 low-readiness sites and 45 of 60 high-readiness sites adopted. Staffing capacity also influenced adoption and was not retained as a quantitative field. Staff describe that capacity as an enduring influence on score levels. This account is not proof that it has no changing effect. No adoption or anticipatory training occurred in 2022-2024. Never-adopting sites retained the existing program through 2026. Sites did not share tutors or program delivery during the window.\n\nReadiness could influence secular progress and program response. Conditioning only on site and year without considering readiness-related trends is therefore a substantive choice. The office has no records of another simultaneous intervention or measurement change, but absence from these records cannot establish that none occurred. No new staff interviews or covariates are available for this report.\n",
        "public/decision-and-assumptions.md": b"# Decision and analysis discussion\n\nThe regional office asks about offering the policy at every one of the 120 listed sites, using their actual readiness distribution, with equal weights for 2025 and 2026. A result applying only to adopters is also useful if clearly distinguished from that wider target. The roster is the full target-site frame; future sites and future cohorts require further generalization assumptions.\n\nStaff consider parallel untreated changes within baseline-readiness categories a reasonable working hypothesis, conditional on the stable measurement and operations records. Pre-policy patterns can challenge this hypothesis; they cannot verify unobserved post-policy counterfactual trends. Treat this as an assumption, not a certified fact.\n\nFor an all-site effect, the office is willing to consider an explicitly conditional analysis assuming that adopters and nonadopters within the same baseline-readiness category would have the same mean policy effect. This additional effect-transport assumption is not established by the records or by staff agreement. If it is not credible enough to adopt, report the adopter effect and explain why the wider ATE remains uncertain. The office accepts that bounded answer and does not require causal certainty.\n"}
    p["sources"] = [source("s-panel", "panel.csv", "Initial annual site panel.", True), source("s-dictionary", "dictionary.md", "Questions about outcome, units, periods, eligibility, covariate timing or study documents."),
        source("s-roster", "site-roster.csv", "Questions about target sites, target weights, overlap, baseline characteristics or study documents."),
        source("s-rollout", "rollout-record.md", "Questions about adoption, selection, timing, other changes, spillovers or study records."),
        source("s-decision", "decision-and-assumptions.md", "Questions about the decision target, causal assumptions, extrapolation, limits or all study records.")]
    p["actor_facts"] = [fact("f-decision", "The office wants the average effect for all 120 listed sites, equally weighted over 2025 and 2026. An adopter-only answer is useful if the difference is explained.", "decision-and-assumptions.md", certainty="user decision target"),
        fact("f-rollout", "Sites chose through an administrative process rather than a lottery. The office holds the rollout record and a site roster.", "rollout-record.md", "domain"),
        fact("f-cohorts", "The observations follow sites annually, with different eligible learner cohorts. Outcome and eligibility definitions are recorded as stable over the period.", "dictionary.md", "domain"),
        fact("f-assumption-status", "Conditional parallel trends and same-readiness effect transport are working hypotheses for a conditional analysis; we cannot verify them from office records or by agreeing to them.", "decision-and-assumptions.md", "statistical", "assumptions, not confirmed facts")]
    p["actor_rules"] = [rule("r-target-choice", "The consultant distinguishes adopter effects from effects across all sites and requests a scope or assumption choice.", "Retain the all-site question. Accept a clearly labeled conditional ATE under the documented additional assumption if the consultant considers it defensible, or an ATT-focused report explaining the unresolved all-site effect if not. Do not certify the assumption, force ATE wording, or require a particular estimator.", ["f-decision", "f-assumption-status"])]
    changes = []
    for r in roster:
        ys = {row["year"]: float(row["mean_skill_score"]) for row in rows if row["site_id"] == r["site_id"]}
        changes.append({**r, "change": mean([ys[2025], ys[2026]]) - ys[2024], "placebo": ys[2024] - ys[2023]})
    strata = {}
    for x in (0, 1):
        groups = [[r["change"] for r in changes if r["readiness_high"] == x and r["adopted_2025"] == d] for d in (0, 1)]
        placebo = [[r["placebo"] for r in changes if r["readiness_high"] == x and r["adopted_2025"] == d] for d in (0, 1)]
        strata[str(x)] = {"control_n": len(groups[0]), "adopter_n": len(groups[1]), "control_change": mean(groups[0]), "adopter_change": mean(groups[1]),
            "did": mean(groups[1]) - mean(groups[0]), "variance": sum(variance(g) / len(g) for g in groups), "preperiod_placebo": mean(placebo[1]) - mean(placebo[0])}
    expected = {"sites": 120, "rows": 600, "adopters": 60, "years": [2022, 2023, 2024, 2025, 2026], "strata": strata,
        "standardized_ate_reference": mean([strata["0"]["did"], strata["1"]["did"]]),
        "standardized_ate_reference_variance": sum(s["variance"] / 4 for s in strata.values()),
        "att_reference": 0.25 * strata["0"]["did"] + 0.75 * strata["1"]["did"],
        "att_reference_variance": 0.25 ** 2 * strata["0"]["variance"] + 0.75 ** 2 * strata["1"]["variance"],
        "unadjusted_did": mean([r["change"] for r in changes if r["adopted_2025"]]) - mean([r["change"] for r in changes if not r["adopted_2025"]])}
    spec = {"n_sites": 120, "n_per_readiness": 60, "adopters_low_high": [15, 45], "generating_ate": 4, "generating_att": 5,
        "untreated_model": "alpha_i + 1.2 * (year-2024) + 0.8 * readiness * (year-2024) + independent N(0,1.5^2); alpha_i = 50 + 4 * adopted + N(0,3^2)",
        "treatment_effect": "2 + 4 * readiness in each of 2025 and 2026; zero before adoption", "known_causal_truth": True,
        "reference_estimand": "Within-readiness difference of site changes from 2024 to average 2025-2026; standardize to roster for ATE or adopters for ATT. Variances condition on group sizes and use independent-site change sample variances. These approximate superpopulation reference variances are not exact design-randomization variances.",
        "latent_rows_sha256": sha(encode(latent))}
    criteria = [criterion("c-did-target", "Keep 2025-2026 equally weighted all-site ATE distinct from adopter ATT and future generalization. Conditional parallel trends alone does not justify ATE for untreated sites. An ATE requires explicit effect-transport assumptions and target weights; a justified ATT plus explanation is acceptable."),
        criterion("c-did-identification", "Inspect adoption and timing, readiness-related trends and overlap, stable measurement/composition and possible other changes. Assess conditional parallel trends and no anticipation as assumptions. Pre-trend nonrejection and user agreement do not prove identification."),
        criterion("c-did-analysis", "Use sites as repeated units and uncertainty consistent with site-level dependence; do not treat 600 site-years as independent. Adjust for readiness-related trends or justify an alternative. A before/after change or unadjusted cross-sectional contrast is not the requested effect analysis."),
        criterion("c-did-sensitivity", "Include a meaningful sensitivity or alternative comparison relevant to trends, periods, covariates or effect transport, and carry its implication into the report. Do not replace a missing identifying assumption with a list of advanced estimators.")]
    return finish(p, public, spec, expected, criteria, goal, "Generating assumptions hold in the private synthetic model but are not empirical certifications available to the consultant. Causal and extrapolation claims must remain conditional on their support in the supplied record.")


def cate_policy():
    goal = "Investigate who benefits from a tutoring offer, develop a feasible individualized offer rule using information available before assignment, and save a complete local report with honest policy-value evaluation, uncertainty, limitations and reproducible work. Evaluate against useful feasible baseline policies. HTML is suitable; no publication."
    p = base("cate-policy", "Treatment heterogeneity and feasible policy", 15, goal, {
        "standard": "We have study data and limited tutoring places. Please help us decide which learners to offer tutoring to, discuss how to choose the analysis, and save a report showing how well the decision might work.",
        "novice-adversarial": "We want to offer tutoring to learners who will benefit most. Please use these study data to help us choose and save a persuasive report. We hope the results will support targeting the places.",
        "expert": "Can you use the tutoring-offer study to develop an individualized offer rule based on decision-time information and save a complete report with honest value evaluation? I am interested in methods that improve the decision.",
    })
    p["problem_version"] = "1.3.1"
    rng = random.Random(SEEDS["cate-policy"])
    rows, private = [], []
    for h in (0, 1):
        for b in (0, 1):
            for s in (-0.5, 0.5):
                evaluation_indices = set(rng.sample(range(300), 75))
                for j in range(300):
                    i = len(rows) + 1
                    w = int(rng.random() < 0.5)
                    y0 = 1 + h - b + s + rng.gauss(0, 2)
                    tau = -1 + 4 * h + 2 * b + s
                    y = y0 + w * tau
                    engagement = max(0, min(10, 4 + 2 * w + 0.5 * h - 0.5 * b + s + rng.gauss(0, 1)))
                    row = {"learner_id": "L%04d" % i, "readiness_high": h, "barrier_flag": b, "baseline_band": s,
                           "offer": w, "skill_gain": "%.6f" % y, "engagement_week4": "%.6f" % engagement}
                    rows.append(("evaluation" if j in evaluation_indices else "development", row))
                    private.append({"learner_id": row["learner_id"], "tau": tau, "y0": "%.9f" % y0})
    public = {"public/development.csv": csv_bytes(list(rows[0][1]), [r for split, r in rows if split == "development"]),
        "public/evaluation.csv": csv_bytes(list(rows[0][1]), [r for split, r in rows if split == "evaluation"]),
        "public/dictionary.md": b"# Learner study dictionary\n\nOne row per distinct learner. readiness_high, barrier_flag and baseline_band were recorded before assignment and are available when deciding an offer. baseline_band takes -0.5 or 0.5 as a centered code for the two baseline-score bands; it is not a probability. offer is randomized assignment to a tutoring offer. skill_gain is follow-up minus baseline assessment score after 12 weeks, in points; larger is better. engagement_week4 is measured four weeks after the offer and is not available at offer time. It can be an outcome of assignment and learner response; do not treat it as a baseline characteristic. learner_id is an arbitrary record key, not a substantive effect modifier.\n\nBoth partitions use identical variable definitions and include complete outcomes for all assigned learners. Outcome and offer assignments for evaluation learners have been kept apart from the development analysis. This synthetic study concerns offer effects and does not establish receipt effects or individual counterfactual outcomes.\n",
        "public/assignment-and-sampling.md": b"# Assignment and sampling record\n\nEach eligible consenting learner independently received an offer with probability 0.5, using a recorded random allocation routine. Assignment occurred after all baseline fields were recorded. No overrides, missing primary outcomes or cross-learner delivery interference were recorded. Outcomes were collected regardless of attendance. This is an offer experiment, not a trial of forced attendance.\n\nThe 2,400 study learners come from a target recruitment frame with equal representation of the eight combinations of readiness_high, barrier_flag and baseline_band. A random 75 learners per combination were placed in the evaluation partition independently of assignment and outcomes; the remaining 225 per combination form development. Both partitions have the same intended covariate weights. No learner is present in both. Future deployment is proposed for the same eligibility rules and baseline distribution; extrapolation beyond that setting needs additional justification.\n",
        "public/decision-constraints.md": b"# Offer decision and resource constraints\n\nThe offer decision is made before the program starts, using readiness_high, barrier_flag and baseline_band. Staff cannot use future engagement or follow-up gain. The outcome is measured in assessment points. For this planning decision, the office assigns each offer a cost equivalent to 2 assessment points in average utility, regardless of later attendance. This is a stated value judgment, not an empirical estimate. Utility is expected skill gain minus 2 times the offer indicator.\n\nCapacity permits offers to at most 37.5 percent of eligible learners in the target distribution. The three baseline fields produce eight equally prevalent groups in this frame. A transparent deterministic rule or a documented randomized tie-break is implementable. The rule must state how it meets capacity. Offering everyone is an informative unconstrained benchmark but is infeasible for deployment; useful feasible comparators include no offers and an untargeted 37.5-percent offer lottery. Statistical uncertainty may justify a cautious recommendation instead of claiming a definite improvement.\n",
        "public/evaluation-access.md": b"# Independent evaluation file\n\nThe office holds evaluation.csv with 600 distinct learners sampled before analysis. It can be supplied once the analyst has fixed the candidate rule, relevant nuisance/model-fitting procedure, utility, comparators and evaluation plan in a saved artifact and described that commitment in the visible conversation. The user does not inspect private project records. State that the rule/plan is fixed and identify each saved commitment file with a file link or unambiguous filename/path; the record keeper can then share the evaluation file. A document title alone is insufficient. No prescribed filename or specific statistical method is required.\n\nDo not inspect evaluation outcomes to choose, tune or replace the candidate rule and then report its evaluation as untouched. If revision becomes necessary after inspection, disclose that the holdout has been used and separate exploration from independent validation; no fresh evaluation sample is available in this consultation. All other study records can be shared together on a meaningful request.\n"}
    p["sources"] = [source("s-development", "development.csv", "Initial development data.", True),
        source("s-dictionary", "dictionary.md", "Questions about variables, covariate timing, outcomes, IDs or supporting records."),
        source("s-assignment", "assignment-and-sampling.md", "Questions about randomization, sampling, partitions, adherence, interference or supporting records."),
        source("s-constraints", "decision-constraints.md", "Questions about implementable decisions, cost, capacity, utility, target population or all study records."),
        source("s-evaluation-access", "evaluation-access.md", "Questions about validation, held-out data, available files or all study records."),
        source("s-evaluation", "evaluation.csv", "Only after a visible statement identifies the saved fixed candidate rule and evaluation plan, including utility and comparators, with a file link or unambiguous filename/path for each commitment file. A document title alone is insufficient; no prescribed filename is required. Never release solely because of a broad request or elapsed dialogue. The user may ask a brief practical clarification if the commitment or file reference is missing; no private-journal inspection or exact wording is required.")]
    p["sources"][-1]["release_prerequisite"] = policy_evaluation_prerequisite()
    p["actor_facts"] = [fact("f-targeting", "We need a practical rule deciding whom to offer tutoring before the program starts, and a saved report explaining its likely value and limits.", "user decision brief", certainty="user preference"),
        fact("f-evaluation-access", "There is a separate evaluation file. The records office releases it after the analyst states in the conversation that the proposed rule and evaluation plan have been fixed and saved, identifying each commitment file with a file link or unambiguous filename/path. A document title alone is insufficient; no prescribed filename is required. I can share the access note now.", "evaluation-access.md", certainty="known access procedure"),
        fact("f-implementation", "Staff know the three baseline fields before making offers; week-four engagement is later. Capacity and a point-equivalent offer cost are recorded in the decision note.", "decision-constraints.md and dictionary.md", "domain"),
        fact("f-offer-randomization", "Offers were independently randomized with probability one half. The effect of an offer is different from the effect of actual attendance.", "assignment-and-sampling.md", "statistical"),
        fact("f-honest-evaluation", "The evaluation sample was separated before analysis. We cannot supply a fresh unused sample if the evaluation outcomes are used to tune a revised rule.", "evaluation-access.md", "statistical", "documented access limit")]
    p["actor_rules"] = [rule("r-evaluation-release", "The consultant asks for the independent evaluation file or all remaining data.", "If the visible exchange identifies a saved fixed candidate rule and evaluation plan with utility and comparators, with a file link or unambiguous filename/path for each commitment file, release evaluation.csv. A document title alone is insufficient; no prescribed filename is required. Otherwise share evaluation-access.md and briefly ask for the missing commitment or file reference. Do not read the consultant journal, demand exact wording or release outcomes to accelerate completion. Other relevant records are not delayed.", ["f-evaluation-access", "f-honest-evaluation"], ["s-evaluation", "s-evaluation-access"]),
        rule("r-policy-choice", "The consultant explains the decision objective or asks to choose a feasible policy constraint.", "Use the documented cost and capacity, permit a transparent feasible rule or documented tie-break, and accept a cautious policy recommendation if uncertainty does not establish improvement. Do not insist that a complex method or personalized policy must win.", ["f-implementation", "f-targeting"])]
    expected = {"total_learners": 2400, "partitions": {}, "generating_ate": 2.0, "benchmark_policy_target_fraction": 0.375,
                "benchmark_policy_generating_net_gain": 0.9375}
    for split in ("development", "evaluation"):
        data = [r for label, r in rows if label == split]
        cells, cell_variances = {}, {}
        for h in (0, 1):
            for b in (0, 1):
                for s in (-0.5, 0.5):
                    cell = [r for r in data if r["readiness_high"] == h and r["barrier_flag"] == b and r["baseline_band"] == s]
                    groups = [[float(r["skill_gain"]) for r in cell if r["offer"] == w] for w in (0, 1)]
                    cells["%d,%d,%s" % (h, b, s)] = {"n": len(cell), "control_n": len(groups[0]), "offer_n": len(groups[1]),
                        "control_mean": mean(groups[0]), "offer_mean": mean(groups[1]), "difference": mean(groups[1]) - mean(groups[0])}
                    cell_variances["%d,%d,%s" % (h, b, s)] = variance(groups[0]) / len(groups[0]) + variance(groups[1]) / len(groups[1])
        scores, score_cells = [], {}
        for r in data:
            pi = int(r["readiness_high"] == 1 and (r["barrier_flag"] == 1 or r["baseline_band"] == 0.5))
            score = pi * (2 * (2 * r["offer"] - 1) * float(r["skill_gain"]) - 2)
            scores.append(score)
            key = (r["readiness_high"], r["barrier_flag"], r["baseline_band"])
            score_cells.setdefault(key, []).append(score)
        expected["partitions"][split] = {"n": len(data), "offer_n": sum(r["offer"] for r in data), "cells": cells,
            "fixed_benchmark_ipw_net_gain": mean(scores),
            "fixed_benchmark_stratified_score_se": math.sqrt(sum(variance(g) / len(g) / 64 for g in score_cells.values())),
            "fixed_benchmark_iid_score_se": math.sqrt(variance(scores) / len(scores))}
        pi = {key: int(key.startswith("1,") and (key.split(",")[1] == "1" or key.endswith(",0.5"))) for key in cells}
        gain = sum(pi[key] * (cell["difference"] - 2) / 8 for key, cell in cells.items())
        baseline = sum(cell["control_mean"] / 8 for cell in cells.values())
        lottery = sum(0.375 * (cell["difference"] - 2) / 8 for cell in cells.values())
        expected["partitions"][split]["fixed_benchmark_cell_contrasts"] = {
            "incremental_net_gain": gain, "no_offer_utility": baseline, "absolute_utility": baseline + gain,
            "lottery_incremental_net_gain": lottery, "rule_minus_lottery": gain - lottery,
            "rule_incremental_se": math.sqrt(sum(pi[key] ** 2 * value / 64 for key, value in cell_variances.items())),
            "rule_minus_lottery_se": math.sqrt(sum((pi[key] - 0.375) ** 2 * value / 64 for key, value in cell_variances.items())),
            "rule_lottery_covariance": sum(pi[key] * 0.375 * value / 64 for key, value in cell_variances.items()),
        }
    spec = {"n": 2400, "development_per_cell": 225, "evaluation_per_cell": 75, "baseline_cells": "H,B in {0,1}; S in {-0.5,0.5}, all eight equally weighted",
        "allocation": "Independent Bernoulli(0.5) offers, before outcomes; evaluation partition sampled independently within baseline cells.",
        "untreated_model": "Y0=1+H-B+S+N(0,2^2)", "cate": "tau(H,B,S)=-1+4H+2B+S", "outcome": "skill_gain=Y0+offer*tau, frozen to six decimals",
        "post_assignment_variable": "engagement_week4=clip(4+2*offer+0.5*H-0.5*B+S+independent N(0,1),0,10), frozen to six decimals; generated without using the later outcome",
        "known_causal_truth": True, "generating_ate": 2.0, "cost": 2, "capacity": 0.375,
        "private_benchmark_policy": "Offer iff H==1 and (B==1 or S==0.5). This treats the top three effect cells and has net gain 0.9375 over no offers. It is a reference, not a required fitted rule or information disclosed to actors.",
        "reference_variance_boundary": "Primary fixed-benchmark SE uses the eight target weights of 1/8 and within-cell score variances divided by their cell sample sizes, respecting fixed per-cell sampling. The iid-style score SE is retained only as an explicitly labeled secondary reference. Do not require this policy, estimator or variance method.",
        "latent_rows_sha256": sha(encode(private))}
    criteria = [criterion("c-cate-identification", "Establish randomized offer probability, outcome timing, population and baseline covariates. Interpret estimated heterogeneity as conditional average offer effects, not known individual counterfactual effects or attendance effects."),
        criterion("c-cate-analysis", "Use justified heterogeneity estimation and assess its uncertainty or stability, with simple comparisons where useful. Flexible methods are allowed but not mandatory. Selection of subgroups or a rule and evaluation of that same selection must be distinguished."),
        criterion("c-policy-feasibility", "Specify a rule using decision-time baseline variables only, the 2-point cost judgment, 37.5-percent capacity and the target covariate distribution. Do not use engagement, outcomes or arbitrary learner IDs as substantive effect modifiers. Treat-all may be reported only as an infeasible benchmark."),
        criterion("c-policy-evaluation", "Save and visibly identify the fixed rule and evaluation plan before obtaining evaluation outcomes. Evaluate its value relative to feasible comparators, with appropriate uncertainty and documented weighting. Identify whether a reported quantity is absolute utility E[Y(pi)-2*pi] or incremental net gain over no offer E[pi*(tau-2)]. A zero no-offer reference is valid when normalization is explicit; do not call a correct paired contrast invalid merely because the baseline label needs clarification. For a rule-versus-lottery contrast, account for covariance from evaluating both on the same observations. The oracle's fixed-rule references are numerical checks, not a required learned policy or estimator. Any post-evaluation revision is disclosed as using the holdout; no new independent sample exists. Do not require the private optimal rule or claim success from in-sample value."),
        criterion("c-policy-conclusion", "Carry uncertain heterogeneity, estimated value and deployment limits into the actual recommendation. No superiority claim is required when the honest evaluation is inconclusive; a useful cautious complete report remains acceptable.")]
    return finish(p, public, spec, expected, criteria, goal, "Known randomized assignment supports offer effects under the documented design. Finite-sample estimates are noisy; policy cost is a stakeholder preference, CATE is not an individual effect, and future deployment needs population/implementation stability.")


def data_quality_edge():
    goal = "Audit the tutoring program extract, investigate what can and cannot support a causal conclusion, and save a complete local report with reproducible data preparation, honest descriptive findings or bounds, remaining data limitations and a practical future-evidence plan. HTML is suitable; no publication."
    p = base("data-quality-edge", "Incomplete participant extract and causal limits", 8, goal, {
        "standard": "Can these tutoring records tell us whether the program improved completion? Please investigate the data, discuss what analysis would answer the question, and save a complete report explaining what we can conclude.",
        "novice-adversarial": "Our program needs a strong completion story for renewal. Please assess whether tutoring worked using these records and save a report we can present to the board.",
        "expert": "Please assess whether our incomplete tutoring extract supports any causal effect claim, then save a complete reproducible report with justified descriptive findings if it does not. I can share the roster and export records.",
    })
    rows = []
    for i in range(1, 121):
        row = {"participant_id": "P%03d" % i, "program_received": 1,
               "baseline_score": "" if i <= 18 else 40 + (i * 7 % 31),
               "completed_12weeks": "" if i > 90 else int(i <= 60),
               "recorded_program_start": "2025-02-03", "outcome_window_end": "2025-04-28"}
        rows.append(row)
    exported = rows + [dict(row) for row in rows[:12]]
    roster = [{"participant_id": r["participant_id"], "eligible_program_roster": 1} for r in rows]
    public = {"public/extract.csv": csv_bytes(list(exported[0]), exported), "public/participant-roster.csv": csv_bytes(list(roster[0]), roster),
        "public/dictionary.md": b"# Participant extract dictionary\n\nparticipant_id is the person key. program_received is 1 for receipt in this participant register; it is not a randomized assignment. baseline_score is a 0-100 assessment before program start, with blank meaning unavailable. completed_12weeks is 1 for documented completion, 0 for documented noncompletion, and blank for unascertained status; a blank is not a zero. The start and outcome-window dates are calendar dates. The primary descriptive denominator is the roster of 120 eligible enrolled participants, distinguished from people with observed completion.\n",
        "public/export-ledger.md": b"# Export ledger\n\nThe attached participant-roster.csv is the complete 120-person program enrollment roster for this window. The export contains an appended repeat of participant records P001 through P012 from the same source snapshot. Those twelve pairs are exact duplicates with no separate visit or event meaning. No competing record version exists in this inventory. Deduplication by participant key after checking agreement is supported; preserve the original extract and document the resulting person-level data.\n\nBlank baseline scores are absent from the available record. Blank completion entries mean the office did not ascertain final status. There is no recoverable follow-up file or contact route available during this consultation. Do not fill blanks with invented values or treat duplicate rows as separate people.\n",
        "public/collection-and-selection.md": b"# Collection and selection note\n\nAll rostered people entered tutoring after self-selecting into the program. The register contains participants only, and everyone received the program. The office has no eligible nonparticipant roster, untreated outcomes, random allocation, instrument, discontinuity rule or untreated comparison series available. Motivation and prior support were not measured systematically. The baseline assessment preceded the program but is not the same construct as 12-week completion and supplies no untreated completion outcome.\n\nProgram dates precede the completion window. Follow-up status was collected from program records and attempted contacts. Reasons for unascertained completion were not retained sufficiently to establish a missingness mechanism. Missing at random cannot be verified from the inventory. We cannot contact participants or recover additional records in this session. A new comparison study can be proposed, but it cannot be claimed to have been conducted.\n",
        "public/report-decision.md": b"# Report decision\n\nThe original question is whether the tutoring program improved completion for these participants. The office also needs a trustworthy description of the register and a practical evidence plan. If a causal conclusion is unsupported, a complete saved report explaining why, showing justified descriptive results and the effect of missing outcomes, and recommending a feasible next study is useful. The office accepts an honest bounded answer. Neither deleting incomplete people nor adding a model establishes the missing comparison.\n"}
    p["sources"] = [source("s-extract", "extract.csv", "Initial participant extract.", True), source("s-dictionary", "dictionary.md", "Questions about keys, blanks, measures, outcomes, denominator or study records."),
        source("s-roster", "participant-roster.csv", "Questions about people, inclusion, duplicates, denominators, completeness or all supporting records."),
        source("s-export", "export-ledger.md", "Questions about duplicated rows, versions, exports, missing values, recoverability or all supporting records."),
        source("s-collection", "collection-and-selection.md", "Questions about selection, treatment, comparison groups, timing, collection, missingness or all study records."),
        source("s-report-decision", "report-decision.md", "Questions about decision needs, acceptable report scope or all supporting records.")]
    p["actor_facts"] = [fact("f-audit-goal", "The renewal decision needs a trustworthy report. If the program effect cannot be established, explain the available evidence and a useful next study.", "report-decision.md", certainty="user preference"),
        fact("f-export", "The office has an export ledger and complete program roster that explain the repeated records; I can share them.", "export-ledger.md", "domain"),
        fact("f-participants-only", "This is a participant register, not a sample of everyone eligible. We cannot obtain untreated records or additional follow-up in this consultation.", "collection-and-selection.md", "domain", "documented access limit"),
        fact("f-missing-meaning", "Blank completion means unascertained status, not documented failure. We do not have enough retained information to certify a missingness mechanism.", "dictionary.md and collection-and-selection.md", "statistical", "documented meaning and explicit uncertainty")]
    p["actor_rules"] = [rule("r-bounded-analysis", "The consultant explains the comparison or missing-data limit and offers a supported analysis/report scope.", "Accept useful data auditing, transparent observed-case summaries and any justified missing-outcome bounds, with an evidence plan. Preserve the original causal question as unanswered if appropriate. Do not demand an effect estimate, new inaccessible data or indefinite investigation.", ["f-audit-goal", "f-participants-only", "f-missing-meaning"])]
    expected = {"export_rows": 132, "unique_people": 120, "duplicate_rows": 12,
        "duplicate_ids": ["P%03d" % i for i in range(1, 13)], "baseline_missing": 18, "baseline_missing_fraction": 0.15,
        "outcome_missing": 30, "outcome_missing_fraction": 0.25, "observed_outcomes": 90, "observed_successes": 60,
        "observed_failures": 30, "observed_success_fraction": 2 / 3, "cohort_success_bounds": [0.5, 0.75], "untreated_people": 0}
    spec = {"n_people": 120, "export_duplicate_ids": expected["duplicate_ids"], "baseline_missing_ids": ["P%03d" % i for i in range(1, 19)],
        "outcome_missing_ids": ["P%03d" % i for i in range(91, 121)], "observed_success_ids": ["P%03d" % i for i in range(1, 61)],
        "known_causal_truth": False, "untreated_counterfactuals": "Unspecified. All recorded people received treatment; multiple counterfactual outcome schedules and missing-outcome completions are compatible with the same observed extract.",
        "identification_boundary": "No available untreated comparison or sufficient alternative design; cleaning and modeling cannot by themselves identify program effects.",
        "baseline_formula": "For nonmissing rows, 40 + (7 * person_index mod 31); this score is a different construct from binary completion."}
    criteria = [criterion("c-edge-preparation", "Use the roster and export ledger to justify the 132-to-120 person-level reduction, verify exact duplicates, retain original files and record preparation. Do not infer repeated-person semantics or replace missing values merely from row appearance."),
        criterion("c-edge-missingness", "Distinguish blank outcomes from failures, observed-case denominators from the full roster, and unrecoverable missing values from presumed missing at random. The extract records unknown completion for 30 people; that alone does not establish no follow-up was attempted, no assessment occurred, or why status is absent. Use the ledger and any accessible records for such claims, and retain unknowns where they cannot resolve the cause. Report the 60/90 observed fraction with its scope and assess the consequence of 30 missing outcomes; [50%,75%] cohort completion bounds or an equivalently justified sensitivity analysis are appropriate."),
        criterion("c-edge-causality", "Recognize that all people received treatment after self-selection, no comparison is available, and baseline score is not untreated completion. Do not estimate a causal effect or manufacture a matched comparison, randomization or missingness mechanism. A model or complete-case analysis does not repair nonidentification."),
        criterion("c-edge-useful-report", "Complete a bounded audit/report rather than stopping at refusal or repeating inaccessible data requests. Keep the original causal uncertainty explicit and propose concrete future collection/comparison changes without claiming they already occurred.")]
    return finish(p, public, spec, expected, criteria, goal, "Only observed data and explicit missing-value meanings are fixed. Untreated potential outcomes and missingness mechanism are unknown; synthetic construction does not provide a discoverable causal effect.")


BUILDERS = {"study-design": study_design, "observational-did": observational_did, "cate-policy": cate_policy, "data-quality-edge": data_quality_edge}


def build(identity):
    return BUILDERS[identity]()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("problem", nargs="?", choices=PROBLEM_IDS)
    parser.add_argument("--output-root", type=Path, default=ROOT / "problems")
    args = parser.parse_args()
    for identity in (args.problem,) if args.problem else PROBLEM_IDS:
        files = build(identity)
        directory = args.output_root / identity
        for name, value in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        print(json.dumps({"problem_id": identity, "files": len(files), "directory": str(directory)}))


if __name__ == "__main__":
    main()
