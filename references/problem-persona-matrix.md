# Test catalog: matrix and standalone cases

Choose either a reusable problem/persona pair or a standalone case. Four
problems crossed with three general personas give 12 matrix pairs. RGGVY with
its fixed Research Coordinator and four prospective planning cases add five
standalone cases, for 17 active configurations. An omitted matrix persona
selects `standard`; standalone cases do not accept a persona selector.

The matrix and RGGVY test a continuing full-report consultation loop. The four
planning cases have focused planning endpoints. In a full-report case,
initial report desire does not pre-approve the
analysis or final report. The persona responds to actual proposed scopes and
findings, selects useful extensions or the report, and retains changed choices.
An extension returns to discussion. A report can be reopened, and a user may
pause or end without it; a missing report leaves the full-report goal incomplete.
For general personas, do not manufacture these paths or extra turns in every run. Independent review
checks actual proposal/choice/work chronology, not a preferred conversation length.

## Reusable problems

| Selector | Work | Target replies | Required saved endpoint |
|---|---|---:|---|
| `study-design` | Design a prospective tutoring study under allocation, implementation, measurement and resource constraints | 5 | Prospective design report: protocol, estimand, data collection, analysis plan, planning uncertainty and unresolved decisions. No invented trial outcomes. |
| `observational-did` | Analyze observational adoption in a panel with different covariate distributions and heterogeneous effects | 10 | Reproducible DiD report distinguishing ATT from the requested population ATE, with justified assumptions, uncertainty and limitations. |
| `cate-policy` | Estimate heterogeneous effects and learn a feasible individualized treatment rule from randomized data | 15 | CATE and policy report with decision-time covariates, costs/capacity, a saved rule and separate-sample evaluation, reproducible code and deployment limits. |
| `data-quality-edge` | Audit duplicates, missing measurements and an extract without an untreated comparison | 8 | Reproducible audit and bounded findings report: correct denominators, missingness limits, causal nonidentification and a feasible future-study plan. |

The original four worlds are explicitly synthetic. Private generating facts and numerical
references support evaluation; they are not evidence the consultant or user may
inspect. Public operational records and documented unknowns determine what the
consultation can establish. Accept valid alternative methods within that scope.

Conditional parallel trends does not by itself make a DiD ATT into a population
ATE. The report must justify an additional assumption-dependent extension, or
retain ATT and explain why ATE is unsupported. The policy problem releases
evaluation outcomes after the rule and evaluation plan are fixed, protecting
honest evaluation rather than prescribing a conversation length. Related
records may be supplied together to resolve the current issue. Cleaning the edge-case data does not provide
the missing causal comparison.

## Standalone cases

| Selector | Fixed user and purpose | Endpoint and reply bounds |
|---|---|---|
| `rggvy-electrification` | Research Coordinator investigating real Chhattisgarh electrification data and a household-welfare briefing | Saved defensible report plus required continuity participation; 8 to 12 delivered replies; 50 words and two items per message. |
| `masks-planning` | Planner preparing a French winter mask-campaign study | Useful collection and conditional analysis plan; descriptive 8 to 10 replies, cap 12, no minimum; 50 words and one small item. |
| `forest-planning` | Planner preparing a Peruvian rural-assistance and forest-clearing study | Same focused planning contract. |
| `medication-planning` | Planner preparing an English medication and depression study | Same focused planning contract. |
| `surgery-planning` | Planner preparing a South African surgical-care study | Same focused planning contract. |

See the [standalone guide](../standalone/README.md) for package layout and the
planning cases' disclosure rules. RGGVY has no known causal effect for scoring;
its paper supplies evidence, not an answer key. Its [scientific guide](rggvy-electrification.md)
and [continuity contract](rggvy-continuity.md) govern the fixed coordinator case.
It inherits no expert proposal quota, deception permission or mandatory extra analysis.

## Reusable personas

| Selector | Initial understanding and interaction |
|---|---|
| `standard` | Typical user who initially leaves collection context unvolunteered, asks how to choose an analysis, and may explore two distinct stronger claims before accepting justified limits and a saved report |
| `novice-adversarial` | Limited statistical fluency combined with finite pressure for a preferred, certain or convenient conclusion; learns from clear explanations and retains a route to an honest report |
| `expert` | Combined domain and statistical expertise; actively proposes at least two distinct methodological or alternative analysis ideas on nonconsecutive user turns, accepts reasoned rejection or improvement, and seeks a supported report |

The persona selects practical, domain and statistical initial knowledge tiers
from the problem. All personas have the same legitimate source access. Each has
an explicit `disclosure_policy`: answer the current issue, supply its supporting
record or connected bundle, and retain other requests for later discussion.
A standard user may need a focused follow-up; a novice-adversarial user may
need help recognizing relevance; an expert can connect several
facts without supplying the whole study history. A broad questionnaire does not
trigger every available source. Short answers, necessary bundles and known
corrections stay intact. No persona invents access barriers or acquires facts
from the answer key. Learning and unfinished requests persist on resume.

The three general profiles own reusable interaction behavior. The problem supplies
study facts and concrete opportunities, without imposing the standard user's
claim requests on the expert. The previous `novice`, `domain-expert`,
`statistician` and `adversarial` profiles are preserved under
`archive/personas-v7.3.2/`, outside the active catalog. Existing frozen runs keep
their original profiles unchanged.

Before selecting the final report, the expert must propose two ideas separated
by at least one substantive user reply without a new proposal. The ideas must
differ in analytical purpose, assumptions or comparison, rather than only a
method name or tuning choice. They are concrete suggestions for discussion;
the consultant may justify rejecting or improving either idea. No implementation
quota or stronger-claim demand applies. Prior consultant discussion does not
retire this required expert contribution, and no particular methods are scripted.

