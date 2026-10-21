# Interactive Test

Release identity is specified in [SKILL.md](SKILL.md); private consultant mechanics
are in [observation profiles](references/observation-profiles.md).
The current testing release identity is **8.4.7**; this source supports consultant
**8.0.0, 8.0.1, 8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6, 8.0.7, 8.0.8, 8.0.9, 8.0.10, 8.0.11, 8.0.12, 8.0.13, 8.0.14 and 8.0.15**.
New attempts require an explicit loading choice; native Claude uses the staged
entry binding. CATE is problem version 1.3.1; the other synthetic problems remain 1.3.0. The RGGVY scientific
problem remains 1.2.0 under suite 8.2.0; its fixed coordinator case remains 1.1.0.
The four prospective cases retain suite `prospective-study-design-1.1.0`.
Surgery is case version 1.1.4; the other three are 1.1.3. All four retain
world version 1.1.0. Scientific facts are unchanged; CATE now states the existing
file-reference requirement for held-out data release. Historical attempts retain
their recorded versions and loading contracts.
The [21 October source implementation](../development-support/common-issues-implementation-2026-10-21/tester-implementation.md)
clarifies selecting one planning question before composing its answer, retaining
unanswered requests, reviewing conditional advice and checking actual actor behavior.
These clarifications were introduced in tester 8.4.6. Tester 8.4.7 also
credits delivered planning content separately from offers, preserving conditional
advice and useful stopping under the selected case contract.
The v8 profile observes the canonical journal and generated project/brief,
source-linked handling, work and next-turn actual reply records. V11 labels remain;
8.0.0 retains its 50/100/200-word allowances, while 8.0.1, 8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6, 8.0.7, 8.0.8, 8.0.9, 8.0.10, 8.0.11, 8.0.12, 8.0.13, 8.0.14 and 8.0.15 limit every next-step
option to 50 words and retain the conditional 200-word requested-answer allowance.
The frozen presentation policy governs both per-turn and final observations.
Native capture is optional, and a saved draft is not proof of actual
communication. Historical profiles retain their
contracts without changing case identities. Focused admission, observation and
continuity checks accompany this release. No full test suite or
live host qualification was run.

A simulated user interacts with a consultant on a selected agent host and model
provider. The tester captures the actual conversation, released evidence,
analysis and saved reporting for independent review. The executable runner
currently supports Claude Code directly and Kimi and Pi through transport
shims. Each host and model configuration needs its own smoke and isolation check.

The tester independently checks actual replies, saved captures and intact
reply recovery. It separates missing evidence from mismatches, permits an
undetermined failure cause, and flags source appearances without a recorded
release. Standard users disclose progressively and discuss useful model choices;
experts actively propose distinct methodological alternatives. V8 records and
retained v7 delivery/recovery records use their respective observation profiles.
These changes have not been live-qualified.

The actor receives only its own protocol, setting/persona packet, public
conversation, permitted materials and its own disclosures/updates. Candidate
skills, consultant state, observer results and reviewer rules stay outside that
input. The actor responds as a user rather than checking consultant mechanics.
Fresh processes and disabled skills do not themselves prove access isolation.

The catalog contains **four reusable problems and three general personas**,
giving **12 matrix pairs**, plus **five standalone cases**, for **17 active
configurations**. RGGVY now uses only its fixed
[Research Coordinator](references/rggvy-continuity.md). The four prospective
planning cases also have fixed actors. Standalone cases are not crossed with
the general personas. Historical frozen runs, including other RGGVY personas,
retain their original contracts. The [catalog guide](references/problem-persona-matrix.md)
lists selection commands; the [standalone guide](standalone/README.md) describes
the fixed cases and their different endpoints.

| Problem | Target replies |
|---|---:|
| `study-design` | 5 |
| `observational-did` | 10 |
| `cate-policy` | 15 |
| `data-quality-edge` | 8 |

