import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parents[1]

COMPETITIVE_DATA_PATH = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "competitive_product_analytics.csv"
)

COMPETITOR_COLORS = {
    "Teva": "#1F77B4",
    "Apotex": "#2CA02C",
    "Pharmascience": "#FF7F0E",
    "Mylan": "#9467BD",
    "Riva": "#D62728",
    "Taro": "#17BECF",
    "Other / Unknown": "#7F7F7F",
}

@st.cache_data
def load_competitive_data():

    return pd.read_csv(COMPETITIVE_DATA_PATH)

def show_products_competition(
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
    product_analytics = load_competitive_data()

    st.subheader("Products & Competition")

    st.caption(
        "Analyze competitive demand, prescription activity, and access "
        "signals across the synthetic product landscape."
    )

    # ========================================================
    # FILTERS
    # ========================================================

    st.markdown("### Competitive Filters")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        therapy_options = sorted(
            product_analytics["Therapy_Class"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_therapy = st.selectbox(
            "Therapy Class",
            ["All"] + therapy_options,
            key="competitive_therapy_filter",
        )

    with filter_col2:
        competitor_options = sorted(
            product_analytics["Competitor"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_competitor = st.selectbox(
            "Competitor",
            ["All"] + competitor_options,
            key="competitive_competitor_filter",
        )

    with filter_col3:
        product_options = sorted(
            product_analytics["Brand_Name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_product = st.selectbox(
            "Product / Brand",
            ["All"] + product_options,
            key="competitive_product_filter",
        )

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_products = product_analytics.copy()

    if selected_therapy != "All":
        filtered_products = filtered_products[
            filtered_products["Therapy_Class"].astype(str)
            == selected_therapy
        ]

    if selected_competitor != "All":
        filtered_products = filtered_products[
            filtered_products["Competitor"].astype(str)
            == selected_competitor
        ]

    if selected_product != "All":
        filtered_products = filtered_products[
            filtered_products["Brand_Name"].astype(str)
            == selected_product
        ]

    # ========================================================
    # EMPTY FILTER STATE
    # ========================================================

    if filtered_products.empty:

        st.warning(
            "No products match the selected filters. "
            "Try broadening one or more filters."
        )

        return

    # ========================================================
    # KPI CALCULATIONS
    # ========================================================

    product_count = filtered_products["Product_ID"].nunique()

    competitor_count = filtered_products["Competitor"].nunique()

    total_nrx = pd.to_numeric(
        filtered_products["NRx_Proxy"],
        errors="coerce"
    ).fillna(0).sum()

    total_trx = pd.to_numeric(
        filtered_products["TRx_Proxy"],
        errors="coerce"
    ).fillna(0).sum()

    total_unique_patients = pd.to_numeric(
        filtered_products["Unique_Patients"],
        errors="coerce"
    ).fillna(0).sum()

    total_pharmacy_claims = pd.to_numeric(
        filtered_products["Pharmacy_Claims"],
        errors="coerce"
    ).fillna(0).sum()

    # ========================================================
    # KPI DISPLAY
    # ========================================================

    st.markdown("### Competitive Demand Overview")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.metric(
            "Products",
            f"{product_count:,}"
        )

    with kpi2:
        st.metric(
            "Competitors",
            f"{competitor_count:,}"
        )

    with kpi3:
        st.metric(
            "NRx Proxy",
            f"{total_nrx:,.0f}"
        )

    with kpi4:
        st.metric(
            "TRx Proxy",
            f"{total_trx:,.0f}"
        )

    with kpi5:
        st.metric(
            "Unique Patients",
            f"{total_unique_patients:,.0f}"
        )

    with kpi6:
        st.metric(
            "Pharmacy Claims",
            f"{total_pharmacy_claims:,.0f}"
        )

    st.caption(
        "NRx Proxy represents observed initial fills; TRx Proxy represents "
        "observed initial fills plus refills in the synthetic dataset."
    )

    # ========================================================
    # COMPETITIVE DEMAND LANDSCAPE
    # ========================================================

    st.markdown("### Competitive Demand Landscape")

    st.write(
        "Compare observed new prescription activity with overall prescription "
        "volume to identify emerging, established, and lower-traction products."
    )

    scatter_data = filtered_products.copy()

    scatter_data["NRx Proxy"] = pd.to_numeric(
        scatter_data["NRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    scatter_data["TRx Proxy"] = pd.to_numeric(
        scatter_data["TRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    scatter_data["Unique Patients"] = pd.to_numeric(
        scatter_data["Unique_Patients"],
        errors="coerce"
    ).fillna(0)

    fig = px.scatter(
        scatter_data,
        x="NRx Proxy",
        y="TRx Proxy",
        size="Unique Patients",
        color="Competitor",
        color_discrete_map=COMPETITOR_COLORS,
        hover_name="Brand_Name",
        hover_data={
            "Competitor": True,
            "Therapy_Class": True,
            "NRx Proxy": ":,.0f",
            "TRx Proxy": ":,.0f",
            "Unique Patients": ":,.0f",
            "NRx_Proxy": False,
            "TRx_Proxy": False,
        },
        labels={
            "Competitor": "Competitor",
            "Therapy_Class": "Therapy Class",
        },
    )

    fig.update_traces(
        marker=dict(
            opacity=0.80,
            line=dict(
                width=0.8,
                color="rgba(255,255,255,0.65)"
            ),
        )
    )

    fig.update_layout(
        height=600,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#43AADB"
        ),
        xaxis=dict(
            title="NRx Proxy — New Prescription Activity",
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title="TRx Proxy — Total Prescription Activity",
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
        ),
        legend_title="Competitor",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )


    # ========================================================
    # PRESCRIPTION SHARE
    # ========================================================

    st.markdown("### Prescription Share")

    st.write(
        "Compare each product's share of observed total prescription activity "
        "with its share of new prescription activity within the selected "
        "therapy class."
    )

    share_data = filtered_products.copy()

    share_data["NRx Proxy"] = pd.to_numeric(
        share_data["NRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    share_data["TRx Proxy"] = pd.to_numeric(
        share_data["TRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    total_class_nrx = share_data["NRx Proxy"].sum()
    total_class_trx = share_data["TRx Proxy"].sum()

    if total_class_nrx > 0:
        share_data["NRx Share"] = (
            share_data["NRx Proxy"] / total_class_nrx * 100
        )
    else:
        share_data["NRx Share"] = 0

    if total_class_trx > 0:
        share_data["TRx Share"] = (
            share_data["TRx Proxy"] / total_class_trx * 100
        )
    else:
        share_data["TRx Share"] = 0

    share_data = share_data.sort_values(
        "TRx Share",
        ascending=True
    )

    share_col1, share_col2 = st.columns(2)

    with share_col1:

        trx_fig = px.bar(
            share_data,
            x="TRx Share",
            y="Brand_Name",
            orientation="h",
            color="Competitor",
            color_discrete_map=COMPETITOR_COLORS,
            hover_data={
                "Brand_Name": True,
                "Competitor": True,
                "TRx Proxy": ":,.0f",
                "TRx Share": ":.1f",
            },
            labels={
                "Brand_Name": "Product",
                "TRx Share": "TRx Share (%)",
                "Competitor": "Competitor",
            },
        )

        trx_fig.update_layout(
            height=500,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),
            xaxis=dict(
                title="TRx Share (%)",
                ticksuffix="%",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
            ),
            yaxis=dict(
                title="",
            ),
            legend_title="Competitor",
        )

        st.plotly_chart(
            trx_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with share_col2:

        nrx_fig = px.bar(
            share_data.sort_values(
                "NRx Share",
                ascending=True
            ),
            x="NRx Share",
            y="Brand_Name",
            orientation="h",
            color="Competitor",
            color_discrete_map=COMPETITOR_COLORS,
            hover_data={
                "Brand_Name": True,
                "Competitor": True,
                "NRx Proxy": ":,.0f",
                "NRx Share": ":.1f",
            },
            labels={
                "Brand_Name": "Product",
                "NRx Share": "NRx Share (%)",
                "Competitor": "Competitor",
            },
        )

        nrx_fig.update_layout(
            height=500,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#43AADB"),
            xaxis=dict(
                title="NRx Share (%)",
                ticksuffix="%",
                gridcolor="rgba(120,120,120,0.15)",
                zeroline=False,
            ),
            yaxis=dict(
                title="",
            ),
            legend_title="Competitor",
        )

        st.plotly_chart(
            nrx_fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.caption(
        "Shares are calculated within the currently selected competitive "
        "landscape. NRx and TRx are synthetic prescription activity proxies."
    )

    # ========================================================
    # DEMAND & ACCESS
    # ========================================================

    st.markdown("### Demand & Access")

    st.write(
        "Compare observed prescription demand with pharmacy claim payment "
        "performance to identify products that may warrant further access review."
    )

    demand_access = filtered_products.copy()

    demand_access["TRx Proxy"] = pd.to_numeric(
        demand_access["TRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    demand_access["Unique Patients"] = pd.to_numeric(
        demand_access["Unique_Patients"],
        errors="coerce"
    ).fillna(0)

    demand_access["Paid Claim Rate"] = pd.to_numeric(
        demand_access["Paid_Claim_Rate"],
        errors="coerce"
    ).fillna(0)

    # Convert decimal rates to percentages for display.
    demand_access["Paid Claim Rate (%)"] = (
        demand_access["Paid Claim Rate"] * 100
    )

    demand_access["Paid Claim Rate (%)"] = (
        demand_access["Paid Claim Rate (%)"]
        .clip(lower=0, upper=100)
    )

    demand_access_fig = px.scatter(
        demand_access,
        x="TRx Proxy",
        y="Paid Claim Rate (%)",
        size="Unique Patients",
        color="Competitor",
        color_discrete_map=COMPETITOR_COLORS,
        hover_name="Brand_Name",
        hover_data={
            "Competitor": True,
            "Therapy_Class": True,
            "TRx Proxy": ":,.0f",
            "Unique Patients": ":,.0f",
            "Paid Claim Rate (%)": ":.1f",
            "Paid Claim Rate": False,
        },
        labels={
            "TRx Proxy": "TRx Proxy — Total Prescription Activity",
            "Paid Claim Rate (%)": "Paid Claim Rate (%)",
            "Competitor": "Competitor",
        },
        size_max=40,
    )

    demand_access_fig.update_traces(
        marker=dict(
            opacity=0.80,
            line=dict(
                width=0.8,
                color="rgba(255,255,255,0.65)"
            ),
        )
    )

    demand_access_fig.update_layout(
        height=600,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#43AADB"
        ),
        xaxis=dict(
            title="TRx Proxy — Total Prescription Activity",
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Paid Claim Rate (%)",
            ticksuffix="%",
            gridcolor="rgba(120,120,120,0.15)",
            zeroline=False,
            range=[0, 100],
        ),
        legend_title="Competitor",
    )

    st.plotly_chart(
        demand_access_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        "Analytical signal only: higher prescription activity combined with "
        "lower paid-claim rates may warrant further access investigation. "
        "The synthetic data does not establish causality."
    )

    # ========================================================
    # COMPETITIVE PRODUCT COMPARISON
    # ========================================================

    st.markdown("### Competitive Product Comparison")

    st.write(
        "Compare products across prescription demand, patient reach, "
        "and pharmacy access indicators."
    )

    comparison_data = filtered_products.copy()

    comparison_data["NRx Proxy"] = pd.to_numeric(
        comparison_data["NRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    comparison_data["TRx Proxy"] = pd.to_numeric(
        comparison_data["TRx_Proxy"],
        errors="coerce"
    ).fillna(0)

    comparison_data["Unique Patients"] = pd.to_numeric(
        comparison_data["Unique_Patients"],
        errors="coerce"
    ).fillna(0)

    comparison_data["Paid Claim Rate"] = (
        pd.to_numeric(
            comparison_data["Paid_Claim_Rate"],
            errors="coerce"
        )
        .fillna(0)
        * 100
    )

    comparison_data["Formulary Match Rate"] = (
        pd.to_numeric(
            comparison_data["Formulary_Match_Rate"],
            errors="coerce"
        )
        .fillna(0)
        * 100
    )

    comparison_data["NRx Share"] = (
        comparison_data["NRx Proxy"]
        / comparison_data["NRx Proxy"].sum()
        * 100
        if comparison_data["NRx Proxy"].sum() > 0
        else 0
    )

    comparison_data["TRx Share"] = (
        comparison_data["TRx Proxy"]
        / comparison_data["TRx Proxy"].sum()
        * 100
        if comparison_data["TRx Proxy"].sum() > 0
        else 0
    )

    display_columns = [
        "Competitor",
        "Brand_Name",
        "Therapy_Class",
        "NRx Proxy",
        "TRx Proxy",
        "NRx Share",
        "TRx Share",
        "Unique Patients",
        "Paid Claim Rate",
        "Formulary Match Rate",
    ]

    comparison_display = comparison_data[display_columns].copy()

    comparison_display = comparison_display.rename(
        columns={
            "Brand_Name": "Product",
            "Therapy_Class": "Therapy",
            "NRx Proxy": "NRx",
            "TRx Proxy": "TRx",
            "Unique Patients": "Patients",
            "Paid Claim Rate": "Paid Rate",
            "Formulary Match Rate": "Formulary Match",
        }
    )

    comparison_display = comparison_display.sort_values(
        "TRx",
        ascending=False
    )

    st.dataframe(
        comparison_display.style.format(
            {
                "NRx": "{:,.0f}",
                "TRx": "{:,.0f}",
                "NRx Share": "{:.1f}%",
                "TRx Share": "{:.1f}%",
                "Patients": "{:,.0f}",
                "Paid Rate": "{:.1f}%",
                "Formulary Match": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # SELECTED PRODUCT DETAIL
    # ========================================================

    st.markdown("### Selected Product")

    detail_options = sorted(
        filtered_products["Brand_Name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if detail_options:

        detail_product = st.selectbox(
            "Select a product to explore",
            detail_options,
            key="competitive_detail_product",
        )

        selected_product_data = filtered_products[
            filtered_products["Brand_Name"].astype(str)
            == detail_product
        ].copy()

        if not selected_product_data.empty:

            product_row = selected_product_data.iloc[0]

            detail_nrx = pd.to_numeric(
                product_row["NRx_Proxy"],
                errors="coerce"
            )

            detail_trx = pd.to_numeric(
                product_row["TRx_Proxy"],
                errors="coerce"
            )

            detail_patients = pd.to_numeric(
                product_row["Unique_Patients"],
                errors="coerce"
            )

            detail_active = pd.to_numeric(
                product_row["Active_Treatments"],
                errors="coerce"
            )

            detail_discontinued = pd.to_numeric(
                product_row["Discontinued_Treatments"],
                errors="coerce"
            )

            detail_paid_rate = pd.to_numeric(
                product_row["Paid_Claim_Rate"],
                errors="coerce"
            ) * 100

            detail_formulary_rate = pd.to_numeric(
                product_row["Formulary_Match_Rate"],
                errors="coerce"
            ) * 100

            class_nrx_total = comparison_data["NRx Proxy"].sum()
            class_trx_total = comparison_data["TRx Proxy"].sum()

            detail_nrx_share = (
                detail_nrx / class_nrx_total * 100
                if class_nrx_total > 0
                else 0
            )

            detail_trx_share = (
                detail_trx / class_trx_total * 100
                if class_trx_total > 0
                else 0
            )

            detail_col1, detail_col2, detail_col3 = st.columns(3)

            with detail_col1:

                st.markdown("#### Product")

                st.write(f"**{detail_product}**")

                st.write(
                    f"Competitor: **{product_row['Competitor']}**"
                )

                st.write(
                    f"Therapy: **{product_row['Therapy_Class']}**"
                )

                st.write(
                    f"DIN: **{product_row['DIN']}**"
                )

            with detail_col2:

                st.markdown("#### Prescription Activity")

                st.metric(
                    "NRx Proxy",
                    f"{detail_nrx:,.0f}"
                )

                st.metric(
                    "TRx Proxy",
                    f"{detail_trx:,.0f}"
                )

                st.metric(
                    "NRx Share",
                    f"{detail_nrx_share:.1f}%"
                )

                st.metric(
                    "TRx Share",
                    f"{detail_trx_share:.1f}%"
                )

            with detail_col3:

                st.markdown("#### Patients & Access")

                st.metric(
                    "Unique Patients",
                    f"{detail_patients:,.0f}"
                )

                st.metric(
                    "Paid Claim Rate",
                    f"{detail_paid_rate:.1f}%"
                )

                st.metric(
                    "Formulary Match",
                    f"{detail_formulary_rate:.1f}%"
                )

                st.write(
                    f"Active Treatments: **{detail_active:,.0f}**"
                )

                st.write(
                    f"Discontinued Treatments: **{detail_discontinued:,.0f}**"
                )

    # ========================================================
    # DATA & INTERPRETATION NOTE
    # ========================================================

    st.markdown("### Analytical Note")

    st.info(
        "This view uses synthetic prescription, treatment, and pharmacy "
        "claims data. NRx and TRx are analytical proxies rather than "
        "real-world prescription measures. Competitor attribution is "
        "synthetically inferred from product naming conventions. "
        "The visualizations identify analytical signals and do not "
        "establish causal relationships."
    )

