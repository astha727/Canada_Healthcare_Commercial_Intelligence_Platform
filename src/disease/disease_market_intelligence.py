"""
# LIFE SCIENCES COMMERCIAL INTELLIGENCE PLATFORM

## Disease Market Intelligence — Exploratory Analysis

This file is currently being used to explore the relationship between:

**Population → Disease Burden → Geographic Variation → Healthcare Market**

The goal at this stage is to understand the CCDSS disease data properly
before connecting diseases to specialties and market activity.

### Analytical principle

**Python = evidence**
**AI = interpretation**

Python should calculate the underlying metrics and comparisons.
AI can later explain those findings, but should not invent evidence
or make unsupported causal claims.
"""


# PROJECT SETUP

from pathlib import Path

import pandas as pd

from src.data.data_loader import load_file
import numpy as np

def print_module(number, title):
    print("\n"+ "*"*80)
    print(f"MODULE {number} - {title}")
    print("*"*80)


print_module(1, "PROJECT SETUP & DATA LOADING")


"""
# PROJECT SETUP

The project root is determined dynamically from the location of this file.

This allows the code to work regardless of the current working directory
from which the Python file is executed.
"""

project_root = Path(__file__).resolve().parents[2]

market_data = (
    project_root
    / "Data"
    / "synthetic"
    / "market_context.csv"
)

canada_disease_rate = (
    project_root
    / "Data"
    / "raw"
    / "Canada_Disease_Rates.xlsx"
)


"""
# LOAD DATA


Two datasets are currently being explored:

### 1. Market context

A synthetic province × specialty dataset containing variables such as:

- Population
- Physician count
- Physicians per 100,000
- Service volume
- Services per physician

This will eventually provide healthcare-market context.

### 2. CCDSS disease data

The Canadian Chronic Disease Surveillance System dataset contains
disease measures across:

- Conditions
- Data types
- Geographies
- Sex
- Age groups
- Fiscal years

The raw CCDSS file is kept untouched.
"""

market = load_file(market_data)

disease_rate = load_file(canada_disease_rate)

print_module(2, "MARKET CONTEXT")

"""
# MARKET CONTEXT

`Services_per_Physician` provides a simple measure of healthcare activity
within each province-specialty combination.

We use the **median** as the benchmark because it is less influenced by
extreme values than the mean.

### Market Activity Index

The index is:

**Services per Physician / Median Services per Physician**

Interpretation:

- `1.0` = exactly at the median
- `>1.0` = above the median
- `<1.0` = below the median

This is a **relative market-context measure**.

It is not a measure of commercial opportunity by itself.

Missing values are preserved as missing values rather than being treated
as zero.
"""

benchmark_services = market["Services_per_Physician"].median()

market["Market_Activity_Index"] = (
    market["Services_per_Physician"]
    / benchmark_services
)

print("Market benchmark:")
print(benchmark_services)

print("\nAvailable specialties:")
print(sorted(market["Specialty"].unique()))

print_module(3, "CCDSS DATA CLEANING & STRUCTURE")

"""
# CCDSS DATA CLEANING

The CCDSS source contains a non-breaking space in the rate column name.

For example, the source may contain:

`Rate (per 100,000)`

rather than:

`Rate (per 100,000)`

We standardize the column name so it can be referenced consistently
throughout the analysis.

### Missing values

The source contains observations such as `Data not submitted`.

These become missing values when the dataset is loaded.

**NaN does not mean zero.**

We preserve missing values because the reason for missingness must come
from the CCDSS source information rather than being inferred from the
absence of a numeric value.
"""

disease_rate.columns = (
    disease_rate.columns
    .str.replace("\xa0", " ", regex=False)
)

print("\nCCDSS columns:")
print(disease_rate.columns.tolist())


"""
# CCDSS DATA STRUCTURE EXPLORATION

Before calculating any disease metrics, we need to understand the
structure and grain of the dataset.

The expected logical grain is:

**Condition + Data Type + Geography + Sex + Age group + Fiscal year**

If this combination is unique, each row represents one distinct
disease observation at the expected analytical level.
"""

print("\nNumber of rows:")
print(len(disease_rate))

print("\nNumber of conditions:")
print(disease_rate["Condition"].nunique())

print("\nData types:")
print(disease_rate["Data Type"].value_counts())

