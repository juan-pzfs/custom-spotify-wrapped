import pandas as pd

ruta = "sample_data/Spotify Extended Streaming History/Streaming_History_Audio_2026.json"
df = pd.read_json(ruta)

print("Filas y columnas:", df.shape)

# Convertir ts de texto a fecha real, y sacar el mes
df["ts"] = pd.to_datetime(df["ts"])
df["mes"] = df["ts"].dt.month

# Tabla: cuántas reproducciones por mes y artista
tabla = pd.crosstab(df["mes"], df["master_metadata_album_artist_name"])
print(tabla.to_string())