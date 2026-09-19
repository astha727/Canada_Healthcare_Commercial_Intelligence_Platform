import pandas as pd
from pathlib import Path
import numpy as np

from src.data.data_loader import load_file

project_root = Path(__file__).resolve().parents[2]

patient_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_master.csv"
)

diagnosis_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_diagnoses.csv"
)

hcp_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_hcp_master.csv"
)

mapping_path = (
    project_root
    / "Data"
    / "processed"
    / "disease_specialty_mapping.csv"
)

patients = load_file(patient_path)
diagnoses = load_file(diagnosis_path)
hcp = load_file(hcp_path)
disease_specialty = load_file(mapping_path)
diagnoses["Diagnosis_Date"] = pd.to_datetime(
    diagnoses["Diagnosis_Date"]
).dt.normalize()

rng = np.random.default_rng(42)
date_rng = np.random.default_rng(42)

# PRIMARY SPECIALTY ELIGIBILITY

patient_specialty = diagnoses.merge(
    disease_specialty[
        [
            "Condition",
            "Primary_Specialty"
        ]
    ],
    on="Condition",
    how="left"
)

# ADD PATIENT PROVINCE

patient_specialty = patient_specialty.merge(
    patients[
        [
            "Patient_ID",
            "Province"
        ]
    ],
    on="Patient_ID",
    how="left"
)


# FIND ELIGIBLE HCPS

eligible_hcps = patient_specialty.merge(
    hcp[
        [
            "HCP_ID",
            "Province",
            "Specialty"
        ]
    ],
    left_on=[
        "Province",
        "Primary_Specialty"
    ],
    right_on=[
        "Province",
        "Specialty"
    ],
    how="left"
)

# ELIGIBILITY QA

missing_hcp = eligible_hcps[
    eligible_hcps["HCP_ID"].isna()
]


# HCP COVERAGE IN SMALL PROVINCES AND TERRITORIES

small_region_hcps = (
    hcp[
        hcp["Province"].isin(
            [
                "Prince Edward Island",
                "Yukon",
                "Northwest Territories",
                "Nunavut"
            ]
        )
    ]
    .groupby(
        [
            "Province",
            "Specialty"
        ]
    )
    .size()
    .reset_index(name="HCP_Count")
    .sort_values(
        [
            "Province",
            "Specialty"
        ]
    )
)

# PATIENT DIAGNOSIS BURDEN

diagnosis_burden = (
    diagnoses[
        [
            "Patient_ID",
            "Condition"
        ]
    ]
    .drop_duplicates()
    .groupby("Patient_ID")
    .size()
    .reset_index(name="Diagnosis_Count")
)





# IDENTIFY MISSING HCP ELIGIBILITY

missing_hcp = eligible_hcps[
    eligible_hcps["HCP_ID"].isna()
].copy()


# MISSING HCP COVERAGE

missing_combinations = (
    missing_hcp[
        [
            "Province",
            "Primary_Specialty"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "Province",
            "Primary_Specialty"
        ]
    )
)


# PATIENT OBSERVATION WINDOW

reference_date = pd.Timestamp("2024-07-01")
observation_start_date = pd.Timestamp("2014-07-01")

first_diagnosis = (
    diagnoses
    .groupby("Patient_ID")["Diagnosis_Date"]
    .min()
    .reset_index(name="First_Diagnosis_Date")
)

patient_observation = first_diagnosis.copy()

patient_observation["Observation_Start"] = (
    patient_observation["First_Diagnosis_Date"]
    .clip(lower=observation_start_date)
)

patient_observation["Observation_End"] = reference_date


# ADD DIAGNOSIS BURDEN TO OBSERVATION TABLE

patient_observation = patient_observation.merge(
    diagnosis_burden,
    on="Patient_ID",
    how="left"
)

# OBSERVATION DURATION

patient_observation["Observation_Years"] = (
    (
        patient_observation["Observation_End"]
        - patient_observation["Observation_Start"]
    ).dt.days
    / 365.25
)

# ENCOUNTER INTENSITY

