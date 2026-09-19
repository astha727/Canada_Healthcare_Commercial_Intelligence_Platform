## 2026-09-18 — Synthetic Diagnosis Design

### Objective

Create a longitudinal synthetic diagnosis table where:

- one row represents one patient-condition diagnosis relationship/event
- patients can have multiple conditions
- the patient master remains free of disease flags
- diagnosis timing is represented explicitly
- disease prevalence is calibrated to public CCDSS evidence where available

Architecture:

Patient Master → Patient Diagnoses → Encounters → Treatments → Prescriptions / Claims

### V1 disease scope

Included 16 CCDSS conditions:

1. Acute myocardial infarction
2. Heart failure
3. Hypertension
4. Ischemic heart disease
5. Stroke
6. Epilepsy
7. Multiple sclerosis
8. Parkinsonism, including Parkinson disease
9. Dementia, including Alzheimer disease
10. Diabetes mellitus (types combined), excluding gestational diabetes
11. Asthma
12. Chronic obstructive pulmonary disease
13. Schizophrenia
14. Osteoarthritis
15. Rheumatoid arthritis
16. Osteoporosis

Excluded for V1:

- Autism
- Juvenile idiopathic arthritis
- Arthritis umbrella measure
- Use of health services for mental illness and alcohol/drug induced disorders
- Use of health services for mood and anxiety disorders
- Use of health services for schizophrenia

These exclusions were made to keep V1 focused on conditions for which a relatively simple prevalence-calibrated diagnosis model could be implemented transparently.

### Reference age groups

Disease-specific CCDSS reference age groups were retained:

- Acute myocardial infarction: 20+
- Asthma: 1+
- COPD: 35+
- Dementia: 65+
- Diabetes: 1+
- Epilepsy: 1+
- Heart failure: 40+
- Hypertension: 20+
- Ischemic heart disease: 20+
- Multiple sclerosis: 20+
- Osteoarthritis: 20+
- Osteoporosis: 40+
- Parkinsonism: 40+
- Rheumatoid arthritis: 16+
- Schizophrenia: 10+
- Stroke: 20+

### Eligibility logic

Patients must meet the condition's CCDSS reference age threshold before they can receive a synthetic diagnosis.

Examples:

- Diabetes 1+ → age >= 1
- Hypertension 20+ → age >= 20
- COPD 35+ → age >= 35
- Dementia 65+ → age >= 65

Patient age is derived from `Birth_Date` using the diagnosis reference date rather than stored as a permanent patient-master attribute.

### Prevalence calibration

For each condition:

- Use province-specific CCDSS prevalence when available.
- Preserve missing CCDSS values as missing.
- When province-level prevalence is unavailable, use the condition-level median of available provincial prevalence as a synthetic calibration fallback.
- Record the calibration source during generation:
  - `CCDSS reported`
  - `Condition median imputation`

Important:

- Median imputation is a synthetic modeling assumption, not an estimate of the missing CCDSS value.
- Missing evidence must never be interpreted as zero prevalence.

### V1 diagnosis-generation approach

CCDSS prevalence is used as a population-level calibration target rather than an individual clinical risk prediction.

Process:

CCDSS prevalence
→ province-specific calibration
→ age eligibility
→ synthetic diagnosis-generation probability
→ stochastic Bernoulli assignment
→ diagnosis record

The individual probability should therefore be described as:

"Probability used for synthetic diagnosis generation"

and not as:

"Individual clinical risk of developing the disease."

### Diabetes calibration experiment

A diabetes-only diagnostic experiment was completed before generalizing the methodology to all 16 conditions.

Eligible synthetic patients:

- 9,910 of 10,000
- Eligibility threshold: age 1+

Province-specific calibration range:

- 7.54% to 11.12%

Synthetic assignment:

- No diabetes: 8,997
- Diabetes: 913
- Synthetic diabetes prevalence among eligible patients: 9.2129%

Synthetic-population-weighted calibration:

- Expected/calibrated prevalence: 9.3910%
- Generated synthetic prevalence: 9.2129%
- Difference: -0.1780 percentage points

### Diabetes province-level validation

Large provinces showed close alignment between synthetic and calibration prevalence:

- Alberta: 9.66% synthetic vs 9.31% calibration
- British Columbia: 8.68% vs 9.27%
- Ontario: 10.24% vs 10.35%
- Quebec: 7.94% vs 7.54%
- Saskatchewan: 9.27% vs 9.71%

Small provinces showed larger percentage deviations because of small synthetic sample sizes.

Examples:

