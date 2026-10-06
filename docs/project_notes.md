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


# Patient Longitudinal & Treatment Layers

## Synthetic Patient Master

The synthetic patient master provides a stable patient-level foundation for the longitudinal healthcare data model.

### Source

* Statistics Canada 2024 population data by province, age group, and sex.
* Synthetic patient names are generated for display purposes only.
* Names are not used to infer ethnicity, nationality, socioeconomic status, or other patient characteristics.

### Final structure

* 10,000 synthetic patients
* One row per patient
* Stable `Patient_ID`
* Province
* Sex at birth
* Birth date
* Patient status

### Modeling principle

Synthetic patient demographics are calibrated to Canadian 2024 population estimates by province, age group, and sex.

Patient-level longitudinal events are generated separately rather than storing diagnoses, encounters, or treatments directly in the patient master.

---

## Synthetic Diagnosis Layer

The diagnosis layer connects synthetic patients to population-level disease surveillance evidence.

### Source

Canadian Chronic Disease Surveillance System (CCDSS).

The CCDSS data is used as a **population-level calibration target**, not as individual clinical risk data.

### Final scope

V1 includes 16 conditions:

* Acute myocardial infarction
* Asthma
* Chronic obstructive pulmonary disease
* Dementia, including Alzheimer disease
* Diabetes mellitus (types combined), excluding gestational diabetes
* Epilepsy
* Heart failure
* Hypertension
* Ischemic heart disease
* Multiple sclerosis
* Osteoarthritis
* Osteoporosis
* Parkinsonism, including Parkinson disease
* Rheumatoid arthritis
* Schizophrenia
* Stroke

### Diagnosis generation approach

```text
CCDSS prevalence
        ↓
Province-specific calibration
        ↓
Age eligibility
        ↓
Synthetic diagnosis probability
        ↓
Stochastic assignment
        ↓
Diagnosis record
```

The generated probability is explicitly a:

> "Probability used for synthetic diagnosis generation"

It is not an individual clinical risk estimate.

### Final diagnosis QA

* 7,749 diagnosis records
* 5,374 unique diagnosed patients
* 16 unique conditions
* Missing diagnosis fields: 0
* Duplicate Patient_ID + Condition relationships: 0
* Diagnosis dates before birth: 0
* Diagnosis dates after reference date: 0
* All 16 conditions represented
* Diagnosis status: Active

### Guardrails

* Missing surveillance data is not treated as zero.
* Synthetic diagnosis prevalence is not forced to exactly equal CCDSS prevalence.
* Comorbidities are allowed because a patient can have multiple synthetic diagnoses.
* Synthetic diagnosis dates represent modeled timing and should not be interpreted as true disease onset.
* The diagnosis layer demonstrates methodology rather than clinical prediction.

---

## Disease → Specialty Crosswalk

A disease-to-specialty mapping was created to connect patient disease burden with the available synthetic HCP universe.

The mapping uses the specialties actually represented in the synthetic HCP dataset.

Examples include:

* Cardiovascular conditions → Cardiology / Internal Medicine
* Neurological conditions → Neurology
* Psychiatric conditions → Psychiatry
* Osteoarthritis → Orthopedic Surgery / Internal Medicine
* COPD / Asthma → Internal Medicine

The crosswalk represents an analytical relationship rather than an exclusive real-world care pathway.

It should not be interpreted as saying that a condition is managed exclusively by one specialty.

---

# Synthetic Encounter Layer

The encounter layer introduces longitudinal healthcare utilization and patient-HCP interactions.

### Observation period

* Observation start: 2014-07-01
* Observation end: 2024-07-01
* Reference date: 2024-07-01

Patients enter the observation period at the later of:

* 2014-07-01, or
* their earliest eligible diagnosis date.

### Encounter generation

Encounter intensity is based on the number of synthetic diagnoses:

* Low: 1.5 encounters/year
* Moderate: 2.5 encounters/year
* Moderate-High: 3.5 encounters/year
* High: 4.5 encounters/year

A Poisson process is used to generate annual encounter counts.

### Final encounter volume

* 84,586 encounters
* 5,125 unique patients with encounters
* 945 unique HCPs used
* 266 unique facilities used