def assign_encounter_intensity(diagnosis_count):

    if diagnosis_count == 1:
        return "Low"

    elif diagnosis_count == 2:
        return "Moderate"

    elif diagnosis_count == 3:
        return "Moderate-High"

    else:
        return "High"


patient_observation["Encounter_Intensity"] = (
    patient_observation["Diagnosis_Count"]
    .apply(assign_encounter_intensity)
)

# YEAR-LEVEL OBSERVATION

observation_rows = []

for _, row in patient_observation.iterrows():

    years = range(
        row["Observation_Start"].year,
        row["Observation_End"].year + 1
    )

    for year in years:

        year_start = pd.Timestamp(f"{year}-01-01")
        year_end = pd.Timestamp(f"{year}-12-31")

        active_start = max(
            row["Observation_Start"],
            year_start
        )

        active_end = min(
            row["Observation_End"],
            year_end
        )

        active_days = (
                              active_end - active_start
                      ).days + 1

        days_in_year = (
                               year_end - year_start
                       ).days + 1

        year_fraction = active_days / days_in_year

        observation_rows.append({
            "Patient_ID": row["Patient_ID"],
            "Year": year,
            "Active_Start": active_start,
            "Active_End": active_end,
            "Active_Days": active_days,
            "Year_Fraction": year_fraction,
            "Diagnosis_Count": row["Diagnosis_Count"],
            "Encounter_Intensity": row["Encounter_Intensity"]
        })

patient_year_observation = pd.DataFrame(observation_rows)

# ANNUAL ENCOUNTER RATE ASSUMPTION

annual_encounter_rate = {
    "Low": 1.5,
    "Moderate": 2.5,
    "Moderate-High": 3.5,
    "High": 4.5
}

patient_year_observation["Expected_Encounters"] = (
    patient_year_observation["Encounter_Intensity"]
    .map(annual_encounter_rate)
    * patient_year_observation["Year_Fraction"]
)

# GENERATE ANNUAL ENCOUNTER COUNTS

patient_year_observation["Encounter_Count"] = (
    rng.poisson(
        patient_year_observation["Expected_Encounters"]
    )
)


# ENCOUNTER DATE GENERATION

def generate_encounter_dates(
    start_date,
    end_date,
    encounter_count,
    rng
):

    if encounter_count == 0:
        return []

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    date_range = (
        end_date - start_date
    ).days

    random_offsets = rng.integers(
        0,
        date_range + 1,
        size=encounter_count
    )

    encounter_dates = [
        start_date + pd.Timedelta(days=int(offset))
        for offset in random_offsets
    ]

    return sorted(encounter_dates)


# GENERATE ENCOUNTER DATE RECORDS

encounter_date_rows = []

for _, row in patient_year_observation.iterrows():

    encounter_dates = generate_encounter_dates(
        row["Active_Start"],
        row["Active_End"],
        int(row["Encounter_Count"]),
        date_rng
    )

    for encounter_date in encounter_dates:

        encounter_date_rows.append({
            "Patient_ID": row["Patient_ID"],
            "Year": row["Year"],
            "Encounter_Date": encounter_date
        })

encounter_dates = pd.DataFrame(encounter_date_rows)

# CREATE ENCOUNTER IDs

encounter_dates["Encounter_ID"] = [
    f"ENC_{i:06d}"
    for i in range(1, len(encounter_dates) + 1)
]

encounter_dates = encounter_dates[
    [
        "Encounter_ID",
        "Patient_ID",
        "Year",
        "Encounter_Date"
    ]
]

# PRIMARY CARE ENCOUNTER ASSUMPTIONS

primary_care_share = 0.80

primary_care_type_probabilities = {
    "Routine Visit": 0.45,
    "Chronic Disease Management": 0.35,
    "Follow-up": 0.20
}


# CLASSIFY PRIMARY CARE ENCOUNTERS

pathway_rng = np.random.default_rng(42)

encounter_dates["Care_Pathway"] = np.where(
    pathway_rng.random(len(encounter_dates)) < primary_care_share,
    "Primary Care",
    "Other"
)
# ASSIGN PRIMARY CARE ENCOUNTER TYPES

