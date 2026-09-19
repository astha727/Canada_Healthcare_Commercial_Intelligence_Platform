import pandas as pd
import numpy as np
from pathlib import Path


# PROJECT PATHS

project_root = Path(__file__).resolve().parents[2]

processed_output = (
    project_root
    / "Data"
    / "processed"
)


# CONFIGURATION

REFERENCE_DATE = pd.Timestamp("2024-07-01")

DIAGNOSIS_SEED = 42
DIAGNOSIS_DATE_SEED = 123

INCLUDED_CONDITIONS = [
    "Acute myocardial infarction",
    "Heart failure",
    "Hypertension",
    "Ischemic heart disease",
    "Stroke",
    "Epilepsy",
    "Multiple sclerosis",
    "Parkinsonism, including Parkinson disease",
    "Dementia, including Alzheimer disease",
    "Diabetes mellitus (types combined), excluding gestational diabetes",
    "Asthma",
    "Chronic obstructive pulmonary disease",
    "Schizophrenia",
    "Osteoarthritis",
    "Rheumatoid arthritis",
    "Osteoporosis"
]


# LOAD SOURCE DATA

disease_evidence_path = (
    processed_output
    / "disease_market_evidence.csv"
)

patient_master_path = (
    processed_output
    / "synthetic_patient_master.csv"
)

disease_evidence = pd.read_csv(
    disease_evidence_path
)

patients = pd.read_csv(
    patient_master_path,
    parse_dates=["Birth_Date"]
)


# DISEASE CONFIGURATION

disease_config = (
    disease_evidence[
        [
            "Condition",
            "Prevalence_Age_Group"
        ]
    ]
    .drop_duplicates()
    .rename(
        columns={
            "Prevalence_Age_Group": "Reference_Age_Group"
        }
    )
)

disease_config = (
    disease_config[
        disease_config["Condition"].isin(
            INCLUDED_CONDITIONS
        )
    ]
    .sort_values("Condition")
    .reset_index(drop=True)
)


# PREVALENCE CALIBRATION

def build_prevalence_calibration(
    disease_evidence,
    condition
):
    """
    Build province-level prevalence calibration
    for one condition.

    Reported CCDSS prevalence is used where available.
    Missing provincial values are replaced with the
    condition-level median prevalence.
    """

    evidence = disease_evidence[
        disease_evidence["Condition"] == condition
    ].copy()

    calibration = evidence[
        [
            "Province",
            "Prevalence_Rate"
        ]
    ].copy()

    median_prevalence = (
        calibration["Prevalence_Rate"]
        .median()
    )

    calibration["Prevalence_Source"] = np.where(
        calibration["Prevalence_Rate"].notna(),
        "CCDSS reported",
        "Condition median imputation"
    )

    calibration["Calibration_Prevalence"] = (
        calibration["Prevalence_Rate"]
        .fillna(median_prevalence)
    )

    return calibration


# AGE CALCULATION

patients["Age"] = (
    REFERENCE_DATE.year
    - patients["Birth_Date"].dt.year
    - (
        (patients["Birth_Date"].dt.month > REFERENCE_DATE.month)
        |
        (
            (patients["Birth_Date"].dt.month == REFERENCE_DATE.month)
            &
            (patients["Birth_Date"].dt.day > REFERENCE_DATE.day)
        )
    ).astype(int)
)


# AGE ELIGIBILITY

def is_age_eligible(
    age,
    reference_age_group
):
    """
    Determine whether a patient is eligible for
    a condition based on the CCDSS reference age group.
    """

    minimum_age = int(
        reference_age_group.replace("+", "")
    )

    return age >= minimum_age


# DIAGNOSIS ASSIGNMENT

def assign_diagnosis_status(
    patients,
    probability_column,
    rng
):
    """
    Randomly assign diagnosis status using
    patient-level diagnosis probabilities.
    """

    random_numbers = rng.random(
        len(patients)
    )

    return (
        random_numbers
        < patients[probability_column]
    )


# CONDITION DIAGNOSIS GENERATION

def generate_condition_diagnoses(
    patients,
    disease_config,
    disease_evidence,
    condition,
    rng
):
    """
    Generate synthetic diagnoses for one condition.

    Patients are first filtered using the condition's
    CCDSS reference age group. Province-level prevalence
    is then used as the diagnosis probability.

    Conditions are generated independently in V1.
    """

    condition_reference_age = (
        disease_config.loc[
            disease_config["Condition"] == condition,
            "Reference_Age_Group"
        ]
        .iloc[0]
    )

    eligible = is_age_eligible(
        patients["Age"],
        condition_reference_age
    )

    eligible_patients = patients[
        eligible
    ].copy()

    condition_calibration = (
        build_prevalence_calibration(
            disease_evidence,
            condition
        )
    )

    eligible_patients = (
        eligible_patients.merge(
            condition_calibration,
            on="Province",
            how="left"
        )
    )

    eligible_patients["Diagnosis_Probability"] = (
        eligible_patients["Calibration_Prevalence"]
        / 100
    )

    eligible_patients["Has_Diagnosis"] = (
        assign_diagnosis_status(
            eligible_patients,
            "Diagnosis_Probability",
            rng
        )
    )

    diagnosed_patients = (
        eligible_patients[
            eligible_patients["Has_Diagnosis"]
        ]
        .copy()
    )

    diagnosed_patients["Condition"] = condition

    diagnosed_patients["Reference_Age_Group"] = (
        condition_reference_age
    )

    return diagnosed_patients


