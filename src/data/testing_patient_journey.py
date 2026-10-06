import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

Project_root  = Path(__file__).resolve().parents[2]

# PATIENT TIMELINE: LOAD CORE TABLES

patient_id = "PAT_00008"

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

diagnoses = load_file(diagnoses_path)
encounters = load_file(encounters_path)
treatments = load_file(treatments_path)
rx_events = load_file(rx_path)

# print("Diagnoses:")
# print(
#     diagnoses[diagnoses["Patient_ID"] == patient_id]
#     .to_string(index=False)
# )
#
# print("\nEncounters:")
# print(
#     encounters[encounters["Patient_ID"] == patient_id]
#     .head(20)
#     .to_string(index=False)
# )
#
# print("\nTreatments:")
# print(
#     treatments[treatments["Patient_ID"] == patient_id]
#     .to_string(index=False)
# )
#
# print("\nRx events:")
# print(
#     rx_events[rx_events["Patient_ID"] == patient_id]
#     .head(20)
#     .to_string(index=False)
# )

# PATIENT TIMELINE: CORE EVENTS

patient_id = "PAT_00008"

# PATIENT TIMELINE: RETAIN EVENT DETAILS

timeline_diagnosis = diagnoses[
    diagnoses["Patient_ID"] == patient_id
].copy()

timeline_diagnosis["Event_Date"] = timeline_diagnosis["Diagnosis_Date"]
timeline_diagnosis["Event_Type"] = "Diagnosis"
timeline_diagnosis["Condition"] = timeline_diagnosis["Condition"]

timeline_diagnosis["Encounter_ID"] = pd.NA
timeline_diagnosis["Treatment_ID"] = pd.NA
timeline_diagnosis["Rx_Event_ID"] = pd.NA
timeline_diagnosis["HCP_ID"] = pd.NA
timeline_diagnosis["Product_ID"] = pd.NA
timeline_diagnosis["Event_Detail"] = timeline_diagnosis["Diagnosis_Status"]


timeline_encounters = encounters[
    encounters["Patient_ID"] == patient_id
].copy()

timeline_encounters["Event_Date"] = timeline_encounters["Encounter_Date"]
timeline_encounters["Event_Type"] = "Encounter"
timeline_encounters["Condition"] = timeline_encounters["Primary_Condition"]
timeline_encounters["Treatment_ID"] = pd.NA
timeline_encounters["Rx_Event_ID"] = pd.NA
timeline_encounters["Product_ID"] = pd.NA
timeline_encounters["Event_Detail"] = timeline_encounters["Encounter_Type"]


timeline_treatments = treatments[
    treatments["Patient_ID"] == patient_id
].copy()

timeline_treatments["Event_Date"] = timeline_treatments["Treatment_Start_Date"]
timeline_treatments["Event_Type"] = "Treatment Start"
timeline_treatments["Condition"] = timeline_treatments["Condition"]
timeline_treatments["Encounter_ID"] = pd.NA
timeline_treatments["Rx_Event_ID"] = pd.NA
timeline_treatments["HCP_ID"] = pd.NA
timeline_treatments["Event_Detail"] = timeline_treatments["Therapy_Class"]


timeline_rx = rx_events[
    rx_events["Patient_ID"] == patient_id
].copy()

timeline_rx["Event_Date"] = timeline_rx["Fill_Date"]
timeline_rx["Event_Type"] = "Rx Event"
timeline_rx["Condition"] = timeline_rx["Therapy_Class"]
timeline_rx["Encounter_ID"] = pd.NA
timeline_rx["Treatment_ID"] = timeline_rx["Treatment_ID"]
timeline_rx["HCP_ID"] = timeline_rx["HCP_ID"]
timeline_rx["Product_ID"] = timeline_rx["Product_ID"]
timeline_rx["Event_Detail"] = timeline_rx["Rx_Event_Type"]