### Care pathways

| Care pathway    | Encounters |
| --------------- | ---------: |
| Primary Care    |     67,763 |
| Specialist      |     12,549 |
| Emergency       |      2,550 |
| Hospitalization |      1,724 |

### Encounter types

| Encounter type             | Encounters |
| -------------------------- | ---------: |
| Routine Visit              |     30,623 |
| Chronic Disease Management |     23,604 |
| Follow-up                  |     13,536 |
| Specialist Follow-up       |      8,312 |
| Specialist Consultation    |      4,237 |
| Emergency                  |      2,550 |
| Hospitalization            |      1,724 |

### Care settings

* Primary Care
* Specialist Clinic
* Emergency Department
* Inpatient

### HCP assignment

Specialist encounters are assigned using:

```text
Patient Province + Primary Specialty
```

with patient-level continuity where possible.

Non-specialist encounters use synthetic physician proxies:

* Adults → Internal Medicine
* Pediatric patients → Pediatrics
* Pediatrics fallback → Internal Medicine where necessary

These are analytical proxies and do not claim to reproduce actual Canadian primary-care, emergency, or inpatient staffing structures.

### Encounter QA

* Missing Encounter_ID: 0
* Missing Patient_ID: 0
* Missing HCP_ID: 0
* Missing Facility_ID: 0
* Missing Encounter_Date: 0
* Missing Encounter_Type: 0
* Missing Care_Setting: 0
* Missing Primary_Condition: 0
* Duplicate Encounter_IDs: 0
* Invalid encounter dates: 0

---

# Synthetic Referral Layer

A referral process was added to represent movement from diagnosed disease toward specialist care.

Referral probability varies by synthetic referral category:

* Higher
* Moderate
* Lower

The categories are modeling assumptions used to generate synthetic referral behavior.

### Final referral volume

* 776 synthetic referrals
* 741 unique referral patients
* 742 referrals were potentially observable within the consultation window
* 34 referrals were outside the observable consultation window because of the synthetic waiting-period/reference-date structure

### Referral-to-encounter linkage

Linkage requires:

1. Same patient
2. Same condition
3. Specialist encounter on or after referral date
4. Encounter within 180 days

Only qualifying observed encounters are linked.

Final linkage:

* 92 referral-linked specialist encounters
* 0 non-specialist incorrectly linked
* Remaining referrals are not artificially forced into the encounter table

### Modeling principle

A referral represents a synthetic healthcare access/process event. It does not guarantee that the corresponding consultation was observed in the encounter dataset.

This preserves imperfect linkage rather than manufacturing encounters.

---

# HCP Master

The original synthetic HCP universe is retained as the foundation for downstream commercial analytics.

### Final structure

* 2,009 synthetic HCPs
* HCP_ID
* HCP_Name
* Province
* Specialty
* Facility_ID
* HCP_Type
* Practice_Setting
* Years_in_Practice

The original 2,000-HCP universe was preserved.

An additional 9 synthetic HCPs were added only to cover province-specialty combinations required by the patient/encounter model:

* Northwest Territories — Cardiology
* Northwest Territories — Internal Medicine
* Northwest Territories — Neurology
* Nunavut — Cardiology
* Nunavut — Internal Medicine
* Yukon — Cardiology
* Yukon — Internal Medicine
* Yukon — Orthopedic Surgery
* Prince Edward Island — Neurology

These additions are synthetic coverage expansions and should not be interpreted as estimates of actual physician workforce distribution.

The earlier HCP segmentation prototype remains a methodological prototype. The lean HCP master does not carry the old commercial metrics; downstream commercial metrics should be derived from longitudinal activity.

---

# 2026-09-23 Treatment Product Layer

## Health Canada Drug Product Database

The Health Canada Drug Product Database (DPD) was used to create a human drug product master.

### Raw source

* `Data/raw/drugs.zip`
* DPD `drugs.txt`
* 13,351 total product records in the raw file
* 11,456 human products after filtering `CLASS == "Human"`

The DPD product table is maintained at the product/DIN level.

### Final drug product master

`Data/processed/drug_product_master.csv`

Fields:

* Product_ID
* DRUG_CODE
* DIN
* Brand_Name
* Descriptor
* Product_Categorization
* AI_Group_No
* Pediatric_Flag
* Last_Update_Date

QA:

* 11,456 human products
* 11,456 unique Product_ID
* 11,456 unique DIN
* Missing Product_ID: 0
* Missing DIN: 0

`AI_Group_No` is treated as a grouping field and not as a deduplication key.

### Important limitation

The DPD product table does not provide a complete therapeutic-class structure for this project's intended analytical use.

Therefore, treatment classes are explicitly modeled rather than inferred automatically from the DPD.

---

# Condition → Therapy Mapping

A transparent condition-to-therapy-class mapping was created for the 16 synthetic diagnosis conditions.

Examples:

* Diabetes → Antidiabetic
* Hypertension → Antihypertensive
* Stroke → Antithrombotic / secondary prevention
* Asthma / COPD → Respiratory
* Multiple sclerosis → Disease-modifying therapy
* Parkinsonism → Parkinson's therapy
* Schizophrenia → Antipsychotic

All 16 diagnosis conditions have a therapy-class mapping.

The mapping is a synthetic analytical framework and does not represent complete clinical treatment guidelines.

---

# Therapy → Product Mapping

A controlled product selection was created from the DPD human product master.

### Final structure

`Data/processed/therapy_product_mapping.csv`

* 36 selected synthetic products
* 14 therapy classes
* 36 unique Product_IDs
* 0 missing DINs
* 0 duplicate Product_ID rows

The selected products provide representative treatment-product variation for the portfolio.

They should not be interpreted as:

* Canadian market share
* formulary preference
* clinical interchangeability
* prescribing preference
* real-world utilization

---

# Synthetic Treatment Episode Layer

The treatment layer models longitudinal treatment episodes derived from synthetic diagnoses.

### Generation logic

```text
Diagnosis
    ↓
Condition → Therapy Class
    ↓
Treatment initiation probability
    ↓
Synthetic treatment candidate
    ↓
Treatment start date
    ↓
Therapy/product assignment
    ↓
Synthetic duration
    ↓
Observed treatment episode
```

### Treatment initiation

Each diagnosis receives a therapy-specific synthetic initiation probability.

The probability is a modeling assumption used to generate the portfolio dataset and is not a real-world treatment rate.

Initial treatment candidates were generated stochastically using a fixed random seed for reproducibility.

### Final treatment volume

* 5,219 initial treatment candidates
* 5,147 treatment episodes retained within the observation window
* 3,990 unique patients
* 16 conditions
* 14 therapy classes
* 36 products

Treatment starts whose modeled start date fell after 2024-07-01 were excluded rather than clipped to the observation boundary.

This avoids artificially creating treatment initiation events at the end of the observation period.

---

# Treatment Duration Modeling

Five duration archetypes were used:

* Chronic / indefinite
* Long-term / reassessment
* Variable chronic
* Medium / variable
* Episodic / shorter-term

Therapy classes are assigned to duration profiles based on the intended synthetic treatment behavior.

Examples:

* Antidiabetic → Chronic / indefinite
* Antihypertensive → Chronic / indefinite
* Cardiovascular → Chronic / indefinite
* Heart failure therapy → Chronic / indefinite
* Disease-modifying therapy → Chronic / indefinite
* Parkinson's therapy → Chronic / indefinite
* Antiepileptic → Chronic / indefinite
* Cognitive disorder therapy → Chronic / indefinite
* Bone health → Long-term / reassessment
* Immunomodulatory therapy → Variable chronic
* Respiratory → Medium / variable
* Antipsychotic → Medium / variable
* Antithrombotic / secondary prevention → Medium / variable
* Analgesic / anti-inflammatory → Episodic / shorter-term

Durations are generated using log-normal distributions around profile-specific median durations.

The latent duration is capped at 3,653 days because the observation window is approximately 10 years. Longer latent durations cannot be distinguished from one another using the available observation period.

---

# Treatment Status and Right-Censoring

Treatment episodes are divided into:

* `Active`
* `Discontinued`

A treatment is considered active when its modeled end date extends beyond the observation end date.

