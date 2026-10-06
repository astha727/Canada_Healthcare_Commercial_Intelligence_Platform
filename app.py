import pandas as pd
import streamlit as st

import numpy as np
from tabs.executive_overview import show_executive_overview
from tabs.market_disease import show_market_disease
from tabs.patient_journey import show_patient_journey
from tabs.hcp_engagement import show_hcp_engagement
from tabs.access import show_access
from tabs.comeptitor_products import show_products_competition
from tabs.commercial_opportunities import show_commercial_opportunities
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "Data" / "processed"
RAW_DATA_PATH = PROJECT_ROOT / "Data" / "raw"


st.set_page_config(
    page_title="Life Sciences Commercial Intelligence Platform",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_processed_data():

    patients = pd.read_csv(
        DATA_PATH / "synthetic_patient_master.csv"
    )

    diagnoses = pd.read_csv(
        DATA_PATH / "synthetic_patient_diagnoses.csv"
    )

    treatments = pd.read_csv(
        DATA_PATH / "synthetic_patient_treatments.csv"
    )

    rx_events = pd.read_csv(
        DATA_PATH / "synthetic_patient_rx_events.csv"
    )

    hcp_master = pd.read_csv(
        DATA_PATH / "synthetic_hcp_master.csv"
    )

    pharmacy_claims = pd.read_csv(
        DATA_PATH / "synthetic_pharmacy_claims.csv"
    )

    medical_claims = pd.read_csv(
        DATA_PATH / "synthetic_medical_claims.csv"
    )

    opportunities = pd.read_csv(
        DATA_PATH / "commercial_opportunity_analytics.csv"
    )

    product_master = pd.read_csv(
        DATA_PATH / "drug_product_master.csv"
    )

    return (
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
    )


(
    patients,
    diagnoses,
    treatments,
    rx_events,
    hcp_master,
    pharmacy_claims,
    medical_claims,
    opportunities,
    product_master,
) = load_processed_data()


@st.cache_data
def load_ccdss():

    data = pd.read_excel(
        RAW_DATA_PATH / "Canada_Disease_Rates.xlsx"
    )

    data.columns = (
        data.columns
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
    )

    return data


ccdss = load_ccdss()


st.title("Life Sciences Commercial Intelligence Platform")

st.caption(
    "Synthetic commercial intelligence across market, disease, patients, HCPs, "
    "access, products, and opportunities."
)
# CCDSS reference age groups used for V1 disease calibration

disease_reference_ages = {
    "Acute myocardial infarction": "20+",
    "Asthma": "1+",
    "Chronic obstructive pulmonary disease": "35+",
    "Dementia, including Alzheimer disease": "65+",
    "Diabetes mellitus (types combined), excluding gestational diabetes": "1+",
    "Epilepsy": "1+",
    "Heart failure": "40+",
    "Hypertension": "20+",
    "Ischemic heart disease": "20+",
    "Multiple sclerosis": "20+",
    "Osteoarthritis": "20+",
    "Osteoporosis": "40+",
    "Parkinsonism, including Parkinson disease": "40+",
    "Rheumatoid arthritis": "16+",
    "Schizophrenia": "10+",
    "Stroke": "20+"
}

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">
            Life Sciences
        </div>
        <div class="sidebar-brand-subtitle">
            Commercial Intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="sidebar-section-label">ANALYTICS</div>',
    unsafe_allow_html=True,
)

section_options = [
    "Executive Overview",
    "Market & Disease",
    "Patient Journey",
    "HCP & Engagement",
    "Access",
    "Products & Competition",
    "Commercial Opportunities",
]

section_icons = {
    "Executive Overview": "◈",
    "Market & Disease": "⌁",
    "Patient Journey": "◉",
    "HCP & Engagement": "◎",
    "Access": "▣",
    "Products & Competition": "◆",
    "Commercial Opportunities": "↗",
}

selected_section = st.sidebar.radio(
    "Navigate",
    section_options,
    format_func=lambda section: (
        f"{section_icons[section]}   {section}"
    ),
    label_visibility="collapsed",
)

