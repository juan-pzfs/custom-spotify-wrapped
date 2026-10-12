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

class CardComments(BaseModel):
    minutes: str
    number_one_track: str
    obsession_day: str
    record_day: str
    time_of_day: str  

class Wrapped(BaseModel):
    title: str
    phases: list[Phase]
    discoveries: list[Discovery]
    music_personality: Personality
    fun_fact: str
    card_comments: CardComments