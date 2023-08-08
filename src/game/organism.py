from pydantic import BaseModel
from typing import Optional
from nurses_2.data_structures import Point # namedtuple[int, int]

class Organism(BaseModel):
    idx: Optional[int] = None
    pos: Point
    bounds: Point
