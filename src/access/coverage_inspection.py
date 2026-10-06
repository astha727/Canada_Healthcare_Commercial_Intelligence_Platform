import pandas as pd
from pathlib import Path
from src.data.data_loader import load_file


Project_root = Path(__file__).resolve().parents[2]

formulary = load_file(
    Project_root / "Data" / "processed" / "formulary_coverage.parquet"
)

coverage = load_file(
    Project_root / "Data" / "processed" / "synthetic_patient_coverage.csv"
)

rx_events = load_file(
    Project_root / "Data" / "processed" / "synthetic_patient_rx_events.csv"
)

product_master = load_file(
    Project_root / "Data" / "processed" / "drug_product_master.csv"
)

# print("Formulary:", formulary.shape)
# print("Coverage:", coverage.shape)
# print("Rx Events:", rx_events.shape)
# print("Product Master:", product_master.shape)

# print(formulary.columns.tolist())

formulary["Coverage_start_date"] = pd.to_datetime(
    formulary["Coverage_start_date"]
)

formulary["Coverage_end_date"] = pd.to_datetime(
    formulary["Coverage_end_date"]
)

rx_events["Fill_Date"] = pd.to_datetime(
    rx_events["Fill_Date"]
)

formulary_date_check = formulary[
    [
        "Jurisdiction",
        "Drug_program",
        "DIN",
        "Coverage_start_date",
        "Coverage_end_date",
        "Benefit_status"
    ]
].copy()

formulary_date_check = formulary_date_check.sort_values(
    [
        "Jurisdiction",
        "Drug_program",
        "DIN",
        "Coverage_start_date"
    ]
)

# print(
#     formulary_date_check.head(20).to_string(index=False)
# )


# Look for overlapping formulary coverage periods
# within the same jurisdiction, program, and DIN.

overlap_candidates = formulary_date_check[
    formulary_date_check.duplicated(
        subset=["Jurisdiction", "Drug_program", "DIN"],
        keep=False
    )
].copy()

# print(
#     "Rows involving repeated Jurisdiction + Program + DIN:",
#     len(overlap_candidates)
# )
#
# print(
#     "\nRepeated examples:"
# )
#
# print(
#     overlap_candidates.head(30).to_string(index=False)
# )

# Check whether any repeated formulary records overlap in time.

repeated = formulary_date_check[
    formulary_date_check.duplicated(
        subset=["Jurisdiction", "Drug_program", "DIN"],
        keep=False
    )
].copy()

repeated = repeated.sort_values(
    [
        "Jurisdiction",
        "Drug_program",
        "DIN",
        "Coverage_start_date"
    ]
)

overlap_rows = []
#
# for key, group in repeated.groupby(
#         ["Jurisdiction", "Drug_program", "DIN"]
# ):
#
#     group = group.sort_values("Coverage_start_date")
#
#     previous_end = None
#
#     for _, row in group.iterrows():
#
#         current_start = row["Coverage_start_date"]
#         current_end = row["Coverage_end_date"]
#
#         if previous_end is not None:
#
#             if pd.isna(previous_end) or current_start <= previous_end:
#                 overlap_rows.append(key)
#
#         if pd.isna(previous_end):
#             previous_end = current_end
#
#         elif pd.isna(current_end):
#             previous_end = current_end
#
#         else:
#             previous_end = max(previous_end, current_end)
#
overlap_groups = pd.DataFrame(
     overlap_rows,
     columns=["Jurisdiction", "Drug_program", "DIN"]
 ).drop_duplicates()
#
# print(
#     "Groups with overlapping coverage periods:",
#     len(overlap_groups)
# )
#
# print(
#     "\nExample overlapping groups:"
# )
#
# print(
#     overlap_groups.head(20).to_string(index=False)
# )
#
# example_overlap = formulary_date_check[
#     (
#         formulary_date_check["Jurisdiction"] == "British Columbia"
#     )
#     &
#     (
#         formulary_date_check["Drug_program"]
#         == "Children in the At Home Program"
#     )
#     &
#     (
#         formulary_date_check["DIN"] == "00333395"
#     )
# ].sort_values("Coverage_start_date")
#
# print(
#     example_overlap.to_string(index=False)
# )

