# Five standalone cases

Each case has one fixed user role and is selected without a persona option.
These five cases sit alongside the four reusable problems crossed with three
general personas, giving 17 configurations in `references/problem-persona-matrix.md`
at the skill root.

| Selector | Study and fixed user | Endpoint |
|---|---|---|
| `rggvy-electrification` | Research Coordinator preparing a household-welfare briefing from real Chhattisgarh electrification data | Saved scientific report and bounded continuity participation. See `references/rggvy-electrification.md` and `references/rggvy-continuity.md` at the skill root. |
| `masks-planning` | Planner preparing a winter mask-campaign study in France | Useful prospective collection and conditional analysis plan. Private case book: `masks-planning/playbook.md`. |
| `forest-planning` | Planner preparing a rural-assistance and forest-clearing study in Peru | Same planning endpoint. Private case book: `forest-planning/playbook.md`. |
| `medication-planning` | Planner preparing a medication and depression study in England | Collection and conditional analysis plan plus numerical sample-size planning. Private case book: `medication-planning/playbook.md`. |
| `surgery-planning` | Planner preparing a study of surgical outcomes by surgeon gender in South Africa | Same planning endpoint. Private case book: `surgery-planning/playbook.md`. |

The four prospective settings and operations are fictional. The surgical case
uses voluntary gender self-description. None provides future outcomes or a
known causal effect. No saved report or observed treatment-effect estimate is
required. Medication also requests a conditional numerical recruitment plan,
with sensitivity and a comparison to the budget. An explicitly chosen narrower
feasibility endpoint can be a useful stop; missing numerical work remains
unobserved coverage rather than completed sizing. Generic refusal or reaching
capacity does not complete a case.

## Selecting and running

From the tester directory, using a shared Python installation:

```sh
python scripts/compose_case.py --standalone rggvy-electrification --output /private/cases/run001
python scripts/compose_case.py --standalone masks-planning --output /private/cases/run002
```

Use any of the five selectors. Pass the fresh output directory as the runner's
`--case`, following `references/runner.md` at the skill root. Composition
does not launch a consultation. `--persona` is not accepted with `--standalone`.
An older `--problem rggvy-electrification` command, optionally naming its exact
coordinator persona, remains an alias; general RGGVY personas cannot be newly composed.

RGGVY keeps its 1.1.0 coordinator and continuity variant under suite 8.2.0.
Its source folder contains `problem/`, `persona.json` and `continuity-variant.json`.
The other four folders are self-contained frozen cases under suite
`prospective-study-design-1.1.0`. Medication is case version 1.2.4 and world
version 1.2.0; masks and forest are case version 1.1.7, and surgery is case
version 1.1.8. Those three retain world version 1.1.0. The current policy
keeps precise unanswered remainders, permits grounded researcher choices, and
distinguishes temporary pauses from completed planning goals.
The earlier source patches clarified selecting one question before
composing its answer and retaining the precise unanswered remainder. They preserve
the earlier reply examples, useful stopping, disclosure, public timing and conditional
review corrections without changing study facts. Medication 1.2.0 adds four
provisional planning inputs and the numerical request. All four retain the fixed internal actor
identity `single-question-planner`; this is not a reusable persona selector.
Running the shipped cases needs no development-support files or source stories.

## Disclosure and duration

RGGVY retains at most 50 spoken words and two semantic items per message. It
requires eight ordered client participation events and 8 to 12 delivered
consultant replies, with the actual runner cap set to 12. An early report does
not waive participation. Its source-release rules remain unchanged.

The four prospective cases retain at most 50 spoken words and **one small
semantic item** per message. A consequential false-premise correction takes
priority. Otherwise the actor chooses one current or still-relevant earlier
request, choice or clarification useful to its practical goal, guided by known
constraints, preferences and the visible explanation. Reading order breaks ties
when those give no reason to prefer one item. Other requests remain privately
pending. Necessary qualifications stay with the answer; a label or fact card
does not justify answering several questions. The actor does not dump its book
or automatically empty pending questions after a recommendation. An external
fact-finding pause preserves the unfinished goal and needs no extra assent turn.

Their fixed facts, unknowns, preferences and detailed selection policy are in
each `actor.json`. There are no releasable attachments. Questions about known
record contents can receive a short spoken answer; an explicit file request
cannot create a file or permission. Their expected 8 to 10 delivered consultant
replies, nominally 9, are private descriptive metadata. They have no minimum,
disclosure quota or ordered event requirement. Set the actual runner ceiling to
12; unfinished planning at that ceiling is incomplete.

## Information boundaries and evidence

Only `public/initial-message.txt` starts a planning consultation. The actor
receives its own packet, shared reply policy, visible conversation and disclosure
history. The private world, reviewer criteria, playbook and provenance belong
only to authors or reviewers. Keep the complete source and frozen run packages
outside the consultant's permitted filesystem; directory names alone do not
establish isolation. Use neutral public work paths.

Scientific content, disclosure and completion contracts are unchanged by this
catalog reorganization. Historical frozen runs retain their own bytes and rules.
Structural validation and actor rehearsals remain distinct from live host or
consultant qualification.
