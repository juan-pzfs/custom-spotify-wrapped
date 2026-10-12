import os
import json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Data folder: set SPOTIFY_DATA_FOLDER in .env to use your real data;
# otherwise it uses the public sample data
DATA_FOLDER = Path(os.getenv("SPOTIFY_DATA_FOLDER", "sample_data/Spotify Extended Streaming History"))

# Time zone for dates and hours (set TIMEZONE in .env, e.g. America/Chicago)
TIMEZONE = os.getenv("TIMEZONE", "UTC")

WARMUP_DAYS = 90       # first days of history that don't count as "discoveries"
MAX_NEW_ARTISTS = 10   # how many new artists to send to Claude (the most played)
TOP_ARTISTS = 10       # how many artists in the top list
TOP_TRACKS = 5         # how many tracks in the top list


def load_history(folder):
    """Read every history file in a folder and combine them into one table."""
    files = sorted(folder.glob("Streaming_History_Audio_*.json"))
    print(f"Reading: {folder} ({len(files)} files)")
    if not files:
        raise FileNotFoundError(
            f"No Streaming_History_Audio_*.json files found in '{folder}'. "
            "Check that DATA_FOLDER points to the right folder."
        )
    tables = [pd.read_json(file) for file in files]
    return pd.concat(tables, ignore_index=True)


def clean(df):
    """Keep only music you actually listened to, with the columns we need."""
    df = df[df["master_metadata_track_name"].notna()]   # drop podcasts and audiobooks
    df = df[df["ms_played"] >= 30_000]                    # 30+ seconds counts as a "stream"
    df = df.rename(columns={
        "master_metadata_track_name": "track",
        "master_metadata_album_artist_name": "artist",
    })
    df = df[["ts", "ms_played", "track", "artist"]].copy()
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_convert(TIMEZONE)
    return df


def filter_dates(df, start, end):
    """Keep only plays between two dates (both included)."""
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE) + pd.Timedelta(days=1)
    return df[(df["ts"] >= start) & (df["ts"] < end)]


def top_artists(df, n=5):
    """The n artists with the most hours listened."""
    hours = df.groupby("artist")["ms_played"].sum() / 3_600_000
    return hours.sort_values(ascending=False).head(n).round(1)


def top_tracks(df, n=5):
    """The n most-played tracks. Artist + track = unique key."""
    counts = df.groupby(["artist", "track"]).size()
    return counts.sort_values(ascending=False, kind="stable").head(n)



def new_artists(df, start, end, min_plays=10):
    """Artists you heard for the FIRST time in the period and who stuck around (>= min_plays)."""
    # 1. The first time you played each artist, across your WHOLE history
    firsts = df.groupby("artist")["ts"].min().reset_index()

    # 2. Which of those first plays fall inside the period?
    firsts = filter_dates(firsts, start, end)

    # 3. How many times you played each one during the period
    counts = filter_dates(df, start, end)["artist"].value_counts()
    firsts["plays"] = firsts["artist"].map(counts)

    # 4. Only the ones that really entered your rotation
    return firsts[firsts["plays"] >= min_plays].sort_values("ts")

def first_play(df, artist, track):
    """When you played a specific track for the very first time (whole history)."""
    is_track = (df["artist"] == artist) & (df["track"] == track)
    return df.loc[is_track, "ts"].min()


def obsession_day(period):
    """The track you repeated the most in a single day."""
    counts = period.groupby([period["ts"].dt.date, "artist", "track"]).size()
    date, artist, track = counts.idxmax()
    return {"date": date.strftime("%Y-%m-%d"), "artist": artist,
            "track": track, "plays": int(counts.max())}

