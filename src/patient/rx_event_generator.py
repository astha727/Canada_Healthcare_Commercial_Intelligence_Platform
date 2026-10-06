from pathlib import Path
import pandas as pd
import numpy as np


project_root = Path(__file__).resolve().parents[2]

treatment_path = (
    project_root / "Data" / "processed" / "synthetic_patient_treatments.csv"
)

hcp_path = (
    project_root / "Data" / "processed" / "synthetic_hcp_master.csv"
)

therapy_product_path = (
    project_root / "Data" / "processed" / "therapy_product_mapping.csv"
)

treatments = pd.read_csv(treatment_path)
hcps = pd.read_csv(hcp_path)
therapy_products = pd.read_csv(therapy_product_path)

treatments["Treatment_Start_Date"] = pd.to_datetime(
    treatments["Treatment_Start_Date"]
)

treatments["Treatment_End_Date"] = pd.to_datetime(
    treatments["Treatment_End_Date"]
)

days_supply_profiles = {
    "Chronic / indefinite": {
        "options": [30, 60, 90],
        "probabilities": [0.45, 0.35, 0.20]
    },
    "Long-term / reassessment": {
        "options": [30, 60, 90],
        "probabilities": [0.40, 0.35, 0.25]
    },
    "Variable chronic": {
        "options": [30, 60, 90],
        "probabilities": [0.50, 0.30, 0.20]
    },
    "Medium / variable": {
        "options": [30, 60],
        "probabilities": [0.65, 0.35]
    },
    "Episodic / shorter-term": {
        "options": [15, 30, 60],
        "probabilities": [0.45, 0.45, 0.10]
    }
}

therapy_duration_profile = {
    "Antidiabetic": "Chronic / indefinite",
    "Antihypertensive": "Chronic / indefinite",
    "Cardiovascular": "Chronic / indefinite",
    "Heart failure therapy": "Chronic / indefinite",
    "Disease-modifying therapy": "Chronic / indefinite",
    "Parkinson's therapy": "Chronic / indefinite",
    "Antiepileptic": "Chronic / indefinite",
    "Cognitive disorder therapy": "Chronic / indefinite",

    "Bone health": "Long-term / reassessment",

    "Immunomodulatory / anti-inflammatory": "Variable chronic",

    "Respiratory": "Medium / variable",
    "Antipsychotic": "Medium / variable",

    "Antithrombotic / secondary prevention": "Medium / variable",

    "Analgesic / anti-inflammatory": "Episodic / shorter-term"
}

treatments["Duration_Profile"] = treatments["Therapy_Class"].map(
    therapy_duration_profile
)

# print("\nDuration profiles:")
# print(treatments["Duration_Profile"].value_counts())
#
# print(
#     "\nMissing duration profiles:",
#     treatments["Duration_Profile"].isna().sum()
# )

rng = np.random.default_rng(42)

rx_events = []

for _, treatment in treatments.iterrows():

    profile = treatment["Duration_Profile"]

    options = days_supply_profiles[profile]["options"]
    probabilities = days_supply_profiles[profile]["probabilities"]

    initial_delay_max = min(
        7,
        (
                treatment["Treatment_End_Date"]
                - treatment["Treatment_Start_Date"]
        ).days
    )

    initial_delay = int(
        rng.integers(0, initial_delay_max + 1)
    )

    fill_date = (
            treatment["Treatment_Start_Date"]
            + pd.Timedelta(days=initial_delay)
    )

    while fill_date <= treatment["Treatment_End_Date"]:

        days_supply = int(
            rng.choice(
                options,
                p=probabilities
            )
        )

        if fill_date > treatment["Treatment_End_Date"]:
            break

        rx_events.append({
            "Treatment_ID": treatment["Treatment_ID"],
            "Patient_ID": treatment["Patient_ID"],
            "Product_ID": treatment["Product_ID"],
            "Therapy_Class": treatment["Therapy_Class"],
            "Fill_Date": fill_date,
            "Days_Supply": days_supply
        })

        refill_gap = int(rng.integers(-5, 8))

        fill_date = (
            fill_date
            + pd.Timedelta(days=days_supply + refill_gap)
        )

rx_events = pd.DataFrame(rx_events)

# print("\nRx events:", rx_events.shape)
# print(
#      "Unique treatments with Rx events:",
#      rx_events["Treatment_ID"].nunique()
#  )

rx_events_per_treatment = (
    rx_events
    .groupby("Treatment_ID")
    .size()
)

# print("\nRx events per treatment:")
# print(rx_events_per_treatment.describe())
#
# print("\nTreatments by number of Rx events:")
# print(
#     rx_events_per_treatment
#     .value_counts()
#     .sort_index()
# )

rx_summary = (
    rx_events
    .groupby(["Treatment_ID", "Therapy_Class"])
    .agg(
        Rx_Event_Count=("Fill_Date", "size"),
        First_Fill_Date=("Fill_Date", "min"),
        Last_Fill_Date=("Fill_Date", "max")
    )
    .reset_index()
)

