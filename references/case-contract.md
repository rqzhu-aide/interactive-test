# Frozen Case Contract

For fixture authors and run operators. The matrix and standalone catalog cases
use this contract and the shared validator described in [runner.md](runner.md).

Source-specific `release_prerequisite` metadata is frozen in the problem, case
manifest and actor source inventory. The validator requires agreement, including
presence. For CATE held-out outcomes, `saved-policy-evaluation-commitment-v1`
requires the candidate rule, utility, comparators and evaluation procedure to be
saved and publicly identified in an earlier completed consultant turn. The
operator binds exact artifact quotes and hashes to that turn's snapshot using
`source_release_receipts`. A promised future plan does not qualify. The held-out
file hash is recorded after release; requiring it beforehand would be circular.
This checks timing and evidence anchors, not statistical adequacy. Ordinary
requested sources and coherent bundles retain their existing disclosure rules.

## Information Boundaries

Prepare separately accessible public, world, actor and reviewer materials. The actor packet is private to
the user simulator, not a file to attach to the consultant.

| Packet | Required content |
|---|---|
| Public | Natural initial request; initial files and dictionaries; audience information a real user would share; valid initial history only when the case calls for it |
| World (`world.json`) | Immutable study facts or documented unknowns, real-source provenance or synthetic generation process, and available evidence; separate from actor access and reviewer judgments |
| Actor | User goal and decision constraints; domain/statistical fluency; factual beliefs with certainty and source; facts the user can learn and how; accessible source inventory; disclosure/correction rules; unknown and declined-source replies; allowed action choices and stopping behavior |
| Reviewer | Answer key and independent reference outputs grounded in the world; acceptable alternative paths and claim boundaries; observable success/failure criteria; actor fidelity criteria; required coverage; fixture validation and limitations |

Declare a conditionally applicable reviewer criterion with `conditional: true`
and state its trigger in the criterion text. A scope label alone does not enable
`not_applicable`. Reviewers justify whether the trigger occurred. A triggered
criterion cannot be not applicable: mark it observed when evidence supports a
judgment, including a supported omission or counterexample; otherwise retain
unobserved. Do not relabel coverage to satisfy finalization.

The actor and consultant never receive the world dossier or reviewer key. Freeze
persona differences in initial knowledge, mistaken beliefs, learning conditions,
reasoning and cooperation, rather than fluency alone. Actor-accessible facts are
an explicit subset of the world and accessible source inventory; a true world
fact is not automatically something the user knows or can obtain.

For persona fixtures, `case.json` includes `world: "world.json"`, `world_id`,
`world_version` and `persona_id`. Match the dossier's world identity and the
actor's `persona_id`, and bind the private dossier in the fixture hashes.
The runner can still read older external frozen run packages; do not rewrite them.

Facts are not necessarily identifying assumptions. The user may know how a list
was assembled but cannot establish exchangeability just by agreeing to it.
Separate an inaccurate user belief from the underlying truth and freeze the
event by which the user can learn a correction. Do not secretly alter the world.

Matrix and RGGVY cases bind `reply_limits` of 50 whitespace-delimited spoken
words and two semantic items, including the initial message. The four standalone
planning cases retain 50 words and one small semantic item under their frozen
selection policy. Matrix pairs may freeze one seeded, case-specific `interaction_challenges` opportunity
with a visible trigger and recovery condition. The actor need not force an
untriggered challenge. A partial answer may omit the public checklist while its
exact remainder stays in the private `unanswered_questions` record. These
communication rules do not change source facts, release gates or authorization.

The author also supplies a private manifest containing:

- `suite_version`, `case_id`, `case_version`, communication `edition`, author
  and, when relevant, `base_case_id` plus the exact adaptation delta;
- generator identity and seed, and exact hashes of all packets, datasets,
  dictionaries, staged documents and independent reference outputs;
- required shared tools/packages, access conditions, source-release mapping,
  completion conditions, required observations and prospectively set limits.

