from typing import Callable
from enum import Enum, auto
from pydantic import BaseModel


class Resource(BaseModel):
    """Represents a resource the player can collect, along with a 
    short "ticker" name that uniquely identifies it."""
    ticker: str
    name: str
    description: str
    amount: float = 0
    rate: float = 0

RESOURCES = {
    "ATP": Resource(
        ticker="ATP",
        name="Adenosine Triphosphate",
        description="The basic unit of energy to be created and used inside a cellular organism.",
        amount=15
    ),
    "CYTO": Resource(
        ticker="CYTO",
        name="Cytosol",
        description="The liquid stored within a cell. Consumed by some actions and upgrades."
    ),
    "GLUC": Resource(
        ticker="GLUC",
        name="Glucose",
        description="Consumed by some organelles to make ATP. Produced by finding food in your organism's environment.",
        amount=10
    )
}