These four problems remain synthetic. Standalone `rggvy-electrification` uses a
real Chhattisgarh extract from the RGGVY replication data to test proactive
investigation, defensible analysis and saved reporting. The paper is a source
of study evidence, not known causal ground truth. See the
[RGGVY case guide](references/rggvy-electrification.md). The other standalone
cases are `masks-planning`, `forest-planning`, `medication-planning` and
`surgery-planning`. They ask for feasible future data collection and analysis
plans, with no required report or numerical result. Each expects about 8 to 10
replies, descriptively, with a cap of 12 and no minimum.

Matrix persona selectors are `standard` (the default), `novice-adversarial` and `expert`.
The standard persona represents a typical user: initially unvolunteered study
context, follow-up questions about model choice, and two finite opportunities
to ask whether stronger causal or practical conclusions are justified. The
novice-adversarial persona combines limited statistical fluency with bounded
pressure for a preferred conclusion. The expert combines domain and statistical
expertise and actively proposes at least two distinct methodological or alternative
analysis ideas before selecting the final report. The proposals occur on
nonconsecutive user turns, with a substantive reply without a new proposal in
between. The expert accepts reasoned rejection or improvement of either idea;
implementation and stronger causal wording are not required. The previous four profiles
are archived outside the active catalog; historical frozen runs retain them.
Each has an explicit disclosure policy. Replies address the current issue with
its supporting record or connected bundle. A broad request does not trigger all
facts and files at once. Unanswered requests, prior disclosures, learning and
choices remain available after an interruption. Apply the frozen persona's
disclosure and correction rules. Matrix and RGGVY messages are limited to 50
words and two semantic items. The four planning cases retain the 50-word limit
and permit only one small item, following their frozen selection policy.
A reply may leave part of a compound request unspoken
while retaining it privately for a later focused follow-up. One seeded,
case-specific communication challenge is frozen per general-persona composition and used only
when the visible conversation warrants it. Users do not invent retrieval delays
or source-access barriers.
Scientific truth and legitimate source access remain the same across personas.

Ordinary target lengths are descriptive and stay out of actor instructions. They are
neither deadlines nor minimums. Information and report completion follow the
conversation, without rushing or adding exchanges to meet a target.
The selected persona governs investigation, model discussion, claim pressure and
report completion in matrix pairs.
For a standard user this includes two finite stronger-claim opportunities before
report selection and verification. Relevant source information is supplied when
requested without a fixed-turn delay. Expert ideas must differ in analytical
purpose, assumptions or comparison, and cannot be retired merely because the
consultant discussed methods first. No ordinary profile adds exchanges to meet a total
turn target. An explicit stop before both ideas leaves expert coverage incomplete.
The [coordinator 1.1.0 contract](references/rggvy-continuity.md) separately
requires substantive participation and minimum eight delivered replies, with
actual configuration cap 12. An early report cannot waive participation. Stop
after reply 12 without dispatch 13 and mark unfinished work incomplete; numeric
bounds do not certify event occurrence or consultant quality.

```sh
python scripts/compose_case.py --list
python scripts/compose_case.py --problem cate-policy --persona standard --output /private/cases/run001
python scripts/compose_case.py --standalone rggvy-electrification --output /private/cases/run002
python scripts/compose_case.py --standalone masks-planning --output /private/cases/run003
```

Pass the generated directory as the runner's `--case`. Composition freezes the
selected definitions and does not launch a consultation. See the
[catalog and programmer guide](references/problem-persona-matrix.md).

The consultation keeps returning findings and choices to the user. An initial
report request expresses a goal; concrete analysis and report choices follow
actual proposals and findings. Extensions return to discussion. The passive
observer preserves early-work and early-report breaches even if later approved.
Behavioral compliance, scientific quality and artifact completion are assessed
separately. Natural-language consent and uncaptured host activity still need
independent review.

