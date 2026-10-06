import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np




def show_hcp_engagement(
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


    st.subheader("HCP & Engagement")

    st.caption(
        "HCP-level view of observed patient, treatment, "
        "and engagement activity."
    )

    st.markdown("### HCP Targeting & Prioritization")

    st.write(
        "Identify HCPs of interest by geography, specialty, and condition "
        "before drilling into an individual HCP."
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        selected_province = st.selectbox(
            "Province",
            ["All"] + sorted(
                filtered_opportunities["Province"]
                .dropna()
                .unique()
                .tolist()
            ),
            key="hcp_target_province"
        )

    with filter_col2:
        selected_specialty = st.selectbox(
            "Specialty",
            ["All"] + sorted(
                filtered_opportunities["Specialty"]
                .dropna()
                .unique()
                .tolist()
            ),
            key="hcp_target_specialty"
        )

    with filter_col3:
        condition_options = sorted(
            filtered_opportunities["Condition"]
            .map(disease_display_names)
            .dropna()
            .unique()
            .tolist()
        )

        selected_condition = st.selectbox(
            "Condition",
            ["All"] + condition_options,
            key="hcp_target_condition"
        )

    target_hcp_opportunities = filtered_opportunities.copy()

    if selected_province != "All":
        target_hcp_opportunities = target_hcp_opportunities[
            target_hcp_opportunities["Province"] == selected_province
            ]

    if selected_specialty != "All":
        target_hcp_opportunities = target_hcp_opportunities[
            target_hcp_opportunities["Specialty"] == selected_specialty
            ]

    if selected_condition != "All":
        target_hcp_opportunities = target_hcp_opportunities[
            target_hcp_opportunities["Condition"]
            .map(disease_display_names) == selected_condition
            ]

    hcp_target_list = (
        target_hcp_opportunities
        .groupby(
            [
                "Prescribing_HCP_ID",
                "HCP_Name",
                "Specialty",
                "Province"
            ]
        )
        .agg(
            Patients=("Unique_Patients", "sum"),
            TRx_Proxy=("TRx_Proxy", "sum"),
            Conditions=("Condition", "nunique"),
            High_Activity=("High_TRx_Activity_Flag", "sum")
        )
        .reset_index()
    )

    st.markdown("#### HCP Target List")

    if hcp_target_list.empty:

        st.info(
            "No HCPs match the selected targeting criteria."
        )

    else:

        st.dataframe(
            hcp_target_list[
                [
                    "HCP_Name",
                    "Specialty",
                    "Province",
                    "Patients",
                    "TRx_Proxy",
                    "Conditions",
                    "High_Activity"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        hcp_selection = hcp_target_list[
            [
                "Prescribing_HCP_ID",
                "HCP_Name"
            ]
        ].copy()

        hcp_selection["Display"] = (
                hcp_selection["HCP_Name"]
                + " — "
                + hcp_selection["Prescribing_HCP_ID"]
        )

        selected_hcp_display = st.selectbox(
            "Select HCP to view details",
            hcp_selection["Display"].tolist(),
            key="hcp_target_selection"
        )

        selected_hcp = hcp_selection.loc[
            hcp_selection["Display"] == selected_hcp_display,
            "Prescribing_HCP_ID"
        ].iloc[0]

        # ====================================================
        # HCP PROFILE
        # ====================================================

        hcp_details = hcp_master[
            hcp_master["HCP_ID"] == selected_hcp
            ].iloc[0]

        st.markdown("### HCP Profile")

        # ====================================================
        # HCP PATIENT-LEVEL ACTIVITY
        # ====================================================

        # ====================================================
        # HCP PROFILE
        # ====================================================

        hcp_details = hcp_master[
            hcp_master["HCP_ID"] == selected_hcp
            ].iloc[0]

        hcp_assessment = filtered_opportunities[
            filtered_opportunities["Prescribing_HCP_ID"] == selected_hcp
            ].copy()

        # ----------------------------------------------------
        # HCP PATIENT-LEVEL ACTIVITY
        # ----------------------------------------------------

        hcp_medical = medical_claims[
            medical_claims["HCP_ID"] == selected_hcp
            ].copy()

        hcp_rx = rx_events[
            rx_events["HCP_ID"] == selected_hcp
            ].copy()

        hcp_pharmacy = pharmacy_claims[
            pharmacy_claims["HCP_ID"] == selected_hcp
            ].copy()

        # Treatments directly linked to this HCP through Rx activity

        hcp_treatment_ids = (
            hcp_rx["Treatment_ID"]
            .dropna()
            .unique()
        )

        hcp_treatments = treatments[
            treatments["Treatment_ID"].isin(hcp_treatment_ids)
        ].copy()

        hcp_patient_ids = set(
            pd.concat([
                hcp_medical["Patient_ID"],
                hcp_rx["Patient_ID"],
                hcp_pharmacy["Patient_ID"]
            ]).dropna()
        )

        hcp_patient_count = len(hcp_patient_ids)

        hcp_encounter_count = len(hcp_medical)

        hcp_rx_count = len(hcp_rx)

        hcp_claim_count = len(hcp_pharmacy)

        # ----------------------------------------------------
        # COMMERCIAL METRICS
        # ----------------------------------------------------

        if hcp_assessment.empty:

            total_patients = 0
            total_trx = 0
            total_nrx = 0
            avg_treatment_gap = 0
            assessment_conditions = []
            high_activity_count = 0

        else:

            assessment_conditions = (
                hcp_assessment["Condition"]
                .map(disease_display_names)
                .dropna()
                .unique()
                .tolist()
            )

            total_patients = int(
                hcp_assessment["Unique_Patients"].sum()
            )

            total_trx = int(
                hcp_assessment["TRx_Proxy"].sum()
            )

            total_nrx = int(
                hcp_assessment["NRx_Proxy"].sum()
            )

            avg_treatment_gap = (
                    hcp_assessment["Treatment_Gap_Rate"]
                    .mean() * 100
            )

            high_activity_count = len(
                hcp_assessment[
                    hcp_assessment["High_TRx_Activity_Flag"].isin(
                        [True, 1]
                    )
                ]
            )

        # ----------------------------------------------------
        # PERSONA
        # ----------------------------------------------------

        # Use the strongest available synthetic commercial signal
        # to create an understandable user-facing persona.

        if hcp_assessment.empty:

            hcp_persona = "Emerging HCP"

        else:

            high_activity = (
                hcp_assessment["High_TRx_Activity_Flag"]
                .isin([True, 1])
                .any()
            )

            high_gap = (
                    avg_treatment_gap >= 25
            )

            high_trx = (
                total_trx >= hcp_assessment["TRx_Proxy"].median()
                if len(hcp_assessment) > 1
                else total_trx > 0
            )

            if high_activity and not high_gap:

                hcp_persona = "Established Clinical Leader"

            elif high_gap and high_trx:

                hcp_persona = "Growth Opportunity HCP"

            elif total_trx == 0:

                hcp_persona = "Emerging HCP"

            else:

                hcp_persona = "Digital-Ready Specialist"

        # ----------------------------------------------------
        # PROFILE LAYOUT
        # ----------------------------------------------------

        profile_col1, profile_col2 = st.columns(
            [1.05, 2.4],
            gap="large"
        )

        # ====================================================
        # LEFT — HCP IDENTITY
        # ====================================================

        st.html(
            """
            <style>
                .st-key-hcp_profile_blue {
                    background-color: #003366 !important;
                    border-radius: 12px !important;
                    padding: 20px !important;
                }

                .st-key-hcp_profile_blue h2,
                .st-key-hcp_profile_blue h3,
                .st-key-hcp_profile_blue p,
                .st-key-hcp_profile_blue strong {
                    color: #FFFFFF !important;
                }

                .st-key-hcp_profile_blue [data-testid="stCaptionContainer"] {
                    color: rgba(255,255,255,0.72) !important;
                }
            </style>
            """
        )



        with profile_col1:

            with st.container(
                    key="hcp_profile_blue",
            ):


                st.markdown(
                     f"## Dr. {hcp_details['HCP_Name']}"
                )

                st.write(
                    f"**{hcp_details['Specialty']}**"
                )

                identity_col1, identity_col2 = st.columns(2)

                with identity_col1:
                    st.caption("YEARS IN PRACTICE")
                    st.write(
                        f"**{hcp_details['Years_in_Practice']}**"
                    )

                with identity_col2:
                    st.caption("PROVINCE")
                    st.write(
                        f"**{hcp_details['Province']}**"
                    )

                st.caption("PERSONA")

                st.write(
                    f"**{hcp_persona}**"
                )
        # ====================================================
        # RIGHT — PATIENT & TREATMENT OVERVIEW
        # ====================================================

        with profile_col2:

            st.markdown("### Patient & Treatment Overview")

            overview_col1, overview_col2, overview_col3, overview_col4 = (
                st.columns(4)
            )

            with overview_col1:
                st.caption("OBSERVED PATIENTS")

                st.write(
                    f"**{total_patients:,}**"
                )

            with overview_col2:
                st.caption("CONDITIONS")

                st.write(
                    f"**{len(assessment_conditions):,}**"
                )

            with overview_col3:
                st.caption("TRx")

                st.write(
                    f"**{total_trx:,}**"
                )

            with overview_col4:
                st.caption("NRx")

                st.write(
                    f"**{total_nrx:,}**"
                )

            overview_col5, overview_col6, overview_col7 = st.columns(3)

            with overview_col5:
                st.caption("TREATMENT GAP SIGNAL")

                st.write(
                    f"**{avg_treatment_gap:.1f}%**"
                )

            with overview_col6:
                st.caption("HIGH-ACTIVITY AREAS")

                st.write(
                    f"**{high_activity_count:,}**"
                )

            with overview_col7:
                st.caption("ENCOUNTERS")

                st.write(
                    f"**{hcp_encounter_count:,}**"
                )

            if assessment_conditions:
                st.caption(
                    "Observed conditions"
                )

                st.write(
                    " · ".join(assessment_conditions)
                )

            st.caption(
                "Metrics describe observed synthetic HCP–patient and treatment activity."
            )

        # COMMERCIAL SIGNAL

        st.markdown("### Commercial Signal")

        st.caption(
            "A concise summary of the selected HCP's observed synthetic commercial signals."
        )

        signal_col1, signal_col2, signal_col3, signal_col4, signal_col5 = st.columns(5)

        with signal_col1:
            st.markdown("**Evidence**")

            if hcp_assessment.empty:
                evidence_signal = "No observed relationship"
            elif hcp_assessment["Active_Treatment_Flag"].isin([True, 1]).any():
                evidence_signal = "Active treatment relationship"
            else:
                evidence_signal = "Historical relationship"

            st.write(evidence_signal)

        with signal_col2:
            st.markdown("**Rx Activity**")

            if total_trx == 0:
                rx_activity_signal = "No observed activity"
            elif (
                    not hcp_assessment.empty
                    and hcp_assessment["High_TRx_Activity_Flag"].isin([True, 1]).any()
            ):
                rx_activity_signal = "High"
            else:
                rx_activity_signal = "Lower"

            st.write(rx_activity_signal)

        with signal_col3:
            st.markdown("**Treatment Gap**")

            if hcp_assessment.empty:
                st.write("N/A")
            else:
                st.write(f"{avg_treatment_gap:.1f}%")

        with signal_col4:
            st.markdown("**Commercial Persona**")
            st.write(hcp_persona)

        with signal_col5:
            st.markdown("**Recommended Action**")

            if hcp_assessment.empty:
                engagement_signal = "Monitor"
            elif hcp_assessment["High_TRx_Activity_Flag"].isin([True, 1]).any() and avg_treatment_gap >= 25:
                engagement_signal = "Targeted engagement"
            elif hcp_assessment["High_TRx_Activity_Flag"].isin([True, 1]).any():
                engagement_signal = "Maintain engagement"
            elif avg_treatment_gap >= 25:
                engagement_signal = "Opportunity follow-up"
            else:
                engagement_signal = "Monitor"

            st.write(engagement_signal)

        st.caption(
            "Signals are derived from observed synthetic HCP–condition–therapy relationships. "
            "They describe analytical opportunity signals and are not clinical recommendations."
        )

        # HCP LONGITUDINAL TIMELINE

        st.markdown("### Patient Activity Timeline")
        st.caption(
            "Observed synthetic patient activity associated with this HCP. "
            "Treatment spans show observed treatment episodes over time; "
            "events and monthly activity are layered on top."
        )

        # ---------------------------------------------------------
        # 1. PREPARE HCP DATA
        # ---------------------------------------------------------

        hcp_medical_timeline = hcp_medical.copy()
        hcp_rx_timeline = hcp_rx.copy()
        hcp_treatments_timeline = hcp_treatments.copy()

        hcp_medical_timeline["Claim_Date"] = pd.to_datetime(
            hcp_medical_timeline["Claim_Date"],
            errors="coerce"
        )

        hcp_rx_timeline["Fill_Date"] = pd.to_datetime(
            hcp_rx_timeline["Fill_Date"],
            errors="coerce"
        )

        hcp_treatments_timeline["Treatment_Start_Date"] = pd.to_datetime(
            hcp_treatments_timeline["Treatment_Start_Date"],
            errors="coerce"
        )

        hcp_treatments_timeline["Treatment_End_Date"] = pd.to_datetime(
            hcp_treatments_timeline["Treatment_End_Date"],
            errors="coerce"
        )

        # Observation end for active treatments
        observation_end = pd.Timestamp("2024-07-01")

        hcp_treatments_timeline["Timeline_End_Date"] = (
            hcp_treatments_timeline["Treatment_End_Date"]
            .fillna(observation_end)
        )

        hcp_treatments_timeline["Timeline_End_Date"] = (
            hcp_treatments_timeline["Timeline_End_Date"]
            .clip(upper=observation_end)
        )

        # Add product / brand information
        if "Brand_Name" in product_master.columns:
            product_lookup = (
                product_master[["Product_ID", "Brand_Name"]]
                .drop_duplicates("Product_ID")
            )

            hcp_treatments_timeline = hcp_treatments_timeline.merge(
                product_lookup,
                on="Product_ID",
                how="left"
            )
        else:
            hcp_treatments_timeline["Brand_Name"] = (
                hcp_treatments_timeline["Product_ID"]
            )

        hcp_treatments_timeline["Brand_Name"] = (
            hcp_treatments_timeline["Brand_Name"]
            .fillna(hcp_treatments_timeline["Product_ID"])
        )

        # ---------------------------------------------------------
        # 2. PATIENT ACTIVITY SUMMARY
        # ---------------------------------------------------------

        treatment_patient_ids = set(
            hcp_treatments_timeline["Patient_ID"].dropna()
        )

        rx_patient_ids = set(
            hcp_rx_timeline["Patient_ID"].dropna()
        )

        encounter_patient_ids = set(
            hcp_medical_timeline["Patient_ID"].dropna()
        )

        # Product switches
        switch_data = (
            hcp_treatments_timeline[
                [
                    "Patient_ID",
                    "Condition",
                    "Product_ID",
                    "Treatment_Start_Date"
                ]
            ]
            .dropna(subset=["Patient_ID", "Condition", "Product_ID", "Treatment_Start_Date"])
            .sort_values(
                ["Patient_ID", "Condition", "Treatment_Start_Date"]
            )
            .copy()
        )

        switch_data["Previous_Product_ID"] = (
            switch_data
            .groupby(["Patient_ID", "Condition"])["Product_ID"]
            .shift(1)
        )

        switch_data["Is_Switch"] = (
                switch_data["Previous_Product_ID"].notna()
                & (
                        switch_data["Previous_Product_ID"]
                        != switch_data["Product_ID"]
                )
        )

        switch_patient_ids = set(
            switch_data.loc[
                switch_data["Is_Switch"],
                "Patient_ID"
            ].dropna()
        )

        # Recent activity = activity within last 12 months of observation
        recent_cutoff = observation_end - pd.DateOffset(months=12)

        recent_medical_patients = set(
            hcp_medical_timeline.loc[
                hcp_medical_timeline["Claim_Date"] >= recent_cutoff,
                "Patient_ID"
            ].dropna()
        )

        recent_rx_patients = set(
            hcp_rx_timeline.loc[
                hcp_rx_timeline["Fill_Date"] >= recent_cutoff,
                "Patient_ID"
            ].dropna()
        )

        recent_treatment_patients = set(
            hcp_treatments_timeline.loc[
                hcp_treatments_timeline["Timeline_End_Date"] >= recent_cutoff,
                "Patient_ID"
            ].dropna()
        )

        recent_patient_ids = (
                recent_medical_patients
                | recent_rx_patients
                | recent_treatment_patients
        )

        # ---------------------------------------------------------
        # 3. KPI ROW
        # ---------------------------------------------------------

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(
                "Patients with Recent Activity",
                f"{len(recent_patient_ids):,}"
            )

        with kpi2:
            st.metric(
                "Patients with Treatment Activity",
                f"{len(treatment_patient_ids):,}"
            )

        with kpi3:
            st.metric(
                "Patients with Rx Activity",
                f"{len(rx_patient_ids):,}"
            )

        with kpi4:
            st.metric(
                "Patients with Product Switches",
                f"{len(switch_patient_ids):,}"
            )

        # ---------------------------------------------------------
        # 4. LATEST ACTIVITY
        # ---------------------------------------------------------

        all_activity_dates = []

        if not hcp_medical_timeline.empty:
            all_activity_dates.extend(
                hcp_medical_timeline["Claim_Date"].dropna().tolist()
            )

        if not hcp_rx_timeline.empty:
            all_activity_dates.extend(
                hcp_rx_timeline["Fill_Date"].dropna().tolist()
            )

        if not hcp_treatments_timeline.empty:
            all_activity_dates.extend(
                hcp_treatments_timeline["Timeline_End_Date"].dropna().tolist()
            )

        if all_activity_dates:
            latest_activity_date = max(all_activity_dates)

            latest_activity_labels = []

            if not hcp_rx_timeline.empty:
                if (
                        hcp_rx_timeline["Fill_Date"].max()
                        == latest_activity_date
                ):
                    latest_activity_labels.append("Rx")

            if not hcp_medical_timeline.empty:
                if (
                        hcp_medical_timeline["Claim_Date"].max()
                        == latest_activity_date
                ):
                    latest_activity_labels.append("Encounter")

            if not hcp_treatments_timeline.empty:
                if (
                        hcp_treatments_timeline["Timeline_End_Date"].max()
                        == latest_activity_date
                ):
                    latest_activity_labels.append("Treatment")

            latest_activity_text = (
                " + ".join(latest_activity_labels)
                if latest_activity_labels
                else "Observed activity"
            )

            st.info(
                f"Latest observed activity: "
                f"**{latest_activity_date.strftime('%d %b %Y')}** "
                f"· {latest_activity_text}"
            )

        # ---------------------------------------------------------
        # 5. TIMELINE FILTERS
        # ---------------------------------------------------------

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            activity_options = [
                "All",
                "Treatment Spans",
                "Encounter",
                "First Rx",
                "Product Switch",
                "Rx Activity",
                "Claim Activity"
            ]

            selected_activity = st.selectbox(
                "Activity Type",
                activity_options,
                key="hcp_timeline_activity"
            )

        with filter_col2:
            patient_options = ["All"]

            patient_values = sorted(
                set(
                    pd.concat(
                        [
                            hcp_medical_timeline["Patient_ID"],
                            hcp_rx_timeline["Patient_ID"],
                            hcp_treatments_timeline["Patient_ID"]
                        ]
                    )
                    .dropna()
                    .astype(str)
                    .tolist()
                )
            )

            patient_options.extend(patient_values)

            selected_patient = st.selectbox(
                "Patient",
                patient_options,
                key="hcp_timeline_patient"
            )

        with filter_col3:
            date_range_options = [
                "Full History",
                "Last 12 Months",
                "Last 24 Months",
                "Last 3 Years"
            ]

            selected_date_range = st.selectbox(
                "Date Range",
                date_range_options,
                key="hcp_timeline_date_range"
            )

        # ---------------------------------------------------------
        # 6. DATE RANGE
        # ---------------------------------------------------------

        if selected_date_range == "Last 12 Months":
            timeline_start = observation_end - pd.DateOffset(months=12)

        elif selected_date_range == "Last 24 Months":
            timeline_start = observation_end - pd.DateOffset(months=24)

        elif selected_date_range == "Last 3 Years":
            timeline_start = observation_end - pd.DateOffset(years=3)

        else:
            timeline_start = pd.Timestamp("2014-07-01")

        timeline_end = observation_end

        # ---------------------------------------------------------
        # 7. FILTER PATIENT
        # ---------------------------------------------------------

        if selected_patient != "All":
            hcp_medical_timeline = hcp_medical_timeline[
                hcp_medical_timeline["Patient_ID"].astype(str)
                == selected_patient
                ].copy()

            hcp_rx_timeline = hcp_rx_timeline[
                hcp_rx_timeline["Patient_ID"].astype(str)
                == selected_patient
                ].copy()

            hcp_treatments_timeline = hcp_treatments_timeline[
                hcp_treatments_timeline["Patient_ID"].astype(str)
                == selected_patient
                ].copy()

            switch_data = switch_data[
                switch_data["Patient_ID"].astype(str)
                == selected_patient
                ].copy()

        # ---------------------------------------------------------
        # 8. APPLY DATE RANGE TO EVENTS
        # ---------------------------------------------------------

        hcp_medical_timeline = hcp_medical_timeline[
            hcp_medical_timeline["Claim_Date"].between(
                timeline_start,
                timeline_end
            )
        ].copy()

        hcp_rx_timeline = hcp_rx_timeline[
            hcp_rx_timeline["Fill_Date"].between(
                timeline_start,
                timeline_end
            )
        ].copy()

        # Keep treatment spans that overlap selected period
        hcp_treatments_timeline = hcp_treatments_timeline[
            (
                    hcp_treatments_timeline["Timeline_End_Date"]
                    >= timeline_start
            )
            &
            (
                    hcp_treatments_timeline["Treatment_Start_Date"]
                    <= timeline_end
            )
            ].copy()

        # Clip spans to selected date window
        hcp_treatments_timeline["Plot_Start"] = (
            hcp_treatments_timeline["Treatment_Start_Date"]
            .clip(lower=timeline_start, upper=timeline_end)
        )

        hcp_treatments_timeline["Plot_End"] = (
            hcp_treatments_timeline["Timeline_End_Date"]
            .clip(lower=timeline_start, upper=timeline_end)
        )

        # ---------------------------------------------------------
        # 9. FIRST RX EVENTS
        # ---------------------------------------------------------

        first_rx = (
            hcp_rx_timeline
            .sort_values(["Patient_ID", "Fill_Date"])
            .groupby("Patient_ID", as_index=False)
            .head(1)
            .copy()
        )

        # ---------------------------------------------------------
        # 10. PRODUCT SWITCH EVENTS
        # ---------------------------------------------------------

        switch_events = switch_data[
            switch_data["Is_Switch"]
        ].copy()

        if not switch_events.empty:
            switch_events = switch_events.merge(
                hcp_treatments_timeline[
                    [
                        "Patient_ID",
                        "Condition",
                        "Product_ID",
                        "Treatment_Start_Date",
                        "Brand_Name",
                        "Therapy_Class"
                    ]
                ],
                on=[
                    "Patient_ID",
                    "Condition",
                    "Product_ID",
                    "Treatment_Start_Date"
                ],
                how="left"
            )

        # ---------------------------------------------------------
        # 11. MONTHLY RX ACTIVITY
        # ---------------------------------------------------------

        if not hcp_rx_timeline.empty:

            hcp_rx_timeline["Month"] = (
                hcp_rx_timeline["Fill_Date"]
                .dt.to_period("M")
                .dt.to_timestamp()
            )

            rx_monthly = (
                hcp_rx_timeline
                .groupby(["Patient_ID", "Month"])
                .size()
                .reset_index(name="Rx_Count")
            )

        else:

            rx_monthly = pd.DataFrame(
                columns=["Patient_ID", "Month", "Rx_Count"]
            )

        # ---------------------------------------------------------
        # 12. MONTHLY CLAIM ACTIVITY
        # ---------------------------------------------------------

        if not hcp_pharmacy.empty:

            hcp_pharmacy_timeline = hcp_pharmacy.copy()

            hcp_pharmacy_timeline["Claim_Date"] = pd.to_datetime(
                hcp_pharmacy_timeline["Claim_Date"],
                errors="coerce"
            )

            if selected_patient != "All":
                hcp_pharmacy_timeline = hcp_pharmacy_timeline[
                    hcp_pharmacy_timeline["Patient_ID"].astype(str)
                    == selected_patient
                    ].copy()

            hcp_pharmacy_timeline = hcp_pharmacy_timeline[
                hcp_pharmacy_timeline["Claim_Date"].between(
                    timeline_start,
                    timeline_end
                )
            ].copy()

            if not hcp_pharmacy_timeline.empty:

                hcp_pharmacy_timeline["Month"] = (
                    hcp_pharmacy_timeline["Claim_Date"]
                    .dt.to_period("M")
                    .dt.to_timestamp()
                )

                claim_monthly = (
                    hcp_pharmacy_timeline
                    .groupby(["Patient_ID", "Month"])
                    .size()
                    .reset_index(name="Claim_Count")
                )

            else:

                claim_monthly = pd.DataFrame(
                    columns=["Patient_ID", "Month", "Claim_Count"]
                )

        else:

            claim_monthly = pd.DataFrame(
                columns=["Patient_ID", "Month", "Claim_Count"]
            )

        # ---------------------------------------------------------
        # 13. BUILD FIGURE
        # ---------------------------------------------------------

        fig = go.Figure()

        # Patients appearing anywhere in the timeline
        timeline_patients = set()

        timeline_patients.update(
            hcp_medical_timeline["Patient_ID"].dropna().astype(str)
        )

        timeline_patients.update(
            hcp_rx_timeline["Patient_ID"].dropna().astype(str)
        )

        timeline_patients.update(
            hcp_treatments_timeline["Patient_ID"].dropna().astype(str)
        )

        timeline_patients = sorted(timeline_patients)

        if not timeline_patients:

            st.warning(
                "No observed activity is available for the selected filters."
            )

        else:

            patient_to_y = {
                patient_id: i
                for i, patient_id in enumerate(timeline_patients)
            }

            # -----------------------------------------------------
            # TREATMENT SPANS
            # -----------------------------------------------------

            if selected_activity in ["All", "Treatment Spans"]:

                for _, row in hcp_treatments_timeline.iterrows():

                    patient_id = str(row["Patient_ID"])

                    if patient_id not in patient_to_y:
                        continue

                    start = row["Plot_Start"]
                    end = row["Plot_End"]

                    if pd.isna(start) or pd.isna(end):
                        continue

                    condition = row.get("Condition", "Unknown")
                    therapy = row.get("Therapy_Class", "Unknown")
                    brand = row.get("Brand_Name", row.get("Product_ID", "Unknown"))
                    status = row.get("Treatment_Status", "Unknown")

                    observed_days = row.get(
                        "Observed_Treatment_Days",
                        np.nan
                    )

                    if pd.isna(observed_days):
                        observed_days = max(
                            0,
                            (end - start).days
                        )

                    if status == "Active":
                        end_label = "Observed through 01 Jul 2024"
                    else:
                        end_label = end.strftime("%d %b %Y")

                    hover_text = (
                        f"<b>{patient_id}</b><br>"
                        f"Condition: {condition}<br>"
                        f"Therapy: {therapy}<br>"
                        f"Brand: {brand}<br>"
                        f"Status: {status}<br>"
                        f"Start: {start.strftime('%d %b %Y')}<br>"
                        f"End: {end_label}<br>"
                        f"Observed days: {int(observed_days):,}"
                    )

                    # Use therapy-level colors through a neutral rotating palette
                    therapy_colors = [
                        "#004B88",
                        "#0087CC",
                        "#43AADB",
                        "#6A5ACD",
                        "#7A7A7A",
                        "#8A5A44"
                    ]

                    therapy_values = sorted(
                        hcp_treatments_timeline["Therapy_Class"]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                    therapy_color_map = {
                        therapy_name: therapy_colors[
                            i % len(therapy_colors)
                            ]
                        for i, therapy_name
                        in enumerate(therapy_values)
                    }

                    span_color = therapy_color_map.get(
                        str(therapy),
                        "#004B88"
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=[start, end],
                            y=[
                                patient_to_y[patient_id],
                                patient_to_y[patient_id]
                            ],
                            mode="lines",
                            line=dict(
                                color=span_color,
                                width=12
                            ),
                            hovertemplate=hover_text + "<extra>Treatment span</extra>",
                            showlegend=False
                        )
                    )

                    # Start marker
                    fig.add_trace(
                        go.Scatter(
                            x=[start],
                            y=[patient_to_y[patient_id]],
                            mode="markers",
                            marker=dict(
                                symbol="square",
                                size=9,
                                color=span_color
                            ),
                            hovertemplate=hover_text + "<extra>Treatment start</extra>",
                            showlegend=False
                        )
                    )

            # -----------------------------------------------------
            # ENCOUNTERS
            # -----------------------------------------------------

            if selected_activity in ["All", "Encounter"]:

                if not hcp_medical_timeline.empty:

                    first_encounters = (
                        hcp_medical_timeline
                        .sort_values(["Patient_ID", "Claim_Date"])
                        .groupby("Patient_ID", as_index=False)
                        .head(1)
                        .copy()
                    )

                    for _, row in first_encounters.iterrows():

                        patient_id = str(row["Patient_ID"])

                        if patient_id not in patient_to_y:
                            continue

                        condition = row.get(
                            "Primary_Condition",
                            "Unknown"
                        )

                        specialty = row.get(
                            "Specialty",
                            "Unknown"
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=[row["Claim_Date"]],
                                y=[patient_to_y[patient_id]],
                                mode="markers",
                                marker=dict(
                                    symbol="circle",
                                    size=10,
                                    color="#6A5ACD",
                                    line=dict(
                                        color="white",
                                        width=1
                                    )
                                ),
                                hovertemplate=(
                                    f"<b>{patient_id}</b><br>"
                                    f"Encounter: {row['Claim_Date'].strftime('%d %b %Y')}<br>"
                                    f"Condition: {condition}<br>"
                                    f"Specialty: {specialty}"
                                    "<extra>Encounter</extra>"
                                ),
                                showlegend=False
                            )
                        )

            # -----------------------------------------------------
            # FIRST RX
            # -----------------------------------------------------

            if selected_activity in ["All", "First Rx"]:

                for _, row in first_rx.iterrows():

                    patient_id = str(row["Patient_ID"])

                    if patient_id not in patient_to_y:
                        continue

                    product_id = row.get(
                        "Product_ID",
                        "Unknown"
                    )

                    therapy = row.get(
                        "Therapy_Class",
                        "Unknown"
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=[row["Fill_Date"]],
                            y=[patient_to_y[patient_id]],
                            mode="markers",
                            marker=dict(
                                symbol="triangle-up",
                                size=10,
                                color="#0087CC"
                            ),
                            hovertemplate=(
                                f"<b>{patient_id}</b><br>"
                                f"First Rx: {row['Fill_Date'].strftime('%d %b %Y')}<br>"
                                f"Therapy: {therapy}<br>"
                                f"Product: {product_id}"
                                "<extra>First Rx</extra>"
                            ),
                            showlegend=False
                        )
                    )

            # -----------------------------------------------------
            # PRODUCT SWITCHES
            # -----------------------------------------------------

            if selected_activity in ["All", "Product Switch"]:

                if not switch_events.empty:

                    for _, row in switch_events.iterrows():

                        patient_id = str(row["Patient_ID"])

                        if patient_id not in patient_to_y:
                            continue

                        previous_product = row.get(
                            "Previous_Product_ID",
                            "Unknown"
                        )

                        current_product = row.get(
                            "Brand_Name",
                            row.get("Product_ID", "Unknown")
                        )

                        condition = row.get(
                            "Condition",
                            "Unknown"
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=[row["Treatment_Start_Date"]],
                                y=[patient_to_y[patient_id]],
                                mode="markers",
                                marker=dict(
                                    symbol="diamond",
                                    size=13,
                                    color="#8A5A44",
                                    line=dict(
                                        color="white",
                                        width=1
                                    )
                                ),
                                hovertemplate=(
                                    f"<b>{patient_id}</b><br>"
                                    f"Switch date: "
                                    f"{row['Treatment_Start_Date'].strftime('%d %b %Y')}<br>"
                                    f"Condition: {condition}<br>"
                                    f"Previous product: {previous_product}<br>"
                                    f"New product: {current_product}"
                                    "<extra>Product switch</extra>"
                                ),
                                showlegend=False
                            )
                        )

            # -----------------------------------------------------
            # MONTHLY RX ACTIVITY
            # -----------------------------------------------------

            if selected_activity in ["All", "Rx Activity"]:

                if not rx_monthly.empty:

                    for _, row in rx_monthly.iterrows():

                        patient_id = str(row["Patient_ID"])

                        if patient_id not in patient_to_y:
                            continue

                        rx_count = int(row["Rx_Count"])

                        fig.add_trace(
                            go.Scatter(
                                x=[row["Month"]],
                                y=[patient_to_y[patient_id]],
                                mode="markers",
                                marker=dict(
                                    symbol="circle-open",
                                    size=7,
                                    color="#43AADB",
                                    line=dict(
                                        width=2
                                    )
                                ),
                                hovertemplate=(
                                    f"<b>{patient_id}</b><br>"
                                    f"Month: {row['Month'].strftime('%b %Y')}<br>"
                                    f"Rx events: {rx_count}"
                                    "<extra>Monthly Rx activity</extra>"
                                ),
                                showlegend=False
                            )
                        )

            # -----------------------------------------------------
            # MONTHLY CLAIM ACTIVITY
            # -----------------------------------------------------

            if selected_activity in ["All", "Claim Activity"]:

                if not claim_monthly.empty:

                    for _, row in claim_monthly.iterrows():

                        patient_id = str(row["Patient_ID"])

                        if patient_id not in patient_to_y:
                            continue

                        claim_count = int(row["Claim_Count"])

                        fig.add_trace(
                            go.Scatter(
                                x=[row["Month"]],
                                y=[patient_to_y[patient_id]],
                                mode="markers",
                                marker=dict(
                                    symbol="x",
                                    size=7,
                                    color="#7A7A7A"
                                ),
                                hovertemplate=(
                                    f"<b>{patient_id}</b><br>"
                                    f"Month: {row['Month'].strftime('%b %Y')}<br>"
                                    f"Pharmacy claims: {claim_count}"
                                    "<extra>Monthly claim activity</extra>"
                                ),
                                showlegend=False
                            )
                        )

            # -----------------------------------------------------
            # LEGEND
            # -----------------------------------------------------

            legend_items = [
                ("Treatment span", "#004B88", "line"),
                ("Encounter", "#6A5ACD", "circle"),
                ("First Rx", "#0087CC", "triangle-up"),
                ("Product switch", "#8A5A44", "diamond"),
                ("Rx activity", "#43AADB", "circle-open"),
                ("Claim activity", "#7A7A7A", "x")
            ]

            for label, color, symbol in legend_items:

                if selected_activity != "All":

                    if (
                            selected_activity == "Treatment Spans"
                            and label != "Treatment span"
                    ):
                        continue

                    if (
                            selected_activity == "Encounter"
                            and label != "Encounter"
                    ):
                        continue

                    if (
                            selected_activity == "First Rx"
                            and label != "First Rx"
                    ):
                        continue

                    if (
                            selected_activity == "Product Switch"
                            and label != "Product switch"
                    ):
                        continue

                    if (
                            selected_activity == "Rx Activity"
                            and label != "Rx activity"
                    ):
                        continue

                    if (
                            selected_activity == "Claim Activity"
                            and label != "Claim activity"
                    ):
                        continue

                if symbol == "line":

                    fig.add_trace(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode="lines",
                            line=dict(
                                color=color,
                                width=8
                            ),
                            name=label,
                            hoverinfo="skip"
                        )
                    )

                else:

                    fig.add_trace(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode="markers",
                            marker=dict(
                                symbol=symbol,
                                size=10,
                                color=color
                            ),
                            name=label,
                            hoverinfo="skip"
                        )
                    )

            # -----------------------------------------------------
            # CHART LAYOUT
            # -----------------------------------------------------

            fig.update_layout(
                height=max(
                    500,
                    min(
                        950,
                        120 + (len(timeline_patients) * 32)
                    )
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#43AADB"
                ),
                xaxis=dict(
                    title="Observed Date",
                    range=[
                        timeline_start,
                        timeline_end
                    ],
                    showgrid=True,
                    gridcolor="rgba(120,120,120,0.15)",
                    zeroline=False
                ),
                yaxis=dict(
                    title="Patient",
                    tickmode="array",
                    tickvals=list(range(len(timeline_patients))),
                    ticktext=timeline_patients,
                    showgrid=True,
                    gridcolor="rgba(120,120,120,0.08)",
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
                    l=90,
                    r=30,
                    t=80,
                    b=60
                ),
                hovermode="closest"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

            st.caption(
                "Treatment spans represent observed synthetic treatment episodes. "
                "Active episodes extend through the end of the synthetic observation period "
                "(01 Jul 2024) rather than implying a treatment stop. "
                "A product switch represents a subsequent observed treatment episode with "
                "a different product for the same patient and condition. "
                "Monthly Rx and claim activity is aggregated to reduce visual noise. "
                "These are synthetic longitudinal signals and are not clinical treatment "
                "recommendations or causal measures of HCP behavior."
            )

        # ====================================================
        # HCP ACTIVITY OVERVIEW
        # ====================================================

        st.markdown("### HCP Activity Overview")

        chart_col1, chart_col2 = st.columns(2)

        # Patient & Condition Mix

        with chart_col1:

            hcp_patient_condition = (
                hcp_treatments
                .groupby("Condition")["Patient_ID"]
                .nunique()
                .reset_index(name="Patients")
                .sort_values("Patients", ascending=True)
            )

            hcp_patient_condition["Display Condition"] = (
                hcp_patient_condition["Condition"]
                .map(disease_display_names)
            )

            fig_hcp_conditions = px.bar(
                hcp_patient_condition,
                x="Patients",
                y="Display Condition",
                orientation="h",
            )

            fig_hcp_conditions.update_layout(
                height=400,
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(
                    l=10,
                    r=20,
                    t=20,
                    b=40
                ),
            )

            st.markdown("#### Patient & Condition Mix")

            st.plotly_chart(
                fig_hcp_conditions,
                use_container_width=True
            )

        # Treatment Activity

        with chart_col2:

            hcp_treatment_activity = (
                hcp_rx
                .groupby("Therapy_Class")
                .agg(
                    NRx_Proxy=(
                        "Rx_Event_Type",
                        lambda x: (x == "Initial Fill").sum()
                    ),
                    TRx_Proxy=("Rx_Event_ID", "count")
                )
                .reset_index()
                .sort_values("TRx_Proxy", ascending=True)
            )

            fig_hcp_activity = px.bar(
                hcp_treatment_activity,
                x="Therapy_Class",
                y="TRx_Proxy",
            )

            fig_hcp_activity.update_layout(
                height=400,
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(
                    l=10,
                    r=20,
                    t=20,
                    b=40
                ),
            )

            st.markdown("#### Treatment Activity")

            st.plotly_chart(
                fig_hcp_activity,
                use_container_width=True
            )