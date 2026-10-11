from pathlib import Path
import pandas as pd
import json

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

def crear_resumen(df, inicio, fin, n=5):
    """Arma el resumen (pequeño) que le mandaremos a Claude."""
    periodo = filtrar_fechas(df, inicio, fin)
    artistas = top_artistas(periodo, n)
    canciones = top_canciones(periodo, n)

    # Top 3 artistas de cada mes → para que Claude vea las fases
    por_mes = {}
    for mes, grupo in periodo.groupby(periodo["ts"].dt.strftime("%Y-%m")):
        por_mes[mes] = list(top_artistas(grupo, 3).index)

    # Artistas nuevos, ignorando el periodo de calentamiento
    historial_desde = df["ts"].min()
    calentamiento = historial_desde + pd.Timedelta(days=90)
    nuevos = artistas_nuevos(df, inicio, fin)
    nuevos = nuevos[nuevos["ts"] >= calentamiento]

    return {
        "periodo": {"inicio": inicio, "fin": fin},
        "historial_desde": historial_desde.strftime("%Y-%m-%d"),
        "total_reproducciones": len(periodo),
        "horas_totales": round(periodo["ms_played"].sum() / 3_600_000, 1),
        "top_artistas": [
            {"artista": artista, "horas": float(horas)}
            for artista, horas in artistas.items()
        ],
        "top_canciones": [
            {"artista": artista, "cancion": cancion, "reproducciones": int(veces)}
            for (artista, cancion), veces in canciones.items()
        ],
        "top_artistas_por_mes": por_mes,
        "artistas_nuevos": [
            {"artista": artista, "primera_vez": fecha.strftime("%Y-%m-%d"),
             "reproducciones": int(veces)}
            for artista, fecha, veces in zip(nuevos["artista"], nuevos["ts"], nuevos["reproducciones"])
        ],
    }

if __name__ == "__main__":
    df = limpiar(cargar_historial(CARPETA))

    resumen = crear_resumen(df, "2026-01-01", "2026-09-30")
    texto = json.dumps(resumen, indent=2, ensure_ascii=False)
    print(texto)
    print("Caracteres del resumen:", len(texto))