- PEI: 1 / 40 = 2.5%
- Yukon: 4 / 16 = 25%

These deviations are treated as stochastic sampling variation. Synthetic data should not be forced to exactly reproduce CCDSS values.

### Diagnosis date generation

A synthetic diagnosis date is generated after diagnosis assignment.

Rules:

- `Diagnosis_Date` must be after the patient's birth date.
- `Diagnosis_Date` must be on or before the reference date.
- The earliest possible diagnosis date is based on the condition's CCDSS reference age threshold.
- Diagnosis dates are generated stochastically within the valid date range.

The diagnosis date provides longitudinal structure for downstream encounters and treatment events.

Important limitation:

The generated diagnosis date does not represent true disease onset or a clinically modeled diagnosis delay. It is a synthetic timing mechanism for constructing a longitudinal dataset.

### Comorbidity modeling

Conditions are generated independently in V1 using their respective prevalence calibrations.

This allows patients to have multiple diagnoses and creates a realistic relational structure such as:

Patient A
→ Diabetes
→ Hypertension
→ Osteoarthritis

However:

- Comorbidity frequencies are not calibrated to real-world Canadian comorbidity statistics.
- Observed condition combinations are synthetic outcomes of the independent generation process.
- No causal interpretation should be applied to the generated disease relationships.

Future versions may introduce explicitly documented disease correlations if required for a specific analytical use case.

### Final diagnosis table

File:

`Data/processed/synthetic_patient_diagnoses.csv`

Final grain:

**One row = one Patient_ID × Condition diagnosis relationship**

Final columns:

- `Patient_ID`
- `Condition`
- `Diagnosis_Date`
- `Diagnosis_Status`

`Diagnosis_Status` is currently set to `Active` for all generated diagnoses.

### Final diagnosis QA

- Final diagnosis table successfully generated.
- Unique diagnosed patients: 5,374
- Unique conditions: 16
- Missing values: 0
- Duplicate Patient_ID + Condition records: 0
- Diagnosis dates before birth: 0
- Diagnosis dates after reference date: 0
- Diagnosis status: Active
- All 16 included conditions represented.

### Diagnosis modeling guardrails

- V1 prioritizes a simple, transparent, reproducible calibration mechanism.
- Do not build individual clinical risk models for V1.
- Do not introduce unsupported age-risk curves.
- Do not over-engineer epidemiological relationships.
- Do not force synthetic prevalence to exactly equal CCDSS values.
- Do not interpret synthetic diagnosis probabilities as clinical risk.
- Do not interpret synthetic diagnosis dates as true disease onset.
- Do not interpret independently generated comorbidities as real-world prevalence or causal relationships.
- Diagnosis generation is for methodology demonstration, not clinical prediction.
- Public CCDSS evidence is used for calibration, not as patient-level clinical data.


## 2026-09-19 — Synthetic Encounter Design

### Objective

Create a longitudinal synthetic encounter table connecting patients to:

* encounters
* HCPs
* facilities
* conditions
* care pathways
* care settings
* referral relationships

The encounter layer sits between diagnoses and downstream treatment/prescription activity.

Architecture:

Patient Master → Patient Diagnoses → Encounters → Treatments → Prescriptions / Claims

### Source tables

The encounter generator uses:

* `Data/processed/synthetic_patient_master.csv`
* `Data/processed/synthetic_patient_diagnoses.csv`
* `Data/processed/synthetic_hcp_master.csv`
* `Data/processed/disease_specialty_mapping.csv`

### Observation period

Reference date:

* `2024-07-01`

Observation start:

* `2014-07-01`

A patient's observation start is clipped to the later of:

* 2014-07-01
* earliest synthetic diagnosis date

Observation end:

* 2024-07-01

Encounter dates therefore fall within the patient's active observation period.

### Encounter frequency model

Patients were assigned to synthetic encounter-intensity categories based on the number of diagnosed conditions.

Intensity categories:

* Low
* Moderate
* Moderate-High
* High

Synthetic annual encounter-rate assumptions:

* Low: 1.5 encounters/year
* Moderate: 2.5 encounters/year
* Moderate-High: 3.5 encounters/year
* High: 4.5 encounters/year

Encounter counts were generated using a Poisson process.

These rates are synthetic modeling assumptions and do not represent Canadian healthcare utilization rates.

Final encounter count:

* 84,586

### Care pathway model

Each generated encounter is assigned to one of four synthetic care pathways:

* Primary Care: 67,763
* Specialist: 12,549
* Emergency: 2,550
* Hospitalization: 1,724

