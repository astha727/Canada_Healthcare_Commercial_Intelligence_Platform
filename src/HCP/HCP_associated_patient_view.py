import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path
import numpy as np

Project_root  = Path(__file__).resolve().parents[2]



# HCP ANALYTICS: LOAD PATIENT JOURNEY DATA

diagnoses = pd.read_csv(
    Project_root / "Data" / "processed" / "synthetic_patient_diagnoses.csv"
)

treatments = pd.read_csv(
    Project_root / "Data" / "processed" / "synthetic_patient_treatments.csv"
)

rx_events = pd.read_csv(
    Project_root / "Data" / "processed" / "synthetic_patient_rx_events.csv"
)

# print("Diagnoses:", diagnoses.shape)
# print("Treatments:", treatments.shape)
# print("Rx events:", rx_events.shape)
# print(diagnoses[["Patient_ID", "Condition"]].drop_duplicates().shape)
#
# print(treatments[["Patient_ID", "Condition"]].drop_duplicates().shape)
#
# print(rx_events[["Patient_ID", "Treatment_ID"]].drop_duplicates().shape)

# HCP ANALYTICS: PATIENT-CONDITION BASE

patient_condition = (
    diagnoses[
        ["Patient_ID", "Condition", "Diagnosis_Date"]
    ]
    .drop_duplicates()
    .copy()
)

# print("Patient-condition shape:", patient_condition.shape)
# print(patient_condition.head())

# HCP ANALYTICS: ADD TREATMENT INFORMATION

patient_condition = patient_condition.merge(
    treatments[
        [
            "Treatment_ID",
            "Patient_ID",
            "Condition",
            "Therapy_Class",
            "Treatment_Start_Date",
            "Treatment_End_Date",
            "Treatment_Status"
        ]
    ],
    on=["Patient_ID", "Condition"],
    how="left"
)

# print("Shape:", patient_condition.shape)
# print(patient_condition.to_string())

# HCP ANALYTICS: CHECK TREATMENT COVERAGE
#
# print(
#     patient_condition["Treatment_Status"]
#     .value_counts(dropna=False)
# )

# HCP ANALYTICS: BUILD TREATMENT-HCP LOOKUP

treatment_hcp = (
    rx_events[rx_events["Rx_Event_Type"] == "Initial Fill"]
    [
        [
            "Treatment_ID",
            "Patient_ID",
            "HCP_ID"
        ]
    ]
    .drop_duplicates()
)

# print("Treatment-HCP shape:", treatment_hcp.shape)
# print(treatment_hcp.head())
# print(
#     treatment_hcp
#     .groupby("Treatment_ID")["HCP_ID"]
#     .nunique()
#     .value_counts()
# )

# HCP ANALYTICS: ATTACH PRESCRIBING HCP

patient_condition = patient_condition.merge(
    treatment_hcp[
        ["Treatment_ID", "HCP_ID"]
    ],
    on="Treatment_ID",
    how="left"
)

# print("Shape:", patient_condition.shape)
# print(patient_condition.head())
# print(
#     patient_condition["HCP_ID"]
#     .isna()
#     .value_counts()
# )

# HCP ANALYTICS: ASSIGN PATIENT STAGE

patient_condition["Analytical_Stage"] = np.select(
    [
        patient_condition["Treatment_Status"].isna(),
        patient_condition["Treatment_Status"] == "Active",
        patient_condition["Treatment_Status"] == "Discontinued"
    ],
    [
        "Diagnosed - No Observed Treatment",
        "Active Treatment",
        "Discontinued Treatment"
    ],
    default="Unknown"
)
#
# print(
#     patient_condition["Analytical_Stage"]
#     .value_counts()
# )

# HCP ANALYTICS: HCP PATIENT-STAGE PORTFOLIO

