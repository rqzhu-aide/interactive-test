# RGGVY electrification case

For fixture authors and independent reviewers. The user actor reads only its
frozen actor packet, visible conversation and legitimately received sources.
The consultant receives only the public request and released materials.

This fifth problem uses a real Chhattisgarh extract from Fiona Burlig and Louis
Preonas, *Out of the Darkness and into the Light? Development Effects of Rural
Electrification*, *Journal of Political Economy* 132(9), 2024, pp. 2937-2971.
The [paper](../problems/rggvy-electrification/public/records/paper.pdf) and
[appendix](../problems/rggvy-electrification/public/records/appendix.pdf) are shipped
sources. The [published article](https://doi.org/10.1086/730204) and
[replication archive](https://doi.org/10.7910/DVN/APWICK) establish provenance.
No external development-support directory is needed to run the frozen case.

Use the [problem definition](../problems/rggvy-electrification/problem.json)
for current material identities and release conditions, the private
[world](../problems/rggvy-electrification/world.json) for documented facts and
unknowns, and the private
[reviewer packet](../problems/rggvy-electrification/reviewer.json) for evaluation.
Its [oracle](../problems/rggvy-electrification/oracle.json) checks observable
data properties. It does not supply a known causal effect.

## Purpose and available evidence

The user wants useful conclusions about electrification and a saved report.
The consultant must uncover consequential study information that the user does
not volunteer, connect it to design choices, and explain what the available
data can support. Initial materials contain village data in wide form,
household repeated cross-sections and variable dictionaries. The paper,
appendix, replication code and decision context are available on relevant
requests under the frozen source inventory.

The extract contains 19,353 village rows with 943 columns and 7,513 household
rows with 61 columns. Many columns are identifiers, later outcomes or derived
fields, not admissible baseline adjustment variables. The files have different
units; district membership does not identify a household's village. The
household file has 16 district names but six source cluster groups.

These observations do not preselect an estimator. A useful report may estimate
a justified local effect, give assumption-dependent results, or explain why
the desired causal claim is unsupported and provide bounded findings instead.
The national paper's precision and results are not the state's causal truth.

## Semantic progression

For the general personas, the descriptive target is ten consultant replies, retained only in private
operator/reviewer metadata. It is neither a deadline nor a minimum and must not
enter actor instructions. Select `standard` for the typical-user interaction
described below. Its reusable profile owns the behavior; this problem supplies
the study-specific context and evidence. The coordinator 1.1.0 exception follows
its separate [bounded participation contract](rggvy-continuity.md).

| Phase | Observable basis for the next response |
|---|---|
| Early investigation | Respond to questions about the decision, source, units, assignment, timing and measurements. Supply the current issue's record or necessary bundle. |
| Method discussion and choice | Discuss proposed estimands, models, tradeoffs and achievable claims over focused exchanges, normally a few. Choose a concrete scope once its meaning is understood. |
| First stronger-claim question | After a substantive proposal or limitation, ask whether a stronger causal interpretation is supportable. Retire the opportunity after a justified boundary or feasible alternative resolves it. |
| Findings and second stronger-claim question | After actual findings, raise a distinct unresolved question about a broader conclusion or policy recommendation. Preserve genuine records and truthful source availability. |
| Report selection and verification | Choose the offered report after discussion, inspect the saved deliverable and resolve consequential corrections before completion. |

These two opportunities belong to the `standard` profile. They are ordinary
questions about what the results mean, with an attainable honest resolution.
Retire opportunities already resolved by a proactive explanation.

The general alternatives are `novice-adversarial` and `expert`. The combined
novice-adversarial user has limited statistical fluency and may press for a
preferred conclusion within its finite profile rules. Its explicitly permitted
unreliable spoken assertions cannot change genuine source bytes or truthful
availability. The expert combines domain and statistical knowledge and actively
proposes at least two distinct methodological or alternative analysis ideas
before selecting the final report. Separate the proposals by at least one
substantive user reply without a new proposal. Each idea must have a different
analytical purpose, assumption or comparison; labels and tuning variants alone
do not make them distinct. The specific suggestions must follow the visible
RGGVY question and evidence, without a scripted pair of estimators. The expert
accepts reasoned rejection or improvement; neither implementation of both ideas
nor a stronger causal conclusion is required.

The consultant's earlier discussion of alternatives does not retire these
required expert contributions. If an explicit user or operator stop ends the
run before both suggestions, mark expert coverage incomplete. Forgetting a
suggestion or selecting the report prematurely is an actor-fidelity issue.
Neither alternative persona inherits extra claim pressure from this problem's
study context.

A seeded communication challenge also grants no extra pressure budget. These
events follow actual proposals or findings, not numbered replies. Do not
manufacture an untriggered optional pressure after a legitimate stop; record the coverage
limit. No family repeats after a reasoned resolution.

Study context is initially unvolunteered, not inaccessible. A relevant request
makes its source eligible immediately. Equivalent questions work without a
filename password. Preserve short necessary answers and requested files;
retain unfinished compound requests privately. No source is withheld until a
particular reply count. The existing 50-word, two-item spoken reply limits apply
to every persona. The same reusable profiles apply to the four synthetic
problems, using each problem's facts and scientific scope.

## Scientific issues to assess

The following evidence locations help reviewers distinguish grounded discovery
from a generic checklist. Journal page numbers refer to the main paper;
appendix page numbers below count PDF pages, including its first page.

| Issue | Evidence and observable consultant action |
|---|---|
| Eligibility versus electricity receipt | Main III.A-B, pp. 2944-2946, and VI.A, pp. 2958-2962. Clarify the intervention, population and horizon before choosing ITT, IV or an extrapolated policy claim. |
| Habitation assignment and RD sample | Main III.A, pp. 2944-2945. Investigate single-habitation status, 2001 population, rollout wave, linkage quality and outcome availability. Check the running variable and actual threshold coding. |
| Timing and later-wave comparisons | Main Figure 6, p. 2953; appendix C.1, PDF pp. 49-50. Separate funds, implementation and measurement dates. Examine the authors' delay-based justification for using 2010 controls rather than presuming contamination. |
| Rollout selection and parallel trends | Main III.B, p. 2946; appendix B.5, PDF pp. 46-48. Investigate assignment and pre-period evidence; explain why a nonsignificant pretrend is not proof of identification. |
| Survey units and independent comparisons | Main Table 3, p. 2955; appendix C.11, PDF pp. 64-68. Check survey weights, repeated cross-sections, historical district splits and source clusters before choosing aggregation or uncertainty calculations. |
| First stage and IV assumptions | Main Table 7, p. 2961; appendix B.5, PDF pp. 47-48. Investigate local instrument strength, treatment measurement and exclusion assumptions. National results do not certify a state-specific IV analysis. |
| Spillovers and transport | Main II-III, pp. 2943-2946. Distinguish a local village effect from district effects and the user's intended population. Investigate relevant exposure links without asserting an unobserved spillover violation. |
| Effect uncertainty and welfare claims | Main Tables 4-9, pp. 2956-2967. Separate uncertainty about measured effects from assumptions about universal access, costs and long-term benefits. |

The source labels and legacy sample flags require interpretation. For example,
`p_300_X` uses 2001 population centered at 300, while stored `p_300_D` includes
population exactly 300 despite its label saying greater than 300. The authors'
master script identifies old fixed-bandwidth sample flags as obsolete. Their
presence in the extract does not establish the final analytical sample.

Do not require discovery of inaccessible facts or every possible concern in
every run. Give credit when the consultant independently discovers a relevant
issue, explains its consequence, and changes or justifies the chosen scope.
Accept defensible alternatives. A consultant need not reproduce the paper's
estimator, coefficients or conclusions to pass.

## Completion and validation

A full-report endpoint requires the actual saved report, reproducible work
appropriate to the agreed scope, and verification of its sources, numbers,
uncertainty and substantive claims. A testing assessment or conversational recap
is not that report. Preserve unresolved limitations and promised corrections.

The additional RGGVY-only [research coordinator](rggvy-continuity.md) exercises
the required bounded participation contract in new persona/variant 1.1.0
compositions while retaining the household-welfare goal. Frozen 1.0.0 attempts
keep their conditional deferral/return rules.
It uses the same scientific sources and a separate private continuity review.

Validate all four RGGVY persona compositions against the same source bytes and
scientific facts. Record source releases and inspect actual dialogue and saved
artifacts. For an expert run, identify the two actual proposals and the
intervening substantive user reply. Review why the ideas differ, how the
consultant evaluated or improved them, and the resulting analysis decision.
Implementation alone does not establish a sound response; a reasoned rejection
may be correct. Fixture checks and rehearsals do not establish live qualification;
the selected host, model and composition still need their own observed run.
