import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.metrics import explicit_content_share, rank_group_analysis
from utils.charts import (
    chart_explicit_donut,
    chart_explicit_by_rank,
    chart_explicit_trend,
)
import plotly.express as px

st.set_page_config(page_title="Explicit Content", page_icon="🔞", layout="wide")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

df_raw = load_data()

with st.sidebar:
    st.markdown("## 🔞 Explicit Content")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    album_types = df_raw["album_type"].unique().tolist()
    at = st.multiselect("Album Type", album_types, default=album_types)

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d), album_type_filter=at)

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#E63946,#FF6B6B);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">🔞 Explicit Content Analysis</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            UK listener sensitivity — explicit vs clean content performance by chart position.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
explicit_df = df[df["is_explicit"]]
clean_df    = df[~df["is_explicit"]]

c1, c2, c3, c4 = st.columns(4)
c1.metric("🔞 Explicit Share",      f"{explicit_content_share(df)*100:.1f}%")
c2.metric("✅ Clean Share",          f"{(1-explicit_content_share(df))*100:.1f}%")
c3.metric("📈 Explicit Avg Popularity",
          f"{explicit_df['popularity'].mean():.1f}" if not explicit_df.empty else "N/A")
c4.metric("📊 Clean Avg Popularity",
          f"{clean_df['popularity'].mean():.1f}" if not clean_df.empty else "N/A")

st.markdown("---")

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(chart_explicit_donut(df), use_container_width=True)
with col_r:
    st.plotly_chart(chart_explicit_by_rank(df), use_container_width=True)

st.plotly_chart(chart_explicit_trend(df), use_container_width=True)

# ── Popularity comparison ──────────────────────────────────────────────────────
st.markdown("### 🎯 Popularity: Explicit vs Clean by Album Type")
fig = px.box(
    df,
    x="album_type",
    y="popularity",
    color="is_explicit",
    color_discrete_map={True: "#E63946", False: "#06D6A0"},
    labels={"is_explicit": "Explicit", "album_type": "Album Type", "popularity": "Popularity"},
    title="Popularity Distribution by Album Type & Explicit Flag",
    template="plotly_dark",
)
fig.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#161B22")
st.plotly_chart(fig, use_container_width=True)

# ── Rank group table ───────────────────────────────────────────────────────────
st.markdown("### 📋 Rank Group Breakdown")
rga = rank_group_analysis(df)
st.dataframe(rga, use_container_width=True)