timeline = pd.concat(
    [
        timeline_diagnosis[
            [
                "Patient_ID", "Event_Date", "Event_Type", "Condition",
                "Encounter_ID", "Treatment_ID", "Rx_Event_ID",
                "HCP_ID", "Product_ID", "Event_Detail"
            ]
        ],
        timeline_encounters[
            [
                "Patient_ID", "Event_Date", "Event_Type", "Condition",
                "Encounter_ID", "Treatment_ID", "Rx_Event_ID",
                "HCP_ID", "Product_ID", "Event_Detail"
            ]
        ],
        timeline_treatments[
            [
                "Patient_ID", "Event_Date", "Event_Type", "Condition",
                "Encounter_ID", "Treatment_ID", "Rx_Event_ID",
                "HCP_ID", "Product_ID", "Event_Detail"
            ]
        ],
        timeline_rx[
            [
                "Patient_ID", "Event_Date", "Event_Type", "Condition",
                "Encounter_ID", "Treatment_ID", "Rx_Event_ID",
                "HCP_ID", "Product_ID", "Event_Detail"
            ]
        ]
    ],
    ignore_index=True
)

timeline = timeline.sort_values(
    ["Event_Date", "Event_Type"]
).reset_index(drop=True)

# print(timeline.to_string(index=False))


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

timeline_pharmacy = pharmacy_claims[
    pharmacy_claims["Patient_ID"] == patient_id
].copy()

timeline_pharmacy["Event_Date"] = timeline_pharmacy["Claim_Date"]
timeline_pharmacy["Event_Type"] = "Pharmacy Claim"
timeline_pharmacy["Condition"] = timeline_pharmacy["Product_ID"]
timeline_pharmacy["Encounter_ID"] = pd.NA
timeline_pharmacy["Treatment_ID"] = timeline_pharmacy["Treatment_ID"]
timeline_pharmacy["Rx_Event_ID"] = timeline_pharmacy["Rx_Event_ID"]
timeline_pharmacy["HCP_ID"] = timeline_pharmacy["HCP_ID"]
timeline_pharmacy["Product_ID"] = timeline_pharmacy["Product_ID"]
timeline_pharmacy["Event_Detail"] = timeline_pharmacy["Claim_Status"]


timeline_medical = medical_claims[
    medical_claims["Patient_ID"] == patient_id
].copy()

timeline_medical["Event_Date"] = timeline_medical["Claim_Date"]
timeline_medical["Event_Type"] = "Medical Claim"
timeline_medical["Condition"] = timeline_medical["Primary_Condition"]
timeline_medical["Encounter_ID"] = timeline_medical["Encounter_ID"]
timeline_medical["Treatment_ID"] = pd.NA
timeline_medical["Rx_Event_ID"] = pd.NA
timeline_medical["HCP_ID"] = timeline_medical["HCP_ID"]
timeline_medical["Product_ID"] = pd.NA
timeline_medical["Event_Detail"] = timeline_medical["Service_Type"]


# print("Pharmacy claims:", len(timeline_pharmacy))
# print("Medical claims:", len(timeline_medical))
#
# print("\nPharmacy claim sample:")
# print(
#     timeline_pharmacy[
#         [
#             "Event_Date",
#             "Event_Type",
#             "Treatment_ID",
#             "Rx_Event_ID",
#             "HCP_ID",
#             "Product_ID",
#             "Event_Detail"
#         ]
#     ].head(10).to_string(index=False)
# )
#
# print("\nMedical claim sample:")
# print(
#     timeline_medical[
#         [
#             "Event_Date",
#             "Event_Type",
#             "Encounter_ID",
#             "HCP_ID",
#             "Condition",
#             "Event_Detail"
#         ]
#     ].head(10).to_string(index=False)
# )


# PATIENT TIMELINE: COMBINE ALL EVENTS

timeline_diagnosis["Event_Category"] = "Clinical"
timeline_encounters["Event_Category"] = "Clinical"
timeline_treatments["Event_Category"] = "Treatment"
timeline_rx["Event_Category"] = "Medication"
timeline_pharmacy["Event_Category"] = "Access"
timeline_medical["Event_Category"] = "Healthcare Utilization"

timeline_diagnosis["Event_Date"] = pd.to_datetime(timeline_diagnosis["Event_Date"])
timeline_encounters["Event_Date"] = pd.to_datetime(timeline_encounters["Event_Date"])
timeline_treatments["Event_Date"] = pd.to_datetime(timeline_treatments["Event_Date"])
timeline_rx["Event_Date"] = pd.to_datetime(timeline_rx["Event_Date"])
timeline_pharmacy["Event_Date"] = pd.to_datetime(timeline_pharmacy["Event_Date"])
timeline_medical["Event_Date"] = pd.to_datetime(timeline_medical["Event_Date"])