print("\nGeographies:")
print(disease_rate["Geography"].unique())

print("\nSex categories:")
print(disease_rate["Sex"].unique())

print("\nAge groups:")
print(disease_rate["Age group"].unique())

print("\nFiscal years:")
print(disease_rate["Fiscal year"].unique())


"""
# CCDSS DATA GRAIN CHECK

We explicitly test whether the expected logical grain contains duplicates.

A result of zero means there are no duplicate observations at the
specified grain.
"""

grain_columns = [
    "Condition",
    "Data Type",
    "Geography",
    "Sex",
    "Age group",
    "Fiscal year"
]

duplicates = disease_rate.duplicated(
    subset=grain_columns,
    keep=False
)

print("\nDuplicate rows at expected grain:")
print(duplicates.sum())

print_module(4, "DIABETES DISEASE EXPLORATION")
"""
# DIABETES: PREVALENCE

Prevalence describes how widespread a disease is within a population.

For the initial diabetes analysis, we use:

- **Condition:** Diabetes mellitus
- **Measure:** Age-standardized prevalence
- **Sex:** Both sexes
- **Geography:** Canada or individual provinces/territories

The CCDSS diabetes prevalence measure is reported as a **percentage**.

Although the source dataframe uses the generic column name
`Rate (per 100,000)`, the diabetes prevalence values must be interpreted
according to the source measure definition.

### Why start with prevalence?

Prevalence provides a useful view of the overall disease burden in the
population.

It answers:

> How widespread is the condition?

This is different from incidence, which looks at newly identified cases.
"""

diabetes_prev = disease_rate[
    (
        disease_rate["Condition"]
        == "Diabetes mellitus (types combined), excluding gestational diabetes"
    )
    & (
        disease_rate["Data Type"]
        == "Age-standardized prevalence"
    )
    & (
        disease_rate["Sex"]
        == "Both sexes"
    )
].copy()


"""
# DIABETES: CANADA LONG-TERM PREVALENCE

We first examine the full available Canadian time series.

The comparison is between the first available observation and the latest
available observation.

### Metrics

**Absolute change**

Latest prevalence − First prevalence

Because prevalence is expressed as a percentage, this is reported in
**percentage points**.

**Relative change**

Absolute change / First prevalence × 100

The relative change describes the percentage increase or decrease relative
to the starting value.

These are descriptive endpoint comparisons, not causal estimates.
"""

canada_diabetes = diabetes_prev[
    diabetes_prev["Geography"] == "Canada"
].copy()

first_rate = (
    canada_diabetes["Rate (per 100,000)"]
    .iloc[0]
)

latest_rate = (
    canada_diabetes["Rate (per 100,000)"]
    .iloc[-1]
)

absolute_change = latest_rate - first_rate

percent_change = (
    absolute_change / first_rate
) * 100

print("\nCanada diabetes prevalence:")

print(
    f"First available rate: "
    f"{first_rate:.2f}%"
)

print(
    f"Latest rate: "
    f"{latest_rate:.2f}%"
)

print(
    f"Absolute change: "
    f"{absolute_change:.2f} percentage points"
)

print(
    f"Relative change: "
    f"{percent_change:.1f}%"
)


"""
# DIABETES: CANADA RECENT PREVALENCE

A long-term trend can hide more recent changes.

We therefore examine the recent period from:

**2018–2019 → 2023–2024**

The CCDSS identifies:

**2020–2021 through 2022–2023**

as the COVID-19 pandemic period for this data tool.

Changes during this period should therefore be interpreted cautiously.
"""

recent_years = [
    "2018–2019",
    "2019–2020",
    "2020–2021*",
    "2021–2022*",
    "2022–2023*",
    "2023–2024"
]

canada_recent = canada_diabetes[
    canada_diabetes["Fiscal year"].isin(recent_years)
].copy()

recent_first = (
    canada_recent["Rate (per 100,000)"]
    .iloc[0]
)

recent_latest = (
    canada_recent["Rate (per 100,000)"]
    .iloc[-1]
)

recent_absolute_change = (
    recent_latest - recent_first
)

recent_percent_change = (
    recent_absolute_change / recent_first
) * 100

print("\nRecent Canada diabetes prevalence:")

print(
    f"2018–2019: "
    f"{recent_first:.2f}%"
)

