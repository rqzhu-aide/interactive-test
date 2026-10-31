# Interactive Test

![Version 8.5.6](https://img.shields.io/badge/version-8.5.6-blue)

Anonymous review copy of version **8.5.6**.

A companion skill for testing Causal Consultant
through adaptive, multi-turn conversations. A simulated user discloses study
information gradually and responds to the consultant's questions and choices.
A coordinator runs the exchange and records observable issues, uncertainty and
supporting evidence so another programmer can investigate the problems. The
simulated user and consultant each run as a separate agent.

Supports consultant **8.0.0 through 8.0.17 and 8.1.0 through 8.1.4** and
selected historical v7 releases. See `references/observation-profiles.md`
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
catalog guide, `references/problem-persona-matrix.md`.

### Standalone cases

**`rggvy-electrification`:** Burlig and Preonas (2024),
[Out of the Darkness and into the Light? Development Effects of Rural Electrification](https://doi.org/10.1086/730204).
*Journal of Political Economy*, 132(9), 2937-2971. Includes actual Chhattisgarh
village and household data in `standalone/rggvy-electrification/problem/public/data.zip`
from the [replication archive](https://doi.org/10.7910/DVN/APWICK), for a
household-welfare briefing with a fixed Research Coordinator. It requires a
saved report and continuity participation as described in `references/rggvy-continuity.md`.

The four planning cases are fictional prospective adaptations of published studies:

- **`masks-planning`:** Mitze et al. (2020),
  [Face masks considerably reduce COVID-19 cases in Germany](https://doi.org/10.1073/pnas.2015954117).
  *PNAS*, 117(51), 32293-32301. Adapted from German mask mandates into a planned
  voluntary mask campaign and winter respiratory-illness study in France.
- **`forest-planning`:** Ferraro and Simorangkir (2020),
  [Conditional cash transfers to alleviate poverty also reduced deforestation in Indonesia](https://doi.org/10.1126/sciadv.aaz1298).
  *Science Advances*, 6(24), eaaz1298. Adapted into planned food and school-transport
  assistance and forest-clearing research in Peru.
- **`medication-planning`:** Wang et al. (2024),
  [Association of semaglutide with risk of suicidal ideation in a real-world cohort](https://doi.org/10.1038/s41591-023-02672-2).
  *Nature Medicine*, 30(1), 168-176. Adapted into a planned comparison of
  dapagliflozin versus empagliflozin and subsequent depression in England,
  including a conditional sample-size request with fictional planning assumptions.
- **`surgery-planning`:** Wallis et al. (2017),
  [Comparison of postoperative outcomes among patients treated by male and female surgeons: a population based matched cohort study](https://doi.org/10.1136/bmj.j4366).
  *BMJ*, 359, j4366. Adapted from Canadian retrospective records into prospective
  collection on surgeon self-described gender and surgical outcomes in South Africa.

The papers inspire the design challenges; their findings do not supply expected
answers. These four cases seek useful collection and conditional analysis plans,
with no required report or numerical effect estimate. Each planning reply offers
one small answer, choice or clarification, selected for its usefulness to the
researcher's goal. Actors may return to relevant earlier questions, retain
unanswered requests, and preserve uncertainty about unknown study facts. All five
standalone cases have fixed user roles and do **not** accept `--persona`; see the
standalone guide, `standalone/README.md`.

## Setup and running

Requires shared **Python 3.10+**, **Node.js 18.18+**, a compatible consultant folder,
and a configured agent CLI: Claude Code, or Kimi/Pi through the supplied adapter.
See the configuration and startup section of `references/runner.md` for configuration
and permissions. Keep tester materials outside the consultant's permitted access
under the private information boundary in `references/host-contract.md`.

From the tester directory, list cases or compose one into a fresh private directory:

```sh
python scripts/compose_case.py --list
python scripts/compose_case.py --problem observational-did --persona standard --output /private/cases/run001
python scripts/compose_case.py --standalone masks-planning --output /private/cases/run002
```

Paths are examples; choose one case. Composition does not call a model. Then:

1. Configure and prepare with
   `preflight` and `start`. Set the actual reply cap to **12** for standalone cases.
   `start` prepares the attempt without sending a user message.
2. Run the conversation using the frozen
   opening, then a separate simulated user and repeated `inspect`/`step` calls.
   Each reply responds to the actual conversation. If the next step requires
   obtaining information outside the conversation, pause after the consultant
   responds to that deferral and keep the attempt resumable.
3. Record issues and export
   the diagnostic snapshot, private `issues.md` and raw evidence with `export`
   and `check-package`. The tester supplies no final grade; a complete evidence
   package does not itself establish scientific validity.

## Further details

- `SKILL.md`: operator, actor and issue-recording responsibilities.
- `references/runner.md`: configuration, reply formats, execution, issue records and evidence packaging.
- `references/problem-persona-matrix.md`: selection, personas and completion rules.
- `references/observation-profiles.md`: current and historical compatibility.

Historical attempts retain their original cases, versions and rules. Local
fixture checks do not establish live host or model performance.
