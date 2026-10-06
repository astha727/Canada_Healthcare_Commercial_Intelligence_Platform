import pandas as pd
from pathlib import Path
from src.data.data_loader import load_file
import numpy as np


Project_root = Path(__file__).resolve().parents[2]
rx_path = Project_root / "Data" / "processed" / "synthetic_patient_rx_events.csv"

rx = load_file(rx_path)

# print("Rx Events shape:", rx.shape)
# print("\nColumns:")
# print(rx.columns.tolist())

patient_path = Project_root / "Data" / "processed" / "synthetic_patient_master.csv"

patients = load_file(patient_path)

rx = rx.merge(
    patients[["Patient_ID", "Province"]],
    on="Patient_ID",
    how="left"
)

rx_province_counts = rx["Province"].value_counts().sort_index()

# print("\nRx Events by province:")
# print(rx_province_counts)
#
# print("\nMissing province:", rx["Province"].isna().sum())

pharmacy_counts = (
    rx_province_counts
    .apply(lambda x: max(2, min(20, round(x / 5000))))
)

# print("\nSynthetic pharmacies by province:")
# print(pharmacy_counts)
#
# print(
#     "\nTotal synthetic pharmacies:",
#     pharmacy_counts.sum()
# )

province_codes = {
    "Alberta": "AB",
    "British Columbia": "BC",
    "Manitoba": "MB",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Northwest Territories": "NT",
    "Nova Scotia": "NS",
    "Nunavut": "NU",
    "Ontario": "ON",
    "Prince Edward Island": "PE",
    "Quebec": "QC",
    "Saskatchewan": "SK",
    "Yukon": "YT"
}

pharmacies = []

for province, count in pharmacy_counts.items():

    code = province_codes[province]

    for i in range(1, count + 1):

        pharmacies.append({
            "Pharmacy_ID": f"PHARM_{code}_{i:03d}",
            "Province": province
        })

pharmacy_master = pd.DataFrame(pharmacies)

# print("\nPharmacy Master shape:", pharmacy_master.shape)
#
# print("\nFirst 10 pharmacies:")
# print(pharmacy_master.head(10))
#
# print("\nPharmacies by province:")
# print(pharmacy_master["Province"].value_counts().sort_index())



np.random.seed(42)

pharmacy_types = np.random.choice(
    ["Community Pharmacy", "Hospital Pharmacy", "Specialty Pharmacy"],
    size=len(pharmacy_master),
    p=[0.70, 0.20, 0.10]
)

pharmacy_master["Pharmacy_Type"] = pharmacy_types

# print("\nPharmacy type distribution:")
# print(pharmacy_master["Pharmacy_Type"].value_counts())
#
# print("\nPharmacy Master:")
# print(pharmacy_master.head(10))

pharmacy_output_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_pharmacy_master.csv"
)


pharmacy_master.to_csv(
    pharmacy_output_path,
    index=False
)

# print(f"\nSaved Pharmacy Master to: {pharmacy_output_path}")
#
# print("\nQA checks:")
#
# print(
#     "Missing Pharmacy_ID:",
#     pharmacy_master["Pharmacy_ID"].isna().sum()
# )
#
# print(
#     "Duplicate Pharmacy_ID:",
#     pharmacy_master["Pharmacy_ID"].duplicated().sum()
# )
#
# print(
#     "Missing Province:",
#     pharmacy_master["Province"].isna().sum()
# )
#
# print(
#     "Missing Pharmacy_Type:",
#     pharmacy_master["Pharmacy_Type"].isna().sum()
# )

np.random.seed(42)

pharmacy_lookup = (
    pharmacy_master
    .groupby("Province")["Pharmacy_ID"]
    .apply(list)
    .to_dict()
)

rx["Pharmacy_ID"] = rx["Province"].map(
    lambda province: np.random.choice(pharmacy_lookup[province])
)
#
# print("\nRx Events with Pharmacy_ID:")
# print(
#     rx[
#         [
#             "Rx_Event_ID",
#             "Patient_ID",
#             "Province",
#             "Pharmacy_ID"
#         ]
#     ].head(10)
# )
#
# print(
#     "\nMissing Pharmacy_ID:",
#     rx["Pharmacy_ID"].isna().sum()
# )