def time_of_day(period):
    """Share of listening time in each part of the day (local time), plus the peak hour."""
    hour = period["ts"].dt.hour
    part = pd.cut(hour, bins=[0, 6, 12, 18, 24], right=False,
                  labels=["night (0-6h)", "morning (6-12h)",
                          "afternoon (12-18h)", "evening (18-24h)"])
    minutes = period.groupby(part, observed=False)["ms_played"].sum()
    shares = (minutes / minutes.sum() * 100).round(1)

    return {
        "share_pct": {label: float(value) for label, value in shares.items()},
        "peak_hour": int(period.groupby(hour)["ms_played"].sum().idxmax()),
    }

def listening_stats(period):
    """Totals, daily average, record day and variety for the period."""
    # Minutes listened on each calendar day (local time)
    minutes_per_day = period.groupby(period["ts"].dt.date)["ms_played"].sum() / 60_000
    total_minutes = minutes_per_day.sum()
    record_day = minutes_per_day.idxmax()

    return {
        "total_minutes": int(round(total_minutes)),
        "days_with_music": len(minutes_per_day),
        "avg_minutes_per_listening_day": int(round(total_minutes / len(minutes_per_day))),
        "record_day": {"date": record_day.strftime("%Y-%m-%d"),
                       "minutes": int(round(minutes_per_day.max()))},
        "unique_artists": int(period["artist"].nunique()),
        "unique_tracks": len(period[["artist", "track"]].drop_duplicates()),
    }

def build_summary(df, start, end):
    """Build the (small) summary we will send to Claude."""
    period = filter_dates(df, start, end)
    total_hours = period["ms_played"].sum() / 3_600_000
    artists = top_artists(period, TOP_ARTISTS)
    tracks = top_tracks(period, TOP_TRACKS)

    # Top 3 artists per month → so Claude can see the phases
    by_month = {}
    for month, group in period.groupby(period["ts"].dt.strftime("%Y-%m")):
        by_month[month] = list(top_artists(group, 3).index)

    # New artists, ignoring the warm-up period, keeping only the most played
    history_start = df["ts"].min()
    warmup_end = history_start + pd.Timedelta(days=WARMUP_DAYS)
    new = new_artists(df, start, end)
    new = new[new["ts"] >= warmup_end]
    new = new.nlargest(MAX_NEW_ARTISTS, "plays").sort_values("ts")
    # When you first played your #1 track (across your whole history)
    first_played = first_play(df, *tracks.index[0])

    return {
        "period": {"start": start, "end": end},
        "history_start": history_start.strftime("%Y-%m-%d"),
        "total_plays": len(period),
        "total_hours": round(total_hours, 1),
        "stats": listening_stats(period),
        "time_of_day": time_of_day(period),
        "top_artists": [
            {"artist": artist, "hours": float(hours),
             "share_pct": round(hours / total_hours * 100, 1)}
            for artist, hours in artists.items()
        ],
        "top_tracks": [
            {"artist": artist, "track": track, "plays": int(plays)}
            for (artist, track), plays in tracks.items()
        ],
        "number_one_track": {
            "artist": tracks.index[0][0],
            "track": tracks.index[0][1],
            "plays": int(tracks.iloc[0]),
            "first_played": first_played.strftime("%Y-%m-%d"),
            "first_played_during_warmup": bool(first_played < warmup_end),
        },
        "obsession_day": obsession_day(period),        
        "top_artists_by_month": by_month,
        "new_artists": [
            {"artist": artist, "first_played": date.strftime("%Y-%m-%d"), "plays": int(plays)}
            for artist, date, plays in zip(new["artist"], new["ts"], new["plays"])
        ],
    }


if __name__ == "__main__":
    df = clean(load_history(DATA_FOLDER))
    print(df["ts"].head(3))

    summary = build_summary(df, "2017-01-01", "2026-12-31")
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print("Months:", len(summary["top_artists_by_month"]))
    print("New artists:", len(summary["new_artists"]))
    print("Top artists:", len(summary["top_artists"]))
    print("Summary characters:", len(text))
    for key in ["stats", "number_one_track", "obsession_day", "time_of_day"]:
        print(key, json.dumps(summary[key], indent=2, ensure_ascii=False))