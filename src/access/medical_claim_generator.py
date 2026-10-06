import pandas as pd
from pathlib import Path

from src.data.data_loader import load_file

Project_root = Path(__file__).resolve().parents[2]

encounter_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_encounters.csv"
)

encounters = load_file(encounter_path)
#
# print("Encounters shape:", encounters.shape)
# print("\nEncounter columns:")
# print(encounters.columns.tolist())
#
# print("\nEncounter types:")
# print(encounters["Encounter_Type"].value_counts())

medical_claims = encounters[
    [
        "Encounter_ID",
        "Patient_ID",
        "HCP_ID",
        "Facility_ID",
        "Year",
        "Encounter_Date",
        "Care_Pathway",
        "Encounter_Type",
        "Primary_Condition",
        "Specialty",
        "Care_Setting"
    ]
].copy()

medical_claims = medical_claims.rename(
    columns={
        "Encounter_Date": "Claim_Date",
        "Care_Pathway": "Claim_Pathway",
        "Encounter_Type": "Service_Type"
    }
)

medical_claims.insert(
    0,
    "Medical_Claim_ID",
    [
        f"MEDCLM_{i:06d}"
        for i in range(1, len(medical_claims) + 1)
    ]
)

# print("\nMedical Claims shape:", medical_claims.shape)
# print("\nMedical Claims columns:")
# print(medical_claims.columns.tolist())
#
# print("\nFirst 5 medical claims:")
# print(medical_claims.head().to_string(index=False))

service_costs = {
    "Routine Visit": 75,
    "Chronic Disease Management": 100,
    "Follow-up": 80,
    "Specialist Consultation": 150,
    "Specialist Follow-up": 100,
    "Emergency": 250,
    "Hospitalization": 500
}

medical_claims["Synthetic_Claim_Amount"] = (
    medical_claims["Service_Type"]
    .map(service_costs)
)

# print("\nMissing synthetic claim amounts:")
# print(
#     medical_claims["Synthetic_Claim_Amount"].isna().sum()
# )
#
# print("\nClaim amounts by service type:")
# print(
#     medical_claims[
#         ["Service_Type", "Synthetic_Claim_Amount"]
#     ]
#     .drop_duplicates()
#     .sort_values("Service_Type")
#     .to_string(index=False)
# )

print("\nMedical Claims QA")

print(
    "Duplicate Medical_Claim_ID:",
    medical_claims["Medical_Claim_ID"].duplicated().sum()
)

print(
    "Duplicate Encounter_ID:",
    medical_claims["Encounter_ID"].duplicated().sum()
)

print(
    "Missing Patient_ID:",
    medical_claims["Patient_ID"].isna().sum()
)

print(
    "Missing HCP_ID:",
    medical_claims["HCP_ID"].isna().sum()
)

print(
    "Missing Facility_ID:",
    medical_claims["Facility_ID"].isna().sum()
)

print(
    "Missing Claim_Date:",
    medical_claims["Claim_Date"].isna().sum()
)

print(
    "Negative claim amounts:",
    (medical_claims["Synthetic_Claim_Amount"] < 0).sum()
)

medical_claims_output_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_medical_claims.csv"
)

medical_claims.to_csv(
    medical_claims_output_path,
    index=False
)

print(
    f"\nSaved medical claims: {medical_claims_output_path}"
)