rx_summary = rx_summary.merge(
    treatments[
        [
            "Treatment_ID",
            "Duration_Profile",
            "Observed_Treatment_Days"
        ]
    ],
    on="Treatment_ID",
    how="left"
)

# print("\nRx events by duration profile:")
# print(
#     rx_summary
#     .groupby("Duration_Profile")["Rx_Event_Count"]
#     .describe()
#     .round(2)
# )
#
# print("\nDays supply distribution:")
# print(
#     rx_events["Days_Supply"]
#     .value_counts()
#     .sort_index()
# )

rx_events = rx_events.sort_values(
    ["Treatment_ID", "Fill_Date"]
).reset_index(drop=True)

rx_events["Rx_Event_ID"] = [
    f"RX_{i:06d}"
    for i in range(1, len(rx_events) + 1)
]

rx_events["Rx_Event_Type"] = (
    rx_events
    .groupby("Treatment_ID")
    .cumcount()
    .eq(0)
    .map({
        True: "Initial Fill",
        False: "Refill"
    })
)

# print("\nRx Event Type:")
# print(
#     rx_events["Rx_Event_Type"]
#     .value_counts()
# )
#
# print(
#     "\nUnique Rx_Event_ID:",
#     rx_events["Rx_Event_ID"].nunique()
# )
#
# print(
#     "Duplicate Rx_Event_ID:",
#     rx_events["Rx_Event_ID"].duplicated().sum()
# )




linkage_path = (
    project_root
    / "Data"
    / "processed"
    / "treatment_encounter_linkage.csv"
)

treatment_linkage = pd.read_csv(linkage_path)

observed_treatment_hcp = (
    treatment_linkage[
        ["Treatment_ID", "HCP_ID", "Link_Type"]
    ]
    .drop_duplicates("Treatment_ID")
)



treatments = treatments.merge(
    observed_treatment_hcp,
    on="Treatment_ID",
    how="left"
)

mapping_path = (
    project_root
    / "Data"
    / "processed"
    / "disease_specialty_mapping.csv"
)

disease_specialty = pd.read_csv(mapping_path)

# print("Disease-specialty mapping:", disease_specialty.shape)
# print(disease_specialty.columns.tolist())
#
# print(
#     disease_specialty[
#         ["Condition", "Primary_Specialty"]
#     ].drop_duplicates()
# )

treatment_conditions = set(treatments["Condition"].unique())

mapped_conditions = set(
    disease_specialty["Condition"].unique()
    )
#
# print(
#     "Treatment conditions:",
#     len(treatment_conditions)
# )
#
# print(
#     "Mapped conditions:",
#     len(mapped_conditions)
# )
#
# print(
#     "Missing condition mappings:",
#     treatment_conditions - mapped_conditions
# )

patient_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_master.csv"
)

patients = pd.read_csv(patient_path)

print("Patients:", patients.shape)

treatments = treatments.merge(
    disease_specialty[
        ["Condition", "Primary_Specialty"]
    ],
    on="Condition",
    how="left",
    validate="many_to_one"
)

treatments = treatments.merge(
    patients[
        ["Patient_ID", "Province"]
    ],
    on="Patient_ID",
    how="left",
    validate="many_to_one"
)

# print(
#     "Missing treatment province:",
#     treatments["Province"].isna().sum()
# )

# print("Missing treatment specialties:")
# print(
#     treatments["Primary_Specialty"].isna().sum()
# )

hcp_pool = (
    hcps
    .groupby(["Province", "Specialty"])["HCP_ID"]
    .apply(list)
    .to_dict()
)

# print("Province-specialty HCP pools:", len(hcp_pool))

treatments["HCP_Pool_Size"] = [
    len(
        hcp_pool.get(
            (province, specialty),
            []
        )
    )
    for province, specialty in zip(
        treatments["Province"],
        treatments["Primary_Specialty"]
    )
]

# print(
#     "\nHCP pool size distribution:"
# )
#
# print(
#     treatments["HCP_Pool_Size"]
#     .value_counts()
#     .sort_index()
# )
#
# print(
#     "\nTreatments with no eligible HCP:",
#     (treatments["HCP_Pool_Size"] == 0).sum()
# )

rng = np.random.default_rng(42)

missing_hcp_mask = treatments["HCP_ID"].isna()

treatments.loc[missing_hcp_mask, "HCP_ID"] = [
    rng.choice(
        hcp_pool[(province, specialty)]
    )
    for province, specialty in zip(
        treatments.loc[missing_hcp_mask, "Province"],
        treatments.loc[missing_hcp_mask, "Primary_Specialty"]
    )
]