pharmacy_province_check = rx.merge(
    pharmacy_master[["Pharmacy_ID", "Province"]].rename(
        columns={"Province": "Pharmacy_Province"}
    ),
    on="Pharmacy_ID",
    how="left"
)

# print("\nPharmacy province mismatches:")
# print(
#     (
#         pharmacy_province_check["Province"]
#         != pharmacy_province_check["Pharmacy_Province"]
#     ).sum()
# )
#
# print(
#     "Missing Pharmacy records:",
#     pharmacy_province_check["Pharmacy_Province"].isna().sum()
# )


#creating claims
pharmacy_claims = rx[
    [
        "Rx_Event_ID",
        "Treatment_ID",
        "Patient_ID",
        "Product_ID",
        "HCP_ID",
        "Pharmacy_ID",
        "Province",
        "Fill_Date",
        "Days_Supply"
    ]
].copy()

pharmacy_claims = pharmacy_claims.rename(
    columns={
        "Fill_Date": "Claim_Date"
    }
)

pharmacy_claims.insert(
    0,
    "Rx_Claim_ID",
    [
        f"RXCLM_{i:06d}"
        for i in range(1, len(pharmacy_claims) + 1)
    ]
)

# print("Pharmacy Claims shape:", pharmacy_claims.shape)
#
# print("\nColumns:")
# print(pharmacy_claims.columns.tolist())
#
# print("\nFirst 5 claims:")
# print(pharmacy_claims.head())



coverage_lookup = load_file(
    Project_root / "Data" / "processed" / "synthetic_patient_coverage.csv"
)

pharmacy_claims = pharmacy_claims.merge(
    coverage_lookup[
        [
            "Patient_ID",
            "Synthetic_Coverage_Program"
        ]
    ],
    on="Patient_ID",
    how="left"
)

formulary_lookup = load_file(
    Project_root / "Data" / "processed" / "rx_formulary_lookup.csv"
)

pharmacy_claims = pharmacy_claims.merge(
    formulary_lookup[
        [
            "Rx_Event_ID",
            "Formulary_Match",
            "Benefit_status"
        ]
    ],
    on="Rx_Event_ID",
    how="left"
)

# print("\nPharmacy Claims shape after coverage + formulary merge:")
# print(pharmacy_claims.shape)
#
# print("\nCoverage and formulary columns:")
# print(
#     pharmacy_claims[
#         [
#             "Rx_Event_ID",
#             "Patient_ID",
#             "Province",
#             "Synthetic_Coverage_Program",
#             "Formulary_Match",
#             "Benefit_status"
#         ]
#     ].head(10)
# )

# print(
#     "\nMissing coverage program:",
#     pharmacy_claims["Synthetic_Coverage_Program"].isna().sum()
# )
#
# print(
#     "Missing formulary match:",
#     pharmacy_claims["Formulary_Match"].isna().sum()
# )
#
# print(
#     "Missing benefit status:",
#     pharmacy_claims["Benefit_status"].isna().sum()
# )

# print("\nBenefit status distribution:")
# print(
#     pharmacy_claims.loc[
#         pharmacy_claims["Formulary_Match"] == True,
#         "Benefit_status"
#     ].value_counts(dropna=False)
# )
#
# print("\nFormulary match distribution:")
# print(pharmacy_claims["Formulary_Match"].value_counts())

rng = np.random.default_rng(42)

# ------------------------------------------------------------
# BENEFIT STATUS + CLAIM STATUS
# ------------------------------------------------------------

formulary_match = (
    pharmacy_claims["Formulary_Match"]
    .fillna(False)
    .astype(bool)
)

# Non-formulary claims need an explicit benefit restriction
# rather than a missing Benefit_status.
non_formulary_mask = ~formulary_match

