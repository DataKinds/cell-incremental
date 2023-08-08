from pydantic import BaseModel
from sys import maxsize
from random import randint
import numpy as np
from nurses_2.widgets.text_field import TextParticleField
from nurses_2.widgets.widget_data_structures import Char
import asyncio
from nurses_2.colors import ColorPair, BLACK, RED, WHITE
from collections import namedtuple 


from .config import DISH_RERENDER_PERIOD
from .organism import Organism


Food = namedtuple('Food', ['y', 'x', 'calories'])

class Dish(BaseModel):
    """The Dish manages the simulation of Organisms and provides the basic
    functionality required for the in-game Petri Dish."""

    organisms: dict[int, Organism] = {}
    food: list[Food] = [Food(1, 1, 0.1)]
    bounds: tuple[int, int] = (100, 600)

    def add_organism(self, organism):
        """Finish initializing an organism and add it to our dish."""
        new_idx = randint(0, maxsize)
        while new_idx in self.organisms:
            new_idx = randint(0, maxsize)
        organism.idx = new_idx
        self.organisms[new_idx] = organism

    def add_food(self, *args):
        """Add food to our dish."""
        self.food.append(Food(*args))

    # These three functions are for converting the Dish into a nurses_2 TextParticleField
    # def get_particle_positions(self):
    #     return np.array([[0,0], [1,1], [2,2]]) 
    # def get_particle_chars(self):
    #     out = np.zeros(3, dtype=Char) 
    #     out['char'] = "@"
    #     return out
    # def get_particle_color_pairs(self):
    #     return np.array([list(ColorPair.from_colors(WHITE, BLACK))]*3) 
    def render_onto_textparticlefield(self, tpf: TextParticleField):
        # create empty render area
        particle_positions_stack = []
        particle_chars_stack = []
        particle_color_pairs_stack = []
        # render food
        if len(self.food) > 0:
            particle_positions_stack.append(
                np.array([[f.y, f.x] for f in self.food])
            )
            ary = np.zeros(len(self.food), dtype=Char) 
            ary['char'] = "x"
            particle_chars_stack.append(ary)
            particle_color_pairs_stack.append(
                np.full((len(self.food), 6), [list(ColorPair.from_colors(WHITE, BLACK))])
            )
        # render organisms
        if len(self.organisms) > 0:
            particle_positions_stack.append(
                np.array([[o.pos.y, o.pos.x] for o in self.organisms.values()])
            )
            ary = np.zeros(len(self.organisms), dtype=Char) 
            ary['char'] = "@"
            particle_chars_stack.append(ary)
            particle_color_pairs_stack.append(
                np.full((len(self.organisms), 6), [list(ColorPair.from_colors(WHITE, BLACK))])
            )
        # blit to terminal
        assert len(particle_positions_stack) == len(particle_chars_stack) and len(particle_chars_stack) == len(particle_color_pairs_stack)
        if len(particle_positions_stack) > 0:
            tpf.particle_positions = np.concatenate(particle_positions_stack)
            tpf.particle_chars = np.concatenate(particle_chars_stack)
            tpf.particle_color_pairs = np.concatenate(particle_color_pairs_stack)

class DishWidget(TextParticleField):
    """Renders the base visual layer representing the Dish. May be configured
    with config.DISH_RERENDER_PERIOD. """
    def __init__(self, dish: Dish, **kwargs):
        super().__init__(**kwargs)
        self.dish = dish

    def on_add(self):
        """Start the render loop."""
        self.update_loop = asyncio.create_task(self.update())

    def on_remove(self):
        """Stop the render loop."""
        self.update_loop.cancel()

    async def update(self) -> None:
        """Pulls the latest information from the Dish."""
        while True:
            self.dish.render_onto_textparticlefield(self)
            await asyncio.sleep(DISH_RERENDER_PERIOD)

    # def on_add(self):
    #     self.update_loop = asyncio.create_task(self.update())

    # def on_remove(self):
    #     self.update_loop.cancel()
