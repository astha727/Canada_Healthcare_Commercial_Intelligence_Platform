import pandas as pd
from pathlib import Path
import numpy as np
from src.data.data_loader import load_file

project_root = Path(__file__).resolve().parents[2]

patient_diagnosis = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_diagnoses.csv"
)

therapy_product_mapping = (
    project_root
    / "Data"
    / "processed"
    / "therapy_product_mapping.csv"
)

patient_encounters = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_encounters.csv"
)

patient_diagnosis = load_file(patient_diagnosis)
patient_encounters = load_file(patient_encounters)
therapy_product_mapping = load_file(therapy_product_mapping)

condition_therapy_mapping = {
    "Diabetes mellitus (types combined), excluding gestational diabetes": "Antidiabetic",
    "Hypertension": "Antihypertensive",
    "Ischemic heart disease": "Cardiovascular",
    "Acute myocardial infarction": "Cardiovascular",
    "Heart failure": "Heart failure therapy",
    "Stroke": "Antithrombotic / secondary prevention",
    "Asthma": "Respiratory",
    "Chronic obstructive pulmonary disease": "Respiratory",
    "Osteoarthritis": "Analgesic / anti-inflammatory",
    "Osteoporosis": "Bone health",
    "Rheumatoid arthritis": "Immunomodulatory / anti-inflammatory",
    "Multiple sclerosis": "Disease-modifying therapy",
    "Parkinsonism, including Parkinson disease": "Parkinson's therapy",
    "Epilepsy": "Antiepileptic",
    "Dementia, including Alzheimer disease": "Cognitive disorder therapy",
    "Schizophrenia": "Antipsychotic"
}

patient_diagnosis["Therapy_Class"] = patient_diagnosis["Condition"].map(
    condition_therapy_mapping
)

treatment_initiation_probability = {
    "Antidiabetic":	0.75,
    "Antihypertensive":	0.75,
    "Cardiovascular":	0.65,
    "Heart failure therapy": 0.80,
    "Antithrombotic / secondary prevention": 0.75,
    "Respiratory":	0.65,
    "Analgesic / anti-inflammatory": 0.45,
    "Bone health":	0.65,
    "Immunomodulatory / anti-inflammatory":	0.65,
    "Disease-modifying therapy": 0.70,
    "Parkinson's therapy":	0.70,
    "Antiepileptic": 0.70,
    "Cognitive disorder therapy": 0.65,
    "Antipsychotic": 0.70
}

patient_diagnosis["Treatment_Probability"] = (
    patient_diagnosis["Therapy_Class"]
    .map(treatment_initiation_probability)
)

rng = np.random.default_rng(42)
random_draw = rng.random(len(patient_diagnosis))

patient_diagnosis["Treatment_Candidate"] = (
    random_draw < patient_diagnosis["Treatment_Probability"]
)

treatment_candidates = patient_diagnosis[
    patient_diagnosis["Treatment_Candidate"]
].copy()


treatment_candidates["Diagnosis_Date"] = pd.to_datetime(
    treatment_candidates["Diagnosis_Date"]
)



observation_start_date = pd.Timestamp("2014-07-01")

treatment_candidates["Treatment_Start_Base"] = (
    treatment_candidates["Diagnosis_Date"]
)

treatment_delay_days = rng.integers(
    0,
    91,
    size=len(treatment_candidates)
)

treatment_candidates["Treatment_Delay_Days"] = treatment_delay_days

treatment_candidates["Treatment_Start_Date"] = (
    treatment_candidates["Treatment_Start_Base"]
    + pd.to_timedelta(
        treatment_candidates["Treatment_Delay_Days"],
        unit="D"
    )
)

observation_end_date = pd.Timestamp("2024-07-01")

treatment_candidates = treatment_candidates[
    treatment_candidates["Treatment_Start_Date"] <= observation_end_date
].copy()

products_by_therapy = (
    therapy_product_mapping
    .groupby("Therapy_Class")["Product_ID"]
    .apply(list)
    .to_dict()
)

#print(products_by_therapy)

treatment_candidates["Product_ID"] = [
    rng.choice(products_by_therapy[therapy_class])
    for therapy_class in treatment_candidates["Therapy_Class"]
]