print(
    f"2023–2024: "
    f"{recent_latest:.2f}%"
)

print(
    f"Absolute change: "
    f"{recent_absolute_change:.2f} percentage points"
)

print(
    f"Relative change: "
    f"{recent_percent_change:.2f}%"
)


"""
# DIABETES: INCIDENCE

Incidence measures newly identified cases over a period of time.

For diabetes, we are using:

- **Age-standardized incidence rate**
- **Both sexes**
- **Canada**

This measure is reported per **100,000 population**.

### Important age-group distinction

The diabetes incidence measure uses the age group:

**1+**

The diabetes prevalence measure above uses:

**20+**

Therefore, we should **not directly compare their numerical values**
as though they represent the same population.

We can still analyze prevalence and incidence as two different dimensions
of disease burden.
"""

diabetes_inc = disease_rate[
    (
        disease_rate["Condition"]
        == "Diabetes mellitus (types combined), excluding gestational diabetes"
    )
    & (
        disease_rate["Data Type"]
        == "Age-standardized incidence rate"
    )
    & (
        disease_rate["Sex"]
        == "Both sexes"
    )
    & (
        disease_rate["Geography"]
        == "Canada"
    )
].copy()


"""
# DIABETES: INCIDENCE RANGE

We identify the lowest and highest observed incidence rates in the
available Canadian time series.

This helps us understand the shape and variability of the historical
series before interpreting the recent trend.
"""

min_row = diabetes_inc.loc[
    diabetes_inc["Rate (per 100,000)"].idxmin()
]

max_row = diabetes_inc.loc[
    diabetes_inc["Rate (per 100,000)"].idxmax()
]

print("\nCanada diabetes incidence range:")

print(
    f"Minimum: "
    f"{min_row['Rate (per 100,000)']:.0f} "
    f"in {min_row['Fiscal year']}"
)

print(
    f"Maximum: "
    f"{max_row['Rate (per 100,000)']:.0f} "
    f"in {max_row['Fiscal year']}"
)


"""
# DIABETES: RECENT INCIDENCE

We compare the Canadian incidence rate between:

**2018–2019 → 2023–2024**

The historical series shows a non-linear pattern, including a pronounced
decline during 2020–2021 followed by a rebound.

The recent endpoint comparison therefore needs to be interpreted alongside
the full time series rather than treated as a simple linear trend.
"""

diabetes_inc_recent = diabetes_inc[
    diabetes_inc["Fiscal year"].isin(recent_years)
].copy()

recent_inc_first = (
    diabetes_inc_recent["Rate (per 100,000)"]
    .iloc[0]
)

recent_inc_latest = (
    diabetes_inc_recent["Rate (per 100,000)"]
    .iloc[-1]
)

recent_inc_absolute_change = (
    recent_inc_latest - recent_inc_first
)

recent_inc_percent_change = (
    recent_inc_absolute_change
    / recent_inc_first
) * 100

print("\nRecent Canada diabetes incidence:")

print(
    f"2018–2019: "
    f"{recent_inc_first:.0f} per 100,000"
)

print(
    f"2023–2024: "
    f"{recent_inc_latest:.0f} per 100,000"
)

print(
    f"Absolute change: "
    f"{recent_inc_absolute_change:.0f} per 100,000"
)

print(
    f"Relative change: "
    f"{recent_inc_percent_change:.1f}%"
)


"""
# DIABETES: GEOGRAPHIC VARIATION

We now examine the most recent fiscal year:

**2023–2024**

The purpose is to understand how reported diabetes prevalence varies
across Canadian provinces and territories.

Canada is retained as a national benchmark.

When identifying the highest and lowest provincial/territorial estimates,
Canada itself is excluded because it is not a province or territory.

### Interpretation guardrail

A higher reported prevalence does not automatically mean:

- greater commercial opportunity
- greater healthcare spending
- greater physician activity
- greater unmet need

Those require additional evidence from other datasets.
"""

diabetes_latest = diabetes_prev[
    diabetes_prev["Fiscal year"] == "2023–2024"
].copy()

geo_rates = diabetes_latest.dropna(
    subset=["Rate (per 100,000)"]
).copy()

province_territory_rates = geo_rates[
    geo_rates["Geography"] != "Canada"
].copy()