primary_care_mask = (
    encounter_dates["Care_Pathway"] == "Primary Care"
)

encounter_dates.loc[
    primary_care_mask,
    "Encounter_Type"
] = pathway_rng.choice(
    list(primary_care_type_probabilities.keys()),
    size=primary_care_mask.sum(),
    p=list(primary_care_type_probabilities.values())
)

primary_care_counts = (
    encounter_dates.loc[
        primary_care_mask,
        "Encounter_Type"
    ]
    .value_counts()
)

primary_care_percent = (
    primary_care_counts
    / primary_care_counts.sum()
    * 100
)

# SPECIALIST REFERRAL ASSUMPTIONS

specialist_referral_probability = {
    "Higher": 0.30,
    "Moderate": 0.15,
    "Lower": 0.05
}

condition_referral_category = {
    "Stroke": "Higher",
    "Multiple sclerosis": "Higher",
    "Parkinsonism, including Parkinson disease": "Higher",
    "Dementia, including Alzheimer disease": "Higher",
    "Epilepsy": "Higher",

    "Heart failure": "Moderate",
    "Ischemic heart disease": "Moderate",
    "Acute myocardial infarction": "Moderate",
    "Osteoporosis": "Moderate",
    "Rheumatoid arthritis": "Moderate",
    "Osteoarthritis": "Moderate",

    "Diabetes mellitus (types combined), excluding gestational diabetes": "Lower",
    "Hypertension": "Lower",
    "Asthma": "Lower",
    "Chronic obstructive pulmonary disease": "Lower",
    "Schizophrenia": "Lower"
}


# ATTACH REFERRAL ASSUMPTIONS TO DIAGNOSES

diagnoses["Referral_Category"] = diagnoses["Condition"].map(
    condition_referral_category
)

diagnoses["Referral_Probability"] = diagnoses["Referral_Category"].map(
    specialist_referral_probability
)

# GENERATE REFERRAL EVENTS

referral_rng = np.random.default_rng(42)

diagnoses["Referral_Flag"] = (
    referral_rng.random(len(diagnoses))
    < diagnoses["Referral_Probability"]
)
# CREATE REFERRAL EVENTS

referrals = diagnoses.loc[
    diagnoses["Referral_Flag"],
    [
        "Patient_ID",
        "Condition",
        "Diagnosis_Date",
        "Referral_Category",
        "Referral_Probability"
    ]
].copy()

referrals = referrals.merge(
    disease_specialty[
        [
            "Condition",
            "Primary_Specialty"
        ]
    ],
    on="Condition",
    how="left"
)

# ADD PATIENT OBSERVATION START

referrals = referrals.merge(
    patient_observation[
        [
            "Patient_ID",
            "Observation_Start",
            "Observation_End"
        ]
    ],
    on="Patient_ID",
    how="left"
)

# CALCULATE REFERRAL DATE WINDOW

maximum_wait_days = 180

referrals["Referral_Start"] = (
    referrals[
        ["Diagnosis_Date", "Observation_Start"]
    ]
    .max(axis=1)
)

referrals["Latest_Referral_Date"] = (
    reference_date
    - pd.Timedelta(days=maximum_wait_days)
)

# IDENTIFY OBSERVABLE SPECIALIST CONSULTATIONS

referrals["Consultation_Observable"] = (
    referrals["Referral_Start"]
    <= referrals["Latest_Referral_Date"]
)

# IDENTIFY OBSERVABLE SPECIALIST CONSULTATIONS

referrals["Consultation_Observable"] = (
    referrals["Referral_Start"]
    <= referrals["Latest_Referral_Date"]
)

# GENERATE REFERRAL DATES

referral_date_rng = np.random.default_rng(42)

referrals["Referral_Date"] = pd.NaT

observable_mask = referrals["Consultation_Observable"]

