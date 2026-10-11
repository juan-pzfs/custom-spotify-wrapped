from pathlib import Path
import pandas as pd

# 👇 Para cambiar a datos reales, solo cambia esta línea
CARPETA = Path("sample_data/Spotify Extended Streaming History")


def cargar_historial(carpeta):
    """Lee todos los archivos de historial de una carpeta y los junta en una tabla."""
    archivos = sorted(carpeta.glob("Streaming_History_Audio_*.json"))
    print(f"Leyendo: {carpeta} ({len(archivos)} archivos)")
    tablas = [pd.read_json(archivo) for archivo in archivos]
    return pd.concat(tablas, ignore_index=True)

def limpiar(df):
    """Deja solo música escuchada de verdad, con las columnas que necesitamos."""
    df = df[df["master_metadata_track_name"].notna()]   # quitar podcasts y audiolibros
    df = df[df["ms_played"] >= 30_000]                    # 30+ segundos = cuenta como "stream"
    df = df.rename(columns={
        "master_metadata_track_name": "cancion",
        "master_metadata_album_artist_name": "artista",
    })
    df = df[["ts", "ms_played", "cancion", "artista"]].copy()
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def filtrar_fechas(df, inicio, fin):
    """Deja solo las reproducciones entre dos fechas (ambas incluidas)."""
    inicio = pd.Timestamp(inicio, tz="UTC")
    fin = pd.Timestamp(fin, tz="UTC") + pd.Timedelta(days=1)
    return df[(df["ts"] >= inicio) & (df["ts"] < fin)]

def top_artistas(df, n=5):
    """Los n artistas con más horas escuchadas."""
    horas = df.groupby("artista")["ms_played"].sum() / 3_600_000
    return horas.sort_values(ascending=False).head(n).round(1)


def top_canciones(df, n=5):
    """Las n canciones más reproducidas. Artista + canción = llave única."""
    conteo = df.groupby(["artista", "cancion"]).size()
    return conteo.sort_values(ascending=False).head(n)

def artistas_nuevos(df, inicio, fin, minimo=10):
    """Artistas que escuchaste por PRIMERA VEZ en el periodo y que se quedaron (>= minimo)."""
    # 1. La primera vez que escuchaste a cada artista, en TODO el historial
    primeras = df.groupby("artista")["ts"].min().reset_index()

    # 2. ¿Cuáles de esas primeras veces cayeron dentro del periodo?
    primeras = filtrar_fechas(primeras, inicio, fin)

    # 3. Cuántas veces escuchaste a cada uno durante el periodo
    conteo = filtrar_fechas(df, inicio, fin)["artista"].value_counts()
    primeras["reproducciones"] = primeras["artista"].map(conteo)

    # 4. Solo los que de verdad entraron a tu rotación
    return primeras[primeras["reproducciones"] >= minimo].sort_values("ts")


if __name__ == "__main__":
    df = limpiar(cargar_historial(CARPETA))
    for inicio, fin in [("2026-01-01", "2026-03-31"),
                        ("2026-04-01", "2026-06-30"),
                        ("2026-07-01", "2026-09-30")]:
        print(f"--- Artistas nuevos {inicio} a {fin} ---")
        print(artistas_nuevos(df, inicio, fin))