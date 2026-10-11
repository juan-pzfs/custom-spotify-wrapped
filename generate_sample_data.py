import json
import random                                         # pick things at random
from datetime import datetime, timezone, timedelta    # dates, times and durations
from pathlib import Path

# Fake music catalog: each artist has songs with their album
# Structure: {artist: [(song, album), (song, album), ...]}
CATALOG = {
    "Bad Bunny": [
        ("Tití Me Preguntó", "Un Verano Sin Ti"),
        ("Me Porto Bonito", "Un Verano Sin Ti"),
        ("DtMF", "DeBÍ TiRAR MáS FOToS"),
        ("Safaera", "YHLQMDLG"),
    ],
    "Post Malone": [
        ("Circles", "Hollywood's Bleeding"),
        ("Sunflower", "Hollywood's Bleeding"),
        ("rockstar", "beerbongs & bentleys"),
        ("I Had Some Help", "F-1 Trillion"),
    ],
    "BABYMETAL": [
        ("Gimme Chocolate!!", "BABYMETAL"),
        ("Megitsune", "BABYMETAL"),
        ("KARATE", "METAL RESISTANCE"),
        ("PA PA YA!!", "METAL GALAXY"),
    ],
    "The Warning": [
        ("CHOKE", "ERROR"),
        ("EVOLVE", "ERROR"),
        ("Qué Más Quieres", "ERROR"),
        ("MORE", "MAYDAY"),
    ],
    "Rex Orange County": [
        ("Loving Is Easy", "Loving Is Easy"),
        ("Best Friend", "Bcos U Will Never B Free"),
        ("Pluto Projector", "Pony"),
        ("Sunflower", "Bcos U Will Never B Free"),
    ],
}

# Each phase: which months it covers and how likely each artist is (weights)
PHASES = [
    {"months": [1, 2, 3],
     "weights": {"Bad Bunny": 60, "Post Malone": 30, "Rex Orange County": 10}},
    {"months": [4, 5, 6],
     "weights": {"BABYMETAL": 40, "The Warning": 30, "Bad Bunny": 20, "Post Malone": 10}},
    {"months": [7, 8, 9],
     "weights": {"Rex Orange County": 50, "Post Malone": 25, "The Warning": 15, "Bad Bunny": 10}},
]


def pick_artist(month):
    """Pick an artist based on the phase for that month."""
    for phase in PHASES:
        if month in phase["months"]:
            artists = list(phase["weights"].keys())
            weights = list(phase["weights"].values())
            return random.choices(artists, weights=weights)[0]
    # If the month isn't in any phase, any artist with equal probability
    return random.choice(list(CATALOG.keys()))


def create_play(when, artist):
    """Create one fake record with the same shape as Spotify's."""
    song, album = random.choice(CATALOG[artist])

    # 15% chance the song gets skipped
    skipped = random.random() < 0.15
    if skipped:
        ms = random.randint(5_000, 30_000)      # 5 to 30 seconds
    else:
        ms = random.randint(150_000, 240_000)   # 2.5 to 4 minutes

    return {
        "ts": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": random.choice(["android", "windows", "web_player"]),
        "ms_played": ms,
        "conn_country": "US",
        "ip_addr": "0.0.0.0",                   # fake on purpose
        "master_metadata_track_name": song,
        "master_metadata_album_artist_name": artist,
        "master_metadata_album_album_name": album,
        "spotify_track_uri": f"spotify:track:fake_{artist}_{song}",
        "episode_name": None,
        "episode_show_name": None,
        "spotify_episode_uri": None,
        "audiobook_title": None,
        "audiobook_uri": None,
        "audiobook_chapter_uri": None,
        "audiobook_chapter_title": None,
        "reason_start": "trackdone",
        "reason_end": "fwdbtn" if skipped else "trackdone",
        "shuffle": random.random() < 0.5,
        "skipped": skipped,
        "offline": False,
        "offline_timestamp": None,
        "incognito_mode": False,
    }


def generate_history(start, end, per_day=30):
    """Generate fake plays for every day between start and end."""
    records = []
    day = start
    while day <= end:
        # Each day you listen to between 20 and 40 songs
        for _ in range(random.randint(per_day - 10, per_day + 10)):
            moment = day + timedelta(
                hours=random.randint(7, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            artist = pick_artist(day.month)
            records.append(create_play(moment, artist))
        day += timedelta(days=1)
    # Sort by date, like the real file
    records.sort(key=lambda r: r["ts"])
    return records


def save(records, path):
    """Save the list as a UTF-8 JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    random.seed(42)  # same "luck" every time → same fake data

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 30, tzinfo=timezone.utc)
    history = generate_history(start, end)

    path = Path("sample_data/Spotify Extended Streaming History/Streaming_History_Audio_2026.json")
    save(history, path)
    print(f"Done: {len(history)} plays saved to {path}")