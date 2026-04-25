import streamlit as st
from utils.data_loader import load_data, filter_data
from utils.metrics import collaboration_network_data, collaboration_ratio
from utils.charts import (
    chart_collab_vs_solo,
    chart_collab_by_rank_group,
    chart_collaboration_network,
)
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Collaboration Analysis", page_icon="🤝", layout="wide")
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

df_raw = load_data()

with st.sidebar:
    st.markdown("## 🤝 Collaboration Analysis")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    min_weight = st.slider("Min. collaboration appearances for network", 1, 10, 1)

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d))

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#2EC4B6,#457B9D);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">🤝 Collaboration Structure Analysis</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            How do artist partnerships shape the UK chart? Network dynamics & collaboration patterns.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
collab_tracks = df[df["is_collaboration"]]
solo_tracks   = df[~df["is_collaboration"]]

c1.metric("🤝 Collaboration Rate",  f"{collaboration_ratio(df)*100:.1f}%")
c2.metric("🎵 Collab Tracks",       len(collab_tracks))
c3.metric("🎤 Solo Tracks",         len(solo_tracks))
c4.metric("👥 Avg Collaborators",   f"{df.loc[df['is_collaboration'], 'collaborator_count'].mean():.2f}")

st.markdown("---")

# ── Donut + Rank bar ───────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(chart_collab_vs_solo(df), use_container_width=True)
with col_r:
    st.plotly_chart(chart_collab_by_rank_group(df), use_container_width=True)

# ── Network ────────────────────────────────────────────────────────────────────
st.markdown("### 🕸️ Artist Collaboration Network")
nodes_df, edges_df = collaboration_network_data(df)

if not edges_df.empty:
    edges_filtered = edges_df[edges_df["weight"] >= min_weight]
    nodes_filtered = nodes_df[
        nodes_df["artist"].isin(
            set(edges_filtered["source"]).union(set(edges_filtered["target"]))
        )
    ]
    st.plotly_chart(
        chart_collaboration_network(nodes_filtered, edges_filtered),
        use_container_width=True,
    )

    st.markdown("### 📋 Top Collaboration Pairs")
    edges_display = edges_filtered.sort_values("weight", ascending=False).head(20)
    edges_display.columns = ["Artist A", "Artist B", "Co-appearances", "Avg Position"]
    st.dataframe(edges_display, use_container_width=True)
else:
    st.info("No collaboration data found in the current filter selection.")

# ── Collaborator count distribution ───────────────────────────────────────────
st.markdown("### 📊 Collaborator Count Distribution")
count_dist = df["collaborator_count"].value_counts().sort_index().reset_index()
count_dist.columns = ["Collaborators", "Track Count"]
fig_bar = px.bar(
    count_dist,
    x="Collaborators",
    y="Track Count",
    color="Track Count",
    color_continuous_scale=[[0, "#2EC4B6"], [1, "#E63946"]],
    title="Number of Artists per Track",
    template="plotly_dark",
)
fig_bar.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#161B22")
st.plotly_chart(fig_bar, use_container_width=True)