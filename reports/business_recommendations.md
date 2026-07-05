# Business Recommendations — Patient Segmentation Results

This is a plain-language summary of what the segmentation found and what to do
about it. For technical details, see the main [README](../README.md); for the
underlying analysis, see [`notebooks/01_eda_and_clustering.ipynb`](../notebooks/01_eda_and_clustering.ipynb).

## What we did

We grouped 2,000 patients into four segments based on age, BMI, chronic
conditions, visit frequency, billing history, and preventive care behavior —
not on a single metric, but on the overall pattern across all of them. Each
patient lands in exactly one segment.

## The four segments

| Segment | Patients | Share | Avg age | Avg risk score | Avg visits/yr | Avg billing/yr | Most common condition | Most common insurance |
|---|---|---|---|---|---|---|---|---|
| 🔴 **Highest Risk** | 331 | 16.6% | 68.7 | 74.6 | 5.6 | $6,616 | Hypertension | Medicare |
| 🟠 **High Risk** | 597 | 29.9% | 53.7 | 44.6 | 6.8 | $3,863 | Hypertension | Medicare |
| 🟡 **Moderate Risk** | 579 | 29.0% | 54.6 | 28.9 | 6.5 | $3,844 | Obesity | Medicare |
| 🟢 **Low Risk** | 493 | 24.6% | 30.4 | 9.3 | 2.5 | $2,594 | None (healthy) | Medicaid |

*(Risk score is a simple point system: +20 per chronic condition, up to +20 for
BMI, up to +15 for age, −10 for preventive care — see the README for the exact
formula.)*

## What each segment means, and what to do about it

### 🔴 Highest Risk Patients (331 patients, 16.6%)
The oldest group (avg. 68.7) and by far the most expensive per patient
(avg. $6,616/year) despite visiting less often than the two middle groups.
That combination — older, high cost, moderate visit frequency — usually means
conditions are being managed reactively rather than proactively. Hypertension
is the most common diagnosis here, and Medicare is the dominant payer, which
is expected for this age group.

**Recommended action:** prioritize this group for care management programs —
regular check-ins, medication adherence support, and early intervention
before conditions escalate into emergency or inpatient care. This is the
segment where preventive spending has the clearest chance of reducing future
cost.

### 🟠 High Risk Patients (597 patients, 29.9%)
The largest segment. Middle-aged (avg. 53.7) with the highest average BMI of
any group (38.7) and the highest visit frequency (6.8/year), but billing is
close to the Moderate group despite the elevated risk score — likely because
this group is still relatively young and not yet accumulating the same cost
burden as the Highest Risk group.

**Recommended action:** this is the group with the most to gain from
intervention now, before they age into the Highest Risk segment. Weight
management and hypertension monitoring programs would directly target this
group's two biggest risk drivers (BMI and chronic condition count).

### 🟡 Moderate Risk Patients (579 patients, 29.0%)
Similar age to the High Risk group (54.6) but with a healthy average BMI
(23.4) and the lowest chronic condition burden of the three "risk" groups.
Obesity is still the most common recorded condition, but this group's overall
profile is meaningfully healthier than High Risk.

**Recommended action:** routine preventive care and annual wellness visits
are enough here — this group doesn't need intensive management, just
consistency so they don't drift toward the High Risk segment over time.

### 🟢 Low Risk Patients (493 patients, 24.6%)
Clearly the youngest and healthiest segment (avg. age 30.4, avg. risk score
9.3) — visiting the least (2.5/year) and spending the least ($2,594/year).
Medicaid is the dominant payer here, consistent with a younger population.

**Recommended action:** minimal intervention needed. Standard reminders for
annual checkups and preventive screenings are sufficient — the goal here is
just to keep this group from being neglected entirely, not to add active
management.

## The honest caveat

These four segments are useful groupings, not sharply distinct populations —
statistically, the separation between them is moderate rather than dramatic
(this is documented and discussed with real numbers in the notebook). In
practice, that means the boundaries between "Moderate" and "High" risk in
particular should be treated as soft, not as rigid eligibility cutoffs for
any program.
