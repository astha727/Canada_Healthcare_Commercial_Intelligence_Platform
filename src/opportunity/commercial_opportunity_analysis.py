import pandas as pd
from src.data.data_loader import load_file
from pathlib import Path
import numpy as np

Project_root  = Path(__file__).resolve().parents[2]

# OPPORTUNITY ANALYTICS: LOAD FINAL TABLES

hcp_condition_stage = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "hcp_condition_stage_analytics.csv"
)

product_analytics = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "competitive_product_analytics.csv"
)

hcp_portfolio_summary = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "hcp_prescribing_analytics.csv"
)

# print("HCP condition-stage:", hcp_condition_stage.shape)
# print("Product analytics:", product_analytics.shape)
# print("HCP prescribing:", hcp_portfolio_summary.shape)

# OPPORTUNITY ANALYTICS: BUILD THERAPY CONTEXT

therapy_product_summary = (
    product_analytics
    .groupby("Therapy_Class")
    .agg(
        Product_Count=("Product_ID", "nunique"),
        Therapy_NRx_Proxy=("NRx_Proxy", "sum"),
        Therapy_TRx_Proxy=("TRx_Proxy", "sum"),
        Therapy_Refills=("Refills", "sum"),
        Pharmacy_Claims=("Pharmacy_Claims", "sum"),
        Formulary_Matched_Claims=("Formulary_Matched_Claims", "sum"),
        Plan_Paid_Amount=("Plan_Paid_Amount", "sum"),
        Patient_Paid_Amount=("Patient_Paid_Amount", "sum")
    )
    .reset_index()
)

therapy_product_summary["Therapy_Formulary_Match_Rate"] = (
    therapy_product_summary["Formulary_Matched_Claims"]
    / therapy_product_summary["Pharmacy_Claims"]
)
#
# print(therapy_product_summary.shape)
# print(therapy_product_summary.head())

# OPPORTUNITY ANALYTICS: CONDITION-LEVEL TREATMENT GAP

timeline = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "patient_longitudinal_timeline.csv"
)

diagnosed = (
    timeline[timeline["Event_Type"] == "Diagnosis"]
    [["Patient_ID", "Condition"]]
    .drop_duplicates()
)

treated = (
    timeline[timeline["Event_Type"] == "Treatment Start"]
    [["Patient_ID", "Condition"]]
    .drop_duplicates()
)

diagnosed_treatment_status = diagnosed.merge(
    treated,
    on=["Patient_ID", "Condition"],
    how="left",
    indicator=True
)

diagnosed_treatment_status["No_Observed_Treatment"] = (
    diagnosed_treatment_status["_merge"] == "left_only"
)

condition_treatment_gap = (
    diagnosed_treatment_status
    .groupby("Condition")
    .agg(
        Diagnosed_Patients=("Patient_ID", "nunique"),
        Diagnosed_No_Observed_Treatment=(
            "No_Observed_Treatment",
            "sum"
        )
    )
    .reset_index()
)

condition_treatment_gap["Treatment_Gap_Rate"] = (
    condition_treatment_gap["Diagnosed_No_Observed_Treatment"]
    / condition_treatment_gap["Diagnosed_Patients"]
)
#
# print(condition_treatment_gap.shape)
# print(condition_treatment_gap.sort_values(
#     "Diagnosed_No_Observed_Treatment",
#     ascending=False
# ).head(10))

# OPPORTUNITY ANALYTICS: BUILD COMMERCIAL OPPORTUNITY TABLE

# print("Opportunity table:", opportunity.shape)
# print(opportunity.head())
# # OPPORTUNITY ANALYTICS: VERIFY GRAIN
#
# grain_check = (
#     opportunity
#     .groupby([
#         "Prescribing_HCP_ID",
#         "Condition",
#         "Therapy_Class"
#     ])
#     .size()
# )
#
# print("Maximum rows per HCP-condition-therapy:", grain_check.max())
# print("Duplicate grain rows:", (grain_check > 1).sum())

