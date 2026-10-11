from pydantic import BaseModel


class Fase(BaseModel):
    nombre: str
    desde: str
    hasta: str
    artistas_clave: list[str]
    descripcion: str


class Descubrimiento(BaseModel):
    artista: str
    comentario: str


class Personalidad(BaseModel):
    tipo: str
    descripcion: str


class Wrapped(BaseModel):
    titulo: str
    fases: list[Fase]
    descubrimientos: list[Descubrimiento]
    personalidad_musical: Personalidad
    dato_curioso: str