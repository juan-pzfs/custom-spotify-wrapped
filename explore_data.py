import pandas as pd

path = "sample_data/Spotify Extended Streaming History/Streaming_History_Audio_2026.json"
df = pd.read_json(path)

print("Rows and columns:", df.shape)

# Convert ts from text to a real date, and extract the month
df["ts"] = pd.to_datetime(df["ts"])
df["month"] = df["ts"].dt.month

# Table: plays per month and artist
table = pd.crosstab(df["month"], df["master_metadata_album_artist_name"])
print(table.to_string())