import json
from dotenv import load_dotenv
import anthropic
from resumen import CARPETA, cargar_historial, limpiar, crear_resumen

MODELO = "claude-haiku-5-5"
PRECIO_ENTRADA = 0.10   # dólares por millón de tokens
PRECIO_SALIDA = 0.50

SYSTEM_PROMPT = """Eres un analista musical con estilo divertido, como el Spotify Wrapped.
Recibes un resumen de escucha calculado con pandas.

Reglas:
- Usa SOLO los datos del resumen. No inventes artistas, canciones ni números.
- "historial_desde" es cuando empiezan los datos: no afirmes nada sobre antes de esa fecha.
- Responde en español."""

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
print(texto)
if respuesta.stop_reason == "max_tokens":
    print("\n⚠️ La respuesta se cortó: se alcanzó max_tokens.")
uso = respuesta.usage
costo = (uso.input_tokens * PRECIO_ENTRADA + uso.output_tokens * PRECIO_SALIDA) / 1_000_000
print(f"\nTokens: {uso.input_tokens} entrada / {uso.output_tokens} salida | Costo: ${costo:.6f}")