# OPPORTUNITY ANALYTICS: DIAGNOSE DUPLICATE GRAIN
#
# hcp_duplicates = (
#     hcp_condition_stage
#     .groupby([
#         "Prescribing_HCP_ID",
#         "Condition",
#         "Therapy_Class"
#     ])
#     .size()
# )
#
# print(
#     "HCP condition-stage duplicate combinations:",
#     (hcp_duplicates > 1).sum()
# )
#
# therapy_duplicates = (
#     therapy_product_summary
#     .groupby("Therapy_Class")
#     .size()
# )
#
# print(
#     "Therapy summary duplicate combinations:",
#     (therapy_duplicates > 1).sum()
# )
#
# condition_duplicates = (
#     condition_treatment_gap
#     .groupby("Condition")
#     .size()
# )
#
# print(
#     "Condition gap duplicate combinations:",
#     (condition_duplicates > 1).sum()
# )
# OPPORTUNITY ANALYTICS: INSPECT DUPLICATE HCP GRAIN
#
# duplicate_keys = (
#     hcp_condition_stage
#     .groupby([
#         "Prescribing_HCP_ID",
#         "Condition",
#         "Therapy_Class"
#     ])
#     .size()
#     .reset_index(name="Row_Count")
# )
#
# duplicate_keys = duplicate_keys[
#     duplicate_keys["Row_Count"] > 1
# ]
#
# print(duplicate_keys.head(10))
# # OPPORTUNITY ANALYTICS: INSPECT DUPLICATE ROWS
#
# example = duplicate_keys.iloc[0]
#
# duplicate_rows = hcp_condition_stage[
#     (hcp_condition_stage["Prescribing_HCP_ID"] == example["Prescribing_HCP_ID"]) &
#     (hcp_condition_stage["Condition"] == example["Condition"]) &
#     (hcp_condition_stage["Therapy_Class"] == example["Therapy_Class"])
# ]
#
# print(duplicate_rows.T)

# OPPORTUNITY ANALYTICS: AGGREGATE TREATMENT STAGES

hcp_opportunity_base = (
    hcp_condition_stage
    .groupby([
        "Prescribing_HCP_ID",
        "HCP_Name",
        "Province",
        "Specialty",
        "Condition",
        "Therapy_Class"
    ])
    .agg(
        Unique_Patients=("Unique_Patients", "sum"),
        Treatment_Episodes=("Treatment_Episodes", "sum"),
        NRx_Proxy=("NRx_Proxy", "sum"),
        Refills=("Refills", "sum"),
        TRx_Proxy=("TRx_Proxy", "sum")
    )
    .reset_index()
)
stage_activity = (
    hcp_condition_stage
    .pivot_table(
        index=[
            "Prescribing_HCP_ID",
            "Condition",
            "Therapy_Class"
        ],
        columns="Analytical_Stage",
        values=[
            "Treatment_Episodes",
            "NRx_Proxy",
            "Refills",
            "TRx_Proxy"
        ],
        aggfunc="sum",
        fill_value=0
    )
)

# print("HCP opportunity base:", hcp_opportunity_base.shape)
# print(hcp_opportunity_base.head())
# print("Stage activity:", stage_activity.shape)
# print(stage_activity.columns.tolist())
# print(stage_activity.head())

# OPPORTUNITY ANALYTICS: FLATTEN STAGE METRICS

stage_activity.columns = [
    f"{metric}_{stage.replace(' ', '_')}"
    for metric, stage in stage_activity.columns
]

stage_activity = stage_activity.reset_index()

# print(stage_activity.columns.tolist())
# print(stage_activity.head())
# OPPORTUNITY ANALYTICS: MERGE STAGE METRICS

opportunity = hcp_opportunity_base.merge(
    stage_activity,
    on=[
        "Prescribing_HCP_ID",
        "Condition",
        "Therapy_Class"
    ],
    how="left"
)

opportunity = opportunity.merge(
    therapy_product_summary,
    on="Therapy_Class",
    how="left"
)

opportunity = opportunity.merge(
    condition_treatment_gap,
    on="Condition",
    how="left"
)

# print("Opportunity table:", opportunity.shape)
# print(opportunity.columns.tolist())
# OPPORTUNITY ANALYTICS: ACTIVE TREATMENT SIGNAL

opportunity["Active_Treatment_Flag"] = (
    opportunity["Treatment_Episodes_Active_Treatment"] > 0
)

# print(
#     opportunity["Active_Treatment_Flag"]
#     .value_counts()
# )

# OPPORTUNITY ANALYTICS: HIGH ACTIVITY SIGNAL

trx_threshold = opportunity["TRx_Proxy"].quantile(0.75)