"""
# DIABETES: HIGHEST AND LOWEST REPORTED ESTIMATES

We identify the highest and lowest **reported** prevalence estimates among
provinces and territories.

The word "reported" is important because some geographies may have
missing data.

Missing data should not be interpreted as zero or automatically assumed
to indicate low disease burden.
"""

highest = province_territory_rates.loc[
    province_territory_rates["Rate (per 100,000)"].idxmax()
]

lowest = province_territory_rates.loc[
    province_territory_rates["Rate (per 100,000)"].idxmin()
]

geo_range = (
    highest["Rate (per 100,000)"]
    - lowest["Rate (per 100,000)"]
)

print("\nDiabetes prevalence by geography, 2023–2024:")

print(
    geo_rates[
        [
            "Geography",
            "Rate (per 100,000)"
        ]
    ].sort_values(
        "Rate (per 100,000)",
        ascending=False
    )
)

print("\nProvince/territory variation:")

print(
    f"Highest reported estimate: "
    f"{highest['Geography']} "
    f"({highest['Rate (per 100,000)']:.2f}%)"
)

print(
    f"Lowest reported estimate: "
    f"{lowest['Geography']} "
    f"({lowest['Rate (per 100,000)']:.2f}%)"
)

print(
    f"Range: "
    f"{geo_range:.2f} percentage points"
)


"""
# NEXT ANALYTICAL STEP

The disease analysis currently answers:

1. **What is the disease burden?**
2. **How has it changed over time?**
3. **How does it vary geographically?**

The next step is to connect disease intelligence to healthcare-market
context.

Before doing that, we need an explicit:

**Condition → Specialty**

mapping.

This mapping should be documented rather than inferred automatically.

Only specialties that actually exist in the synthetic market dataset
should be used.

After that, the analytical chain becomes:

**Disease → Specialty → Province → Market Context → Commercial Signal**

Importantly, disease burden itself is not the commercial opportunity.
It is one input into a broader commercial-intelligence framework.
"""

print_module(5, "DISEASE → SPECIALTY MAPPING")
"""
# DISEASE → SPECIALTY MAPPING VALIDATION

The mapping connects CCDSS disease conditions to the specialty
categories available in the synthetic market-context dataset.

Before using the mapping for commercial analysis, we validate:
- all CCDSS conditions have a mapping
- no disease is mapped more than once
- all specialties exist in market_context.csv
"""

mapping_path = (
    project_root
    /"Data"
    /"processed"
    /"disease_specialty_mapping.csv"
)

disease_mapping = pd.read_csv(mapping_path)

print(disease_mapping.shape)
print(disease_mapping["Condition"].nunique())
print(disease_mapping["Primary_Specialty"].unique())

"""
# DISEASE MARKET JOIN: LATEST DISEASE SNAPSHOT

For the first cross-dataset view, we use:
- Age-standardized prevalence
- Both sexes
- 2023–2024
- Province and territory level

Canada is excluded because the synthetic market-context dataset
contains province/territory rows but no national market row.

This creates the disease-side dataset that will later be linked
to specialty and market context.
"""

disease_latest = disease_rate[
(disease_rate["Data Type"] == "Age-standardized prevalence")
    & (disease_rate["Sex"] == "Both sexes")
    & (disease_rate["Fiscal year"] == "2023–2024")
    & (disease_rate["Geography"] != "Canada")
].copy()

print(disease_latest.shape)
print(disease_latest["Geography"].nunique())
print(disease_latest["Condition"].nunique())

"""
# DISEASE → SPECIALTY MAPPING

This merge connects each CCDSS condition to the specialty
category used by the market-context dataset.

The mapping is a crosswalk to the available market taxonomy.
It does not imply that every patient with a condition receives
care from that specialty.
"""

disease_market = disease_latest.merge(
    disease_mapping,
    on="Condition",
    how="left"
)

print(disease_market.shape)
print(disease_market["Primary_Specialty"].isna().sum())
print(disease_market["Primary_Specialty"].value_counts())


"""
# DISEASE → SPECIALTY → MARKET CONTEXT

This merge connects each disease/geography combination
to the corresponding specialty market in that geography.

Join keys:
- Disease Geography → Market Province
- Primary Specialty → Market Specialty

Market-context values are synthetic and are used only to
demonstrate the commercial-intelligence methodology.
Missing market values are preserved as missing.
"""

