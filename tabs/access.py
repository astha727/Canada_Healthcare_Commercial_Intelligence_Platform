import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def show_access(
    patients,
    diagnoses,
    treatments,
    rx_events,
    hcp_master,
    access_claims,
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
    st.subheader("Access")

    st.caption(
        "Understand observed claims activity, coverage outcomes, "
        "patient cost, and potential access-friction signals."
    )

    # ============================================================
    # ACCESS FILTERS
    # ============================================================

    st.markdown("### Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        selected_brand = st.selectbox(
            "Drug / Brand",
            ["All"] + sorted(
                access_claims["Brand_Name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="access_filter_brand",
        )

    with filter_col2:
        selected_condition = st.selectbox(
            "Condition",
            ["All"] + sorted(
                opportunities["Condition"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="access_filter_condition",
        )

    with filter_col3:
        selected_therapy_class = st.selectbox(
            "Therapy Class",
            ["All"] + sorted(
                opportunities["Therapy_Class"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="access_filter_therapy_class",
        )

    with filter_col4:
        selected_province = st.selectbox(
            "Province",
            ["All"] + sorted(
                access_claims["Province"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="access_filter_province",
        )

    # ============================================================
    # APPLY ACCESS FILTERS
    # ============================================================

    access_claims = access_claims.copy()

    if selected_brand != "All":
        access_claims = access_claims[
            access_claims["Brand_Name"].astype(str) == selected_brand
            ]

    if selected_condition != "All":
        selected_treatment_ids = treatments.loc[
            treatments["Condition"].astype(str) == selected_condition,
            "Treatment_ID",
        ]

        access_claims = access_claims[
            access_claims["Treatment_ID"].isin(selected_treatment_ids)
        ]

    if selected_therapy_class != "All":
        selected_treatment_ids = treatments.loc[
            treatments["Therapy_Class"].astype(str) == selected_therapy_class,
            "Treatment_ID",
        ]

        access_claims = access_claims[
            access_claims["Treatment_ID"].isin(selected_treatment_ids)
        ]

    if selected_province != "All":
        access_claims = access_claims[
            access_claims["Province"].astype(str) == selected_province
            ]

    st.caption(
        f"Showing {len(access_claims):,} claims matching the selected filters."
    )

    if access_claims.empty:
        st.info(
            "No pharmacy claims match the selected filters. "
            "Try a different drug, condition, therapy class, or province."
        )
        return

    # ============================================================
    # ACCESS OVERVIEW
    # ============================================================

    st.markdown("### Access Overview")

    total_claims = len(access_claims)

    paid_claims = (
        access_claims["Claim_Status"]
        .eq("Paid")
        .sum()
    )

    partial_claims = (
        access_claims["Claim_Status"]
        .eq("Partial")
        .sum()
    )

    rejected_claims = (
        access_claims["Claim_Status"]
        .eq("Rejected")
        .sum()
    )

    patient_paid = access_claims["Patient_Paid_Amount"].sum()

    plan_paid = access_claims["Plan_Paid_Amount"].sum()

    claim_acceptance_rate = (
        paid_claims / total_claims * 100
        if total_claims > 0
        else 0
    )

    rejection_rate = (
        rejected_claims / total_claims * 100
        if total_claims > 0
        else 0
    )

    partial_rate = (
        partial_claims / total_claims * 100
        if total_claims > 0
        else 0
    )

    # patient_paid = pharmacy_claims["Patient_Paid_Amount"].sum()
    #
    # plan_paid = pharmacy_claims["Plan_Paid_Amount"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Pharmacy Claims",
            f"{total_claims:,}"
        )

    with col2:
        st.metric(
            "Paid Claims",
            f"{paid_claims:,}"
        )

    with col3:
        st.metric(
            "Partial Claims",
            f"{partial_claims:,}"
        )

    with col4:
        st.metric(
            "Rejected Claims",
            f"{rejected_claims:,}"
        )

    with col5:
        st.metric(
            "Rejection Rate",
            f"{rejection_rate:.1f}%"
        )

    st.caption(
        "Access signals are derived from synthetic pharmacy claims and "
        "represent observed claim outcomes rather than real payer policy."
    )

    st.markdown("### Claim Outcomes & Patient Cost")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.markdown("#### Claim Outcomes")

        status_summary = (
            access_claims["Claim_Status"]
            .value_counts()
            .rename_axis("Claim Status")
            .reset_index(name="Claims")
        )

        status_fig = px.pie(
            status_summary,
            names="Claim Status",
            values="Claims",
            hole=0.55,
        )

        status_fig.update_traces(
            textinfo="label+percent",
            textposition="outside",
        )

        status_fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend_title=None,
            font=dict(color="#43AADB"),
            margin=dict(t=20, b=20, l=10, r=10),
        )

        st.plotly_chart(
            status_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with chart_col2:

        st.markdown("#### Patient Cost & Coverage")

        total_plan_paid = (
            access_claims["Plan_Paid_Amount"].sum()
        )

        total_patient_paid = (
            access_claims["Patient_Paid_Amount"].sum()
        )

        payment_summary = pd.DataFrame({
            "Category": [
                "Plan Paid",
                "Patient Paid",
            ],
            "Amount": [
                total_plan_paid,
                total_patient_paid,
            ],
        })

        payment_fig = px.pie(
            payment_summary,
            names="Category",
            values="Amount",
            hole=0.55,
        )

        payment_fig.update_traces(
            textinfo="label+percent",
            textposition="outside",
            hovertemplate=(
                "%{label}<br>"
                "$%{value:,.0f}<extra></extra>"
            ),
        )

        payment_fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend_title=None,
            font=dict(color="#43AADB"),
            margin=dict(t=20, b=20, l=10, r=10),
        )

        st.plotly_chart(
            payment_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown("### Access Friction")

    province_friction = (
        access_claims
        .groupby("Province")
        .agg(
            Claims=("Claim_Status", "size"),
            Rejected=(
                "Claim_Status",
                lambda x: x.astype(str).str.strip().eq("Rejected").sum(),
            ),
            Partial=(
                "Claim_Status",
                lambda x: x.astype(str).str.strip().eq("Partial").sum(),
            ),
        )
        .reset_index()
    )

    province_friction["Claims"] = pd.to_numeric(
        province_friction["Claims"],
        errors="coerce",
    ).fillna(0)

    province_friction["Rejected"] = pd.to_numeric(
        province_friction["Rejected"],
        errors="coerce",
    ).fillna(0)

    province_friction["Partial"] = pd.to_numeric(
        province_friction["Partial"],
        errors="coerce",
    ).fillna(0)

    province_friction["Rejection Rate"] = (
            province_friction["Rejected"]
            / province_friction["Claims"]
            * 100
    )

    highest_claims_row = province_friction.loc[
        province_friction["Claims"].idxmax()
    ]

    highest_rejection_row = province_friction.loc[
        province_friction["Rejection Rate"].idxmax()
    ]

    lowest_rejection_row = province_friction.loc[
        province_friction["Rejection Rate"].idxmin()
    ]

    rejection_range = (
            highest_rejection_row["Rejection Rate"]
            - lowest_rejection_row["Rejection Rate"]
    )

    top_rejection_provinces = (
        province_friction
        .sort_values("Rejection Rate", ascending=False)
        .head(3)
        .copy()
    )

    province_map_data = province_friction[
        [
            "Province",
            "Claims",
            "Rejected",
            "Partial",
            "Rejection Rate",
        ]
    ].copy()

    province_map_data["Partial"] = (
        pd.to_numeric(
            province_map_data["Partial"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    province_map_data["Claims"] = (
        pd.to_numeric(
            province_map_data["Claims"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    province_map_data["Rejected"] = (
        pd.to_numeric(
            province_map_data["Rejected"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    province_map_data["Rejection Rate"] = (
        pd.to_numeric(
            province_map_data["Rejection Rate"],
            errors="coerce",
        )
        .fillna(0)
    )

    friction_col1, friction_col2 = st.columns([1, 1])

    # ============================================================
    # LEFT: CANADA MAP
    # ============================================================

    with friction_col1:

        canada_geojson_url = (
            "https://raw.githubusercontent.com/chadbeebe/"
            "Canadian_Provinces/main/canada.geojson"
        )
        province_map_data["Claims_Log"] = np.log1p(
            province_map_data["Claims"]
        )

        province_map = px.choropleth(
            province_map_data,
            geojson=canada_geojson_url,
            locations="Province",
            featureidkey="properties.name",
            color="Claims",
            color_continuous_scale=[
                [0.00, "#90CDF4"],
                [0.15, "#6A5ACD"],
                [0.30, "#120A8F"],
                [0.45, "#0E98BA"],
                [0.50, "#6A5ACD"],
                [0.60, "#2B6CB0"],
                [0.75, "#1A365D"],
                [1.00, "#0A2540"],
            ],
            color_continuous_midpoint=province_map_data["Claims"].median(),
            hover_name="Province",
            custom_data=[
                "Claims",
                "Rejected",
                "Partial",
                "Rejection Rate",
            ],
        )

        province_map.update_traces(
            marker_line_width=0,
            marker_line_color="rgba(0,0,0,0)",
            hovertemplate=(
                "<b>%{location}</b><br>"
                "Claims: %{customdata[0]:,}<br>"
                "Rejected: %{customdata[1]:,}<br>"
                "Partial: %{customdata[2]:,}<br>"
                "Rejection Rate: %{customdata[3]:.1f}%"
                "<extra></extra>"
            ),
        )

        # Approximate province label locations
        province_lon = {
            "British Columbia": -125.0,
            "Alberta": -114.0,
            "Saskatchewan": -106.0,
            "Manitoba": -98.0,
            "Ontario": -84.5,
            "Quebec": -71.5,
            "New Brunswick": -66.5,
            "Nova Scotia": -63.0,
            "Prince Edward Island": -63.2,
            "Newfoundland and Labrador": -57.5,
            "Yukon": -135.0,
            "Northwest Territories": -120.0,
            "Nunavut": -95.0,
        }

        province_lat = {
            "British Columbia": 53.5,
            "Alberta": 53.5,
            "Saskatchewan": 54.0,
            "Manitoba": 53.5,
            "Ontario": 50.5,
            "Quebec": 52.0,
            "New Brunswick": 46.5,
            "Nova Scotia": 45.0,
            "Prince Edward Island": 46.3,
            "Newfoundland and Labrador": 52.0,
            "Yukon": 63.5,
            "Northwest Territories": 64.0,
            "Nunavut": 65.0,
        }

        label_lon = top_rejection_provinces["Province"].map(province_lon)
        label_lat = top_rejection_provinces["Province"].map(province_lat)

        province_labels = go.Scattergeo(
            lon=label_lon,
            lat=label_lat,
            mode="text",
            text=top_rejection_provinces.apply(
                lambda row: (
                    f"<b>{row['Province']}</b><br>"
                    f"{row['Rejection Rate']:.1f}%"
                ),
                axis=1,
            ),
            textfont=dict(
                color="#43AADB",
                size=11,
            ),
            hoverinfo="skip",
            showlegend=False,
        )

        province_map.add_trace(province_labels)

        province_map.update_geos(
            visible=False,
            #fitbounds="locations",
            projection_type="mercator",
            center=dict(
                lat=70,
                lon=-95,
            ),
            projection_scale=3.4,
            showcountries=False,
            showcoastlines=False,
            showland=False,
            showlakes=False,
            bgcolor="rgba(0,0,0,0)",
        )

        province_map.update_layout(
            height=700,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),

            # Remove claims legend/colorbar
            coloraxis_showscale=False,
        )

        st.plotly_chart(
            province_map,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ============================================================
    # RIGHT: GEOGRAPHIC READOUT + DRIVER ANALYSIS
    # ============================================================

    with friction_col2:

        st.markdown("#### Geographic Readout")

        # ---------- KPI ROW 1 ----------

        geo_row1_col1, geo_row1_col2 = st.columns(2)

        with geo_row1_col1:
            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    border:1px solid rgba(120,120,120,0.2);
                    border-radius:8px;
                    min-height:105px;
                ">
                    <div style="color:#43AADB;font-size:12px;">
                        Highest Claim Volume
                    </div>
                    <div style="font-size:20px;font-weight:600;margin-top:5px;">
                        {highest_claims_row['Province']}
                    </div>
                    <div style="color:#43AADB;font-size:13px;">
                        {highest_claims_row['Claims']:,} claims
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with geo_row1_col2:
            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    border:1px solid rgba(120,120,120,0.2);
                    border-radius:8px;
                    min-height:105px;
                ">
                    <div style="color:#43AADB;font-size:12px;">
                        Highest Rejection Rate
                    </div>
                    <div style="font-size:20px;font-weight:600;margin-top:5px;">
                        {highest_rejection_row['Province']}
                    </div>
                    <div style="color:#43AADB;font-size:13px;">
                        {highest_rejection_row['Rejection Rate']:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # ---------- KPI ROW 2 ----------

        geo_row2_col1, geo_row2_col2 = st.columns(2)

        with geo_row2_col1:
            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    border:1px solid rgba(120,120,120,0.2);
                    border-radius:8px;
                    min-height:105px;
                ">
                    <div style="color:#43AADB;font-size:12px;">
                        Lowest Rejection Rate
                    </div>
                    <div style="font-size:20px;font-weight:600;margin-top:5px;">
                        {lowest_rejection_row['Province']}
                    </div>
                    <div style="color:#43AADB;font-size:13px;">
                        {lowest_rejection_row['Rejection Rate']:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with geo_row2_col2:
            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    border:1px solid rgba(120,120,120,0.2);
                    border-radius:8px;
                    min-height:105px;
                ">
                    <div style="color:#43AADB;font-size:12px;">
                        Rejection-Rate Spread
                    </div>
                    <div style="font-size:20px;font-weight:600;margin-top:5px;">
                        {rejection_range:.1f} pp
                    </div>
                    <div style="color:#43AADB;font-size:13px;">
                        highest vs. lowest
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### Potential Drivers")

        st.caption(
            "Observed patterns in synthetic claims that may help explain "
            "geographic differences."
        )

        # ---------- FACTOR 1: FORMULARY MATCH ----------

        formulary_analysis = (
            access_claims
            .groupby("Formulary_Match")
            .agg(
                Claims=("Claim_Status", "size"),
                Rejected=("Claim_Status", lambda x: (x == "Rejected").sum()),
            )
            .reset_index()
        )

        formulary_analysis["Rejection Rate"] = (
                formulary_analysis["Rejected"]
                / formulary_analysis["Claims"]
                * 100
        )

        formulary_analysis = formulary_analysis.sort_values(
            "Rejection Rate",
            ascending=False
        )

        if not formulary_analysis.empty:
            highest_formulary = formulary_analysis.iloc[0]

            st.markdown(
                f"""
                **Formulary Match**

                `{highest_formulary['Formulary_Match']}` claims show the highest
                observed rejection rate at
                **{highest_formulary['Rejection Rate']:.1f}%**
                ({highest_formulary['Claims']:,} claims).
                """
            )

        # ---------- FACTOR 2: BENEFIT STATUS ----------

        benefit_analysis = (
            access_claims
            .groupby("Benefit_status")
            .agg(
                Claims=("Claim_Status", "size"),
                Rejected=("Claim_Status", lambda x: (x == "Rejected").sum()),
            )
            .reset_index()
        )

        benefit_analysis["Rejection Rate"] = (
                benefit_analysis["Rejected"]
                / benefit_analysis["Claims"]
                * 100
        )

        benefit_analysis = benefit_analysis.sort_values(
            "Rejection Rate",
            ascending=False
        )

        if not benefit_analysis.empty:
            highest_benefit = benefit_analysis.iloc[0]

            st.markdown(
                f"""
                **Benefit Status**

                `{highest_benefit['Benefit_status']}` claims show the highest
                observed rejection rate at
                **{highest_benefit['Rejection Rate']:.1f}%**
                ({highest_benefit['Claims']:,} claims).
                """
            )

        # ---------- FACTOR 3: COVERAGE PROGRAM ----------

        coverage_analysis = (
            access_claims
            .groupby("Synthetic_Coverage_Program")
            .agg(
                Claims=("Claim_Status", "size"),
                Rejected=("Claim_Status", lambda x: (x == "Rejected").sum()),
            )
            .reset_index()
        )

        coverage_analysis["Rejection Rate"] = (
                coverage_analysis["Rejected"]
                / coverage_analysis["Claims"]
                * 100
        )

        coverage_analysis = coverage_analysis.sort_values(
            "Rejection Rate",
            ascending=False
        )

        if not coverage_analysis.empty:
            highest_coverage = coverage_analysis.iloc[0]

            st.markdown(
                f"""
                **Coverage Program**

                `{highest_coverage['Synthetic_Coverage_Program']}` has the highest
                observed rejection rate at
                **{highest_coverage['Rejection Rate']:.1f}%**
                ({highest_coverage['Claims']:,} claims).
                """
            )



        st.caption(
            "These are synthetic claims signals. The factor patterns indicate "
            "potential drivers for investigation, not confirmed causal explanations."
        )

    st.markdown(
        """
        <div style="height: 0px;"></div>
        """,
        unsafe_allow_html=True,
    )

    # Normalize claim status once for all rejection-driver analysis
    access_claims = access_claims.copy()

    access_claims["_Rejected_Flag"] = (
        access_claims["Claim_Status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("rejected")
    )



    # ============================================================
    # REJECTION DRIVERS
    # ============================================================

    st.markdown("### Rejection Drivers")

    st.caption(
        "Observed rejection patterns by formulary, benefit status, and coverage program. "
        "These are synthetic signals for further investigation."
    )

    driver_col1, driver_col2, driver_col3 = st.columns(3)

    # ------------------------------------------------------------
    # FORMULARY MATCH
    # ------------------------------------------------------------

    formulary_analysis = (
        access_claims
        .assign(
            _Rejected=(
                access_claims["Claim_Status"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("rejected")
            )
        )
        .groupby("Formulary_Match", dropna=False)
        .agg(
            Claims=("_Rejected", "size"),
            Rejected=("_Rejected", "sum"),
        )
        .reset_index()
    )

    formulary_analysis["Rejection Rate"] = (
            formulary_analysis["Rejected"]
            / formulary_analysis["Claims"]
            * 100
    )

    formulary_analysis["Formulary_Match"] = (
        formulary_analysis["Formulary_Match"]
        .astype(str)
        .replace({
            "True": "Match",
            "False": "No Match",
            "nan": "Unknown",
        })
    )

    with driver_col1:

        st.markdown("#### Formulary Match")

        fig_formulary = px.bar(
            formulary_analysis.sort_values("Rejection Rate"),
            x="Rejection Rate",
            y="Formulary_Match",
            orientation="h",
            text="Rejection Rate",
        )

        fig_formulary.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            marker_color="#0087CC",
        )

        fig_formulary.update_layout(
            height=300,
            margin=dict(l=10, r=45, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),
            xaxis=dict(
                title="Rejection Rate (%)",
                range=[0, max(formulary_analysis["Rejection Rate"].max() * 1.15, 5)],
                gridcolor="rgba(120,120,120,0.15)",
                automargin=True,
            ),
            yaxis=dict(
                title="",
                gridcolor="rgba(0,0,0,0)",
                automargin=True,
            ),
            showlegend=False,
        )

        st.plotly_chart(
            fig_formulary,
            use_container_width=True,
            config={"displayModeBar": False},
            key="access_rejection_formulary",
        )

    # ------------------------------------------------------------
    # BENEFIT STATUS
    # ------------------------------------------------------------

    benefit_analysis = (
        access_claims
        .assign(
            _Rejected=(
                access_claims["Claim_Status"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("rejected")
            )
        )
        .groupby("Benefit_status", dropna=False)
        .agg(
            Claims=("_Rejected", "size"),
            Rejected=("_Rejected", "sum"),
        )
        .reset_index()
    )

    benefit_analysis["Rejection Rate"] = (
            benefit_analysis["Rejected"]
            / benefit_analysis["Claims"]
            * 100
    )

    benefit_analysis["Benefit_status"] = (
        benefit_analysis["Benefit_status"]
        .astype(str)
        .str.strip()
        .replace({
            "": "Unknown",
            "nan": "Unknown",
            "None": "Unknown",
        })
    )

    with driver_col2:

        st.markdown("#### Benefit Status")

        fig_benefit = px.bar(
            benefit_analysis.sort_values("Rejection Rate"),
            x="Rejection Rate",
            y="Benefit_status",
            orientation="h",
            text="Rejection Rate",
        )

        fig_benefit.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
            marker_color="#0167A6",
        )

        fig_benefit.update_layout(
            height=300,
            margin=dict(l=10, r=60, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),
            xaxis=dict(
                title="Rejection Rate (%)",
                range=[0, 115],
                gridcolor="rgba(120,120,120,0.15)",
                automargin=True,
            ),
            yaxis=dict(
                title="",
                gridcolor="rgba(0,0,0,0)",
                automargin=True,
            ),
            showlegend=False,
        )

        st.plotly_chart(
            fig_benefit,
            use_container_width=True,
            config={"displayModeBar": False},
            key="access_rejection_benefit",
        )

    # ------------------------------------------------------------
    # COVERAGE PROGRAM
    # ------------------------------------------------------------

    coverage_analysis = (
        access_claims
        .assign(
            _Rejected=(
                access_claims["Claim_Status"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("rejected")
            )
        )
        .groupby("Synthetic_Coverage_Program", dropna=False)
        .agg(
            Claims=("_Rejected", "size"),
            Rejected=("_Rejected", "sum"),
        )
        .reset_index()
    )

    coverage_analysis["Rejection Rate"] = (
            coverage_analysis["Rejected"]
            / coverage_analysis["Claims"]
            * 100
    )

    coverage_analysis["Coverage_Display"] = (
        coverage_analysis["Synthetic_Coverage_Program"]
        .replace({
            "Public Prescription Drug Insurance Plan":
                "Public Drug Insurance",
            "Private Insurance":
                "Private Insurance",
            "Employer-Sponsored Insurance":
                "Employer-Sponsored",
            "No Coverage":
                "No Coverage",
        })
    )

    with driver_col3:

        st.markdown("#### Coverage Program")

        fig_coverage = px.bar(
            coverage_analysis.sort_values("Rejection Rate"),
            x="Rejection Rate",
            y="Coverage_Display",
            orientation="h",
            text="Rejection Rate",
        )

        fig_coverage.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
            marker_color="#43AADB",
            customdata=coverage_analysis[
                ["Synthetic_Coverage_Program"]
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Rejection Rate: %{x:.1f}%"
                "<extra></extra>"
            ),
        )

        fig_coverage.update_layout(
            height=260,
            margin=dict(l=0, r=25, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),
            xaxis=dict(
                title="Rejection Rate (%)",
                gridcolor="rgba(120,120,120,0.15)",
            ),
            yaxis=dict(
                title="",
                gridcolor="rgba(0,0,0,0)",
            ),
            showlegend=False,
        )

        st.plotly_chart(
            fig_coverage,
            use_container_width=True,
            config={"displayModeBar": False},
            key="access_rejection_coverage",
        )

    st.markdown("### Claim Explorer")

    st.caption(
        "Detailed view of synthetic pharmacy claims."
    )

    display_claims = access_claims[
        [
            "Rx_Claim_ID",
            "Patient_ID",
            "Province",
            "Brand_Name",
            "Claim_Date",
            "Claim_Status",
            "Formulary_Match",
            "Benefit_status",
            "Synthetic_Coverage_Program",
            "Submitted_Amount",
            "Accepted_Amount",
            "Plan_Paid_Amount",
            "Patient_Paid_Amount",
        ]
    ].copy()

    display_claims = display_claims.rename(
        columns={
            "Rx_Claim_ID": "Rx Claim ID",
            "Patient_ID": "Patient ID",
            "Brand_Name": "Brand",
            "Claim_Date": "Claim Date",
            "Claim_Status": "Claim Status",
            "Formulary_Match": "Formulary Match",
            "Benefit_status": "Benefit Status",
            "Synthetic_Coverage_Program": "Coverage Program",
            "Submitted_Amount": "Submitted Amount",
            "Accepted_Amount": "Accepted Amount",
            "Plan_Paid_Amount": "Plan Paid",
            "Patient_Paid_Amount": "Patient Paid",
        }
    )

    st.dataframe(
        display_claims,
        use_container_width=True,
        hide_index=True,
    )