hcp_patient_stage = (
    patient_condition[
        patient_condition["HCP_ID"].notna()
    ]
    .groupby(["HCP_ID", "Analytical_Stage"])
    .agg(
        Patient_Condition_Count=("Patient_ID", "count"),
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Conditions=("Condition", "nunique")
    )
    .reset_index()
)
#
# print("Shape:", hcp_patient_stage.shape)
# print(hcp_patient_stage.head(10))
# # HCP ANALYTICS: STAGE HCP COVERAGE
#
# print(
#     hcp_patient_stage
#     .groupby("Analytical_Stage")["HCP_ID"]
#     .nunique()
# )
# HCP ANALYTICS: CHECK HCP-PATIENT-CONDITION GRAIN

# grain_check = (
#     patient_condition[
#         patient_condition["HCP_ID"].notna()
#     ]
#     .groupby(["HCP_ID", "Patient_ID", "Condition"])
#     .size()
# )

# print("Duplicate HCP-patient-condition combinations:")
# print((grain_check > 1).sum())

# HCP ANALYTICS: ADD HCP ATTRIBUTES

hcp_master = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "synthetic_hcp_master.csv"
)

# HCP ANALYTICS: HCP PATIENT PORTFOLIO

hcp_patient_portfolio = (
    patient_condition[
        patient_condition["HCP_ID"].notna()
    ][
        [
            "HCP_ID",
            "Patient_ID",
            "Condition",
            "Diagnosis_Date",
            "Treatment_ID",
            "Therapy_Class",
            "Treatment_Start_Date",
            "Treatment_End_Date",
            "Treatment_Status",
            "Analytical_Stage"
        ]
    ]
    .copy()
)

hcp_patient_portfolio = hcp_patient_portfolio.merge(
    hcp_master[
        [
            "HCP_ID",
            "HCP_Name",
            "Province",
            "Specialty",
            "HCP_Type",
            "Practice_Setting"
        ]
    ],
    on="HCP_ID",
    how="left"
)
#
# print("Shape:", hcp_patient_portfolio.shape)
# print(hcp_patient_portfolio.head())

# HCP ANALYTICS: SUMMARIZE RX ACTIVITY BY TREATMENT

rx_activity = (
    rx_events
    .groupby("Treatment_ID")
    .agg(
        Rx_Event_Count=("Rx_Event_ID", "count"),
        Initial_Fill_Count=(
            "Rx_Event_Type",
            lambda x: (x == "Initial Fill").sum()
        ),
        Refill_Count=(
            "Rx_Event_Type",
            lambda x: (x == "Refill").sum()
        ),
        Last_Rx_Date=("Fill_Date", "max")
    )
    .reset_index()
)
#
# print("Shape:", rx_activity.shape)
# print(rx_activity.head())

# HCP ANALYTICS: ADD RX ACTIVITY TO HCP PORTFOLIO

hcp_patient_portfolio = hcp_patient_portfolio.merge(
    rx_activity,
    on="Treatment_ID",
    how="left"
)

# print("Shape:", hcp_patient_portfolio.shape)
# print(hcp_patient_portfolio.head())
#
# # HCP ANALYTICS: VALIDATE RX ACTIVITY
#
# print(
#     hcp_patient_portfolio[
#         [
#             "Rx_Event_Count",
#             "Initial_Fill_Count",
#             "Refill_Count",
#             "Last_Rx_Date"
#         ]
#     ]
#     .isna()
#     .sum()
# )

# HCP ANALYTICS: DEFINE HCP ROLES

hcp_patient_portfolio = hcp_patient_portfolio.rename(
    columns={"HCP_ID": "Prescribing_HCP_ID"}
)

# print(
#     hcp_patient_portfolio[
#         ["Prescribing_HCP_ID", "Patient_ID", "Condition"]
#     ].head()
# )
# HCP ANALYTICS: LOAD TREATMENT-ENCOUNTER LINKAGE

treatment_encounter = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "treatment_encounter_linkage.csv"
)
#
# print("Shape:", treatment_encounter.shape)
# print(treatment_encounter.head())

# HCP ANALYTICS: DEFINE ENCOUNTER HCP

treatment_encounter = treatment_encounter.rename(
    columns={"HCP_ID": "Encounter_HCP_ID"}
)