for idx in referrals.index[observable_mask]:

    start_date = referrals.loc[idx, "Referral_Start"]
    end_date = referrals.loc[idx, "Latest_Referral_Date"]

    date_range = (
        end_date - start_date
    ).days

    random_offset = referral_date_rng.integers(
        0,
        date_range + 1
    )

    referrals.loc[idx, "Referral_Date"] = (
        start_date
        + pd.Timedelta(days=int(random_offset))
    )

# GENERATE SPECIALIST WAIT TIME

wait_rng = np.random.default_rng(42)

referrals["Referral_to_Encounter_Days"] = pd.NA

referrals.loc[
    observable_mask,
    "Referral_to_Encounter_Days"
] = wait_rng.integers(
    30,
    181,
    size=observable_mask.sum()
)

# DERIVE SPECIALIST CONSULTATION DATE

referrals["Consultation_Date"] = pd.NaT

referrals.loc[
    observable_mask,
    "Consultation_Date"
] = (
    referrals.loc[
        observable_mask,
        "Referral_Date"
    ]
    + pd.to_timedelta(
        referrals.loc[
            observable_mask,
            "Referral_to_Encounter_Days"
        ],
        unit="D"
    )
)

other_pathway_probabilities = {
    "Specialist": 0.75,
    "Emergency": 0.15,
    "Hospitalization": 0.10
}

other_mask = (
    encounter_dates["Care_Pathway"] == "Other"
)

encounter_dates.loc[
    other_mask,
    "Care_Pathway"
] = pathway_rng.choice(
    list(other_pathway_probabilities.keys()),
    size=other_mask.sum(),
    p=list(other_pathway_probabilities.values())
)

# ENCOUNTER TYPE

encounter_dates["Encounter_Type"] = pd.NA

# Primary Care
primary_care_mask = (
    encounter_dates["Care_Pathway"] == "Primary Care"
)

encounter_dates.loc[
    primary_care_mask,
    "Encounter_Type"
] = encounter_dates.loc[
    primary_care_mask,
    "Encounter_Type"
]

# SPECIALIST ENCOUNTER TYPE

specialist_mask = (
    encounter_dates["Care_Pathway"] == "Specialist"
)

specialist_encounters = encounter_dates.loc[
    specialist_mask
].copy()

specialist_encounters = specialist_encounters.sort_values(
    ["Patient_ID", "Encounter_Date", "Encounter_ID"]
)

specialist_encounters["Specialist_Sequence"] = (
    specialist_encounters
    .groupby("Patient_ID")
    .cumcount()
    + 1
)

encounter_dates.loc[
    specialist_encounters.index,
    "Encounter_Type"
] = np.where(
    specialist_encounters["Specialist_Sequence"] == 1,
    "Specialist Consultation",
    "Specialist Follow-up"
)

# EMERGENCY

emergency_mask = (
    encounter_dates["Care_Pathway"] == "Emergency"
)

encounter_dates.loc[
    emergency_mask,
    "Encounter_Type"
] = "Emergency"


# HOSPITALIZATION

hospitalization_mask = (
    encounter_dates["Care_Pathway"] == "Hospitalization"
)

encounter_dates.loc[
    hospitalization_mask,
    "Encounter_Type"
] = "Hospitalization"


# PRIMARY CONDITION ELIGIBILITY

encounter_condition_pool = encounter_dates[
    ["Encounter_ID", "Patient_ID", "Encounter_Date"]
].merge(
    diagnoses[
        ["Patient_ID", "Condition", "Diagnosis_Date"]
    ],
    on="Patient_ID",
    how="left"
)

encounter_condition_pool = encounter_condition_pool[
    encounter_condition_pool["Diagnosis_Date"]
    <= encounter_condition_pool["Encounter_Date"]
].copy()

condition_coverage = (
    encounter_condition_pool
    .groupby("Encounter_ID")
    .size()
)


# Assign primary care encounter types

primary_care_mask = encounter_dates["Care_Pathway"] == "Primary Care"

encounter_dates.loc[
    primary_care_mask,
    "Encounter_Type"
] = pathway_rng.choice(
    list(primary_care_type_probabilities.keys()),
    size=primary_care_mask.sum(),
    p=list(primary_care_type_probabilities.values())
)

