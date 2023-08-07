from pydantic import BaseModel


class Organism(BaseModel):
    idx: int
    pos: tuple[int, int]
    bounds: tuple[int, int]
