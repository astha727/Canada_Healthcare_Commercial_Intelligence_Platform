import pandas as pd
from pathlib import Path
from src.data.data_loader import load_file
import numpy as np
from src.data.hcp_names import HCP_NAMES


project_root = Path(__file__).resolve().parents[2]

hcp_data = (
    project_root
    / "Data"
    / "synthetic"
    / "synthetic_hcp_segmentation_output.csv"
)

hcp = load_file(hcp_data)

# KEEP STABLE HCP ATTRIBUTES

hcp = hcp[
    [
        "HCP_ID",
        "Province",
        "Specialty"
    ]
].copy()

# GENERATE SYNTHETIC HCP NAMES

rng = np.random.default_rng(42)

hcp["HCP_Name"] = rng.choice(
    HCP_NAMES,
    size=len(hcp)
)

# HCP TYPE

hcp["HCP_Type"] = "Physician"

# PRACTICE SETTING

practice_settings = [
    "Hospital",
    "Community Clinic",
    "Private Practice",
    "Academic/Teaching Hospital"
]

hcp["Practice_Setting"] = rng.choice(
    practice_settings,
    size=len(hcp)
)

# FACILITY POOL

province_codes = {
    "Ontario": "ON",
    "Quebec": "QC",
    "British Columbia": "BC",
    "Alberta": "AB",
    "Manitoba": "MB",
    "Saskatchewan": "SK",
    "Nova Scotia": "NS",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Prince Edward Island": "PE",
    "Yukon": "YT",
    "Northwest Territories": "NT",
    "Nunavut": "NU"
}

setting_codes = {
    "Hospital": "HOSP",
    "Academic/Teaching Hospital": "ACAD",
    "Community Clinic": "CLIN",
    "Private Practice": "PRIV"
}

# FACILITY ID

facility_ids = []

for (province, setting), group in hcp.groupby(
    ["Province", "Practice_Setting"]
):
    province_code = province_codes[province]
    setting_code = setting_codes[setting]

    n_hcps = len(group)

    # Aim for roughly 8 HCPs per facility
    n_facilities = max(1, int(np.ceil(n_hcps / 8)))

    facilities = [
        f"FAC_{province_code}_{setting_code}_{i:03d}"
        for i in range(1, n_facilities + 1)
    ]

    assigned_facilities = rng.choice(
        facilities,
        size=n_hcps
    )

    facility_ids.extend(
        zip(group.index, assigned_facilities)
    )

for index, facility_id in facility_ids:
    hcp.loc[index, "Facility_ID"] = facility_id

# YEARS IN PRACTICE

hcp["Years_in_Practice"] = rng.integers(
    1,
    36,
    size=len(hcp)
)

# EXPAND HCP COVERAGE FOR REQUIRED PROVINCE-SPECIALTY COMBINATIONS

additional_hcps = [
    ("Northwest Territories", "Cardiology"),
    ("Northwest Territories", "Internal Medicine"),
    ("Northwest Territories", "Neurology"),
    ("Nunavut", "Cardiology"),
    ("Nunavut", "Internal Medicine"),
    ("Yukon", "Cardiology"),
    ("Yukon", "Internal Medicine"),
    ("Yukon", "Orthopedic Surgery"),
    ("Prince Edward Island", "Neurology"),
]

start_id = len(hcp) + 1

additional_rows = []

for i, (province, specialty) in enumerate(
    additional_hcps,
    start=start_id
):
    additional_rows.append(
        {
            "HCP_ID": f"HCP_{i:04d}",
            "Province": province,
            "Specialty": specialty
        }
    )

additional_hcp_df = pd.DataFrame(additional_rows)

# SYNTHETIC ATTRIBUTES FOR ADDITIONAL HCPS

additional_hcp_df["HCP_Name"] = rng.choice(
    HCP_NAMES,
    size=len(additional_hcp_df)
)

additional_hcp_df["HCP_Type"] = "Physician"

additional_hcp_df["Practice_Setting"] = rng.choice(
    practice_settings,
    size=len(additional_hcp_df)
)

additional_hcp_df["Years_in_Practice"] = rng.integers(
    1,
    36,
    size=len(additional_hcp_df)
)

print("\nAdditional HCPs:")
print(additional_hcp_df)


# FACILITY IDs FOR ADDITIONAL HCPS

additional_hcp_df["Facility_ID"] = ""

for (province, setting), group in additional_hcp_df.groupby(
    ["Province", "Practice_Setting"]
):
    province_code = province_codes[province]
    setting_code = setting_codes[setting]

    facility_id = (
        f"FAC_{province_code}_{setting_code}_001"
    )

    additional_hcp_df.loc[
        group.index,
        "Facility_ID"
    ] = facility_id


# ADD COVERAGE HCPS TO MASTER

hcp = pd.concat(
    [
        hcp,
        additional_hcp_df
    ],
    ignore_index=True
)

print("\nHCP master after coverage expansion:")
print(hcp.shape)


# FINAL HCP MASTER

hcp = hcp[
    [
        "HCP_ID",
        "HCP_Name",
        "Province",
        "Specialty",
        "Facility_ID",
        "HCP_Type",
        "Practice_Setting",
        "Years_in_Practice"
    ]
].copy()

print(hcp.shape)
print(hcp.columns.tolist())
print(hcp.head())

# EXPORT HCP MASTER

output_path = (
    project_root
    / "Data"
    / "processed"
    / "synthetic_hcp_master.csv"
)

hcp.to_csv(output_path, index=False)

print(f"\nHCP master saved to: {output_path}")