# overlap_details = []
#
# for _, row in overlap_groups.iterrows():
#
#     subset = formulary_date_check[
#         (formulary_date_check["Jurisdiction"] == row["Jurisdiction"])
#         &
#         (formulary_date_check["Drug_program"] == row["Drug_program"])
#         &
#         (formulary_date_check["DIN"] == row["DIN"])
#     ]
#
#     statuses = subset["Benefit_status"].dropna().unique()
#
#     if len(statuses) > 1:
#         overlap_details.append(
#             [
#                 row["Jurisdiction"],
#                 row["Drug_program"],
#                 row["DIN"],
#                 ", ".join(sorted(statuses))
#             ]
#         )
#
# overlap_status_conflicts = pd.DataFrame(
#     overlap_details,
#     columns=[
#         "Jurisdiction",
#         "Drug_program",
#         "DIN",
#         "Benefit_statuses"
#     ]
# )
#
# print(
#     "Overlapping groups with multiple Benefit statuses:",
#     len(overlap_status_conflicts)
# )
#
# print(
#     "\nExamples:"
# )
#
# print(
#     overlap_status_conflicts.head(20).to_string(index=False)
# )

product_din = product_master[
    [
        "Product_ID",
        "DIN"
    ]
].drop_duplicates()

rx_formulary = rx_events.merge(
    product_din,
    on="Product_ID",
    how="left",
    validate="many_to_one"
)

# print("Rx events:", len(rx_events))
# print("After Product → DIN merge:", len(rx_formulary))
#
# print(
#     "\nMissing DIN:",
#     rx_formulary["DIN"].isna().sum()
# )
#
# print(
#     "\nDuplicate Rx Event IDs:",
#     rx_formulary["Rx_Event_ID"].duplicated().sum()
# )
#
# print(
#     "\nSample:"
# )
#
# print(
#     rx_formulary[
#         [
#             "Rx_Event_ID",
#             "Patient_ID",
#             "Product_ID",
#             "DIN",
#             "Fill_Date"
#         ]
#     ].head(10).to_string(index=False)
# )

rx_formulary["DIN"] = (
    rx_formulary["DIN"]
    .astype(str)
    .str.strip()
    .str.zfill(8)
)

formulary["DIN"] = (
    formulary["DIN"]
    .astype(str)
    .str.strip()
    .str.zfill(8)
)

# print(
#     rx_formulary["DIN"].head(10).to_string(index=False)
# )
#
# print(
#     "\nFormulary DIN sample:"
# )
#
# print(
#     formulary["DIN"].head(10).to_string(index=False)
# )

coverage_lookup = coverage[
    [
        "Patient_ID",
        "Province",
        "Synthetic_Coverage_Program",
        "Coverage_Start_Date",
        "Coverage_End_Date",
        "Coverage_Assignment_Type"
    ]
].copy()

rx_formulary = rx_formulary.merge(
    coverage_lookup,
    on="Patient_ID",
    how="left",
    validate="many_to_one"
)
#
# print(
#     "Rx events after coverage merge:",
#     len(rx_formulary)
# )
#
# print(
#     "Missing Province:",
#     rx_formulary["Province"].isna().sum()
# )
#
# print(
#     "Missing Synthetic Coverage Program:",
#     rx_formulary[
#         "Synthetic_Coverage_Program"
#     ].isna().sum()
# )
#
# print(
#     "\nSample:"
# )
#
# print(
#     rx_formulary[
#         [
#             "Rx_Event_ID",
#             "Patient_ID",
#             "DIN",
#             "Fill_Date",
#             "Province",
#             "Synthetic_Coverage_Program"
#         ]
#     ].head(10).to_string(index=False)
# )


#formulary lookup
rx_formulary["Jurisdiction"] = rx_formulary["Province"]

rx_formulary["Drug_program"] = (
    rx_formulary["Synthetic_Coverage_Program"]
)
#
# print(
#     rx_formulary[
#         [
#             "Rx_Event_ID",
#             "DIN",
#             "Fill_Date",
#             "Jurisdiction",
#             "Drug_program"
#         ]
#     ].head(10).to_string(index=False)
# )

coverage_programs = coverage[
    [
        "Province",
        "Synthetic_Coverage_Program"
    ]
].drop_duplicates()

coverage_programs = coverage_programs.rename(
    columns={
        "Province": "Jurisdiction",
        "Synthetic_Coverage_Program": "Drug_program"
    }
)

formulary_v1 = formulary.merge(
    coverage_programs,
    on=["Jurisdiction", "Drug_program"],
    how="inner"
)

# print(
#     "Original formulary rows:",
#     len(formulary)
# )
#
# print(
#     "V1 formulary rows:",
#     len(formulary_v1)
# )
#
# print(
#     "V1 jurisdictions:",
#     formulary_v1["Jurisdiction"].nunique()
# )
#
# print(
#     "V1 programs:",
#     formulary_v1["Drug_program"].nunique()
# )

