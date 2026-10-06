import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

Project_root  = Path(__file__).resolve().parents[2]

treatment_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_treatments.csv"
)

treatments = load_file(treatment_path)

# print("Treatments shape:", treatments.shape)
#
# print("\nTreatment status:")
# print(treatments["Treatment_Status"].value_counts())
#
# print("\nObserved treatment days:")
# print(
#     treatments["Observed_Treatment_Days"].describe()
# )
#
# print("\nActive treatment examples:")
# print(
#     treatments[
#         treatments["Treatment_Status"] == "Active"
#     ][
#         [
#             "Treatment_ID",
#             "Patient_ID",
#             "Condition",
#             "Treatment_Start_Date",
#             "Treatment_End_Date",
#             "Treatment_Status",
#             "Observed_Treatment_Days"
#         ]
#     ].head(10).to_string(index=False)
# )

# PERSISTENCE: EVENT AND OBSERVATION TIME

treatments["Persistence_Days"] = treatments["Observed_Treatment_Days"]

treatments["Persistence_Event"] = (
    treatments["Treatment_Status"] == "Discontinued"
).astype(int)

print(
    treatments[
        [
            "Treatment_ID",
            "Treatment_Status",
            "Observed_Treatment_Days",
            "Persistence_Days",
            "Persistence_Event"
        ]
    ].head(10).to_string(index=False)
)

# print("\nPersistence event counts:")
# print(treatments["Persistence_Event"].value_counts())

# PERSISTENCE: SUMMARY BY THERAPY CLASS

persistence_summary = (
    treatments
    .groupby("Therapy_Class")
    .agg(
        Treatment_Count=("Treatment_ID", "count"),
        Median_Persistence_Days=("Persistence_Days", "median"),
        Mean_Persistence_Days=("Persistence_Days", "mean"),
        Discontinued_Count=("Persistence_Event", "sum")
    )
    .reset_index()
)

persistence_summary["Discontinuation_Rate"] = (
    persistence_summary["Discontinued_Count"]
    / persistence_summary["Treatment_Count"]
)

# print(
#     persistence_summary
#     .sort_values("Median_Persistence_Days")
#     .to_string(index=False)
# )

# SWITCHING: TREATMENT EPISODES PER PATIENT AND CONDITION

treatment_sequence = (
    treatments
    .sort_values(["Patient_ID", "Condition", "Treatment_Start_Date"])
    .groupby(["Patient_ID", "Condition"])
    .size()
    .reset_index(name="Treatment_Episode_Count")
)

print("Patient-condition combinations:", len(treatment_sequence))

print("\nTreatment episode count:")
print(
    treatment_sequence["Treatment_Episode_Count"]
    .value_counts()
    .sort_index()
)