# SPECIALIST CONDITION AND SPECIALTY ASSIGNMENT

specialist_pool = (
    encounter_condition_pool[
        encounter_condition_pool["Encounter_ID"].isin(
            specialist_encounters["Encounter_ID"]
        )
    ]
    .merge(
        disease_specialty[
            ["Condition", "Primary_Specialty"]
        ],
        on="Condition",
        how="left"
    )
)

# Most recently diagnosed eligible condition first
specialist_pool = specialist_pool.sort_values(
    [
        "Encounter_ID",
        "Diagnosis_Date",
        "Condition"
    ],
    ascending=[True, False, True]
)

# One condition per specialist encounter
specialist_assignment = (
    specialist_pool
    .drop_duplicates("Encounter_ID")
    [
        [
            "Encounter_ID",
            "Condition",
            "Primary_Specialty"
        ]
    ]
    .rename(
        columns={
            "Condition": "Primary_Condition",
            "Primary_Specialty": "Specialty"
        }
    )
)


encounter_dates = encounter_dates.merge(
    specialist_assignment,
    on="Encounter_ID",
    how="left"
)

# SPECIALIST HCP ELIGIBILITY

specialist_assignment = encounter_dates.loc[
    encounter_dates["Care_Pathway"] == "Specialist",
    [
        "Encounter_ID",
        "Patient_ID",
        "Encounter_Date",
        "Specialty"
    ]
].copy()

specialist_hcp_pool = specialist_assignment.merge(
    patients[
        ["Patient_ID", "Province"]
    ],
    on="Patient_ID",
    how="left"
)

specialist_hcp_pool = specialist_hcp_pool.merge(
    hcp[
        [
            "HCP_ID",
            "Province",
            "Specialty",
            "Facility_ID"
        ]
    ],
    on=["Province", "Specialty"],
    how="left"
)

# SPECIALIST HCP ASSIGNMENT

specialist_assignment = encounter_dates.loc[
    encounter_dates["Care_Pathway"] == "Specialist",
    [
        "Encounter_ID",
        "Patient_ID",
        "Encounter_Date",
        "Specialty",
        "Primary_Condition"
    ]
].copy()

# Add province once
specialist_assignment = specialist_assignment.merge(
    patients[
        ["Patient_ID", "Province"]
    ],
    on="Patient_ID",
    how="left"
)

# Build HCP lookup by province and specialty
hcp_lookup = (
    hcp.groupby(
        ["Province", "Specialty"]
    )["HCP_ID"]
    .apply(list)
    .to_dict()
)

# HCP → Facility lookup
hcp_facility_lookup = (
    hcp.set_index("HCP_ID")["Facility_ID"]
    .to_dict()
)

hcp_rng = np.random.default_rng(42)

# Patient → previously assigned specialist HCP
patient_hcp = {}

assigned_hcp = []
assigned_facility = []

specialist_assignment = specialist_assignment.sort_values(
    [
        "Patient_ID",
        "Encounter_Date",
        "Encounter_ID"
    ]
)

for _, row in specialist_assignment.iterrows():

    patient_id = row["Patient_ID"]
    province = row["Province"]
    specialty = row["Specialty"]

    eligible_hcps = hcp_lookup[
        (province, specialty)
    ]

    # Reuse previous specialist HCP when possible
    if patient_id in patient_hcp:

        selected_hcp = patient_hcp[patient_id]

        # Safety check
        if selected_hcp not in eligible_hcps:
            selected_hcp = eligible_hcps[
                hcp_rng.integers(
                    len(eligible_hcps)
                )
            ]

    else:

        selected_hcp = eligible_hcps[
            hcp_rng.integers(
                len(eligible_hcps)
            )
        ]

    patient_hcp[patient_id] = selected_hcp

    assigned_hcp.append(selected_hcp)

    assigned_facility.append(
        hcp_facility_lookup[selected_hcp]
    )

specialist_assignment["HCP_ID"] = assigned_hcp

specialist_assignment["Facility_ID"] = assigned_facility




