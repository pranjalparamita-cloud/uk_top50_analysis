import pandas as pd
import numpy as np
from utils.data_loader import get_exploded_artists


def artist_concentration_index(df: pd.DataFrame, top_n: int = 5) -> float:
    """
    Concentration Ratio: share of chart entries held by top N artists.
    Range: 0 (perfectly diverse) → 1 (monopoly).
    """
    exploded = get_exploded_artists(df)
    counts = exploded["individual_artist"].value_counts()
    total = counts.sum()
    if total == 0:
        return 0.0
    top_share = counts.head(top_n).sum() / total
    return round(float(top_share), 4)


def unique_artist_count(df: pd.DataFrame) -> int:
    """Total unique individual artists across the filtered dataset."""
    exploded = get_exploded_artists(df)
    return int(exploded["individual_artist"].nunique())


def diversity_score(df: pd.DataFrame) -> float:
    """
    Diversity Score = Unique Artists / Total Chart Entries.
    Higher = more diverse market.
    """
    total_entries = len(df)
    if total_entries == 0:
        return 0.0
    unique = unique_artist_count(df)
    return round(unique / total_entries, 4)


def collaboration_ratio(df: pd.DataFrame) -> float:
    """Share of tracks that feature 2+ artists."""
    if len(df) == 0:
        return 0.0
    return round(df["is_collaboration"].mean(), 4)


def explicit_content_share(df: pd.DataFrame) -> float:
    """Share of tracks flagged as explicit."""
    if len(df) == 0:
        return 0.0
    return round(df["is_explicit"].mean(), 4)


def single_vs_album_ratio(df: pd.DataFrame) -> dict:
    """Returns count and share of each album_type."""
    counts = df["album_type"].value_counts()
    shares = df["album_type"].value_counts(normalize=True).round(4)
    return {"counts": counts.to_dict(), "shares": shares.to_dict()}


def content_variety_index(df: pd.DataFrame) -> float:
    """
    Composite variety = average of diversity, (1-concentration),
    and collaboration ratio normalized.
    """
    d = diversity_score(df)
    c = 1 - artist_concentration_index(df)
    cr = collaboration_ratio(df)
    return round(np.mean([d, c, cr]), 4)


def top_artists_table(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Leaderboard: top N artists by chart appearances."""
    exploded = get_exploded_artists(df)
    table = (
        exploded.groupby("individual_artist")
        .agg(
            appearances=("song_artist_key", "count"),
            avg_position=("position", "mean"),
            avg_popularity=("popularity", "mean"),
            unique_songs=("song", "nunique"),
            top1_count=("position", lambda x: (x == 1).sum()),
            top10_count=("position", lambda x: (x <= 10).sum()),
        )
        .reset_index()
        .sort_values("appearances", ascending=False)
        .head(n)
    )
    table["avg_position"] = table["avg_position"].round(1)
    table["avg_popularity"] = table["avg_popularity"].round(1)
    return table.reset_index(drop=True)


def collaboration_network_data(df: pd.DataFrame) -> tuple:
    """
    Build nodes and edges for the collaboration network.
    Returns (nodes_df, edges_df).
    """
    from itertools import combinations

    edges = []
    collab_df = df[df["is_collaboration"]].copy()

    for _, row in collab_df.iterrows():
        artists = row["artist_list"]
        for a, b in combinations(sorted(artists), 2):
            edges.append(
                {
                    "source": a,
                    "target": b,
                    "song": row["song"],
                    "position": row["position"],
                    "popularity": row["popularity"],
                }
            )

    if not edges:
        return pd.DataFrame(), pd.DataFrame()

    edges_df = (
        pd.DataFrame(edges)
        .groupby(["source", "target"])
        .agg(weight=("song", "count"), avg_position=("position", "mean"))
        .reset_index()
    )

    all_artists = set(edges_df["source"]).union(set(edges_df["target"]))
    exploded = get_exploded_artists(df)
    artist_appearances = (
        exploded.groupby("individual_artist")["song_artist_key"]
        .count()
        .to_dict()
    )

    nodes_df = pd.DataFrame(
        [
            {"artist": a, "appearances": artist_appearances.get(a, 1)}
            for a in all_artists
        ]
    )
    return nodes_df, edges_df


def duration_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Summary stats of duration grouped by popularity bucket."""
    return (
        df.groupby("popularity_bucket", observed=True)
        .agg(
            avg_duration_min=("duration_min", "mean"),
            median_duration_min=("duration_min", "median"),
            track_count=("song", "count"),
        )
        .round(2)
        .reset_index()
    )


def rank_group_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """KPI breakdown by rank group."""
    group = df.groupby("rank_group", observed=True)
    result = pd.DataFrame(
        {
            "Explicit Share": group["is_explicit"].mean().round(3),
            "Collab Share": group["is_collaboration"].mean().round(3),
            "Avg Duration (min)": group["duration_min"].mean().round(2),
            "Avg Popularity": group["popularity"].mean().round(1),
            "Track Count": group["song"].count(),
        }
    ).reset_index()
    return result