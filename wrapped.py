import json
from dotenv import load_dotenv
import anthropic
from resumen import CARPETA, cargar_historial, limpiar, crear_resumen

MODELO = "claude-haiku-5-5"
PRECIO_ENTRADA = 0.10   # dólares por millón de tokens
PRECIO_SALIDA = 0.50

SYSTEM_PROMPT = """Eres un analista musical con estilo divertido, como el Spotify Wrapped.
Recibes un resumen de escucha calculado con pandas.

Qué significa cada campo del resumen:
- historial_desde: fecha en que empiezan los datos. No afirmes nada sobre antes.
- top_artistas_por_mes: top 3 de cada mes. Úsalo para encontrar fases musicales.
- artistas_nuevos: artistas escuchados por primera vez en el periodo. Ya se excluyeron
  los primeros 90 días del historial, así que sí son descubrimientos reales.

Reglas:
- Usa SOLO los datos del resumen. No inventes artistas, canciones ni números.
- Responde en español.
- Responde ÚNICAMENTE con un objeto JSON válido, sin texto antes ni después
  y sin bloques de código (```). Usa exactamente esta estructura:

{
  "titulo": "frase corta y divertida",
  "fases": [
    {"nombre": "nombre creativo", "desde": "AAAA-MM", "hasta": "AAAA-MM",
     "artistas_clave": ["artista"], "descripcion": "1-2 frases"}
  ],
  "descubrimientos": [
    {"artista": "nombre", "comentario": "1 frase"}
  ],
  "personalidad_musical": {"tipo": "nombre creativo", "descripcion": "2-3 frases"},
  "dato_curioso": "1 frase basada en los números del resumen"
}"""

# 1. Preparar los datos (pandas)
df = limpiar(cargar_historial(CARPETA))
resumen = crear_resumen(df, "2026-01-01", "2026-09-30")

# 2. Llamar a Claude
load_dotenv()
cliente = anthropic.Anthropic()
respuesta = cliente.messages.create(
    model=MODELO,
    max_tokens=3000,
    system=SYSTEM_PROMPT,
    messages=[{
        "role": "user",
        "content": "Este es mi resumen de escucha. Escribe mi Wrapped.\n\n"
                   + json.dumps(resumen, ensure_ascii=False),
    }],
)

# 3. Resultado y costo
texto = "".join(bloque.text for bloque in respuesta.content if bloque.type == "text")
# Convertir el texto JSON en un diccionario de Python
wrapped = json.loads(texto)

print("🎧", wrapped["titulo"])
print("\nFases:")
for fase in wrapped["fases"]:
    artistas = ", ".join(fase["artistas_clave"])
    print(f"  - {fase['nombre']} ({fase['desde']} a {fase['hasta']}): {artistas}")
print("\nPersonalidad:", wrapped["personalidad_musical"]["tipo"])
if respuesta.stop_reason == "max_tokens":
    print("\n⚠️ La respuesta se cortó: se alcanzó max_tokens.")
uso = respuesta.usage
costo = (uso.input_tokens * PRECIO_ENTRADA + uso.output_tokens * PRECIO_SALIDA) / 1_000_000
print(f"\nTokens: {uso.input_tokens} entrada / {uso.output_tokens} salida | Costo: ${costo:.6f}")