disease_market = disease_market.merge(
    market,
    left_on=["Geography", "Primary_Specialty"],
    right_on=["Province", "Specialty"],
    how="left",
    suffixes=("_disease", "_market")
)

print(disease_market.shape)
print(disease_market[[
    "Condition",
    "Geography",
    "Primary_Specialty",
    "Physician_Count",
    "Service_Volume",
    "Services_per_Physician"
]].head(10))

diabetes_market = disease_market[
    disease_market["Condition"] ==
    "Diabetes mellitus (types combined), excluding gestational diabetes"
][[
    "Condition",
    "Geography",
    "Rate (per 100,000)",
    "Primary_Specialty",
    "Physician_Count",
    "Physicians_per_100k",
    "Service_Volume",
    "Services_per_Physician",
    "Market_Activity_Index"
]].copy()

print(diabetes_market)

print(
    disease_market["Province"].isna().sum()
)

print(
    disease_market["Specialty"].isna().sum()
)


print(disease_market.columns.tolist())
print(
    disease_market[
        [
            "Condition",
            "Geography",
            "Primary_Specialty",
            "Rate (per 100,000)",
            "Physician_Count",
            "Physicians_per_100k",
            "Service_Volume",
            "Services_per_Physician",
            "Market_Activity_Index"
        ]
    ].head(20)
)


"""
# INCIDENCE: LATEST DISEASE SNAPSHOT

Create the incidence-side dataset for the latest fiscal year.

We use:
- Age-standardized incidence rate
- Both sexes
- 2023–2024
- Province and territory level

This is kept separate from prevalence because incidence
and prevalence measure different aspects of disease burden
and may use different age groups and units.
"""

disease_incidence_latest = disease_rate[
    (disease_rate["Data Type"] == "Age-standardized incidence rate")
    & (disease_rate["Sex"] == "Both sexes")
    & (disease_rate["Fiscal year"] == "2023–2024")
    & (disease_rate["Geography"] != "Canada")
].copy()

print(disease_incidence_latest.shape)
print(disease_incidence_latest["Condition"].nunique())
print(disease_incidence_latest["Condition"].unique())


print(
    disease_incidence_latest[
        [
            "Condition",
            "Age group",
            "Age group type",
            "Rate (per 100,000)"
        ]
    ].drop_duplicates()
    .sort_values("Condition")
    .to_string(index=False)
)


"""
# INCIDENCE → SPECIALTY MAPPING

Attach the disease-to-specialty crosswalk to the latest
incidence estimates.

Incidence remains a separate measure from prevalence because
conditions use different age groups and incidence is expressed
as a rate per 100,000.
"""

incidence_market = disease_incidence_latest.merge(
    disease_mapping,
    on="Condition",
    how="left"
)

print(incidence_market.shape)
print(incidence_market["Primary_Specialty"].isna().sum())


incidence_market = incidence_market.merge(
    market,
    left_on=["Geography", "Primary_Specialty"],
    right_on=["Province", "Specialty"],
    how="left",
    suffixes=("_disease", "_market")
)

print(incidence_market.shape)
print(incidence_market["Province"].isna().sum())
print(incidence_market["Specialty"].isna().sum())


print(
    incidence_market[
        [
            "Condition",
            "Geography",
            "Age group",
            "Rate (per 100,000)",
            "Primary_Specialty",
            "Physician_Count",
            "Services_per_Physician",
            "Market_Activity_Index"
        ]
    ].head(15)
)
print(
    incidence_market[
        [
            "Condition",
            "Age group",
            "Rate (per 100,000)"
        ]
    ].drop_duplicates()
    .sort_values(["Condition", "Age group"])
)


prevalence_market = disease_market.rename(
    columns={
        "Rate (per 100,000)": "Prevalence_Rate",
        "Age group": "Prevalence_Age_Group",
        "Lower 95%_CI": "Prevalence_Lower_CI",
        "Upper 95%_CI": "Prevalence_Upper_CI"
    }
)

incidence_market = incidence_market.rename(
    columns={
        "Rate (per 100,000)": "Incidence_Rate",
        "Age group": "Incidence_Age_Group",
        "Lower 95%_CI": "Incidence_Lower_CI",
        "Upper 95%_CI": "Incidence_Upper_CI"
    }
)

print(prevalence_market[[
    "Condition",
    "Geography",
    "Prevalence_Rate",
    "Prevalence_Age_Group"
]].head())

