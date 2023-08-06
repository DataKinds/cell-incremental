import asyncio
from textwrap import dedent, fill

from nurses_2.colors import RED, WHITE, ColorPair
from nurses_2.widgets.button import Button
from nurses_2.widgets.grid_layout import GridLayout, Orientation
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget
from nurses_2.widgets.widget_data_structures import Anchor, style_char

from game.config import *
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
            self.set_text('\n'.join(resource_text))
            await asyncio.sleep(RERENDER_PERIOD)


class OrganelleBuySellWidget(Widget):
    horiz_button_size = 0.1

    def __init__(self, world: "World", organelle: Organelle, **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.organelle = organelle
        self.background_color_pair = ColorPair.from_colors(WHITE, RED)
        self.title_widget = TextWidget(pos=(0, 0), size_hint=(None, 1 - self.horiz_button_size))
        self.description_widget = TextWidget(pos=(1, 0), size_hint=(None, 1 - self.horiz_button_size))
        self.stat_widget = TextWidget(
            pos=(self.description_widget.canvas.shape[1] - 3, 0), size_hint=(None, 1 - self.horiz_button_size)
        )
        self.buy_button = Button(
            label="Buy",
            anchor=Anchor.TOP_RIGHT,
            size=(10, 10),
            size_hint=(0.5, self.horiz_button_size),
            pos_hint=(0, 1),
            callback=lambda: self.world.st.buy(organelle.idx),
        )
        self.sell_button = Button(
            label="Sell", anchor=Anchor.TOP_RIGHT, size_hint=(0.5, self.horiz_button_size), pos_hint=(0.5, 1), callback=lambda: self.world.st.sell(organelle.idx)
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
            self.description_widget.set_text(fill(self.organelle.description, self.description_widget.size[1]), italic=True)
            stats_text = dedent(
                f"""
                Cost: {self.organelle.cost:.2f} ATP
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

    # def on_key(self, key_event: 'nurses_2.io.input.events.KeyEvent') -> bool:
    #     self.add_str(key_event.key)