# MERGE SPECIALIST ASSIGNMENTS INTO ENCOUNTERS

specialist_assignment_for_merge = specialist_assignment[
    [
        "Encounter_ID",
        "HCP_ID",
        "Facility_ID"
    ]
].copy()

encounter_dates = encounter_dates.merge(
    specialist_assignment_for_merge,
    on="Encounter_ID",
    how="left"
)



# ASSIGN HCPs TO PRIMARY CARE, EMERGENCY, AND HOSPITALIZATION

non_specialist_mask = encounter_dates["Care_Pathway"] != "Specialist"

non_specialist = encounter_dates.loc[
    non_specialist_mask,
    ["Encounter_ID", "Patient_ID", "Encounter_Date", "Care_Pathway"]
].copy()

# Bring patient province and age at encounter
non_specialist = non_specialist.merge(
    patients[
        ["Patient_ID", "Province", "Birth_Date"]
    ],
    on="Patient_ID",
    how="left"
)

non_specialist["Age_at_Encounter"] = (
    non_specialist["Encounter_Date"]
    - pd.to_datetime(non_specialist["Birth_Date"])
).dt.days / 365.25

# Synthetic HCP specialty proxy
non_specialist["Assignment_Specialty"] = np.where(
    non_specialist["Age_at_Encounter"] < 18,
    "Pediatrics",
    "Internal Medicine"
)

# Build province + specialty lookup
non_specialist_hcp_lookup = (
    hcp.groupby(
        ["Province", "Specialty"]
    )["HCP_ID"]
    .apply(list)
    .to_dict()
)

hcp_facility_lookup = (
    hcp.set_index("HCP_ID")["Facility_ID"]
    .to_dict()
)

# Assign one HCP per patient/specialty and reuse when possible
non_specialist_patient_hcp = {}

assigned_hcp = []
assigned_facility = []

non_specialist = non_specialist.sort_values(
    ["Patient_ID", "Encounter_Date", "Encounter_ID"]
)

for _, row in non_specialist.iterrows():

    patient_id = row["Patient_ID"]
    province = row["Province"]
    specialty = row["Assignment_Specialty"]

    # Use the age-appropriate specialty when available.
    # If Pediatrics is unavailable in a province/territory,
    # use Internal Medicine as a synthetic fallback.

    if (province, specialty) in non_specialist_hcp_lookup:
        eligible_hcps = non_specialist_hcp_lookup[
            (province, specialty)
        ]
    else:
        eligible_hcps = non_specialist_hcp_lookup[
            (province, "Internal Medicine")
        ]

    if (patient_id, specialty) in non_specialist_patient_hcp:
        selected_hcp = non_specialist_patient_hcp[
            (patient_id, specialty)
        ]
    else:
        selected_hcp = eligible_hcps[
            hcp_rng.integers(len(eligible_hcps))
        ]

        non_specialist_patient_hcp[
            (patient_id, specialty)
        ] = selected_hcp

    assigned_hcp.append(selected_hcp)
    assigned_facility.append(
        hcp_facility_lookup[selected_hcp]
    )

non_specialist["HCP_ID"] = assigned_hcp
non_specialist["Facility_ID"] = assigned_facility

# Merge assignments back
non_specialist_assignment = non_specialist[
    ["Encounter_ID", "HCP_ID", "Facility_ID"]
].copy()

encounter_dates = encounter_dates.merge(
    non_specialist_assignment,
    on="Encounter_ID",
    how="left",
    suffixes=("", "_new")
)

# Fill HCP/facility only for encounters that did not already
# receive specialist assignments
encounter_dates["HCP_ID"] = encounter_dates["HCP_ID"].fillna(
    encounter_dates["HCP_ID_new"]
)

encounter_dates["Facility_ID"] = encounter_dates["Facility_ID"].fillna(
    encounter_dates["Facility_ID_new"]
)

encounter_dates = encounter_dates.drop(
    columns=["HCP_ID_new", "Facility_ID_new"]
)


# CARE SETTING

