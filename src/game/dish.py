from collections import namedtuple
from enum import Enum, auto
from random import choice, randint, random, randrange
from sys import maxsize
from typing import NamedTuple, Optional

from nurses_2.colors import BLACK, RED, WHITE, ColorPair
from pydantic import BaseModel

from game.config import DISH_RERENDER_PERIOD

Food = namedtuple("Food", ["y", "x", "calories"])


def p(probability_out_of_100):
    return random() * 100 < probability_out_of_100


class Point(BaseModel):
    y: int
    x: int

    def __init__(self, y=None, x=None, **kwargs):
        if y is not None:
            kwargs["y"] = y
        if x is not None:
            kwargs["x"] = x
        super().__init__(**kwargs)

    def __add__(self, other):
        return Point(other.y + self.y, other.x + self.x)
    def __sub__(self, other):
        return Point(self.y - other.y, self.x - other.x)


class Organism(BaseModel):
    idx: Optional[int] = None
    dish: Optional["Dish"] = None
    pos: Point
    bounds: Point

    def move(self, direction: int):
        r"""Try to move in a direction. True if successful.
        :param direction: is given by classic numpad order:
                7 8 9
                 \|/
                4-5-6
                 /|\
                1 2 3
        """
        assert 0 < direction < 10
        # TODO: decide if diagonal movement is possible
        if direction in [1, 3, 7, 9]:
            return False
        if direction == 5:
            return True
        if direction == 2:
            self.pos.y += 1
        elif direction == 4:
            self.pos.x -= 1
        elif direction == 6:
            self.pos.x += 1
        elif direction == 8:
            self.pos.y -= 1

    def free_wander_think(self):
        """Called once every tick if free wandering is enabled."""
        if p(10):
            d = choice([2, 4, 6, 8])
            self.move(d)


class Dish(BaseModel):
    """The Dish manages the simulation of Organisms and provides the basic
    functionality required for the in-game Petri Dish."""

    organisms: dict[int, Organism] = {}
    food: list[Food] = []
    bounds: tuple[int, int] = (100, 600)

    def add_organism(self, organism: Organism) -> Organism:
        """Finish initializing an organism and add it to our dish."""
        new_idx = randint(0, maxsize)
        while new_idx in self.organisms:
            new_idx = randint(0, maxsize)
        organism.idx = new_idx
        organism.dish = self
        self.organisms[new_idx] = organism
        return organism

    def add_food(self, *args):
        """Add food to our dish."""
        self.food.append(Food(*args))
