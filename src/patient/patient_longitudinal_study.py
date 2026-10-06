import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

Project_root  = Path(__file__).resolve().parents[2]

# PATIENT TIMELINE: LOAD CORE TABLES

diagnoses_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_diagnoses.csv"
)

encounters_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_encounters.csv"
)

treatments_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_treatments.csv"
)

rx_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_rx_events.csv"
)

diagnosis = load_file(diagnoses_path)
encounters = load_file(encounters_path)
treatments = load_file(treatments_path)
rx_events = load_file(rx_path)

# PATIENT TIMELINE: LOAD CLAIMS

pharmacy_claims_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_pharmacy_claims.csv"
)

medical_claims_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_medical_claims.csv"
)

pharmacy_claims = load_file(pharmacy_claims_path)
medical_claims = load_file(medical_claims_path)


# PATIENT TIMELINE: LINK RX EVENTS TO TREATMENT

rx_events_timeline = rx_events.merge(
    treatments[
        [
            "Treatment_ID",
            "Condition",
            "Therapy_Class"
        ]
    ],
    on="Treatment_ID",
    how="left"
)


# PATIENT TIMELINE: CLEAN RX EVENT LINKAGE

rx_events_timeline = (
    rx_events_timeline
    .drop(columns=["Therapy_Class_x"])
    .rename(columns={"Therapy_Class_y": "Therapy_Class"})
)

# PATIENT TIMELINE: LINK PHARMACY CLAIMS TO RX EVENTS

pharmacy_claims_timeline = pharmacy_claims.merge(
    rx_events_timeline[
        [
            "Rx_Event_ID",
            "Treatment_ID",
            "Patient_ID",
            "Condition",
            "Therapy_Class"
        ]
    ],
    on="Rx_Event_ID",
    how="left",
    suffixes=("_claim", "_rx")
)
#
# print("Shape:", pharmacy_claims_timeline.shape)
#
# print(
#     pharmacy_claims_timeline[
#         [
#             "Rx_Claim_ID",
#             "Rx_Event_ID",
#             "Patient_ID_claim",
#             "Condition",
#             "Therapy_Class",
#             "Claim_Status"
#         ]
#     ].head()
# )
#
# print("\nMissing Condition:", pharmacy_claims_timeline["Condition"].isna().sum())
# print("Missing Therapy Class:", pharmacy_claims_timeline["Therapy_Class"].isna().sum())

# PATIENT TIMELINE: DIAGNOSIS EVENTS

timeline_diagnosis = diagnosis[
    [
        "Patient_ID",
        "Diagnosis_Date",
        "Condition",
        "Diagnosis_Status"
    ]
].copy()

timeline_diagnosis = timeline_diagnosis.rename(
    columns={
        "Diagnosis_Date": "Event_Date",
        "Diagnosis_Status": "Event_Detail"
    }
)

timeline_diagnosis["Event_Type"] = "Diagnosis"
timeline_diagnosis["Event_Category"] = "Clinical"
timeline_diagnosis["Therapy_Class"] = pd.NA
timeline_diagnosis["Encounter_ID"] = pd.NA
timeline_diagnosis["Treatment_ID"] = pd.NA
timeline_diagnosis["Rx_Event_ID"] = pd.NA
timeline_diagnosis["HCP_ID"] = pd.NA
timeline_diagnosis["Product_ID"] = pd.NA
timeline_diagnosis["Event_Order"] = 1

timeline_diagnosis = timeline_diagnosis[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]

# print("Shape:", timeline_diagnosis.shape)
# print(timeline_diagnosis.head())

# PATIENT TIMELINE: TREATMENT START EVENTS

timeline_treatments = treatments[
    [
        "Patient_ID",
        "Treatment_Start_Date",
        "Condition",
        "Therapy_Class",
        "Treatment_ID",
        "Product_ID"
    ]
].copy()

timeline_treatments = timeline_treatments.rename(
    columns={
        "Treatment_Start_Date": "Event_Date"
    }
)

timeline_treatments["Event_Type"] = "Treatment Start"
timeline_treatments["Event_Category"] = "Treatment"
timeline_treatments["Encounter_ID"] = pd.NA
timeline_treatments["Rx_Event_ID"] = pd.NA
timeline_treatments["HCP_ID"] = pd.NA
timeline_treatments["Event_Detail"] = "Treatment initiated"
timeline_treatments["Event_Order"] = 2

timeline_treatments = timeline_treatments[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]

# print("Shape:", timeline_treatments.shape)
# print(timeline_treatments.head())

# PATIENT TIMELINE: ENCOUNTER EVENTS