# print(
#     treatment_encounter[
#         ["Treatment_ID", "Encounter_ID", "Encounter_HCP_ID"]
#     ].head()
# )
# print(treatment_encounter.columns.tolist())

# HCP ANALYTICS: ADD OBSERVED ENCOUNTER INFORMATION

hcp_patient_portfolio = hcp_patient_portfolio.merge(
    treatment_encounter[
        [
            "Treatment_ID",
            "Encounter_ID",
            "Encounter_HCP_ID",
            "Link_Type",
            "Encounter_Type",
            "Care_Setting",
            "Days_From_Encounter_To_Treatment"
        ]
    ],
    on="Treatment_ID",
    how="left"
)

# print("Shape:", hcp_patient_portfolio.shape)
# print(hcp_patient_portfolio.head())
# # HCP ANALYTICS: CHECK OBSERVED ENCOUNTER LINKAGE
#
# print(
#     hcp_patient_portfolio["Encounter_ID"]
#     .notna()
#     .value_counts()
# )

# HCP ANALYTICS: DEFINE HCP ASSOCIATION TYPE

hcp_patient_portfolio["HCP_Association_Type"] = np.where(
    hcp_patient_portfolio["Encounter_ID"].notna(),
    "Observed Encounter Linked",
    "Synthetic Prescribing Assignment"
)

# print(
#     hcp_patient_portfolio["HCP_Association_Type"]
#     .value_counts()
# )
# print(hcp_patient_portfolio.columns.tolist())

# HCP ANALYTICS: BUILD HCP PORTFOLIO SUMMARY

hcp_portfolio_summary = (
    hcp_patient_portfolio
    .groupby(
        [
            "Prescribing_HCP_ID",
            "HCP_Name",
            "Province",
            "Specialty",
            "HCP_Type",
            "Practice_Setting"
        ]
    )
    .agg(
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Conditions=("Condition", "nunique"),
        Treatment_Episodes=("Treatment_ID", "nunique"),
        Active_Treatment_Episodes=(
            "Treatment_Status",
            lambda x: (x == "Active").sum()
        ),
        Discontinued_Treatment_Episodes=(
            "Treatment_Status",
            lambda x: (x == "Discontinued").sum()
        ),
        Total_Rx_Events=("Rx_Event_Count", "sum"),
        Initial_Fills=("Initial_Fill_Count", "sum"),
        Refills=("Refill_Count", "sum"),
        Observed_Encounter_Linked=(
            "Encounter_ID",
            lambda x: x.notna().sum()
        ),
        Synthetic_Prescribing_Assignments=(
            "HCP_Association_Type",
            lambda x: (x == "Synthetic Prescribing Assignment").sum()
        )
    )
    .reset_index()
)

# print("Shape:", hcp_portfolio_summary.shape)
# print(hcp_portfolio_summary.head())

# HCP ANALYTICS: CALCULATE PORTFOLIO METRICS

hcp_portfolio_summary["Active_Treatment_Share"] = (
    hcp_portfolio_summary["Active_Treatment_Episodes"]
    / hcp_portfolio_summary["Treatment_Episodes"]
)

hcp_portfolio_summary["Discontinued_Treatment_Share"] = (
    hcp_portfolio_summary["Discontinued_Treatment_Episodes"]
    / hcp_portfolio_summary["Treatment_Episodes"]
)

hcp_portfolio_summary["Observed_Encounter_Link_Rate"] = (
    hcp_portfolio_summary["Observed_Encounter_Linked"]
    / hcp_portfolio_summary["Treatment_Episodes"]
)

# print(
#     hcp_portfolio_summary[
#         [
#             "Prescribing_HCP_ID",
#             "HCP_Name",
#             "Unique_Patients",
#             "Unique_Conditions",
#             "Treatment_Episodes",
#             "Active_Treatment_Share",
#             "Discontinued_Treatment_Share",
#             "Observed_Encounter_Link_Rate"
#         ]
#     ].head(10)
# )
# print(
#     hcp_portfolio_summary[
#         [
#             "Active_Treatment_Share",
#             "Discontinued_Treatment_Share",
#             "Observed_Encounter_Link_Rate"
#         ]
#     ].describe()
# )

