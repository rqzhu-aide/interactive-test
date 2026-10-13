# Private consultant observation profiles

For operators, observer developers and independent reviewers only. Do not put
this reference, candidate instructions or observer results in an actor prompt
or bundle. The simulated user follows its own protocol, setting and persona,
using the public conversation and legitimately received materials.

Tester 8.3.7 source supports consultant 8.0.0, 8.0.1, 8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6 and 8.0.7. Freeze the actual
candidate inventory, capabilities, journal format and presentation policy for
each attempt. Focused admission, observation and continuity checks accompany
this release; live host qualification remains pending.
Historical attempts keep their frozen contracts;
do not reinterpret them using a newer record schema or renderer.

## Consultants 8.0.0, 8.0.1, 8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6 and 8.0.7

The primary journal format is `consultation-journal-v8`. Its top-level
capabilities include `canonical-memory-v8`, `content-authoring-v8`,
`six-section-brief-v8`, `exact-record-read-v8`, `agent-recorded-reply-v1`,
`actual-reply-reconciliation-v1` and `four-section-responses-v1`. V8 is a separate
profile, not a cumulative requirement to advertise every historical v7 capability.
The package also retains a legacy codec for existing v7 journals.

All eight supported releases activate v8 loop observation and the existing before/after
work-inventory receipt used by full-report completion. The capability response must
name the exact selected candidate version. This does not admit other 8.x releases.

`journal.jsonl` owns chronological entries and adopted entity definitions.
`project.yaml` is a generated current-state export, using JSON syntax, and
`case-brief.md` is a selected six-section continuation view. Use the full journal
entry and frozen run evidence for consequential details. A compact index or
brief is not the complete body of a review, interpretation, scope or reply.

Original input is retained as `user_message`. Whole-message handling may be a
`knowledge`, `decision` or `interpretation` entry linked to it. A clear decision
or sourced update needs no additional interpretation narrative. Work, reviews
and prepared replies cite their committed handling through `responds_to`.
Review mixed intentions, qualifications, partial answers and timing against the
original message. The presence of a handling link does not prove sound judgment.
On a resumed turn, a prepared closeout can cite only the current handling while
answer and work references retain their earlier sources. Compare frozen plans
and completion manifests with the original work start, not the later closeout.

Continuation is derived from explicit direction and owned records. Do not
require an authored checkpoint, a fixed window of recent intakes, a new entity
version for an unchanged definition or knowledge growth on every turn. A pure
knowledge no-op can commit no entry; original incoming messages, actual replies
and consequential decisions still retain their own evidence. Read live
obligations, question remainders and newer user steering even after focus changes.

`reply_prepared` is a draft. `reply_recorded` retains the actual prior reply,
normally at the next appropriate resume before interpreting a dependent choice.
Its `before_user` anchor and source identify the public reply being recorded.
Compare the ordered actual items, labels, qualifications and mappings with the
independently captured public conversation. Native host capture is optional;
assistant recording does not establish native identity or exact byte provenance.
A latest reply can legitimately await its next-turn record. A repaired account
of unchanged terms preserves existing acceptance; changed or omitted terms
cannot gain permission retrospectively. Preserve conflicting observations and
the supported current resolution without deleting historical evidence.

Association with a public turn does not establish that its recorded option was
offered. An accepted option absent from a structurally readable public reply is
a record contradiction. Missing public text or differences in wording or format
remain unobserved for semantic review, not automatic permission violations.

Scopes, decisions and run starts use entry identities. Read the scope's shared
`terms`, execution-only `execution`, actual public offer, later user choice and
run binding together. Do not demand v7 `scopes/<scope_id>/scope.json` exports or
v7 field names from a v8 journal. Reports remain selected, revisable artifacts.
Full-report cases still require their frozen report endpoint; a valid user pause
can leave that objective incomplete.

The report observer's `prior_discussion_refs` is a raw reference collection,
not proof that completed findings were delivered. Review the work version at
the public reply's time: a progress item can name a run before completion.
A completed-run review can support its linked findings; a distinct later review
needs its own coverage. Follow the actual review-to-run links and qualifications
without treating every review of the same run as interchangeable. A raw-ID
`report_discussion_unobserved` finding requires this evidence review, not an
automatic breach. Do not require another answer or a bookkeeping-only reply
when the retained public text already communicates the relevant findings.

## Public response review

V8 retains `lead-markdown-v11`. Its populated sections, in order, are
`[To answer your question]`, `[What has been done]`, `[Questions for you]` and
`[Next steps]`. Answers, explanations and a complementary findings item use
flat `[A1]`, `[A2]` labels; consultant questions use `[Q1]`, `[Q2]` and next
steps use `[N1]`, `[N2]`.
The optional work summary is one unnumbered paragraph about only the preceding
turn. Omit empty sections and redundant summaries. Labels identify local items
in one actual reply, not global records or permission.

