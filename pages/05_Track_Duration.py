import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.metrics import duration_analysis
from utils.charts import (
    chart_duration_histogram,
    chart_duration_bucket_popularity,
    chart_duration_by_explicit,
)
import plotly.express as px

st.set_page_config(page_title="Track Duration", page_icon="⏱️", layout="wide")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

df_raw = load_data()

with st.sidebar:
    st.markdown("## ⏱️ Track Duration")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    collab_f = st.radio("Track Type", ["All", "Solo Only", "Collaborations Only"])

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d), collab_filter=collab_f)

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#06D6A0,#3A86FF);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">⏱️ Track Duration & Format Analysis</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            UK listener format preferences — short-form vs long-form & popularity correlation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("⏱️ Avg Duration",    f"{df['duration_min'].mean():.2f} min")
c2.metric("📐 Median Duration", f"{df['duration_min'].median():.2f} min")
c3.metric("⬇️ Shortest Track",  f"{df['duration_min'].min():.2f} min")
c4.metric("⬆️ Longest Track",   f"{df['duration_min'].max():.2f} min")

st.markdown("---")

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(chart_duration_histogram(df), use_container_width=True)
with col_r:
    st.plotly_chart(chart_duration_bucket_popularity(df), use_container_width=True)

st.plotly_chart(chart_duration_by_explicit(df), use_container_width=True)

# ── Duration vs position scatter ───────────────────────────────────────────────
st.markdown("### 🎯 Duration vs Chart Position")
fig = px.scatter(
    df,
    x="duration_min",
    y="position",
    color="popularity",
    size="popularity",
    hover_data=["song", "artist", "album_type"],
    color_continuous_scale="RdYlGn",
    labels={"duration_min": "Duration (min)", "position": "Chart Position"},
    title="Track Duration vs Chart Position (colored by Popularity)",
    template="plotly_dark",
)
fig.update_layout(
    paper_bgcolor="#0D1117",
    plot_bgcolor="#161B22",
    yaxis_autorange="reversed",
    height=480,
)
st.plotly_chart(fig, use_container_width=True)

# ── Duration stats table ───────────────────────────────────────────────────────
st.markdown("### 📋 Duration Analysis by Popularity Bucket")
da = duration_analysis(df)
st.dataframe(da, use_container_width=True)