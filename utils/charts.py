import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx

# ── Brand Colors ──────────────────────────────────────────────────────────────
BRAND_RED      = "#E63946"
BRAND_BLUE     = "#457B9D"
BRAND_TEAL     = "#2EC4B6"
BRAND_YELLOW   = "#FFB703"
BRAND_PURPLE   = "#9B5DE5"
BRAND_GREEN    = "#06D6A0"
BG_DARK        = "#0D1117"
BG_CARD        = "#161B22"
TEXT_COLOR     = "#FFFFFF"

PALETTE = [
    BRAND_RED, BRAND_BLUE, BRAND_TEAL,
    BRAND_YELLOW, BRAND_PURPLE, BRAND_GREEN,
    "#FB8500", "#8338EC", "#3A86FF", "#FF006E",
]

BASE_LAYOUT = dict(
    paper_bgcolor=BG_DARK,
    plot_bgcolor=BG_CARD,
    font=dict(color=TEXT_COLOR, family="Arial"),
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)"),
)


def apply_base(fig: go.Figure) -> go.Figure:
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", zeroline=False)
    return fig


# ── 1. Artist Dominance ───────────────────────────────────────────────────────

def chart_artist_leaderboard(df: pd.DataFrame) -> go.Figure:
    df_s = df.head(15).sort_values("appearances")
    fig = go.Figure(
        go.Bar(
            x=df_s["appearances"],
            y=df_s["individual_artist"],
            orientation="h",
            marker=dict(
                color=df_s["appearances"],
                colorscale=[[0, BRAND_BLUE], [1, BRAND_RED]],
                showscale=False,
            ),
            text=df_s["appearances"],
            textposition="outside",
            textfont=dict(color=TEXT_COLOR),
        )
    )
    fig.update_layout(
        title="🏆 Top Artists by Chart Appearances",
        xaxis_title="Appearances",
        yaxis_title="Artist",
        height=520,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_artist_avg_position(df: pd.DataFrame) -> go.Figure:
    df_s = df.head(15).sort_values("avg_position", ascending=False)
    fig = go.Figure(
        go.Bar(
            x=df_s["avg_position"],
            y=df_s["individual_artist"],
            orientation="h",
            marker=dict(
                color=df_s["avg_position"],
                colorscale=[[0, BRAND_GREEN], [1, BRAND_YELLOW]],
                reversescale=True,
                showscale=False,
            ),
            text=df_s["avg_position"].apply(lambda x: f"#{x:.1f}"),
            textposition="outside",
            textfont=dict(color=TEXT_COLOR),
        )
    )
    fig.update_layout(
        title="📍 Average Chart Position (Lower = Better)",
        xaxis_title="Average Position",
        yaxis_title="Artist",
        height=520,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_top1_dominance(df: pd.DataFrame) -> go.Figure:
    df_s = df[df["top1_count"] > 0].sort_values("top1_count", ascending=False).head(10)
    fig = go.Figure(
        go.Bar(
            x=df_s["individual_artist"],
            y=df_s["top1_count"],
            marker_color=BRAND_RED,
            text=df_s["top1_count"],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="👑 #1 Position Count by Artist",
        xaxis_title="Artist",
        yaxis_title="Times at #1",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


# ── 2. Collaboration ──────────────────────────────────────────────────────────

def chart_collab_vs_solo(df: pd.DataFrame) -> go.Figure:
    counts = df["is_collaboration"].map({True: "Collaboration", False: "Solo"}).value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=[BRAND_TEAL, BRAND_RED]),
            textinfo="label+percent",
            textfont=dict(size=14, color=TEXT_COLOR),
        )
    )
    fig.update_layout(
        title="🤝 Solo vs Collaboration Tracks",
        height=420,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_collab_by_rank_group(df: pd.DataFrame) -> go.Figure:
    grp = (
        df.groupby("rank_group", observed=True)["is_collaboration"]
        .mean()
        .reset_index()
    )
    grp["pct"] = (grp["is_collaboration"] * 100).round(1)
    fig = go.Figure(
        go.Bar(
            x=grp["rank_group"].astype(str),
            y=grp["pct"],
            marker_color=BRAND_PURPLE,
            text=grp["pct"].apply(lambda x: f"{x}%"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="📊 Collaboration Rate by Chart Rank Group",
        xaxis_title="Rank Group",
        yaxis_title="Collaboration %",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_collaboration_network(nodes_df, edges_df) -> go.Figure:
    if nodes_df.empty or edges_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No collaboration data available",
            **BASE_LAYOUT,
        )
        return fig

    G = nx.Graph()
    for _, row in nodes_df.iterrows():
        G.add_node(row["artist"], size=row["appearances"])
    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"], weight=row["weight"])

    pos = nx.spring_layout(G, seed=42, k=1.2)

    edge_x, edge_y = [], []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_text = list(G.nodes())
    node_size = [max(10, G.nodes[n].get("size", 5) * 3) for n in G.nodes()]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=0.8, color="rgba(255,255,255,0.15)"),
            hoverinfo="none",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            textfont=dict(size=9, color=TEXT_COLOR),
            marker=dict(
                size=node_size,
                color=BRAND_RED,
                line=dict(width=1.5, color=TEXT_COLOR),
                opacity=0.85,
            ),
            hovertemplate="<b>%{text}</b><extra></extra>",
        )
    )
    fig.update_layout(
        title="🕸️ Artist Collaboration Network",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=580,
        **BASE_LAYOUT,
    )
    return fig


# ── 3. Explicit Content ───────────────────────────────────────────────────────

def chart_explicit_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["is_explicit"].map({True: "🔞 Explicit", False: "✅ Clean"}).value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.60,
            marker=dict(colors=[BRAND_RED, BRAND_GREEN]),
            textinfo="label+percent",
            textfont=dict(size=14),
        )
    )
    fig.update_layout(
        title="🎵 Explicit vs Clean Content Distribution",
        height=420,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_explicit_by_rank(df: pd.DataFrame) -> go.Figure:
    grp = (
        df.groupby("rank_group", observed=True)["is_explicit"]
        .mean()
        .reset_index()
    )
    grp["pct"] = (grp["is_explicit"] * 100).round(1)
    fig = go.Figure(
        go.Bar(
            x=grp["rank_group"].astype(str),
            y=grp["pct"],
            marker=dict(
                color=grp["pct"],
                colorscale=[[0, BRAND_GREEN], [1, BRAND_RED]],
            ),
            text=grp["pct"].apply(lambda x: f"{x}%"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="🔞 Explicit Content Rate by Rank Group",
        xaxis_title="Rank Group",
        yaxis_title="Explicit %",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_explicit_trend(df: pd.DataFrame) -> go.Figure:
    trend = (
        df.groupby("year_month")["is_explicit"]
        .mean()
        .reset_index()
        .sort_values("year_month")
    )
    trend["pct"] = (trend["is_explicit"] * 100).round(1)
    fig = go.Figure(
        go.Scatter(
            x=trend["year_month"],
            y=trend["pct"],
            mode="lines+markers",
            line=dict(color=BRAND_RED, width=2.5),
            marker=dict(size=7, color=BRAND_RED),
            fill="tozeroy",
            fillcolor="rgba(230,57,70,0.15)",
        )
    )
    fig.update_layout(
        title="📈 Explicit Content Trend Over Time",
        xaxis_title="Month",
        yaxis_title="Explicit %",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


# ── 4. Album Structure ────────────────────────────────────────────────────────

def chart_album_type_bar(df: pd.DataFrame) -> go.Figure:
    counts = df["album_type"].value_counts().reset_index()
    counts.columns = ["Album Type", "Count"]
    fig = go.Figure(
        go.Bar(
            x=counts["Album Type"],
            y=counts["Count"],
            marker_color=[BRAND_TEAL, BRAND_YELLOW, BRAND_PURPLE][: len(counts)],
            text=counts["Count"],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="💿 Album Type Distribution",
        xaxis_title="Type",
        yaxis_title="Track Count",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_album_size_vs_position(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=df["total_tracks"],
            y=df["position"],
            mode="markers",
            marker=dict(
                color=df["popularity"],
                colorscale="RdYlGn",
                size=8,
                opacity=0.7,
                colorbar=dict(title="Popularity"),
            ),
            text=df["song"] + " – " + df["artist"],
            hovertemplate="<b>%{text}</b><br>Tracks: %{x}<br>Position: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title="📦 Album Size vs Chart Position (colored by Popularity)",
        xaxis_title="Total Tracks in Album",
        yaxis_title="Chart Position",
        yaxis_autorange="reversed",
        height=460,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_album_size_category(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["album_size_category"]
        .value_counts()
        .reindex(["Single (1)", "EP (2–6)", "Standard (7–12)", "Deluxe (13–20)", "Extended (20+)"])
        .dropna()
        .reset_index()
    )
    counts.columns = ["Category", "Count"]
    fig = go.Figure(
        go.Bar(
            x=counts["Category"],
            y=counts["Count"],
            marker_color=PALETTE[: len(counts)],
            text=counts["Count"],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="🗂️ Album Size Category Distribution",
        xaxis_title="Category",
        yaxis_title="Track Count",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


# ── 5. Duration ───────────────────────────────────────────────────────────────

def chart_duration_histogram(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Histogram(
            x=df["duration_min"],
            nbinsx=40,
            marker=dict(
                color=BRAND_TEAL,
                line=dict(color=BG_DARK, width=0.5),
            ),
        )
    )
    fig.update_layout(
        title="⏱️ Track Duration Distribution",
        xaxis_title="Duration (minutes)",
        yaxis_title="Count",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_duration_bucket_popularity(df: pd.DataFrame) -> go.Figure:
    grp = (
        df.groupby("duration_bucket", observed=True)["popularity"]
        .mean()
        .reset_index()
    )
    fig = go.Figure(
        go.Bar(
            x=grp["duration_bucket"].astype(str),
            y=grp["popularity"].round(1),
            marker_color=BRAND_YELLOW,
            text=grp["popularity"].round(1),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="🎯 Avg Popularity by Duration Bucket",
        xaxis_title="Duration Bucket",
        yaxis_title="Avg Popularity Score",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_duration_by_explicit(df: pd.DataFrame) -> go.Figure:
    labels = {True: "Explicit", False: "Clean"}
    fig = go.Figure()
    for flag, label in labels.items():
        sub = df[df["is_explicit"] == flag]["duration_min"]
        fig.add_trace(
            go.Box(
                y=sub,
                name=label,
                marker_color=BRAND_RED if flag else BRAND_GREEN,
                boxmean=True,
            )
        )
    fig.update_layout(
        title="📦 Duration Distribution: Explicit vs Clean",
        yaxis_title="Duration (minutes)",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


# ── 6. Market Structure ───────────────────────────────────────────────────────

def chart_market_kpi_gauge(value: float, title: str, color: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(value * 100, 1),
            title={"text": title, "font": {"color": TEXT_COLOR, "size": 14}},
            number={"suffix": "%", "font": {"color": TEXT_COLOR}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": TEXT_COLOR},
                "bar": {"color": color},
                "bgcolor": BG_CARD,
                "bordercolor": TEXT_COLOR,
                "steps": [
                    {"range": [0, 33], "color": "rgba(255,255,255,0.05)"},
                    {"range": [33, 66], "color": "rgba(255,255,255,0.08)"},
                    {"range": [66, 100], "color": "rgba(255,255,255,0.12)"},
                ],
            },
        )
    )
    fig.update_layout(height=280, paper_bgcolor=BG_DARK, font=dict(color=TEXT_COLOR))
    return fig


def chart_popularity_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = (
        df.groupby(["rank_group", "album_type"], observed=True)["popularity"]
        .mean()
        .unstack(fill_value=0)
        .round(1)
    )
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.astype(str).tolist(),
            colorscale="RdYlGn",
            text=pivot.values.round(1),
            texttemplate="%{text}",
            textfont={"size": 12},
        )
    )
    fig.update_layout(
        title="🌡️ Popularity Heatmap: Rank Group × Album Type",
        height=400,
        **BASE_LAYOUT,
    )
    return apply_base(fig)


def chart_daily_unique_artists(df: pd.DataFrame) -> go.Figure:
    from utils.data_loader import get_exploded_artists
    daily = (
        get_exploded_artists(df)
        .groupby("date")["individual_artist"]
        .nunique()
        .reset_index()
        .rename(columns={"individual_artist": "unique_artists"})
    )
    fig = go.Figure(
        go.Scatter(
            x=daily["date"],
            y=daily["unique_artists"],
            mode="lines",
            line=dict(color=BRAND_GREEN, width=2),
            fill="tozeroy",
            fillcolor="rgba(6,214,160,0.15)",
        )
    )
    fig.update_layout(
        title="📅 Daily Unique Artist Count",
        xaxis_title="Date",
        yaxis_title="Unique Artists",
        height=380,
        **BASE_LAYOUT,
    )
    return apply_base(fig)