print()

print(incidence_market[[
    "Condition",
    "Geography",
    "Incidence_Rate",
    "Incidence_Age_Group"
]].head())

print_module(6, "DISEASE → MARKET EVIDENCE")
#merging incidence and prevalence
disease_market_evidence = prevalence_market.merge(
    incidence_market[
        [
            "Condition",
            "Geography",
            "Incidence_Rate",
            "Incidence_Age_Group",
            "Incidence_Lower_CI",
            "Incidence_Upper_CI"
        ]
    ],
    on=["Condition", "Geography"],
    how="left"
)

print(disease_market_evidence.shape)

print(
    disease_market_evidence["Incidence_Rate"].isna().sum()
)


print(
    disease_market_evidence["Incidence_Rate"].notna().sum()
)

print(
    disease_market_evidence["Incidence_Rate"].isna().sum()
)

incidence_coverage = (
    disease_market_evidence
    .groupby("Condition")
    .agg(
        Geography_Count=("Geography", "count"),
        Incidence_Available=("Incidence_Rate", "count")
    )
    .reset_index()
)

incidence_coverage["Incidence_Missing"] = (
    incidence_coverage["Geography_Count"]
    - incidence_coverage["Incidence_Available"]
)

print(incidence_coverage)


print(
    disease_market_evidence[
        [
            "Condition",
            "Geography",
            "Primary_Specialty",
            "Prevalence_Rate",
            "Prevalence_Age_Group",
            "Incidence_Rate",
            "Incidence_Age_Group",
            "Physician_Count",
            "Physicians_per_100k",
            "Service_Volume",
            "Services_per_Physician",
            "Market_Activity_Index"
        ]
    ].head(20)
)

print(disease_market_evidence.shape)
print(disease_market_evidence.columns.tolist())


"""
# DISEASE-MARKET EVIDENCE CHECK

Before creating commercial signals, inspect the completeness
and structure of the combined evidence table.
"""

print("Shape:", disease_market_evidence.shape)

print("\nMissing values:")
print(
    disease_market_evidence[
        ["Prevalence_Rate", "Incidence_Rate",
         "Physician_Count", "Service_Volume",
         "Services_per_Physician", "Market_Activity_Index"]
    ].isna().sum()
)

print("\nIncidence availability:")
print(
    disease_market_evidence["Incidence_Rate"]
    .notna()
    .value_counts()
)
print("\nIncidence availability by condition:")

print(
    disease_market_evidence
    .groupby("Condition")["Incidence_Rate"]
    .apply(lambda x: x.notna().sum())
    .sort_values()
)

"""
# INCIDENCE EVIDENCE STATUS

Distinguish between conditions that do not have an incidence
measure in the CCDSS data and observations where incidence
exists for the condition but is unavailable for a geography.
"""

conditions_with_no_incidence = [
    "Arthritis",
    "Autism",
    "Use of health services for mental illness and alcohol/drug induced disorders (annual)",
    "Schizophrenia",
    "Use of health services for mood and anxiety disorders (annual)",
    "Use of health services for schizophrenia (annual)"
]

disease_market_evidence["Incidence_Evidence_Status"] = np.select(
    [
        disease_market_evidence["Condition"].isin(
            conditions_with_no_incidence
        ),
        disease_market_evidence["Incidence_Rate"].isna()
    ],
    [
        "Not_available_for_condition",
        "Unavailable_for_geography"
    ],
    default="Available"
)
print(
    disease_market_evidence[
        ["Condition", "Geography", "Incidence_Rate", "Incidence_Evidence_Status"]
    ]
    .groupby(["Condition", "Incidence_Evidence_Status"])
    .size()
)

print_module(7, "EVIDENCE QUALITY & COMPLETENESS")
print("Evidence table shape:", disease_market_evidence.shape)

print("\nMissing values:")
print(
    disease_market_evidence[
        [
            "Prevalence_Rate",
            "Incidence_Rate",
            "Physician_Count",
            "Service_Volume",
            "Services_per_Physician",
            "Market_Activity_Index"
        ]
    ].isna().sum()
)
conditions_with_no_incidence = [
    "Arthritis",
    "Autism",
    "Use of health services for mental illness and alcohol/drug induced disorders (annual)",
    "Schizophrenia",
    "Use of health services for mood and anxiety disorders (annual)",
    "Use of health services for schizophrenia (annual)"
]