st.sidebar.markdown(
    """
    <div class="sidebar-footer">
        <div class="sidebar-footer-label">DATA ENVIRONMENT</div>
        <div class="sidebar-footer-value">
            Synthetic & Public Reference Data
        </div>
        <div class="sidebar-footer-note">
            For analytical demonstration only
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       SIDEBAR
    -------------------------------------------------------- */

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }


    /* --------------------------------------------------------
       BRAND
    -------------------------------------------------------- */

    .sidebar-brand {
        padding: 0.25rem 0.5rem 1.5rem 0.5rem;
    }

    .sidebar-brand-title {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .sidebar-brand-subtitle {
        font-size: 0.78rem;
        opacity: 0.62;
        margin-top: 0.25rem;
        line-height: 1.3;
    }


    /* --------------------------------------------------------
       SECTION LABEL
    -------------------------------------------------------- */

    .sidebar-section-label {
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        opacity: 0.45;
        padding: 0 0.5rem 0.55rem 0.5rem;
    }


    /* --------------------------------------------------------
       REMOVE DEFAULT RADIO CIRCLES
    -------------------------------------------------------- */

    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.18rem;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        border-radius: 0.45rem;
        padding: 0.55rem 0.65rem;
        margin: 0;
        transition: background-color 0.15s ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(37, 99, 235, 0.06);
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label
    [data-testid="stMarkdownContainer"] p {
        font-size: 0.84rem;
        line-height: 1.2;
    }

    [data-testid="stSidebar"] div[role="radiogroup"]
    label > div:first-child {
        display: none;
    }


    /* --------------------------------------------------------
       SELECTED NAVIGATION ITEM
    -------------------------------------------------------- */

    [data-testid="stSidebar"] div[role="radiogroup"]
    label:has(input:checked) {
        background: rgba(37, 99, 235, 0.10);
        border-left: 3px solid #2563EB;
    }

    [data-testid="stSidebar"] div[role="radiogroup"]
    label:has(input:checked)
    [data-testid="stMarkdownContainer"] p {
        font-weight: 650;
    }


    /* --------------------------------------------------------
       FOOTER
    -------------------------------------------------------- */

    .sidebar-footer {
        margin-top: 2rem;
        padding: 0.85rem 0.65rem;
        border-top: 1px solid rgba(128, 128, 128, 0.15);
    }

    .sidebar-footer-label {
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        opacity: 0.45;
    }

    .sidebar-footer-value {
        font-size: 0.72rem;
        margin-top: 0.35rem;
        opacity: 0.75;
    }

    .sidebar-footer-note {
        font-size: 0.64rem;
        margin-top: 0.2rem;
        opacity: 0.45;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# Commercial Opportunity filter
filtered_opportunities = opportunities.copy()
# Diagnosis filter
filtered_diagnoses = diagnoses.copy()
# Treatment filter
filtered_treatments = treatments.copy()

disease_display_names = {
        "Acute myocardial infarction": "Acute MI",
        "Heart failure": "Heart failure",
        "Hypertension": "Hypertension",
        "Ischemic heart disease": "Ischemic heart disease",
        "Stroke": "Stroke",
        "Epilepsy": "Epilepsy",
        "Multiple sclerosis": "Multiple sclerosis",
        "Parkinsonism, including Parkinson disease": "Parkinsonism",
        "Dementia, including Alzheimer disease": "Dementia",
        "Diabetes mellitus (types combined), excluding gestational diabetes": "Diabetes",
        "Asthma": "Asthma",
        "Chronic obstructive pulmonary disease": "COPD",
        "Schizophrenia": "Schizophrenia",
        "Osteoarthritis": "Osteoarthritis",
        "Rheumatoid arthritis": "Rheumatoid arthritis",
        "Osteoporosis": "Osteoporosis"
    }

# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================
if selected_section == "Executive Overview":

    show_executive_overview(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )


# ============================================================
# MARKET & DISEASE
# ============================================================
elif selected_section == "Market & Disease":

    show_market_disease(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )


# ============================================================
# PATIENT JOURNEY
# ============================================================

elif selected_section == "Patient Journey":

    show_patient_journey(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )

# ============================================================
# HCP
# ============================================================

elif selected_section == "HCP & Engagement":

    show_hcp_engagement(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )


# ============================================================
# ACCESS
# ============================================================

elif selected_section == "Access":

    show_access(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )


# ============================================================
# PRODUCTS & COMPETITION
# ============================================================

elif selected_section == "Products & Competition":

    show_products_competition(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )


# ============================================================
# COMMERCIAL OPPORTUNITIES
# ============================================================

elif selected_section == "Commercial Opportunities":

    show_commercial_opportunities(
        patients,
        diagnoses,
        treatments,
        rx_events,
        hcp_master,
        pharmacy_claims,
        medical_claims,
        opportunities,
        product_master,
        filtered_opportunities,
        filtered_diagnoses,
        filtered_treatments,
        ccdss,
        disease_reference_ages,
        disease_display_names,
    )



