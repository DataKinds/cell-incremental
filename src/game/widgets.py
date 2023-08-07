import asyncio
from textwrap import dedent, fill, wrap

from nurses_2.colors import RED, WHITE, ColorPair
from nurses_2.widgets.button import Button
from nurses_2.widgets.grid_layout import GridLayout, Orientation
from nurses_2.widgets.text_widget import TextWidget, Border
from nurses_2.widgets.widget import Widget
from nurses_2.widgets.widget_data_structures import Anchor, style_char
from nurses_2.io.input.events import MouseEventType

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
    horiz_button_size_hint = 0.1

    def __init__(self, world: "World", organelle: Organelle, **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self.organelle = organelle
        self.height = 6
        self.background_color_pair = ColorPair.from_colors(WHITE, RED)
        self.title_widget = TextWidget(
            pos=(0, 0), 
            size_hint=(None, 1 - self.horiz_button_size_hint)
        )
        self.description_widget = TextWidget(
            pos=(1, 0), 
            size_hint=(None, 1 - self.horiz_button_size_hint)
        )
        self.stat_widget = TextWidget(
            pos=(4, 0),
            # pos=(self.description_widget.canvas.shape[1] - 3, 0), 
            size_hint=(None, 1 - self.horiz_button_size_hint),
        )
        self.buy_button = Button(
            label="Buy",
            anchor=Anchor.TOP_RIGHT,
            size=(10, 10),
            size_hint=(0.5, self.horiz_button_size_hint),
            pos_hint=(0, 1),
            callback=lambda: self.world.st.buy(organelle.idx),
        )
        self.sell_button = Button(
            label="Sell",
            anchor=Anchor.TOP_RIGHT,
            size_hint=(0.5, self.horiz_button_size_hint),
            pos_hint=(0.5, 1),
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
                kwargs['callback'] = callback
                super().__init__(**kwargs)
                self.add_border(Border.CURVED)

            def on_key(self, key_event: 'nurses_2.io.input.events.KeyEvent') -> bool:
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
