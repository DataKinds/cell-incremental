from typing import Callable

from pydantic import BaseModel


class ConditionalRate(BaseModel):
    """Describes how an Organelle can use or produce resources.

    :ivar consumption: Keyed on resource ticker, with values giving rates of decrease per second.
    :ivar production: Keyed on resource ticker, with values giving rates of increase per second.
        May only be applied if all of the above consumption is satisfied.
    """

    consumption: dict[str, float] = {}
    production: dict[str, float] = {}


class Organelle(BaseModel):
    idx: int
    name: str
    description: str
    # Keyed on ticker name, with a value equal to the starting cost
    base_cost: dict[str, float] = {}
    # Keyed on ticker name, with a value equal to the iterated exponent of the
    # cost as more organelles are purchased
    cost_exponent: dict[str, float] = {}
    count: int = 0
    rates: list[ConditionalRate] = []

    @property
    def costs(self) -> dict[str, float]:
        out = {}
        for ticker_name, base_cost in self.base_cost.items():
            out[ticker_name] = base_cost ** (self.cost_exponent[ticker_name]**self.count)
        return out


ORGANELLES = {
    0: Organelle(
        idx=0,
        name="Chloroplast",
        description="Generates 0.1 ATP/s passively.",
        base_cost={'ATP': 10},
        cost_exponent={'ATP': 1.11},
        rates=[ConditionalRate(production={'ATP': 0.1})],
    ),
    1: Organelle(
        idx=1,
        name="Mitochondria",
        description="Generates 0.1 ATP/s passively. If glucose is present, consume 0.5 glucose/s to produce an additional 1 ATP/s.",
        base_cost={'ATP': 30},
        cost_exponent={'ATP': 1.12},
        rates=[
            ConditionalRate(production={'ATP': 0.1}),
            ConditionalRate(consumption={'GLUC': 0.5}, production={'ATP': 1}),
        ],
    ),
    2: Organelle(
        idx=2,
        name="Nanoconsumer",
        description="Eats away at the very matter of your organism to produce energy. Consumes 0.1 cytosol/s to produce 2 ATP/s.",
        base_cost={'ATP': 100},
        cost_exponent={'ATP': 1.01},
        rates=[
            ConditionalRate(production={'ATP': 0.5}),
            ConditionalRate(consumption={'CYTO': 0.1}, production={'ATP': 2}),
        ],
    ),
}
