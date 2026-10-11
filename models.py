from pydantic import BaseModel


class Phase(BaseModel):
    name: str
    start_month: str
    end_month: str
    key_artists: list[str]
    description: str


class Discovery(BaseModel):
    artist: str
    comment: str


class Personality(BaseModel):
    label: str
    description: str


class Wrapped(BaseModel):
    title: str
    phases: list[Phase]
    discoveries: list[Discovery]
    music_personality: Personality
    fun_fact: str