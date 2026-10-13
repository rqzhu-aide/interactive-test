# RGGVY coordinator bounded continuity stress case

For fixture authors, operators and reviewers, not the user actor. This persona
is available only with `rggvy-electrification`; it is not a fourth general persona.
Use the ordinary [runner](runner.md) with a fresh composed case:

```sh
python scripts/compose_case.py --problem rggvy-electrification --persona rggvy-research-coordinator --output /private/cases/coordinator001
```

New compositions select coordinator persona and variant **1.1.0** automatically.
Tester **8.3.5** releases this case while retaining suite **8.2.0**, the 15
general problem/persona pairs and frozen coordinator **1.0.0** attempts unchanged.
The coordinator prepares a research briefing on household welfare in historical
Chhattisgarh. They understand logistics and basic summaries and need explanation
of identification and uncertainty. This edition requires eight ordered client
participation events and **8 to 12 delivered consultant replies**. It is a
controlled stress contract, not a descriptive duration target.

The [persona](../personas/rggvy-research-coordinator.json) contains only user
behavior. The [private variant](rggvy-continuity.json) supplies initial wording,
the client-priority fact, required participation and extra review criteria.
The composer copies only the actor portions into `actor.json`. The actor uses
the usual reply policy, public conversation, permitted materials and own history;
neither this guide nor the complete variant resource belongs in its input.

Each event needs a distinct public client message and its own consultant reply.
Event order is fixed; wording, scientific route and actual scope choices adapt to
the visible discussion. Events are not fixed dispatch numbers: genuine source
questions or selected work may need additional exchanges.

| Event | Required client contribution |
|---|---|
| 1 | Establish historical Chhattisgarh household welfare as the original target, supply data and request an eventual saved report. |
| 2 | Supply requested accessible records promptly and intact. Publicly state the existing `f-rggvy-access` limit: no additional survey, author contact or national-data acquisition is available in this consultation. If established earlier, confirm that limit rather than withholding it. |
| 3 | Select an actually offered useful bounded contribution, or accept a justified scientific limit. Explicitly defer the final welfare-framing decision for the briefing. |
| 4 | Ask what the actual finding or limit means for a briefing statement, without selecting further computation. |
| 5 | Revise the audience requirement to add a plain-language decision summary for district officials alongside the research audience. |
| 6 | Discuss the practical recommendation supported for those officials, including an honest limit. |
| 7 | Return to the deferred framing after at least two substantive intervening consultant replies, using a natural backward reference without resupplying all earlier facts. Apply the retained target, access limit and revised preference to the decision. |
| 8 | Select actual offered report contents, or assess an early report against the now-settled decisions. Request revision only for a real mismatch. |

If the scientific question is already answered, retain that answer and defer a
genuinely undecided briefing emphasis. No method, second computation, numerical
finding, error or late correction is mandatory. Questions do not authorize work.
An early report does not waive unfinished client participation. Do not delay
requested records, repeat settled questions or invent defects to fill exchanges.
Spoken replies retain 50 words and two items; use existing actor update fields,
not a new mutable event record. This case adds no seeded communication challenge.

The manifest declares `minimum_consultant_replies: 8` and
`run_limits.consultant_turns: 12`; the actual runner configuration must set
`limits.consultant_turns: 12`. Preflight checks agreement with the actor packet.
The minimum counts retained successful delivered public replies, not attempted
calls. Actor stops below eight are rejected before state changes. After reply 12 a
stop record adds no reply; never dispatch reply 13. Replies 9 to 12 allow genuine
unfinished sources, selected work, report delivery or correction. Unfinished
participation or reporting is `incomplete`; an explicit human cancellation or
provider failure can end earlier without completing the stress contract. General
personas retain their prospective default of 40.

The independent reviewer establishes all eight event occurrences from public
anchors and measures the actual deferral/return gap. Count at least two
substantive responses to events 4 through 6 strictly between event 3's deferral
and event 7's return; the response to deferral does not supply this gap.
Actor update assertions do not prove
occurrence. Compare relevant original and current consultant records privately
for preservation of facts, qualifications and decisions.

Numeric checks are mechanical. Public event occurrence and correct consultant
handling are separate questions: `coverage: observed` never means passed. An
absent or unproven required event makes stress outcome `incomplete`, even with a
complete report; explain the omission or uncertainty in existing coverage and
findings fields. If the event occurred and the consultant mishandled it, retain
the exercised coverage and consultant finding, which can make quality `fail`.
Unrelated missing scientific review evidence affects quality under the usual
rules, not an automatic numeric completion override. Report completion, bounded
participation, consultant quality and test validity remain separate. Same-session
continuity does not establish recovery after a pause or a fresh context.

Original data, source documents, scientific world, oracle and reviewer file stay
unchanged. The composed `continuity-reviewer.json` includes the original criteria
plus continuity criteria; `case.json` selects it. Always follow that manifest path.
The frozen variant resource and hashes retain the added design independently of
the base scientific problem. No report-production requirement, source prerequisite
or permission rule is relaxed by selecting this persona.

Source alignment is not executed verification. Composition, boundary and actor
checks must be reported separately from a prospective live attempt with actual
cap 12; live 8 to 12 qualification remains pending. Freeze host/model, loading,
permissions and isolation evidence before a run.
