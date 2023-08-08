import asyncio
import logging
from random import choice, randint, random, randrange
from textwrap import dedent, fill, wrap

import numpy as np
from nurses_2.colors import BLACK, RED, WHITE, ColorPair
from nurses_2.io.input.events import MouseEventType
from nurses_2.widgets.button import Button
from nurses_2.widgets.grid_layout import GridLayout, Orientation
from nurses_2.widgets.text_field import TextParticleField
from nurses_2.widgets.text_widget import Border, TextWidget
from nurses_2.widgets.widget import Widget
from nurses_2.widgets.widget_data_structures import Anchor, Char, style_char

from game.config import *
from game.dish import Dish, Organism, Point
from game.organelle import ORGANELLES, Organelle


class ResourceWidget(TextWidget):
    """This widget shows the user what resources they have available."""

    def __init__(self, world: "World", **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.update_loop = asyncio.create_task(self.update())

    def on_remove(self):
        """Stop the render loop."""
        self.update_loop.cancel()

    async def update(self) -> None:
        while True:
            resource_text = []
            for ticker, res in self.world.st.resources.items():
                resource_text.append(f"{res.name} ({ticker}): {res.amount:.2f} @ {res.rate:.2f}/s")
            self.set_text("\n".join(resource_text))
            await asyncio.sleep(RERENDER_PERIOD)


class OrganelleBuySellWidget(Widget):
    horiz_button_size_hint = 0.1

    def __init__(self, world: "World", organelle: Organelle, **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.organelle = organelle
        self.height = 5
        self.background_color_pair = ColorPair.from_colors(WHITE, RED)
        self.title_widget = TextWidget(pos=(0, 0), size_hint=(None, 1 - self.horiz_button_size_hint))
        self.description_widget = TextWidget(pos=(1, 0), size_hint=(None, 1 - self.horiz_button_size_hint))
        self.stat_widget = TextWidget(
            pos=(3, 0),
            # pos=(self.description_widget.canvas.shape[1] - 3, 0),
            size_hint=(None, 1 - self.horiz_button_size_hint),
        )
        self.buy_button = Button(
            label="Buy",
            anchor=Anchor.TOP_RIGHT,
            size=(10, 10),
            size_hint=(0.51, self.horiz_button_size_hint),
            pos_hint=(0, 1),
            callback=lambda: self.world.st.buy(organelle.idx),
        )
        self.sell_button = Button(
            label="Sell",
            anchor=Anchor.BOTTOM_RIGHT,
            size_hint=(0.5, self.horiz_button_size_hint),
            pos_hint=(1, 1),
            callback=lambda: self.world.st.sell(organelle.idx),
        )
        self.add_widgets(
            self.title_widget, self.description_widget, self.stat_widget, self.buy_button, self.sell_button
        )
        self.update_loop = asyncio.create_task(self.update())

    def on_remove(self):
        """Stop the render loop."""
        self.update_loop.cancel()

    async def update(self):
        while True:
            self.title_widget.set_text(self.organelle.name, underline=True)
            self.description_widget.apply_hints()
            self.description_widget.set_text(
                fill(self.organelle.description, self.description_widget.size[1]), italic=True
            )
            stats_text = dedent(
                f"""
                Cost: {self.organelle.costs}
                Owned: {self.organelle.count}
            """
            ).strip()
            self.stat_widget.set_text(stats_text)
            self.title_widget.normalize_canvas()
            self.description_widget.normalize_canvas()
            self.stat_widget.normalize_canvas()
            await asyncio.sleep(RERENDER_PERIOD)


class OrganelleListWidget(GridLayout):
    def __init__(self, world: "World", **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.vertical_spacing = 1
        self.grid_rows = len(world.st.organelles)
        for organelle in world.st.organelles.values():
            self.add_widget(OrganelleBuySellWidget(world, organelle, size_hint=(None, 1)))


class MainViewTabWidget(GridLayout):
    tab_width = 18

    def make_tab_label(self, name, hotkey, callback):
        """Create and add a new tab.
        :param name: The displayed name of the tab.
        :param hotkey: The key the user must press to switch to the tab.
        :param callback: The callback that is fired to change the content view.
        """

        class Tab(Button, TextWidget):
            def __init__(self, **kwargs):
                kwargs["callback"] = callback
                super().__init__(**kwargs)
                self.add_border(Border.CURVED)

            def on_key(self, key_event: "nurses_2.io.input.events.KeyEvent") -> bool:
                if key_event.key == hotkey and not (key_event.mods.alt or key_event.mods.ctrl or key_event.mods.shift):
                    callback()
                    return True
                return False

        tab = Tab(size=(4, self.tab_width))
        for line_idx, line in enumerate(wrap(name + f" [{hotkey}]", width=self.tab_width - 2)):
            tab.add_str(line, pos=(1 + line_idx, 1))
        self.grid_columns += 1
        self.add_widget(tab)
        return tab

    def __init__(self, world: "World", **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.grid_columns = 3
        self.make_tab_label("Organelle Upgrades", "q", lambda: self.world.switch_to_tab(0))
        self.make_tab_label("Petri Dish", "w", lambda: self.world.switch_to_tab(1))
        self.make_tab_label("Edit Organism", "e", lambda: self.world.switch_to_tab(2))


class DishWidget(TextParticleField):
    """Renders the base visual layer representing the Dish. May be configured
    with config.DISH_RERENDER_PERIOD."""

    def __init__(self, dish: Dish, **kwargs):
        super().__init__(**kwargs)
        self.dish = dish
        self.follow_organism: Organism | None = None
        self.follow_organism_camera_offset: Point = Point(4, 9)

    def on_add(self):
        """Start the render loop."""
        self.update_loop = asyncio.create_task(self.update())

    def on_remove(self):
        """Stop the render loop."""
        self.update_loop.cancel()

    def render_dish(self, origin_y: int, origin_x: int):
        """Render our dish onto a nurses_2 TextParticleField. Apply a "camera
        offset" according to the origin_y and origin_x parameters."""
        # create empty render area
        particle_positions_stack = []
        particle_chars_stack = []
        particle_color_pairs_stack = []
        # render food
        if len(self.dish.food) > 0:
            particle_positions_stack.append(np.array([[f.y, f.x] for f in self.dish.food]) - (origin_y, origin_x))
            ary = np.zeros(len(self.dish.food), dtype=Char)
            ary["char"] = "x"
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
            ary["char"] = "@"
            particle_chars_stack.append(ary)
            particle_color_pairs_stack.append(
                np.full((len(self.dish.organisms), 6), [list(ColorPair.from_colors(WHITE, BLACK))])
            )
        # blit to terminal
        assert len(particle_positions_stack) == len(particle_chars_stack) and len(particle_chars_stack) == len(
            particle_color_pairs_stack
        )
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
                offset_pos = self.follow_organism.pos - self.follow_organism_camera_offset
                self.render_dish(offset_pos.y, offset_pos.x)
            await asyncio.sleep(DISH_RERENDER_PERIOD)


class PlayableDishWidget(DishWidget):
    def on_key(self, key_event: "nurses_2.io.input.events.KeyEvent") -> bool:
        try:
            if key_event.mods.shift or key_event.mods.ctrl:
                # Don't capture shift or control modified keys in da dish
                return False
            if key_event.mods.alt:
                if key_event.keyin "hjkl":
                    cam_keymap = {"h": Point(0,-1), "j": Point(-1,0), "k": Point(1,0), "l": Point(0,1)}
                    self.follow_organism_camera_offset += cam_keymap[key_event.key]
            else:
                if key_event.key in "hjkl":
                    if self.follow_organism is not None:
                        self.follow_organism.move({"h": 4, "j": 2, "k": 8, "l": 6}[key_event.key])
                elif key_event.key == "p":
                    self.follow_organism = self.dish.add_organism(Organism(pos=Point(0, -5), bounds=Point(2, 2)))
                elif key_event.key == "f":
                    self.dish.add_food(randrange(50), randrange(150), random())
                elif key_event.key == "n":
                    self.follow_organism_camera_offset.y += 1
        except Exception as e:
            logging.critical(e, exc_info=True)
        return False