Count the complete visible item, including its title, qualifications, expanded
scope terms and visible pointer text. Ordinary items and the optional summary
have a 50-word allowance. Explicitly requested answers or clarification may use
up to 200 words, subject to review of the actual request.

Consultant 8.0.0 retains the allowance of up to 100 words for essential selectable
scope terms when needed; review necessity before applying it. Consultants 8.0.1,
8.0.2, 8.0.3, 8.0.4, 8.0.5, 8.0.6 and 8.0.7 require every next-step option to stay within 50 words, including scope options.
The frozen profile's `public_presentation_option_max_words` selects this policy
for both per-turn and final observation. Historical profiles without that field
retain the earlier 100-word scope ceiling; journal format and renderer alone do
not select the 8.0.1/8.0.2/8.0.3/8.0.4/8.0.5/8.0.6/8.0.7 rule.

A requested answer may show complete same-reply scope terms once, with its option
pointing to that visible answer; the 8.0.1/8.0.2/8.0.3/8.0.4/8.0.5/8.0.6/8.0.7 option still stays within 50 words.
A heading or saved link alone proves neither disclosure nor consent. Internal
records and report artifacts retain their needed detail.

Preserve complete public text and report presentation observations separately
from scientific meaning, provenance, consent and chronology. Draft byte
comparison is informational for profiles using next-turn actual reply recording.
Public structure, omitted qualifications and user understanding still require
review. No renderer label, valid manifest or successful verification certifies
scientific validity.

Retain at most one substantive specialist review per consultant assistant turn,
whether performed locally or delegated. Direct explanation, synthesis,
clarification or justified stopping can use zero. A prerequisite answer precedes
dependent work; clearly authorized independent work need not wait for an
unrelated unresolved question. Distinguish acceptance, immediate direction,
execution and communication instead of demanding another ritual approval.

## Retained v7 profiles

Supported versions are 7.5.0 through 7.5.6, 7.4.1, 7.4.0, 7.3.1, 7.3.0, 7.2.0,
7.0.0 through 7.0.2, and 7.0.4 through 7.0.13. Unlisted versions need an explicitly
checked profile. Requirements accumulate only within these supported v7 versions.

| Added in | Required capability or renderer |
| --- | --- |
| 7.0.5 | `durable-exchanges-v1` |
| 7.0.7 | `consultation-loop-v1` |
| 7.0.8 | `captured-delivery-v1`, `proposal-preflight-v1` |
| 7.0.9 | `intact-reply-recovery-v1`, `source-attributed-memory-v1` |
| 7.0.11 | `reply-reconciliation-v1`, `compact-proposals-v1`, `lead-markdown-v5` |
| 7.0.12 | `concise-authoring-v1` |
| 7.0.13 | `conversational-responses-v1`, `lead-markdown-v6` |
| 7.2.0 | `deferred-release-v1` |
| 7.4.0 | `assisted-authoring-v1`, `claude-transcript-capture-v1` |
| 7.5.0 | `operational-summary-v1`, `report-deliverables-v1`, `report-presentation-adjustment-v1` |
| 7.5.1 | `lead-markdown-v7` |
| 7.5.2 | `lead-markdown-v8` |
| 7.5.3 | `four-section-responses-v1`, `lead-markdown-v9`, `message-bound-delivery-v2`, `pending-intake-v1` |
| 7.5.4 | `visible-scope-answers-v1`, `lead-markdown-v10` |
| 7.5.5 | `section-item-labels-v1`, `lead-markdown-v11` |
| 7.5.6 | `agent-recorded-reply-v1` |

Renderer v3/v4 keeps its historical headings. V5 may omit empty sections; v6
also permits omitted question echoes and redundant status. V7 uses flat
`Option 1:` paragraphs. Renderer v8 uses populated labeled sections and local
`[1]`, `[2]` items, including its historical numbered summary. V9 introduces the
four current sections with an unnumbered summary, v10 supports a visible scope
answer referenced by an option, and v11 distinguishes A/Q/N items. Do not confuse
renderer v8 with consultant version 8.0.0.

Historical compact offers retain public material terms, linked full scope
exports and exact execution bindings. Deferred input release retains its
pre-result prerequisite and freezes input hashes at start. For 7.5.0 onward,
inspect designated report primary/companions and source-bound presentation
adjustments. A local format request does not authorize changed science.

For 7.5.6, associate next-turn agent records with the independently retained
public conversation using the retained next-user source and stable intake event.
Review meanings, mappings and omissions without treating agent records as native
capture proof. A latest reply may await its next-turn record. Earlier prepared
replies and actual-message evidence keep their own historical contracts.