For active treatments:

```text
Treatment_End_Date = 2024-07-01
```

This represents **right-censoring**, not necessarily the true clinical discontinuation date.

For discontinued treatments:

```text
Treatment_End_Date = modeled discontinuation date
```

### Final treatment status

| Treatment status | Episodes | Share |
| ---------------- | -------: | ----: |
| Discontinued     |    3,697 | 71.8% |
| Active           |    1,450 | 28.2% |
| Total            |    5,147 |  100% |

### Observed treatment duration

`Observed_Treatment_Days` is calculated from treatment start to the observed treatment end date.

This is intentionally distinguished from the latent synthetic duration.

The latent value represents the modeled underlying duration, while the observed duration reflects what can actually be seen inside the observation window.

Three active treatments have an observed duration of zero days because they start on the observation end date, 2024-07-01. These are retained rather than artificially changed to one day.

### Treatment QA

* Treatment episode shape: 5,147 × 9 in final analytical table
* Missing values: 0
* Duplicate Treatment_IDs: 0
* Negative observed durations: 0
* Treatment-product mapping failures: 0
* Unique patients: 3,990
* Unique conditions: 16
* Unique therapy classes: 14
* Unique products: 36

### Final treatment file

`Data/processed/synthetic_patient_treatments.csv`

Final analytical fields:

* Treatment_ID
* Patient_ID
* Condition
* Therapy_Class
* Product_ID
* Treatment_Start_Date
* Treatment_End_Date
* Treatment_Status
* Observed_Treatment_Days

The latent `Synthetic_Duration_Days` is retained in the generation logic but is not included in the primary analytical treatment output.

---

# Treatment–Encounter Linkage Design Decision

Treatment episodes and healthcare encounters are intentionally maintained as separate entities.

The data does not contain a true prescription/order event indicating that a particular encounter initiated a treatment. Therefore, temporal proximity alone should not be interpreted as proof that an encounter caused treatment initiation.

A preliminary analysis found:

* 1,833 of 5,147 treatment starts had a prior encounter for the same patient
* 772 treatment starts had a prior encounter within 30 days
* 608 unique treatment starts had a same-condition encounter within 30 days
* Some treatment starts had multiple qualifying encounters

Because multiple encounters can plausibly be associated with one treatment start, forcing a single encounter as the definitive "initiation encounter" would introduce unsupported certainty.

### Decision

Treatment–encounter linkage will therefore be implemented as a **separate derived analytical table** rather than as a required field in the treatment master.

This preserves the distinction between:

* treatment episode
* healthcare encounter
* observed temporal association
* inferred treatment initiation

The future linkage layer can support analytical questions such as:

> "How often can treatment initiation be associated with an observed healthcare encounter, and what types of encounters are most commonly associated with treatment starts?"

This approach deliberately preserves imperfect real-world-style linkage rather than artificially making every treatment episode fully connected.


## Treatment ↔ Encounter Linkage

### Purpose

The treatment episode table represents the longitudinal treatment period, while the encounter table represents observed healthcare interactions. These are intentionally kept as separate entities.

A separate linkage layer was created to identify the observed encounter evidence closest to a treatment start without claiming that the encounter initiated or caused the treatment.

Output:

`Data/processed/treatment_encounter_linkage.csv`

### Linkage rule

A qualifying encounter must:

1. Belong to the same patient as the treatment.
2. Occur on or before the treatment start date.
3. Occur within 30 days before the treatment start.

Each treatment can have multiple qualifying encounters. For the final analytical linkage table, the **most recent qualifying encounter** was selected. If multiple encounters occurred on the same date, `Encounter_ID` provides a deterministic tie-breaker.

### Link types

**Strong**

* Same patient
* Same treatment condition and encounter primary condition
* Encounter occurred within 30 days before treatment start

**Contextual**

* Same patient
* Encounter occurred within 30 days before treatment start
* Encounter primary condition differs from the treatment condition

**Unlinked**

* No qualifying encounter within 30 days before treatment start.
* Unlinked treatments are not represented as rows in the linkage table because there is no corresponding `Encounter_ID`.

### Final results

