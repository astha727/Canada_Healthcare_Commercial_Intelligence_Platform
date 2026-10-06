import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path

Project_root  = Path(__file__).resolve().parents[2]
# COMPETITIVE ANALYTICS: LOAD SOURCE TABLES

product_master = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "drug_product_master.csv"
)

therapy_mapping = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "therapy_product_mapping.csv"
)

treatments = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_treatments.csv"
)

rx_events = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "synthetic_patient_rx_events.csv"
)

pharmacy_claims = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "synthetic_pharmacy_claims.csv"
)

# print("Product master:", product_master.shape)
# print("Therapy mapping:", therapy_mapping.shape)
# print("Treatments:", treatments.shape)
# print("Rx events:", rx_events.shape)
# print("Pharmacy claims:", pharmacy_claims.shape)

# COMPETITIVE ANALYTICS: TREATMENT ACTIVITY

product_treatment = (
    treatments
    .groupby("Product_ID")
    .agg(
        Treatment_Episodes=("Treatment_ID", "nunique"),
        Unique_Patients=("Patient_ID", "nunique"),
        Active_Treatments=(
            "Treatment_Status",
            lambda x: (x == "Active").sum()
        ),
        Discontinued_Treatments=(
            "Treatment_Status",
            lambda x: (x == "Discontinued").sum()
        )
    )
    .reset_index()
)
#
# print("Shape:", product_treatment.shape)
# print(product_treatment.head())


# COMPETITIVE ANALYTICS: Rx ACTIVITY

product_rx = (
    rx_events
    .groupby("Product_ID")
    .agg(
        NRx_Proxy=(
            "Rx_Event_Type",
            lambda x: (x == "Initial Fill").sum()
        ),
        Refills=(
            "Rx_Event_Type",
            lambda x: (x == "Refill").sum()
        ),
        TRx_Proxy=("Rx_Event_ID", "count"),
        Rx_Unique_Patients=("Patient_ID", "nunique")
    )
    .reset_index()
)

# print("Shape:", product_rx.shape)
# print(product_rx.head())

# COMPETITIVE ANALYTICS: ACCESS ACTIVITY

product_access = (
    pharmacy_claims
    .groupby("Product_ID")
    .agg(
        Pharmacy_Claims=("Rx_Claim_ID", "count"),
        Paid_Claims=(
            "Claim_Status",
            lambda x: (x == "Paid").sum()
        ),
        Rejected_Claims=(
            "Claim_Status",
            lambda x: (x == "Rejected").sum()
        ),
        Formulary_Matched_Claims=(
            "Formulary_Match",
            "sum"
        ),
        Plan_Paid_Amount=("Plan_Paid_Amount", "sum"),
        Patient_Paid_Amount=("Patient_Paid_Amount", "sum")
    )
    .reset_index()
)

product_access["Formulary_Match_Rate"] = (
    product_access["Formulary_Matched_Claims"]
    / product_access["Pharmacy_Claims"]
)

product_access["Paid_Claim_Rate"] = (
    product_access["Paid_Claims"]
    / product_access["Pharmacy_Claims"]
)

# print("Shape:", product_access.shape)
# print(product_access.head())

# COMPETITIVE ANALYTICS: INSPECT THERAPY MAPPING

# print(therapy_mapping.columns.tolist())
# print(therapy_mapping.head())

# COMPETITIVE ANALYTICS: BUILD FINAL PRODUCT VIEW

product_analytics = (
    therapy_mapping[
        [
            "Therapy_Class",
            "Product_ID",
            "DIN",
            "Brand_Name",
            "AI_Group_No"
        ]
    ]
    .merge(
        product_treatment,
        on="Product_ID",
        how="left"
    )
    .merge(
        product_rx,
        on="Product_ID",
        how="left"
    )
    .merge(
        product_access,
        on="Product_ID",
        how="left"
    )
)

def derive_competitor(brand_name):
    if pd.isna(brand_name):
        return "Other / Unknown"

    brand = str(brand_name).strip().upper()

    competitor_prefixes = {
        "TEVA-": "Teva",
        "TEVA ": "Teva",
        "APO-": "Apotex",
        "APO ": "Apotex",
        "MYLAN-": "Mylan",
        "MYLAN ": "Mylan",
        "PMS-": "Pharmascience",
        "PMS ": "Pharmascience",
        "RIVA-": "Riva",
        "RIVA ": "Riva",
        "TARO-": "Taro",
        "TARO ": "Taro",
    }

    for prefix, competitor in competitor_prefixes.items():
        if brand.startswith(prefix):
            return competitor

    return "Other / Unknown"


product_analytics["Competitor"] = (
    product_analytics["Brand_Name"].apply(derive_competitor)
)

# COMPETITIVE ANALYTICS: DERIVE SYNTHETIC COMPETITOR

def derive_competitor(brand_name):
    if pd.isna(brand_name):
        return "Unknown"

    brand = str(brand_name).strip().upper()

    competitor_prefixes = {
        "TEVA-": "Teva",
        "TEVA ": "Teva",
        "APO-": "Apotex",
        "APO ": "Apotex",
        "MYLAN-": "Mylan",
        "MYLAN ": "Mylan",
        "PMS-": "Pharmascience",
        "PMS ": "Pharmascience",
        "RIVA-": "Riva",
        "RIVA ": "Riva",
        "TARO-": "Taro",
        "TARO ": "Taro",
    }

    for prefix, competitor in competitor_prefixes.items():
        if brand.startswith(prefix):
            return competitor

    return "Other / Unknown"


product_analytics["Competitor"] = (
    product_analytics["Brand_Name"]
    .apply(derive_competitor)
)

print("\nCompetitor distribution:")
print(
    product_analytics["Competitor"]
    .value_counts()
)

print(
    "\nProducts without competitor attribution:",
    (
        product_analytics["Competitor"]
        == "Other / Unknown"
    ).sum()
)

print(
    product_analytics.loc[
        product_analytics["Competitor"] == "Other / Unknown",
        ["Product_ID", "Brand_Name", "Therapy_Class"]
    ].to_string(index=False)
)
# print("Shape:", product_analytics.shape)
# print(product_analytics.head(10))
# print(product_analytics.columns.tolist())
# # COMPETITIVE ANALYTICS: FINAL QA
#
# print("Rows:", len(product_analytics))
# print("Unique products:", product_analytics["Product_ID"].nunique())
#
# print(
#     "Missing therapy class:",
#     product_analytics["Therapy_Class"].isna().sum()
# )
#
# print(
#     "Missing treatment activity:",
#     product_analytics["Treatment_Episodes"].isna().sum()
# )
#
# print(
#     "Missing TRx:",
#     product_analytics["TRx_Proxy"].isna().sum()
# )
#
# print(
#     "Missing access activity:",
#     product_analytics["Pharmacy_Claims"].isna().sum()
# )
#
# print(
#     "TRx mismatch:",
#     (
#         product_analytics["TRx_Proxy"]
#         != (
#             product_analytics["NRx_Proxy"]
#             + product_analytics["Refills"]
#         )
#     ).sum()
# )
#


# COMPETITIVE ANALYTICS: SAVE FINAL OUTPUT

product_output_path = (
     Project_root
     / "Data"
     / "processed"
     / "competitive_product_analytics.csv"
)

product_analytics.to_csv(
     product_output_path,
     index=False
)
#
print("Saved:", product_output_path)
print("Final shape:", product_analytics.shape)