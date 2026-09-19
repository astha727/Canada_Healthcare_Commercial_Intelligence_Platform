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

### Implementation status

- Patient age calculation: complete and validated.
- Age eligibility function: complete and validated.
- Province-specific prevalence calibration: complete and tested.
- Diabetes stochastic assignment: complete and validated.
- Reusable diagnosis generation: complete.
- Diagnosis date generation: complete.
- Full 16-condition diagnosis table: complete.
- Diagnosis QA: complete.
- Final diagnosis dataset saved to `Data/processed/synthetic_patient_diagnoses.csv`.

## Project Scope — Before Streamlit

The project has many downstream tables, so synthetic data generation should remain **simple, transparent, reproducible, and commercially useful** rather than becoming an epidemiological modeling exercise.

### Completed / substantially completed

- CCDSS disease intelligence
- Disease evidence processing
- Disease → specialty crosswalk
- Canadian market context
- Synthetic patient master
- Synthetic diagnosis table
- HCP segmentation prototype
- HCP opportunity scoring
- HCP priority tiers
- Initial engagement strategy framework
- Diabetes diagnosis calibration experiment

### Remaining before Streamlit

#### Patient / longitudinal layer

1. Encounter table
2. Treatment table
3. Prescription / Rx table
4. Claims / utilization table
5. Patient journey derivations

#### HCP layer

6. Create lean HCP master
7. Connect HCPs to patients / encounters / treatments
8. Create HCP treatment/Rx activity
9. Create synthetic HCP engagement events
10. Derive commercial HCP metrics from underlying events

#### Commercial intelligence layer

11. Treatment/product structure
12. Market access table
13. Competitor intelligence table
14. Commercial opportunity engine
15. Evidence objects / AI input layer

#### Application layer

16. Streamlit application
17. Integrate dashboards, filters, patient/HCP exploration, opportunity views, and AI copilot