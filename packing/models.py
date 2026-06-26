"""
packing/models.py
-----------------
Pure-Python dataclasses used by the packing algorithm.
No Django imports — this module is independently unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProductSpec:
    """Physical specification of a single product unit."""

    id: int
    name: str
    length: float
    width: float
    height: float
    weight: float

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class BoxSpec:
    """Specification of a box type (not an instance)."""

    id: int
    name: str
    internal_length: float
    internal_width: float
    internal_height: float
    max_weight: float
    cost: float

    @property
    def volume(self) -> float:
        return self.internal_length * self.internal_width * self.internal_height


@dataclass
class PlacedItem:
    """A product placed inside a box result (quantity aggregated for output)."""

    product_id: int
    product_name: str
    quantity: int = 1


@dataclass
class BoxResult:
    """One box used in the packing result, with its contents and cost."""

    box: BoxSpec
    items: list[PlacedItem] = field(default_factory=list)

    @property
    def cost(self) -> float:
        return self.box.cost


@dataclass
class PackingResult:
    """Successful packing result: list of boxes and total cost."""

    boxes: list[BoxResult]
    total_cost: float


@dataclass
class PackingError:
    """Returned (not raised) when a product cannot fit in any box."""

    message: str
