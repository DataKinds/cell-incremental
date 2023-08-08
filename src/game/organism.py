from pydantic import BaseModel
from nurses_2.data_structures import Point # namedtuple[int, int]

class Organism(BaseModel):
    idx: int
    pos: Point
    bounds: Point
