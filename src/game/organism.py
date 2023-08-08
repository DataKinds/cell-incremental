from pydantic import BaseModel
from typing import Optional
from nurses_2.data_structures import Point # namedtuple[int, int]
import random

def p(probability_out_of_100):
    return random.random() * 100 < probability_out_of_100

class Organism(BaseModel):
    idx: Optional[int] = None
    pos: Point
    bounds: Point

    def __init__(self, dish: 'Dish', **kwargs):
        self().__init__(**kwargs)
        self.dish = dish

    def free_wander_think(self):
        """Called once every tick if free wandering is enabled."""
        if p(10):
            d = random.choice(['u', 'd', 'l', 'r'])
            if d == 'u':
                pos.y -= 1
            elif d == 'd':
                pos.y += 1
            elif d == 'l':
                pos.x -= 1
            elif d == 'r':
                pos.x += 1
        