# DIAGNOSIS DATE GENERATION

def age_group_to_years(
    reference_age_group
):
    return int(
        reference_age_group.replace("+", "")
    )


def generate_diagnosis_dates(
    diagnosed_patients,
    reference_date,
    rng
):
    """
    Generate a synthetic diagnosis date between the
    patient's minimum eligible age and the reference date.

    Dates are synthetic and are intended to provide
    longitudinal structure rather than reproduce
    real disease onset patterns.
    """

    earliest_dates = (
        diagnosed_patients["Birth_Date"]
        + pd.to_timedelta(
            diagnosed_patients[
                "Reference_Age_Years"
            ] * 365.25,
            unit="D"
        )
    )

    latest_dates = pd.Series(
        reference_date,
        index=diagnosed_patients.index
    )

    date_range_days = (
        latest_dates
        - earliest_dates
    ).dt.days

    random_days = (
        rng.random(
            len(diagnosed_patients)
        )
        * date_range_days
    ).astype(int)

    return (
        earliest_dates
        + pd.to_timedelta(
            random_days,
            unit="D"
        )
    )


# GENERATE ALL DIAGNOSES

diagnosis_rng = np.random.default_rng(
    DIAGNOSIS_SEED
)

diagnosis_tables = []

for condition in INCLUDED_CONDITIONS:

    condition_diagnoses = (
        generate_condition_diagnoses(
            patients,
            disease_config,
            disease_evidence,
            condition,
            diagnosis_rng
        )
    )

    diagnosis_tables.append(
        condition_diagnoses
    )

all_diagnoses = pd.concat(
    diagnosis_tables,
    ignore_index=True
)


# GENERATE DIAGNOSIS DATES

all_diagnoses["Reference_Age_Years"] = (
    all_diagnoses["Reference_Age_Group"]
    .apply(age_group_to_years)
)

diagnosis_date_rng = np.random.default_rng(
    DIAGNOSIS_DATE_SEED
)

all_diagnoses["Diagnosis_Date"] = (
    generate_diagnosis_dates(
        all_diagnoses,
        REFERENCE_DATE,
        diagnosis_date_rng
    )
)


# DIAGNOSIS STATUS

all_diagnoses["Diagnosis_Status"] = (
    "Active"
)


# FINAL DIAGNOSIS TABLE

diagnoses = all_diagnoses[
    [
        "Patient_ID",
        "Condition",
        "Diagnosis_Date",
        "Diagnosis_Status"
    ]
].copy()

diagnoses = (
    diagnoses
    .sort_values(
        [
            "Patient_ID",
            "Diagnosis_Date",
            "Condition"
        ]
    )
    .reset_index(drop=True)
)


# FINAL QA

print("\nDiagnosis table shape:")
print(diagnoses.shape)

print("\nColumns:")
print(diagnoses.columns.tolist())

print("\nMissing values:")
print(diagnoses.isna().sum())

birth_dates = (
    patients
    .set_index("Patient_ID")["Birth_Date"]
)

diagnosis_before_birth = (
    diagnoses["Diagnosis_Date"]
    <= diagnoses["Patient_ID"].map(
        birth_dates
    )
).sum()

diagnosis_after_reference = (
    diagnoses["Diagnosis_Date"]
    > REFERENCE_DATE
).sum()

duplicate_diagnoses = (
    diagnoses
    .duplicated(
        ["Patient_ID", "Condition"]
    )
    .sum()
)

print(
    "\nDiagnosis before birth:",
    diagnosis_before_birth
)

print(
    "Diagnosis after reference date:",
    diagnosis_after_reference
)

print(
    "Duplicate patient-condition records:",
    duplicate_diagnoses
)

print("\nDiagnosis status:")
print(
    diagnoses["Diagnosis_Status"]
    .value_counts()
)

print(
    "\nUnique diagnosed patients:",
    diagnoses["Patient_ID"].nunique()
)

print(
    "Unique conditions:",
    diagnoses["Condition"].nunique()
)


# SAVE OUTPUT

diagnosis_output_path = (
    processed_output
    / "synthetic_patient_diagnoses.csv"
)

diagnoses.to_csv(
    diagnosis_output_path,
    index=False
)

print(
    "\nSaved:",
    diagnosis_output_path
)