disease_market_evidence["Incidence_Evidence_Status"] = np.select(
    [
        disease_market_evidence["Condition"].isin(
            conditions_with_no_incidence
        ),
        disease_market_evidence["Incidence_Rate"].isna()
    ],
    [
        "Not_available_for_condition",
        "Unavailable_for_geography"
    ],
    default="Available"
)
disease_market_evidence["Market_Evidence_Status"] = np.where(
    disease_market_evidence["Service_Volume"].isna(),
    "Unavailable_due_to_service_volume",
    "Available"
)
print("\nIncidence evidence status:")
print(
    disease_market_evidence["Incidence_Evidence_Status"]
    .value_counts()
)

print("\nMarket evidence status:")
print(
    disease_market_evidence["Market_Evidence_Status"]
    .value_counts()
)


print_module(8, "Disease-Market Signals")

disease_market_signals = disease_market_evidence.copy()
disease_market_signals["Prevalence_Percentile"] = (
    disease_market_signals.groupby("Condition")["Prevalence_Rate"].rank(pct=True)
)

disease_market_signals["Geographic_Prevalence_Signal"] = np.select(
    [
        disease_market_signals["Prevalence_Percentile"].isna(),
        disease_market_signals["Prevalence_Percentile"] >= 0.75,
        disease_market_signals["Prevalence_Percentile"] >= 0.50
    ],
    [
        "Evidence unavailable",
        "High relative prevalence",
        "Moderate relative prevalence"
    ],
    default="Lower relative prevalence"
)
print("Disease market signals")
print(
    disease_market_signals[
        [
            "Condition",
            "Geography",
            "Prevalence_Rate",
            "Prevalence_Percentile",
            "Geographic_Prevalence_Signal"
        ]
    ]
    .query("Condition == 'Diabetes mellitus (types combined), excluding gestational diabetes'")
    .sort_values("Prevalence_Rate", ascending=False)
    .to_string(index=False)
)


disease_market_signals["Market_Activity_Percentile"] = (
    disease_market_signals.groupby("Primary_Specialty")["Market_Activity_Index"].rank(pct=True)
)

print_module(9, "DISEASE GEOGRAPHIC PREVALENCE SIGNALS")

signal_summary = (
    disease_market_signals
    .groupby(["Condition", "Geographic_Prevalence_Signal"])
    .size()
    .unstack(fill_value=0)
)

print(signal_summary)


prevalence_geographic_summary = (
    disease_market_signals
    .groupby("Condition")["Prevalence_Rate"]
    .agg(
        Provinces_Reported="count",
        Minimum_Prevalence="min",
        Maximum_Prevalence="max"
    )
    .reset_index()
)

prevalence_geographic_summary["Prevalence_Range"] = (
    prevalence_geographic_summary["Maximum_Prevalence"]
    - prevalence_geographic_summary["Minimum_Prevalence"]
)

print(prevalence_geographic_summary)

prevalence_trend = disease_rate[
    (disease_rate["Data Type"] == "Age-standardized prevalence")
    & (disease_rate["Sex"] == "Both sexes")
    & (disease_rate["Geography"] != "Canada")
].copy()

#print(prevalence_trend.shape)
#print(prevalence_trend["Condition"].nunique())
#print(prevalence_trend["Geography"].nunique())
#print(prevalence_trend["Fiscal year"].nunique())

prevalence_trend["Start_Year"] = (
    prevalence_trend["Fiscal year"]
    .str[:4]
    .astype(int)
)
prevalence_trend = prevalence_trend.sort_values(
    ["Condition", "Geography", "Start_Year"]
)

#print(prevalence_trend[
    #["Condition", "Geography", "Fiscal year", "Start_Year", "Rate (per 100,000)"]
#].head(10))

prevalence_endpoints = (
    prevalence_trend
    .groupby(["Condition", "Geography"])
    .agg(
        Earliest_Year=("Start_Year", "first"),
        Latest_Year=("Start_Year", "last"),
        Earliest_Prevalence=("Rate (per 100,000)", "first"),
        Latest_Prevalence=("Rate (per 100,000)", "last"),
        Years_Observed=("Start_Year", "count")
    )
    .reset_index()
)