non_formulary_draw = rng.random(
    len(pharmacy_claims)
)

pharmacy_claims.loc[
    non_formulary_mask & (non_formulary_draw < 0.70),
    "Benefit_status"
] = "Restricted"

pharmacy_claims.loc[
    non_formulary_mask & (non_formulary_draw >= 0.70),
    "Benefit_status"
] = "Limited"

# Fill any remaining missing benefit status for formulary claims.
# This keeps the synthetic dataset complete.
benefit_draw = rng.random(
    len(pharmacy_claims)
)

pharmacy_claims.loc[
    pharmacy_claims["Benefit_status"].isna()
    & (benefit_draw < 0.80),
    "Benefit_status"
] = "Benefit"

pharmacy_claims.loc[
    pharmacy_claims["Benefit_status"].isna()
    & (benefit_draw >= 0.80),
    "Benefit_status"
] = "Limited"


# ------------------------------------------------------------
# CLAIM OUTCOME
# ------------------------------------------------------------

outcome_draw = rng.random(
    len(pharmacy_claims)
)

pharmacy_claims["Claim_Status"] = np.select(
    [
        pharmacy_claims["Benefit_status"].eq("Restricted"),
        pharmacy_claims["Benefit_status"].eq("Limited")
        & (outcome_draw < 0.25),
        pharmacy_claims["Benefit_status"].eq("Limited")
        & (outcome_draw >= 0.25)
        & (outcome_draw < 0.45),
        pharmacy_claims["Benefit_status"].eq("Benefit")
        & (outcome_draw < 0.05),
    ],
    [
        "Rejected",
        "Rejected",
        "Partial",
        "Partial",
    ],
    default="Paid"
)
# print("\nClaim status distribution:")
# print(pharmacy_claims["Claim_Status"].value_counts())
#
# print("\nClaim status by formulary status:")
# print(
#     pharmacy_claims[
#         ["Formulary_Match", "Benefit_status", "Claim_Status"]
#     ]
#     .value_counts(dropna=False)
# )
#
# print("\nProduct and drug type:")
# print(
#     pharmacy_claims[
#         ["Product_ID"]
#     ]
#     .drop_duplicates()
#     .merge(
#         formulary_lookup[
#             ["Product_ID", "Drug_type"]
#         ].drop_duplicates(),
#         on="Product_ID",
#         how="left"
#     )
#     .head(20)
# )
#
#
#
# print("\nUnique products:")
# print(pharmacy_claims["Product_ID"].nunique())


product_master = load_file(
    Project_root / "Data" / "processed" / "drug_product_master.csv"
)
pharmacy_claims = pharmacy_claims.merge(
    product_master[
        [
            "Product_ID",
            "Brand_Name",
            "Descriptor"
        ]
    ].drop_duplicates("Product_ID"),
    on="Product_ID",
    how="left"
)

# print("\nProduct master:")
# print(product_master.columns.tolist())
#
# print("\nSelected products:")
# print(
#     product_master[
#         product_master["Product_ID"].isin(
#             pharmacy_claims["Product_ID"].unique()
#         )
#     ][
#         [
#             "Product_ID",
#             "DIN",
#             "Brand_Name",
#             "Descriptor"
#         ]
#     ].head(20)
# )
#
# print(
#     "\nSelected product count:",
#     product_master[
#         product_master["Product_ID"].isin(
#             pharmacy_claims["Product_ID"].unique()
#         )
#     ]["Product_ID"].nunique()
# )

therapy_mapping = load_file(
    Project_root / "Data" / "processed" / "therapy_product_mapping.csv"
)

# print("\nTherapy-product mapping:")
# print(
#     therapy_mapping[
#         [
#             "Therapy_Class",
#             "Product_ID",
#             "DIN",
#             "Brand_Name"
#         ]
#     ].to_string(index=False)
# )


#
# print("\nTherapy-product mapping:")
# print(
#     therapy_mapping[
#         [
#             "Therapy_Class",
#             "Product_ID",
#             "DIN",
#             "Brand_Name"
#         ]
#     ].to_string(index=False)
# )