timeline_encounters = encounters[
    [
        "Patient_ID",
        "Encounter_Date",
        "Primary_Condition",
        "Encounter_ID",
        "HCP_ID",
        "Encounter_Type"
    ]
].copy()

timeline_encounters = timeline_encounters.rename(
    columns={
        "Encounter_Date": "Event_Date",
        "Primary_Condition": "Condition",
        "Encounter_Type": "Event_Detail"
    }
)

timeline_encounters["Event_Type"] = "Encounter"
timeline_encounters["Event_Category"] = "Clinical"
timeline_encounters["Therapy_Class"] = pd.NA
timeline_encounters["Treatment_ID"] = pd.NA
timeline_encounters["Rx_Event_ID"] = pd.NA
timeline_encounters["Product_ID"] = pd.NA
timeline_encounters["Event_Order"] = 3

timeline_encounters = timeline_encounters[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]

# print("Shape:", timeline_encounters.shape)
# print(timeline_encounters.head())

# PATIENT TIMELINE: MEDICAL CLAIM EVENTS

timeline_medical = medical_claims[
    [
        "Medical_Claim_ID",
        "Encounter_ID",
        "Patient_ID",
        "HCP_ID",
        "Claim_Date",
        "Primary_Condition",
        "Service_Type",
        "Synthetic_Claim_Amount"
    ]
].copy()

timeline_medical = timeline_medical.rename(
    columns={
        "Claim_Date": "Event_Date",
        "Primary_Condition": "Condition",
        "Service_Type": "Event_Detail"
    }
)

timeline_medical["Event_Type"] = "Medical Claim"
timeline_medical["Event_Category"] = "Healthcare Utilization"
timeline_medical["Therapy_Class"] = pd.NA
timeline_medical["Treatment_ID"] = pd.NA
timeline_medical["Rx_Event_ID"] = pd.NA
timeline_medical["Product_ID"] = pd.NA
timeline_medical["Event_Order"] = 4

timeline_medical = timeline_medical[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]

# print("Shape:", timeline_medical.shape)
# print(timeline_medical.head())

# PATIENT TIMELINE: RX EVENTS

timeline_rx = rx_events_timeline[
    [
        "Patient_ID",
        "Fill_Date",
        "Condition",
        "Therapy_Class",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Rx_Event_Type"
    ]
].copy()

timeline_rx = timeline_rx.rename(
    columns={
        "Fill_Date": "Event_Date",
        "Rx_Event_Type": "Event_Detail"
    }
)

timeline_rx["Event_Type"] = "Rx Event"
timeline_rx["Event_Category"] = "Medication"
timeline_rx["Encounter_ID"] = pd.NA
timeline_rx["Event_Order"] = 5

timeline_rx = timeline_rx[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]
#
# print("Shape:", timeline_rx.shape)
# print(timeline_rx.head())
#
# print("\nMissing Condition:", timeline_rx["Condition"].isna().sum())
# print("Missing Therapy Class:", timeline_rx["Therapy_Class"].isna().sum())

# PATIENT TIMELINE: PHARMACY CLAIM EVENTS
# print(pharmacy_claims_timeline.columns.tolist())

# PATIENT TIMELINE: PHARMACY CLAIM EVENTS

timeline_pharmacy = pharmacy_claims_timeline[
    [
        "Patient_ID_claim",
        "Claim_Date",
        "Condition",
        "Therapy_Class",
        "Treatment_ID_claim",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Claim_Status"
    ]
].copy()

timeline_pharmacy = timeline_pharmacy.rename(
    columns={
        "Patient_ID_claim": "Patient_ID",
        "Claim_Date": "Event_Date",
        "Treatment_ID_claim": "Treatment_ID",
        "Claim_Status": "Event_Detail"
    }
)

timeline_pharmacy["Event_Type"] = "Pharmacy Claim"
timeline_pharmacy["Event_Category"] = "Access"
timeline_pharmacy["Encounter_ID"] = pd.NA
timeline_pharmacy["Event_Order"] = 6

timeline_pharmacy = timeline_pharmacy[
    [
        "Patient_ID",
        "Event_Date",
        "Event_Type",
        "Event_Category",
        "Condition",
        "Therapy_Class",
        "Encounter_ID",
        "Treatment_ID",
        "Rx_Event_ID",
        "HCP_ID",
        "Product_ID",
        "Event_Detail",
        "Event_Order"
    ]
]
#
# print("Shape:", timeline_pharmacy.shape)
# print(timeline_pharmacy.head())
#
# print("\nMissing Condition:", timeline_pharmacy["Condition"].isna().sum())
# print("Missing Therapy Class:", timeline_pharmacy["Therapy_Class"].isna().sum())
# print("Missing Treatment ID:", timeline_pharmacy["Treatment_ID"].isna().sum())
# print("Missing HCP ID:", timeline_pharmacy["HCP_ID"].isna().sum())

