import os
import json
from dotenv import load_dotenv
import anthropic
from pydantic import ValidationError
from summary import (DATA_FOLDER, WARMUP_DAYS, load_history, clean,
                     build_summary, filter_dates, top_tracks)
from models import Wrapped

MODEL = "claude-haiku-5-5"
PRICE_INPUT = 0.10    # dollars per million input tokens
PRICE_OUTPUT = 0.50   # dollars per million output tokens
LANGUAGE = "Spanish"  # language for the Wrapped text (the JSON keys stay in English)
START, END = "2026-01-01", "2026-10-11"
TOP_TRACKS_TO_SHOW = 20   # only displayed, NOT sent to Claude

# Labels printed by our code, in each language
LABELS = {
    "Spanish": {
        "minutes": "Minutos escuchados", "days": "días con música", "avg": "min/día en promedio",
        "top": "Top 10 artistas (% de tu tiempo)", "tracks": "Top 20 canciones",
        "number_one": "Tu canción #1", "plays": "reproducciones", "first": "primera vez",
        "since_start": "desde que empiezan tus datos",
        "obsession": "Tu día obsesión", "record": "Tu día récord", "variety": "Variedad",
        "artists": "artistas", "songs": "canciones distintas",
        "time": "¿Cuándo escuchas?", "peak": "Tu hora pico",
        "parts": ["Madrugada (0-6h)", "Mañana (6-12h)", "Tarde (12-18h)", "Noche (18-24h)"],
        "phases": "Tus fases", "discoveries": "Descubrimientos",
        "personality": "Personalidad", "fun_fact": "Dato curioso",
    },
    "English": {
        "minutes": "Minutes listened", "days": "days with music", "avg": "min/day on average",
        "top": "Top 10 artists (% of your time)", "tracks": "Top 20 tracks",
        "number_one": "Your #1 track", "plays": "plays", "first": "first played",
        "since_start": "since your data begins",
        "obsession": "Your obsession day", "record": "Your record day", "variety": "Variety",
        "artists": "artists", "songs": "different tracks",
        "time": "When do you listen?", "peak": "Your peak hour",
        "parts": ["Late night (0-6h)", "Morning (6-12h)", "Afternoon (12-18h)", "Evening (18-24h)"],
        "phases": "Your phases", "discoveries": "Discoveries",
        "personality": "Personality", "fun_fact": "Fun fact",
    },
}
L = LABELS[LANGUAGE]

# The structure Claude must follow (same fields as models.py)
JSON_FORMAT = """{
  "title": "short, fun headline",
  "card_comments": {
    "minutes": "1 fun sentence about the total minutes",
    "number_one_track": "1 fun sentence about the #1 track",
    "obsession_day": "1 fun sentence about the obsession day",
    "record_day": "1 fun sentence about the record day",
    "time_of_day": "1 fun sentence about when they listen"
  },
  "phases": [
    {"name": "creative name", "start_month": "YYYY-MM", "end_month": "YYYY-MM",
     "key_artists": ["artist"], "description": "1-2 sentences"}
  ],
  "discoveries": [
    {"artist": "name", "comment": "1 sentence"}
  ],
  "music_personality": {"label": "creative name", "description": "2-3 sentences"},
  "fun_fact": "1 sentence based on the numbers in the summary"
}"""

SYSTEM_PROMPT = f"""You are a music analyst with a fun style, like Spotify Wrapped.
You receive a listening summary computed with pandas.

What each summary field means:
- history_start: the date the data begins. Don't claim anything about before it.
- stats: total minutes, days with music, average minutes per listening day,
  record_day (the day with the most minutes), number of different artists and tracks.
- top_artists: hours and share_pct (% of total listening time in the period).
- number_one_track: the most-played track in the period. If first_played_during_warmup
  is true, the real first play may be earlier than the data: say "since your data
  begins", never "the first time you heard it".
- obsession_day: the single track repeated the most times in one day.
- time_of_day: share of listening time per part of the day, in the user's local time.
  peak_hour is 0-23.
- top_artists_by_month: top 3 artists per month. Use it to find musical phases.
- new_artists: artists played for the first time in the period. The first {WARMUP_DAYS}
  days of history are already excluded, so these are real discoveries.

Rules:
- Use ONLY the data in the summary. Don't invent artists, tracks or numbers.
- Only call an artist "new" or "discovered" if it is in new_artists. An artist
  entering the monthly top is NOT a discovery.
- Write all text values in {LANGUAGE}. Keep the JSON keys exactly as shown, in English.
- Reply ONLY with a valid JSON object: no text before or after, no code fences (```).
  Use exactly this structure:

""" + JSON_FORMAT

# 1. Prepare the data (pandas)
try:
    df = clean(load_history(DATA_FOLDER))
except FileNotFoundError as error:
    print(f"❌ {error}")
    raise SystemExit(1)