* Total treatment episodes: **5,147**
* Treatment episodes with a qualifying encounter: **772**
* Unlinked treatment episodes: **4,375**
* Linked treatment episodes: **15.0%**
* Strong links: **608 (78.76%)**
* Contextual links: **164 (21.24%)**
* Final linkage rows: **772**
* One linkage row per linked treatment episode

The initial candidate pool contained **861 encounter rows** across 772 treatment episodes. Of these, 83 treatment episodes had multiple qualifying encounters: 77 had two candidates and 6 had three candidates. The most recent qualifying encounter was therefore selected for the final linkage table.

### Final analytical fields

`Treatment_ID`, `Encounter_ID`, `Patient_ID`, `Treatment_Condition`, `Treatment_Start_Date`, `Encounter_Date`, `Link_Type`, `Days_From_Encounter_To_Treatment`, `Encounter_Type`, `Care_Setting`, `Primary_Condition`, `HCP_ID`

### QA

* Duplicate `Treatment_ID`: **0**
* Duplicate `Treatment_ID + Encounter_ID`: **0**
* Invalid encounter-to-treatment day gaps: **0**
* Strong links with condition mismatch: **0**
* Contextual links with condition match: **0**
* Missing `Encounter_ID`: **0**
* Missing `HCP_ID`: **0**
* Total + unlinked reconciliation: **5,147 = 772 + 4,375**

# Claims Data Notes

## Purpose

The claims layer demonstrates how clinical and prescription activity can be connected to payer, coverage, utilization, and financial information in a Canadian life-sciences commercial intelligence workflow.

The claims data in this project is **synthetic** at the individual transaction level. Public Canadian data is used as contextual evidence and, where appropriate, for calibration/validation. The project does not attempt to reproduce proprietary claims datasets such as IQVIA, or the exact adjudication rules of Canadian provincial drug plans.

---

## Pharmacy Claims

### Data flow

```text
Patient
   ↓
Diagnosis
   ↓
Encounter
   ↓
Treatment
   ↓
Rx Event
   ↓
Pharmacy Claim
   ↓
Coverage + Formulary
   ↓
Synthetic Adjudication
   ↓
Financial Outcome
```

### Grain

V1 uses:

> **1 Rx Event → 1 Synthetic Pharmacy Claim**

Real pharmacy claims systems can contain multiple transaction types such as submission, rejection, resubmission, payment, and reversal. These transaction-level complexities are intentionally not simulated in V1.

### Pharmacy Master

A synthetic pharmacy universe was created from Rx-event volume by province.

* Total synthetic pharmacies: **39**
* Pharmacy types:

  * Community Pharmacy
  * Hospital Pharmacy
  * Specialty Pharmacy
* Pharmacy is modeled as a separate entity from the prescribing HCP.
* `Pharmacy_ID` represents the dispensing organization/location.
* `HCP_ID` represents the prescribing HCP proxy.

Pharmacy province is validated against the patient's/Rx event's province.

Output:

`Data/processed/synthetic_pharmacy_master.csv`

### Pharmacy Claims fields

The pharmacy claim contains:

* `Rx_Claim_ID`
* `Rx_Event_ID`
* `Treatment_ID`
* `Patient_ID`
* `Product_ID`
* `HCP_ID`
* `Pharmacy_ID`
* `Province`
* `Claim_Date`
* `Days_Supply`
* `Synthetic_Coverage_Program`
* `Formulary_Match`
* `Benefit_status`
* `Claim_Status`
* `Synthetic_Drug_Cost`
* `Synthetic_Markup`
* `Synthetic_Professional_Fee`
* `Submitted_Amount`
* `Accepted_Amount`
* `Plan_Paid_Amount`
* `Patient_Paid_Amount`

Output:

`Data/processed/synthetic_pharmacy_claims.csv`

---

## Coverage and Formulary

Patient coverage is a **synthetic coverage context**, not observed enrollment.

The project uses selected representative public drug programs from the formulary source rather than attempting to model every real Canadian program.

Important distinction:

> **Formulary eligibility ≠ patient eligibility ≠ claim payment.**