opportunity["High_TRx_Activity_Flag"] = (
    opportunity["TRx_Proxy"] >= trx_threshold
)

# print("TRx threshold:", trx_threshold)
#
# print(
#     opportunity["High_TRx_Activity_Flag"]
#     .value_counts()
# )

# OPPORTUNITY ANALYTICS: TREATMENT GAP SIGNAL

opportunity["Treatment_Gap_Signal"] = (
    opportunity["Diagnosed_No_Observed_Treatment"] > 0
)

# print(
#     opportunity["Treatment_Gap_Signal"]
#     .value_counts()
# )
#

# OPPORTUNITY ANALYTICS: CREATE OPPORTUNITY CATEGORIES

opportunity["Commercial_Evidence_Category"] = np.select(
    [
        (
            opportunity["Active_Treatment_Flag"]
            & opportunity["High_TRx_Activity_Flag"]
        ),
        (
            opportunity["Active_Treatment_Flag"]
            & ~opportunity["High_TRx_Activity_Flag"]
        ),
        (
            ~opportunity["Active_Treatment_Flag"]
            & opportunity["High_TRx_Activity_Flag"]
        ),
    ],
    [
        "Active + High Activity",
        "Active + Lower Activity",
        "Historical + High Activity",
    ],
    default="Historical + Lower Activity"
)

# print(
#     opportunity["Commercial_Evidence_Category"]
#     .value_counts()
# )

# OMNICHANNEL ENGAGEMENT: BASE RECOMMENDATION

opportunity["Engagement_Recommendation"] = np.select(
    [
        opportunity["Commercial_Evidence_Category"]
        == "Active + High Activity",

        opportunity["Commercial_Evidence_Category"]
        == "Active + Lower Activity",

        opportunity["Commercial_Evidence_Category"]
        == "Historical + High Activity",
    ],
    [
        "Rep + Peer Education",
        "Rep + Digital Education",
        "Re-engagement + Rep Review",
    ],
    default="Digital / Low-Intensity"
)
#
# print(
#     opportunity["Engagement_Recommendation"]
#     .value_counts()
# )

# OMNICHANNEL ENGAGEMENT: RECOMMENDATION RATIONALE

opportunity["Engagement_Rationale"] = np.select(
    [
        opportunity["Commercial_Evidence_Category"]
        == "Active + High Activity",

        opportunity["Commercial_Evidence_Category"]
        == "Active + Lower Activity",

        opportunity["Commercial_Evidence_Category"]
        == "Historical + High Activity",
    ],
    [
        "Active treatment with high synthetic Rx activity supports higher-touch educational engagement.",
        "Active treatment is present, but synthetic Rx activity is lower; combine targeted field and digital education.",
        "Historical Rx activity was high but no active treatment is observed; re-engagement should investigate the change before further targeting.",
    ],
    [
        "Historical treatment activity is lower; use lower-intensity digital engagement rather than assuming active demand."
    ]
)

print(
    opportunity[
        [
            "Prescribing_HCP_ID",
            "Condition",
            "Therapy_Class",
            "Commercial_Evidence_Category",
            "Engagement_Recommendation",
            "Engagement_Rationale"
        ]
    ].head(10)
)

# OMNICHANNEL ENGAGEMENT: METHODOLOGY LABEL

opportunity["Recommendation_Basis"] = (
    "Rule-based recommendation from synthetic activity evidence"
)

print(
    opportunity["Recommendation_Basis"].value_counts()
)

# OPPORTUNITY ANALYTICS: FINAL QA

# print("Rows:", len(opportunity))
#
# print(
#     "Duplicate HCP-condition-therapy:",
#     opportunity.duplicated(
#         subset=[
#             "Prescribing_HCP_ID",
#             "Condition",
#             "Therapy_Class"
#         ]
#     ).sum()
# )

# print(
#     "Missing engagement recommendation:",
#     opportunity["Engagement_Recommendation"].isna().sum()
# )
#
# print(
#     "Missing engagement rationale:",
#     opportunity["Engagement_Rationale"].isna().sum()
# )
#

# OPPORTUNITY ANALYTICS: SAVE FINAL OUTPUT

opportunity_output = (
    Project_root
    / "Data"
    / "processed"
    / "commercial_opportunity_analytics.csv"
)

opportunity.to_csv(
    opportunity_output,
    index=False
)

print("Saved:", opportunity_output)
print("Shape:", opportunity.shape)