product_volume = (
    pharmacy_claims
    .groupby("Product_ID")
    .size()
    .reset_index(name="Rx_Event_Count")
)

product_cost_setup = (
    therapy_mapping[
        [
            "Therapy_Class",
            "Product_ID",
            "DIN",
            "Brand_Name"
        ]
    ]
    .merge(
        product_volume,
        on="Product_ID",
        how="left"
    )
    .sort_values(
        "Rx_Event_Count",
        ascending=False
    )
)

# print("\nProduct volume and therapy:")
# print(
#     product_cost_setup.to_string(index=False)
# )
# print("\nRx events by therapy class:")
# print(
#     pharmacy_claims
#     .merge(
#         therapy_mapping[
#             ["Product_ID", "Therapy_Class"]
#         ],
#         on="Product_ID",
#         how="left"
#     )["Therapy_Class"]
#     .value_counts()
# )


product_drug_type = (
    formulary_lookup[
        formulary_lookup["Formulary_Match"] == True
    ]
    [
        ["Product_ID", "Drug_type"]
    ]
    .dropna(subset=["Drug_type"])
    .drop_duplicates()
    .sort_values(["Product_ID", "Drug_type"])
)
#
# print("\nProduct → Drug type records:")
# print(product_drug_type.to_string(index=False))

drug_type_counts = (
    product_drug_type
    .groupby("Product_ID")["Drug_type"]
    .nunique()
)

# print("\nProducts with multiple drug types:")
# print(
#     drug_type_counts[drug_type_counts > 1]
# )
#
# print("\nDrug type distribution across products:")
# print(
#     product_drug_type
#     .drop_duplicates("Product_ID")["Drug_type"]
#     .value_counts()
# )

selected_products = (
    load_file(
        Project_root / "Data" / "processed" / "therapy_product_mapping.csv"
    )[["Product_ID"]]
    .drop_duplicates()
)

products_with_drug_type = product_drug_type[
    ["Product_ID"]
].drop_duplicates()

missing_drug_type = selected_products[
    ~selected_products["Product_ID"].isin(
        products_with_drug_type["Product_ID"]
    )
]
#
# print("\nProducts without Drug_type:")
# print(missing_drug_type.to_string(index=False))

# drug_spending = load_file(
#     Project_root / "Data" / "raw" / "CIHI_drug_spending.xlsx"
# )
# print(drug_spending.shape)
# print(drug_spending["year"].unique())
# print(drug_spending["Jurisdiction"].unique())

therapy_cost_ranges = {
    "Antidiabetic": (8, 25),
    "Antihypertensive": (6, 20),
    "Cardiovascular": (8, 25),
    "Heart failure therapy": (7, 22),
    "Antithrombotic / secondary prevention": (5, 30),
    "Respiratory": (15, 45),
    "Analgesic / anti-inflammatory": (5, 20),
    "Bone health": (8, 25),
    "Immunomodulatory / anti-inflammatory": (30, 150),
    "Disease-modifying therapy": (200, 500),
    "Parkinson's therapy": (10, 40),
    "Antiepileptic": (10, 35),
    "Cognitive disorder therapy": (10, 35),
    "Antipsychotic": (10, 40)
}
therapy_product_mapping = load_file(
    Project_root / "Data" / "processed" / "therapy_product_mapping.csv"
)

np.random.seed(42)

product_costs = therapy_product_mapping[
    ["Product_ID", "Therapy_Class"]
].drop_duplicates().copy()

product_costs["Synthetic_Drug_Cost"] = product_costs.apply(
    lambda row: round(
        np.random.uniform(
            *therapy_cost_ranges[row["Therapy_Class"]]
        ),
        2
    ),
    axis=1
)

# print(product_costs.to_string(index=False))

pharmacy_claims = pharmacy_claims.merge(
    product_costs[
        ["Product_ID", "Synthetic_Drug_Cost"]
    ],
    on="Product_ID",
    how="left"
)