A formulary match means that a matching formulary record exists for the patient's synthetic province/program/date context. It does not by itself prove that the patient is eligible or that a real-world claim would be paid.

The formulary lookup is date-aware:

```text
Coverage_start_date <= Fill_Date
AND
(Coverage_end_date >= Fill_Date OR Coverage_end_date is missing)
```

Historical formulary records are retained because the same `Jurisdiction + Drug_program + DIN` can legitimately appear across different coverage periods and statuses.

Output:

`Data/processed/rx_formulary_lookup.csv`

### Synthetic adjudication rule

V1 uses a deliberately simplified rule:

```text
Formulary match = True  → Paid
Formulary match = False → Rejected
```

`Benefit`, `Limited`, and `Restricted` statuses are retained as coverage attributes.

They are **not** independently interpreted as rejection because detailed authorization/restriction criteria are outside the scope of V1.

Therefore:

> `Claim_Status` is a **synthetic adjudication outcome**, not a recreation of actual provincial adjudication.

---

## Synthetic Claim Financials

The project separates the financial components of a pharmacy claim:

```text
Synthetic Drug Cost
       +
Synthetic Markup
       +
Synthetic Professional Fee
       ↓
Submitted Amount
       ↓
Synthetic Adjudication
       ↓
Accepted Amount
       ↓
 ┌───────────────┴───────────────┐
 ▼                               ▼
Plan Paid                    Patient Paid
```

### Product cost

A stable synthetic dispensing cost is assigned at the `Product_ID` level.

This means the same synthetic product has the same underlying synthetic drug cost across its Rx events.

The cost is generated from a therapy-level synthetic range.

These values are **not observed Canadian drug prices**.

### Synthetic financial assumptions

V1 uses:

* Markup = **10% of synthetic drug cost**
* Professional fee = **$10**
* Plan paid = **80% of accepted amount**
* Patient paid = **20% of accepted amount**

These are modeling assumptions for demonstrating claims mechanics.

They should **not** be interpreted as Canadian provincial reimbursement, deductible, copayment, markup, or dispensing-fee rules.

### Financial definitions

* **Submitted Amount** = synthetic drug cost + markup + professional fee
* **Accepted Amount** = submitted amount for synthetic Paid claims; 0 for synthetic Rejected claims
* **Plan Paid Amount** = synthetic payer contribution
* **Patient Paid Amount** = remaining synthetic patient contribution

QA requirement:

```text
Plan Paid Amount + Patient Paid Amount = Accepted Amount
```

---

## Pharmacy Claims QA

Final pharmacy claims:

* **126,960 claims**
* **104,439 Paid**
* **22,521 Rejected**

QA checks completed:

* No missing synthetic drug costs
* No negative drug costs
* No negative submitted amounts
* No accepted amount greater than submitted amount
* Plan paid + patient paid reconciles to accepted amount
* Pharmacy IDs are valid
* Pharmacy province matches Rx province
* Every Rx Event has one synthetic pharmacy claim

---

# Medical Claims

## Purpose

Medical claims represent the **billing/claim side of a healthcare encounter**.

Important distinction:

> **Encounter ≠ Medical Claim**

An encounter represents a synthetic healthcare service/utilization event.

A medical claim represents the corresponding synthetic billing/financial record.

### Grain

V1 uses:

> **1 Encounter → 1 Synthetic Medical Claim**

Real Canadian medical billing systems can contain much more detailed provincial billing codes and transaction structures. These are intentionally not reproduced in V1.

### Data flow

```text
Patient
   ↓
Diagnosis
   ↓
Encounter
   ↓
Medical Claim
```

### Medical Claims fields

* `Medical_Claim_ID`
* `Encounter_ID`
* `Patient_ID`
* `HCP_ID`
* `Facility_ID`
* `Year`
* `Claim_Date`
* `Claim_Pathway`
* `Service_Type`
* `Primary_Condition`
* `Specialty`
* `Care_Setting`
* `Synthetic_Claim_Amount`

Output:

`Data/processed/synthetic_medical_claims.csv`

### Synthetic medical claim amounts

V1 uses simple service-level synthetic amounts:

| Service type               | Synthetic amount |
| -------------------------- | ---------------: |
| Routine Visit              |              $75 |
| Chronic Disease Management |             $100 |
| Follow-up                  |              $80 |
| Specialist Consultation    |             $150 |
| Specialist Follow-up       |             $100 |
| Emergency                  |             $250 |
| Hospitalization            |             $500 |

These are **synthetic demonstration values**, not Canadian physician fee schedules or actual provincial reimbursement rates.

### Medical Claims QA

Final medical claims:

* **84,586 medical claims**
* One claim per encounter
* Duplicate Medical Claim IDs: 0
* Duplicate Encounter IDs: 0
* Missing Patient IDs: 0
* Missing HCP IDs: 0
* Missing Facility IDs: 0
* Missing Claim Dates: 0
* Negative claim amounts: 0

---

# Public Canadian Drug Spending Data

The project also contains a real aggregate Canadian public drug-spending dataset covering:

* **2020–2024**
* **11 jurisdictions**
* **55 province/year observations**

The dataset includes aggregate measures such as:

* Total public drug spending
* Beneficiaries
* Spending per beneficiary
* Brand spending share
* Generic spending share
* Biologic spending share
* Demographic/geographic spending measures

This dataset is **not treated as individual claims data**.

### Intended use

The public spending data provides a **market-level benchmark/calibration layer**.

```text
Public aggregate spending
          ↓
Province × Year benchmark
          ↓
Calibration / validation
          ↓
Synthetic individual claims
```

We do **not**:

* divide provincial spending by synthetic patients to create individual claim prices
* assign aggregate provincial spending directly to individual claims
* treat public spending as an observed patient-level claim
* imply that aggregate spending represents all Canadian drug spending or all payer types

The distinction is:

```text
Level 1: Public aggregate evidence
         Province × Year

Level 2: Synthetic transaction data
         Patient × Rx Event × Claim
```

This preserves data lineage and avoids presenting synthetic transactions as observed claims.

---

# Important Modeling Boundaries

The claims layer is designed to demonstrate **data architecture and commercial reasoning**, not to reproduce the Canadian healthcare reimbursement system.

The project intentionally does not model:

* Full provincial adjudication rules
* Every provincial/territorial drug program
* Detailed deductibles and copayment schedules
* Private insurance adjudication
* Manufacturer rebates
* Complex claim reversal/resubmission workflows
* Real provincial medical billing codes
* Real-world drug prices
* Real patient enrollment
* Real prescribing behavior
* Proprietary claims datasets



### Interpretation and guardrail

The linkage represents **observed temporal and condition-based association**, not treatment initiation causality.

For example, an emergency visit or hospitalization for acute myocardial infarction may be temporally associated with a later hypertension treatment. If the encounter's primary condition is acute myocardial infarction and the treatment condition is hypertension, the relationship is classified as **Contextual**, rather than incorrectly claiming that the acute encounter initiated hypertension treatment.

This design allows acute events, specialist encounters, chronic disease management visits, and treatment episodes to coexist without forcing them into a single event or asserting unsupported clinical causality.

The treatment episode and encounter remain separate entities; this linkage table is a derived analytical relationship between them.



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


## Synthetic Treatment Switching Logic

The treatment dataset was extended to support **within-condition longitudinal treatment switching**.

* Original structure: most patient-condition combinations have one observed treatment episode.
* A controlled synthetic subset of eligible treatment episodes receives a **second sequential treatment episode for the same condition**.
* The second episode is assigned a **different product** from the same therapy class.
* The second episode begins only after the first episode ends, so treatment episodes do not overlap.
* Rx events and pharmacy claims are then regenerated from the updated treatment table so the new episodes propagate through the downstream data model.

### Current structure

* 5,118 patient-condition combinations with treatment
* 4,835 with one treatment episode
* 283 with two sequential treatment episodes
* 0 with more than two episodes
* 0 overlapping within-condition treatment episodes

### Important limitation

The switching behavior is **synthetic structural data**, introduced to demonstrate longitudinal treatment-sequence analytics. The switching parameter is **not a real-world clinical switching rate**, and the generated product transitions should not be interpreted as clinical treatment recommendations, treatment guidelines, or estimates of actual patient behavior.


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