rx_dins = rx_formulary["DIN"].dropna().unique()

formulary_dins = formulary_v1["DIN"].dropna().unique()

matching_dins = set(rx_dins).intersection(
    set(formulary_dins)
)

# print(
#     "Unique Rx event DINs:",
#     len(rx_dins)
# )
#
# print(
#     "Unique relevant formulary DINs:",
#     len(formulary_dins)
# )
#
# print(
#     "Rx DINs found in relevant formulary:",
#     len(matching_dins)
# )
#
# print(
#     "Rx DIN match rate:",
#     round(
#         len(matching_dins) / len(rx_dins) * 100,
#         2
#     ),
#     "%"
# )

formulary_candidates = rx_formulary.merge(
    formulary_v1[
        [
            "Jurisdiction",
            "Drug_program",
            "DIN",
            "Coverage_start_date",
            "Coverage_end_date",
            "Benefit_status",
            "Drug_type",
            "ATC5_code",
            "ATC5_description"
        ]
    ],
    on=[
        "Jurisdiction",
        "Drug_program",
        "DIN"
    ],
    how="left"
)
#
# print(
#     "Rx events before formulary merge:",
#     len(rx_formulary)
# )
#
# print(
#     "Rows after candidate merge:",
#     len(formulary_candidates)
# )

active_formulary = formulary_candidates[
    (
        formulary_candidates["Coverage_start_date"]
        <= formulary_candidates["Fill_Date"]
    )
    &
    (
        formulary_candidates["Coverage_end_date"].isna()
        |
        (
            formulary_candidates["Coverage_end_date"]
            >= formulary_candidates["Fill_Date"]
        )
    )
].copy()

# print(
#     "Date-valid formulary matches:",
#     len(active_formulary)
# )
#
# print(
#     "Unique Rx events with a date-valid match:",
#     active_formulary["Rx_Event_ID"].nunique()
# )

match_counts = (
    active_formulary
    .groupby("Rx_Event_ID")
    .size()
)

# print(
#     "Rx events with exactly 1 active formulary row:",
#     (match_counts == 1).sum()
# )
#
# print(
#     "Rx events with multiple active formulary rows:",
#     (match_counts > 1).sum()
# )
#
# print(
#     "Maximum active formulary rows for one Rx event:",
#     match_counts.max()
# )

formulary_matches = active_formulary[
    [
        "Rx_Event_ID",
        "Patient_ID",
        "Product_ID",
        "DIN",
        "Fill_Date",
        "Jurisdiction",
        "Drug_program",
        "Coverage_start_date",
        "Coverage_end_date",
        "Benefit_status",
        "Drug_type",
        "ATC5_code",
        "ATC5_description"
    ]
].copy()

print(
    "Formulary matches:",
    formulary_matches.shape
)

print(
    "Duplicate Rx Event IDs:",
    formulary_matches["Rx_Event_ID"].duplicated().sum()
)

formulary_lookup = rx_formulary[
    [
        "Rx_Event_ID",
        "Patient_ID",
        "Product_ID",
        "DIN",
        "Fill_Date",
        "Jurisdiction",
        "Drug_program"
    ]
].copy()

formulary_lookup = formulary_lookup.merge(
    formulary_matches[
        [
            "Rx_Event_ID",
            "Coverage_start_date",
            "Coverage_end_date",
            "Benefit_status",
            "Drug_type",
            "ATC5_code",
            "ATC5_description"
        ]
    ],
    on="Rx_Event_ID",
    how="left",
    validate="one_to_one"
)

formulary_lookup["Formulary_Match"] = (
    formulary_lookup["Benefit_status"].notna()
)

# print(
#     "Final formulary lookup:",
#     formulary_lookup.shape
# )
#
# print(
#     "\nFormulary match counts:"
# )
#
# print(
#     formulary_lookup["Formulary_Match"]
#     .value_counts()
# )


formulary_output = (
    Project_root
    / "Data"
    / "processed"
    / "rx_formulary_lookup.csv"
)

formulary_lookup.to_csv(
    formulary_output,
    index=False
)
#
# print(
#     "Formulary lookup saved:",
#     formulary_output
# )
#
# print(
#     "Shape:",
#     formulary_lookup.shape
# )

rx_province_counts = (
    rx_formulary
    .groupby("Province")
    .size()
    .sort_values(ascending=False)
)

print(
    rx_province_counts
)

print(
    "\nNumber of provinces:",
    rx_province_counts.index.nunique()
)

print(
    "\nTotal Rx events:",
    rx_province_counts.sum()
)