# HCP ANALYTICS: HCP CONDITION PORTFOLIO

hcp_condition_portfolio = (
    hcp_patient_portfolio
    .groupby(
        [
            "Prescribing_HCP_ID",
            "HCP_Name",
            "Province",
            "Specialty",
            "HCP_Type",
            "Practice_Setting",
            "Condition",
            "Therapy_Class"
        ]
    )
    .agg(
        Unique_Patients=("Patient_ID", "nunique"),
        Treatment_Episodes=("Treatment_ID", "nunique"),
        Active_Treatment_Episodes=(
            "Treatment_Status",
            lambda x: (x == "Active").sum()
        ),
        Discontinued_Treatment_Episodes=(
            "Treatment_Status",
            lambda x: (x == "Discontinued").sum()
        ),
        Rx_Events=("Rx_Event_Count", "sum"),
        Initial_Fills=("Initial_Fill_Count", "sum"),
        Refills=("Refill_Count", "sum")
    )
    .reset_index()
)
#
# print("Shape:", hcp_condition_portfolio.shape)
# print(hcp_condition_portfolio.head(10))

# HCP ANALYTICS: HCP CONDITION STAGE VIEW

# HCP ANALYTICS: CONDITION-STAGE WITH NRx AND TRx

hcp_condition_stage = (
    hcp_patient_portfolio
    .groupby(
        [
            "Prescribing_HCP_ID",
            "HCP_Name",
            "Province",
            "Specialty",
            "Condition",
            "Therapy_Class",
            "Analytical_Stage"
        ]
    )
    .agg(
        Unique_Patients=("Patient_ID", "nunique"),
        Treatment_Episodes=("Treatment_ID", "nunique"),
        NRx_Proxy=("Initial_Fill_Count", "sum"),
        Refills=("Refill_Count", "sum"),
        TRx_Proxy=("Rx_Event_Count", "sum")
    )
    .reset_index()
)

print("Shape:", hcp_condition_stage.shape)
print(hcp_condition_stage.head(10))

#
# print("Shape:", hcp_condition_stage.shape)
# print(hcp_condition_stage.head(10))
# print(
#     hcp_condition_stage["Analytical_Stage"]
#     .value_counts()
# )

# HCP ANALYTICS: FINAL COMMERCIAL METRICS

hcp_condition_stage = hcp_condition_stage.rename(
    columns={
        "Rx_Events": "TRx_Proxy",
        "Initial_Fills": "NRx_Proxy"
    }
)

print(hcp_condition_stage.columns.tolist())
print(hcp_condition_stage.head(10))
# HCP ANALYTICS: NRx/TRx QA

hcp_condition_stage["TRx_Check"] = (
    hcp_condition_stage["NRx_Proxy"]
    + hcp_condition_stage["Refills"]
)

print(
    "TRx mismatch:",
    (
        hcp_condition_stage["TRx_Proxy"]
        != hcp_condition_stage["TRx_Check"]
    ).sum()
)

print(
    "Missing NRx:",
    hcp_condition_stage["NRx_Proxy"].isna().sum()
)

print(
    "Missing TRx:",
    hcp_condition_stage["TRx_Proxy"].isna().sum()
)

print(
    "Missing Refills:",
    hcp_condition_stage["Refills"].isna().sum()
)
hcp_condition_stage = hcp_condition_stage.drop(
    columns=["TRx_Check"]
)
# HCP ANALYTICS: SAVE FINAL CONDITION-STAGE OUTPUT

hcp_condition_stage_path = (
    Project_root
    / "Data"
    / "processed"
    / "hcp_condition_stage_analytics.csv"
)

hcp_condition_stage.to_csv(
    hcp_condition_stage_path,
    index=False
)

print("Saved:", hcp_condition_stage_path)
print("Final shape:", hcp_condition_stage.shape)