summary = build_summary(df, START, END)

# 2. Call Claude
load_dotenv()

# Fail early if there's no API key at all
if not os.getenv("ANTHROPIC_API_KEY"):
    print("❌ No API key found. Create a .env file with ANTHROPIC_API_KEY=your-key")
    raise SystemExit(1)

client = anthropic.Anthropic()
try:
    response = client.messages.create(
        model=MODEL,
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": "Here is my listening summary. Write my Wrapped.\n\n"
                       + json.dumps(summary, ensure_ascii=False),
        }],
    )
except anthropic.AuthenticationError:
    print("❌ Invalid API key. Check ANTHROPIC_API_KEY in your .env (it may have expired).")
    raise SystemExit(1)
except anthropic.APIConnectionError:
    print("❌ Couldn't reach the Claude API. Check your internet connection and try again.")
    raise SystemExit(1)
except anthropic.APIStatusError as error:
    print(f"❌ The Claude API returned an error ({error.status_code}): {error.message}")
    raise SystemExit(1)

# 3. Get the text out of the response
text = "".join(block.text for block in response.content if block.type == "text")

# 4. Check for truncation and cost (always, even if validation fails)
if response.stop_reason == "max_tokens":
    print("\n⚠️ The response was cut off: max_tokens reached.")
usage = response.usage
cost = (usage.input_tokens * PRICE_INPUT + usage.output_tokens * PRICE_OUTPUT) / 1_000_000
print(f"Tokens: {usage.input_tokens} input / {usage.output_tokens} output | Cost: ${cost:.6f}\n")

# 5. Validate the response against the form
try:
    wrapped = Wrapped.model_validate_json(text)
except ValidationError as error:
    print("❌ Claude's response does not match the form:")
    print(error)
    print("\nClaude's raw response:\n", text)
    raise SystemExit(1)

# 6. Show the Wrapped: numbers from pandas, comments from Claude
stats = summary["stats"]
number_one = summary["number_one_track"]
obsession = summary["obsession_day"]
record = stats["record_day"]
time_of_day = summary["time_of_day"]
comments = wrapped.card_comments

print("🎧", wrapped.title)

print(f"\n🕒 {L['minutes']}: {stats['total_minutes']:,}")
print(f"   {stats['days_with_music']} {L['days']} · {stats['avg_minutes_per_listening_day']} {L['avg']}")
print(f"   {comments.minutes}")

print(f"\n🎤 {L['top']}")
for rank, item in enumerate(summary["top_artists"], start=1):
    bar = "█" * round(item["share_pct"])
    print(f"  {rank:>2}. {item['artist']:<22} {item['share_pct']:>5.1f}%  {bar}")

print(f"\n🎵 {L['tracks']}")
period = filter_dates(df, START, END)
for rank, ((artist, track), plays) in enumerate(top_tracks(period, TOP_TRACKS_TO_SHOW).items(), start=1):
    print(f"  {rank:>2}. {track} — {artist} ({plays})")

first_label = L["since_start"] if number_one["first_played_during_warmup"] else f"{L['first']}: {number_one['first_played']}"
print(f"\n🥇 {L['number_one']}: {number_one['track']} — {number_one['artist']}")
print(f"   {number_one['plays']} {L['plays']} · {first_label}")
print(f"   {comments.number_one_track}")

print(f"\n🔁 {L['obsession']}: {obsession['date']}")
print(f"   {obsession['track']} — {obsession['artist']} × {obsession['plays']}")
print(f"   {comments.obsession_day}")

print(f"\n📅 {L['record']}: {record['date']} · {record['minutes']} min")
print(f"   {comments.record_day}")

print(f"\n🌈 {L['variety']}: {stats['unique_artists']:,} {L['artists']} · {stats['unique_tracks']:,} {L['songs']}")

print(f"\n🌙 {L['time']}")
for part, pct in zip(L["parts"], time_of_day["share_pct"].values()):
    print(f"  {part:<20} {pct:>5.1f}%  {'█' * round(pct / 2)}")
print(f"  {L['peak']}: {time_of_day['peak_hour']}:00")
print(f"  {comments.time_of_day}")

print(f"\n🔄 {L['phases']}:")
for phase in wrapped.phases:
    artists = ", ".join(phase.key_artists)
    print(f"  - {phase.name} ({phase.start_month} → {phase.end_month}): {artists}")
    print(f"      {phase.description}")

print(f"\n✨ {L['discoveries']}:")
for discovery in wrapped.discoveries:
    print(f"  - {discovery.artist}: {discovery.comment}")

print(f"\n🧠 {L['personality']}: {wrapped.music_personality.label}")
print(f"   {wrapped.music_personality.description}")

print(f"\n💡 {L['fun_fact']}: {wrapped.fun_fact}")