For an end-to-end report case, set `completion_contract: "full_report"` in
`case.json`. Absence or `"focused"` retains the older case-specific endpoint.
The full-report public request, actor goal/action/stopping rules and reviewer
criteria must agree that a saved consultant report is required. The four
standalone planning cases explicitly use `focused`: a useful collection and
conditional analysis plan requires no report or numerical effect. Freeze the
audience and necessary content, allowing equivalent structure and scientifically
justified claims. A complete bounded descriptive report can satisfy the goal
when causal identification is unsupported; a recap alone cannot.

Full-report completion requires captured evidence of a completed, verified
report run and its actual saved output. The reviewer separately checks report
substance, source/result consistency and applicable readback/render validation.
Keep the consultant report separate from the final testing assessment. Older
external packages retain their recorded endpoint; do not change them in place.

For `consultation-loop-v1`, behavioral validity is separate from the scientific
world and report endpoint. Preserve actual proposal, later choice, protected
start, findings discussion and report selection chronology. An initial desire
for a report cannot authorize a later action automatically. An extension has
its own bounded choice and returns to discussion. Scope revisions, questions,
pause/resume and reopening preserve their user meaning when they occur; none is
a mandatory quota in ordinary cases. The named coordinator 1.1.0 stress edition
requires the participation defined in its [case guide](rggvy-continuity.md).
A faithful user stop without a report leaves a
full-report objective incomplete, without automatically being an actor defect.

Keep the manifest and descriptive case IDs away from the consultant. Use neutral
filenames, working directories and session labels, not names such as
`hidden-post-treatment-trap`. Record originals privately. Initial consultant
loading is permitted; injecting expected findings or evaluator instructions is not.

## Fact and Reply Rules

Each actor fact needs a stable `fact_id`, a factual `statement`, `certainty`,
`source`, `available_when` and any `disclosure_condition`. Source references can
be user recollection, a supplied record or a declared contact, with uncertainty
preserved. Unknown/unobtainable information needs an explicit disposition.

Each response rule identifies its semantic condition, fact/source IDs it may
reveal, any constraints on the reply, and the resulting availability change.
Use events such as a request about the recorded event, not exact words or a
particular assistant turn. Combined questions may satisfy several conditions
at once. Repeated questions do not unlock progressively better facts by default.

Source rules specify the immutable file version, what request makes it eligible,
how it becomes available and any genuine prerequisite. Eligibility is not an
instruction to send every eligible source at once. The persona's disclosure
policy supplies the current topic's record or necessary bundle, acknowledges
remaining requests and follows up as those topics arise. A broad request can
establish those requests without a filename password. Keep short necessary
answers and requested files intact; no invented delay or access barrier is
allowed. Record receipt separately from inspection. Preserve pending requests
in the actor's existing disclosure history, not a second editable memory file.

Action rules allow choosing among consultant options without knowing the scoring
key: for example prefer work on existing records, decline new staff contact,
or authorize a specified preparation once its meaning is understood. A bare
unknown is not blanket authorization. Freeze how learning, corrections and
decisions may change with observable evidence. Preserve supported changes across
turns using the [actor update record](user-simulator.md), without changing the
world or automatically treating consultant assertions as facts. Bounded pressure
needs finite semantic conditions and an attainable honest report endpoint; it
must not force endless resistance or a predetermined estimator.

Freeze reusable interaction behavior in the selected persona. `standard`
includes early investigation, method discussion and choice, two finite
opportunities to ask for distinct stronger claims, and report selection and
verification. `novice-adversarial` combines limited statistical fluency and
bounded pressure; `expert` combines domain and statistical expertise without
mandatory stronger-claim requests. The four reusable problems
supply study-specific context for those behaviors. Standalone cases retain their
own fixed actors and do not inherit these reusable persona requirements. A phase names its observable
trigger, allowed response and honest resolution. Do not encode reply numbers,
minimum exchanges, hidden method requirements or extra release gates for ordinary
cases. Coordinator 1.1.0 is the narrow versioned exception for ordered public
participation and a minimum of eight delivered replies, with a hard ceiling of
twelve. It adds no method requirement or source-release gate. Initially
unvolunteered study context becomes available on a relevant request without an
arbitrary waiting period. Preserve reply limits, disclosure policy and private
unanswered-request history. Record an untriggered pressure as a coverage limit;
do not manufacture resistance.