Start with [SKILL.md](SKILL.md), the [runner guide](references/runner.md) and the
[agent-host contract](references/host-contract.md). The runner supports
preflight, start, step, inspect, finish, export and package checking, including source isolation, snapshot
identity and session continuity. Use the explicit
[observation profiles](references/observation-profiles.md); unlisted candidates
need a checked compatibility update. V8 uses a separate journal profile; do not
require cumulative v7 capabilities from it. The historical v7 profiles require
`consultation-loop-v1`, `durable-exchanges-v1`,
`captured-delivery-v1`, `proposal-preflight-v1`, `intact-reply-recovery-v1` and
`source-attributed-memory-v1`, plus `reply-reconciliation-v1`,
`compact-proposals-v1` and renderer `lead-markdown-v5` for 7.0.11 through 7.3.1.
The 7.0.12 profile additionally requires `concise-authoring-v1`. Its saved
records remain canonical; authoring convenience does not change the observer's
permission, source-release or public-evidence checks. The 7.0.13 profile
additionally requires `conversational-responses-v1` and renderer
`lead-markdown-v6`; the observer treats v6 as a compact renderer under the same
public-terms, linked-scope-export and exact-execution-binding checks.
Compact offers retain public material terms and a linked full scope export;
the observer checks that artifact at offer time and exact execution binding.
The 7.2.0 profile retains every 7.0.13 requirement and additionally requires
`deferred-release-v1`: one unreleased held-out analysis input may be named in
an offered scope without its hash, absent at offer time and hash-bound into
the frozen plan at run start; the observer keeps the existing source-release
and public-evidence checks for it. The 7.3.0 and 7.3.1 profiles retain these requirements.
Older profiles retain their own presentation contracts.
The 7.4.0/7.4.1 profiles require assisted authoring and Claude transcript capture;
7.5.0 also requires operational summaries, report deliverables and source-bound
report presentation adjustments. The 7.5.1 and 7.5.2 profiles retain these checks
and require `lead-markdown-v7` and `lead-markdown-v8`, respectively.
Both renderers use the compact scope contract. V8 adds populated labeled sections
and flat `[1]`, `[2]` items restarting within each section. Those display numbers
do not replace saved question/option IDs or establish permission. Review the actual
reply and later user meaning in context, including which section a number refers to.

The 7.5.3 profile additionally requires `four-section-responses-v1`,
`message-bound-delivery-v2`, `pending-intake-v1` and `lead-markdown-v9`.
Its `public_presentation_check` observes the actual reply independently of saved
body hashes: the four optional sections, unnumbered work summary, flat items,
whole visible-item lengths and correspondence with typed answers, explanations,
findings, information requests and options. Overlength answers need review against
the actual user request; the answer heading grants no automatic exception.
The chronology result remains separate. Exact text matching any earlier reply
does not prove native message identity, current applicability, consent or science.
The 7.5.4 profile additionally requires `visible-scope-answers-v1` and v10. A
requested answer may show a same-exchange option's complete saved scope once;
the short option points to that visible answer. Review the actual source request,
all displayed terms and the later selection. Existing historical exchanges retain
their own renderer, while newly authored legacy exchanges and unavailable history
cannot silently escape current presentation observation.

The 7.5.5 profile requires `section-item-labels-v1` and v11. It observes `[A1]`
answer-section items, `[Q1]` questions and `[N1]` next steps. Complete items,
including the unnumbered summary, normally stay within 50 words. Explicitly
requested answers may use up to 200 words; a protected option may use up to 100
only when essential selection terms need the extra space. Exceptions require
semantic review; the section or option type alone does not establish them.

Local validation must cover all 12 matrix pairs and five standalone cases, scientific references, source
boundaries, runner behavior and consultation-loop chronology. See the
[historical implementation and validation record](references/implementation-plan.md)
for earlier results and coverage limits. Local subprocess tests and actor rehearsals
do not establish live performance for a selected host and model or typical
consultation length.
A missing report or resource-limited attempt is not a completed report test.

Both skills are separate Git repositories under the outer workspace. Each uses
`main` for the current release, with one backup branch for each available earlier
major version. Earlier local archives are separate from this shipped catalog. Loading this skill does not
install software, replace an installed consultant or start a live campaign.