Total:

* 84,586

Primary Care was modeled using an 80% share assumption.

This is a synthetic utilization structure rather than an estimate of actual Canadian care-pathway utilization.

### Encounter types

Primary-care encounters use the following synthetic distribution:

* Routine Visit: 45%
* Chronic Disease Management: 35%
* Follow-up: 20%

Final counts:

* Routine Visit: 30,623
* Chronic Disease Management: 23,604
* Follow-up: 13,536

Specialist encounters are sequenced within each patient:

* first specialist encounter → Specialist Consultation
* subsequent specialist encounters → Specialist Follow-up

Final specialist counts:

* Specialist Consultation: 4,237
* Specialist Follow-up: 8,312

Acute encounter types:

* Emergency: 2,550
* Hospitalization: 1,724

Final encounter-type counts:

* Routine Visit: 30,623
* Chronic Disease Management: 23,604
* Follow-up: 13,536
* Specialist Consultation: 4,237
* Specialist Follow-up: 8,312
* Emergency: 2,550
* Hospitalization: 1,724

### Care setting

Care pathways are mapped to synthetic care settings:

* Primary Care → Primary Care
* Specialist → Specialist Clinic
* Emergency → Emergency Department
* Hospitalization → Inpatient

All 84,586 encounters have a valid care setting.

### Primary condition assignment

Every encounter must have an eligible diagnosed condition.

A condition is eligible for an encounter when:

`Diagnosis_Date <= Encounter_Date`

For specialist encounters:

* eligible diagnosed conditions are mapped to their primary specialty
* the most recently diagnosed eligible condition is selected as the primary condition

For non-specialist encounters:

* the most recently diagnosed eligible condition is selected as the primary condition

This is a synthetic primary-condition assignment rule.

It does not imply that the selected condition caused the encounter or that it represents the clinically documented reason for the visit.

Final QA:

* Missing primary conditions: 0
* All 16 V1 conditions represented

### Specialist HCP assignment

Specialist HCP assignment uses:

`Patient Province + Disease-derived Specialty → Eligible HCPs`

The disease → specialty crosswalk determines the primary specialty associated with the patient's condition.

HCPs are selected from the synthetic HCP master within the patient's province and required specialty.

Where possible, the same HCP is reused for a patient across specialist encounters within the same specialty.

If a patient's specialty changes, a different eligible HCP may be selected.

This creates synthetic HCP continuity without forcing continuity where the specialty eligibility changes.

Final specialist HCP QA:

* Specialist encounters: 12,549
* Missing specialist HCPs: 0
* Missing specialist facilities: 0
* Unique specialist HCPs used: 720

### Non-specialist HCP assignment

The synthetic HCP universe does not contain Family Medicine or Emergency Medicine specialties.

Rather than silently treating another specialty as an exact real-world equivalent, analytical proxy rules were explicitly defined.

For adult patients:

* Internal Medicine → synthetic primary-care / acute-care physician proxy

For pediatric patients:

* Pediatrics → synthetic primary-care / acute-care physician proxy

Where Pediatrics was unavailable in a province/territory, Internal Medicine was used as a synthetic coverage fallback.

The assigned HCP represents an analytical physician proxy and does not claim to reproduce actual Canadian primary-care, emergency-department, or inpatient staffing patterns.

Final non-specialist HCP QA:

* Missing HCPs: 0
* Missing facilities: 0
* Internal Medicine encounters: 68,565
* Pediatrics encounters: 3,472

### HCP and facility continuity

HCP assignment is connected to the synthetic HCP master.

Facility assignment is inherited from the selected HCP's `Facility_ID`.

Final encounter-level HCP usage:

* Unique HCPs used: 945
* Unique facilities used: 266

The HCP master itself contains 2,009 synthetic HCPs. Not every HCP is expected to appear in the observed synthetic encounter period.

### Referral model

A separate synthetic referral process was generated for selected diagnosed conditions.

Referral probabilities were assigned by synthetic referral category:

* Higher
* Moderate
* Lower

The referral table contains 776 synthetic referral events.

Referral dates and expected consultation timing were generated separately from observed encounters.

### Referral-to-encounter linkage

Referrals were linked to observed specialist encounters only when sufficient temporal and condition evidence existed.

Linkage criteria:

1. Same patient
2. Same condition
3. Specialist encounter occurs on or after referral date
4. Specialist encounter occurs within 180 days of referral

When multiple encounters qualified, the earliest qualifying specialist encounter was selected.

Final linkage:

