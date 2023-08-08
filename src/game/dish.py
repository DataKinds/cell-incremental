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

    def add_organism(self, organism: Organism) -> Organism:
        """Finish initializing an organism and add it to our dish."""
        new_idx = randint(0, maxsize)
        while new_idx in self.organisms:
            new_idx = randint(0, maxsize)
        organism.idx = new_idx
        self.organisms[new_idx] = organism
        return organism

    def add_food(self, *args):
        """Add food to our dish."""
        self.food.append(Food(*args))


class DishWidget(TextParticleField):
    """Renders the base visual layer representing the Dish. May be configured
    with config.DISH_RERENDER_PERIOD. """
    def __init__(self, dish: Dish, **kwargs):
        super().__init__(**kwargs)
        self.dish = dish
        self.follow_organism: Organism | None = None

        self.follow_organism = self.dish.add_organism(
            Organism(pos=(0, -5), bounds=(2, 2))
        )

    def on_add(self):
        """Start the render loop."""
        self.update_loop = asyncio.create_task(self.update())

    def on_remove(self):
        """Stop the render loop."""
        self.update_loop.cancel()

    def render_dish(self, origin_y: int, origin_x: int):
        """Render our dish onto a nurses_2 TextParticleField. Apply a "camera
        offset" according to the origin_y and origin_x parameters. """
        # create empty render area
        particle_positions_stack = []
        particle_chars_stack = []
        particle_color_pairs_stack = []
        # render food
        if len(self.dish.food) > 0:
            particle_positions_stack.append(
                np.array([[f.y, f.x] for f in self.dish.food]) - (origin_y, origin_x)
            )
            ary = np.zeros(len(self.dish.food), dtype=Char) 
            ary['char'] = "x"
            particle_chars_stack.append(ary)
            particle_color_pairs_stack.append(
                np.full((len(self.dish.food), 6), [list(ColorPair.from_colors(WHITE, BLACK))])
            )
        # render organisms
        if len(self.dish.organisms) > 0:
            particle_positions_stack.append(
                np.array([[o.pos.y, o.pos.x] for o in self.dish.organisms.values()]) - (origin_y, origin_x)
            )
            ary = np.zeros(len(self.dish.organisms), dtype=Char) 
            ary['char'] = "@"
            particle_chars_stack.append(ary)
            particle_color_pairs_stack.append(
                np.full((len(self.dish.organisms), 6), [list(ColorPair.from_colors(WHITE, BLACK))])
            )
        # blit to terminal
        assert len(particle_positions_stack) == len(particle_chars_stack) and len(particle_chars_stack) == len(particle_color_pairs_stack)
        if len(particle_positions_stack) > 0:
            self.particle_positions = np.concatenate(particle_positions_stack)
            self.particle_chars = np.concatenate(particle_chars_stack)
            self.particle_color_pairs = np.concatenate(particle_color_pairs_stack)

    async def update(self) -> None:
        """Pulls the latest information from the Dish."""
        while True:
            if self.follow_organism is None:
                self.render_dish(0, 0)
            else:
                self.render_dish(self.follow_organism.pos.y, self.follow_organism.pos.x)
            await asyncio.sleep(DISH_RERENDER_PERIOD)