#print("Treatment rows:", len(treatment_candidates))
#print("Missing Product_ID:", treatment_candidates["Product_ID"].isna().sum())
#print("Unique Product_ID:", treatment_candidates["Product_ID"].nunique())
product_check = treatment_candidates.merge(
    therapy_product_mapping[["Therapy_Class", "Product_ID"]],
    on=["Therapy_Class", "Product_ID"],
    how="left",
    indicator=True
)

#print(product_check["_merge"].value_counts())

duration_profiles = {
    "Chronic / indefinite": {
        "median_days": 1825,
        "sigma": 0.75
    },
    "Long-term / reassessment": {
        "median_days": 1095,
        "sigma": 0.60
    },
    "Variable chronic": {
        "median_days": 730,
        "sigma": 1.00
    },
    "Medium / variable": {
        "median_days": 548,
        "sigma": 1.00
    },
    "Episodic / shorter-term": {
        "median_days": 90,
        "sigma": 0.80
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

#print("Therapy classes:", len(therapy_duration_profile))
#print("Duration profiles:", len(duration_profiles))

#print(
    #"Missing therapy mappings:",
    #set(patient_diagnosis["Therapy_Class"])
    #- set(therapy_duration_profile)
#)

#print(
    #"Unused therapy mappings:",
    #set(therapy_duration_profile)
    #- set(patient_diagnosis["Therapy_Class"])
#)

#print(
    #"Invalid duration profiles:",
    #set(therapy_duration_profile.values())
    #- set(duration_profiles)
#)

patient_diagnosis["Duration_Profile"] = (
    patient_diagnosis["Therapy_Class"]
    .map(therapy_duration_profile)
)

patient_diagnosis["Duration_Median_Days"] = (
    patient_diagnosis["Duration_Profile"]
    .map(
        {
            profile: values["median_days"]
            for profile, values in duration_profiles.items()
        }
    )
)

patient_diagnosis["Duration_Sigma"] = (
    patient_diagnosis["Duration_Profile"]
    .map(
        {
            profile: values["sigma"]
            for profile, values in duration_profiles.items()
        }
    )
)

treatment_candidates["Duration_Profile"] = (
    treatment_candidates["Therapy_Class"]
    .map(therapy_duration_profile)
)

treatment_candidates["Duration_Median_Days"] = (
    treatment_candidates["Duration_Profile"]
    .map(
        {
            profile: values["median_days"]
            for profile, values in duration_profiles.items()
        }
    )
)

treatment_candidates["Duration_Sigma"] = (
    treatment_candidates["Duration_Profile"]
    .map(
        {
            profile: values["sigma"]
            for profile, values in duration_profiles.items()
        }
    )
)

treatment_candidates["Treatment_Duration_Days"] = [
    rng.lognormal(
        mean=np.log(median_days),
        sigma=sigma
    )
    for median_days, sigma in zip(
        treatment_candidates["Duration_Median_Days"],
        treatment_candidates["Duration_Sigma"]
    )
]

treatment_candidates["Treatment_Duration_Days"] = (
    treatment_candidates["Treatment_Duration_Days"]
    .round()
    .astype(int)
)


# print(
#     treatment_candidates[
#         [
#             "Therapy_Class",
#             "Duration_Profile",
#             "Treatment_Duration_Days"
#         ]
#     ].head(10)
# )

# print("\nDuration summary:")
# print(
#     treatment_candidates.groupby("Duration_Profile")[
#         "Treatment_Duration_Days"
#     ].describe()
# )
# print(
#     treatment_candidates[
#         ["Therapy_Class", "Treatment_Duration_Days"]
#     ]
#     .groupby("Therapy_Class")
#     ["Treatment_Duration_Days"]
#     .median()
#     .sort_values()
# )

treatment_candidates["Treatment_Duration_Days"] = (
    treatment_candidates["Treatment_Duration_Days"]
    .clip(upper=3653)
)

# print(
#     treatment_candidates[
#         "Treatment_Duration_Days"
#     ].describe()
# )
#
# print(
#     "\nMaximum duration:",
#     treatment_candidates["Treatment_Duration_Days"].max()
# )

treatment_candidates["Potential_End_Date"] = (
    treatment_candidates["Treatment_Start_Date"]
    + pd.to_timedelta(
        treatment_candidates["Treatment_Duration_Days"],
        unit="D"
    )
)

# ------------------------------------------------------------
# SYNTHETIC WITHIN-CONDITION PRODUCT SWITCHING
# ------------------------------------------------------------

# This is a structural synthetic scenario for demonstrating
# longitudinal treatment-sequence analytics.
#
# It does not represent a clinical switching rate or treatment
# recommendation.

switching_rate = 0.10

# Products available within each therapy class
products_by_therapy = (
    therapy_product_mapping
    .groupby("Therapy_Class")["Product_ID"]
    .apply(list)
    .to_dict()
)

# Only patients whose first treatment episode ends before the
# observation period can receive a subsequent episode.
switch_eligible = treatment_candidates[
    treatment_candidates["Potential_End_Date"] < observation_end_date
].copy()

switch_eligible = switch_eligible[
    switch_eligible["Therapy_Class"].map(
        lambda x: len(products_by_therapy.get(x, [])) > 1
    )
].copy()

switch_count = int(
    len(switch_eligible) * switching_rate
)

if switch_count > 0:

    switch_indices = rng.choice(
        switch_eligible.index,
        size=switch_count,
        replace=False
    )

    switch_base = treatment_candidates.loc[
        switch_indices
    ].copy()

    # --------------------------------------------------------
    # FIRST EPISODE
    # --------------------------------------------------------

    # Leave a synthetic gap before the next treatment episode.
    switch_gap_days = rng.integers(
        0,
        61,
        size=len(switch_base)
    )

    # Require enough time for a subsequent observed episode.
    # The first episode is shortened only for the synthetic
    # switching cohort so that the second episode fits inside
    # the observation period.

    minimum_second_episode_days = 90

    maximum_first_duration = (
        observation_end_date
        - switch_base["Treatment_Start_Date"]
        - pd.to_timedelta(
            switch_gap_days
            + minimum_second_episode_days,
            unit="D"
        )
    ).dt.days

    valid_switch_mask = (
        maximum_first_duration >= 30
    )

    switch_base = switch_base[
        valid_switch_mask
    ].copy()

    switch_gap_days = switch_gap_days[
        valid_switch_mask
    ]

    maximum_first_duration = maximum_first_duration[
        valid_switch_mask
    ]

    if not switch_base.empty:

        # Shorten the first episode enough to allow a second
        # observed episode without overlap.
        first_duration = np.minimum(
            switch_base["Treatment_Duration_Days"].to_numpy(),
            maximum_first_duration.to_numpy()
        )

        first_duration = np.maximum(
            first_duration,
            30
        )

        switch_base["Treatment_Duration_Days"] = (
            first_duration.astype(int)
        )

        switch_base["Potential_End_Date"] = (
            switch_base["Treatment_Start_Date"]
            + pd.to_timedelta(
                switch_base["Treatment_Duration_Days"],
                unit="D"
            )
        )

        # ----------------------------------------------------
        # SECOND EPISODE
        # ----------------------------------------------------

        second_start_dates = (
            switch_base["Potential_End_Date"]
            + pd.to_timedelta(
                switch_gap_days,
                unit="D"
            )
        )

        second_duration = []

        for therapy_class in switch_base["Therapy_Class"]:

            profile = therapy_duration_profile[
                therapy_class
            ]

            duration_values = duration_profiles[
                profile
            ]

            duration = rng.lognormal(
                mean=np.log(
                    duration_values["median_days"]
                ),
                sigma=duration_values["sigma"]
            )

            second_duration.append(
                int(round(duration))
            )

        second_duration = np.clip(
            second_duration,
            30,
            3653
        )

        # Make sure the second episode never extends beyond
        # the observation period.
        maximum_second_duration = (
            observation_end_date
            - second_start_dates
        ).dt.days.to_numpy()

        second_duration = np.minimum(
            second_duration,
            maximum_second_duration
        )

        valid_second_mask = (
            second_duration >= 1
        )

        switch_base = switch_base[
            valid_second_mask
        ].copy()

        second_start_dates = second_start_dates[
            valid_second_mask
        ]

        second_duration = second_duration[
            valid_second_mask
        ]

        # ----------------------------------------------------
        # CHOOSE A DIFFERENT PRODUCT
        # ----------------------------------------------------

        second_products = []

        for therapy_class, first_product in zip(
            switch_base["Therapy_Class"],
            switch_base["Product_ID"]
        ):

            available_products = products_by_therapy[
                therapy_class
            ]

            alternative_products = [
                product
                for product in available_products
                if product != first_product
            ]

            second_products.append(
                rng.choice(alternative_products)
            )

        # ----------------------------------------------------
        # CREATE SECOND TREATMENT EPISODES
        # ----------------------------------------------------

        second_episodes = switch_base[
            [
                "Patient_ID",
                "Condition",
                "Therapy_Class"
            ]
        ].copy()

        second_episodes["Product_ID"] = (
            second_products
        )

        second_episodes["Treatment_Start_Date"] = (
            pd.to_datetime(second_start_dates)
        )

        second_episodes["Treatment_Duration_Days"] = (
            second_duration.astype(int)
        )

        second_episodes["Potential_End_Date"] = (
            second_episodes["Treatment_Start_Date"]
            + pd.to_timedelta(
                second_episodes["Treatment_Duration_Days"],
                unit="D"
            )
        )

        second_episodes["Treatment_Status"] = np.where(
            second_episodes["Potential_End_Date"]
            > observation_end_date,
            "Active",
            "Discontinued"
        )

        second_episodes["Treatment_End_Date"] = np.where(
            second_episodes["Treatment_Status"] == "Discontinued",
            second_episodes["Potential_End_Date"],
            observation_end_date
        )

        second_episodes["Treatment_End_Date"] = pd.to_datetime(
            second_episodes["Treatment_End_Date"]
        )

        # ----------------------------------------------------
        # UPDATE FIRST EPISODES
        # ----------------------------------------------------

        switch_base["Treatment_Status"] = (
            "Discontinued"
        )

        switch_base["Treatment_End_Date"] = (
            switch_base["Potential_End_Date"]
        )

        switch_base["Observed_Treatment_Days"] = (
            switch_base["Treatment_End_Date"]
            - switch_base["Treatment_Start_Date"]
        ).dt.days

        second_episodes["Observed_Treatment_Days"] = (
            second_episodes["Treatment_End_Date"]
            - second_episodes["Treatment_Start_Date"]
        ).dt.days

        # Keep the modified first episodes in the main dataset.
        treatment_candidates.loc[
            switch_base.index,
            "Treatment_Duration_Days"
        ] = switch_base[
            "Treatment_Duration_Days"
        ]

        treatment_candidates.loc[
            switch_base.index,
            "Potential_End_Date"
        ] = switch_base[
            "Potential_End_Date"
        ]

        # Add second episodes.
        treatment_candidates = pd.concat(
            [
                treatment_candidates,
                second_episodes[
                    [
                        "Patient_ID",
                        "Condition",
                        "Therapy_Class",
                        "Product_ID",
                        "Treatment_Start_Date",
                        "Treatment_Duration_Days",
                        "Potential_End_Date",
                        "Treatment_Status",
                        "Treatment_End_Date",
                        "Observed_Treatment_Days"
                    ]
                ]
            ],
            ignore_index=True
        )

# print(
#     "\nPotentially active at observation end:",
#     (
#         treatment_candidates["Potential_End_Date"]
#         > observation_end_date
#     ).sum()
# )
#
# print(
#     "Potentially discontinued during observation:",
#     (
#         treatment_candidates["Potential_End_Date"]
#         <= observation_end_date
#     ).sum()
# )

# ------------------------------------------------------------
# FINALIZE TREATMENT STATUS
# ------------------------------------------------------------

treatment_candidates["Treatment_Status"] = np.where(
    treatment_candidates["Potential_End_Date"] > observation_end_date,
    "Active",
    "Discontinued"
)

treatment_candidates["Treatment_End_Date"] = np.where(
    treatment_candidates["Treatment_Status"] == "Discontinued",
    treatment_candidates["Potential_End_Date"],
    observation_end_date
)

treatment_candidates["Treatment_End_Date"] = pd.to_datetime(
    treatment_candidates["Treatment_End_Date"]
)

treatment_candidates["Observed_Treatment_Days"] = (
    treatment_candidates["Treatment_End_Date"]
    - treatment_candidates["Treatment_Start_Date"]
).dt.days

# print(
#     treatment_candidates["Treatment_Status"]
#     .value_counts()
# )
#
# print(
#     treatment_candidates["Treatment_Status"]
#     .value_counts(normalize=True)
# )
# print(
#     "Discontinued after observation end:",
#     (
#         (treatment_candidates["Treatment_Status"] == "Discontinued")
#         &
#         (treatment_candidates["Treatment_End_Date"] > observation_end_date)
#     ).sum()
# )
#
# print(
#     "Active before observation end:",
#     (
#         (treatment_candidates["Treatment_Status"] == "Active")
#         &
#         (treatment_candidates["Treatment_End_Date"] < observation_end_date)
#     ).sum()
# )
# print(
#     "End before start:",
#     (
#         treatment_candidates["Treatment_End_Date"]
#         < treatment_candidates["Treatment_Start_Date"]
#     ).sum()
# )

# print(
#     patient_encounters[
#         [
#             "Encounter_ID",
#             "Patient_ID",
#             "Encounter_Date",
#             "Encounter_Type",
#             "Care_Setting",
#             "Primary_Condition",
#             "HCP_ID"
#         ]
#     ].head()
# )
#
# print("\nEncounter types:")
# print(patient_encounters["Encounter_Type"].value_counts())
#
# print("\nCare settings:")
# print(patient_encounters["Care_Setting"].value_counts())


treatment_link_test = treatment_candidates[
    [
        "Patient_ID",
        "Condition",
        "Therapy_Class",
        "Treatment_Start_Date"
    ]
].copy()

encounter_dates = patient_encounters[
    [
        "Encounter_ID",
        "Patient_ID",
        "Encounter_Date",
        "Encounter_Type",
        "Care_Setting",
        "Primary_Condition",
        "HCP_ID"
    ]
].copy()

treatment_link_test["Treatment_Start_Date"] = pd.to_datetime(
    treatment_link_test["Treatment_Start_Date"]
)

encounter_dates["Encounter_Date"] = pd.to_datetime(
    encounter_dates["Encounter_Date"]
)

treatment_link_test = treatment_link_test.sort_values(
    ["Treatment_Start_Date", "Patient_ID"]
).reset_index(drop=True)

encounter_dates = encounter_dates.sort_values(
    ["Encounter_Date", "Patient_ID"]
).reset_index(drop=True)

treatment_link_test = pd.merge_asof(
    treatment_link_test,
    encounter_dates,
    left_on="Treatment_Start_Date",
    right_on="Encounter_Date",
    by="Patient_ID",
    direction="backward"
)

treatment_link_test["Days_From_Encounter_To_Treatment"] = (
    treatment_link_test["Treatment_Start_Date"]
    - treatment_link_test["Encounter_Date"]
).dt.days


# print(
#     treatment_link_test[
#         "Days_From_Encounter_To_Treatment"
#     ].describe()
# )
#
# print(
#     "\nMissing prior encounter:",
#     treatment_link_test["Encounter_ID"].isna().sum()
# )
#
# print(
#     "\nTreatment starts within 7 days of prior encounter:",
#     (
#         treatment_link_test["Days_From_Encounter_To_Treatment"] <= 7
#     ).sum()
# )
#
# print(
#     "Treatment starts within 30 days:",
#     (
#         treatment_link_test["Days_From_Encounter_To_Treatment"] <= 30
#     ).sum()
# )
#
# print(
#     "Treatment starts within 90 days:",
#     (
#         treatment_link_test["Days_From_Encounter_To_Treatment"] <= 90
#     ).sum()
# )

same_condition_test = treatment_candidates[
    [
        "Patient_ID",
        "Condition",
        "Therapy_Class",
        "Treatment_Start_Date"
    ]
].copy()

same_condition_test["Treatment_Start_Date"] = pd.to_datetime(
    same_condition_test["Treatment_Start_Date"]
)

same_condition_test = same_condition_test.merge(
    patient_encounters[
        [
            "Encounter_ID",
            "Patient_ID",
            "Encounter_Date",
            "Encounter_Type",
            "Care_Setting",
            "Primary_Condition",
            "HCP_ID"
        ]
    ],
    on="Patient_ID",
    how="left"
)

same_condition_test["Encounter_Date"] = pd.to_datetime(
    same_condition_test["Encounter_Date"]
)

treatment_candidates["Observed_Treatment_Days"] = (
    treatment_candidates["Treatment_End_Date"]
    - treatment_candidates["Treatment_Start_Date"]
).dt.days

print(
    treatment_candidates["Observed_Treatment_Days"].describe()
)

print(
    "\nNegative observed durations:",
    (
        treatment_candidates["Observed_Treatment_Days"] < 0
    ).sum()
)

print(
    "Zero-day treatments:",
    (
        treatment_candidates["Observed_Treatment_Days"] == 0
    ).sum()
)
#treatment id
treatment_candidates = treatment_candidates.reset_index(drop=True)

treatment_candidates["Treatment_ID"] = [
    f"TRT_{i:06d}"
    for i in range(1, len(treatment_candidates) + 1)
]

print("Treatment rows:", len(treatment_candidates))
print(
    "Unique Treatment_ID:",
    treatment_candidates["Treatment_ID"].nunique()
)

#rename
treatment_candidates = treatment_candidates.rename(
    columns={
        "Treatment_Duration_Days": "Synthetic_Duration_Days"
    }
)


treatment_episodes = treatment_candidates[
    [
        "Treatment_ID",
        "Patient_ID",
        "Condition",
        "Therapy_Class",
        "Product_ID",
        "Treatment_Start_Date",
        "Treatment_End_Date",
        "Treatment_Status",
        "Observed_Treatment_Days",
        "Synthetic_Duration_Days"
    ]
].copy()

#final QA
# print("Treatment episode shape:", treatment_episodes.shape)
#
# print("\nMissing values:")
# print(treatment_episodes.isna().sum())
#
# print("\nTreatment status:")
# print(treatment_episodes["Treatment_Status"].value_counts())
#
# print("\nUnique patients:")
# print(treatment_episodes["Patient_ID"].nunique())
#
# print("\nUnique conditions:")
# print(treatment_episodes["Condition"].nunique())
#
# print("\nUnique therapy classes:")
# print(treatment_episodes["Therapy_Class"].nunique())
#
# print("\nUnique products:")
# print(treatment_episodes["Product_ID"].nunique())
#
# print("\nDuplicate Treatment_ID:")
# print(treatment_episodes["Treatment_ID"].duplicated().sum())
#

# treatment_product_check = treatment_episodes.merge(
#     therapy_product_mapping[
#         ["Therapy_Class", "Product_ID"]
#     ],
#     on=["Therapy_Class", "Product_ID"],
#     how="left",
#     indicator=True
# )
#
# print(
#     "\nTreatment-product mapping failures:",
#     (treatment_product_check["_merge"] != "both").sum()
# )
#
# print(
#     treatment_episodes[
#         treatment_episodes["Observed_Treatment_Days"] == 0
#     ][
#         [
#             "Treatment_ID",
#             "Patient_ID",
#             "Condition",
#             "Therapy_Class",
#             "Product_ID",
#             "Treatment_Start_Date",
#             "Treatment_End_Date",
#             "Treatment_Status",
#             "Synthetic_Duration_Days"
#         ]
#     ]
# )
#


treatment_episodes = treatment_episodes[
    [
        "Treatment_ID",
        "Patient_ID",
        "Condition",
        "Therapy_Class",
        "Product_ID",
        "Treatment_Start_Date",
        "Treatment_End_Date",
        "Treatment_Status",
        "Observed_Treatment_Days"
    ]
].copy()

treatment_output = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_patient_treatments.csv"
)

treatment_episodes.to_csv(
    treatment_output,
    index=False
)

print("Exported:", treatment_output)
print("Final treatment shape:", treatment_episodes.shape)

print("\nDiagnosis → treatment delay:")
print(
    (
        treatment_candidates["Treatment_Start_Date"]
        - treatment_candidates["Diagnosis_Date"]
    ).dt.days.describe()
)

print(
    "\nTreatment starts before diagnosis:",
    (
        treatment_candidates["Treatment_Start_Date"]
        < treatment_candidates["Diagnosis_Date"]
    ).sum()
)

print(
    "Treatment starts after observation end:",
    (
        treatment_candidates["Treatment_Start_Date"]
        > observation_end_date
    ).sum()
)

print(
    "Maximum diagnosis → treatment delay:",
    (
        treatment_candidates["Treatment_Start_Date"]
        - treatment_candidates["Diagnosis_Date"]
    ).dt.days.max()
)