prevalence_endpoints["Prevalence_Change"] = (
    prevalence_endpoints["Latest_Prevalence"]
    - prevalence_endpoints["Earliest_Prevalence"]
)



#print(prevalence_endpoints.head(10))
#print(prevalence_endpoints["Prevalence_Change"].describe())

condition_change_summary = (
    prevalence_endpoints
    .groupby("Condition")["Prevalence_Change"]
    .agg(
        Median_Change="median",
        Minimum_Change="min",
        Maximum_Change="max"
    )
    .reset_index()
)

print(condition_change_summary)

prevalence_endpoints["Trend_Direction"] = np.select(
    [
        prevalence_endpoints["Prevalence_Change"] > 0,
        prevalence_endpoints["Prevalence_Change"] < 0,
        prevalence_endpoints["Prevalence_Change"] == 0
    ],
    [
        "Increasing",
        "Decreasing",
        "No change"
    ],
    default="Evidence unavailable"
)
print(prevalence_endpoints["Trend_Direction"].value_counts())

print(
    prevalence_endpoints[
        prevalence_endpoints["Trend_Direction"] == "Evidence unavailable"
    ][
        [
            "Condition",
            "Geography",
            "Earliest_Year",
            "Latest_Year",
            "Earliest_Prevalence",
            "Latest_Prevalence",
            "Prevalence_Change"
        ]
    ]
)

print(
    prevalence_endpoints[
        [
            "Condition",
            "Geography",
            "Earliest_Year",
            "Latest_Year",
            "Earliest_Prevalence",
            "Latest_Prevalence",
            "Prevalence_Change",
            "Trend_Direction"
        ]
    ].head(20)
)

diabetes_trend = prevalence_endpoints[
    prevalence_endpoints["Condition"]
    == "Diabetes mellitus (types combined), excluding gestational diabetes"
].copy()

diabetes_trend = diabetes_trend.sort_values(
    "Prevalence_Change",
    ascending=False
)

print(
    diabetes_trend[
        [
            "Condition",
            "Geography",
            "Earliest_Year",
            "Latest_Year",
            "Earliest_Prevalence",
            "Latest_Prevalence",
            "Prevalence_Change",
            "Trend_Direction"
        ]
    ].to_string(index=False)
)


condition_trend_summary = (
    prevalence_endpoints
    .groupby("Condition")
    .agg(
        Geographies_Reported=("Prevalence_Change", "count"),
        Median_Change=("Prevalence_Change", "median"),
        Minimum_Change=("Prevalence_Change", "min"),
        Maximum_Change=("Prevalence_Change", "max")
    )
    .reset_index()
)

print(condition_trend_summary.to_string(index=False))

print_module(9, "EXPORT ANALYTICAL OUTPUTS")
"""
# ANALYTICAL OUTPUTS

The exploratory analysis produces reusable analytical datasets.

Raw source files remain in `Data/raw/`.
Synthetic source data remains in `Data/synthetic/`.

Calculated analytical datasets are exported to `Data/processed/`
so that later parts of the platform can reuse them without modifying
the original source data.
"""

processed_output = (
    project_root
    / "Data"
    / "processed"
)

print("\nOutput folder:")
print(processed_output)

disease_market_evidence_path = (
    processed_output
    / "disease_market_evidence.csv"
)

disease_market_evidence.to_csv(
    disease_market_evidence_path,
    index=False
)

print("\nExported:")
print(disease_market_evidence_path)
"""
# VERIFY EXPORTED EVIDENCE

We reload the exported file and confirm that:
- the file can be read successfully
- the expected number of rows is preserved
- the expected analytical columns are present
"""

verified_evidence = pd.read_csv(
    disease_market_evidence_path
)

print("\nVerified exported evidence:")
print("Shape:", verified_evidence.shape)

print("\nColumns:")
print(verified_evidence.columns.tolist())


disease_market_signals_path = (
    processed_output
    / "disease_market_signals.csv"
)

disease_market_signals.to_csv(
    disease_market_signals_path,
    index=False
)

print("\nExported:")
print(disease_market_signals_path)

disease_prevalence_trends_path = (
    processed_output
    / "disease_prevalence_trends.csv"
)

prevalence_endpoints.to_csv(
    disease_prevalence_trends_path,
    index=False
)

print("\nExported:")
print(disease_prevalence_trends_path)