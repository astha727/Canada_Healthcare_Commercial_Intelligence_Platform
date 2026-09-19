"""
SYNTHETIC PATIENT GENERATOR

This module creates the synthetic patient master table for the
Life Sciences Commercial Intelligence Platform.

The patient table contains relatively stable demographic attributes.

One row represents one synthetic patient.

Longitudinal healthcare information such as diagnoses, encounters,
treatments, prescriptions, and claims will be stored in separate
tables and linked through Patient_ID.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.data.n_set import NAME_SETS,NAME_SET_NAMES

from src.data.data_loader import load_file

# SYNTHETIC NAME PROFILES



# LOAD SOURCE DATA

project_root = Path(__file__).resolve().parents[2]

population_data = (
    project_root
    / "Data"
    / "raw"
    / "Canada_Population_Age_Sex_2024.csv"
)

population = load_file(population_data)


# PREPARE POPULATION DISTRIBUTION

def prepare_population_distribution(population):
    """
    Prepare Canadian population data for synthetic patient sampling.

    Summary rows such as "All ages" and "Median age" are excluded
    because patients must be sampled from specific age-group and
    gender buckets.

    Returns:
        population:
            Cleaned population data with province-level totals and
            within-province sampling probabilities.

        province_distribution:
            Proportion of the Canadian population represented by
            each province/territory.
    """

    population = population[
        ~population["Age group"].isin(
            ["All ages", "Median age"]
        )
    ].copy()

    population["Province_Total"] = (
        population
        .groupby("GEO")["VALUE"]
        .transform("sum")
    )

    population["Within_Province_Probability"] = (
        population["VALUE"]
        / population["Province_Total"]
    )

    population_by_province = (
        population
        .groupby("GEO")["VALUE"]
        .sum()
        .sort_values(ascending=False)
    )

    province_distribution = (
        population_by_province
        / population_by_province.sum()
    )

    return population, province_distribution


population, province_distribution = (
    prepare_population_distribution(population)
)


# PATIENT GENERATION

def generate_patients(
    population,
    province_distribution,
    n_patients=10000,
    rng=None
):
    """
    Generate the initial synthetic patient population.

    Patients are sampled according to the Canadian 2024
    provincial population distribution.

    Args:
        population:
            Cleaned population dataframe.

        province_distribution:
            Provincial population proportions.

        n_patients:
            Number of synthetic patients to generate.

        rng:
            NumPy random number generator used for reproducible sampling.

    Returns:
        DataFrame containing Patient_ID and Province.
    """

    provinces = province_distribution.index.to_numpy()
    province_probabilities = province_distribution.to_numpy()

    sampled_provinces = rng.choice(
        provinces,
        size=n_patients,
        p=province_probabilities
    )

    patients = pd.DataFrame({
        "Patient_ID": [
            f"PAT_{i:05d}"
            for i in range(1, n_patients + 1)
        ],
        "Province": sampled_provinces
    })

    return patients


# DEMOGRAPHIC ASSIGNMENT

def assign_demographics(
    patients,
    population,
    rng
):
    """
    Assign age group and source gender category to each patient.

    Demographic sampling is conditional on the patient's province.

    For each patient, an age-group and gender combination is sampled
    according to the corresponding Statistics Canada 2024 population
    distribution for that province.

    The source gender categories "Men+" and "Women+" are retained
    as source demographic categories.
    """

    age_groups = []
    genders = []

    for province in patients["Province"]:

        province_population = population[
            population["GEO"] == province
        ]

        probabilities = (
            province_population["VALUE"]
            / province_population["VALUE"].sum()
        )

        selected_index = rng.choice(
            province_population.index.to_numpy(),
            p=probabilities.to_numpy()
        )

        selected_row = population.loc[selected_index]

        age_groups.append(selected_row["Age group"])
        genders.append(selected_row["Gender"])

    patients = patients.copy()

    patients["Age_Group"] = age_groups
    patients["Population_Gender"] = genders

    return patients

# NAME PROFILE ASSIGNMENT

def assign_n_set(
    patients,
    rng
):
    """
    Assign a synthetic name profile to each patient.

    Name profiles are sampled independently of province, age,
    and healthcare characteristics.

    All profiles have equal probability.

    The profile is used only for synthetic name generation and
    is not treated as an analytical demographic attribute.
    """

    profiles = rng.choice(
        NAME_SET_NAMES,
        size=len(patients)
    )

    patients = patients.copy()

    patients["Name_Profile"] = profiles

    return patients

# NAME GENERATION

def assign_names(
    patients,
    rng
):
    """
    Generate synthetic first and last names.

    First names are selected according to the patient's
    source gender category and synthetic name profile.

    Last names are selected from the patient's name profile.

    Names are generated only for realistic synthetic identifiers.
    They are not used as demographic or analytical attributes.
    """

    first_names = []
    last_names = []

    for _, patient in patients.iterrows():

        profile = NAME_SETS[
            patient["Name_Profile"]
        ]

        if patient["Population_Gender"] == "Women+":

            first_name = rng.choice(
                profile["Female"]
            )

        elif patient["Population_Gender"] == "Men+":

            first_name = rng.choice(
                profile["Male"]
            )

        else:
            raise ValueError(
                f"Unexpected gender category: "
                f"{patient['Population_Gender']}"
            )

        last_name = rng.choice(
            profile["Last_Names"]
        )

        first_names.append(first_name)
        last_names.append(last_name)

    patients = patients.copy()

    patients["First_Name"] = first_names
    patients["Last_Name"] = last_names

    patients["Patient_Name"] = (
        patients["First_Name"]
        + " "
        + patients["Last_Name"]
    )

    return patients

# SEX ASSIGNMENT

def assign_sex_at_birth(patients):
    """
    Convert the source population gender categories into the
    synthetic patient's Sex_at_Birth field.

    This is a modeling convention for the synthetic dataset.
    """

    patients = patients.copy()

    gender_mapping = {
        "Men+": "Male",
        "Women+": "Female"
    }

    patients["Sex_at_Birth"] = (
        patients["Population_Gender"]
        .map(gender_mapping)
    )

    if patients["Sex_at_Birth"].isna().any():
        raise ValueError(
            "Unexpected Population_Gender category found."
        )

    return patients

# BIRTH DATE ASSIGNMENT

def assign_birth_dates(
    patients,
    rng,
    reference_date="2024-07-01"
):
    """
    Assign a synthetic birth date to each patient based on Age_Group.

    The reference date represents the date on which the synthetic
    population's age distribution is calibrated.

    For bounded age groups such as "30 to 34 years", an exact age
    is randomly selected within the group. A valid birth date is
    then randomly selected for that exact age as of the reference date.

    For the open-ended "100 years and older" group, ages 100-110
    are used as a synthetic modeling assumption.

    Args:
        patients:
            Patient dataframe containing Age_Group.

        rng:
            NumPy random number generator used for reproducibility.

        reference_date:
            Date against which patient age is defined.

    Returns:
        DataFrame with Birth_Date added.
    """

    reference_date = pd.Timestamp(reference_date)

    birth_dates = []

    for age_group in patients["Age_Group"]:

        parts = age_group.split()

        # Bounded age group such as "30 to 34 years"
        if "to" in parts:

            minimum_age = int(parts[0])
            maximum_age = int(parts[2])

            age = rng.integers(
                minimum_age,
                maximum_age + 1
            )

        # Open-ended age group
        elif "and older" in age_group:

            minimum_age = int(
                age_group.split()[0]
            )

            age = rng.integers(
                minimum_age,
                111
            )

        else:
            raise ValueError(
                f"Unexpected age group format: {age_group}"
            )

        latest_birth_date = (
            reference_date
            - pd.DateOffset(years=age)
        )

        earliest_birth_date = (
            reference_date
            - pd.DateOffset(years=age + 1)
            + pd.DateOffset(days=1)
        )

        days_between = (
            latest_birth_date - earliest_birth_date
        ).days

        random_days = rng.integers(
            0,
            days_between + 1
        )

        birth_date = (
            earliest_birth_date
            + pd.Timedelta(days=int(random_days))
        )

        birth_dates.append(birth_date)

    patients = patients.copy()

    patients["Birth_Date"] = birth_dates

    return patients


# VALIDATION: PROVINCE DISTRIBUTION

def validate_province_distribution(
    patients,
    province_distribution
):
    """
    Compare the provincial distribution of synthetic patients
    with the source population distribution.

    Differences are expected because the synthetic population
    is generated through random sampling.
    """

    synthetic_counts = (
        patients["Province"]
        .value_counts()
        .sort_index()
    )

    synthetic_distribution = (
        synthetic_counts
        / len(patients)
    )

    validation = pd.DataFrame({
        "Source_Proportion": province_distribution,
        "Synthetic_Proportion": synthetic_distribution
    })

    validation["Difference"] = (
        validation["Synthetic_Proportion"]
        - validation["Source_Proportion"]
    )

    validation["Synthetic_Count"] = (
        synthetic_counts
        .reindex(province_distribution.index)
        .fillna(0)
        .astype(int)
    )

    return validation


# VALIDATION: AGE DISTRIBUTION

def validate_age_distribution(
    patients,
    population
):
    """
    Compare the national age-group distribution of synthetic patients
    with the source population distribution.

    The source population is aggregated across provinces and
    source gender categories before calculating proportions.
    """

    source_age_counts = (
        population
        .groupby("Age group")["VALUE"]
        .sum()
        .sort_index()
    )

    source_age_distribution = (
        source_age_counts
        / source_age_counts.sum()
    )

    synthetic_age_counts = (
        patients["Age_Group"]
        .value_counts()
        .reindex(source_age_counts.index)
        .fillna(0)
    )

    synthetic_age_distribution = (
        synthetic_age_counts
        / len(patients)
    )

    validation = pd.DataFrame({
        "Source_Proportion": source_age_distribution,
        "Synthetic_Proportion": synthetic_age_distribution
    })

    validation["Difference"] = (
        validation["Synthetic_Proportion"]
        - validation["Source_Proportion"]
    )

    validation["Synthetic_Count"] = (
        synthetic_age_counts
        .astype(int)
    )

    return validation


# VALIDATION: JOINT DISTRIBUTION

def validate_joint_distribution(
    patients,
    population
):
    """
    Compare the synthetic Province × Age × Gender distribution
    with the corresponding source distribution.

    This validates the full demographic structure used by
    the synthetic sampling process.
    """

    source = (
        population
        .groupby(
            ["GEO", "Age group", "Gender"]
        )["VALUE"]
        .sum()
    )

    source_distribution = (
        source
        / source.sum()
    )

    synthetic = (
        patients
        .groupby(
            ["Province", "Age_Group", "Population_Gender"]
        )
        .size()
    )

    synthetic_distribution = (
        synthetic
        / len(patients)
    )

    validation = pd.DataFrame({
        "Source_Proportion": source_distribution,
        "Synthetic_Proportion": synthetic_distribution
    })

    validation["Difference"] = (
        validation["Synthetic_Proportion"]
        - validation["Source_Proportion"]
    )

    validation["Synthetic_Count"] = (
        validation["Synthetic_Proportion"]
        * len(patients)
    ).fillna(0).round().astype(int)

    return validation


# GENERATE SYNTHETIC PATIENTS

random_seed = 42

rng = np.random.default_rng(random_seed)

patients = generate_patients(
    population,
    province_distribution,
    n_patients=10000,
    rng=rng
)

patients = assign_demographics(
    patients,
    population,
    rng=rng
)

patients = assign_n_set(
    patients,
    rng=rng
)

patients = assign_names(
    patients,
    rng=rng
)

patients = assign_sex_at_birth(
    patients
)

patients = assign_birth_dates(
    patients,
    rng=rng,
    reference_date="2024-07-01"
)


# VALIDATION: BIRTH DATE AND AGE GROUP

reference_date = pd.Timestamp("2024-07-01")

patients["Age_at_Reference"] = (
    reference_date.year
    - patients["Birth_Date"].dt.year
)

birthday_not_reached = (
    (patients["Birth_Date"].dt.month > reference_date.month)
    |
    (
        (patients["Birth_Date"].dt.month == reference_date.month)
        &
        (patients["Birth_Date"].dt.day > reference_date.day)
    )
)

patients.loc[
    birthday_not_reached,
    "Age_at_Reference"
] -= 1


# BASIC OUTPUT

print("\nPATIENT TABLE")
print(
    patients[
        [
            "Patient_ID",
            "Patient_Name",
            "Population_Gender",
            "Sex_at_Birth",
            "Name_Profile"
        ]
    ].head(20)
)

print("\nNAME PROFILE DISTRIBUTION")
print(
    patients["Name_Profile"]
    .value_counts()
)

print("\nGENERATED AGE RANGE BY AGE GROUP")

print(
    patients
    .groupby("Age_Group")["Age_at_Reference"]
    .agg(["min", "max"])
)


# REMOVE TEMPORARY VALIDATION COLUMN

patients = patients.drop(
    columns=["Age_at_Reference"]
)




# VALIDATION OUTPUT

province_validation = validate_province_distribution(
    patients,
    province_distribution
)

print("\nPROVINCE DISTRIBUTION VALIDATION")
print(province_validation)


age_validation = validate_age_distribution(
    patients,
    population
)

print("\nAGE DISTRIBUTION VALIDATION")
print(age_validation)


joint_validation = validate_joint_distribution(
    patients,
    population
)

print("\nJOINT DISTRIBUTION VALIDATION")
print(joint_validation.head(20))


# LARGEST JOINT DISTRIBUTION DIFFERENCES

print("\nLARGEST JOINT DISTRIBUTION DIFFERENCES")

print(
    joint_validation
    .sort_values(
        "Difference",
        key=lambda x: x.abs(),
        ascending=False
    )
    .head(10)
)

# REMOVE TEMPORARY GENERATION COLUMNS

patients = patients.drop(
    columns=[
        "Population_Gender",
        "Name_Profile",
        "Age_Group"
    ]
)

# ADD PATIENT STATUS

patients["Patient_Status"] = "Active"

# FINAL PATIENT MASTER QA

print("Shape:", patients.shape)

print("\nColumns:")
print(patients.columns.tolist())

print("\nMissing values:")
print(patients.isna().sum())

print("\nDuplicate Patient_IDs:", patients["Patient_ID"].duplicated().sum())

print("\nPatient_Status:")
print(patients["Patient_Status"].value_counts())

print("\nSex_at_Birth:")
print(patients["Sex_at_Birth"].value_counts())

print("\nProvince count:")
print(patients["Province"].value_counts())

print("\nSample:")
print(patients.head(10))


# SAVE PATIENT MASTER

patient_master_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_master.csv"
)

patients.to_csv(
    patient_master_path,
    index=False
)

print("\nExported:")
print(patient_master_path)