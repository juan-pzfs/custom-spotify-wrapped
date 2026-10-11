import os
import json
from dotenv import load_dotenv
import anthropic
from pydantic import ValidationError
from summary import DATA_FOLDER, WARMUP_DAYS, load_history, clean, build_summary
from models import Wrapped

MODEL = "claude-haiku-5-5"
PRICE_INPUT = 0.10    # dollars per million input tokens
PRICE_OUTPUT = 0.50   # dollars per million output tokens
LANGUAGE = "Spanish"  # language for the Wrapped text (the JSON keys stay in English)
START, END = "2026-01-01", "2026-09-30"

# The structure Claude must follow (same fields as models.py)
JSON_FORMAT = """{
  "title": "short, fun headline",
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
- top_artists_by_month: top 3 artists per month. Use it to find musical phases.
- new_artists: artists played for the first time in the period. The first {WARMUP_DAYS}
  days of history are already excluded, so these are real discoveries.

Rules:
- Use ONLY the data in the summary. Don't invent artists, tracks or numbers.
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
        max_tokens=3000,
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

# 6. Show the Wrapped
print("🎧", wrapped.title)
print("\nPhases:")
for phase in wrapped.phases:
    artists = ", ".join(phase.key_artists)
    print(f"  - {phase.name} ({phase.start_month} to {phase.end_month}): {artists}")
print("\nPersonality:", wrapped.music_personality.label)