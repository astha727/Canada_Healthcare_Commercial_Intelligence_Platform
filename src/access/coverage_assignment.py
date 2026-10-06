import pandas as pd
from pathlib import Path
from src.data.data_loader import load_file


project_root = Path(__file__).resolve().parents[2]

patient_path= project_root / 'Data' / 'processed' / 'synthetic_patient_master.csv'

patients = load_file(patient_path)

default_programs = {
    "Alberta": "Non-Group",
    "British Columbia": "Fair PharmaCare",
    "Manitoba": "Pharmacare",
    "New Brunswick": "New Brunswick Drug Plan",
    "Newfoundland and Labrador": "Access Plan",
    "Nova Scotia": "Department of Community Services Programs",
    "Ontario": "Ontario Drug Benefit Program",
    "Prince Edward Island": "Catastrophic Drug Program",
    "Quebec": "Public Prescription Drug Insurance Plan",
    "Saskatchewan": "Universal Program",
    "Yukon": "Pharmacare"
}

seniors_programs = {
    "Alberta": "Seniors",
    "British Columbia": "Seniors",
    "New Brunswick": "Seniors Plan",
    "Newfoundland and Labrador": "Seniors Plan",
    "Nova Scotia": "Seniors' Pharmacare Program",
    "Prince Edward Island": "Seniors Drug Program"
}

coverage_start = "2014-07-01"
coverage_end = "2024-07-01"

# print(patients.shape)
# print(patients.columns.tolist())
# print(patients["Province"].value_counts())

patients["Birth_Date"] = pd.to_datetime(patients["Birth_Date"])

reference_date = pd.Timestamp("2014-07-01")

observation_start = pd.Timestamp("2014-07-01")
observation_end = pd.Timestamp("2024-07-01")

patients["Coverage_Start_Date"] = patients["Birth_Date"].clip(
    lower=observation_start
)

patients["Coverage_End_Date"] = observation_end

patients["Age_at_Coverage_Start"] = (
    patients["Coverage_Start_Date"].dt.year
    - patients["Birth_Date"].dt.year
    - (
        (
            patients["Coverage_Start_Date"].dt.month
            < patients["Birth_Date"].dt.month
        )
        |
        (
            (patients["Coverage_Start_Date"].dt.month == patients["Birth_Date"].dt.month)
            &
            (patients["Coverage_Start_Date"].dt.day < patients["Birth_Date"].dt.day)
        )
    )
)

default_programs = {
    "Alberta": "Non-Group",
    "British Columbia": "Fair PharmaCare",
    "Manitoba": "Pharmacare",
    "New Brunswick": "New Brunswick Drug Plan",
    "Newfoundland and Labrador": "Access Plan",
    "Nova Scotia": "Department of Community Services Programs",
    "Ontario": "Ontario Drug Benefit Program",
    "Prince Edward Island": "Catastrophic Drug Program",
    "Quebec": "Public Prescription Drug Insurance Plan",
    "Saskatchewan": "Universal Program",
    "Yukon": "Pharmacare"
}

seniors_programs = {
    "Alberta": "Seniors",
    "British Columbia": "Seniors",
    "New Brunswick": "Seniors Plan",
    "Newfoundland and Labrador": "Seniors Plan",
    "Nova Scotia": "Seniors' Pharmacare Program",
    "Prince Edward Island": "Seniors Drug Program"
}


patients["Synthetic_Coverage_Program"] = "Coverage_Not_Available"
patients["Coverage_Assignment_Type"] = "Source_Unavailable"

for province, default_program in default_programs.items():

    province_mask = patients["Province"] == province

    if province in seniors_programs:

        senior_mask = (
            province_mask
            & (patients["Age_at_Coverage_Start"] >= 65)
        )

        patients.loc[
            senior_mask,
            "Synthetic_Coverage_Program"
        ] = seniors_programs[province]

        patients.loc[
            senior_mask,
            "Coverage_Assignment_Type"
        ] = "Age_Based_Synthetic"

    default_mask = (
        province_mask
        & (patients["Synthetic_Coverage_Program"] == "Coverage_Not_Available")
    )

    patients.loc[
        default_mask,
        "Synthetic_Coverage_Program"
    ] = default_program

    patients.loc[
        default_mask,
        "Coverage_Assignment_Type"
    ] = "Province_Default_Synthetic"

# print("\nCoverage program counts:")
# print(
#     patients["Synthetic_Coverage_Program"]
#     .value_counts()
# )
#
# print("\nCoverage assignment types:")
# print(
#     patients["Coverage_Assignment_Type"]
#     .value_counts()
# )
#
# print("\nCoverage by province:")
# print(
#     patients.groupby(
#         ["Province", "Synthetic_Coverage_Program"]
#     ).size()
# )
#
# print("\nSource-unavailable patients:")
# print(
#     patients[
#         patients["Synthetic_Coverage_Program"] == "Coverage_Not_Available"
#     ][
#         ["Patient_ID", "Province", "Age_at_Coverage_Start"]
#     ]
# )
#
# print("\nSenior assignments:")
# print(
#     patients[
#         patients["Coverage_Assignment_Type"] == "Age_Based_Synthetic"
#     ][
#         ["Patient_ID", "Province", "Age_at_Coverage_Start",
#          "Synthetic_Coverage_Program"]
#     ].head(20)
# )
#
# print("\nPatients age 65+ by province:")
# print(
#     patients[
#         patients["Age_at_Coverage_Start"] >= 65
#     ]["Province"].value_counts()
# )

# senior_program_mask = patients["Synthetic_Coverage_Program"].isin(
#     seniors_programs.values()
# )
#
# print(
#     "\nPatients assigned Seniors program but age <65:",
#     (
#         senior_program_mask
#         & (patients["Age_at_Coverage_Start"] < 65)
#     ).sum()
# )
#
# print(
#     "Patients in NWT/NU with unavailable coverage:",
#     (
#         patients["Province"].isin(
#             ["Northwest Territories", "Nunavut"]
#         )
#         & (patients["Synthetic_Coverage_Program"] == "Coverage_Not_Available")
#     ).sum()
# )
#
# print(
#     "Total assigned:",
#     patients["Synthetic_Coverage_Program"].notna().sum()
# )

coverage_output = patients[
    [
        "Patient_ID",
        "Province",
        "Synthetic_Coverage_Program",
        "Coverage_Start_Date",
        "Coverage_End_Date",
        "Coverage_Assignment_Type"
    ]
].copy()

output_path = project_root / "Data" / "processed" / "synthetic_patient_coverage.csv"

coverage_output.to_csv(output_path, index=False)

print("Coverage file saved:", output_path)
print("Shape:", coverage_output.shape)