# PATIENT TIMELINE: BUILD ALL-PATIENT TIMELINE

timeline = pd.concat(
    [
        timeline_diagnosis,
        timeline_treatments,
        timeline_encounters,
        timeline_medical,
        timeline_rx,
        timeline_pharmacy
    ],
    ignore_index=True
)

timeline = timeline.sort_values(
    ["Patient_ID", "Event_Date", "Event_Order"]
).reset_index(drop=True)

#print(timeline.columns.to_list())
# PATIENT TIMELINE: LOAD PATIENT MASTER

patient_master = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_master.csv"
)

print("Shape:", patient_master.shape)
print(patient_master.columns.tolist())

# PATIENT TIMELINE: ADD PATIENT DEMOGRAPHICS

patient_demographics = patient_master[
    [
        "Patient_ID",
        "First_Name",
        "Last_Name",
        "Patient_Name",
        "Birth_Date",
        "Sex_at_Birth",
        "Province",
        "Patient_Status"
    ]
].copy()

patient_demographics["Birth_Date"] = pd.to_datetime(
    patient_demographics["Birth_Date"]
)

# PATIENT TIMELINE: STANDARDIZE EVENT DATES

timeline["Event_Date"] = pd.to_datetime(
    timeline["Event_Date"],
    format="mixed"
)

timeline = timeline.merge(
    patient_demographics,
    on="Patient_ID",
    how="left"
)

# print("Shape after merge:", timeline.shape)
# print(timeline.head())
#

# PATIENT TIMELINE: CALCULATE AGE AT EVENT

timeline["Age_at_Event"] = (
    timeline["Event_Date"].dt.year
    - timeline["Birth_Date"].dt.year
    - (
        (
            timeline["Event_Date"].dt.month
            < timeline["Birth_Date"].dt.month
        )
        |
        (
            (timeline["Event_Date"].dt.month == timeline["Birth_Date"].dt.month)
            & (
                timeline["Event_Date"].dt.day
                < timeline["Birth_Date"].dt.day
            )
        )
    ).astype(int)
)

# print(
#     timeline[
#         [
#             "Patient_ID",
#             "Patient_Name",
#             "Birth_Date",
#             "Event_Date",
#             "Age_at_Event",
#             "Sex_at_Birth",
#             "Province"
#         ]
#     ].head(10)
# )
# PATIENT TIMELINE: DEMOGRAPHIC QA

# print("Timeline shape:", timeline.shape)
#
# print(
#     "Missing Patient_Name:",
#     timeline["Patient_Name"].isna().sum()
# )
#
# print(
#     "Missing Birth_Date:",
#     timeline["Birth_Date"].isna().sum()
# )
#
# print(
#     "Missing Sex_at_Birth:",
#     timeline["Sex_at_Birth"].isna().sum()
# )
#
# print(
#     "Missing Province:",
#     timeline["Province"].isna().sum()
# )
#
# print(
#     "Missing Age_at_Event:",
#     timeline["Age_at_Event"].isna().sum()
# )
#
# print(
#     "Negative Age_at_Event:",
#     (timeline["Age_at_Event"] < 0).sum()
# )

# PATIENT TIMELINE: FINAL COLUMN ORDER

final_timeline_columns = [
    "Patient_ID",
    "Patient_Name",
    "First_Name",
    "Last_Name",
    "Birth_Date",
    "Age_at_Event",
    "Sex_at_Birth",
    "Province",
    "Patient_Status",
    "Event_Date",
    "Event_Type",
    "Event_Category",
    "Condition",
    "Therapy_Class",
    "Encounter_ID",
    "Treatment_ID",
    "Rx_Event_ID",
    "HCP_ID",
    "Product_ID",
    "Event_Detail",
    "Event_Order"
]

timeline = timeline[final_timeline_columns]

print("Final shape:", timeline.shape)
print(timeline.columns.tolist())
# PATIENT TIMELINE: SAVE FINAL OUTPUT

timeline_output_path = (
    Project_root
    / "Data"
    / "processed"
    / "patient_longitudinal_timeline.csv"
)

timeline.to_csv(
    timeline_output_path,
    index=False
)

print("Saved:", timeline_output_path)
print("Final shape:", timeline.shape)

