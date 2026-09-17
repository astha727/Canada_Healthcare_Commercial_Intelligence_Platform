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