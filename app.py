import streamlit as st
import pandas as pd
from utils.data_loader import load_data, filter_data
from utils.metrics import (
    artist_concentration_index,
    unique_artist_count,
    diversity_score,
    collaboration_ratio,
    explicit_content_share,
    single_vs_album_ratio,
    content_variety_index,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UK Top 50 — Atlantic RC",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Global font & background */
    html, body, [class*="css"] { font-family: 'Arial', sans-serif; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #161B22;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    [data-testid="metric-container"] label { color: #9CA3AF !important; font-size: 13px; }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #FFFFFF !important; font-size: 28px; font-weight: 700;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #161B22; }
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #E63946; }

    /* Header gradient */
    .hero-banner {
        background: linear-gradient(135deg, #E63946 0%, #457B9D 100%);
        border-radius: 16px;
        padding: 38px 46px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .hero-banner h1 { color: #FFFFFF; font-size: 2.4rem; margin: 0; }
    .hero-banner p  { color: rgba(255,255,255,0.85); font-size: 1.05rem; margin-top: 8px; }

    /* Section titles */
    .section-title {
        color: #E63946;
        font-size: 1.15rem;
        font-weight: 700;
        border-left: 4px solid #E63946;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.08); }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #161B22;
        border-radius: 8px;
        color: #9CA3AF;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #E63946 !important;
        color: #FFFFFF !important;
    }

    /* Hide Streamlit default header */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Load data ──────────────────────────────────────────────────────────────────
df_raw = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎵 UK Top 50")
    st.markdown("**Atlantic Recording Corporation**")
    st.markdown("---")

    # Date range
    st.markdown("### 📅 Date Range")
    min_date = df_raw["date"].min().date()
    max_date = df_raw["date"].max().date()
    date_range = st.date_input(
        "Select range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("### 🎤 Artist Filter")
    from utils.data_loader import get_exploded_artists
    all_artists = sorted(
        get_exploded_artists(df_raw)["individual_artist"].unique().tolist()
    )
    selected_artists = st.multiselect(
        "Select artists (blank = all)",
        options=all_artists,
        placeholder="All artists",
    )

    st.markdown("### 🤝 Collaboration Filter")
    collab_filter = st.radio(
        "Track type",
        ["All", "Solo Only", "Collaborations Only"],
        index=0,
    )

    st.markdown("### 💿 Album Type")
    album_types = df_raw["album_type"].unique().tolist()
    album_type_filter = st.multiselect(
        "Select album types",
        options=album_types,
        default=album_types,
    )

    st.markdown("---")
    st.caption(f"📊 Dataset: {len(df_raw):,} entries")
    st.caption(f"📆 {min_date} → {max_date}")

# ── Apply filters ──────────────────────────────────────────────────────────────
if len(date_range) == 2:
    df = filter_data(df_raw, date_range, selected_artists, collab_filter, album_type_filter)
else:
    df = df_raw.copy()

# ── Hero Banner ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-banner">
        <h1>🎵 UK Top 50 Playlist Intelligence</h1>
        <p>Atlantic Recording Corporation · Market Structure, Artist Diversity & Content Localization</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top KPI Row ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📌 Key Performance Indicators</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

aci   = artist_concentration_index(df)
uac   = unique_artist_count(df)
ds    = diversity_score(df)
cr    = collaboration_ratio(df)
ecs   = explicit_content_share(df)
sar   = single_vs_album_ratio(df)
cvi   = content_variety_index(df)
total = len(df)

single_pct = sar["shares"].get("Single", 0)

col1.metric("🎯 Artist Concentration", f"{aci*100:.1f}%", help="Top-5 artist share of all entries")
col2.metric("👥 Unique Artists",       f"{uac:,}",         help="Individual artists in filtered data")
col3.metric("🌈 Diversity Score",      f"{ds:.3f}",        help="Unique artists / total entries")
col4.metric("🤝 Collaboration Rate",   f"{cr*100:.1f}%",   help="Tracks with 2+ artists")
col5.metric("🔞 Explicit Share",       f"{ecs*100:.1f}%",  help="Explicit tracks percentage")
col6.metric("💿 Single Share",         f"{single_pct*100:.1f}%", help="Singles vs albums")
col7.metric("📊 Content Variety",      f"{cvi:.3f}",       help="Composite market diversity score")

st.markdown("---")

# ── Data overview ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Dataset Overview</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗂️ Raw Data", "📊 Statistics", "📅 Date Coverage"])

with tab1:
    st.dataframe(
        df[["date", "position", "song", "artist", "popularity",
            "duration_min", "album_type", "total_tracks", "is_explicit",
            "is_collaboration", "collaborator_count", "rank_group"]].sort_values(
            ["date", "position"]
        ).reset_index(drop=True),
        use_container_width=True,
        height=420,
    )

with tab2:
    st.dataframe(
        df[["position", "popularity", "duration_min", "total_tracks",
            "collaborator_count"]].describe().round(2),
        use_container_width=True,
    )

with tab3:
    date_counts = df.groupby("date").size().reset_index(name="entries")
    st.dataframe(date_counts.sort_values("date", ascending=False), use_container_width=True)
    st.info(
        f"📆 **{date_counts['date'].nunique()} unique dates** | "
        f"**{total:,} total entries** in current filter"
    )

# ── Navigation guide ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">🗺️ Navigate the Dashboard</div>', unsafe_allow_html=True)

nav_cols = st.columns(3)
cards = [
    ("🏆", "Artist Dominance",       "Leaderboard, top positions, dominance heatmap",    "pages/01"),
    ("🤝", "Collaboration Analysis", "Network graph, collab rates, partner discovery",    "pages/02"),
    ("🔞", "Explicit Content",       "Explicit vs clean trends, rank & time analysis",    "pages/03"),
    ("💿", "Album Structure",        "Single vs album, size categories, position impact", "pages/04"),
    ("⏱️", "Track Duration",         "Duration distribution, popularity correlation",     "pages/05"),
    ("📊", "Market Structure",       "Concentration, diversity, variety KPI gauges",      "pages/06"),
]
for i, (icon, title, desc, _) in enumerate(cards):
    with nav_cols[i % 3]:
        st.markdown(
            f"""
            <div style="background:#161B22;border:1px solid rgba(255,255,255,0.1);
                        border-radius:12px;padding:20px;margin-bottom:14px;">
                <div style="font-size:2rem;margin-bottom:6px">{icon}</div>
                <div style="color:#E63946;font-weight:700;font-size:1rem">{title}</div>
                <div style="color:#9CA3AF;font-size:0.85rem;margin-top:6px">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.caption("© 2024 Atlantic Recording Corporation · UK Market Intelligence Dashboard · Powered by Streamlit")