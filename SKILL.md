---
name: interactive-test
description: Define, run and evaluate adaptive multi-turn tests of causal-consultant across supported agent hosts and model providers. Use for end-to-end investigation and saved reporting, or focused tests of elicitation, preparation, useful stopping and continuity.
metadata:
  version: "8.3.7"
---

# Adaptive Causal Consultation Testing

Test whether the consultant helps users with different knowledge, reasoning and
cooperation achieve a useful, scientifically defensible outcome. Do not supply
a sequence of expert analysis
instructions and call compliance proactive consulting.

The active problems and personas are listed in the
[problem/persona guide](references/problem-persona-matrix.md). Select the requested pair,
using `standard` when no persona is specified. The other active profiles are
`novice-adversarial` and `expert`. The RGGVY-only
[`rggvy-research-coordinator`](references/rggvy-continuity.md) adds a continuity
case. Explicit full-matrix coverage means the 16 valid pairs, not a Cartesian
product with this restricted persona.
Fixture validation, actor rehearsal and live qualification are separate stages.
Use the [runner guide](references/runner.md) for startup, adaptive steps and review.
Local subprocess tests do not establish compatibility with a live agent host.
Host smoke and live qualification of selected compositions remain pending.

## Compatibility

Tester **8.3.7** source supports `causal-consultant` **8.0.0, 8.0.1, 8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6 and 8.0.7**, pinned
to each attempt's candidate inventory and presentation policy, and retains the
supported v7 profiles. Operators and reviewers use the private
[observation profiles](references/observation-profiles.md)
for version-specific records, presentation and evidence rules. Unlisted versions
need an explicitly checked profile. Focused admission, observation and continuity
checks accompany this release; they do not establish live host qualification.

The case suite remains **8.2.0**; scientific problem and general persona versions are unchanged.
Tester 8.3.7 retains the RGGVY coordinator persona/variant 1.1.0,
automatically composed with its bounded 8 to 12 participation contract. It is
not yet live-qualified; frozen 1.0.0 attempts retain their old contract.
Frozen attempts retain their own versions, source identities, loading choices
and observation contracts. Tester and consultant releases are independent.
Pre-v7 controllers and old persona catalogs remain historical, outside the
active catalog. Use the [runner guide](references/runner.md) for loading and evidence.

## Responsibilities and Reading

The operator coordinates the test, a user actor supplies simulated user messages,
and a selected agent host runs the consultant. Keep these roles separate by
information, not a swarm of new agents on every turn. The current executable
runner supports Claude Code directly and Kimi and Pi through transport shims;
other hosts need their own verified adapter:

| Role | Reads | Produces |
|---|---|---|
| Fixture author | [Case contract](references/case-contract.md), selected [problem and persona](references/problem-persona-matrix.md), [evaluation rules](references/evaluation.md) | Frozen public materials, private world dossier, actor packet and reviewer packet |
| User actor | [Reply policy](references/user-simulator.md), actor packet, visible conversation and legitimately received materials | Persona-appropriate reply and private disclosure/update record |
| Run operator | [Runner guide](references/runner.md), [Agent-host contract](references/host-contract.md), frozen run configuration | Exact-session transport and captured evidence |
| Independent final reviewer | [Evaluation rules](references/evaluation.md), [observation profiles](references/observation-profiles.md), reviewer packet and actual evidence | Evidence-backed outcome, findings and coverage limits |

Read only the references for the current role. Start the actor with its own
protocol, setting, persona, public conversation, permitted materials and its own
disclosure/update history. Do not supply this entrypoint, operator/reviewer
references, candidate skill or guides, internal state/tool reasoning, observer
results, private `world.json` or answer criteria. If the same model authored the
fixture, use a separate actor context containing only that allowed input. The
final reviewer uses a separate context, not the actor's self-assessment.
These can be separate phases; additional live-agent services are not required.

For adapter development or deployment readiness, use the current
[runner guide](references/runner.md) and [host contract](references/host-contract.md).
Do not install packages, change global settings,
replace an installed consultant or launch a campaign merely by loading this skill.

## Consultation Loop

Compose the selected problem and persona with `scripts/compose_case.py`; pass
its output as the runner's `--case`. Each problem specifies its required saved
report in the case materials. Match causal claims to the available evidence.
A recap or testing assessment is a different
deliverable. Use `standard` if the persona is omitted; resolve any unclear
campaign scope before dispatch.

The consultant repeatedly presents understanding and directions, the user
steers, and bounded work or a direct answer returns to discussion. Initial report
desire is not standing permission. Choose a concrete analysis scope after it is
presented, then choose useful extensions or the offered report after findings
discussion. Each extension returns to the user; it does not also authorize a
report. The actor may naturally ask early for a report and should respond to the
consultant's explanation according to its persona, without policing internal
records. The reviewer checks whether the consultant handled the shortcut.
A report can be revised or reopened. User pause/end is legitimate; without the
requested report the full-report objective remains incomplete. Do not dispatch
background work or repeat prompts while waiting for user steering.

Ordinary problem target lengths are private descriptive metadata, never
actor instructions or completion criteria. Persona-dependent discussion and
disclosure may take fewer or more replies. Do not accelerate, pad or withhold
information to meet a target. Keep operational limits separate and prospective.
The named [coordinator 1.1.0 stress case](references/rggvy-continuity.md) is a
narrow exception: its actor packet requires ordered participation and at least
eight delivered replies, with actual configuration cap 12. An early report does
not waive participation; frozen 1.0.0 and the 15 general pairs keep their rules.

