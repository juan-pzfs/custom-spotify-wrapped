# 🎧 Custom Spotify Wrapped

Your own Spotify Wrapped, any time of the year, from your real listening history.

**pandas** crunches the numbers from Spotify's *Extended Streaming History* export, and **Claude** (via the Anthropic API) turns them into a Wrapped: musical phases, discoveries, a listening personality and a fun comment for every card. The output is **validated JSON**, so the code always knows exactly what it got back.

> Built as Level 1 of my personal "AI agents school": a single, well-controlled API call. Prompts, tokens and cost, structured JSON output, validation and error handling.

---

## What you get

| Card | Computed by |
|---|---|
| 🕒 Minutes listened, days with music, daily average | pandas |
| 🎤 Top 10 artists with % of your listening time | pandas |
| 🎵 Top 20 tracks | pandas |
| 🥇 Your #1 track and when you first played it | pandas + Claude comment |
| 🔁 Obsession day: the track you repeated the most in one day | pandas + Claude comment |
| 📅 Record day: the day you listened the most | pandas + Claude comment |
| 🌈 Variety: different artists and tracks | pandas |
| 🌙 When you listen: share by part of the day + peak hour | pandas + Claude comment |
| 🔄 Your musical phases, month by month | Claude |
| ✨ Real discoveries (artists new to you in the period) | pandas + Claude comment |
| 🧠 Your listening personality | Claude |

---

## How it works

```
Spotify JSON files ──► pandas: load, clean, summarize ──► small summary (~1-4k tokens)
                                                                   │
                                                                   ▼
          your terminal ◄── validated Wrapped ◄── Pydantic ◄── Claude (JSON)
```

**Key design rule: pandas calculates, Claude interprets.**
Every number you see comes from pandas, never from the model. Claude only adds what pandas can't: names for your phases, a personality, and the comments.

---

## Privacy by design

- Your real data lives in `data/`, which is in `.gitignore` and never leaves your computer.
- Claude never sees the raw files. It only gets a small summary: artists, tracks, counts and dates. IP address, country and device are dropped during cleaning.
- API keys live in `.env`, which is also in `.gitignore`.

---

## Setup

Requires Python 3.13+ and an [Anthropic API key](https://console.anthropic.com/).

```bash
git clone https://github.com/juan-pzfs/custom-spotify-wrapped.git
cd custom-spotify-wrapped
python -m venv .venv
# Windows:  .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in:

```
ANTHROPIC_API_KEY=your-key-here
# Optional: your real data (otherwise the sample data is used)
SPOTIFY_DATA_FOLDER=data/Spotify Extended Streaming History
# Optional: your time zone (otherwise UTC)
TIMEZONE=America/Chicago
```

## Run it

```bash
python wrapped.py
```

No Spotify data yet? It runs out of the box on the **sample data** in `sample_data/`.

To use your own: request your **Extended streaming history** at Spotify → Account → Privacy settings (it can take up to 30 days), unzip it into `data/` and set `SPOTIFY_DATA_FOLDER` in `.env`.

Change the period, language or model at the top of `wrapped.py`:

```python
LANGUAGE = "Spanish"            # or "English"
START, END = "2026-01-01", "2026-10-11"
```

---

## Cost

Uses **Claude Haiku 5.5** ($0.10 per million input tokens / $0.50 per million output tokens at the time of writing).

| Run | Input tokens | Output tokens | Cost |
|---|---|---|---|
| Sample data (9 months) | ~1.2k | ~1.4k | ~$0.001 |
| Real data, full history (~10 years) | ~4.8k | ~3k | ~$0.002 |

How cost is kept under control:
- Only a **summary** is sent, never the raw history. 400k plays would be ~60M tokens; the summary is ~4k.
- **Signal over noise:** only the top 10 new artists go to Claude; the top 20 tracks are shown but not sent.
- `max_tokens` caps every response, and the script warns if a response was cut off.
- Every run prints its token usage and cost.
- A monthly spend limit and no auto-reload are set in the Anthropic Console.

---

## Reliability

- **Validated output:** Claude's JSON is checked against Pydantic models (`models.py`). Missing fields or wrong types are caught with a clear message and the raw response is shown, instead of crashing later with bad data.
- **Clear errors:** missing or invalid API key, no internet connection, API errors (e.g. out of credits) and a wrong data folder each get a human-readable message. The script fails early, before spending money.
- **Honest data:**
  - *Warm-up period:* the first 90 days of history don't count as "discoveries", because there is nothing earlier to compare against.
  - If your #1 track was first played during that warm-up, the Wrapped says "since your data begins" instead of inventing a first-play date.
  - Ties in the top tracks are broken alphabetically, so results are reproducible.
  - Dates and hours are converted to your time zone, including daylight saving time.
- **Controlled experiment:** `generate_sample_data.py` creates fake data with **hidden phases** (reggaeton → metal → chill) and a fixed random seed. Every feature was tested on it first, where the right answer is known, before trusting it with real data.

---

## Project structure

| File | What it does |
|---|---|
| `wrapped.py` | Main script: prompt, API call, validation, display |
| `summary.py` | pandas: load, clean and summarize the history |
| `models.py` | Pydantic models: the "form" Claude's JSON must match |
| `generate_sample_data.py` | Creates the fake data with hidden phases |
| `test_validation.py` | Checks that validation rejects broken JSON and accepts valid JSON |
| `hello_claude.py` | First API call: tokens and cost |
| `explore_data.py` | Quick first look at the data |

---

## Limitations

- Spotify's export has no genres or release years, so there's no "top genres" or "listening age" card.
- No comparison with other listeners (that needs everyone's data).
- The time zone is a single setting: if you traveled, those hours are shown in your home time zone.
- Claude's comments change on every run; the numbers don't.

## Ideas for later

Interactive dashboard · live updates with the Spotify API · custom timelines ("what did I listen to in summer 2019?") · top podcasts · most-skipped artists.

---

## 🇲🇽 En español

Tu propio Spotify Wrapped, en cualquier momento del año. pandas calcula los números a partir de tu historial de Spotify, y Claude los convierte en un Wrapped con fases musicales, descubrimientos y personalidad, en JSON validado. Tus datos reales nunca salen de tu computadora: a Claude solo le llega un resumen. Funciona con datos de ejemplo sin configurar nada más que la API key.

---

*Not affiliated with Spotify. Personal learning project.*