care_setting_map = {
    "Primary Care": "Primary Care",
    "Specialist": "Specialist Clinic",
    "Emergency": "Emergency Department",
    "Hospitalization": "Inpatient"
}

encounter_dates["Care_Setting"] = (
    encounter_dates["Care_Pathway"]
    .map(care_setting_map)
)



# LINK REFERRALS TO OBSERVED SPECIALIST ENCOUNTERS

# Prepare specialist encounters for referral matching
specialist_encounters_for_referral = encounter_dates[
    encounter_dates["Care_Pathway"] == "Specialist"
][
    [
        "Encounter_ID",
        "Patient_ID",
        "Encounter_Date",
        "Primary_Condition"
    ]
].copy()

# Prepare observable referrals
referral_candidates = referrals[
    referrals["Consultation_Observable"] == True
][
    [
        "Patient_ID",
        "Condition",
        "Referral_Date",
        "Referral_to_Encounter_Days"
    ]
].copy()

# Match by patient + condition
referral_matches = specialist_encounters_for_referral.merge(
    referral_candidates,
    left_on=["Patient_ID", "Primary_Condition"],
    right_on=["Patient_ID", "Condition"],
    how="inner"
)

# Encounter must occur after the referral and within 180 days
referral_matches = referral_matches[
    (
        referral_matches["Encounter_Date"]
        >= referral_matches["Referral_Date"]
    )
    &
    (
        referral_matches["Encounter_Date"]
        <= referral_matches["Referral_Date"]
        + pd.Timedelta(days=180)
    )
].copy()

# If multiple specialist encounters qualify, use the earliest
# observed specialist encounter after the referral.
referral_matches = referral_matches.sort_values(
    ["Patient_ID", "Referral_Date", "Encounter_Date", "Encounter_ID"]
)

referral_matches = referral_matches.drop_duplicates(
    subset=["Patient_ID", "Referral_Date"],
    keep="first"
)

# Keep only the fields needed to enrich encounters
referral_link = referral_matches[
    [
        "Encounter_ID",
        "Referral_Date"
    ]
].copy()

referral_link["Referral_Required"] = True

# Add referral information to encounters
encounter_dates = encounter_dates.merge(
    referral_link,
    on="Encounter_ID",
    how="left"
)

encounter_dates["Referral_Required"] = (
    encounter_dates["Referral_Required"]
    .fillna(False)
)

# Calculate actual observed referral-to-encounter time
encounter_dates["Referral_to_Encounter_Days"] = np.where(
    encounter_dates["Referral_Required"],
    (
        encounter_dates["Encounter_Date"]
        - encounter_dates["Referral_Date"]
    ).dt.days,
    pd.NA
)

# ASSIGN PRIMARY CONDITION TO NON-SPECIALIST ENCOUNTERS

non_specialist_condition_pool = encounter_condition_pool[
    ~encounter_condition_pool["Encounter_ID"].isin(
        specialist_encounters["Encounter_ID"]
    )
].copy()

# Most recently diagnosed eligible condition
non_specialist_condition_assignment = (
    non_specialist_condition_pool
    .sort_values(
        ["Encounter_ID", "Diagnosis_Date", "Condition"],
        ascending=[True, False, True]
    )
    .drop_duplicates("Encounter_ID")
    [
        ["Encounter_ID", "Condition"]
    ]
    .rename(
        columns={"Condition": "Primary_Condition"}
    )
)

encounter_dates = encounter_dates.merge(
    non_specialist_condition_assignment,
    on="Encounter_ID",
    how="left",
    suffixes=("", "_new")
)

encounter_dates["Primary_Condition"] = (
    encounter_dates["Primary_Condition"]
    .fillna(encounter_dates["Primary_Condition_new"])
)

encounter_dates = encounter_dates.drop(
    columns=["Primary_Condition_new"]
)








# EXPORT ENCOUNTER MASTER

encounter_output_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_encounters.csv"
)

encounter_dates.to_csv(
    encounter_output_path,
    index=False
)

print(
    f"\nEncounter master exported to:\n"
    f"{encounter_output_path}"
)