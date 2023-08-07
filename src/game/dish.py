from pydantic import BaseModel
from sys import maxsize
from random import randint
import numpy as np
from nurses_2.widgets.text_field import TextParticleField
import asyncio

from .config import DISH_RERENDER_PERIOD
from .organism import Organism


class Dish(BaseModel):
    """The Dish manages the simulation of Organisms and provides the basic
    functionality required for the in-game Petri Dish."""

    organisms: dict[int, Organism] = []
    bounds: tuple[int, int] = (100, 600)

    def add_organism(self, organism):
        """Finish initializing an organism and add it to our dish."""
        new_idx = randint(0, maxsize)
        while new_idx in self.organisms:
            new_idx = randint(0, maxsize)
        organism.idx = new_idx
        self.organisms[new_idx] = organism

    # These three functions are for converting the Dish into a nurses_2 TextParticleField
    def get_particle_positions(self):
        return np.array([[0,0], [1,1], [2,2]]) 
    def get_particle_chars(self):
        return np.array(['@', '@', '@']) 
    def render_onto_textparticlefield(self, tpf: TextParticleField):
        tpf.particle_positions = self.get_particle_positions()
        tpf.particle_chars = self.get_particle_chars()


class DishWidget(TextParticleField):
    """Renders the base visual layer representing the Dish. May be configured
    with config.DISH_RERENDER_PERIOD. """
    def __init__(self, dish: Dish, **kwargs):
        super().__init__(**kwargs)
        self.dish = dish

    async def update(self) -> None:
        """Pulls the latest information from the Dish."""
        while True:
            self.dish.render_onto_textparticlefield(self)
            await asyncio.sleep(DISH_RERENDER_PERIOD)

    # def on_add(self):
    #     self.update_loop = asyncio.create_task(self.update())

    # def on_remove(self):
    #     self.update_loop.cancel()
