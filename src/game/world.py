import asyncio

from nurses_2.app import App
from nurses_2.colors import RED, WHITE, ColorPair
from nurses_2.widgets.grid_layout import GridLayout
from nurses_2.widgets.scroll_view.scroll_view import ScrollView
from nurses_2.widgets.widget import Widget
from pydantic import BaseModel

from game.config import *
from game.organelle import ORGANELLES, Organelle
from game.resource import RESOURCES, Resource
from game.widgets import OrganelleListWidget, ResourceWidget


class State(BaseModel):
    """Tracks the mutable state of the World."""
    cytosol: float = 0
    organelles: dict[int, Organelle] = {k: v.copy() for k, v in ORGANELLES.items()}
    resources: dict[str, Resource] = {k: v.copy() for k, v in RESOURCES.items()}

    # Helper functions to do common tasks
    def ticker(self, ticker_name):
        """Get a Resource by its ticker name."""
        return self.resources[ticker_name.upper()]

    def withdraw(self, ticker_name, amount):
        """Attempt to withdraw (remove) a certain resource by its ticker name. 
        True if success. If there is less of the resource than the amount
        given, no resource is removed and False is returned."""
        resource = self.ticker(ticker_name)
        if amount > resource.amount:
            return False
        else:
            resource.amount -= amount
            resource.rate -= amount / UPDATE_PERIOD
            return True
        
    def deposit(self, ticker_name, amount):
        """Attempt to deposit (add) to a certain resource by its ticker name."""
        resource = self.ticker(ticker_name)
        resource.amount += amount
        resource.rate += amount / UPDATE_PERIOD
        return True

    def buy(self, organelle_id) -> bool:
        """Attempt to buy an organelle. True if success."""
        organelle = self.organelles[organelle_id]
        atp = self.ticker('atp')
        if atp.amount >= organelle.cost:
            atp.amount -= organelle.cost
            organelle.count += 1
            return True
        else:
            return False    
        
    def sell(self, organelle_id) -> bool:
        """Attempt to sell an organelle. True if success."""
        organelle = self.organelles[organelle_id]
        if organelle.count > 0:
            organelle.count -= 1
            self.ticker('atp').amount += organelle.cost
            return True
        else:
            return False


class World(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.st: State = State()

    async def tick_update_loop(self):
        while True:
            # Reset all the rates as they'll be recalculated shortly
            for resource in self.st.resources.values():
                resource.rate = 0
            for organelle in self.st.organelles.values():
                # Apply conditional rates on organelles
                for cond_rate in organelle.rates:
                    # Check if all the conditions are met for the conditional rate
                    ok = True
                    for ticker_name, rate in cond_rate.consumption.items():
                        if self.st.ticker(ticker_name).amount < rate * UPDATE_PERIOD:
                            ok = False
                            break
                    # If all the conditions are met to apply this rate, do two things:
                    # 1. Withdraw the required resources, updating the rates
                    if ok:
                        for ticker_name, rate in cond_rate.consumption.items():
                            self.st.withdraw(ticker_name, rate * UPDATE_PERIOD * organelle.count)
                    # 2. Deposit the required resources, updating the rates
                        for ticker_name, rate in cond_rate.production.items():
                            self.st.deposit(ticker_name, rate * UPDATE_PERIOD * organelle.count)
            await asyncio.sleep(UPDATE_PERIOD)

    async def on_start(self):
        # Start the async jobb running the main game logic
        self.update_loop = asyncio.create_task(self.tick_update_loop())

        # Add all the widgets to the view
        main_layout_scroll = ScrollView(
            allow_horizontal_scroll=False, show_horizontal_bar=False, size_hint=(1, 1), pos=(0, 0)
        )
        main_layout = Widget(
            size=(100, 1), size_hint=(None, 1), background_color_pair=ColorPair.from_colors(RED, WHITE)
        )
        main_layout_scroll.view = main_layout
        main_layout.add_widgets(
            ResourceWidget(self), OrganelleListWidget(self, pos=(5, 0), size=(40, 1), size_hint=(None, 1))
        )
        self.add_widget(main_layout_scroll)