# print("Pharmacy Claims shape:", pharmacy_claims.shape)
# print("Missing synthetic drug costs:", pharmacy_claims["Synthetic_Drug_Cost"].isna().sum())

pharmacy_claims["Synthetic_Markup"] = (
    pharmacy_claims["Synthetic_Drug_Cost"] * 0.10
).round(2)

pharmacy_claims["Synthetic_Professional_Fee"] = 10.00

pharmacy_claims["Submitted_Amount"] = (
    pharmacy_claims["Synthetic_Drug_Cost"]
    + pharmacy_claims["Synthetic_Markup"]
    + pharmacy_claims["Synthetic_Professional_Fee"]
).round(2)

# ------------------------------------------------------------
# CLAIM FINANCIALS
# ------------------------------------------------------------

partial_rate = rng.uniform(
    0.50,
    0.90,
    size=len(pharmacy_claims)
)

pharmacy_claims["Accepted_Amount"] = np.select(
    [
        pharmacy_claims["Claim_Status"] == "Paid",
        pharmacy_claims["Claim_Status"] == "Partial",
    ],
    [
        pharmacy_claims["Submitted_Amount"],
        (
            pharmacy_claims["Submitted_Amount"]
            * partial_rate
        ),
    ],
    default=0
).round(2)

pharmacy_claims["Plan_Paid_Amount"] = (
    pharmacy_claims["Accepted_Amount"] * 0.80
).round(2)

pharmacy_claims["Patient_Paid_Amount"] = (
    pharmacy_claims["Accepted_Amount"]
    - pharmacy_claims["Plan_Paid_Amount"]
).round(2)


# print("\nFinancial QA")
#
# print(
#     "Negative drug costs:",
#     (pharmacy_claims["Synthetic_Drug_Cost"] < 0).sum()
# )
#
# print(
#     "Negative submitted amounts:",
#     (pharmacy_claims["Submitted_Amount"] < 0).sum()
# )
#
# print(
#     "Accepted > submitted:",
#     (
#         pharmacy_claims["Accepted_Amount"]
#         > pharmacy_claims["Submitted_Amount"]
#     ).sum()
# )
#
# print(
#     "Plan + patient != accepted:",
#     (
#         (
#             pharmacy_claims["Plan_Paid_Amount"]
#             + pharmacy_claims["Patient_Paid_Amount"]
#         ).round(2)
#         != pharmacy_claims["Accepted_Amount"]
#     ).sum()
# )
#
# print("\nClaim status:")
# print(pharmacy_claims["Claim_Status"].value_counts())
#
# print("\nFinancial columns:")
# print(
#     pharmacy_claims[
#         [
#             "Rx_Claim_ID",
#             "Claim_Status",
#             "Synthetic_Drug_Cost",
#             "Synthetic_Markup",
#             "Synthetic_Professional_Fee",
#             "Submitted_Amount",
#             "Accepted_Amount",
#             "Plan_Paid_Amount",
#             "Patient_Paid_Amount"
#         ]
#     ].head(10).to_string(index=False)
# )

print("\nBenefit Status × Claim Status:")
print(
    pd.crosstab(
        pharmacy_claims["Benefit_status"],
        pharmacy_claims["Claim_Status"],
        dropna=False,
    )
)

print("\nMissing Benefit Status:")
print(
    pharmacy_claims["Benefit_status"].isna().sum()
)

print("\nClaim Status:")
print(
    pharmacy_claims["Claim_Status"].value_counts()
)

print("\nClaim Status × Formulary Match:")
print(
    pd.crosstab(
        pharmacy_claims["Formulary_Match"],
        pharmacy_claims["Claim_Status"],
        dropna=False,
    )
)

pharmacy_claims_output_path = (
    Project_root
    / "Data"
    / "processed"
    / "synthetic_pharmacy_claims.csv"
)

pharmacy_claims.to_csv(
    pharmacy_claims_output_path,
    index=False
)

print(
    f"Saved pharmacy claims: {pharmacy_claims_output_path}"
)