"""
packing/algorithm.py
--------------------
Core greedy box-selection algorithm.

Deliberately decoupled from Django — accepts and returns pure-Python
dataclasses only (see packing/models.py). No DB, ORM, or HTTP concerns here.

Algorithm overview
------------------
1. fits_in_box()   — tries all 6 axis-aligned rotations; returns True if any
                     rotation has all three product dimensions ≤ the box's
                     corresponding internal dimensions.

2. pack_order()    — greedy, scalar-volume-budget heuristic:
   a) Expand items by quantity into individual ProductSpec units.
   b) Sort units by volume descending (largest first).
   c) For each unit find an already-open box where the unit fits (rotation +
      remaining-volume budget + remaining-weight budget) and cost is lowest;
      on cost ties prefer the tightest fit (least remaining volume).
   d) If no open box works, open the cheapest viable box type.
   e) If no box type can fit the unit at all, return PackingError (not raise).
   f) Aggregate placed items per box → PackingResult.

Note: "remaining volume" is a scalar budget (sum of product volumes ≤ box
internal volume). This is intentionally NOT 3D spatial bin-packing.
"""

from __future__ import annotations

from itertools import permutations
from dataclasses import dataclass, field

from .models import BoxSpec, PackingError, PackingResult, BoxResult, PlacedItem, ProductSpec


# ---------------------------------------------------------------------------
# 1. Rotation-fit check
# ---------------------------------------------------------------------------

def fits_in_box(product: ProductSpec, box: BoxSpec) -> bool:
    """
    Return True if the product fits inside the box in at least one of the
    6 axis-aligned orientations (all permutations of L, W, H).

    A product fits in an orientation (pL, pW, pH) when:
        pL <= box.internal_length
        pW <= box.internal_width
        pH <= box.internal_height
    """
    box_dims = (box.internal_length, box.internal_width, box.internal_height)
    product_dims = (product.length, product.width, product.height)

    for rotation in permutations(product_dims):
        if all(p <= b for p, b in zip(rotation, box_dims)):
            return True
    return False


# ---------------------------------------------------------------------------
# 2. Internal open-box state
# ---------------------------------------------------------------------------

@dataclass
class _OpenBox:
    """Tracks one in-use box instance during packing."""

    box_spec: BoxSpec
    remaining_volume: float
    remaining_weight: float
    placed: list[tuple[ProductSpec, int]] = field(default_factory=list)
    # placed = list of (product, count) pairs; count is always 1 here,
    # aggregated into PlacedItem only at output time.


# ---------------------------------------------------------------------------
# 3. Greedy pack_order
# ---------------------------------------------------------------------------

def pack_order(
    items: list[tuple[ProductSpec, int]],
    boxes: list[BoxSpec],
) -> PackingResult | PackingError:
    """
    Greedily assign order items to boxes.

    Parameters
    ----------
    items : list of (ProductSpec, quantity) tuples
    boxes : list of available BoxSpec types (all box types, not instances)

    Returns
    -------
    PackingResult on success, PackingError if any product cannot be shipped.
    """
    if not items:
        return PackingResult(boxes=[], total_cost=0.0)

    # Step 1 — expand by quantity into individual units
    units: list[ProductSpec] = []
    for product, qty in items:
        units.extend([product] * qty)

    # Step 2 — sort by volume descending (largest first)
    units.sort(key=lambda p: p.volume, reverse=True)

    # Sort box types by cost ascending (used when opening a new box)
    sorted_boxes = sorted(boxes, key=lambda b: b.cost)

    open_boxes: list[_OpenBox] = []

    # Step 3 — place each unit
    for unit in units:
        # Find candidate open boxes: fits (rotation + volume + weight)
        candidates = [
            ob for ob in open_boxes
            if (
                fits_in_box(unit, ob.box_spec)
                and unit.volume <= ob.remaining_volume
                and unit.weight <= ob.remaining_weight
            )
        ]

        if candidates:
            # Pick lowest cost; break ties by tightest fit (least remaining volume)
            chosen = min(candidates, key=lambda ob: (ob.box_spec.cost, ob.remaining_volume))
            chosen.remaining_volume -= unit.volume
            chosen.remaining_weight -= unit.weight
            chosen.placed.append((unit, 1))
        else:
            # Need to open a new box — find cheapest type that can fit this unit
            viable = [b for b in sorted_boxes if fits_in_box(unit, b)]
            if not viable:
                return PackingError(
                    message=(
                        f"Product '{unit.name}' cannot fit in any available box "
                        f"in any orientation. It cannot be shipped."
                    )
                )
            new_box_spec = viable[0]  # sorted_boxes is already by cost asc
            ob = _OpenBox(
                box_spec=new_box_spec,
                remaining_volume=new_box_spec.volume - unit.volume,
                remaining_weight=new_box_spec.max_weight - unit.weight,
            )
            ob.placed.append((unit, 1))
            open_boxes.append(ob)

    # Step 4 — build output: aggregate placed items per open box
    box_results: list[BoxResult] = []
    for ob in open_boxes:
        # Aggregate: merge multiple placements of the same product
        aggregated: dict[int, PlacedItem] = {}
        for product, _ in ob.placed:
            if product.id in aggregated:
                aggregated[product.id].quantity += 1
            else:
                aggregated[product.id] = PlacedItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=1,
                )
        box_results.append(BoxResult(box=ob.box_spec, items=list(aggregated.values())))

    total_cost = sum(br.cost for br in box_results)
    return PackingResult(boxes=box_results, total_cost=total_cost)
