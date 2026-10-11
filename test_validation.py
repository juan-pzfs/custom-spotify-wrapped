from pydantic import ValidationError
from models import Wrapped

# JSON roto a propósito:
#   1. artistas_clave es texto, no lista
#   2. falta personalidad_musical
json_roto = """{
  "titulo": "Prueba",
  "fases": [{"nombre": "Era Metal", "desde": "2026-04", "hasta": "2026-06",
             "artistas_clave": "BABYMETAL", "descripcion": "Mucho metal"}],
  "descubrimientos": [],
  "dato_curioso": "Nada"
}"""

try:
    Wrapped.model_validate_json(json_roto)
    print("✅ Válido")
except ValidationError as error:
    print("❌ El JSON no cumple el formulario:")
    print(error)