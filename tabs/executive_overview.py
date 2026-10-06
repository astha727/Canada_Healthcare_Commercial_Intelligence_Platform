import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import numpy as np


def show_executive_overview(
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

        st.subheader("Executive Overview")

        st.caption(
            "Overview across market, disease, "
            "patients, HCPs, access, products, and opportunities."
        )

        # ========================================================
        # GLOBAL FILTERS
        # ========================================================

        st.markdown("### Filters")

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            selected_province = st.selectbox(
                "Province",
                ["All"] + sorted(
                    patients["Province"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

        with filter_col2:
            selected_condition = st.selectbox(
                "Condition",
                ["All"] + sorted(
                    diagnoses["Condition"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

        with filter_col3:
            selected_therapy = st.selectbox(
                "Therapy Class",
                ["All"] + sorted(
                    treatments["Therapy_Class"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

        with filter_col4:
            selected_claim_status = st.selectbox(
                "Claim Status",
                ["All"] + sorted(
                    pharmacy_claims["Claim_Status"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )
        # ========================================================
        # APPLY FILTERS
        # ========================================================

        # Patient filter
        filtered_patients = patients.copy()

        if selected_province != "All":
            filtered_patients = filtered_patients[
                filtered_patients["Province"] == selected_province
                ]

        # Province comes from Patient Master through Patient_ID
        if selected_province != "All":
            province_patients = patients.loc[
                patients["Province"] == selected_province,
                "Patient_ID"
            ]

            filtered_diagnoses = filtered_diagnoses[
                filtered_diagnoses["Patient_ID"].isin(province_patients)
            ]

        if selected_condition != "All":
            filtered_diagnoses = filtered_diagnoses[
                filtered_diagnoses["Condition"] == selected_condition
                ]

        # Province comes from Patient Master through Patient_ID
        if selected_province != "All":
            province_patients = patients.loc[
                patients["Province"] == selected_province,
                "Patient_ID"
            ]

            filtered_treatments = filtered_treatments[
                filtered_treatments["Patient_ID"].isin(province_patients)
            ]

        if selected_condition != "All":
            filtered_treatments = filtered_treatments[
                filtered_treatments["Condition"] == selected_condition
                ]

        if selected_therapy != "All":
            filtered_treatments = filtered_treatments[
                filtered_treatments["Therapy_Class"] == selected_therapy
                ]

        # Rx Event filter
        filtered_rx_events = rx_events.copy()

        filtered_rx_events = filtered_rx_events[
            filtered_rx_events["Treatment_ID"].isin(
                filtered_treatments["Treatment_ID"]
            )
        ]

        # Pharmacy Claim filter
        filtered_pharmacy_claims = pharmacy_claims.copy()

        # Keep claims linked to the filtered Rx events
        filtered_pharmacy_claims = filtered_pharmacy_claims[
            filtered_pharmacy_claims["Rx_Event_ID"].isin(
                filtered_rx_events["Rx_Event_ID"]
            )
        ]

        # Apply claim status filter
        if selected_claim_status != "All":
            filtered_pharmacy_claims = filtered_pharmacy_claims[
                filtered_pharmacy_claims["Claim_Status"] == selected_claim_status
                ]

        # Medical Claim filter
        filtered_medical_claims = medical_claims.copy()

        if selected_province != "All":
            filtered_medical_claims = filtered_medical_claims[
                filtered_medical_claims["Patient_ID"].isin(
                    filtered_patients["Patient_ID"]
                )
            ]

        if selected_condition != "All":
            filtered_medical_claims = filtered_medical_claims[
                filtered_medical_claims["Primary_Condition"] == selected_condition
                ]

        if selected_province != "All":
            filtered_opportunities = filtered_opportunities[
                filtered_opportunities["Province"] == selected_province
                ]

        if selected_condition != "All":
            filtered_opportunities = filtered_opportunities[
                filtered_opportunities["Condition"] == selected_condition
                ]

        if selected_therapy != "All":
            filtered_opportunities = filtered_opportunities[
                filtered_opportunities["Therapy_Class"] == selected_therapy
                ]

        # ========================================================
        # KPI CARDS
        # ========================================================

        st.markdown("### Commercial Ecosystem Snapshot")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(
                "Synthetic Patients",
                f"{filtered_patients['Patient_ID'].nunique():,}"
            )

        with kpi2:
            st.metric(
                "Diagnosed Patients",
                f"{filtered_diagnoses['Patient_ID'].nunique():,}"
            )

        with kpi3:
            st.metric(
                "Treatment Episodes",
                f"{filtered_treatments['Treatment_ID'].nunique():,}"
            )

        with kpi4:
            st.metric(
                "Rx Events",
                f"{filtered_rx_events['Rx_Event_ID'].nunique():,}"
            )

        kpi5, kpi6, kpi7, kpi8 = st.columns(4)

        with kpi5:
            st.metric(
                "HCPs",
                f"{filtered_opportunities['Prescribing_HCP_ID'].nunique():,}"
            )

        with kpi6:
            st.metric(
                "Pharmacy Claims",
                f"{filtered_pharmacy_claims['Rx_Claim_ID'].nunique():,}"
            )

        with kpi7:
            st.metric(
                "Medical Claims",
                f"{filtered_medical_claims['Medical_Claim_ID'].nunique():,}"
            )

        with kpi8:
            st.metric(
                "Opportunity Relationships",
                f"{filtered_opportunities.shape[0]:,}"
            )
        # ========================================================
        # DISEASE LANDSCAPE
        # ========================================================

        disease_col, treatment_col = st.columns(2)
        with disease_col:

            st.markdown("### Disease Landscape")

            diagnosed_by_condition = (
                filtered_diagnoses
                .groupby("Condition", as_index=False)["Patient_ID"]
                .nunique()
                .rename(columns={"Patient_ID": "Diagnosed_Patients"})
                .sort_values(
                    "Diagnosed_Patients",
                    ascending=False
                )
            )
            condition_display_names = {
                "Diabetes mellitus (types combined), excluding gestational diabetes": "Diabetes",
                "Chronic obstructive pulmonary disease": "COPD",
                "Dementia, including Alzheimer disease": "Dementia",
                "Parkinsonism, including Parkinson disease": "Parkinsonism",
            }

            diagnosed_by_condition["Condition_Display"] = (
                diagnosed_by_condition["Condition"]
                .replace(condition_display_names)
            )

            disease_chart = px.bar(
                diagnosed_by_condition,
                x="Diagnosed_Patients",
                y="Condition_Display",
                orientation="h",
                title="Diagnosed Patients by Condition"
            )

            disease_chart.update_layout(
                yaxis={
                    "categoryorder": "total ascending"
                },
                xaxis_title="Diagnosed Patients",
                yaxis_title=""
            )

            st.plotly_chart(
                disease_chart,
                use_container_width=True
            )

            # ========================================================
            # TREATMENT ACTIVITY
            # ========================================================

            with treatment_col:
                st.markdown("### Treatment Activity")

                treatment_by_therapy = (
                    filtered_rx_events
                    .groupby("Therapy_Class", as_index=False)["Rx_Event_ID"]
                    .count()
                    .rename(columns={"Rx_Event_ID": "TRx_Proxy"})
                    .sort_values(
                        "TRx_Proxy",
                        ascending=False
                    )
                )

                treatment_chart = px.bar(
                    treatment_by_therapy,
                    x="TRx_Proxy",
                    y="Therapy_Class",
                    orientation="h",
                    title="Rx Activity by Therapy Class"
                )

                treatment_chart.update_layout(
                    yaxis={
                        "categoryorder": "total ascending"
                    },
                    xaxis_title="TRx Proxy",
                    yaxis_title=""
                )

                st.plotly_chart(
                    treatment_chart,
                    use_container_width=True
                )

        # ========================================================
        # ACCESS AND COMMERCIAL OPPORTUNITY
        # ========================================================

        access_col, opportunity_col = st.columns(2)

        # ========================================================
        # ACCESS SNAPSHOT
        # ========================================================

        with access_col:

            st.markdown("### Access Snapshot")

            access_summary = (
                filtered_pharmacy_claims
                .groupby("Claim_Status", as_index=False)["Rx_Claim_ID"]
                .count()
                .rename(columns={"Rx_Claim_ID": "Claim_Count"})
            )

            access_chart = px.pie(
                access_summary,
                names="Claim_Status",
                values="Claim_Count",
                hole=0.55,
                title="Synthetic Pharmacy Claims by Status"
            )

            access_chart.update_traces(
                textinfo="percent+label"
            )

            access_chart.update_layout(
                showlegend=True
            )

            st.plotly_chart(
                access_chart,
                use_container_width=True
            )

        # ========================================================
        # COMMERCIAL OPPORTUNITY
        # ========================================================

        with opportunity_col:

            st.markdown("### Commercial Opportunity")

            opportunity_summary = (
                filtered_opportunities
                .groupby("Commercial_Evidence_Category", as_index=False)
                .size()
                .rename(columns={"size": "Relationship_Count"})
            )

            opportunity_chart = px.pie(
                opportunity_summary,
                names="Commercial_Evidence_Category",
                values="Relationship_Count",
                hole=0.55,
                title="Commercial Evidence Categories"
            )

            opportunity_chart.update_traces(
                textinfo="percent+label"
            )

            opportunity_chart.update_layout(
                showlegend=True
            )

            st.plotly_chart(
                opportunity_chart,
                use_container_width=True
            )

            st.caption(
                "**Active** = an active synthetic treatment is observed. "
                "**Historical** = only discontinued/historical treatment activity is observed. "
                "**High Activity** = TRx Proxy is at or above the 75th percentile. "
                "**Lower Activity** = TRx Proxy is below the 75th percentile."
            )

        # ========================================================
        # COMMERCIAL OPPORTUNITY HIGHLIGHTS
        # TOP 5 HCPs WITHIN TOP 5 CONDITIONS
        # ========================================================

        st.markdown("### Commercial Opportunity Highlights")

        # Top 5 conditions based on diagnosed patient volume
        top_conditions = (
            filtered_diagnoses
            .groupby("Condition")["Patient_ID"]
            .nunique()
            .sort_values(ascending=False)
            .head(5)
            .index
            .tolist()
        )

        # Keep only opportunities within the top 5 conditions
        opportunity_highlights = filtered_opportunities[
            filtered_opportunities["Condition"].isin(top_conditions)
        ].copy()

        # Rank HCP-condition-therapy relationships within each condition
        opportunity_highlights["Condition_Rank"] = (
            opportunity_highlights
            .groupby("Condition")["TRx_Proxy"]
            .rank(
                method="first",
                ascending=False
            )
        )

        # Keep top 5 relationships per condition
        opportunity_highlights = (
            opportunity_highlights[
                opportunity_highlights["Condition_Rank"] <= 5
                ]
            .sort_values(
                ["Condition", "TRx_Proxy"],
                ascending=[True, False]
            )
            [
                [
                    "Condition",
                    "HCP_Name",
                    "Specialty",
                    "Therapy_Class",
                    "TRx_Proxy",
                    "NRx_Proxy",
                    "Active_Treatment_Flag",
                    "Commercial_Evidence_Category",
                    "Engagement_Recommendation"
                ]
            ]
            .copy()
        )

        opportunity_highlights = opportunity_highlights.rename(
            columns={
                "HCP_Name": "HCP",
                "Therapy_Class": "Therapy",
                "TRx_Proxy": "TRx Proxy",
                "NRx_Proxy": "NRx Proxy",
                "Active_Treatment_Flag": "Active",
                "Commercial_Evidence_Category": "Evidence",
                "Engagement_Recommendation": "Engagement"
            }
        )

        opportunity_highlights["Active"] = (
            opportunity_highlights["Active"]
            .map({True: "Yes", False: "No"})
        )

        st.dataframe(
            opportunity_highlights,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Top 5 HCP–condition–therapy relationships by synthetic TRx Proxy "
            "within the five conditions with the largest diagnosed patient populations. "
            "Active = at least one active synthetic treatment episode is observed "
            "for the HCP–condition–therapy relationship; it does not indicate a "
            "recent HCP encounter or confirmed prescribing responsibility."
        )