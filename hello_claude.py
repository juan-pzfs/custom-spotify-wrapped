from dotenv import load_dotenv
import anthropic

# Arriba del archivo, después de los imports
PRECIO_ENTRADA = 0.10   # dólares por millón de tokens de entrada
PRECIO_SALIDA = 0.50    # dólares por millón de tokens de salida

# 1. Cargar la API key desde el archivo .env
load_dotenv()

# 2. Crear el "cliente": la conexión con la API de Claude
cliente = anthropic.Anthropic()

# 3. Mandar el mensaje
respuesta = cliente.messages.create(
    model="claude-haiku-5-5",
    max_tokens=200,
    messages=[
        {"role": "user", "content": "Dime en una frase qué es un Spotify Wrapped."}
    ],
)

# 4. Leer la respuesta y el "ticket"
print(respuesta.content[0].text)
print("Tokens de entrada:", respuesta.usage.input_tokens)
print("Tokens de salida:", respuesta.usage.output_tokens)

# Al final
costo_entrada = respuesta.usage.input_tokens * PRECIO_ENTRADA / 1_000_000
costo_salida = respuesta.usage.output_tokens * PRECIO_SALIDA / 1_000_000
costo_total = costo_entrada + costo_salida
print(f"Costo: ${costo_total:.6f}")