import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
Project_root = Path(__file__).resolve().parents[1]

timeline = pd.read_csv(
    Project_root
    / "Data"
    / "processed"
    / "patient_longitudinal_timeline.csv"
)

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


def show_commercial_opportunities(
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

    st.subheader("Commercial Opportunities")

    st.caption(
        "Identify and prioritize commercially relevant opportunities "
        "using patient, treatment, HCP, access, and competitive signals."
    )

    st.info(
        "Commercial opportunity analytics will be built from the synthetic "
        "HCP, patient, treatment, prescription, access, and competitive datasets."
    )

    # ========================================================
    # OPPORTUNITY FILTERS
    # ========================================================

    st.markdown("### Opportunity Filters")
    evidence_display_map = {
        "Active + High Activity":
            "Active treatment with higher prescribing activity",

        "Active + Lower Activity":
            "Active treatment with lower prescribing activity",

        "Historical + High Activity":
            "Historical treatment with higher prescribing activity",

        "Historical + Lower Activity":
            "Historical treatment with lower prescribing activity",

        "Gap + High Activity":
            "High prescribing activity with treatment gap",

        "Gap + Lower Activity":
            "Lower prescribing activity with treatment gap",
    }

    COMMERCIAL_EVIDENCE_COLORS = {
        "Active + High Activity": "#2563EB",
        "Active + Lower Activity": "#60A5FA",
        "Historical + High Activity": "#7C3AED",
        "Historical + Lower Activity": "#A78BFA",
        "Gap + High Activity": "#1D4ED8",
        "Gap + Lower Activity": "#818CF8",
    }


    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:

        opportunity_conditions_raw = sorted(
            opportunities["Condition"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        opportunity_conditions_display = [
            disease_display_names.get(
                condition,
                condition,
            )
            for condition in opportunity_conditions_raw
        ]

        selected_opportunity_condition_display = st.selectbox(
            "Condition",
            ["All"] + opportunity_conditions_display,
            key="commercial_opportunity_condition",
        )

        if selected_opportunity_condition_display == "All":

            selected_opportunity_condition = "All"

        else:

            selected_opportunity_condition = next(
                (
                    condition
                    for condition in opportunity_conditions_raw
                    if disease_display_names.get(
                    condition,
                    condition,
                )
                       == selected_opportunity_condition_display
                ),
                selected_opportunity_condition_display,
            )

    with filter_col2:

        opportunity_provinces = sorted(
            opportunities["Province"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_opportunity_province = st.selectbox(
            "Province",
            ["All"] + opportunity_provinces,
            key="commercial_opportunity_province",
        )

    with filter_col3:

        opportunity_therapies = sorted(
            opportunities["Therapy_Class"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_opportunity_therapy = st.selectbox(
            "Therapy Class",
            ["All"] + opportunity_therapies,
            key="commercial_opportunity_therapy",
        )

    filter_col4, filter_col5, filter_col6 = st.columns(3)

    with filter_col4:

        opportunity_evidence = sorted(
            opportunities["Commercial_Evidence_Category"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        opportunity_evidence_display = [
            evidence_display_map.get(
                evidence,
                evidence
            )
            for evidence in opportunity_evidence
        ]

        selected_opportunity_evidence_display = st.selectbox(
            "Commercial Evidence",
            ["All"] + opportunity_evidence_display,
            key="commercial_opportunity_evidence",
        )

        if selected_opportunity_evidence_display == "All":
            selected_opportunity_evidence = "All"
        else:
            selected_opportunity_evidence = next(
                (
                    evidence
                    for evidence in opportunity_evidence
                    if evidence_display_map.get(
                    evidence,
                    evidence
                ) == selected_opportunity_evidence_display
                ),
                selected_opportunity_evidence_display,
            )

    with filter_col5:

        opportunity_specialties = sorted(
            opportunities["Specialty"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_opportunity_specialty = st.selectbox(
            "Specialty",
            ["All"] + opportunity_specialties,
            key="commercial_opportunity_specialty",
        )

    with filter_col6:

        opportunity_gap_signal = sorted(
            opportunities["Treatment_Gap_Signal"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_opportunity_gap_signal = st.selectbox(
            "Treatment Gap Signal",
            ["All"] + opportunity_gap_signal,
            key="commercial_opportunity_gap_signal",
        )

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_opportunities = opportunities.copy()

    if selected_opportunity_condition != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Condition"].astype(str)
            == selected_opportunity_condition
            ]

    if selected_opportunity_province != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Province"].astype(str)
            == selected_opportunity_province
            ]

    if selected_opportunity_therapy != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Therapy_Class"].astype(str)
            == selected_opportunity_therapy
            ]

    if selected_opportunity_evidence != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Commercial_Evidence_Category"].astype(str)
            == selected_opportunity_evidence
            ]

    if selected_opportunity_specialty != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Specialty"].astype(str)
            == selected_opportunity_specialty
            ]

    if selected_opportunity_gap_signal != "All":
        filtered_opportunities = filtered_opportunities[
            filtered_opportunities["Treatment_Gap_Signal"].astype(str)
            == selected_opportunity_gap_signal
            ]

    # ========================================================
    # EMPTY STATE
    # ========================================================

    if filtered_opportunities.empty:
        st.warning(
            "No commercial opportunities match the selected filters."
        )

        st.stop()

    # ========================================================
    # PREPARE NUMERIC FIELDS
    # ========================================================

    opportunity_data = filtered_opportunities.copy()

    numeric_opportunity_columns = [
        "Unique_Patients",
        "Treatment_Episodes",
        "NRx_Proxy",
        "Refills",
        "TRx_Proxy",
        "Product_Count",
        "Pharmacy_Claims",
        "Formulary_Matched_Claims",
        "Plan_Paid_Amount",
        "Patient_Paid_Amount",
        "Therapy_Formulary_Match_Rate",
        "Diagnosed_Patients",
        "Diagnosed_No_Observed_Treatment",
        "Treatment_Gap_Rate",
    ]

    for column in numeric_opportunity_columns:
        opportunity_data[column] = pd.to_numeric(
            opportunity_data[column],
            errors="coerce"
        ).fillna(0)

    # ========================================================
    # OPPORTUNITY KPIs
    # ========================================================

    # ========================================================
    # KPI CALCULATIONS — TRUE FILTERED UNIVERSE
    # ========================================================

    total_opportunities = len(opportunity_data)

    high_priority_opportunities = int(
        opportunity_data["High_TRx_Activity_Flag"]
        .astype(bool)
        .sum()
    )

    unique_hcps = opportunity_data[
        "Prescribing_HCP_ID"
    ].nunique()

    # --------------------------------------------------------
    # Patient-level population
    # --------------------------------------------------------

    filtered_patient_ids = set(
        diagnoses.loc[
            diagnoses["Condition"].astype(str)
            == selected_opportunity_condition,
            "Patient_ID",
        ].dropna().unique()
    ) if selected_opportunity_condition != "All" else set(
        diagnoses["Patient_ID"]
        .dropna()
        .unique()
    )

    # Apply province filter
    if selected_opportunity_province != "All":
        province_patient_ids = set(
            patients.loc[
                patients["Province"].astype(str)
                == selected_opportunity_province,
                "Patient_ID",
            ]
            .dropna()
            .unique()
        )

        filtered_patient_ids &= province_patient_ids

    # Apply therapy filter
    if selected_opportunity_therapy != "All":
        therapy_patient_ids = set(
            treatments.loc[
                treatments["Therapy_Class"].astype(str)
                == selected_opportunity_therapy,
                "Patient_ID",
            ]
            .dropna()
            .unique()
        )

        filtered_patient_ids &= therapy_patient_ids

    # --------------------------------------------------------
    # Diagnosed patients
    # --------------------------------------------------------

    filtered_diagnosed = diagnoses[
        diagnoses["Patient_ID"].isin(
            filtered_patient_ids
        )
    ].copy()

    diagnosed_patient_ids = set(
        filtered_diagnosed["Patient_ID"]
        .dropna()
        .unique()
    )

    patients_affected = len(
        diagnosed_patient_ids
    )

    # --------------------------------------------------------
    # Treatment-gap patients
    # --------------------------------------------------------

    treated_patient_ids = set(
        treatments.loc[
            treatments["Patient_ID"].isin(
                diagnosed_patient_ids
            ),
            "Patient_ID",
        ]
        .dropna()
        .unique()
    )

    treatment_gap_patient_ids = (
            diagnosed_patient_ids
            - treated_patient_ids
    )

    treatment_gap_patients = len(
        treatment_gap_patient_ids
    )

    # --------------------------------------------------------
    # Pharmacy claims
    # --------------------------------------------------------

    filtered_pharmacy_claims = pharmacy_claims[
        pharmacy_claims["Patient_ID"].isin(
            filtered_patient_ids
        )
    ].copy()

    if selected_opportunity_therapy != "All":
        filtered_treatment_ids = set(
            treatments.loc[
                treatments["Patient_ID"].isin(
                    filtered_patient_ids
                )
                & (
                        treatments["Therapy_Class"].astype(str)
                        == selected_opportunity_therapy
                ),
                "Treatment_ID",
            ]
            .dropna()
            .unique()
        )

        filtered_pharmacy_claims = (
            filtered_pharmacy_claims[
                filtered_pharmacy_claims["Treatment_ID"].isin(
                    filtered_treatment_ids
                )
            ]
        )

    pharmacy_claims_count = len(
        filtered_pharmacy_claims
    )

    # ========================================================
    # KPI DISPLAY
    # ========================================================

    st.markdown("### Opportunity Overview")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.metric(
            "Opportunities",
            f"{total_opportunities:,}"
        )

    with kpi2:
        st.metric(
            "High-Activity Opportunities",
            f"{high_priority_opportunities:,}"
        )

    with kpi3:
        st.metric(
            "HCPs",
            f"{unique_hcps:,}"
        )

    with kpi4:
        st.metric(
            "Diagnosed Patients",
            f"{patients_affected:,}"
        )

    with kpi5:
        st.metric(
            "Treatment Gap Patients",
            f"{treatment_gap_patients:,}"
        )

    with kpi6:
        st.metric(
            "Pharmacy Claims",
            f"{pharmacy_claims_count:,}"
        )

    # ========================================================
    # OPPORTUNITY PRIORITY LANDSCAPE
    # ========================================================


    st.markdown("### Opportunity Priority Landscape")

    st.write(
        "Identify HCP-condition-therapy opportunities where patient volume and "
        "treatment gaps are both commercially relevant. Multiple opportunities may overlap "
        "when they share similar patient volume and treatment-gap levels."
    )

    # ========================================================
    # BUILD HCP-LEVEL PATIENT / TREATMENT-GAP SIGNALS
    # ========================================================

    priority_data = opportunity_data.copy()

    # --------------------------------------------------------
    # 1. Identify diagnosed patients.
    #
    # Diagnosis events do not contain HCP_ID, so diagnoses
    # cannot be directly attributed to an HCP.
    # --------------------------------------------------------

    diagnosed_patients = (
        timeline[
            timeline["Event_Type"].astype(str).str.strip().eq("Diagnosis")
        ]
        [
            [
                "Patient_ID",
                "Condition",
            ]
        ]
        .dropna(subset=["Patient_ID", "Condition"])
        .drop_duplicates()
    )

    # --------------------------------------------------------
    # 2. Identify HCP-linked patient activity.
    #
    # These event types contain HCP_ID and can therefore
    # establish an observed HCP-patient-condition relationship.
    # --------------------------------------------------------

    hcp_linked_events = timeline[
        timeline["Event_Type"].astype(str).str.strip().isin(
            [
                "Encounter",
                "Medical Claim",
                "Rx Event",
                "Pharmacy Claim",
            ]
        )
    ].copy()

    hcp_linked_events = (
        hcp_linked_events[
            [
                "Patient_ID",
                "Condition",
                "HCP_ID",
            ]
        ]
        .dropna(subset=["Patient_ID", "Condition", "HCP_ID"])
        .drop_duplicates()
    )

    # --------------------------------------------------------
    # 3. Associate diagnosed patients with HCPs through
    #    observed HCP-linked activity for the same condition.
    # --------------------------------------------------------

    hcp_diagnosed_patients = diagnosed_patients.merge(
        hcp_linked_events,
        on=[
            "Patient_ID",
            "Condition",
        ],
        how="inner",
    ).drop_duplicates()

    # --------------------------------------------------------
    # 4. Determine whether each HCP-associated diagnosed
    #    patient has any observed treatment for the condition.
    #
    #    Treatment Start events do not contain HCP_ID, so
    #    treatment status is evaluated at Patient + Condition.
    # --------------------------------------------------------

    treated_patients = (
        timeline[
            timeline["Event_Type"].astype(str).str.strip().eq("Treatment Start")
        ]
        [
            [
                "Patient_ID",
                "Condition",
            ]
        ]
        .dropna(subset=["Patient_ID", "Condition"])
        .drop_duplicates()
    )

    hcp_diagnosed_patients = hcp_diagnosed_patients.merge(
        treated_patients.assign(
            Observed_Treatment=True
        ),
        on=[
            "Patient_ID",
            "Condition",
        ],
        how="left",
    )

    hcp_diagnosed_patients["Observed_Treatment"] = (
        hcp_diagnosed_patients["Observed_Treatment"]
        .fillna(False)
    )

    # --------------------------------------------------------
    # 5. Aggregate to HCP + Condition.
    # --------------------------------------------------------

    hcp_condition_gap = (
        hcp_diagnosed_patients
        .groupby(
            [
                "HCP_ID",
                "Condition",
            ],
            as_index=False,
        )
        .agg(
            Observed_Diagnosed_Patients=(
                "Patient_ID",
                "nunique",
            ),
            Observed_Treatment_Gap_Patients=(
                "Observed_Treatment",
                lambda x: x.eq(False).sum(),
            ),
        )
    )

    hcp_condition_gap["Observed_Treatment_Gap_Rate"] = (
            hcp_condition_gap["Observed_Treatment_Gap_Patients"]
            / hcp_condition_gap["Observed_Diagnosed_Patients"]
    )

    # --------------------------------------------------------
    # 6. Join HCP-condition signals to the opportunity grain.
    # --------------------------------------------------------

    priority_data = priority_data.merge(
        hcp_condition_gap,
        left_on=[
            "Prescribing_HCP_ID",
            "Condition",
        ],
        right_on=[
            "HCP_ID",
            "Condition",
        ],
        how="left",
    )

    priority_data["Observed Diagnosed Patients"] = (
        pd.to_numeric(
            priority_data["Observed_Diagnosed_Patients"],
            errors="coerce",
        )
        .fillna(0)
    )

    priority_data["Observed Treatment Gap (%)"] = (
            pd.to_numeric(
                priority_data["Observed_Treatment_Gap_Rate"],
                errors="coerce",
            )
            .fillna(0)
            * 100
    )




    priority_data["TRx Proxy"] = pd.to_numeric(
        priority_data["TRx_Proxy"],
        errors="coerce",
    ).fillna(0)

    priority_data["HCP Display Name"] = (
            "Dr. " + priority_data["HCP_Name"].astype(str)
    )

    priority_data["Opportunity Type"] = (
            priority_data["Condition"]
            .map(disease_display_names)
            .fillna(priority_data["Condition"].astype(str))
            + " · "
            + priority_data["Therapy_Class"].astype(str)
    )

    # --------------------------------------------------------
    # 5. Human-readable commercial evidence.
    # --------------------------------------------------------

    evidence_display_map = {
        "Active + High Activity":
            "Active treatment with higher prescribing activity",

        "Active + Lower Activity":
            "Active treatment with lower prescribing activity",

        "Historical + High Activity":
            "Historical treatment with higher prescribing activity",

        "Historical + Lower Activity":
            "Historical treatment with lower prescribing activity",

        "Gap + High Activity":
            "High prescribing activity with treatment gap",

        "Gap + Lower Activity":
            "Lower prescribing activity with treatment gap",
    }

    priority_data["Commercial Evidence"] = (
        priority_data["Commercial_Evidence_Category"]
        .map(evidence_display_map)
        .fillna(priority_data["Commercial_Evidence_Category"])
    )

    # --------------------------------------------------------
    # 6. HCP-level opportunity landscape.
    # --------------------------------------------------------

    priority_fig = px.scatter(
        priority_data,
        x="Observed Diagnosed Patients",
        y="Observed Treatment Gap (%)",
        size="TRx Proxy",
        color="Commercial_Evidence_Category",

        color_discrete_sequence=px.colors.qualitative.Set2,

        hover_name="HCP Display Name",

        hover_data={
            "Prescribing_HCP_ID": True,
            "Province": True,
            "Specialty": True,
            "Opportunity Type": True,
            "Commercial Evidence": True,
            "Observed Diagnosed Patients": ":,.0f",
            "Observed Treatment Gap (%)": ":.1f",
            "TRx Proxy": ":,.0f",
            "Unique_Patients": ":,.0f",
            "Condition": False,
            "Therapy_Class": False,
            "Commercial_Evidence_Category": False,
        },

        labels={
            "Prescribing_HCP_ID": "HCP ID",
            "Province": "Province",
            "Specialty": "Specialty",
            "Opportunity Type": "Opportunity",
            "Commercial Evidence": "Commercial Evidence",
            "Observed Diagnosed Patients": "Diagnosed Patients",
            "Observed Treatment Gap (%)": "Treatment Gap",
            "TRx Proxy": "TRx",
            "Unique_Patients": "Observed Treated Patients",
        },

        size_max=22,
    )

    priority_fig.update_traces(
        marker=dict(
            opacity=0.50,
            line=dict(
                width=0.4,
                color="rgba(255,255,255,0.30)"
            )
        ),

        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "HCP ID: %{customdata[0]}<br>"
            "Province: %{customdata[1]}<br>"
            "Specialty: %{customdata[2]}<br>"
            "<br>"
            "<b>%{customdata[3]}</b><br>"
            "Commercial Evidence: %{customdata[4]}<br>"
            "<br>"
            "Diagnosed Patients: %{x:,.0f}<br>"
            "Treatment Gap: %{y:.1f}%<br>"
            "TRx: %{marker.size:,.0f}<br>"
            "Observed Treated Patients: %{customdata[5]:,.0f}"
            "<extra></extra>"
        )
    )


    priority_fig.update_layout(
        height=650,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#43AADB"
        ),

        xaxis=dict(
            title="Observed Diagnosed Patients",
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
            showline=False,
        ),

        yaxis=dict(
            title="Observed Treatment Gap (%)",
            range=[0, 100],
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
            showline=False,
        ),

        legend=dict(
            title="Commercial Evidence",
            font=dict(size=10),
        ),
    )

    st.plotly_chart(
        priority_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        "Each bubble represents an HCP-condition-therapy opportunity. "
        "X-axis shows the observed diagnosed patient population associated "
        "with the HCP and condition in the synthetic longitudinal timeline. "
        "Y-axis shows the proportion of those observed diagnosed patients "
        "without observed treatment for the same HCP-condition relationship. "
        "Bubble size represents observed TRx activity. "
        "Signals are derived from synthetic data and should be interpreted "
        "as analytical opportunity signals rather than real-world patient panels."
    )


    # ========================================================
    # SECOND ROW — OPPORTUNITY CONCENTRATION
    # ========================================================

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # LEFT — OPPORTUNITY VOLUME BY CONDITION
    # --------------------------------------------------------

    with col1:

        st.markdown("#### Opportunity Volume by Condition")

        condition_opportunity = (
            priority_data
            .groupby(
                [
                    "Condition",
                    "Commercial_Evidence_Category",
                ],
                as_index=False,
            )
            .size()
            .rename(columns={"size": "Opportunity_Count"})
        )

        condition_opportunity["Condition Display"] = (
            condition_opportunity["Condition"]
            .map(disease_display_names)
            .fillna(condition_opportunity["Condition"])
        )

        condition_opportunity["Commercial Evidence"] = (
            condition_opportunity["Commercial_Evidence_Category"]
            .map(evidence_display_map)
            .fillna(
                condition_opportunity["Commercial_Evidence_Category"]
            )
        )

        condition_fig = px.bar(
            condition_opportunity,
            x="Opportunity_Count",
            y="Condition Display",
            color="Commercial_Evidence_Category",
            orientation="h",

            color_discrete_map=COMMERCIAL_EVIDENCE_COLORS,

            custom_data=[
                "Commercial Evidence",
                "Opportunity_Count",
            ],

            hover_data={
                "Condition": False,
                "Condition Display": False,
                "Commercial_Evidence_Category": False,
                "Commercial Evidence": False,
                "Opportunity_Count": False,
            },

            labels={
                "Opportunity_Count": "Opportunities",
                "Condition Display": "Condition",
            },
        )

        condition_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Opportunities: %{customdata[1]:,.0f}<br>"
                "Commercial Evidence: %{customdata[0]}"
                "<extra></extra>"
            )
        )

        condition_fig.update_layout(
            height=520,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",

            xaxis=dict(
                title="Opportunities",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
                showline=False,
            ),

            yaxis=dict(
                title=None,
                gridcolor="rgba(0,0,0,0)",
                zeroline=False,
                showline=False,
                categoryorder="total ascending",
            ),

            legend=dict(
                title="Commercial Evidence",
                font=dict(size=10),
            ),

            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            condition_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # --------------------------------------------------------
    # RIGHT — OPPORTUNITY MIX BY THERAPY CLASS
    # --------------------------------------------------------

    with col2:

        st.markdown("#### Opportunity Mix by Therapy Class")

        therapy_opportunity = (
            priority_data
            .groupby(
                [
                    "Therapy_Class",
                    "Commercial_Evidence_Category",
                ],
                as_index=False,
            )
            .size()
            .rename(columns={"size": "Opportunity_Count"})
        )

        therapy_opportunity["Commercial Evidence"] = (
            therapy_opportunity["Commercial_Evidence_Category"]
            .map(evidence_display_map)
            .fillna(
                therapy_opportunity["Commercial_Evidence_Category"]
            )
        )

        therapy_fig = px.bar(
            therapy_opportunity,
            x="Opportunity_Count",
            y="Therapy_Class",
            color="Commercial_Evidence_Category",
            orientation="h",

            color_discrete_map=COMMERCIAL_EVIDENCE_COLORS,

            custom_data=[
                "Commercial Evidence",
                "Opportunity_Count",
            ],

            hover_data={
                "Therapy_Class": False,
                "Commercial_Evidence_Category": False,
                "Commercial Evidence": False,
                "Opportunity_Count": False,
            },

            labels={
                "Therapy_Class": "Therapy Class",
                "Opportunity_Count": "Opportunities",
            },
        )

        therapy_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Opportunities: %{customdata[1]:,.0f}<br>"
                "Commercial Evidence: %{customdata[0]}"
                "<extra></extra>"
            )
        )

        therapy_fig.update_layout(
            height=520,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",

            xaxis=dict(
                title="Opportunities",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
                showline=False,
            ),

            yaxis=dict(
                title=None,
                gridcolor="rgba(0,0,0,0)",
                zeroline=False,
                showline=False,
                categoryorder="total ascending",
            ),

            legend=dict(
                title="Commercial Evidence",
                font=dict(size=10),
            ),

            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            therapy_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ========================================================
    # THIRD ROW — OPPORTUNITY PRIORITIZATION
    # ========================================================

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # LEFT — OPPORTUNITY VOLUME BY PROVINCE
    # --------------------------------------------------------

    with col1:

        st.markdown("#### Opportunity Volume by Province")

        province_opportunity = (
            priority_data
            .groupby(
                [
                    "Province",
                    "Commercial_Evidence_Category",
                ],
                as_index=False,
            )
            .size()
            .rename(columns={"size": "Opportunity_Count"})
        )

        province_opportunity["Commercial Evidence"] = (
            province_opportunity["Commercial_Evidence_Category"]
            .map(evidence_display_map)
            .fillna(
                province_opportunity["Commercial_Evidence_Category"]
            )
        )

        province_fig = px.bar(
            province_opportunity,
            x="Opportunity_Count",
            y="Province",
            color="Commercial_Evidence_Category",
            orientation="h",

            color_discrete_map=COMMERCIAL_EVIDENCE_COLORS,

            custom_data=[
                "Commercial Evidence",
                "Opportunity_Count",
            ],

            hover_data={
                "Province": False,
                "Commercial_Evidence_Category": False,
                "Commercial Evidence": False,
                "Opportunity_Count": False,
            },

            labels={
                "Province": "Province",
                "Opportunity_Count": "Opportunities",
            },
        )

        province_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Opportunities: %{customdata[1]:,.0f}<br>"
                "Commercial Evidence: %{customdata[0]}"
                "<extra></extra>"
            )
        )

        province_fig.update_layout(
            height=520,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",

            xaxis=dict(
                title="Opportunities",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
                showline=False,
            ),

            yaxis=dict(
                title=None,
                gridcolor="rgba(0,0,0,0)",
                zeroline=False,
                showline=False,
                categoryorder="total ascending",
            ),

            legend=dict(
                title="Commercial Evidence",
                font=dict(size=10),
            ),

            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            province_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # --------------------------------------------------------
    # RIGHT — TOP OPPORTUNITY AREAS BY DISEASE
    # --------------------------------------------------------

    with col2:

        st.markdown("#### Top Opportunity Areas by Disease")

        # ----------------------------------------------------
        # Build disease-level metrics without double-counting
        # diagnosed patients or treatment-gap patients.
        # ----------------------------------------------------

        disease_diagnosed_pairs = (
            filtered_diagnosed[
                ["Patient_ID", "Condition"]
            ]
            .dropna(subset=["Patient_ID", "Condition"])
            .drop_duplicates()
        )

        disease_treated_pairs = (
            treatments.loc[
                treatments["Patient_ID"].isin(filtered_patient_ids),
                ["Patient_ID", "Condition"],
            ]
            .dropna(subset=["Patient_ID", "Condition"])
            .drop_duplicates()
        )

        disease_patient_status = disease_diagnosed_pairs.merge(
            disease_treated_pairs.assign(
                Observed_Treatment=True
            ),
            on=["Patient_ID", "Condition"],
            how="left",
        )

        disease_patient_status["Observed_Treatment"] = (
            disease_patient_status["Observed_Treatment"]
            .fillna(False)
            .astype(bool)
        )

        disease_patient_summary = (
            disease_patient_status
            .groupby("Condition", as_index=False)
            .agg(
                Observed_Diagnosed_Patients=(
                    "Patient_ID",
                    "nunique",
                ),
                Observed_Treatment_Gap_Patients=(
                    "Observed_Treatment",
                    lambda values: int((~values).sum()),
                ),
            )
        )

        # Aggregate opportunity-linked activity separately.
        # TRx is an opportunity-level proxy, not unique patients.
        disease_activity_summary = (
            priority_data
            .groupby("Condition", as_index=False)
            .agg(
                TRx_Proxy=("TRx Proxy", "sum"),
                Opportunity_Count=("Condition", "size"),
            )
        )

        disease_opportunity = disease_activity_summary.merge(
            disease_patient_summary,
            on="Condition",
            how="left",
        )

        disease_opportunity[
            [
                "Observed_Diagnosed_Patients",
                "Observed_Treatment_Gap_Patients",
            ]
        ] = disease_opportunity[
            [
                "Observed_Diagnosed_Patients",
                "Observed_Treatment_Gap_Patients",
            ]
        ].fillna(0)

        disease_opportunity["Observed Treatment Gap (%)"] = (
                disease_opportunity[
                    "Observed_Treatment_Gap_Patients"
                ]
                / disease_opportunity[
                    "Observed_Diagnosed_Patients"
                ].replace(0, pd.NA)
                * 100
        ).fillna(0)

        # ----------------------------------------------------
        # Aggregate across commercial evidence categories
        # so each disease appears only once.
        # ----------------------------------------------------

        disease_opportunity = (
            disease_opportunity
            .groupby("Condition", as_index=False)
            .agg(
                Observed_Diagnosed_Patients=(
                    "Observed_Diagnosed_Patients",
                    "sum",
                ),
                Observed_Treatment_Gap_Patients=(
                    "Observed_Treatment_Gap_Patients",
                    "sum",
                ),
                TRx_Proxy=(
                    "TRx_Proxy",
                    "sum",
                ),
                Opportunity_Count=(
                    "Opportunity_Count",
                    "sum",
                ),
            )
        )

        disease_opportunity["Observed Treatment Gap (%)"] = (
                disease_opportunity[
                    "Observed_Treatment_Gap_Patients"
                ]
                / disease_opportunity[
                    "Observed_Diagnosed_Patients"
                ]
                .replace(0, pd.NA)
                * 100
        ).fillna(0)

        # ----------------------------------------------------
        # Transparent disease-level prioritization score
        # ----------------------------------------------------

        max_diagnosed = (
            disease_opportunity[
                "Observed_Diagnosed_Patients"
            ].max()
        )

        max_trx = (
            disease_opportunity[
                "TRx_Proxy"
            ].max()
        )

        disease_opportunity["Diagnosed Score"] = (
            disease_opportunity[
                "Observed_Diagnosed_Patients"
            ]
            / max_diagnosed
            if max_diagnosed > 0
            else 0
        )

        disease_opportunity["Treatment Gap Score"] = (
                disease_opportunity[
                    "Observed Treatment Gap (%)"
                ]
                / 100
        )

        disease_opportunity["TRx Score"] = (
            disease_opportunity[
                "TRx_Proxy"
            ]
            / max_trx
            if max_trx > 0
            else 0
        )

        disease_opportunity["Opportunity Priority Score"] = (
                0.40 * disease_opportunity["Diagnosed Score"]
                + 0.30 * disease_opportunity["Treatment Gap Score"]
                + 0.30 * disease_opportunity["TRx Score"]
        )

        # ----------------------------------------------------
        # Disease display names
        # ----------------------------------------------------

        disease_opportunity["Condition Display"] = (
            disease_opportunity["Condition"]
            .map(disease_display_names)
            .fillna(
                disease_opportunity["Condition"].astype(str)
            )
        )

        # Highest-priority disease areas first
        disease_opportunity = (
            disease_opportunity
            .sort_values(
                "Opportunity Priority Score",
                ascending=False,
            )
            .head(10)
            .copy()
        )

        # ----------------------------------------------------
        # Chart
        # ----------------------------------------------------

        disease_fig = px.bar(
            disease_opportunity,
            x="Opportunity Priority Score",
            y="Condition Display",
            orientation="h",

            color_discrete_sequence=["#4F46E5"],

            custom_data=[
                "Observed_Diagnosed_Patients",
                "Observed Treatment Gap (%)",
                "TRx_Proxy",
                "Opportunity_Count",
            ],

            labels={
                "Condition Display": "Condition",
                "Opportunity Priority Score": "Priority Score",
            },
        )

        disease_fig.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Priority Score: %{x:.2f}<br>"
                "<br>"
                "Diagnosed Patients: %{customdata[0]:,.0f}<br>"
                "Treatment Gap: %{customdata[1]:.1f}%<br>"
                "TRx: %{customdata[2]:,.0f}<br>"
                "Opportunities: %{customdata[3]:,.0f}"
                "<extra></extra>"
            )
        )

        disease_fig.update_layout(
            height=520,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",

            xaxis=dict(
                title="Priority Score",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
                showline=False,
            ),

            yaxis=dict(
                title=None,
                gridcolor="rgba(0,0,0,0)",
                zeroline=False,
                showline=False,
                categoryorder="total ascending",
                automargin=True,
            ),

            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            disease_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ========================================================
    # ROW 4 — STRATEGIC TAKEAWAY
    # ========================================================

    st.markdown("### Strategic Takeaway")

    st.write(
        "Translate the highest-priority disease areas into concise "
        "portfolio-level commercial priorities."
    )

    if disease_opportunity.empty:

        st.info(
            "No strategic priorities are available for the selected filters."
        )

    else:

        # ----------------------------------------------------
        # Identify top disease areas
        # ----------------------------------------------------

        top_priorities = (
            disease_opportunity
            .sort_values(
                "Opportunity Priority Score",
                ascending=False,
            )
            .head(3)
            .copy()
        )

        # ----------------------------------------------------
        # Build strategic signal for each disease
        # ----------------------------------------------------

        def build_strategic_signal(row):

            diagnosed = row["Observed_Diagnosed_Patients"]
            gap = row["Observed Treatment Gap (%)"]
            trx = row["TRx_Proxy"]

            if gap >= 30 and diagnosed >= (
                    disease_opportunity["Observed_Diagnosed_Patients"].median()
            ):
                return (
                    "High patient volume with a meaningful "
                    "observed treatment gap"
                )

            elif trx >= (
                    disease_opportunity["TRx_Proxy"].median()
            ):
                return (
                    "Meaningful prescribing activity indicates "
                    "an established commercial opportunity"
                )

            elif gap >= 30:
                return (
                    "Treatment gap remains a notable "
                    "opportunity signal"
                )

            else:
                return (
                    "Observed activity indicates a developing "
                    "commercial opportunity"
                )

        top_priorities["Strategic Signal"] = (
            top_priorities.apply(
                build_strategic_signal,
                axis=1,
            )
        )

        # ----------------------------------------------------
        # Build strategic implication
        # ----------------------------------------------------

        def build_strategic_implication(row):

            diagnosed = row["Observed_Diagnosed_Patients"]
            gap = row["Observed Treatment Gap (%)"]
            trx = row["TRx_Proxy"]

            if (
                    diagnosed >= disease_opportunity[
                "Observed_Diagnosed_Patients"
            ].median()
                    and gap >= 30
            ):
                return (
                    "Large observed patient opportunity combined "
                    "with unmet treatment activity."
                )

            elif trx >= disease_opportunity[
                "TRx_Proxy"
            ].median():
                return (
                    "Existing prescribing activity suggests "
                    "an opportunity to strengthen and grow the market."
                )

            elif gap >= 30:
                return (
                    "Treatment activity appears lower relative "
                    "to the observed diagnosed population."
                )

            else:
                return (
                    "The opportunity is smaller or less mature "
                    "relative to the highest-priority disease areas."
                )

        top_priorities["Strategic Implication"] = (
            top_priorities.apply(
                build_strategic_implication,
                axis=1,
            )
        )

        # ----------------------------------------------------
        # Render executive priority cards
        # ----------------------------------------------------

        priority_cols = st.columns(len(top_priorities))

        for col, (_, row) in zip(
                priority_cols,
                top_priorities.iterrows(),
        ):
            with col:
                condition_display = (
                    row["Condition Display"]
                )

                priority_score = (
                    row["Opportunity Priority Score"]
                )

                diagnosed = (
                    row["Observed_Diagnosed_Patients"]
                )

                gap = (
                    row["Observed Treatment Gap (%)"]
                )

                trx = (
                    row["TRx_Proxy"]
                )

                opportunity_count = (
                    row["Opportunity_Count"]
                )

                st.markdown(
                    f"#### {condition_display}"
                )

                st.metric(
                    "Priority Score",
                    f"{priority_score:.2f}",
                )

                st.markdown(
                    f"""
                    **Strategic Signal**  
                    {row["Strategic Signal"]}

                    **Observed Scale**  
                    {diagnosed:,.0f} diagnosed patients ·
                    {gap:.1f}% treatment gap ·
                    {trx:,.0f} TRx

                    **Opportunity Areas**  
                    {opportunity_count:,.0f} HCP-condition-therapy opportunities
                    """
                )

                st.caption(
                    row["Strategic Implication"]
                )

        # ----------------------------------------------------
        # Overall strategic action
        # ----------------------------------------------------

        st.markdown("---")

        highest_priority = top_priorities.iloc[0]

        highest_condition = (
            highest_priority["Condition Display"]
        )

        highest_gap = (
            highest_priority["Observed Treatment Gap (%)"]
        )

        highest_diagnosed = (
            highest_priority["Observed_Diagnosed_Patients"]
        )

        highest_trx = (
            highest_priority["TRx_Proxy"]
        )

        if (
                highest_gap >= 30
                and highest_diagnosed >= disease_opportunity[
            "Observed_Diagnosed_Patients"
        ].median()
        ):

            strategic_action = (
                f"Prioritize {highest_condition} for deeper commercial "
                "assessment, with emphasis on the observed treatment "
                "gap and the HCP segments associated with this opportunity."
            )

        elif highest_trx >= disease_opportunity[
            "TRx_Proxy"
        ].median():

            strategic_action = (
                f"Prioritize {highest_condition} for commercial development "
                "by assessing opportunities to strengthen existing "
                "prescribing activity and expand treatment uptake."
            )

        else:

            strategic_action = (
                f"Continue monitoring {highest_condition} as a developing "
                "commercial opportunity and assess whether additional "
                "patient, HCP, or access signals strengthen the case for action."
            )

        st.info(
            f"**Recommended Strategic Focus — {highest_condition}**\n\n"
            f"{strategic_action}"
        )

        st.caption(
            "Strategic priorities are derived from observed synthetic "
            "patient, treatment, prescription, HCP, and access signals. "
            "They represent analytical commercial opportunity signals "
            "and are not clinical recommendations or causal conclusions."
        )


    # ========================================================
    # ROW 5 — COMMERCIAL OPPORTUNITY BRIEF
    # ========================================================

    st.divider()
    st.markdown("### Commercial Opportunity Brief")

    st.write(
        "Explore the evidence behind a disease-level priority, "
        "understand the commercial signal, and identify what to "
        "investigate next."
    )

    if disease_opportunity.empty:

        st.info(
            "No opportunity brief is available for the selected filters."
        )

    else:

        # ----------------------------------------------------
        # Select a disease from the current priority landscape
        # ----------------------------------------------------

        brief_conditions = (
            disease_opportunity["Condition"]
            .drop_duplicates()
            .tolist()
        )

        selected_brief_condition = st.selectbox(
            "Select a disease area",
            options=brief_conditions,
            format_func=lambda condition: disease_display_names.get(
                condition,
                condition,
            ),
            key="commercial_opportunity_brief_condition",
        )

        brief = disease_opportunity.loc[
            disease_opportunity["Condition"]
            == selected_brief_condition
        ].iloc[0]

        brief_condition_name = brief["Condition Display"]
        brief_diagnosed = int(
            brief["Observed_Diagnosed_Patients"]
        )
        brief_gap = float(
            brief["Observed Treatment Gap (%)"]
        )
        brief_gap_patients = int(
            brief["Observed_Treatment_Gap_Patients"]
        )
        brief_trx = float(
            brief["TRx_Proxy"]
        )
        brief_opportunities = int(
            brief["Opportunity_Count"]
        )
        brief_score = float(
            brief["Opportunity Priority Score"]
        )

        median_diagnosed = disease_opportunity[
            "Observed_Diagnosed_Patients"
        ].median()

        median_trx = disease_opportunity[
            "TRx_Proxy"
        ].median()

        # ----------------------------------------------------
        # Evidence snapshot
        # ----------------------------------------------------

        st.markdown(
            f"#### Evidence Snapshot: {brief_condition_name}"
        )

        brief_kpi1, brief_kpi2, brief_kpi3, brief_kpi4 = (
            st.columns(4)
        )

        with brief_kpi1:
            st.metric(
                "Diagnosed Patients",
                f"{brief_diagnosed:,}",
            )

        with brief_kpi2:
            st.metric(
                "Observed Treatment Gap",
                f"{brief_gap:.1f}%",
            )

        with brief_kpi3:
            st.metric(
                "TRx Proxy",
                f"{brief_trx:,.0f}",
            )

        with brief_kpi4:
            st.metric(
                "Opportunity Areas",
                f"{brief_opportunities:,}",
            )

        st.metric(
            "Opportunity Priority Score",
            f"{brief_score:.2f}",
        )

        # ----------------------------------------------------
        # Explain the score using its actual components
        # ----------------------------------------------------


        # ----------------------------------------------------
        # Explain the weighted contribution to the priority score
        # ----------------------------------------------------

        st.markdown("#### Priority Score Breakdown")

        brief_volume_contribution = (
            0.40 * float(brief["Diagnosed Score"])
        )
        brief_gap_contribution = (
            0.30 * float(brief["Treatment Gap Score"])
        )
        brief_trx_contribution = (
            0.30 * float(brief["TRx Score"])
        )

        brief_calculated_score = (
            brief_volume_contribution
            + brief_gap_contribution
            + brief_trx_contribution
        )

        score_col1, score_col2, score_col3, score_col4 = (
            st.columns(4)
        )

        with score_col1:
            st.metric(
                "Patient Volume",
                f"{brief_volume_contribution:.3f}",
                help="Weighted contribution: 40% of the composite score.",
            )

        with score_col2:
            st.metric(
                "Treatment Gap",
                f"{brief_gap_contribution:.3f}",
                help="Weighted contribution: 30% of the composite score.",
            )

        with score_col3:
            st.metric(
                "TRx Activity",
                f"{brief_trx_contribution:.3f}",
                help="Weighted contribution: 30% of the composite score.",
            )

        with score_col4:
            st.metric(
                "Calculated Total",
                f"{brief_calculated_score:.3f}",
                help=(
                    "Sum of the three weighted contributions. "
                    "The headline priority score is rounded to two decimals."
                ),
            )


        # ----------------------------------------------------
        # Deterministic commercial interpretation
        # ----------------------------------------------------

        if (
            brief_gap >= 30
            and brief_diagnosed >= median_diagnosed
        ):
            brief_signal = (
                "Higher observed patient volume combined with a "
                "relatively high treatment-gap signal."
            )

            brief_interpretation = (
                f"{brief_condition_name} merits further investigation "
                "because the observed diagnosed population and "
                "treatment-gap signal are both substantial relative "
                "to the disease areas in the current priority set."
            )

            brief_next_step = (
                "Investigate treatment initiation patterns, relevant "
                "medical and pharmacy claim outcomes, and the HCP "
                "segments associated with this disease. Validate "
                "whether the apparent gap persists in reliable "
                "real-world data."
            )

        elif brief_gap >= 30:
            brief_signal = (
                "Elevated treatment-gap signal, with a smaller "
                "diagnosed population relative to the current priority set."
            )

            brief_interpretation = (
                "The treatment-gap signal may be worth exploring, "
                "but the population size and denominator should be "
                "reviewed before assigning substantial commercial "
                "priority."
            )

            brief_next_step = (
                "Review the cohort size, treatment definitions, "
                "and claim outcomes. Determine whether the signal "
                "is sufficiently robust to justify deeper assessment."
            )

        elif brief_trx >= median_trx:
            brief_signal = (
                "Relatively high observed prescription activity."
            )

            brief_interpretation = (
                "The TRx proxy contributes to this disease area's "
                "priority. This may indicate established activity "
                "within the synthetic opportunity universe, rather "
                "than an independently verified market opportunity."
            )

            brief_next_step = (
                "Examine the contributing products, therapy classes, "
                "and HCP segments. Validate the activity pattern "
                "against appropriate real-world prescription data."
            )

        else:
            brief_signal = (
                "Developing or comparatively lower-priority signal."
            )

            brief_interpretation = (
                "The current signals do not establish the same "
                "combination of patient volume, treatment gap, "
                "and prescription activity as stronger-ranked areas."
            )

            brief_next_step = (
                "Monitor the disease area and review additional "
                "patient, HCP, product, and access evidence before "
                "committing further commercial resources."
            )

        # ----------------------------------------------------
        # Render the decision brief
        # ----------------------------------------------------

        st.markdown("#### Commercial Interpretation")

        st.write(brief_signal)
        st.write(brief_interpretation)

        st.markdown("#### Recommended Next Investigation")

        st.info(brief_next_step)

        with st.expander(
            "Methodology and interpretation limitations"
        ):
            st.markdown(
                f"""
                - **Priority score:** 40% normalized diagnosed-patient
                  volume, 30% observed treatment-gap rate, and 30%
                  normalized TRx proxy.
                - **Treatment gap:** diagnosed patient-condition pairs
                  without an observed treatment record in the selected
                  cohort. This is a synthetic-data signal, not proof
                  of unmet clinical need.
                - **TRx proxy:** an aggregated opportunity-level
                  prescription activity measure. It is not a count
                  of unique patients or a validated market forecast.
                - **Opportunity areas:** HCP-condition-therapy
                  opportunity records; multiple records may relate
                  to the same disease or patient population.
                - **Comparisons:** relative scores depend on the
                  selected filters and the disease areas included in
                  the current priority set.
                """
            )
