import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def load_data(filepath: str = "data/uk_top50.csv") -> pd.DataFrame:
    """
    Load, clean, and standardize the UK Top 50 dataset.
    Returns a fully validated and enriched DataFrame.
    """
    df = pd.read_csv(filepath)

    # ── 1. Column name standardization ──────────────────────────────
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ── 2. Date parsing ─────────────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.normalize()           # remove time component
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["date"].dt.day_name()
    df["week_number"] = df["date"].dt.isocalendar().week.astype(int)

    # ── 3. Position validation ──────────────────────────────────────
    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    df = df[df["position"].between(1, 50)]

    # ── 4. Artist normalization ──────────────────────────────────────
    df["artist"] = df["artist"].astype(str).str.strip()
    df["artist_normalized"] = (
        df["artist"]
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # ── 5. Collaboration detection ───────────────────────────────────
    # Split on common delimiters: &, feat., ft., x, ,
    df["artist_list"] = df["artist"].apply(split_artists)
    df["collaborator_count"] = df["artist_list"].apply(len)
    df["is_collaboration"] = df["collaborator_count"] > 1

    # ── 6. Explicit content flag ─────────────────────────────────────
    if "is_explicit" in df.columns:
        df["is_explicit"] = df["is_explicit"].astype(str).str.lower()
        df["is_explicit"] = df["is_explicit"].map(
            {"true": True, "false": False, "1": True, "0": False}
        ).fillna(False).astype(bool)
    else:
        df["is_explicit"] = False

    # ── 7. Duration engineering ──────────────────────────────────────
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce").fillna(0)
    df["duration_sec"] = (df["duration_ms"] / 1000).round(1)
    df["duration_min"] = (df["duration_ms"] / 60000).round(2)
    df["duration_bucket"] = pd.cut(
        df["duration_min"],
        bins=[0, 2, 3, 4, 5, 100],
        labels=["<2 min", "2–3 min", "3–4 min", "4–5 min", "5+ min"],
    )

    # ── 8. Popularity ────────────────────────────────────────────────
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0)
    df["popularity_bucket"] = pd.cut(
        df["popularity"],
        bins=[0, 40, 60, 75, 90, 101],
        labels=["Very Low", "Low", "Medium", "High", "Very High"],
    )

    # ── 9. Album type & track count ──────────────────────────────────
    if "album_type" in df.columns:
        df["album_type"] = df["album_type"].astype(str).str.strip().str.title()
    else:
        df["album_type"] = "Unknown"

    df["total_tracks"] = pd.to_numeric(
        df.get("total_tracks", 1), errors="coerce"
    ).fillna(1).astype(int)

    df["album_size_category"] = pd.cut(
        df["total_tracks"],
        bins=[0, 1, 6, 12, 20, 500],
        labels=["Single (1)", "EP (2–6)", "Standard (7–12)", "Deluxe (13–20)", "Extended (20+)"],
    )

    # ── 10. Rank groups ──────────────────────────────────────────────
    df["rank_group"] = pd.cut(
        df["position"],
        bins=[0, 10, 20, 30, 40, 50],
        labels=["Top 10", "Top 11–20", "Top 21–30", "Top 31–40", "Top 41–50"],
    )

    # ── 11. Song key ─────────────────────────────────────────────────
    df["song"] = df["song"].astype(str).str.strip()
    df["song_artist_key"] = df["song"].str.lower() + "||" + df["artist_normalized"]

    return df.reset_index(drop=True)


def split_artists(artist_str: str) -> list:
    """Parse artist string into individual artist list."""
    import re
    if not isinstance(artist_str, str):
        return ["Unknown"]
    # Normalize delimiters
    cleaned = re.sub(
        r"\bfeat\.?\b|\bft\.?\b|\bwith\b|\bvs\.?\b",
        "&",
        artist_str,
        flags=re.IGNORECASE,
    )
    parts = re.split(r"[&,x×]", cleaned)
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [artist_str]


def get_exploded_artists(df: pd.DataFrame) -> pd.DataFrame:
    """Return a row-per-artist exploded version of the dataframe."""
    exploded = df.copy()
    exploded = exploded.explode("artist_list").rename(
        columns={"artist_list": "individual_artist"}
    )
    exploded["individual_artist"] = exploded["individual_artist"].str.strip()
    return exploded


def filter_data(
    df: pd.DataFrame,
    date_range: tuple = None,
    selected_artists: list = None,
    collab_filter: str = "All",
    album_type_filter: list = None,
) -> pd.DataFrame:
    """Apply sidebar filters and return filtered DataFrame."""
    filtered = df.copy()

    if date_range:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered[filtered["date"].between(start, end)]

    if selected_artists:
        mask = filtered["artist_list"].apply(
            lambda lst: any(a in selected_artists for a in lst)
        )
        filtered = filtered[mask]

    if collab_filter == "Solo Only":
        filtered = filtered[~filtered["is_collaboration"]]
    elif collab_filter == "Collaborations Only":
        filtered = filtered[filtered["is_collaboration"]]

    if album_type_filter:
        filtered = filtered[filtered["album_type"].isin(album_type_filter)]

    return filtered