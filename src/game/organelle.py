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
    def cost(self) -> float:
        return self.base_cost ** (self.cost_exponent**self.count)


ORGANELLES = {
    0: Organelle(
        idx=0,
        name="Chloroplast",
        description="Generates 1 ATP/s passively.",
        base_cost={'ATP': 10},
        cost_exponent={'ATP': 1.11},
        rates=[ConditionalRate(production={'ATP': 1})]
    ),
    1: Organelle(
        idx=1,
        name="Mitochondria",
        description="Generates 0.5 ATP/s passively. If glucose is present, consume 0.5 glucose/s to produce an additional 2 ATP/s.",
        base_cost={'ATP': 10},
        cost_exponent={'ATP': 1.12},
        rates=[
            ConditionalRate(production={'ATP': 0.5}),
            ConditionalRate(consumption={'GLUC': 0.5}, production={'ATP': 2})
        ]
    ),
}