timeline = pd.concat(
    [
        timeline_diagnosis[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ],
        timeline_encounters[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ],
        timeline_treatments[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ],
        timeline_rx[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ],
        timeline_pharmacy[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ],
        timeline_medical[
            [
                "Patient_ID", "Event_Date", "Event_Type",
                "Condition", "Encounter_ID", "Treatment_ID",
                "Rx_Event_ID", "HCP_ID", "Product_ID",
                "Event_Detail", "Event_Category"
            ]
        ]
    ],
    ignore_index=True
)


timeline = timeline.sort_values(
    ["Event_Date", "Event_Type"]
).reset_index(drop=True)
#
# print("Timeline shape:", timeline.shape)
# print("\nEvents by type:")
# print(timeline["Event_Type"].value_counts())
#
# print("\nComplete timeline:")
# print(timeline.to_string(index=False))

# PATIENT TIMELINE: FIX RX AND PHARMACY FIELDS

timeline_rx["Condition"] = "Stroke"
timeline_rx["Therapy_Class"] = timeline_rx["Event_Detail"]

timeline_pharmacy["Condition"] = "Stroke"
timeline_pharmacy["Therapy_Class"] = "Antithrombotic / secondary prevention"

# print(timeline_rx[[
#     "Event_Date", "Event_Type", "Condition",
#     "Therapy_Class", "Event_Detail"
# ]].head())
#
# print("\n")
#
# print(timeline_pharmacy[[
#     "Event_Date", "Event_Type", "Condition",
#     "Therapy_Class", "Event_Detail"
# ]].head())

# PATIENT TIMELINE: REBUILD FINAL TIMELINE

# Add therapy class where it does not apply
timeline_diagnosis["Therapy_Class"] = pd.NA
timeline_encounters["Therapy_Class"] = pd.NA
timeline_treatments["Therapy_Class"] = timeline_treatments["Event_Detail"]
timeline_medical["Therapy_Class"] = pd.NA

# Make sure Condition is correct
timeline_treatments["Condition"] = "Stroke"
timeline_medical["Condition"] = "Stroke"
timeline_encounters["Condition"] = "Stroke"

# Define event order
event_order = {
    "Diagnosis": 1,
    "Treatment Start": 2,
    "Encounter": 3,
    "Medical Claim": 4,
    "Rx Event": 5,
    "Pharmacy Claim": 6
}

# Combine
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

# Assign event order
timeline["Event_Order"] = timeline["Event_Type"].map(event_order)

# Sort chronologically, then logically within the same date
timeline = timeline.sort_values(
    ["Event_Date", "Event_Order"]
).reset_index(drop=True)

# print("Timeline shape:", timeline.shape)
#
# print("\nEvents by type:")
# print(timeline["Event_Type"].value_counts())
#
# print("\nFinal timeline:")
# print(
#     timeline[
#         [
#             "Patient_ID",
#             "Event_Date",
#             "Event_Type",
#             "Event_Category",
#             "Condition",
#             "Therapy_Class",
#             "Encounter_ID",
#             "Treatment_ID",
#             "Rx_Event_ID",
#             "HCP_ID",
#             "Product_ID",
#             "Event_Detail",
#             "Event_Order"
#         ]
#     ].to_string(index=False)
# )

# PATIENT TIMELINE: CLEAN FINAL SCHEMA

timeline_rx["Therapy_Class"] = "Antithrombotic / secondary prevention"
timeline_pharmacy["Therapy_Class"] = "Antithrombotic / secondary prevention"

timeline = timeline[
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
].copy()

print("Final timeline shape:", timeline.shape)

print("\nColumns:")
print(timeline.columns.tolist())

print("\nRx events:")
print(
    timeline[timeline["Event_Type"] == "Rx Event"][
        ["Event_Date", "Condition", "Therapy_Class", "Event_Detail"]
    ].head()
)

print("\nEvent counts:")
print(timeline["Event_Type"].value_counts())