* Referral-linked specialist encounters: 92
* Non-specialist encounters incorrectly linked: 0
* Invalid negative referral-to-encounter intervals: 0

Important modeling decision:

Not every synthetic referral is forced to produce an observed encounter.

The referral table therefore represents a separate access/referral process, while only referrals with defensible links are connected to observed encounters.

This avoids artificially creating encounters simply to satisfy referral events.

### Final encounter table

File:

`Data/processed/synthetic_patient_encounters.csv`

Final grain:

**One row = one synthetic patient encounter**

Final dataset:

* 84,586 encounters
* 5,125 unique patients
* 945 unique HCPs used
* 266 unique facilities used

Core fields include:

* `Encounter_ID`
* `Patient_ID`
* `HCP_ID`
* `Facility_ID`
* `Encounter_Date`
* `Encounter_Type`
* `Care_Pathway`
* `Care_Setting`
* `Primary_Condition`
* `Referral_Required`
* `Referral_Date`
* `Referral_to_Encounter_Days`

Additional intermediate fields may be retained where useful for downstream analysis.

### Final encounter QA

* Total encounters: 84,586
* Duplicate Encounter_IDs: 0
* Missing HCPs: 0
* Missing facilities: 0
* Missing encounter dates: 0
* Missing encounter types: 0
* Missing care settings: 0
* Missing primary conditions: 0
* Missing referral flags: 0
* Encounter date range: 2014-07-01 to 2024-07-01
* Unique patients with encounters: 5,125
* Unique HCPs used: 945
* Unique facilities used: 266

### Encounter modeling guardrails

* Encounter rates are synthetic assumptions and are not Canadian utilization estimates.
* Care-pathway proportions are synthetic assumptions.
* HCP assignments are analytical proxies, not actual provider records.
* Internal Medicine is not being presented as equivalent to Family Medicine.
* Pediatrics fallback to Internal Medicine is a synthetic coverage rule.
* Emergency and inpatient HCP assignments do not represent actual staffing structures.
* Primary condition represents an analytically assigned condition, not necessarily the clinical reason for encounter.
* Referral linkage is conservative and does not force every referral to an observed encounter.
* Synthetic encounters should not be interpreted as real patient utilization.
* No causal interpretation should be applied to encounter-condition relationships.

### Implementation status

* Observation-period logic: complete and validated
* Encounter-intensity model: complete
* Encounter-date generation: complete
* Care-pathway generation: complete
* Encounter-type assignment: complete
* Primary-condition assignment: complete
* Specialist specialty assignment: complete
* Specialist HCP assignment: complete
* Non-specialist HCP assignment: complete
* Facility assignment: complete
* Care-setting assignment: complete
* Referral linkage: complete
* Encounter QA: complete
* Final encounter dataset saved: complete

## Project Scope — Before Streamlit

The project has many downstream tables, so synthetic data generation should remain **simple, transparent, reproducible, and commercially useful** rather than becoming an epidemiological modeling exercise.

### Completed / substantially completed

* CCDSS disease intelligence
* Disease evidence processing
* Disease → specialty crosswalk
* Canadian market context
* Synthetic patient master
* Synthetic diagnosis table
* Synthetic encounter table
* Lean synthetic HCP master
* HCP-to-patient/encounter connectivity
* Initial HCP segmentation prototype
* Initial HCP opportunity scoring
* Initial HCP priority tiers
* Initial engagement strategy framework
* Diabetes diagnosis calibration experiment

### Remaining before Streamlit

#### Patient / longitudinal layer

1. Treatment table
2. Prescription / Rx table
3. Claims / utilization table
4. Patient journey derivations

#### HCP layer

5. Create HCP treatment/Rx activity
6. Create synthetic HCP engagement events
7. Derive commercial HCP metrics from underlying events
8. Rebuild/finalize HCP segmentation using derived longitudinal activity rather than the original synthetic commercial metrics

#### Commercial intelligence layer

9. Treatment/product structure
10. Market access table
11. Competitor intelligence table
12. Commercial opportunity engine
13. Evidence objects / AI input layer

#### Application layer

14. Streamlit application
15. Integrate dashboards, filters, patient/HCP exploration, opportunity views, and AI copilot

### Current architecture

Patient Master
→ Patient Diagnoses
→ Encounters
→ Treatments
→ Prescriptions / Claims
→ Patient Journey
→ HCP Activity
→ Commercial Opportunity
→ Evidence / AI Layer
→ Streamlit Application

The encounter layer is now considered **locked** and should be treated as an upstream longitudinal source for treatment and prescription generation.


