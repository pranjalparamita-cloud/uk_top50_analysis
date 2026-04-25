import streamlit as st
from utils.data_loader import load_data, filter_data, get_exploded_artists
from utils.metrics import (
    artist_concentration_index,
    unique_artist_count,
    diversity_score,
    collaboration_ratio,
    explicit_content_share,
    content_variety_index,
    rank_group_analysis,
)
from utils.charts import (
    chart_market_kpi_gauge,
    chart_popularity_heatmap,
    chart_daily_unique_artists,
    BRAND_RED, BRAND_BLUE, BRAND_TEAL, BRAND_YELLOW, BRAND_GREEN, BRAND_PURPLE,
)
import plotly.express as px

st.set_page_config(page_title="Market Structure", page_icon="📊", layout="wide")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

df_raw = load_data()

with st.sidebar:
    st.markdown("## 📊 Market Structure")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d))

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#9B5DE5,#3A86FF);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">📊 Market Structure Metrics</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            Concentration, diversity, variety — a holistic view of the UK music market balance.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Gauge KPIs ─────────────────────────────────────────────────────────────────
st.markdown("### 🎯 KPI Gauges")
g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(
        chart_market_kpi_gauge(artist_concentration_index(df), "Artist Concentration Index", BRAND_RED),
        use_container_width=True,
    )
with g2:
    st.plotly_chart(
        chart_market_kpi_gauge(diversity_score(df), "Diversity Score", BRAND_GREEN),
        use_container_width=True,
    )
with g3:
    st.plotly_chart(
        chart_market_kpi_gauge(content_variety_index(df), "Content Variety Index", BRAND_PURPLE),
        use_container_width=True,
    )

g4, g5, g6 = st.columns(3)
with g4:
    st.plotly_chart(
        chart_market_kpi_gauge(collaboration_ratio(df), "Collaboration Ratio", BRAND_TEAL),
        use_container_width=True,
    )
with g5:
    st.plotly_chart(
        chart_market_kpi_gauge(explicit_content_share(df), "Explicit Content Share", BRAND_RED),
        use_container_width=True,
    )
with g6:
    st.plotly_chart(
        chart_market_kpi_gauge(
            min(unique_artist_count(df) / 50, 1.0), "Unique Artist Density", BRAND_YELLOW
        ),
        use_container_width=True,
    )

st.markdown("---")

# ── Heatmap & trend ────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(chart_popularity_heatmap(df), use_container_width=True)
with col_r:
    st.plotly_chart(chart_daily_unique_artists(df), use_container_width=True)

# ── Rank group breakdown ───────────────────────────────────────────────────────
st.markdown("### 📋 Rank Group KPI Breakdown")
rga = rank_group_analysis(df)
st.dataframe(
    rga.style.background_gradient(subset=["Explicit Share", "Collab Share"], cmap="RdYlGn"),
    use_container_width=True,
)

# ── Monthly diversity trend ────────────────────────────────────────────────────
st.markdown("### 📅 Monthly Diversity Trend")
exploded = get_exploded_artists(df)
monthly = (
    exploded.groupby("year_month")["individual_artist"]
    .nunique()
    .reset_index()
    .rename(columns={"individual_artist": "unique_artists"})
    .sort_values("year_month")
)
fig = px.area(
    monthly,
    x="year_month",
    y="unique_artists",
    title="Unique Artists per Month",
    color_discrete_sequence=[BRAND_BLUE],
    template="plotly_dark",
)
fig.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#161B22")
st.plotly_chart(fig, use_container_width=True)

# ── Summary metrics table ──────────────────────────────────────────────────────
st.markdown("### 🧾 Full KPI Summary")
summary = {
    "KPI": [
        "Artist Concentration Index (CR5)",
        "Unique Artist Count",
        "Diversity Score",
        "Collaboration Ratio",
        "Explicit Content Share",
        "Content Variety Index",
        "Total Chart Entries",
    ],
    "Value": [
        f"{artist_concentration_index(df)*100:.2f}%",
        str(unique_artist_count(df)),
        f"{diversity_score(df):.4f}",
        f"{collaboration_ratio(df)*100:.2f}%",
        f"{explicit_content_share(df)*100:.2f}%",
        f"{content_variety_index(df):.4f}",
        str(len(df)),
    ],
    "Interpretation": [
        "% of chart owned by top 5 artists — lower = healthier market",
        "Higher = more artist variety in the market",
        "Ratio of distinct artists — closer to 1.0 = very diverse",
        "% of tracks featuring partnerships",
        "% of tracks flagged explicit — cultural sensitivity signal",
        "Composite market balance score — higher = more balanced",
        "Total data rows in current selection",
    ],
}
import pandas as pd
st.dataframe(pd.DataFrame(summary), use_container_width=True, height=320)