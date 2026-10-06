import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

Project_root  = Path(__file__).resolve().parents[2]
# MARKET ACCESS: LOAD PHARMACY CLAIMS

claims_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_pharmacy_claims.csv"
)

pharmacy_claims = load_file(claims_path)

# HCP ANALYTICS: PRESCRIBING ACTIVITY

hcp_activity = (
    pharmacy_claims
    .groupby("HCP_ID")
    .agg(
        Rx_Claims=("Rx_Claim_ID", "count"),
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Products=("Product_ID", "nunique"),
        Plan_Paid=("Plan_Paid_Amount", "sum"),
        Patient_Paid=("Patient_Paid_Amount", "sum")
    )
    .reset_index()
)

# print("HCPs:", len(hcp_activity))
#
# print(
#     hcp_activity
#     .sort_values("Rx_Claims", ascending=False)
#     .head(20)
#     .to_string(index=False)
# )

# HCP ANALYTICS: INITIAL FILLS VS REFILLS

rx_events_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_rx_events.csv"
)

rx_events = load_file(rx_events_path)

pharmacy_claims = pharmacy_claims.merge(
    rx_events[["Rx_Event_ID", "Rx_Event_Type"]],
    on="Rx_Event_ID",
    how="left"
)

# print("Pharmacy claims shape:", pharmacy_claims.shape)
#
# print("\nRx event type:")
# print(pharmacy_claims["Rx_Event_Type"].value_counts())
#
# print("\nMissing Rx event type:", pharmacy_claims["Rx_Event_Type"].isna().sum())

# HCP ANALYTICS: PRESCRIBING ACTIVITY

hcp_prescribing = (
    pharmacy_claims
    .groupby("HCP_ID")
    .agg(
        Total_Rx_Events=("Rx_Event_ID", "count"),
        Initial_Fills=("Rx_Event_Type", lambda x: (x == "Initial Fill").sum()),
        Refills=("Rx_Event_Type", lambda x: (x == "Refill").sum()),
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Products=("Product_ID", "nunique")
    )
    .reset_index()
)

hcp_prescribing["Refill_to_Initial_Ratio"] = (
    hcp_prescribing["Refills"]
    / hcp_prescribing["Initial_Fills"]
)
#
# print(
#     hcp_prescribing
#     .sort_values("Total_Rx_Events", ascending=False)
#     .head(20)
#     .to_string(index=False)
# )

# HCP ANALYTICS: ADD HCP ATTRIBUTES

hcp_master_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_hcp_master.csv"
)

hcp_master = load_file(hcp_master_path)

hcp_prescribing = hcp_prescribing.merge(
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

print("HCP prescribing shape:", hcp_prescribing.shape)

print("\nMissing HCP attributes:")
print(
    hcp_prescribing[
        ["HCP_Name", "Province", "Specialty", "HCP_Type", "Practice_Setting"]
    ]
    .isna()
    .sum()
)

print("\nHCP prescribing examples:")
print(
    hcp_prescribing
    .sort_values("Total_Rx_Events", ascending=False)
    .head(10)
    .to_string(index=False)
)

# HCP ANALYTICS: SAVE OUTPUT

hcp_output_path = (
    Project_root
    / "Data"
    / "processed"
    / "hcp_prescribing_analytics.csv"
)

hcp_prescribing.to_csv(hcp_output_path, index=False)

print("\nSaved:", hcp_output_path)