If a question reaches an unspecified fact, the actor says it does not know and
records a fixture gap privately. If that gap materially affects evaluation, mark
the case invalid for that claim. Fix the version and rerun all candidates being
compared; do not invent facts or repair one candidate's run in place.

## Randomization and Reproducibility

Use the four problems and three general personas in the
[catalog guide](problem-persona-matrix.md) for 12 matrix pairs. Five standalone
cases give 17 full-catalog configurations. RGGVY uses only its Research
Coordinator; the four planning cases also have fixed actors. The selected scope
determines which to run. The same reusable problem's world,
scientific sources and criteria remain invariant across personas. Initial
understanding and natural disclosure differ. Generate no new study world during
a conversation or additional crossed factors without review. The old fixed
case catalog is removed; prior versions remain in Git and frozen run packages.
The previous four personas are archived outside the active catalog. They remain
valid within their original frozen runs and must not be rewritten there.

The RGGVY continuity variant preserves the original source-bound `reviewer.json`
and selects a combined `continuity-reviewer.json` through `case.json`'s `reviewer`
field. Follow that field when building reviewer input. Its private variant resource
and hash are retained in the composition; actor input receives only its selected
facts and behavior, never this case guide, private criteria or descriptive
duration target. Coordinator 1.1.0 actor-safe participation includes its required
events and bounds; frozen 1.0.0 attempts retain their original packet.

Matrix and RGGVY manifests add `problem_id`, `problem_version`, `persona_version` and
`target_turns`. Private `problem.json`, `persona.json` and `composition.json` are
hash-bound alongside ordinary files. The target is operator/reviewer metadata;
it does not appear in actor packets, govern release or change report completion.
Operational caps remain a separate frozen configuration.
New coordinator 1.1.0 manifests additionally declare
`minimum_consultant_replies: 8` and reuse `run_limits.consultant_turns: 12`.
Its actual configuration must agree at 12, without an extra opt-in flag. A
delivered-count check is mechanical; public event occurrence, consultant handling
and report substance require independent review. Use existing actor updates,
coverage, findings and outcome fields, not a new mutable event schema. Required
stress completion cannot retire after an early report; omitted or unproven
events leave outcome incomplete.

Useful axes include operational definitions, linkage/missingness patterns,
source availability, user knowledge, statistical fluency and wording. A changed
assignment mechanism is a changed scientific edition: regenerate coherent data
and documentation and review its identifying argument. Do not rewrite documented
real-study facts. Label hypothetical adaptations explicitly in fixture records.

Preserve generated bytes and actual replies as well as seeds. A seed does not
guarantee identical language-model behavior. Paired candidates receive the same
world and semantic response policy, not a forced identical transcript. Alternate
candidate order and keep model/configuration/tool conditions matched when the
comparison concerns the skill alone. Cross-system comparisons are separate and
must identify the host/configuration differences.

## Validation Before a Scored Run

Check that public files agree with the world, actor knowledge is attainable, each
planned source can be supplied, and legitimate unknowns have useful dispositions.
Review semantic-equivalence examples and a no-question response before freezing.
Do not require discovery of inaccessible truth or a single preferred route.

For preparation, freeze row IDs, inclusion/exclusion reasons, expected joins and
timing boundaries using an independent calculation. For estimation, define the
target, valid reference calculations and tolerances before consultant output is
seen. Synthetic causal truth is not the same as the realized estimator: do not
fail a sound estimate because it differs from the generating effect, or require
every single confidence interval to contain it. Coverage claims require their
own repeated-simulation design. Real observational data do not supply a known
causal truth merely because a reference analysis exists.
For the RGGVY case, independently check extract dimensions, sample construction,
source handling and arithmetic. Score the discovery and use of consequential
information, plus defensible alternatives, rather than proximity to a published
coefficient. See the [case guide](rggvy-electrification.md) for the study-specific
evidence boundaries.

Author-created examples and protocol rehearsals are not live observations. A
reviewed blueprint becomes a runnable case only after actual materials, hashes,
world/actor/reviewer packets, oracle checks and run limits have been frozen.
