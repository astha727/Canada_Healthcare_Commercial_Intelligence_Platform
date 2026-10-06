from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).resolve().parents[2]

treatment_path = (
    project_root / "Data" / "processed" / "synthetic_patient_treatments.csv"
)

encounter_path = (
    project_root / "Data" / "processed" / "synthetic_patient_encounters.csv"
)

treatments = pd.read_csv(treatment_path)
encounters = pd.read_csv(encounter_path)

treatments["Treatment_Start_Date"] = pd.to_datetime(
    treatments["Treatment_Start_Date"]
)

encounters["Encounter_Date"] = pd.to_datetime(
    encounters["Encounter_Date"]
)


treatment_encounter_candidates = treatments[
    [
        "Treatment_ID",
        "Patient_ID",
        "Condition",
        "Treatment_Start_Date"
    ]
].merge(
    encounters[
        [
            "Encounter_ID",
            "Patient_ID",
            "Encounter_Date",
            "Encounter_Type",
            "Primary_Condition",
            "HCP_ID",
            "Care_Setting"
        ]
    ],
    on="Patient_ID",
    how="inner"
)

treatment_encounter_candidates["Days_From_Encounter_To_Treatment"] = (
    treatment_encounter_candidates["Treatment_Start_Date"]
    - treatment_encounter_candidates["Encounter_Date"]
).dt.days

treatment_encounter_candidates = treatment_encounter_candidates[
    treatment_encounter_candidates["Days_From_Encounter_To_Treatment"].between(0, 30)
].copy()

# print("\nCandidate encounter rows:", len(treatment_encounter_candidates))
# print(
#     "Unique treatment episodes with candidates:",
#     treatment_encounter_candidates["Treatment_ID"].nunique()
# )
#
# print("\nDays from encounter to treatment:")
# print(
#     treatment_encounter_candidates["Days_From_Encounter_To_Treatment"]
#     .describe()
# )

candidate_counts = (
    treatment_encounter_candidates
    .groupby("Treatment_ID")
    .size()
    .value_counts()
    .sort_index()
)

# print("\nNumber of qualifying encounters per treatment:")
# print(candidate_counts)
#
# print(
#     "\nTreatments with multiple qualifying encounters:",
#     (candidate_counts[candidate_counts.index > 1]).sum()
# )


treatment_encounter_candidates["Link_Type"] = np.where(
    treatment_encounter_candidates["Condition"]
    == treatment_encounter_candidates["Primary_Condition"],
    "Strong",
    "Contextual"
)

# print("\nCandidate Link_Type counts:")
# print(
#     treatment_encounter_candidates["Link_Type"]
#     .value_counts()
# )
#
# print("\nCandidate Link_Type percentages:")
# print(
#     treatment_encounter_candidates["Link_Type"]
#     .value_counts(normalize=True)
#     .mul(100)
#     .round(2)
# )


treatment_encounter_candidates = (
    treatment_encounter_candidates
    .sort_values(
        [
            "Treatment_ID",
            "Days_From_Encounter_To_Treatment",
            "Encounter_ID"
        ],
        ascending=[True, True, True]
    )
)

treatment_encounter_linkage = (
    treatment_encounter_candidates
    .drop_duplicates(
        subset="Treatment_ID",
        keep="first"
    )
    .copy()
)

# print("\nFinal linkage rows:", len(treatment_encounter_linkage))
# print(
#     "Unique treatments linked:",
#     treatment_encounter_linkage["Treatment_ID"].nunique()
# )

# print("\nFinal Link_Type counts:")
# print(
#     treatment_encounter_linkage["Link_Type"]
#     .value_counts()
# )
#
# print("\nFinal Link_Type percentages:")
# print(
#     treatment_encounter_linkage["Link_Type"]
#     .value_counts(normalize=True)
#     .mul(100)
#     .round(2)
# )

treatment_encounter_linkage = (
    treatment_encounter_linkage
    .rename(columns={
        "Condition": "Treatment_Condition"
    })
)

print("\nFinal linkage columns:")
print(treatment_encounter_linkage.columns.tolist())

treatment_encounter_linkage = treatment_encounter_linkage[
    [
        "Treatment_ID",
        "Encounter_ID",
        "Patient_ID",
        "Treatment_Condition",
        "Link_Type",
        "Days_From_Encounter_To_Treatment",
        "Encounter_Type",
        "Care_Setting",
        "Primary_Condition",
        "HCP_ID"
    ]
]

# print("\nQA")
#
# print(
#     "Duplicate Treatment_ID:",
#     treatment_encounter_linkage["Treatment_ID"].duplicated().sum()
# )
#
# print(
#     "Duplicate Treatment + Encounter:",
#     treatment_encounter_linkage[
#         ["Treatment_ID", "Encounter_ID"]
#     ].duplicated().sum()
# )
#
# print(
#     "Invalid day gaps:",
#     (
#         ~treatment_encounter_linkage[
#             "Days_From_Encounter_To_Treatment"
#         ].between(0, 30)
#     ).sum()
# )
#
# print(
#     "Strong links with condition mismatch:",
#     (
#         (treatment_encounter_linkage["Link_Type"] == "Strong")
#         &
#         (
#             treatment_encounter_linkage["Treatment_Condition"]
#             != treatment_encounter_linkage["Primary_Condition"]
#         )
#     ).sum()
# )
#
# print(
#     "Contextual links with condition match:",
#     (
#         (treatment_encounter_linkage["Link_Type"] == "Contextual")
#         &
#         (
#             treatment_encounter_linkage["Treatment_Condition"]
#             == treatment_encounter_linkage["Primary_Condition"]
#         )
#     ).sum()
# )
#
# print(
#     "Missing Encounter_ID:",
#     treatment_encounter_linkage["Encounter_ID"].isna().sum()
# )
#
# print(
#     "Missing HCP_ID:",
#     treatment_encounter_linkage["HCP_ID"].isna().sum()
# )

# output_path = (
#     project_root
#     / "Data"
#     / "processed"
#     / "treatment_encounter_linkage.csv"
# )
#
# treatment_encounter_linkage.to_csv(
#     output_path,
#     index=False
# )
#
# print("\nTreatment-encounter linkage:", treatment_encounter_linkage.shape)
# print("Exported:", output_path)

linked_treatments = treatment_encounter_linkage["Treatment_ID"].nunique()
total_treatments = treatments["Treatment_ID"].nunique()
unlinked_treatments = total_treatments - linked_treatments

print("\nTreatment linkage reconciliation")
print("Total treatment episodes:", total_treatments)
print("Linked treatment episodes:", linked_treatments)
print("Unlinked treatment episodes:", unlinked_treatments)
print(
    "Linked percentage:",
    round(linked_treatments / total_treatments * 100, 2)
)
print(
    "Reconciles:",
    linked_treatments + unlinked_treatments == total_treatments
)