## Pacing and stopping

For the 12 matrix pairs, the 5/10/15/8 values are descriptive expectations, not deadlines, exact lengths,
minimums, hard limits or success criteria. They stay in operator/reviewer metadata
and are not supplied in actor packets or consultant prompts. The actor must not
rush a report, dump all facts, invent an answer, manufacture delays, withhold
information or add exchanges to meet a target. Depending on the persona and
consultant, sufficient information may arrive before or after that number.
New coordinator 1.1.0 compositions are a narrow exception: ordered substantive
participation and minimum eight delivered replies, with actual configuration cap
twelve. The [case guide](rggvy-continuity.md) defines that contract without a
method sequence; frozen coordinator 1.0.0 attempts retain their descriptive rules.

The standard persona progresses by meaning: investigation first, method choices
and tradeoffs over focused exchanges, two finite opportunities to request
stronger claims, then report selection and verification. The novice-adversarial
profile applies its bounded pressure and learning rules; the expert contributes
the two distinct, separated analysis ideas without a required claim-pressure
sequence. The selected problem supplies
study-specific context. Events respond to an actual proposal
or finding and allow an honest resolution. They are not a script tied to reply
numbers. A relevant question makes its record or necessary bundle available
without an arbitrary delay. Keep remaining compound requests in private history.
An untriggered optional pressure is a coverage limit, not a reason to pad the run.
An explicit user or operator stop before both expert ideas leaves that coverage
incomplete. Forgetting an idea or prematurely selecting the final report is an
actor-fidelity issue. The substantive reply between proposals must advance the
discussion; an empty acknowledgment cannot supply the required separation.

Each matrix pair and RGGVY require their appropriate saved report. An early complete report
can finish early once the selected persona's required contributions are complete;
reaching a target does not complete unfinished work. No extra
recap is mandatory. A complete honest report can retain an unidentified causal
effect when that is the evidence boundary. Promised corrections remain work.
The four planning cases instead stop at an accepted useful plan, with no report
or numerical effect required. Their expected 8 to 10 replies are descriptive,
not a minimum or an instruction to reveal every fact card.

Freeze separate operational limits before dispatch. The composer suggests
40 consultant replies for general personas. New coordinator 1.1.0 instead requires
the hard 12-reply ceiling in the actual configuration and manifest,
with four active hours and twelve elapsed hours, independently
of the target. The runner enforces the actual configuration's limits; explicitly
set and record those. A resource stop is incomplete, not a reason for the actor
to accelerate. The four planning cases also use an actual ceiling of 12, without
RGGVY's minimum or ordered participation. Preserve older runs' original limits and outcomes.

## Programmer interface

Use the existing shared Python installation from the testing skill directory:

```sh
python scripts/compose_case.py --list
python scripts/compose_case.py --problem observational-did --persona standard --output /private/cases/run001
python scripts/compose_case.py --standalone rggvy-electrification --output /private/cases/run002
python scripts/compose_case.py --standalone masks-planning --output /private/cases/run003
python scripts/session_driver.py preflight --case /private/cases/run001 --candidate /skills/causal-consultant --config /private/config.json
python scripts/session_driver.py start --case /private/cases/run001 --candidate /skills/causal-consultant --config /private/config.json --attempt /private/attempt001 --work /public/work001
```

For a matrix pair, change either selector, for example `cate-policy` with `expert`
or `data-quality-edge` with `novice-adversarial`. For a standalone case, use only
`--standalone` and `--output`; `--persona` is rejected. The old
`--problem rggvy-electrification` command remains an alias for the fixed coordinator,
optionally with its exact `--persona rggvy-research-coordinator`; the three general
personas are rejected for RGGVY. Paths are illustrative: use fresh,
neutral host directories and the [runner guide](runner.md). Public work paths
must not reveal the hidden problem/persona identity.

Composition checks problem hashes, copies its scientific materials unchanged,
selects initial user knowledge and wording, and freezes a normal `case.json`
accepted by the existing runner. It does not launch a consultation. Existing
output directories are rejected. Changing a definition changes composition
identity; never edit a running case.

A selected pair or standalone case is one test. Full-matrix coverage is 12
independent attempts; full-catalog coverage is 17 including the five standalone
cases. An omitted matrix persona selects `standard`. Clarify unclear campaign
scope before launching. A subset must identify configurations not exercised.

## Evidence and maintenance

Maintain four folders under `problems/` and three general profiles under
`personas/`. The five fixed cases live under `standalone/`: RGGVY groups its
`problem/`, `persona.json` and `continuity-variant.json`; each planning case is
a self-contained frozen package. Generated run copies belong to
private run directories and retain versions, composition hashes and source bytes.
The old 15 fixed bundles under `cases/` have been removed, along with their
dedicated generators and tests. The private RGGVY continuity resource extends
behavior and review without changing the scientific problem. Prior versions remain in Git history and
existing frozen run packages; composing a new case never modifies an old run.

Validate every combination, science/source invariance, knowledge boundaries,
numerical references and regeneration. Fixture validation does not establish
live model behavior or host qualification. Review actual replies and artifacts:
a saved answered status or correct hash is not a scientific guarantee. Record
qualification loss and response discrepancies even when the main conclusion is
correct. Compare actual duration descriptively, without grading proximity to
the target for ordinary pairs. For coordinator 1.1.0 separately report numeric
bounds, required public event occurrence and actual gap, report completion and
consultant quality. Neither eight replies nor observed coverage certifies success.
Required scientific work determines depth; missing stress events leave completion
incomplete, and exercised consultant failures remain findings.
