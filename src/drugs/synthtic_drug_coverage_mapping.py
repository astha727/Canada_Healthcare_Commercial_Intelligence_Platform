import pandas as pd
from pathlib import Path
# CREATE SYNTHETIC COVERAGE PROGRAM MAPPING

project_root = Path(__file__).resolve().parents[2]
coverage_mapping = [
    # Alberta
    ["Alberta", "Non-Group", "Broad", "Yes"],
    ["Alberta", "Seniors", "Population", "Yes"],
    ["Alberta", "Palliative Care", "Population", "Yes"],

    # British Columbia
    ["British Columbia", "Fair PharmaCare", "Broad", "Yes"],
    ["British Columbia", "Seniors", "Population", "Yes"],
    ["British Columbia", "Palliative Care", "Population", "Yes"],

    # Manitoba
    ["Manitoba", "Pharmacare", "Broad", "Yes"],
    ["Manitoba", "Employment and Income Assistance", "Population", "Yes"],
    ["Manitoba", "Palliative Care", "Population", "Yes"],

    # New Brunswick
    ["New Brunswick", "New Brunswick Drug Plan", "Broad", "Yes"],
    ["New Brunswick", "Seniors Plan", "Population", "Yes"],
    ["New Brunswick", "Social Development Clients", "Population", "Yes"],

    # Newfoundland and Labrador
    ["Newfoundland and Labrador", "Access Plan", "Broad", "Yes"],
    ["Newfoundland and Labrador", "Assurance Plan", "Broad", "Yes"],
    ["Newfoundland and Labrador", "Seniors Plan", "Population", "Yes"],

    # Nova Scotia
    ["Nova Scotia", "Department of Community Services Programs", "Population", "Yes"],
    ["Nova Scotia", "Seniors' Pharmacare Program", "Population", "Yes"],
    ["Nova Scotia", "Drug Assistance for Cancer patients", "Condition_Specific", "Yes"],

    # Ontario
    ["Ontario", "Ontario Drug Benefit Program", "Broad", "Yes"],

    # Prince Edward Island
    ["Prince Edward Island", "Catastrophic Drug Program", "Broad", "Yes"],
    ["Prince Edward Island", "Seniors Drug Program", "Population", "Yes"],
    ["Prince Edward Island", "Family Health Benefit Drug Program", "Population", "Yes"],

    # Quebec
    ["Quebec", "Public Prescription Drug Insurance Plan", "Broad", "Yes"],

    # Saskatchewan
    ["Saskatchewan", "Universal Program", "Broad", "Yes"],

    # Yukon
    ["Yukon", "Pharmacare", "Broad", "Yes"],
    ["Yukon", "Chronic Disease Program", "Condition_Specific", "Yes"],
    ["Yukon", "Palliative", "Population", "Yes"]
]

coverage_mapping = pd.DataFrame(
    coverage_mapping,
    columns=[
        "Jurisdiction",
        "Drug_program",
        "Program_Type",
        "Synthetic_Use"
    ]
)

OUTPUT_PATH = project_root / "Data" / "processed" / "synthetic_coverage_program_mapping.csv"

coverage_mapping.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nCoverage mapping shape:", coverage_mapping.shape)
print("\nPrograms by jurisdiction:")
print(
    coverage_mapping
    .groupby("Jurisdiction")
    .size()
)

print("\nSaved:", OUTPUT_PATH)