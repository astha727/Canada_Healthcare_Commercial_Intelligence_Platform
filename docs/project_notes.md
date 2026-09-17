# Project Notes

## 2026-09-17 — CCDSS Disease Intelligence

### Dataset
- Source: Canadian Chronic Disease Surveillance System (CCDSS)
- File: `Data/raw/Canada_Disease_Rates.xlsx`
- 22 conditions
- 24 fiscal years: 2000–01 to 2023–24
- 14 geographies
- 3 sex categories
- Confirmed grain:
  Condition + Data Type + Geography + Sex + Age group + Fiscal year

### Data-quality decisions
- Do not treat NaN as zero.
- Preserve raw CCDSS data.
- COVID period: 2020–21 to 2022–23.
- CCDSS estimates now use 2021 Canadian population for age standardization.
- Historical estimates may change with surveillance updates.

### Diabetes analysis

#### Prevalence
- Measure: Age-standardized prevalence
- Sex: Both sexes
- Canada
- Age group: 20+
- 2000–01: 5.29%
- 2023–24: 9.40%
- Absolute change: +4.11 percentage points
- Relative change: +77.7%

#### Recent prevalence
- 2018–19: 9.05%
- 2023–24: 9.40%
- Absolute change: +0.35 percentage points
- Relative change: +3.87%

#### Incidence
- Measure: Age-standardized incidence rate
- Sex: Both sexes
- Geography: Canada
- Age group: 1+
- 2018–19: 649 per 100,000
- 2023–24: 753 per 100,000
- Relative change: +16.0%
- 2020–21: 605 per 100,000
- COVID-period decline followed by rebound

#### Geographic variation
- Year: 2023–24
- Highest reported estimate: Manitoba, 11.12%
- Lowest reported estimate: Quebec, 7.54%
- Range: 3.58 percentage points
- New Brunswick: unavailable
- Nunavut: 7.77%

### Interpretation guardrails
- Do not infer causality from prevalence/incidence trends.
- Do not attribute changes to immigration without supporting evidence.
- Disease burden does not automatically equal commercial opportunity.
- Disease-to-specialty relationships must be explicitly documented.

### Next step
Create condition → specialty mapping using only specialties available in `market_context.csv`.