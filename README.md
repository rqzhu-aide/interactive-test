# Interactive Test

A companion skill for testing [Causal Consultant](https://github.com/rqzhu-aide/causal-consultant)
through adaptive, multi-turn conversations. A simulated user discloses study
information gradually and responds to the consultant's questions and choices.
A separate reviewer checks the actual conversation, analysis and deliverables,
distinguishing consultant issues from actor or test-design issues.

Current version: **8.4.7**, supporting consultant **8.0.0 through 8.0.15** and
selected historical v7 releases. See [observation profiles](references/observation-profiles.md)
for exact compatibility; unlisted versions need a checked profile.

## Available cases

There are **17 configurations**: four reusable synthetic problems paired with
three personas, plus five standalone cases with fixed user roles.

### Reusable problems

| Selector | What the case tests |
|---|---|
| `study-design` | Plan a prospective tutoring evaluation under allocation, measurement and resource constraints. |
| `observational-did` | Analyze a tutoring-policy panel using difference-in-differences, distinguishing effects for adopting sites from effects across all sites. |
| `cate-policy` | Learn whom to offer tutoring using randomized data, costs and capacity, then evaluate the saved policy on separate data. |
| `data-quality-edge` | Audit duplicated and incomplete tutoring records and determine which descriptive or causal conclusions they support. |

Choose one of three personas for any reusable problem:

- `standard` (default): a typical user who shares context progressively and discusses analysis choices.
- `novice-adversarial`: a user with limited statistical fluency who presses for a preferred conclusion but can learn from explanations.
- `expert`: a knowledgeable user who proposes distinct analysis ideas and accepts justified rejection or refinement.

These **12 problem/persona pairs** require a saved report appropriate to the
study. The study-design case produces a prospective design report, without
inventing trial outcomes. Detailed disclosure and completion rules are in the
[catalog guide](references/problem-persona-matrix.md).

### Standalone cases

| Selector | Study |
|---|---|
| `rggvy-electrification` | Investigate real Chhattisgarh electrification data for a household-welfare briefing with a fixed Research Coordinator. |
| `masks-planning` | Plan data collection and analysis for a winter mask campaign in French cities. |
| `forest-planning` | Plan a study of rural assistance and forest clearing in Peru. |
| `medication-planning` | Plan a study comparing medication initiation and subsequent depression in England. |
| `surgery-planning` | Plan a study of surgical outcomes by surgeon gender in South Africa. |

RGGVY uses real replication data and requires a saved report plus its
[continuity participation](references/rggvy-continuity.md). Its source paper is
evidence, not known causal ground truth. The other four studies are fictional
prospective scenarios: they seek useful data-collection and conditional analysis
plans, with no required report or numerical effect estimate.

All five have fixed user roles and do **not** accept `--persona`. The four
planning actors answer one small question or subquestion at a time and retain
unanswered requests; they do not disclose their whole study book. See the
[standalone guide](standalone/README.md) for their contracts.

## Run an interactive test

Use a shared **Python 3.10+**, **Node.js 18.18+**, an installed and configured
supported agent CLI, and a compatible consultant folder. The runner uses Python's
standard library. It supports Claude Code directly and Kimi and Pi through a
transport adapter; analysis and report tools depend on the chosen study.

Run the commands below from this tester directory. Paths are illustrative:
replace them with fresh, nonoverlapping locations on your host. Keep the tester,
case books, actor/reviewer inputs and attempt records outside the consultant's
permitted filesystem. Separate directories alone do not establish isolation;
follow the [host contract](references/host-contract.md#private-information-boundary).

### 1. Choose and compose a case

```sh
python scripts/compose_case.py --list
python scripts/compose_case.py --problem observational-did --persona standard --output /private/cases/run001
```

For a standalone case, use this form instead:

```sh
python scripts/compose_case.py --standalone masks-planning --output /private/cases/run002
```

Composition freezes the selected case inputs; it does not call a model. The
remaining examples use `run001`. Substitute your chosen case directory.

### 2. Configure and prepare the run

Save a configuration outside the public work directory. This example uses
native Claude Code for an explicitly unblinded diagnostic run; replace the
executable paths with your shared installations:

```json
{
  "claude_command": ["/path/to/claude"],
  "candidate_loading": "claude_explicit",
  "node_command": ["/path/to/node"],
  "mode": "diagnostic",
  "max_agent_turns_per_call": 120,
  "call_timeout_seconds": 3600,
  "limits": {
    "consultant_turns": 40,
    "active_seconds": 14400,
    "elapsed_seconds": 43200
  }
}
```

For **every standalone case**, set `limits.consultant_turns` to **12**. RGGVY
requires 8 to 12 delivered replies and its specified participation. The four
planning cases expect about 8 to 10 replies descriptively, with no minimum.
Ordinary target lengths are not deadlines or success criteria.

The [configuration guide](references/runner.md#configuration-and-startup) covers
model selection, tool permissions, Kimi/Pi adapters and `verified_host` setup.
Diagnostic runs are marked invalid and cannot receive a passing rating. For a
valid blinded comparison, each host/model configuration needs its own loading,
session-resume and isolation checks; passing preflight alone does not establish them.

```sh
python scripts/session_driver.py preflight --case /private/cases/run001 --candidate /skills/causal-consultant --config /private/config.json
python scripts/session_driver.py start --case /private/cases/run001 --candidate /skills/causal-consultant --config /private/config.json --attempt /private/run001 --work /public/work001
```

`preflight` checks the inputs without a paid consultation. `start` stages the
candidate and public materials but sends no user message.

### 3. Conduct the conversation

Prepare the first reply file using the exact composed `public/initial-message.txt`,
empty disclosure lists and `stop: false`, following the
[reply format](references/runner.md#user-actor-loop). Then dispatch it:

```sh
python scripts/session_driver.py step --attempt /private/run001 --reply /private/inbox/initial.json
python scripts/session_driver.py inspect --attempt /private/run001 --view actor
```

Give only the returned actor bundle to a separate simulated-user context. It
produces the next short reply using the latest conversation and its retained
knowledge. Save that reply with the bundle's digest and actual actor context ID,
as described in the reply format, then send it:

```sh
python scripts/session_driver.py step --attempt /private/run001 --reply /private/inbox/reply.json
```

Repeat actor inspection and adaptive replies until the case's endpoint or a
declared stop. Each ordinary `step` sends one user message. To end the conversation,
submit an actor stop with `message: null`, `stop: true`, no attachments and the
current actor binding. This ends dispatch without another consultant reply;
review determines completion. A temporary pause needs no stop record.
A timeout or provider failure is an execution error; unfinished work at a resource
limit remains incomplete. Preserve the evidence rather than assuming success or
blindly resending an uncertain dispatch.

### 4. Review and save the results

A separate reviewer assesses both the consultant's work and the actor's
adherence to its case, using the latest evidence:

```sh
python scripts/session_driver.py inspect --attempt /private/run001 --view reviewer
```

Have the reviewer create `review.json` outside the attempt and work directories,
following the [assessment format](references/runner.md#independent-review).
It must cite the returned evidence and address the recorded findings. Then:

```sh
python scripts/session_driver.py finish --attempt /private/run001 --assessment /private/inbox/review.json
python scripts/session_driver.py export --attempt /private/run001 --output /packages/run001.zip
python scripts/session_driver.py check-package --package /packages/run001.zip
```

Create the export parent directory first. A complete evidence package is distinct
from a successful consultation. For an incomplete evidence package, use
`--allow-partial` on both export and checking and retain its incomplete status.

## Further details

- [Skill instructions](SKILL.md): operator, actor and reviewer responsibilities.
- [Runner guide](references/runner.md): configuration, reply formats, execution and evidence packaging.
- [Case catalog](references/problem-persona-matrix.md): selection, personas and completion rules.
- [Evaluation guide](references/evaluation.md): scientific review, attribution and incomplete outcomes.
- [Observation profiles](references/observation-profiles.md): current and historical compatibility.

Historical attempts retain their original cases, versions and rules. Local
fixture checks do not establish live host or model performance.
