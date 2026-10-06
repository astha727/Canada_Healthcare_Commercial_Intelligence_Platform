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

# print("Pharmacy claims shape:", pharmacy_claims.shape)
#
# print("\nClaim status:")
# print(pharmacy_claims["Claim_Status"].value_counts())
#
# print("\nClaim fields:")
# print(pharmacy_claims.columns.tolist())

# MARKET ACCESS: FORMULARY SUMMARY

formulary_summary = (
    pharmacy_claims
    .groupby("Formulary_Match")
    .agg(
        Rx_Claims=("Rx_Claim_ID", "count"),
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Products=("Product_ID", "nunique")
    )
    .reset_index()
)

formulary_summary["Claim_Share"] = (
    formulary_summary["Rx_Claims"]
    / formulary_summary["Rx_Claims"].sum()
)

# print(formulary_summary.to_string(index=False))

# MARKET ACCESS: BENEFIT STATUS

benefit_summary = (
    pharmacy_claims[
        pharmacy_claims["Formulary_Match"] == True
    ]
    .groupby("Benefit_status")
    .agg(
        Rx_Claims=("Rx_Claim_ID", "count"),
        Unique_Patients=("Patient_ID", "nunique"),
        Unique_Products=("Product_ID", "nunique")
    )
    .reset_index()
)

benefit_summary["Claim_Share"] = (
    benefit_summary["Rx_Claims"]
    / benefit_summary["Rx_Claims"].sum()
)

# print(benefit_summary.to_string(index=False))

# MARKET ACCESS: PROVINCIAL SUMMARY

provincial_access = (
    pharmacy_claims
    .groupby("Province")
    .agg(
        Rx_Claims=("Rx_Claim_ID", "count"),
        Formulary_Matched=("Formulary_Match", "sum"),
        Paid_Claims=("Claim_Status", lambda x: (x == "Paid").sum()),
        Patient_Paid=("Patient_Paid_Amount", "sum"),
        Plan_Paid=("Plan_Paid_Amount", "sum")
    )
    .reset_index()
)

provincial_access["Formulary_Match_Rate"] = (
    provincial_access["Formulary_Matched"]
    / provincial_access["Rx_Claims"]
)

provincial_access["Paid_Claim_Rate"] = (
    provincial_access["Paid_Claims"]
    / provincial_access["Rx_Claims"]
)

print(
    provincial_access
    .sort_values("Formulary_Match_Rate")
    .to_string(index=False)
)