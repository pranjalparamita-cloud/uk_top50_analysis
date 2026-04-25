import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.metrics import single_vs_album_ratio
from utils.charts import (
    chart_album_type_bar,
    chart_album_size_vs_position,
    chart_album_size_category,
)
import plotly.express as px

st.set_page_config(page_title="Album Structure", page_icon="💿", layout="wide")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

df_raw = load_data()

with st.sidebar:
    st.markdown("## 💿 Album Structure")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    explicit_toggle = st.radio("Explicit Filter", ["All", "Explicit Only", "Clean Only"])

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d))
if explicit_toggle == "Explicit Only":
    df = df[df["is_explicit"]]
elif explicit_toggle == "Clean Only":
    df = df[~df["is_explicit"]]

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#FFB703,#FB8500);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">💿 Album Structure & Release Strategy</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            Single vs album, album size categories and their impact on chart performance.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
sar = single_vs_album_ratio(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("💿 Most Common Type",   max(sar["counts"], key=sar["counts"].get, default="N/A"))
c2.metric("📀 Single Share",       f"{sar['shares'].get('Single', 0)*100:.1f}%")
c3.metric("🎵 Album Share",        f"{sar['shares'].get('Album', 0)*100:.1f}%")
c4.metric("📊 Avg Album Tracks",   f"{df['total_tracks'].mean():.1f}")

st.markdown("---")

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(chart_album_type_bar(df), use_container_width=True)
with col_r:
    st.plotly_chart(chart_album_size_category(df), use_container_width=True)

st.plotly_chart(chart_album_size_vs_position(df), use_container_width=True)

# ── Album type vs popularity ───────────────────────────────────────────────────
st.markdown("### 🌟 Album Type vs Popularity")
fig = px.violin(
    df,
    x="album_type",
    y="popularity",
    color="album_type",
    box=True,
    points="outliers",
    color_discrete_sequence=["#2EC4B6", "#FFB703", "#9B5DE5"],
    title="Popularity Distribution by Album Type",
    template="plotly_dark",
)
fig.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#161B22", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ── Album size heatmap ─────────────────────────────────────────────────────────
st.markdown("### 🌡️ Album Size Category × Rank Group Heatmap")
import pandas as pd
hmap = (
    df.groupby(["album_size_category", "rank_group"], observed=True)
    .size()
    .unstack(fill_value=0)
)
import plotly.graph_objects as go
fig_h = go.Figure(
    go.Heatmap(
        z=hmap.values,
        x=hmap.columns.astype(str).tolist(),
        y=hmap.index.astype(str).tolist(),
        colorscale="YlOrRd",
        text=hmap.values,
        texttemplate="%{text}",
    )
)
fig_h.update_layout(
    paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
    font=dict(color="#FFFFFF"),
    height=400,
    title="Track Count Heatmap: Album Size vs Chart Rank Group",
)
st.plotly_chart(fig_h, use_container_width=True)