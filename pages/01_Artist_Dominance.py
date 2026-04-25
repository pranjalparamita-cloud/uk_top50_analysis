import streamlit as st
from utils.data_loader import load_data, filter_data, get_exploded_artists
from utils.metrics import top_artists_table, artist_concentration_index
from utils.charts import (
    chart_artist_leaderboard,
    chart_artist_avg_position,
    chart_top1_dominance,
)
import plotly.express as px

st.set_page_config(page_title="Artist Dominance", page_icon="🏆", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="metric-container"] {
        background: #161B22;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

df_raw = load_data()

# ── Sidebar filters (mirror main) ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 Artist Dominance")
    min_d = df_raw["date"].min().date()
    max_d = df_raw["date"].max().date()
    dr = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    top_n = st.slider("Top N Artists", 5, 30, 15)
    collab_f = st.radio("Track Type", ["All", "Solo Only", "Collaborations Only"])

df = filter_data(df_raw, dr if len(dr) == 2 else (min_d, max_d), collab_filter=collab_f)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:linear-gradient(135deg,#E63946,#9B5DE5);
                border-radius:14px;padding:32px 40px;margin-bottom:24px;">
        <h1 style="color:#fff;margin:0">🏆 Artist Dominance & Diversity</h1>
        <p style="color:rgba(255,255,255,0.85);margin-top:8px">
            Who controls the UK Top 50? Leaderboard, position analysis & market concentration.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
table = top_artists_table(df, n=top_n)
c1, c2, c3, c4 = st.columns(4)
c1.metric("🎤 Top Artist",        table.iloc[0]["individual_artist"] if not table.empty else "N/A")
c2.metric("📈 Max Appearances",   int(table.iloc[0]["appearances"]) if not table.empty else 0)
c3.metric("🎯 Concentration CR5", f"{artist_concentration_index(df, top_n=5)*100:.1f}%")
c4.metric("🎵 Unique Songs",      int(df["song"].nunique()))

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.plotly_chart(chart_artist_leaderboard(table), use_container_width=True)

with col_r:
    st.plotly_chart(chart_artist_avg_position(table), use_container_width=True)

st.plotly_chart(chart_top1_dominance(table), use_container_width=True)

# ── Leaderboard table ──────────────────────────────────────────────────────────
st.markdown("### 📋 Full Artist Leaderboard")
st.dataframe(
    table.rename(
        columns={
            "individual_artist": "Artist",
            "appearances": "Appearances",
            "avg_position": "Avg Position",
            "avg_popularity": "Avg Popularity",
            "unique_songs": "Unique Songs",
            "top1_count": "#1 Count",
            "top10_count": "Top-10 Count",
        }
    ),
    use_container_width=True,
    height=480,
)

# ── Popularity scatter ─────────────────────────────────────────────────────────
st.markdown("### 🌟 Appearances vs Popularity Scatter")
fig_scatter = px.scatter(
    table,
    x="appearances",
    y="avg_popularity",
    size="top10_count",
    color="avg_position",
    text="individual_artist",
    color_continuous_scale="RdYlGn_r",
    labels={
        "appearances": "Chart Appearances",
        "avg_popularity": "Avg Popularity",
        "avg_position": "Avg Position",
    },
    title="Artist Appearances vs Average Popularity (size = Top-10 count)",
    template="plotly_dark",
)
fig_scatter.update_traces(textposition="top center", textfont_size=9)
fig_scatter.update_layout(
    paper_bgcolor="#0D1117",
    plot_bgcolor="#161B22",
    height=500,
)
st.plotly_chart(fig_scatter, use_container_width=True)