# print("Treatments:", len(treatments))
#
# print(
#     "Missing HCP_ID:",
#     treatments["HCP_ID"].isna().sum()
# )
#
# print(
#     "Unique HCPs assigned:",
#     treatments["HCP_ID"].nunique()
# )
#
# print(
#     "Unique treatments:",
#     treatments["Treatment_ID"].nunique()
# )

treatments["HCP_Assignment_Type"] = np.where(
    treatments["Treatment_ID"].isin(
        observed_treatment_hcp["Treatment_ID"]
    ),
    "Observed encounter-linked",
    "Synthetic eligibility-based"
)

# print(
#     "\nHCP assignment type:"
# )
#
# print(
#     treatments["HCP_Assignment_Type"].value_counts()
# )

# print(treatments.columns.tolist())
treatment_hcp = treatments[
     [
         "Treatment_ID",
         "HCP_ID",
         "HCP_Assignment_Type"
     ]
 ].copy()
#
# print(
#     "\nTreatment-HCP lookup:",
#     treatment_hcp.shape
# )
#
# print(
#     "Duplicate Treatment_ID:",
#     treatment_hcp["Treatment_ID"].duplicated().sum()
# )
#
# print(
#     "Missing HCP_ID:",
#     treatment_hcp["HCP_ID"].isna().sum()
# )

rx_events = rx_events.merge(
    treatment_hcp,
    on="Treatment_ID",
    how="left",
    validate="many_to_one"
)

# print("Rx events:", rx_events.shape)
#
# print(
#     "\nMissing HCP_ID:",
#     rx_events["HCP_ID"].isna().sum()
# )
#
# print(
#     "Missing HCP assignment type:",
#     rx_events["HCP_Assignment_Type"].isna().sum()
# )
# hcp_per_treatment = (
#     rx_events
#     .groupby("Treatment_ID")["HCP_ID"]
#     .nunique()
# )
#
# print(
#     "Treatments with >1 HCP:",
#     (hcp_per_treatment > 1).sum()
# )
#
# print(
#     "Treatments with exactly 1 HCP:",
#     (hcp_per_treatment == 1).sum()
# )


# print("HCP assignment across Rx events:")
# print(
#     rx_events["HCP_Assignment_Type"].value_counts()
# )
#
# print("\nHCP assignment across treatments:")
# print(
#     treatment_hcp["HCP_Assignment_Type"].value_counts()
# )
#
# print("\nUnique HCPs by assignment type:")
# print(
#     rx_events
#     .groupby("HCP_Assignment_Type")["HCP_ID"]
#     .nunique()
# )
#
# print(
#     "\nRx events by assignment type:"
# )
#
# print(
#     rx_events
#     .groupby(
#         ["HCP_Assignment_Type", "Rx_Event_Type"]
#     )
#     .size()
# )

rx_events = rx_events[
    [
        "Rx_Event_ID",
        "Treatment_ID",
        "Patient_ID",
        "Product_ID",
        "Therapy_Class",
        "HCP_ID",
        "Fill_Date",
        "Days_Supply",
        "Rx_Event_Type",
        "HCP_Assignment_Type"
    ]
].copy()

print("Final Rx event shape:", rx_events.shape)

print("\nFinal Rx columns:")
print(rx_events.columns.tolist())

print("\nMissing values:")
print(
    rx_events.isna().sum()
)

print("\nDuplicate Rx_Event_ID:")
print(
    rx_events["Rx_Event_ID"].duplicated().sum()
)

print("\nUnique treatments:")
print(
    rx_events["Treatment_ID"].nunique()
)

print("\nUnique HCPs:")
print(
    rx_events["HCP_ID"].nunique()
)

print("\nRx event types:")
print(
    rx_events["Rx_Event_Type"].value_counts()
)

rx_output_path = (
    project_root / "Data" / "processed" / "synthetic_patient_rx_events.csv"
)

rx_events.to_csv(
    rx_output_path,
    index=False
)

print("Exported:", rx_output_path)

print("\nRx fill date range:")
print(rx_events["Fill_Date"].min())
print(rx_events["Fill_Date"].max())

print("\nDays supply:")
print(
    rx_events["Days_Supply"]
    .value_counts()
    .sort_index()
)

print("\nRx events per treatment:")
rx_events_per_treatment = (
    rx_events
    .groupby("Treatment_ID")
    .size()
)

print(rx_events_per_treatment.describe())

print(
    "\nTreatments with no Rx events:",
    treatments["Treatment_ID"].nunique()
    - rx_events["Treatment_ID"].nunique()
)

print(
    "Rx fills before treatment start:",
    (
        rx_events["Fill_Date"]
        <
        rx_events["Treatment_ID"].map(
            treatments.set_index("Treatment_ID")["Treatment_Start_Date"]
        )
    ).sum()
)

print(
    "Rx fills after treatment end:",
    (
        rx_events["Fill_Date"]
        >
        rx_events["Treatment_ID"].map(
            treatments.set_index("Treatment_ID")["Treatment_End_Date"]
        )
    ).sum()
)