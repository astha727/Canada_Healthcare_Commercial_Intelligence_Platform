import streamlit as st
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import numpy as np
from tabs.executive_overview import show_executive_overview



def show_market_disease(
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

    st.subheader("Market & Disease")

    st.caption(
        "Disease burden, market context, and treatment-gap signals."
    )

    # NATIONAL CCDSS PREVALENCE
    # Uses each condition's defined reference age group

    v1_conditions = list(disease_reference_ages.keys())

    national_prevalence = ccdss[
        (ccdss["Data Type"] == "Age-standardized prevalence") &
        (ccdss["Geography"] == "Canada") &
        (ccdss["Sex"] == "Both sexes") &
        (ccdss["Condition"].isin(v1_conditions))
        ].copy()

    national_prevalence["Reference Age"] = (
        national_prevalence["Condition"]
        .map(disease_reference_ages)
    )

    national_prevalence = national_prevalence[
        national_prevalence["Age group"]
        == national_prevalence["Reference Age"]
        ].copy()

    national_prevalence = (
        national_prevalence[
            [
                "Fiscal year",
                "Condition",
                "Age group",
                "Rate (per 100,000)"
            ]
        ]
        .sort_values(
            ["Condition", "Fiscal year"]
        )
    )

    national_prevalence["Display Condition"] = (
        national_prevalence["Condition"]
        .map(disease_display_names)
    )

    st.markdown("#### Disease Burden Trends")
    st.caption("Source: CCDS")

    trend_fig = px.line(
        national_prevalence,
        x="Fiscal year",
        y="Rate (per 100,000)",
        color="Display Condition",
        hover_data={
            "Rate (per 100,000)": ":.2f",
            "Display Condition": False
        },
        color_discrete_sequence=[
            "#004B88",
            "#0167A6",
            "#0087CC",
            "#43AADB",
            "#034B89",
            "#6A5ACD",
            "#7B61A8",
            "#8E6BBE",
            "#A45DB5",
            "#C06C84",
            "#D4778A",
            "#5B8E7D",
            "#4F9D9D",
            "#7C83A8",
            "#6574A8",
            "#9A8FBF"
        ]
    )

    trend_fig.update_traces(
        line=dict(width=2.8),
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Fiscal year: %{x}<br>"
            "Rate: %{y:.2f} per 100,000"
            "<extra></extra>"
        )
    )

    trend_fig.update_layout(
        height=560,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Fiscal year",
            showgrid=False,
            showline=False,
            zeroline=False,
            tickfont=dict(
                size=11,
                color="#43AADB"
            ),
        ),
        yaxis=dict(
            title="Rate per 100,000",
            showgrid=True,
            gridcolor="rgba(100,116,139,0.12)",
            gridwidth=1,
            zeroline=False,
            showline=False,
            tickfont=dict(
                size=11,
                color="#43AADB"
            ),
        ),
        legend=dict(
            title="Condition",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(
                size=10,
                color="#43AADB"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        margin=dict(
            l=20,
            r=160,
            t=10,
            b=30
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D9E2EC",
            font=dict(
                size=12,
                color="#243B53"
            )
        )
    )

    st.plotly_chart(
        trend_fig,
        use_container_width=True
    )




    # -------------------------
    # ROW 2
    # -------------------------

    col3, col4 = st.columns(2)
    with col3:

        st.markdown("#### Geographic Disease Burden")

        # MAP + FILTER PANEL
        map_area, filter_area = st.columns([4, 1])

        # -------------------------
        # MAP FILTERS
        # -------------------------
        with filter_area:

            st.markdown("##### Map Filters")

            map_measure = st.radio(
                "Measure",
                ["Prevalence", "Incidence"],
                key="disease_map_measure"
            )

            if map_measure == "Prevalence":
                selected_data_type = "Age-standardized prevalence"
            else:
                selected_data_type = "Age-standardized incidence rate"

            # DATA AVAILABLE FOR SELECTED MEASURE
            map_data = ccdss[
                (ccdss["Data Type"] == selected_data_type) &
                (ccdss["Sex"] == "Both sexes") &
                (ccdss["Age group type"] == "Total") &
                (ccdss["Geography"] != "Canada") &
                (ccdss["Condition"].isin(v1_conditions))
                ].copy()

            map_data["Reference Age"] = (
                map_data["Condition"]
                .map(disease_reference_ages)
            )

            map_data = map_data[
                map_data["Age group"] == map_data["Reference Age"]
                ].copy()

            map_condition = st.selectbox(
                "Condition",
                sorted(
                    map_data["Condition"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
                key="disease_map_condition"
            )

            map_year = st.selectbox(
                "Fiscal year",
                sorted(
                    map_data["Fiscal year"]
                    .dropna()
                    .unique()
                    .tolist(),
                    reverse=True
                ),
                key="disease_map_year"
            )

        # -------------------------
        # FILTER TO CONDITION + YEAR
        # -------------------------
        map_data = map_data[
            (map_data["Condition"] == map_condition) &
            (map_data["Fiscal year"] == map_year)
            ].copy()

        # -------------------------
        # CANADA GEOJSON
        # -------------------------
        canada_geojson_url = (
            "https://raw.githubusercontent.com/chadbeebe/"
            "Canadian_Provinces/main/canada.geojson"
        )

        # -------------------------
        # PREPARE PROVINCE VALUES
        # -------------------------
        province_map_data = map_data.copy()

        province_map_data["Rate (per 100,000)"] = pd.to_numeric(
            province_map_data["Rate (per 100,000)"],
            errors="coerce"
        )

        # -------------------------
        # CREATE MAP
        # -------------------------
        with map_area:

            canada_map = px.choropleth(
                province_map_data,
                geojson=canada_geojson_url,
                locations="Geography",
                featureidkey="properties.name",
                color="Rate (per 100,000)",
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
                color_continuous_midpoint=province_map_data[
                    "Rate (per 100,000)"
                ].median(),
                hover_name="Geography",
                custom_data=[
                    "Rate (per 100,000)",
                ],
            )

            # -------------------------
            # MAP HOVER
            # -------------------------
            canada_map.update_traces(
                marker_line_width=0,
                marker_line_color="rgba(0,0,0,0)",
                hovertemplate=(
                    "<b>%{location}</b><br>"
                    "Rate: %{customdata[0]:,.1f} per 100,000"
                    "<extra></extra>"
                ),
            )

            # -------------------------
            # APPROXIMATE PROVINCE LABEL LOCATIONS
            # -------------------------
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

            # -------------------------
            # PROVINCE LABELS
            # -------------------------
            label_data = province_map_data[
                province_map_data["Geography"].isin(province_lon)
            ].copy()

            label_data["Label Lon"] = label_data["Geography"].map(province_lon)
            label_data["Label Lat"] = label_data["Geography"].map(province_lat)

            province_labels = go.Scattergeo(
                lon=label_data["Label Lon"],
                lat=label_data["Label Lat"],
                mode="text",
                text=label_data.apply(
                    lambda row: (
                        f"<b>{row['Geography']}</b><br>"
                        f"{row['Rate (per 100,000)']:.1f}"
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

            canada_map.add_trace(province_labels)

            # -------------------------
            # MAP GEOGRAPHY
            # -------------------------
            canada_map.update_geos(
                visible=False,
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

            # -------------------------
            # MAP LAYOUT
            # -------------------------
            canada_map.update_layout(
                height=480,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#43AADB"),
                coloraxis_showscale=False,
            )

            # -------------------------
            # RENDER MAP
            # -------------------------
            st.plotly_chart(
                canada_map,
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with col4:
        st.markdown("#### Treatment Gap")

        treatment_gap = (
            filtered_opportunities
            .groupby("Condition", as_index=False)
            .agg(
                Diagnosed_Patients=("Diagnosed_Patients", "sum"),
                Diagnosed_No_Observed_Treatment=(
                    "Diagnosed_No_Observed_Treatment",
                    "sum"
                )
            )
        )

        treatment_gap["Treatment_Gap_Rate"] = (
                treatment_gap["Diagnosed_No_Observed_Treatment"]
                / treatment_gap["Diagnosed_Patients"]
                * 100
        )

        treatment_gap = treatment_gap[
            treatment_gap["Diagnosed_Patients"] > 0
            ].sort_values(
            "Treatment_Gap_Rate",
            ascending=True
        )

        # Use shorter disease names for display only
        treatment_gap["Display Condition"] = (
            treatment_gap["Condition"]
            .map(disease_display_names)
        )

        gap_fig = px.bar(
            treatment_gap,
            x="Treatment_Gap_Rate",
            y="Display Condition",
            orientation="h",
            text="Treatment_Gap_Rate",
            color="Treatment_Gap_Rate",
            color_continuous_scale=[
                "#D8D0EC",
                "#A995D1",
                "#7B61A8",
                "#6A5ACD",
                "#4B3B78"
            ]
        )

        gap_fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Treatment gap: %{x:.1f}%"
                "<extra></extra>"
            )
        )

        gap_fig.update_layout(
            height=450,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,

            xaxis=dict(
                title="Diagnosed patients without observed treatment",
                ticksuffix="%",
                showgrid=True,
                gridcolor="rgba(100,116,139,0.12)",
                zeroline=False,
                showline=False,
                tickfont=dict(
                    size=10,
                    color="#43AADB"
                ),

            ),

            yaxis=dict(
                title=None,
                showgrid=False,
                showline=False,
                tickfont=dict(
                    size=10,
                    color="#43AADB"
                )
            ),

            margin=dict(
                l=10,
                r=55,
                t=10,
                b=20
            )
        )

        st.plotly_chart(
            gap_fig,
            use_container_width=True
        )

    # -------------------------
    # ROW 3
    # -------------------------

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### Province × Disease Burden")

        heatmap_data = ccdss[
            (ccdss["Data Type"] == "Age-standardized prevalence") &
            (ccdss["Sex"] == "Both sexes") &
            (ccdss["Age group type"] == "Total") &
            (ccdss["Geography"] != "Canada") &
            (ccdss["Condition"].isin(v1_conditions))
            ].copy()

        heatmap_data["Reference Age"] = (
            heatmap_data["Condition"]
            .map(disease_reference_ages)
        )

        heatmap_data = heatmap_data[
            heatmap_data["Age group"]
            == heatmap_data["Reference Age"]
            ].copy()

        heatmap_data = (
            heatmap_data
            .sort_values("Fiscal year")
            .groupby(
                ["Geography", "Condition"],
                as_index=False
            )
            .tail(1)
            .copy()
        )

        heatmap_data["Display Condition"] = (
            heatmap_data["Condition"]
            .map(disease_display_names)
        )

        heatmap_data = heatmap_data[
            [
                "Geography",
                "Condition",
                "Display Condition",
                "Fiscal year",
                "Rate (per 100,000)"
            ]
        ]

        # Create a province × disease matrix
        heatmap_matrix = heatmap_data.pivot(
            index="Geography",
            columns="Display Condition",
            values="Rate (per 100,000)"
        )

        # Keep disease order consistent with the V1 disease list
        disease_order = [
            disease_display_names[disease]
            for disease in v1_conditions
            if disease in heatmap_data["Condition"].unique()
        ]

        heatmap_matrix = heatmap_matrix.reindex(
            columns=disease_order
        )

        # Create fiscal-year lookup for tooltip
        year_matrix = heatmap_data.pivot(
            index="Geography",
            columns="Display Condition",
            values="Fiscal year"
        ).reindex(
            index=heatmap_matrix.index,
            columns=heatmap_matrix.columns
        )

        # Create full-condition lookup for tooltip
        condition_lookup = {
            disease_display_names[disease]: disease
            for disease in v1_conditions
        }

        hover_text = []

        for province in heatmap_matrix.index:
            row = []

            for condition in heatmap_matrix.columns:
                rate = heatmap_matrix.loc[province, condition]
                fiscal_year = year_matrix.loc[province, condition]
                full_condition = condition_lookup.get(
                    condition,
                    condition
                )

                if pd.isna(rate):
                    row.append(
                        f"<b>{province}</b><br>"
                        f"Condition: {full_condition}<br>"
                        f"Fiscal year: {fiscal_year}<br>"
                        "Rate: No data"
                    )
                else:
                    row.append(
                        f"<b>{province}</b><br>"
                        f"Condition: {full_condition}<br>"
                        f"Fiscal year: {fiscal_year}<br>"
                        f"Rate: {rate:.2f} per 100,000"
                    )

            hover_text.append(row)

        heatmap_fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_matrix.values,
                x=heatmap_matrix.columns,
                y=heatmap_matrix.index,
                colorscale=[
                    [0.00, "#D6EEF9"],
                    [0.25, "#43AADB"],
                    [0.50, "#0087CC"],
                    [0.75, "#0167A6"],
                    [1.00, "#004B88"]
                ],
                hovertext=hover_text,
                hovertemplate="%{hovertext}<extra></extra>",
                colorbar=dict(
                    title="Rate",
                    thickness=10,
                    len=0.65
                ),
                xgap=2,
                ygap=2
            )
        )

        heatmap_fig.update_layout(
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",

            xaxis=dict(
                title=None,
                tickangle=-45,
                tickfont=dict(
                    size=9,
                    color="#43AADB"
                ),
                showgrid=False
            ),

            yaxis=dict(
                title=None,
                tickfont=dict(
                    size=9,
                    color="#43AADB"
                ),
                showgrid=False
            ),

            margin=dict(
                l=10,
                r=10,
                t=10,
                b=100
            )
        )

        st.plotly_chart(
            heatmap_fig,
            use_container_width=True
        )

    with col6:
        st.markdown("#### Patient Treatment Funnel")

        diagnosed_patients = filtered_diagnoses[
            "Patient_ID"
        ].nunique()

        treated_patients = filtered_treatments[
            "Patient_ID"
        ].nunique()

        active_treated_patients = filtered_treatments[
            filtered_treatments["Treatment_Status"] == "Active"
            ]["Patient_ID"].nunique()

        funnel_data = pd.DataFrame({
            "Stage": [
                "Diagnosed",
                "Observed Treatment",
                "Active Treatment"
            ],
            "Patients": [
                diagnosed_patients,
                treated_patients,
                active_treated_patients
            ]
        })

        funnel_fig = px.funnel(
            funnel_data,
            y="Stage",
            x="Patients",
            color="Stage",
            color_discrete_sequence=[
                "#43AADB",
                "#0167A6",
                "#004B88"
            ]
        )

        funnel_fig.update_traces(
            texttemplate="%{value:,}",
            textposition="inside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Patients: %{x:,}"
                "<extra></extra>"
            )
        )

        funnel_fig.update_layout(
            height=450,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,

            xaxis=dict(
                title="Patients",
                showgrid=False,
                zeroline=False,
                showline=False,
                tickfont=dict(
                    size=10,
                    color="#43AADB"
                )
            ),

            yaxis=dict(
                title=None,
                showgrid=False,
                showline=False,
                tickfont=dict(
                    size=10,
                    color="#43AADB"
                )
            ),

            margin=dict(
                l=20,
                r=20,
                t=10,
                b=20
            )
        )

        st.plotly_chart(
            funnel_fig,
            use_container_width=True
        )