The reusable persona governs the interaction. `standard` represents a typical
user who initially leaves collection context unvolunteered, follows model-choice
discussion and may ask twice about distinct stronger claims before accepting a
supported report. `novice-adversarial` combines limited statistical fluency with
finite pressure for a preferred conclusion. `expert` combines domain and
statistical expertise and actively proposes at least two distinct methodological
or alternative analysis ideas before selecting the final report. The proposals
must occur on nonconsecutive user turns, separated by at least one substantive
user reply without a new proposal. Ideas differ in analytical purpose, assumptions
or comparison; changing a method's name or tuning does not suffice. Specific
methods follow the study and visible discussion. The expert accepts reasoned
rejection or improvement without demanding implementation or stronger claims.
Case materials supply study context for these behaviors. Triggers come from actual
discussion, not reply numbers. Relevant requests receive their sources without
artificial delay. Preserve learning and an attainable honest endpoint. Ordinary
claim-pressure opportunities may retire unused; the expert's two required ideas
cannot retire merely because the consultant already discussed methods. An
explicit user or operator stop can end earlier with expert coverage incomplete.
Forgetting an idea or selecting the final report too early is an actor-fidelity
issue. These requirements do not set a fixed total turn count.

1. Freeze the scenario, material identities, actor rules, candidate, environment
   and whole-consultation limits. Verify that private materials are outside the
   consultant's permitted access, not merely in another working directory.
2. Start a fresh consultant project and conversation with only the public
   request and initial materials. Explicitly invoke the selected consultant
   skill in the agreed host invocation, without method or rubric hints.
3. Observe the actual user-facing reply. Select the items to address under the
   frozen persona's disclosure policy, distinguishing actual information requests
   from an answer that quotes the user's own question. Use
   currently known facts and the persona's reasoning and cooperation. Every
   spoken message has at most 50 words and two semantic items. A compound request
   may receive a partial or nearby answer without a public checklist; retain
   omitted parts privately for a focused follow-up. Apply a frozen interaction
   challenge only when the visible wording and persona make it plausible.
   A broad request does not trigger the whole dossier in one reply. Keep short
   answers and necessary bundles complete. When no question is
   asked, respond to the recommendation according to the user's goal and bounds.
4. Record the reply, disclosure/source IDs and any attachments privately; send
   only the natural-language message and released files. Resume the exact same
   consultant session. Never select the next message from a fixed turn number.
   Use `inspect --view actor` to retain the permitted actor input and bind its
   digest to the separate actor context. The operator records source-release
   receipts for held-out data; a promise to save a plan later cannot release it.
5. Continue until the frozen objective or its permitted useful stopping condition
   is reached, or a declared limit/failure ends the attempt. In a full-report case,
   continue from investigation and supported analysis through report delivery and
   any needed correction. Then independently review the conversation, committed
   evidence, code and report. A missing report leaves that objective incomplete.
   Run `inspect --view reviewer` before writing the assessment, address every
   resulting machine finding, and finalize against that exact evidence snapshot.
   Use `export` and `check-package` to retain all raw captures. An incomplete
   evidence package must be explicitly marked partial.

For ordinary cases, do not stop after a fixed number of rounds or a convenient first result. A round
is one consultant response to a dispatched user message; the actor's final stop
record is not another round. Internal agent/tool turns are a separate
limit. Use the [runner's prospective capacity](references/runner.md), without
turning its ceiling or a planning estimate into a required conversation length.
The bounded coordinator must stop dispatching at reply 12 without reply 13;
unfinished participation/reporting and earlier cancellation remain incomplete.

The actor cannot change the study world, released document bytes or source
inventory, or acquire inaccessible truth. Only a persona whose frozen packet
explicitly permits unreliable spoken claims may make them. It can learn
from the visible exchange and received sources, revise mistaken beliefs, and
make choices allowed by its packet. Preserve that learning on later turns.
Equivalent requests establish the same source eligibility without secret
passwords. Disclosure follows the issue being discussed and persona understanding,
with unfinished requests and learning retained in the actor's private history.
See the reply policy for progressive disclosure, bounded pressure and corrections.

Review consultant mechanics privately under the frozen
[observation profile](references/observation-profiles.md). Distinguish user
questions from information requests and assess whether their answers were needed
before work or depended on its results. Preserve actual wording, qualifications,
user steering and evidence gaps. Do not teach these review rules to the actor,
require artificial record growth or impose a predetermined method order.

## What Counts as Success

Judge the consequential evidence chain, correct use of the information, scientific and
computational validity, understandable advice and proportionate user effort.
Credit facts only when actually disclosed or established from inspected sources.
Acceptance of an intermediate descriptive result does not itself close the
original causal inquiry; follow the actor's frozen scope and stopping choices.
Do not reward question count, a preferred estimator or refusal alone. A fully
specified attainable analysis must be tested alongside cases needing questions
or weaker claims. Use independent row/numerical checks where the case requires
them; a valid manifest is not proof of a valid analysis.

Evaluate actor fidelity separately from consultant quality. Keep outcome,
findings, test validity, coverage and resources separate. Missing
evidence is not a pass; a cap-limited run is not a successful useful stop. Save
failed attempts as well as successes. Report current cost descriptively under
prospectively frozen limits; do not retrospectively relabel earlier cap failures.
For full-report cases, the adapter checks retained evidence of a completed,
verified report artifact before accepting a successful outcome. The independent
reviewer still assesses whether its content answers the actual question and
preserves results, uncertainty, limitations and source evidence.
For the loop profile, a retained early start or report creation is a protocol
failure even if later approved. `consultation_loop_check` records structural
chronology separately from artifact completion and scientific judgment. Read
its actual user text and proposal evidence; a candidate approval record, actor
update or keyword match cannot certify the user's meaning.
Selected problem/persona runs diagnose observed behavior; they do not establish
population reliability or untested combination coverage.
