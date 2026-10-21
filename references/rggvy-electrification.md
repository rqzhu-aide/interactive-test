# RGGVY electrification case

For fixture authors and independent reviewers. The user actor reads only its
frozen actor packet, visible conversation and legitimately received sources.
The consultant receives only the public request and released materials.

This standalone case uses a real Chhattisgarh extract from Fiona Burlig and Louis
Preonas, *Out of the Darkness and into the Light? Development Effects of Rural
Electrification*, *Journal of Political Economy* 132(9), 2024, pp. 2937-2971.
The [paper](../standalone/rggvy-electrification/problem/public/records/paper.pdf) and
[appendix](../standalone/rggvy-electrification/problem/public/records/appendix.pdf) are shipped
sources. The [published article](https://doi.org/10.1086/730204) and
[replication archive](https://doi.org/10.7910/DVN/APWICK) establish provenance.
No external development-support directory is needed to run the frozen case.

Use the [problem definition](../standalone/rggvy-electrification/problem/problem.json)
for current material identities and release conditions, the private
[world](../standalone/rggvy-electrification/problem/world.json) for documented facts and
unknowns, and the private
[reviewer packet](../standalone/rggvy-electrification/problem/reviewer.json) for evaluation.
Its [oracle](../standalone/rggvy-electrification/problem/oracle.json) checks observable
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

## Fixed Research Coordinator

The only active RGGVY actor is the Research Coordinator. Compose it with
`--standalone rggvy-electrification`; the three general persona selectors are
not supported for new RGGVY cases. Earlier frozen runs keep their own profiles.

The coordinator retains the household-welfare goal and follows the separate
[bounded participation contract](rggvy-continuity.md): eight required public
client events, at least eight delivered consultant replies and a hard cap of
12. It has no expert proposal quota, novice deception permission or seeded
communication challenge. Follow the frozen actor and reviewer packets.

Study context is initially unvolunteered, not inaccessible. A relevant request
makes its source eligible immediately. Equivalent questions work without a
filename password. Preserve short necessary answers and requested files;
retain unfinished compound requests privately. No source is withheld until a
particular reply count. Spoken messages retain the 50-word, two-item limit.

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

The fixed [Research Coordinator](rggvy-continuity.md) also exercises bounded
continuity participation, while preserving the scientific sources and a separate
private continuity review. Frozen 1.0.0 attempts retain their original rules.

Validate the coordinator composition against the unchanged source bytes and
scientific facts. Record source releases and inspect actual dialogue and saved
artifacts, including the required public participation and deferral/return gap.
Fixture checks and rehearsals do not establish live qualification; the selected
host and model still need their own observed run.
