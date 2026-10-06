import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def show_patient_journey(
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
):



    st.subheader("Patient & Journey")

    st.caption(
        "Understand the observed patient population, treatment journey, "
        "persistence, patient characteristics, and individual patient records."
    )

    # ------------------------------------------------------------
    # PATIENT JOURNEY COHORT
    # ------------------------------------------------------------

    st.markdown("### Patient Cohort")

    st.write(
        "Select a patient cohort once, then explore its population, "
        "treatment journey, persistence, and individual patient records."
    )

    cohort_filter_col1, cohort_filter_col2, cohort_filter_col3 = st.columns(3)

    with cohort_filter_col1:

        cohort_conditions = sorted(
            diagnoses["Condition"]
            .dropna()
            .map(disease_display_names)
            .dropna()
            .unique()
            .tolist()
        )

        selected_cohort_condition = st.selectbox(
            "Condition",
            ["All"] + cohort_conditions,
            key="patient_journey_cohort_condition",
        )

    with cohort_filter_col2:

        cohort_provinces = sorted(
            patients["Province"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_cohort_province = st.selectbox(
            "Province",
            ["All"] + cohort_provinces,
            key="patient_journey_cohort_province",
        )

    with cohort_filter_col3:

        cohort_therapies = sorted(
            treatments["Therapy_Class"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_cohort_therapy = st.selectbox(
            "Therapy Class",
            ["All"] + cohort_therapies,
            key="patient_journey_cohort_therapy",
        )

    # ------------------------------------------------------------
    # BUILD SHARED PATIENT COHORT
    # ------------------------------------------------------------

    cohort_patient_ids = set(
        diagnoses["Patient_ID"]
        .dropna()
        .unique()
    )

    if selected_cohort_condition != "All":
        condition_patient_ids = set(
            diagnoses.loc[
                diagnoses["Condition"]
                .map(disease_display_names)
                == selected_cohort_condition,
                "Patient_ID",
            ]
                .dropna()
                .unique()
        )

        cohort_patient_ids &= condition_patient_ids

    if selected_cohort_province != "All":
        province_patient_ids = set(
            patients.loc[
                patients["Province"].astype(str)
                == selected_cohort_province,
                "Patient_ID",
            ]
            .dropna()
            .unique()
        )

        cohort_patient_ids &= province_patient_ids

    if selected_cohort_therapy != "All":
        therapy_patient_ids = set(
            treatments.loc[
                treatments["Therapy_Class"].astype(str)
                == selected_cohort_therapy,
                "Patient_ID",
            ]
            .dropna()
            .unique()
        )

        cohort_patient_ids &= therapy_patient_ids

    # ------------------------------------------------------------
    # SHARED COHORT DATASETS
    # ------------------------------------------------------------

    cohort_patients = patients[
        patients["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    # Keep ALL diagnoses for the selected patients.
    # This is important for the comorbidity analysis.
    cohort_diagnoses = diagnoses[
        diagnoses["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    # Treatment data is scoped to the selected patient cohort.
    cohort_treatments = treatments[
        treatments["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    # If Therapy Class is selected, treatment records are also
    # restricted to that therapy class.
    if selected_cohort_therapy != "All":
        cohort_treatments = cohort_treatments[
            cohort_treatments["Therapy_Class"].astype(str)
            == selected_cohort_therapy
            ].copy()

    cohort_treatment_ids = set(
        cohort_treatments["Treatment_ID"]
        .dropna()
        .unique()
    )

    # Rx and pharmacy claims associated with the selected
    # treatment cohort.
    cohort_rx = rx_events[
        rx_events["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    if selected_cohort_therapy != "All":
        cohort_rx = cohort_rx[
            cohort_rx["Treatment_ID"].isin(cohort_treatment_ids)
        ].copy()

    cohort_pharmacy = pharmacy_claims[
        pharmacy_claims["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    if selected_cohort_therapy != "All":
        cohort_pharmacy = cohort_pharmacy[
            cohort_pharmacy["Treatment_ID"].isin(cohort_treatment_ids)
        ].copy()

    # Medical claims remain patient-level so that medical activity
    # for the selected cohort is retained.
    cohort_medical = medical_claims[
        medical_claims["Patient_ID"].isin(cohort_patient_ids)
    ].copy()

    # ------------------------------------------------------------
    # COHORT SUMMARY
    # ------------------------------------------------------------

    cohort_patient_count = len(cohort_patient_ids)

    cohort_condition_label = (
        selected_cohort_condition
        if selected_cohort_condition != "All"
        else "All conditions"
    )

    cohort_province_label = (
        selected_cohort_province
        if selected_cohort_province != "All"
        else "All provinces"
    )

    cohort_therapy_label = (
        selected_cohort_therapy
        if selected_cohort_therapy != "All"
        else "All therapy classes"
    )

    st.markdown(
        f"**Selected cohort:** "
        f"{cohort_condition_label} · "
        f"{cohort_province_label} · "
        f"{cohort_therapy_label}"
    )

    st.caption(
        f"{cohort_patient_count:,} patients in the selected cohort."
    )

    if cohort_patient_count == 0:
        st.warning(
            "No patients match the selected cohort. "
            "Try broadening one or more filters."
        )

    # ------------------------------------------------------------
    # PATIENT JOURNEY TABS
    # ------------------------------------------------------------

    population_tab, treatment_journey_tab, persistence_tab, explorer_tab = st.tabs(
        [
            "Population",
            "Treatment Journey",
            "Persistence & Adherence",
            "Patient Explorer",
        ]
    )

    with population_tab:

        st.markdown("### Patient Population")

        st.write(
            "Understand the observed patient population, demographics, "
            "disease distribution, geographic concentration, and product landscape."
        )

        # ------------------------------------------------------------
        # PATIENT COHORT COUNTS
        # ------------------------------------------------------------

        diagnosed_patient_ids = set(
            cohort_diagnoses["Patient_ID"]
            .dropna()
        )

        treatment_patient_ids = set(
            cohort_treatments["Patient_ID"]
            .dropna()
        )

        rx_patient_ids = set(
            cohort_rx["Patient_ID"]
            .dropna()
        )

        pharmacy_patient_ids = set(
            cohort_pharmacy["Patient_ID"]
            .dropna()
        )

        medical_patient_ids = set(
            cohort_medical["Patient_ID"]
            .dropna()
        )

        observed_patient_ids = (
                diagnosed_patient_ids
                | treatment_patient_ids
                | rx_patient_ids
                | pharmacy_patient_ids
                | medical_patient_ids
        )

        observed_patient_count = len(
            observed_patient_ids
        )

        diagnosed_patient_count = len(
            diagnosed_patient_ids
        )

        treated_patient_count = len(
            treatment_patient_ids
        )

        treatment_gap_patient_count = len(
            diagnosed_patient_ids
            - treatment_patient_ids
        )

        treatment_rate = (
            treated_patient_count
            / diagnosed_patient_count * 100
            if diagnosed_patient_count > 0
            else 0
        )

        # ------------------------------------------------------------
        # NEW PATIENTS
        # ------------------------------------------------------------

        cohort_diagnoses["Diagnosis_Date"] = pd.to_datetime(
            cohort_diagnoses["Diagnosis_Date"],
            errors="coerce"
        )

        first_diagnosis = (
            cohort_diagnoses
            .dropna(subset=["Patient_ID", "Diagnosis_Date"])
            .groupby("Patient_ID")["Diagnosis_Date"]
            .min()
            .reset_index()
        )

        analysis_end_date = first_diagnosis["Diagnosis_Date"].max()

        if pd.notna(analysis_end_date):

            new_patient_start_date = (
                    analysis_end_date - pd.DateOffset(years=1)
            )

            new_patient_count = first_diagnosis[
                first_diagnosis["Diagnosis_Date"]
                > new_patient_start_date
                ].shape[0]

        else:

            new_patient_count = 0

        # ------------------------------------------------------------
        # POPULATION OVERVIEW
        # ------------------------------------------------------------

        st.markdown("### Population Overview")

        metric_col1, metric_col2, metric_col3, metric_col4 = (
            st.columns(4)
        )

        with metric_col1:

            st.metric(
                "Total Patients",
                f"{observed_patient_count:,}"
            )

        with metric_col2:

            st.metric(
                "Diagnosed Patients",
                f"{diagnosed_patient_count:,}"
            )

        with metric_col3:

            st.metric(
                "Undergoing Treatment",
                f"{treated_patient_count:,}"
            )

        with metric_col4:

            st.metric(
                "New Patients",
                f"{new_patient_count:,}"
            )

        st.caption(
            "New patients represent patients with an observed diagnosis "
            "date in the selected synthetic cohort. These measures "
            "describe observed synthetic records and are not estimates "
            "of the total real-world disease population."
        )

        # ------------------------------------------------------------
        # DEMOGRAPHICS + CONDITION
        # ------------------------------------------------------------

        demographics_col, condition_col = st.columns(2)

        with demographics_col:

            st.markdown("### Patient Demographics")

            # The selected cohort already contains the relevant
            # patient IDs after applying Condition + Province +
            # Therapy Class.

            demographic_patients = patients[
                patients["Patient_ID"].isin(cohort_patient_ids)
            ].copy()

            # Calculate age using the platform's 2024 snapshot date.
            demographic_patients["Birth_Date"] = pd.to_datetime(
                demographic_patients["Birth_Date"],
                errors="coerce"
            )

            snapshot_date = pd.Timestamp("2024-07-01")

            demographic_patients["Age"] = (
                    snapshot_date.year
                    - demographic_patients["Birth_Date"].dt.year
                    - (
                            (demographic_patients["Birth_Date"].dt.month > snapshot_date.month)
                            |
                            (
                                    (demographic_patients["Birth_Date"].dt.month == snapshot_date.month)
                                    &
                                    (demographic_patients["Birth_Date"].dt.day > snapshot_date.day)
                            )
                    ).astype(int)
            )

            def age_group(age):

                if pd.isna(age):
                    return "Unknown"

                elif age < 18:
                    return "<18"

                elif age <= 24:
                    return "18–24"

                elif age <= 34:
                    return "25–34"

                elif age <= 44:
                    return "35–44"

                elif age <= 54:
                    return "45–54"

                elif age <= 64:
                    return "55–64"

                else:
                    return "65+"




            demographic_patients["Age_Group"] = (
                demographic_patients["Age"]
                .apply(age_group)
            )

            age_order = [
                "<18",
                "18–24",
                "25–34",
                "35–44",
                "45–54",
                "55–64",
                "65+",
                "Unknown"
            ]

            demographic_patients["Age_Group"] = pd.Categorical(
                demographic_patients["Age_Group"],
                categories=age_order,
                ordered=True
            )

            demographic_summary = (
                demographic_patients
                .groupby(
                    ["Age_Group", "Sex_at_Birth"],
                    observed=False
                )
                .size()
                .reset_index(name="Patient_Count")
            )

            if demographic_summary["Patient_Count"].sum() == 0:

                st.info(
                    "No patient demographic data are available under "
                    "the selected criteria."
                )

            else:

                fig_demographics = px.bar(
                    demographic_summary,
                    x="Age_Group",
                    y="Patient_Count",
                    color="Sex_at_Birth",
                    barmode="stack",
                    category_orders={
                        "Age_Group": age_order
                    },
                    labels={
                        "Age_Group": "Age Group",
                        "Patient_Count": "Patients",
                        "Sex_at_Birth": "Sex at Birth"
                    }
                )

                fig_demographics.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(
                        color="#43AADB"
                    ),
                    xaxis=dict(
                        title="Age Group",
                        showgrid=False
                    ),
                    yaxis=dict(
                        title="Patients",
                        gridcolor="rgba(120,120,120,0.15)"
                    ),
                    legend=dict(
                        title="Sex at Birth"
                    ),
                    margin=dict(
                        l=10,
                        r=10,
                        t=10,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig_demographics,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

        with condition_col:

            st.markdown("### Population by Condition and Comorbidity")

            patients_by_condition = (
                cohort_diagnoses
                .groupby("Condition")["Patient_ID"]
                .nunique()
                .reset_index(name="Patients")
            )

            patients_by_condition["Condition"] = (
                patients_by_condition["Condition"]
                .map(disease_display_names)
            )

            patients_by_condition = (
                patients_by_condition
                .sort_values("Patients", ascending=True)
            )

            if patients_by_condition.empty:

                st.info(
                    "No observed patients are available for the "
                    "selected criteria."
                )

            else:

                fig_population_condition = px.bar(
                    patients_by_condition,
                    x="Patients",
                    y="Condition",
                    orientation="h",
                )

                fig_population_condition.update_layout(
                    height=400,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    font=dict(
                        color="#43AADB"
                    ),
                    margin=dict(
                        l=10,
                        r=20,
                        t=20,
                        b=40
                    ),
                    xaxis=dict(
                        title="Population",
                        title_font=dict(
                            color="#43AADB"
                        ),
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        showgrid=True,
                        gridcolor="rgba(120,120,120,0.15)"
                    ),
                    yaxis=dict(
                        title=None,
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        showgrid=False
                    )
                )

                st.plotly_chart(
                    fig_population_condition,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

        # ------------------------------------------------------------
        # MAP + PRODUCT LANDSCAPE
        # ------------------------------------------------------------

        map_col, product_col = st.columns(2)

        with map_col:

            st.markdown("### Geographic Distribution")

            population_patient_master = patients[
                patients["Patient_ID"]
                .isin(observed_patient_ids)
            ].copy()

            patients_by_province = (
                population_patient_master
                .groupby("Province")["Patient_ID"]
                .nunique()
                .reset_index(name="Patients")
            )

            if patients_by_province.empty:

                st.info(
                    "No geographic patient data are available under "
                    "the selected criteria."
                )

            else:

                # Canadian province / territory abbreviations
                province_codes = {
                    "Alberta": "AB",
                    "British Columbia": "BC",
                    "Manitoba": "MB",
                    "New Brunswick": "NB",
                    "Newfoundland and Labrador": "NL",
                    "Nova Scotia": "NS",
                    "Ontario": "ON",
                    "Prince Edward Island": "PE",
                    "Quebec": "QC",
                    "Saskatchewan": "SK",
                    "Northwest Territories": "NT",
                    "Nunavut": "NU",
                    "Yukon": "YT",
                }

                patients_by_province["Province Code"] = (
                    patients_by_province["Province"]
                    .map(province_codes)
                )



                fig_province = px.bar(
                    patients_by_province.sort_values(
                        "Patients",
                        ascending=True
                    ),
                    x="Patients",
                    y="Province",
                    orientation="h",
                )

                fig_province.update_layout(
                    height=400,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    font=dict(
                        color="#43AADB"
                    ),
                    margin=dict(
                        l=10,
                        r=20,
                        t=20,
                        b=40
                    ),
                    xaxis=dict(
                        title="Population",
                        title_font=dict(
                            color="#43AADB"
                        ),
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        showgrid=True,
                        gridcolor="rgba(120,120,120,0.15)"
                    ),
                    yaxis=dict(
                        title=None,
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        showgrid=False
                    )
                )

                st.plotly_chart(
                    fig_province,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

        with product_col:

            st.markdown("### Product Landscape - Condition and Comobidity")

            product_patient_ids = set(
                cohort_treatments["Patient_ID"]
                .dropna()
            )

            product_treatments = cohort_treatments[
                cohort_treatments["Patient_ID"]
                .isin(product_patient_ids)
            ].copy()

            # Add product names
            product_treatments = product_treatments.merge(
                product_master[
                    [
                        "Product_ID",
                        "Brand_Name"
                    ]
                ].drop_duplicates("Product_ID"),
                on="Product_ID",
                how="left"
            )



            product_patient_counts = (
                product_treatments[
                    [
                        "Patient_ID",
                        "Product_ID",
                        "Brand_Name"
                    ]
                ]
                .dropna(subset=["Patient_ID", "Product_ID"])
                .drop_duplicates()
                .groupby(
                    [
                        "Product_ID",
                        "Brand_Name"
                    ]
                )["Patient_ID"]
                .nunique()
                .reset_index(name="Patients")
            )

            if product_patient_counts.empty:

                st.info(
                    "No observed product data are available under "
                    "the selected criteria."
                )

            else:

                product_patient_counts = (
                    product_patient_counts
                    .sort_values(
                        "Patients",
                        ascending=False
                    )
                )

                fig_products = px.pie(
                    product_patient_counts,
                    names="Brand_Name",
                    values="Patients",
                    hole=0.55,
                )

                fig_products.update_layout(
                    height=400,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(
                        color="#43AADB"
                    ),
                    showlegend=True,
                    legend=dict(
                        title="Product",
                        font=dict(
                            color="#43AADB"
                        )
                    ),
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=20
                    )
                )

                fig_products.update_traces(
                    textinfo="percent",
                    hovertemplate=(
                        "Product: %{label}<br>"
                        "Patients: %{value:,}<br>"
                        "Share: %{percent}"
                        "<extra></extra>"
                    )
                )

                st.plotly_chart(
                    fig_products,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.caption(
                    "Share of observed treated patients by product. "
                    "Each patient is counted once per observed product."
                )

        # ------------------------------------------------------------
        # DIAGNOSIS → TREATMENT GAP
        # ------------------------------------------------------------

        st.markdown("### Diagnosis → Treatment Gap")

        gap_total = diagnosed_patient_count

        gap_treated = treated_patient_count

        gap_no_observed_treatment = treatment_gap_patient_count

        gap_df = pd.DataFrame({
            "Stage": [
                "Diagnosed",
                "Observed Treatment",
                "Diagnosed — No Observed Treatment"
            ],
            "Patients": [
                gap_total,
                gap_treated,
                gap_no_observed_treatment
            ]
        })

        gap_col1, gap_col2 = st.columns([2, 1])

        with gap_col1:

            fig_gap = px.bar(
                gap_df,
                x="Patients",
                y="Stage",
                orientation="h",
            )

            fig_gap.update_layout(
                height=300,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(
                    color="#43AADB"
                ),
                margin=dict(
                    l=10,
                    r=20,
                    t=20,
                    b=30
                ),
                xaxis=dict(
                    title="Patients",
                    title_font=dict(
                        color="#43AADB"
                    ),
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    showgrid=True,
                    gridcolor="rgba(120,120,120,0.15)"
                ),
                yaxis=dict(
                    title=None,
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    showgrid=False
                )
            )

            st.plotly_chart(
                fig_gap,
                use_container_width=True,
                config={"displayModeBar": False}
            )

        with gap_col2:

            st.metric(
                "Treatment Rate",
                f"{treatment_rate:.1f}%"
            )

            st.metric(
                "Diagnosed — No Observed Treatment",
                f"{gap_no_observed_treatment:,}"
            )

            st.caption(
                "This is an observed treatment-gap signal. "
                "A missing treatment record does not imply clinical "
                "undertreatment, treatment need, or eligibility."
            )


    # ================================================================
    # OTHER PATIENT SUB-TABS
    # ================================================================

    with treatment_journey_tab:

        st.markdown("### Treatment Journey")

        st.write(
            "Observed patient progression from diagnosis through treatment initiation "
            "and subsequent treatment activity."
        )

        # ------------------------------------------------------------
        # USE SHARED PATIENT JOURNEY COHORT
        # ------------------------------------------------------------

        journey_diagnoses = cohort_diagnoses.copy()
        journey_treatments = cohort_treatments.copy()
        journey_rx = cohort_rx.copy()
        journey_pharmacy = cohort_pharmacy.copy()
        journey_medical = cohort_medical.copy()

        # ------------------------------------------------------------
        # PATIENT COHORTS
        # ------------------------------------------------------------

        journey_diagnosis_patient_ids = set(
            journey_diagnoses["Patient_ID"].dropna()
        )

        journey_treatment_patient_ids = set(
            journey_treatments["Patient_ID"].dropna()
        )

        journey_rx_patient_ids = set(
            journey_rx["Patient_ID"].dropna()
        )

        journey_observed_patient_ids = (
                journey_diagnosis_patient_ids
                | journey_treatment_patient_ids
                | journey_rx_patient_ids
        )

        if not journey_observed_patient_ids:

            st.info(
                "No observed patient journeys are available for the selected cohort."
            )

        else:

            # --------------------------------------------------------
            # TIME TO OBSERVED TREATMENT
            # --------------------------------------------------------

            st.markdown("### Time to Observed Treatment")

            diagnosis_dates = (
                journey_diagnoses[
                    [
                        "Patient_ID",
                        "Diagnosis_Date"
                    ]
                ]
                .copy()
            )

            diagnosis_dates["Diagnosis_Date"] = pd.to_datetime(
                diagnosis_dates["Diagnosis_Date"],
                errors="coerce"
            )

            first_diagnosis = (
                diagnosis_dates
                .dropna(
                    subset=[
                        "Patient_ID",
                        "Diagnosis_Date"
                    ]
                )
                .groupby("Patient_ID")["Diagnosis_Date"]
                .min()
                .reset_index()
            )

            treatment_dates = (
                journey_treatments[
                    [
                        "Patient_ID",
                        "Treatment_Start_Date"
                    ]
                ]
                .copy()
            )

            treatment_dates["Treatment_Start_Date"] = pd.to_datetime(
                treatment_dates["Treatment_Start_Date"],
                errors="coerce"
            )

            first_treatment = (
                treatment_dates
                .dropna(
                    subset=[
                        "Patient_ID",
                        "Treatment_Start_Date"
                    ]
                )
                .groupby("Patient_ID")["Treatment_Start_Date"]
                .min()
                .reset_index()
            )

            time_to_treatment = first_diagnosis.merge(
                first_treatment,
                on="Patient_ID",
                how="inner"
            )

            time_to_treatment["Days_to_Treatment"] = (
                    time_to_treatment["Treatment_Start_Date"]
                    - time_to_treatment["Diagnosis_Date"]
            ).dt.days

            time_to_treatment = time_to_treatment[
                time_to_treatment["Days_to_Treatment"] >= 0
                ].copy()

            if time_to_treatment.empty:

                st.info(
                    "No patients have both an observed diagnosis and treatment start "
                    "date in the selected cohort."
                )

            else:

                median_days = (
                    time_to_treatment["Days_to_Treatment"]
                    .median()
                )

                ttt_col1, ttt_col2 = st.columns(2)

                with ttt_col1:

                    st.metric(
                        "Median Days to Observed Treatment",
                        f"{median_days:.0f}"
                    )

                with ttt_col2:

                    st.metric(
                        "Patients with Observed Treatment",
                        f"{len(time_to_treatment):,}"
                    )

                fig_ttt = px.histogram(
                    time_to_treatment,
                    x="Days_to_Treatment",
                    nbins=30,
                )

                fig_ttt.update_layout(
                    height=360,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#43AADB"),

                    xaxis=dict(
                        title="Days from Diagnosis to Observed Treatment",
                        title_font=dict(color="#43AADB"),
                        tickfont=dict(color="#43AADB"),
                        showgrid=False
                    ),

                    yaxis=dict(
                        title="Patients",
                        title_font=dict(color="#43AADB"),
                        tickfont=dict(color="#43AADB"),
                        showgrid=True,
                        gridcolor="rgba(120,120,120,0.15)"
                    ),

                    margin=dict(
                        l=20,
                        r=20,
                        t=20,
                        b=50
                    )
                )

                st.plotly_chart(
                    fig_ttt,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.caption(
                    "Time to treatment is calculated from the earliest observed diagnosis "
                    "to the earliest observed treatment start in the selected synthetic cohort."
                )
            # ------------------------------------------------------------
            # PRODUCT SWITCHING
            # ------------------------------------------------------------

            st.markdown("### Product Switching")

            switching_data = journey_treatments[
                [
                    "Patient_ID",
                    "Product_ID",
                    "Treatment_Start_Date"
                ]
            ].copy()

            switching_data["Treatment_Start_Date"] = pd.to_datetime(
                switching_data["Treatment_Start_Date"],
                errors="coerce"
            )

            switching_data = switching_data.dropna(
                subset=[
                    "Patient_ID",
                    "Product_ID",
                    "Treatment_Start_Date"
                ]
            )

            switching_data = switching_data.sort_values(
                [
                    "Patient_ID",
                    "Treatment_Start_Date"
                ]
            )

            # Previous product for each patient
            switching_data["Previous_Product_ID"] = (
                switching_data
                .groupby("Patient_ID")["Product_ID"]
                .shift(1)
            )

            # Keep only actual product changes
            product_switch_events = switching_data[
                switching_data["Previous_Product_ID"].notna()
                & (
                        switching_data["Product_ID"]
                        != switching_data["Previous_Product_ID"]
                )
                ].copy()

            if product_switch_events.empty:

                st.info(
                    "No observed product switching is available under "
                    "the current filters."
                )

            else:

                # --------------------------------------------------------
                # MAP PRODUCT IDs TO BRAND NAMES
                # --------------------------------------------------------

                product_name_lookup = (
                    product_master[
                        [
                            "Product_ID",
                            "Brand_Name"
                        ]
                    ]
                    .drop_duplicates("Product_ID")
                    .set_index("Product_ID")["Brand_Name"]
                )

                product_switch_events["From_Product"] = (
                    product_switch_events["Previous_Product_ID"]
                    .map(product_name_lookup)
                )

                product_switch_events["To_Product"] = (
                    product_switch_events["Product_ID"]
                    .map(product_name_lookup)
                )

                # Fall back to Product_ID if a product name is unavailable
                product_switch_events["From_Product"] = (
                    product_switch_events["From_Product"]
                    .fillna(
                        product_switch_events["Previous_Product_ID"]
                    )
                )

                product_switch_events["To_Product"] = (
                    product_switch_events["To_Product"]
                    .fillna(
                        product_switch_events["Product_ID"]
                    )
                )

                # Create readable switch label
                product_switch_events["Switch"] = (
                        product_switch_events["From_Product"].astype(str)
                        + " → "
                        + product_switch_events["To_Product"].astype(str)
                )

                # --------------------------------------------------------
                # COUNT UNIQUE PATIENTS PER SWITCH
                # --------------------------------------------------------

                product_switch_summary = (
                    product_switch_events[
                        [
                            "Patient_ID",
                            "Switch"
                        ]
                    ]
                    .drop_duplicates()
                    .groupby("Switch")["Patient_ID"]
                    .nunique()
                    .reset_index(name="Patients")
                    .sort_values(
                        "Patients",
                        ascending=False
                    )
                    .head(10)
                )

                if product_switch_summary.empty:

                    st.info(
                        "No observed product switching is available under "
                        "the current filters."
                    )

                else:

                    product_switch_summary = (
                        product_switch_summary
                        .sort_values(
                            "Patients",
                            ascending=True
                        )
                    )

                    fig_switching = px.bar(
                        product_switch_summary,
                        x="Patients",
                        y="Switch",
                        orientation="h",
                        text="Patients"
                    )

                    fig_switching.update_traces(
                        textposition="outside"
                    )

                    fig_switching.update_layout(
                        xaxis_title="Patients",
                        yaxis_title="",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(
                            color="#43AADB"
                        ),
                        xaxis=dict(
                            tickfont=dict(
                                color="#43AADB"
                            ),
                            title_font=dict(
                                color="#43AADB"
                            ),
                            gridcolor="rgba(120,120,120,0.15)"
                        ),
                        yaxis=dict(
                            tickfont=dict(
                                color="#43AADB"
                            ),
                            title_font=dict(
                                color="#43AADB"
                            ),
                            showgrid=False
                        ),
                        showlegend=False
                    )

                    st.plotly_chart(
                        fig_switching,
                        use_container_width=True,
                        config={"displayModeBar": False}
                    )

                    st.caption(
                        f"{product_switch_events['Patient_ID'].nunique():,} patients "
                        "have an observed change from one product to another. "
                        "Switches are identified chronologically from treatment episodes; "
                        "repeated records for the same product are not counted as switches."
                    )

            # --------------------------------------------------------
            # TREATMENT PATHWAYS + STATUS
            # --------------------------------------------------------

            pathway_col, status_col = st.columns([1, 1])

            with pathway_col:

                st.markdown("### Treatment Pathways")

                pathway_treatments = journey_treatments[
                    [
                        "Patient_ID",
                        "Therapy_Class",
                        "Treatment_Start_Date"
                    ]
                ].copy()

                pathway_treatments["Treatment_Start_Date"] = pd.to_datetime(
                    pathway_treatments["Treatment_Start_Date"],
                    errors="coerce"
                )

                pathway_treatments = pathway_treatments.dropna(
                    subset=[
                        "Patient_ID",
                        "Therapy_Class",
                        "Treatment_Start_Date"
                    ]
                )

                pathway_treatments = pathway_treatments.sort_values(
                    [
                        "Patient_ID",
                        "Treatment_Start_Date"
                    ]
                )

                pathway_rows = []

                for patient_id, patient_group in pathway_treatments.groupby(
                        "Patient_ID"
                ):

                    therapy_sequence = (
                        patient_group["Therapy_Class"]
                        .astype(str)
                        .tolist()
                    )

                    # Collapse consecutive duplicate therapies.
                    collapsed_sequence = []

                    for therapy in therapy_sequence:

                        if (
                                not collapsed_sequence
                                or collapsed_sequence[-1] != therapy
                        ):
                            collapsed_sequence.append(
                                therapy
                            )

                    if not collapsed_sequence:
                        continue

                    pathway_rows.append({
                        "Patient_ID": patient_id,
                        "Pathway": " → ".join(
                            collapsed_sequence
                        )
                    })

                pathway_df = pd.DataFrame(
                    pathway_rows
                )

                if pathway_df.empty:

                    st.info(
                        "No observed treatment pathways are available under the current filters."
                    )

                else:

                    pathway_summary = (
                        pathway_df[
                            [
                                "Patient_ID",
                                "Pathway"
                            ]
                        ]
                        .drop_duplicates()
                        .groupby("Pathway")["Patient_ID"]
                        .nunique()
                        .reset_index(name="Patients")
                        .sort_values(
                            "Patients",
                            ascending=False
                        )
                        .head(8)
                    )

                    pathway_summary = pathway_summary.sort_values(
                        "Patients",
                        ascending=True
                    )

                    fig_pathways = px.bar(
                        pathway_summary,
                        x="Patients",
                        y="Pathway",
                        orientation="h",
                    )

                    fig_pathways.update_layout(
                        height=420,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#43AADB"),

                        xaxis=dict(
                            title="Patients",
                            title_font=dict(color="#43AADB"),
                            tickfont=dict(color="#43AADB"),
                            showgrid=True,
                            gridcolor="rgba(120,120,120,0.15)"
                        ),

                        yaxis=dict(
                            title=None,
                            tickfont=dict(color="#43AADB"),
                            showgrid=False
                        ),

                        margin=dict(
                            l=20,
                            r=20,
                            t=20,
                            b=40
                        )
                    )

                    st.plotly_chart(
                        fig_pathways,
                        use_container_width=True,
                        config={"displayModeBar": False}
                    )

                    st.caption(
                        "Top observed therapy-class sequences across treatment episodes. "
                        "Consecutive records for the same therapy are collapsed."
                    )

            with status_col:

                st.markdown("### Treatment Status")

                treatment_status = (
                    journey_treatments["Treatment_Status"]
                    .value_counts()
                    .reset_index()
                )

                treatment_status.columns = [
                    "Treatment Status",
                    "Treatments"
                ]

                fig_status = px.bar(
                    treatment_status,
                    x="Treatment Status",
                    y="Treatments",
                )

                fig_status.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#43AADB"),

                    xaxis=dict(
                        title=None,
                        tickfont=dict(color="#43AADB"),
                        showgrid=False
                    ),

                    yaxis=dict(
                        title="Observed Treatments",
                        title_font=dict(color="#43AADB"),
                        tickfont=dict(color="#43AADB"),
                        showgrid=True,
                        gridcolor="rgba(120,120,120,0.15)"
                    ),

                    margin=dict(
                        l=20,
                        r=20,
                        t=20,
                        b=50
                    )
                )

                st.plotly_chart(
                    fig_status,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.caption(
                    "Treatment episode status across observed treatment records. "
                    "A patient may have more than one treatment episode."
                )

    with persistence_tab:

        st.markdown("### Persistence & Adherence")

        st.write(
            "Observed treatment continuation and refill activity across "
            "the selected synthetic patient cohort."
        )

        # ------------------------------------------------------------
        # USE SHARED PATIENT JOURNEY COHORT
        # ------------------------------------------------------------

        persistence_treatments = cohort_treatments.copy()
        persistence_rx = cohort_rx.copy()

        persistence_treatments["Treatment_Start_Date"] = pd.to_datetime(
            persistence_treatments["Treatment_Start_Date"],
            errors="coerce"
        )

        persistence_treatments["Treatment_End_Date"] = pd.to_datetime(
            persistence_treatments["Treatment_End_Date"],
            errors="coerce"
        )

        persistence_rx["Fill_Date"] = pd.to_datetime(
            persistence_rx["Fill_Date"],
            errors="coerce"
        )

        # ------------------------------------------------------------
        # FILTER RX EVENTS TO OBSERVED TREATMENTS
        # ------------------------------------------------------------

        persistence_treatment_ids = set(
            persistence_treatments["Treatment_ID"]
            .dropna()
        )

        persistence_rx = persistence_rx[
            persistence_rx["Treatment_ID"].isin(
                persistence_treatment_ids
            )
        ].copy()

        # ------------------------------------------------------------
        # KPI METRICS
        # ------------------------------------------------------------

        persistence_patient_ids = set(
            persistence_treatments["Patient_ID"]
            .dropna()
        )

        treated_patient_count = len(
            persistence_patient_ids
        )

        observed_treatment_days = pd.to_numeric(
            persistence_treatments["Observed_Treatment_Days"],
            errors="coerce"
        )

        median_treatment_duration = (
            observed_treatment_days.median()
            if not observed_treatment_days.dropna().empty
            else 0
        )

        # Patients with more than one treatment episode
        treatment_episode_counts = (
            persistence_treatments
            .groupby("Patient_ID")["Treatment_ID"]
            .nunique()
        )

        persistent_patient_count = len(
            treatment_episode_counts[
                treatment_episode_counts > 1
                ]
        )

        # Patients with only one observed treatment episode
        single_episode_patient_count = len(
            treatment_episode_counts[
                treatment_episode_counts == 1
                ]
        )

        # ------------------------------------------------------------
        # REFILL CONTINUITY
        # ------------------------------------------------------------

        refill_counts = (
            persistence_rx
            .groupby("Patient_ID")["Rx_Event_ID"]
            .count()
        )

        refill_counts = refill_counts.reindex(
            persistence_patient_ids,
            fill_value=0
        )

        refill_gap_patient_count = 0

        if not persistence_rx.empty:
            refill_dates = (
                persistence_rx[
                    [
                        "Patient_ID",
                        "Fill_Date"
                    ]
                ]
                .dropna()
                .sort_values(
                    [
                        "Patient_ID",
                        "Fill_Date"
                    ]
                )
            )

            refill_dates["Previous_Fill_Date"] = (
                refill_dates
                .groupby("Patient_ID")["Fill_Date"]
                .shift(1)
            )

            refill_dates["Days_Between_Fills"] = (
                    refill_dates["Fill_Date"]
                    - refill_dates["Previous_Fill_Date"]
            ).dt.days

            refill_gap_patients = set(
                refill_dates.loc[
                    refill_dates["Days_Between_Fills"] > 90,
                    "Patient_ID"
                ]
            )

            refill_gap_patient_count = len(
                refill_gap_patients
            )

        # ------------------------------------------------------------
        # KPI ROW
        # ------------------------------------------------------------

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        with kpi_col1:
            st.metric(
                "Patients with Observed Treatment",
                f"{treated_patient_count:,}"
            )

        with kpi_col2:
            st.metric(
                "Patients with Multiple Episodes",
                f"{persistent_patient_count:,}"
            )

        with kpi_col3:
            st.metric(
                "Patients with Refill Gap >90 Days",
                f"{refill_gap_patient_count:,}"
            )

        with kpi_col4:
            st.metric(
                "Median Observed Treatment Days",
                f"{median_treatment_duration:,.0f}"
            )

        # ------------------------------------------------------------
        # PERSISTENCE OVER TIME
        # ------------------------------------------------------------

        st.markdown("### Persistence Over Time")

        persistence_curve = []

        persistence_thresholds = [
            30,
            90,
            180,
            365
        ]

        for threshold in persistence_thresholds:
            persistent_patients = (
                persistence_treatments[
                    persistence_treatments[
                        "Observed_Treatment_Days"
                    ] >= threshold
                    ]["Patient_ID"]
                .nunique()
            )

            persistence_rate = (
                persistent_patients
                / treated_patient_count
                * 100
                if treated_patient_count > 0
                else 0
            )

            persistence_curve.append(
                {
                    "Days": threshold,
                    "Patients": persistent_patients,
                    "Persistence_Rate": persistence_rate
                }
            )

        persistence_curve = pd.DataFrame(
            persistence_curve
        )

        if persistence_curve.empty:

            st.info(
                "No observed treatment duration data are available "
                "under the selected criteria."
            )

        else:

            fig_persistence = px.line(
                persistence_curve,
                x="Days",
                y="Persistence_Rate",
                markers=True
            )

            fig_persistence.update_layout(
                xaxis_title="Days Since Treatment Start",
                yaxis_title="Patients Remaining on Observed Treatment (%)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#43AADB"
                ),
                xaxis=dict(
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    title_font=dict(
                        color="#43AADB"
                    ),
                    gridcolor="rgba(120,120,120,0.15)"
                ),
                yaxis=dict(
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    title_font=dict(
                        color="#43AADB"
                    ),
                    gridcolor="rgba(120,120,120,0.15)"
                ),
                showlegend=False
            )

            st.plotly_chart(
                fig_persistence,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.caption(
                "Share of treated patients with observed treatment duration "
                "reaching each time threshold. This is an observed synthetic "
                "persistence signal, not a validated adherence measure."
            )

        # ------------------------------------------------------------
        # TREATMENT DURATION DISTRIBUTION
        # ------------------------------------------------------------

        st.markdown("### Treatment Duration Distribution")

        duration_data = persistence_treatments[
            [
                "Patient_ID",
                "Treatment_ID",
                "Observed_Treatment_Days"
            ]
        ].dropna(
            subset=["Observed_Treatment_Days"]
        ).copy()

        duration_data["Duration_Bucket"] = pd.cut(
            duration_data["Observed_Treatment_Days"],
            bins=[
                -1,
                29,
                89,
                179,
                364,
                729,
                float("inf")
            ],
            labels=[
                "<30 days",
                "30–89 days",
                "90–179 days",
                "180–364 days",
                "365–729 days",
                "730+ days"
            ]
        )

        duration_summary = (
            duration_data
            .groupby(
                "Duration_Bucket",
                observed=False
            )["Patient_ID"]
            .nunique()
            .reset_index(name="Patients")
        )

        fig_duration = px.bar(
            duration_summary,
            x="Duration_Bucket",
            y="Patients",
            text="Patients"
        )

        fig_duration.update_traces(
            textposition="outside"
        )

        fig_duration.update_layout(
            xaxis_title="Observed Treatment Duration",
            yaxis_title="Patients",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#43AADB"
            ),
            xaxis=dict(
                tickfont=dict(
                    color="#43AADB"
                ),
                title_font=dict(
                    color="#43AADB"
                ),
                showgrid=False
            ),
            yaxis=dict(
                tickfont=dict(
                    color="#43AADB"
                ),
                title_font=dict(
                    color="#43AADB"
                ),
                gridcolor="rgba(120,120,120,0.15)"
            ),
            showlegend=False
        )

        st.plotly_chart(
            fig_duration,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        st.caption(
            "Distribution of observed treatment duration across treatment episodes. "
            "A patient may contribute more than one episode."
        )

        # ------------------------------------------------------------
        # REFILL CONTINUITY + PERSISTENCE BY THERAPY
        # ------------------------------------------------------------

        refill_col, therapy_col = st.columns(2)

        with refill_col:

            st.markdown("### Refill Continuity")

            refill_summary = pd.DataFrame(
                {
                    "Refill Category": [
                        "Initial fill only",
                        "2–3 fills",
                        "4–11 fills",
                        "12+ fills"
                    ],
                    "Patients": [
                        (refill_counts == 1).sum(),
                        refill_counts.between(2, 3).sum(),
                        refill_counts.between(4, 11).sum(),
                        (refill_counts >= 12).sum()
                    ]
                }
            )

            fig_refills = px.bar(
                refill_summary,
                x="Refill Category",
                y="Patients",
                text="Patients"
            )

            fig_refills.update_traces(
                textposition="outside"
            )

            fig_refills.update_layout(
                xaxis_title="Observed Refill Activity",
                yaxis_title="Patients",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#43AADB"
                ),
                xaxis=dict(
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    title_font=dict(
                        color="#43AADB"
                    ),
                    showgrid=False
                ),
                yaxis=dict(
                    tickfont=dict(
                        color="#43AADB"
                    ),
                    title_font=dict(
                        color="#43AADB"
                    ),
                    gridcolor="rgba(120,120,120,0.15)"
                ),
                showlegend=False
            )

            st.plotly_chart(
                fig_refills,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.caption(
                "Patients grouped by the number of observed Rx events. "
                "Refill count alone does not establish medication adherence."
            )

        with therapy_col:

            st.markdown("### Persistence by Therapy Class")

            therapy_persistence = (
                persistence_treatments
                .groupby("Therapy_Class")[
                    "Observed_Treatment_Days"
                ]
                .median()
                .reset_index(
                    name="Median_Days"
                )
                .sort_values(
                    "Median_Days",
                    ascending=True
                )
            )

            if therapy_persistence.empty:

                st.info(
                    "No therapy-level persistence data are available."
                )

            else:

                fig_therapy_persistence = px.bar(
                    therapy_persistence,
                    x="Median_Days",
                    y="Therapy_Class",
                    orientation="h",
                    text="Median_Days"
                )

                fig_therapy_persistence.update_traces(
                    texttemplate="%{text:.0f}",
                    textposition="outside"
                )

                fig_therapy_persistence.update_layout(
                    xaxis_title="Median Observed Treatment Days",
                    yaxis_title="",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(
                        color="#43AADB"
                    ),
                    xaxis=dict(
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        title_font=dict(
                            color="#43AADB"
                        ),
                        gridcolor="rgba(120,120,120,0.15)"
                    ),
                    yaxis=dict(
                        tickfont=dict(
                            color="#43AADB"
                        ),
                        title_font=dict(
                            color="#43AADB"
                        ),
                        showgrid=False
                    ),
                    showlegend=False
                )

                st.plotly_chart(
                    fig_therapy_persistence,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.caption(
                    "Median observed treatment duration by therapy class. "
                    "These values describe synthetic treatment records and "
                    "are not clinical adherence benchmarks."
                )

    with explorer_tab:

        st.markdown("### Patient Explorer")

        st.write(
            "Filter patients within the selected cohort to identify "
            "specific clinical, treatment, and access patterns."
        )

        # ------------------------------------------------------------
        # BUILD PATIENT-LEVEL DATA FROM SHARED COHORT
        # ------------------------------------------------------------

        explorer_patients = cohort_patients.copy()
        explorer_diagnoses = cohort_diagnoses.copy()
        explorer_treatments = cohort_treatments.copy()
        explorer_rx = cohort_rx.copy()
        explorer_pharmacy = cohort_pharmacy.copy()
        explorer_medical = cohort_medical.copy()

        explorer_diagnoses["Condition_Display"] = (
            explorer_diagnoses["Condition"]
            .map(disease_display_names)
        )

        explorer_treatments["Condition_Display"] = (
            explorer_treatments["Condition"]
            .map(disease_display_names)
        )

        explorer_treatments["Treatment_Start_Date"] = pd.to_datetime(
            explorer_treatments["Treatment_Start_Date"],
            errors="coerce"
        )

        explorer_treatments["Treatment_End_Date"] = pd.to_datetime(
            explorer_treatments["Treatment_End_Date"],
            errors="coerce"
        )

        explorer_rx["Fill_Date"] = pd.to_datetime(
            explorer_rx["Fill_Date"],
            errors="coerce"
        )

        # ------------------------------------------------------------
        # EXPLORER FILTER VALUES
        # ------------------------------------------------------------

        explorer_condition_options = sorted(
            explorer_diagnoses["Condition_Display"]
            .dropna()
            .unique()
        )

        explorer_province_options = sorted(
            explorer_patients["Province"]
            .dropna()
            .unique()
        )

        explorer_therapy_options = sorted(
            explorer_treatments["Therapy_Class"]
            .dropna()
            .unique()
        )

        explorer_product_lookup = (
            product_master[
                [
                    "Product_ID",
                    "Brand_Name"
                ]
            ]
            .drop_duplicates("Product_ID")
        )

        explorer_product_lookup["Brand_Name"] = (
            explorer_product_lookup["Brand_Name"]
            .fillna(
                explorer_product_lookup["Product_ID"]
            )
        )

        explorer_product_name_lookup = (
            explorer_product_lookup
            .set_index("Product_ID")["Brand_Name"]
            .to_dict()
        )

        explorer_product_options = sorted(
            explorer_treatments["Product_ID"]
            .map(explorer_product_name_lookup)
            .dropna()
            .unique()
        )

        # ------------------------------------------------------------
        # START WITH SHARED COHORT PATIENTS
        # ------------------------------------------------------------

        explorer_patient_ids = set(
            cohort_patient_ids
        )


        filtered_explorer_patients = explorer_patients[
            explorer_patients["Patient_ID"]
            .isin(explorer_patient_ids)
        ].copy()

        filtered_explorer_diagnoses = explorer_diagnoses[
            explorer_diagnoses["Patient_ID"]
            .isin(explorer_patient_ids)
        ].copy()

        filtered_explorer_treatments = explorer_treatments[
            explorer_treatments["Patient_ID"]
            .isin(explorer_patient_ids)
        ].copy()

        filtered_explorer_rx = explorer_rx[
            explorer_rx["Patient_ID"]
            .isin(explorer_patient_ids)
        ].copy()

        filtered_explorer_pharmacy = explorer_pharmacy[
            explorer_pharmacy["Patient_ID"]
            .isin(explorer_patient_ids)
        ].copy()

        # ------------------------------------------------------------
        # PATIENT-LEVEL SUMMARY
        # ------------------------------------------------------------

        if filtered_explorer_patients.empty:

            st.info(
                "No patients match the selected criteria."
            )

        else:

            # --------------------------------------------------------
            # DIAGNOSIS SUMMARY
            # --------------------------------------------------------

            diagnosis_summary = (
                filtered_explorer_diagnoses
                .groupby("Patient_ID")["Condition_Display"]
                .apply(
                    lambda x: ", ".join(
                        sorted(
                            set(
                                x.dropna()
                            )
                        )
                    )
                )
                .reset_index(
                    name="Conditions"
                )
            )

            # --------------------------------------------------------
            # TREATMENT SUMMARY
            # --------------------------------------------------------

            treatment_summary = (
                filtered_explorer_treatments
                .sort_values(
                    [
                        "Patient_ID",
                        "Treatment_Start_Date"
                    ]
                )
                .groupby("Patient_ID")
                .agg(
                    Therapy_Class=(
                        "Therapy_Class",
                        lambda x: ", ".join(
                            sorted(
                                set(
                                    x.dropna()
                                )
                            )
                        )
                    ),
                    Treatment_Episodes=(
                        "Treatment_ID",
                        "nunique"
                    ),
                    Active_Treatments=(
                        "Treatment_Status",
                        lambda x: (
                                x == "Active"
                        ).sum()
                    )
                )
                .reset_index()
            )

            # --------------------------------------------------------
            # PRODUCT SUMMARY
            # --------------------------------------------------------

            product_summary = (
                filtered_explorer_treatments
                .assign(
                    Brand_Name=lambda x:
                    x["Product_ID"]
                    .map(explorer_product_name_lookup)
                )
                .groupby("Patient_ID")["Brand_Name"]
                .apply(
                    lambda x: ", ".join(
                        dict.fromkeys(
                            x.dropna()
                        )
                    )
                )
                .reset_index(
                    name="Products"
                )
            )

            # --------------------------------------------------------
            # RX SUMMARY
            # --------------------------------------------------------

            rx_summary = (
                filtered_explorer_rx
                .groupby("Patient_ID")
                .agg(
                    Rx_Fills=(
                        "Rx_Event_ID",
                        "nunique"
                    ),
                    Initial_Fills=(
                        "Rx_Event_Type",
                        lambda x: (
                                x == "Initial Fill"
                        ).sum()
                    ),
                    Last_Fill=(
                        "Fill_Date",
                        "max"
                    )
                )
                .reset_index()
            )

            # --------------------------------------------------------
            # CLAIM SUMMARY
            # --------------------------------------------------------

            claim_summary = (
                filtered_explorer_pharmacy
                .groupby("Patient_ID")
                .agg(
                    Paid_Claims=(
                        "Claim_Status",
                        lambda x: (
                                x == "Paid"
                        ).sum()
                    ),
                    Partial_Claims=(
                        "Claim_Status",
                        lambda x: (
                                x == "Partial"
                        ).sum()
                    ),
                    Rejected_Claims=(
                        "Claim_Status",
                        lambda x: (
                                x == "Rejected"
                        ).sum()
                    )
                )
                .reset_index()
            )

            # --------------------------------------------------------
            # SWITCHING SIGNAL
            # --------------------------------------------------------

            switching_data = (
                filtered_explorer_treatments[
                    [
                        "Patient_ID",
                        "Condition",
                        "Product_ID",
                        "Treatment_Start_Date"
                    ]
                ]
                .dropna()
                .sort_values(
                    [
                        "Patient_ID",
                        "Condition",
                        "Treatment_Start_Date"
                    ]
                )
                .copy()
            )

            switching_data["Previous_Product_ID"] = (
                switching_data
                .groupby(
                    [
                        "Patient_ID",
                        "Condition"
                    ]
                )["Product_ID"]
                .shift(1)
            )

            switching_data["Product_Switch"] = (
                    switching_data["Previous_Product_ID"].notna()
                    & (
                            switching_data["Product_ID"]
                            != switching_data["Previous_Product_ID"]
                    )
            )

            switch_summary = (
                switching_data
                .groupby("Patient_ID")["Product_Switch"]
                .sum()
                .reset_index(
                    name="Product_Switches"
                )
            )

            # --------------------------------------------------------
            # COMBINE PATIENT SUMMARY
            # --------------------------------------------------------

            explorer_table = (
                filtered_explorer_patients[
                    [
                        "Patient_ID",
                        "Province",
                        "Sex_at_Birth",
                        "Patient_Status"
                    ]
                ]
                .merge(
                    diagnosis_summary,
                    on="Patient_ID",
                    how="left"
                )
                .merge(
                    treatment_summary,
                    on="Patient_ID",
                    how="left"
                )
                .merge(
                    product_summary,
                    on="Patient_ID",
                    how="left"
                )
                .merge(
                    rx_summary,
                    on="Patient_ID",
                    how="left"
                )
                .merge(
                    claim_summary,
                    on="Patient_ID",
                    how="left"
                )
                .merge(
                    switch_summary,
                    on="Patient_ID",
                    how="left"
                )
            )

            # --------------------------------------------------------
            # CLEAN SUMMARY
            # --------------------------------------------------------

            explorer_table["Treatment_Episodes"] = (
                explorer_table["Treatment_Episodes"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Active_Treatments"] = (
                explorer_table["Active_Treatments"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Rx_Fills"] = (
                explorer_table["Rx_Fills"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Product_Switches"] = (
                explorer_table["Product_Switches"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Paid_Claims"] = (
                explorer_table["Paid_Claims"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Partial_Claims"] = (
                explorer_table["Partial_Claims"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Rejected_Claims"] = (
                explorer_table["Rejected_Claims"]
                .fillna(0)
                .astype(int)
            )

            explorer_table["Last_Fill"] = pd.to_datetime(
                explorer_table["Last_Fill"],
                errors="coerce"
            )

            # ------------------------------------------------------------
            # PATIENT SIGNALS
            # ------------------------------------------------------------

            explorer_table["Signal_Score"] = 0

            # Treatment gap / no observed treatment
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Treatment_Episodes"] == 0
                                              ).astype(int) * 2

            # Multiple treatment episodes
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Treatment_Episodes"] > 1
                                              ).astype(int) * 1

            # Product switching
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Product_Switches"] > 0
                                              ).astype(int) * 1

            # Refill / Rx activity
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Rx_Fills"] == 0
                                              ).astype(int) * 2

            # Rejected claims
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Rejected_Claims"] > 0
                                              ).astype(int) * 2

            # Partial claims
            explorer_table["Signal_Score"] += (
                                                      explorer_table["Partial_Claims"] > 0
                                              ).astype(int) * 1

            explorer_table["Signal_Tier"] = pd.cut(
                explorer_table["Signal_Score"],
                bins=[-1, 1, 3, 10],
                labels=[
                    "Stable",
                    "Moderate Signal",
                    "High Signal"
                ]
            )

            def build_patient_signals(row):

                signals = []

                if row["Treatment_Episodes"] == 0:
                    signals.append("Treatment gap")

                if row["Product_Switches"] > 0:
                    signals.append("Product transition")

                if row["Rx_Fills"] == 0:
                    signals.append("No observed Rx activity")

                if row["Rejected_Claims"] > 0:
                    signals.append("Access friction")

                if row["Partial_Claims"] > 0:
                    signals.append("Partial claim activity")

                if row["Treatment_Episodes"] > 1:
                    signals.append("Multiple treatment episodes")

                if not signals:
                    signals.append("No major observed signal")

                return " · ".join(signals)

            explorer_table["Patient_Signals"] = (
                explorer_table
                .apply(build_patient_signals, axis=1)
            )

            # --------------------------------------------------------
            # COHORT KPIs
            # --------------------------------------------------------

            st.markdown("### Patient Cohort")

            cohort_col1, cohort_col2, cohort_col3, cohort_col4 = (
                st.columns(4)
            )

            with cohort_col1:
                st.metric(
                    "Patients",
                    f"{len(explorer_table):,}"
                )

            with cohort_col2:
                st.metric(
                    "High Signal Patients",
                    f"{(
                            explorer_table["Signal_Tier"] == "High Signal"
                    ).sum():,}"
                )

            with cohort_col3:
                st.metric(
                    "Rx Fills",
                    f"{explorer_table['Rx_Fills'].sum():,}"
                )

            with cohort_col4:
                st.metric(
                    "Rejected Claims",
                    f"{explorer_table['Rejected_Claims'].sum():,}"
                )

            st.markdown("### Patient Signals")

            signal_summary = (
                explorer_table["Signal_Tier"]
                .value_counts()
                .reindex(
                    ["Stable", "Moderate Signal", "High Signal"],
                    fill_value=0
                )
                .reset_index()
            )

            signal_summary.columns = [
                "Signal_Tier",
                "Patients"
            ]

            fig_signal = px.bar(
                signal_summary,
                x="Signal_Tier",
                y="Patients",
                text="Patients"
            )

            fig_signal.update_layout(
                height=320,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#43AADB"),
                xaxis=dict(
                    title=None,
                    showgrid=False
                ),
                yaxis=dict(
                    title="Patients",
                    gridcolor="rgba(120,120,120,0.15)"
                ),
                showlegend=False
            )

            fig_signal.update_traces(
                textposition="outside"
            )

            st.plotly_chart(
                fig_signal,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            # --------------------------------------------------------
            # PATIENT TABLE
            # --------------------------------------------------------

            st.markdown("### Patients")

            display_explorer_table = explorer_table[
                [
                    "Patient_ID",
                    "Province",
                    "Sex_at_Birth",
                    "Patient_Status",
                    "Signal_Tier",
                    "Patient_Signals",
                    "Conditions",
                    "Therapy_Class",
                    "Products",
                    "Treatment_Episodes",
                    "Rx_Fills",
                    "Product_Switches",
                    "Paid_Claims",
                    "Partial_Claims",
                    "Rejected_Claims",
                    "Last_Fill"
                ]
            ].copy()

            display_explorer_table = (
                display_explorer_table
                .rename(
                    columns={
                        "Patient_ID": "Patient ID",
                        "Sex_at_Birth": "Sex at Birth",
                        "Patient_Status": "Patient Status",
                        "Signal_Tier": "Signal Tier",
                        "Patient_Signals": "Observed Signals",
                        "Therapy_Class": "Therapy Class",
                        "Treatment_Episodes": "Treatment Episodes",
                        "Rx_Fills": "Rx Fills",
                        "Product_Switches": "Product Switches",
                        "Paid_Claims": "Paid Claims",
                        "Partial_Claims": "Partial Claims",
                        "Rejected_Claims": "Rejected Claims",
                        "Last_Fill": "Last Fill"
                    }
                )
            )

            st.dataframe(
                display_explorer_table,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Patient-level summary of observed synthetic diagnoses, treatments, "
                "products, Rx activity, product switching, and pharmacy claim outcomes. "
                "Patient IDs are pseudonymous synthetic identifiers."
            )

            # ------------------------------------------------------------
            # SELECTED PATIENT PROFILE
            # ------------------------------------------------------------

            st.markdown("### Selected Patient")

            selected_patient_id = st.selectbox(
                "Patient ID",
                ["None"] + sorted(
                    explorer_table["Patient_ID"]
                    .dropna()
                    .astype(str)
                    .tolist()
                ),
                key="patient_explorer_selected_patient"
            )

            if selected_patient_id != "None":

                selected_patient = explorer_patients[
                    explorer_patients["Patient_ID"].astype(str)
                    == str(selected_patient_id)
                    ].copy()

                if not selected_patient.empty:

                    selected_patient = selected_patient.iloc[0]

                    selected_patient_id = str(
                        selected_patient["Patient_ID"]
                    )

                    # --------------------------------------------------------
                    # PATIENT-LEVEL DATA
                    # --------------------------------------------------------

                    patient_diagnoses = explorer_diagnoses[
                        explorer_diagnoses["Patient_ID"].astype(str)
                        == selected_patient_id
                        ].copy()

                    patient_treatments = explorer_treatments[
                        explorer_treatments["Patient_ID"].astype(str)
                        == selected_patient_id
                        ].copy()

                    patient_rx = explorer_rx[
                        explorer_rx["Patient_ID"].astype(str)
                        == selected_patient_id
                        ].copy()

                    patient_claims = explorer_pharmacy[
                        explorer_pharmacy["Patient_ID"].astype(str)
                        == selected_patient_id
                        ].copy()

                    patient_diagnoses["Diagnosis_Date"] = pd.to_datetime(
                        patient_diagnoses["Diagnosis_Date"],
                        errors="coerce"
                    )

                    patient_treatments["Treatment_Start_Date"] = pd.to_datetime(
                        patient_treatments["Treatment_Start_Date"],
                        errors="coerce"
                    )

                    patient_treatments["Treatment_End_Date"] = pd.to_datetime(
                        patient_treatments["Treatment_End_Date"],
                        errors="coerce"
                    )

                    patient_rx["Fill_Date"] = pd.to_datetime(
                        patient_rx["Fill_Date"],
                        errors="coerce"
                    )

                    # --------------------------------------------------------
                    # PATIENT SIGNAL
                    # --------------------------------------------------------

                    # Observed treatment activity
                    patient_treatment_count = (
                        patient_treatments["Treatment_ID"]
                        .nunique()
                    )

                    # Observed Rx activity
                    patient_rx_fill_count = len(patient_rx)

                    # Observed pharmacy claim outcomes
                    patient_paid_claims = int(
                        (patient_claims["Claim_Status"] == "Paid").sum()
                    )

                    patient_partial_claims = int(
                        (patient_claims["Claim_Status"] == "Partial").sum()
                    )

                    patient_rejected_claims = int(
                        (patient_claims["Claim_Status"] == "Rejected").sum()
                    )

                    # Product switching
                    patient_product_switches = 0

                    if not patient_treatments.empty:
                        patient_treatment_order = (
                            patient_treatments[
                                [
                                    "Patient_ID",
                                    "Condition_Display",
                                    "Treatment_Start_Date",
                                    "Product_ID"
                                ]
                            ]
                            .dropna(subset=["Treatment_Start_Date"])
                            .sort_values("Treatment_Start_Date")
                        )

                        patient_product_switches = (
                            patient_treatment_order
                            .groupby("Condition_Display")["Product_ID"]
                            .apply(
                                lambda x: (x.astype(str) != x.astype(str).shift()).sum() - 1
                            )
                            .clip(lower=0)
                            .sum()
                        )

                    # --------------------------------------------------------
                    # SIGNAL SCORE
                    # --------------------------------------------------------

                    patient_signal_score = 0

                    if patient_treatment_count == 0:
                        patient_signal_score += 2

                    if patient_rx_fill_count == 0:
                        patient_signal_score += 2

                    if patient_rejected_claims > 0:
                        patient_signal_score += 2

                    if patient_partial_claims > 0:
                        patient_signal_score += 1

                    if patient_product_switches > 0:
                        patient_signal_score += 1

                    if patient_treatment_count > 1:
                        patient_signal_score += 1

                    # --------------------------------------------------------
                    # SIGNAL TIER
                    # --------------------------------------------------------

                    if patient_signal_score >= 4:
                        patient_signal_tier = "High Signal"

                    elif patient_signal_score >= 2:
                        patient_signal_tier = "Moderate Signal"

                    else:
                        patient_signal_tier = "Stable"

                    # --------------------------------------------------------
                    # OBSERVED SIGNALS
                    # --------------------------------------------------------

                    patient_signals = []

                    if patient_treatment_count == 0:
                        patient_signals.append("Treatment gap")

                    if patient_rx_fill_count == 0:
                        patient_signals.append("No observed Rx activity")

                    if patient_rejected_claims > 0:
                        patient_signals.append("Access friction")

                    if patient_partial_claims > 0:
                        patient_signals.append("Partial claim activity")

                    if patient_product_switches > 0:
                        patient_signals.append("Product transition")

                    if patient_treatment_count > 1:
                        patient_signals.append("Multiple treatment episodes")

                    if not patient_signals:
                        patient_signals.append("No major observed signal")

                    patient_signal_text = " · ".join(patient_signals)

                    # --------------------------------------------------------
                    # AGE
                    # --------------------------------------------------------

                    birth_date = pd.to_datetime(
                        selected_patient["Birth_Date"],
                        errors="coerce"
                    )

                    reference_date = pd.Timestamp("2024-07-01")

                    if pd.notna(birth_date):

                        patient_age = (
                                reference_date.year
                                - birth_date.year
                                - (
                                        (
                                            reference_date.month,
                                            reference_date.day
                                        )
                                        <
                                        (
                                            birth_date.month,
                                            birth_date.day
                                        )
                                )
                        )

                    else:

                        patient_age = "—"

                    # --------------------------------------------------------
                    # CONDITION SUMMARY
                    # --------------------------------------------------------

                    patient_condition_names = (
                        patient_diagnoses["Condition_Display"]
                        .dropna()
                        .drop_duplicates()
                        .tolist()
                    )

                    patient_condition_count = len(
                        patient_condition_names
                    )

                    # --------------------------------------------------------
                    # DOCTOR SUMMARY
                    # --------------------------------------------------------

                    patient_doctor_ids = set(
                        patient_rx["HCP_ID"]
                        .dropna()
                    )

                    patient_doctors = hcp_master[
                        hcp_master["HCP_ID"].isin(
                            patient_doctor_ids
                        )
                    ].copy()

                    if not patient_doctors.empty:

                        doctor_names = (
                            patient_doctors["HCP_Name"]
                            .dropna()
                            .drop_duplicates()
                            .tolist()
                        )

                    else:

                        doctor_names = []

                    # --------------------------------------------------------
                    # TREATMENT SUMMARY
                    # --------------------------------------------------------

                    patient_treatments["Brand_Name"] = (
                        patient_treatments["Product_ID"]
                        .map(explorer_product_name_lookup)
                    )

                    patient_treatments["Brand_Name"] = (
                        patient_treatments["Brand_Name"]
                        .fillna(
                            patient_treatments["Product_ID"]
                        )
                    )

                    treatment_summary = (
                        patient_treatments[
                            [
                                "Therapy_Class",
                                "Brand_Name",
                                "Treatment_Start_Date",
                                "Treatment_Status"
                            ]
                        ]
                        .drop_duplicates()
                        .sort_values(
                            "Treatment_Start_Date"
                        )
                    )

                    # --------------------------------------------------------
                    # ACCESS SUMMARY
                    # --------------------------------------------------------

                    paid_claims = int(
                        (
                                patient_claims["Claim_Status"]
                                == "Paid"
                        ).sum()
                    )

                    partial_claims = int(
                        (
                                patient_claims["Claim_Status"]
                                == "Partial"
                        ).sum()
                    )

                    rejected_claims = int(
                        (
                                patient_claims["Claim_Status"]
                                == "Rejected"
                        ).sum()
                    )

                    # ------------------------------------------------------------
                    # SELECTED PATIENT PROFILE
                    # ------------------------------------------------------------

                    profile_left, profile_right = st.columns(
                        [1.05, 2.4],
                        gap="large"
                    )

                    # Get selected patient demographics
                    selected_patient_record = patients[
                        patients["Patient_ID"] == selected_patient_id
                        ]

                    if not selected_patient_record.empty:

                        selected_patient_record = selected_patient_record.iloc[0]

                        patient_birth_date = pd.to_datetime(
                            selected_patient_record["Birth_Date"],
                            errors="coerce"
                        )

                        reference_date = pd.Timestamp("2024-07-01")

                        if pd.notna(patient_birth_date):

                            patient_age = (
                                    reference_date.year
                                    - patient_birth_date.year
                                    - (
                                            (reference_date.month, reference_date.day)
                                            <
                                            (patient_birth_date.month, patient_birth_date.day)
                                    )
                            )

                        else:

                            patient_age = "—"

                        patient_sex = selected_patient_record["Sex_at_Birth"]
                        patient_province = selected_patient_record["Province"]
                        patient_status = selected_patient_record["Patient_Status"]

                    else:

                        patient_age = "—"
                        patient_sex = "—"
                        patient_province = "—"
                        patient_status = "—"

                    # ------------------------------------------------------------
                    # LEFT — PATIENT DEMOGRAPHICS
                    # ------------------------------------------------------------

                    st.markdown(
                        """
                            <style>
                            .patient-blue-card {
                                background: #173B67;
                                color: white;
                                padding: 24px 24px 26px 24px;
                                border-radius: 12px;
                                margin-top: 8px;
                                margin-bottom: 20px;
                            }

                            .patient-blue-card .patient-id {
                                font-size: 28px;
                                font-weight: 700;
                                margin-bottom: 26px;
                            }

                            .patient-blue-card .label {
                                font-size: 11px;
                                letter-spacing: 0.8px;
                                opacity: 0.70;
                            }

                            .patient-blue-card .value {
                                font-size: 18px;
                                font-weight: 600;
                                margin-top: 3px;
                                margin-bottom: 18px;
                            }
                            </style>
                            """,
                        unsafe_allow_html=True
                    )

                    # ------------------------------------------------------------
                    # LEFT — PATIENT DEMOGRAPHICS
                    # ------------------------------------------------------------

                    st.markdown(
                        """
                            <style>
                            .patient-blue-card {
                                background: #173B67;
                                color: white;
                                padding: 26px 24px 28px 24px;
                                border-radius: 12px;
                                margin-top: 8px;
                                margin-bottom: 20px;
                            }

                            .patient-blue-card .patient-id {
                                font-size: 28px;
                                font-weight: 700;
                                margin-bottom: 30px;
                            }

                            .patient-blue-card .demo-grid {
                                display: grid;
                                grid-template-columns: 1fr 1fr;
                                column-gap: 24px;
                                row-gap: 24px;
                            }

                            .patient-blue-card .label {
                                font-size: 11px;
                                letter-spacing: 0.8px;
                                opacity: 0.65;
                            }

                            .patient-blue-card .value {
                                font-size: 18px;
                                font-weight: 600;
                                margin-top: 5px;
                            }
                            </style>
                            """,
                        unsafe_allow_html=True
                    )

                    # ------------------------------------------------------------
                    # LEFT — PATIENT DEMOGRAPHICS
                    # ------------------------------------------------------------

                    # ------------------------------------------------------------
                    # LEFT — PATIENT DEMOGRAPHICS
                    # ------------------------------------------------------------

                    st.markdown(
                        """
                            <style>

                            /* Blue patient profile card */
                            div[data-testid="stVerticalBlockBorderWrapper"] {
                                border-radius: 12px;
                            }

                            div[data-testid="stVerticalBlockBorderWrapper"]:has(
                                div[data-testid="stMarkdownContainer"] h3
                            ) {
                                background-color: #173B67;
                                border: 1px solid #173B67;
                                border-radius: 12px;
                                padding: 8px 8px 4px 8px;
                            }

                            </style>
                            """,
                        unsafe_allow_html=True
                    )

                    st.html("""
                    <style>
                    .st-key-patient_profile_blue {
                        display: block !important;
                        width: 100% !important;
                        background-color: #003366 !important;
                        border: 1px solid #003366 !important;
                        border-radius: 12px !important;
                        padding: 20px !important;
                        box-sizing: border-box !important;
                    }

                    .st-key-patient_profile_blue h2,
                    .st-key-patient_profile_blue h3,
                    .st-key-patient_profile_blue p,
                    .st-key-patient_profile_blue strong {
                        color: #FFFFFF !important;
                    }

                    .st-key-patient_profile_blue [data-testid="stCaptionContainer"] {
                        color: rgba(255, 255, 255, 0.72) !important;
                    }

                    .st-key-patient_profile_blue [data-testid="stMarkdownContainer"] {
                        color: #FFFFFF !important;
                    }
                    </style>
                    """)

                    with profile_left:

                        with st.container(key="patient_profile_blue"):

                            st.markdown(
                                f"## {selected_patient_id}"
                            )

                            st.markdown(
                                f"**Patient Signal:** {patient_signal_tier}"
                            )

                            st.caption(
                                patient_signal_text
                            )

                            demo_col1, demo_col2 = st.columns(2)

                            with demo_col1:
                                st.caption("AGE")
                                st.write(f"**{patient_age}**")

                            with demo_col2:
                                st.caption("SEX AT BIRTH")
                                st.write(f"**{patient_sex}**")

                            demo_col3, demo_col4 = st.columns(2)

                            with demo_col3:
                                st.caption("PROVINCE")
                                st.write(f"**{patient_province}**")

                            with demo_col4:
                                st.caption("STATUS")
                                st.write(f"**{patient_status}**")

                    # ------------------------------------------------------------
                    # RIGHT — PATIENT OVERVIEW
                    # ------------------------------------------------------------

                    with profile_right:

                        st.markdown("### Patient Overview")

                        overview_col1, overview_col2 = st.columns(
                            [1.3, 1],
                            gap="large"
                        )

                        with overview_col1:

                            st.markdown("**Conditions**")

                            if patient_condition_names:

                                for condition in patient_condition_names:
                                    st.write(f"• {condition}")

                            else:

                                st.write("No observed conditions")

                            st.markdown("**Treatments**")

                            if treatment_summary.empty:

                                st.write("No observed treatment")

                            else:

                                for _, treatment_row in treatment_summary.iterrows():

                                    brand = treatment_row["Brand_Name"]
                                    therapy = treatment_row["Therapy_Class"]
                                    start_date = treatment_row["Treatment_Start_Date"]
                                    status = treatment_row["Treatment_Status"]

                                    if pd.notna(start_date):

                                        start_text = start_date.strftime("%b %Y")

                                    else:

                                        start_text = "—"

                                    st.write(f"**{brand}**")

                                    st.caption(
                                        f"{therapy} · Started {start_text} · {status}"
                                    )

                        with overview_col2:

                            st.markdown("**Doctors**")

                            if doctor_names:

                                for doctor_name in doctor_names:

                                    doctor_row = patient_doctors[
                                        patient_doctors["HCP_Name"] == doctor_name
                                        ]

                                    if not doctor_row.empty:

                                        doctor_specialties = (
                                            doctor_row["Specialty"]
                                            .dropna()
                                            .drop_duplicates()
                                            .tolist()
                                        )

                                    else:

                                        doctor_specialties = []

                                    if doctor_specialties:

                                        st.write(
                                            f"**{doctor_name}** "
                                            f"({', '.join(doctor_specialties)})"
                                        )

                                    else:

                                        st.write(
                                            f"**{doctor_name}**"
                                        )

                            else:

                                st.write(
                                    "No associated doctor observed"
                                )

                            st.markdown("**Access Activity**")

                            access_col1, access_col2, access_col3 = st.columns(3)

                            with access_col1:

                                st.caption("PAID")
                                st.write(f"**{paid_claims:,}**")

                            with access_col2:

                                st.caption("PARTIAL")
                                st.write(f"**{partial_claims:,}**")

                            with access_col3:

                                st.caption("REJECTED")
                                st.write(f"**{rejected_claims:,}**")

                    # --------------------------------------------------------
                    # JOURNEY SUMMARY
                    # --------------------------------------------------------

                    # --------------------------------------------------------
                    # PATIENT SIGNAL INTERPRETATION
                    # --------------------------------------------------------

                    st.markdown("### Patient Signal")

                    if patient_rejected_claims > 0:

                        signal_follow_up = (
                            "Review observed pharmacy claim outcomes and access friction."
                        )

                    elif patient_product_switches > 0:

                        signal_follow_up = (
                            "Review observed product transitions and treatment history."
                        )

                    elif patient_rx_fill_count == 0:

                        signal_follow_up = (
                            "Review treatment initiation and observed Rx activity."
                        )

                    elif patient_treatment_count > 1:

                        signal_follow_up = (
                            "Review treatment episode transitions and continuity."
                        )

                    else:

                        signal_follow_up = (
                            "No major observed commercial signal requiring review."
                        )

                    st.info(
                        f"**Recommended analytical follow-up:** {signal_follow_up}"
                    )

                    st.caption(
                        "Signal interpretation is based on observed synthetic records "
                        "and is intended for commercial analytics exploration, not clinical decision-making."
                    )

                    # ------------------------------------------------------------
                    # PATIENT TIMELINE
                    # ------------------------------------------------------------

                    st.markdown("### Patient Timeline")

                    st.caption(
                        "Observed longitudinal activity across diagnoses, treatments, product changes, "
                        "and prescription fills."
                    )

                    # ------------------------------------------------------------
                    # PREPARE TIMELINE DATA
                    # ------------------------------------------------------------

                    timeline_events = []

                    # Diagnosis events
                    patient_diagnoses_timeline = (
                        patient_diagnoses[
                            patient_diagnoses["Patient_ID"] == selected_patient_id
                            ]
                        .copy()
                    )

                    patient_diagnoses_timeline["Diagnosis_Date"] = pd.to_datetime(
                        patient_diagnoses_timeline["Diagnosis_Date"],
                        errors="coerce"
                    )

                    for _, row in patient_diagnoses_timeline.dropna(
                            subset=["Diagnosis_Date"]
                    ).iterrows():
                        condition = row["Condition"]
                        condition_display = disease_display_names.get(
                            condition,
                            condition
                        )

                        timeline_events.append(
                            {
                                "Date": row["Diagnosis_Date"],
                                "Condition": condition_display,
                                "Event": "Diagnosis",
                                "Detail": "Diagnosis observed"
                            }
                        )

                    # Treatment events
                    # ------------------------------------------------------------
                    # TREATMENT EVENTS
                    # ------------------------------------------------------------

                    patient_treatments_timeline = (
                        patient_treatments[
                            [
                                "Treatment_ID",
                                "Patient_ID",
                                "Condition",
                                "Product_ID",
                                "Treatment_Start_Date",
                                "Treatment_End_Date"
                            ]
                        ]
                        .copy()
                    )

                    patient_treatments_timeline["Treatment_Start_Date"] = pd.to_datetime(
                        patient_treatments_timeline["Treatment_Start_Date"],
                        errors="coerce"
                    )

                    patient_treatments_timeline["Treatment_End_Date"] = pd.to_datetime(
                        patient_treatments_timeline["Treatment_End_Date"],
                        errors="coerce"
                    )

                    patient_treatments_timeline = (
                        patient_treatments_timeline
                        .merge(
                            product_master[
                                [
                                    "Product_ID",
                                    "Brand_Name"
                                ]
                            ].drop_duplicates("Product_ID"),
                            on="Product_ID",
                            how="left"
                        )
                    )

                    for _, row in patient_treatments_timeline.iterrows():

                        condition = row["Condition"]
                        condition_display = disease_display_names.get(
                            condition,
                            condition
                        )

                        brand = row["Brand_Name"]

                        if pd.isna(brand):
                            brand = row["Product_ID"]

                        # Treatment start
                        if pd.notna(row["Treatment_Start_Date"]):
                            timeline_events.append(
                                {
                                    "Date": row["Treatment_Start_Date"],
                                    "Condition": condition_display,
                                    "Event": "Treatment Start",
                                    "Detail": str(brand)
                                }
                            )

                        # Treatment end
                        if pd.notna(row["Treatment_End_Date"]):
                            timeline_events.append(
                                {
                                    "Date": row["Treatment_End_Date"],
                                    "Condition": condition_display,
                                    "Event": "Treatment End",
                                    "Detail": str(brand)
                                }
                            )

                    # ------------------------------------------------------------
                    # IDENTIFY PRODUCT SWITCHES
                    # ------------------------------------------------------------

                    switching_timeline = (
                        patient_treatments_timeline[
                            [
                                "Patient_ID",
                                "Condition",
                                "Product_ID",
                                "Brand_Name",
                                "Treatment_Start_Date"
                            ]
                        ]
                        .dropna(
                            subset=[
                                "Patient_ID",
                                "Condition",
                                "Product_ID",
                                "Treatment_Start_Date"
                            ]
                        )
                        .sort_values(
                            [
                                "Patient_ID",
                                "Condition",
                                "Treatment_Start_Date"
                            ]
                        )
                        .copy()
                    )

                    switching_timeline["Previous_Product_ID"] = (
                        switching_timeline
                        .groupby(
                            [
                                "Patient_ID",
                                "Condition"
                            ]
                        )["Product_ID"]
                        .shift(1)
                    )

                    switching_timeline["Previous_Brand_Name"] = (
                        switching_timeline
                        .groupby(
                            [
                                "Patient_ID",
                                "Condition"
                            ]
                        )["Brand_Name"]
                        .shift(1)
                    )

                    switch_events = switching_timeline[
                        switching_timeline["Previous_Product_ID"].notna()
                        &
                        (
                                switching_timeline["Product_ID"]
                                != switching_timeline["Previous_Product_ID"]
                        )
                        ].copy()

                    for _, row in switch_events.iterrows():

                        condition_display = disease_display_names.get(
                            row["Condition"],
                            row["Condition"]
                        )

                        previous_brand = row["Previous_Brand_Name"]

                        if pd.isna(previous_brand):
                            previous_brand = row["Previous_Product_ID"]

                        current_brand = row["Brand_Name"]

                        if pd.isna(current_brand):
                            current_brand = row["Product_ID"]

                        timeline_events.append(
                            {
                                "Date": row["Treatment_Start_Date"],
                                "Condition": condition_display,
                                "Event": "Product Switch",
                                "Detail": (
                                    f"{previous_brand} → {current_brand}"
                                )
                            }
                        )

                    # ------------------------------------------------------------
                    # PREPARE RX ACTIVITY
                    # ------------------------------------------------------------

                    patient_rx_timeline = (
                        patient_rx[
                            patient_rx["Patient_ID"] == selected_patient_id
                            ]
                        .copy()
                    )

                    patient_rx_timeline["Fill_Date"] = pd.to_datetime(
                        patient_rx_timeline["Fill_Date"],
                        errors="coerce"
                    )

                    patient_rx_timeline["Condition"] = (
                        patient_rx_timeline["Treatment_ID"]
                        .map(
                            patient_treatments_timeline
                            .set_index("Treatment_ID")["Condition"]
                        )
                    )

                    patient_rx_timeline["Condition"] = (
                        patient_rx_timeline["Condition"]
                        .map(
                            lambda x: disease_display_names.get(x, x)
                            if pd.notna(x)
                            else "Unknown"
                        )
                    )

                    # One dot per month / condition rather than one dot per fill
                    rx_monthly = (
                        patient_rx_timeline
                        .dropna(subset=["Fill_Date"])
                        .assign(
                            Rx_Month=lambda x: x["Fill_Date"].dt.to_period("M")
                        )
                        .groupby(
                            [
                                "Condition",
                                "Rx_Month"
                            ]
                        )
                        .agg(
                            Rx_Fills=("Rx_Event_ID", "nunique")
                        )
                        .reset_index()
                    )

                    rx_monthly["Date"] = (
                        rx_monthly["Rx_Month"]
                        .dt.to_timestamp()
                    )

                    for _, row in rx_monthly.iterrows():
                        timeline_events.append(
                            {
                                "Date": row["Date"],
                                "Condition": row["Condition"],
                                "Event": "Rx Activity",
                                "Detail": f"{int(row['Rx_Fills'])} fill(s)"
                            }
                        )

                    # ------------------------------------------------------------
                    # CREATE DATAFRAME
                    # ------------------------------------------------------------

                    timeline_df = pd.DataFrame(
                        timeline_events
                    )

                    if timeline_df.empty:

                        st.info(
                            "No observed longitudinal activity for this patient."
                        )

                    else:

                        timeline_df["Date"] = pd.to_datetime(
                            timeline_df["Date"],
                            errors="coerce"
                        )

                        timeline_df = (
                            timeline_df
                            .dropna(subset=["Date"])
                            .sort_values("Date")
                            .copy()
                        )

                        # --------------------------------------------------------
                        # CONDITION LANES
                        # --------------------------------------------------------

                        condition_order = (
                            timeline_df["Condition"]
                            .drop_duplicates()
                            .tolist()
                        )

                        condition_y = {
                            condition: i
                            for i, condition in enumerate(
                                condition_order
                            )
                        }

                        timeline_df["Y"] = (
                            timeline_df["Condition"]
                            .map(condition_y)
                        )

                        # --------------------------------------------------------
                        # TIMELINE FIGURE
                        # --------------------------------------------------------

                        fig = go.Figure()

                        # --------------------------------------------------------
                        # TREATMENT SPANS
                        # --------------------------------------------------------

                        for _, row in patient_treatments_timeline.iterrows():

                            if pd.isna(row["Treatment_Start_Date"]):
                                continue

                            condition_display = disease_display_names.get(
                                row["Condition"],
                                row["Condition"]
                            )

                            start_date = row["Treatment_Start_Date"]

                            if pd.notna(row["Treatment_End_Date"]):

                                end_date = row["Treatment_End_Date"]

                            else:

                                # Extend active treatment slightly so it remains visible
                                end_date = pd.Timestamp("2024-07-01")

                            brand = row["Brand_Name"]

                            if pd.isna(brand):
                                brand = row["Product_ID"]

                            y = condition_y.get(
                                condition_display
                            )

                            if y is None:
                                continue

                            fig.add_trace(
                                go.Scatter(
                                    x=[
                                        start_date,
                                        end_date
                                    ],
                                    y=[
                                        y,
                                        y
                                    ],
                                    mode="lines",
                                    line=dict(
                                        width=12,
                                        color="#43AADB"
                                    ),
                                    hovertemplate=(
                                        f"<b>{condition_display}</b><br>"
                                        f"{brand}<br>"
                                        f"{start_date.strftime('%d %b %Y')}"
                                        " → "
                                        f"{end_date.strftime('%d %b %Y')}"
                                        "<extra></extra>"
                                    ),
                                    showlegend=False
                                )
                            )

                        # --------------------------------------------------------
                        # EVENT MARKERS
                        # --------------------------------------------------------

                        marker_config = {
                            "Diagnosis": {
                                "symbol": "circle",
                                "size": 12
                            },
                            "Treatment Start": {
                                "symbol": "square",
                                "size": 12
                            },
                            "Treatment End": {
                                "symbol": "triangle-up",
                                "size": 12
                            },
                            "Product Switch": {
                                "symbol": "diamond",
                                "size": 13
                            },
                            "Rx Activity": {
                                "symbol": "circle",
                                "size": 6
                            }
                        }

                        event_order = [
                            "Diagnosis",
                            "Treatment Start",
                            "Treatment End",
                            "Product Switch",
                            "Rx Activity"
                        ]

                        for event_type in event_order:

                            event_data = timeline_df[
                                timeline_df["Event"] == event_type
                                ]

                            if event_data.empty:
                                continue

                            config = marker_config[event_type]

                            fig.add_trace(
                                go.Scatter(
                                    x=event_data["Date"],
                                    y=event_data["Y"],
                                    mode="markers",
                                    marker=dict(
                                        symbol=config["symbol"],
                                        size=config["size"]
                                    ),
                                    customdata=event_data[
                                        [
                                            "Condition",
                                            "Detail",
                                            "Date"
                                        ]
                                    ],
                                    hovertemplate=(
                                        "<b>%{customdata[0]}</b><br>"
                                        f"{event_type}<br>"
                                        "%{customdata[1]}<br>"
                                        "%{customdata[2]|%d %b %Y}"
                                        "<extra></extra>"
                                    ),
                                    name=event_type,
                                    showlegend=True
                                )
                            )

                        # --------------------------------------------------------
                        # LAYOUT
                        # --------------------------------------------------------

                        fig.update_layout(
                            height=max(
                                260,
                                150 * len(condition_order)
                            ),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(
                                title=dict(
                                    text="Timeline",
                                    font=dict(
                                        color="#43AADB"
                                    )
                                ),
                                showgrid=True,
                                gridcolor="rgba(120,120,120,0.15)",
                                zeroline=False
                            ),
                            yaxis=dict(
                                tickmode="array",
                                tickvals=list(
                                    condition_y.values()
                                ),
                                ticktext=list(
                                    condition_y.keys()
                                ),
                                showgrid=True,
                                gridcolor="rgba(120,120,120,0.10)",
                                zeroline=False
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="left",
                                x=0
                            ),
                            margin=dict(
                                l=20,
                                r=20,
                                t=70,
                                b=20
                            ),
                            hovermode="closest"
                        )

                        fig.update_xaxes(
                            showline=True,
                            linecolor="rgba(120,120,120,0.25)"
                        )

                        fig.update_yaxes(
                            showline=False
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={
                                "displayModeBar": False
                            }
                        )

                        st.caption(
                            "Treatment spans show observed treatment periods. Rx dots represent monthly "
                            "prescription activity; multiple fills in the same month are grouped into one marker."
                        )

