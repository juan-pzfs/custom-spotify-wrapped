import random                              # para elegir cosas al azar
from datetime import datetime, timezone    # para manejar fechas y horas
import json
from collections import Counter   # cuenta cuántas veces aparece cada cosa
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Catálogo de música falsa: cada artista tiene canciones con su álbum
# Estructura: {artista: [(canción, álbum), (canción, álbum), ...]}
CATALOGO = {
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

# Cada fase: qué meses abarca y qué tan probable es cada artista (pesos)
FASES = [
    {"meses": [1, 2, 3],
     "pesos": {"Bad Bunny": 60, "Post Malone": 30, "Rex Orange County": 10}},
    {"meses": [4, 5, 6],
     "pesos": {"BABYMETAL": 40, "The Warning": 30, "Bad Bunny": 20, "Post Malone": 10}},
    {"meses": [7, 8, 9],
     "pesos": {"Rex Orange County": 50, "Post Malone": 25, "The Warning": 15, "Bad Bunny": 10}},
]

def elegir_artista(mes):
    """Elige un artista según la fase del mes."""
    for fase in FASES:
        if mes in fase["meses"]:
            artistas = list(fase["pesos"].keys())
            pesos = list(fase["pesos"].values())
            return random.choices(artistas, weights=pesos)[0]
    # Si el mes no está en ninguna fase, cualquier artista con igual probabilidad
    return random.choice(list(CATALOGO.keys()))



def crear_reproduccion(fecha, artista):
    """Crea un registro falso con la misma forma que el de Spotify."""
    cancion, album = random.choice(CATALOGO[artista])

    # 15% de probabilidad de que la canción se salte
    saltada = random.random() < 0.15
    if saltada:
        ms = random.randint(5_000, 30_000)      # 5 a 30 segundos
    else:
        ms = random.randint(150_000, 240_000)   # 2.5 a 4 minutos

    return {
        "ts": fecha.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": random.choice(["android", "windows", "web_player"]),
        "ms_played": ms,
        "conn_country": "US",
        "ip_addr": "0.0.0.0",                   # falsa a propósito
        "master_metadata_track_name": cancion,
        "master_metadata_album_artist_name": artista,
        "master_metadata_album_album_name": album,
        "spotify_track_uri": f"spotify:track:fake_{artista}_{cancion}",
        "episode_name": None,
        "episode_show_name": None,
        "spotify_episode_uri": None,
        "audiobook_title": None,
        "audiobook_uri": None,
        "audiobook_chapter_uri": None,
        "audiobook_chapter_title": None,
        "reason_start": "trackdone",
        "reason_end": "fwdbtn" if saltada else "trackdone",
        "shuffle": random.random() < 0.5,
        "skipped": saltada,
        "offline": False,
        "offline_timestamp": None,
        "incognito_mode": False,
    }

def generar_historial(inicio, fin, por_dia=30):
    """Genera reproducciones falsas para cada día entre inicio y fin."""
    registros = []
    dia = inicio
    while dia <= fin:
        # Cada día escuchas entre 20 y 40 canciones
        for _ in range(random.randint(por_dia - 10, por_dia + 10)):
            momento = dia + timedelta(
                hours=random.randint(7, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            artista = elegir_artista(dia.month)
            registros.append(crear_reproduccion(momento, artista))
        dia += timedelta(days=1)
    # Ordenar por fecha, como el archivo real
    registros.sort(key=lambda r: r["ts"])
    return registros

def guardar(registros, ruta):
    """Guarda la lista como archivo JSON en UTF-8."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    random.seed(42)  # misma "suerte" cada vez → mismos datos falsos

    inicio = datetime(2026, 1, 1, tzinfo=timezone.utc)
    fin = datetime(2026, 9, 30, tzinfo=timezone.utc)
    historial = generar_historial(inicio, fin)

    ruta = Path("sample_data/Spotify Extended Streaming History/Streaming_History_Audio_2026.json")
    guardar(historial, ruta)
    print(f"Listo: {len(historial)} reproducciones guardadas en {ruta}")