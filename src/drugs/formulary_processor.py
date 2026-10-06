import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

project_root  = Path(__file__).resolve().parents[2]
formulary_path = project_root / 'Data' / 'raw' / 'CIHI_Formulary.xlsx'

formulary = load_file(formulary_path)
OUTPUT_PATH =  project_root / "Data" / "processed" / "formulary_coverage.parquet"

print("Shape:", formulary.shape)
print("\nColumns:")
print(formulary.columns.tolist())

drug_product_path = project_root / 'Data' / 'processed' / 'drug_product_master.csv'
dpd = load_file(drug_product_path)

formulary_dins = set(formulary["DIN"].dropna().astype(str))
dpd_dins = set(dpd["DIN"].dropna().astype(str))

overlap = formulary_dins.intersection(dpd_dins)

# print("\nDIN overlap:")
# print("Unique formulary DINs:", len(formulary_dins))
# print("Unique DPD DINs:", len(dpd_dins))
# print("Overlapping DINs:", len(overlap))
#
# print(
#     "Formulary DIN overlap:",
#     round(len(overlap) / len(formulary_dins) * 100, 2),
#     "%"
# )
#
# print(
#     "DPD DIN covered by formulary:",
#     round(len(overlap) / len(dpd_dins) * 100, 2),
#     "%"
# )

# programs_by_jurisdiction = (
#     formulary.groupby("Jurisdiction")["Drug program"]
#     .nunique()
#     .sort_values(ascending=False)
# )
#
# print("\nDrug programs by jurisdiction:")
# print(programs_by_jurisdiction)
#
# print("\nPrograms by jurisdiction:")
#
# for jurisdiction, group in formulary.groupby("Jurisdiction"):
#     print(f"\n{jurisdiction}")
#     print(sorted(group["Drug program"].dropna().unique()))


formulary.columns = (
    formulary.columns
    .str.strip()
    .str.replace(" ", "_")
)


# CLEAN DIN

formulary["DIN"] = (
    formulary["DIN"]
    .astype(str)
    .str.strip()
    .str.zfill(8)
)


# CLEAN DATE COLUMNS

date_columns = [
    "DIN_market_date",
    "Coverage_start_date",
    "Coverage_end_date"
]

for column in date_columns:
    formulary[column] = pd.to_datetime(
        formulary[column],
        errors="coerce",
        dayfirst=True
    )


# BASIC VALIDATION

print("\nProcessed shape:", formulary.shape)

print("\nMissing values:")
print(formulary.isna().sum())

print("\nExact duplicate rows:", formulary.duplicated().sum())

print("\nUnique DINs:", formulary["DIN"].nunique())

print("\nJurisdictions:", formulary["Jurisdiction"].nunique())

print("\nDrug programs:", formulary["Drug_program"].nunique())

print("\nBenefit statuses:")
print(formulary["Benefit_status"].value_counts(dropna=False))


# OUTPUT_PATH.parent.mkdir(
#     parents=True,
#     exist_ok=True
# )
# # SAVE PROCESSED DATA
#
# formulary.to_parquet(
#     OUTPUT_PATH,
#     index=False
# )
#
# print("\nSaved:", OUTPUT_PATH)

# print("\nPrograms by jurisdiction:")
#
# for jurisdiction, group in formulary.groupby("Jurisdiction"):
#     programs = sorted(
#         group["Drug_program"]
#         .dropna()
#         .unique()
#     )
#
#     print(f"\n{jurisdiction} ({len(programs)} programs)")
#
#     for program in programs:
#         print(f"  - {program}")

#
# # PROGRAM SIZE BY JURISDICTION
#
# program_counts = (
#     formulary
#     .groupby(["Jurisdiction", "Drug_program"])
#     .agg(
#         Records=("DIN", "size"),
#         Unique_DINs=("DIN", "nunique")
#     )
#     .reset_index()
# )
#
# print("\nProgram sizes:")
#
# for jurisdiction, group in program_counts.groupby("Jurisdiction"):
#     print(f"\n{jurisdiction}")
#     print(
#         group
#         .sort_values("Unique_DINs", ascending=False)
#         .to_string(index=False)
#     )


# COVERAGE STATUS BY SELECTED PROGRAM

selected_programs = {
    "Alberta": [
        "Non-Group",
        "Seniors",
        "Palliative Care"
    ],
    "British Columbia": [
        "Fair PharmaCare",
        "Seniors",
        "Palliative Care"
    ],
    "Manitoba": [
        "Pharmacare",
        "Employment and Income Assistance",
        "Palliative Care"
    ],
    "New Brunswick": [
        "New Brunswick Drug Plan",
        "Seniors Plan",
        "Social Development Clients"
    ],
    "Newfoundland and Labrador": [
        "Access Plan",
        "Assurance Plan",
        "Seniors Plan"
    ],
    "Nova Scotia": [
        "Department of Community Services Programs",
        "Seniors' Pharmacare Program",
        "Drug Assistance for Cancer patients"
    ],
    "Ontario": [
        "Ontario Drug Benefit Program"
    ],
    "Prince Edward Island": [
        "Catastrophic Drug Program",
        "Seniors Drug Program",
        "Family Health Benefit Drug Program"
    ],
    "Quebec": [
        "Public Prescription Drug Insurance Plan"
    ],
    "Saskatchewan": [
        "Universal Program"
    ],
    "Yukon": [
        "Pharmacare",
        "Chronic Disease Program",
        "Palliative"
    ]
}


# FILTER TO SELECTED PROGRAMS

selected_rows = []

for jurisdiction, programs in selected_programs.items():
    subset = formulary[
        (formulary["Jurisdiction"] == jurisdiction)
        & (formulary["Drug_program"].isin(programs))
    ].copy()

    selected_rows.append(subset)

selected_formulary = pd.concat(
    selected_rows,
    ignore_index=True
)


# STATUS COUNTS

status_counts = (
    selected_formulary
    .groupby(["Jurisdiction", "Drug_program", "Benefit_status"])
    .size()
    .reset_index(name="Records")
)


# STATUS PERCENTAGES

status_counts["Percentage"] = (
    status_counts["Records"]
    /
    status_counts.groupby(
        ["Jurisdiction", "Drug_program"]
    )["Records"].transform("sum")
    * 100
)


print("\nCoverage status composition:")

print(
    status_counts
    .sort_values(
        ["Jurisdiction", "Drug_program", "Benefit_status"]
    )
    .to_string(index=False)
)