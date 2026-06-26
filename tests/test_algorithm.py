"""
tests/test_algorithm.py
-----------------------
Unit tests for packing/algorithm.py.

All tests use pure-Python dataclasses — NO database required.
Run with: python manage.py test tests.test_algorithm --verbosity=2
"""

import unittest

from packing.algorithm import fits_in_box, pack_order
from packing.models import BoxSpec, PackingError, PackingResult, ProductSpec


# ---------------------------------------------------------------------------
# Helpers — small factory functions to reduce repetition
# ---------------------------------------------------------------------------

def make_product(
    name="Widget",
    length=10.0,
    width=8.0,
    height=5.0,
    weight=1.0,
    pid=1,
) -> ProductSpec:
    return ProductSpec(id=pid, name=name, length=length, width=width, height=height, weight=weight)


def make_box(
    name="Box",
    il=20.0,
    iw=20.0,
    ih=20.0,
    max_weight=10.0,
    cost=5.0,
    bid=1,
) -> BoxSpec:
    return BoxSpec(
        id=bid,
        name=name,
        internal_length=il,
        internal_width=iw,
        internal_height=ih,
        max_weight=max_weight,
        cost=cost,
    )


# ---------------------------------------------------------------------------
# fits_in_box tests
# ---------------------------------------------------------------------------

class TestFitsInBox(unittest.TestCase):

    def test_fits_exact_dimensions(self):
        """Product with the exact same dimensions as the box should fit."""
        product = make_product(length=20.0, width=20.0, height=20.0)
        box = make_box(il=20.0, iw=20.0, ih=20.0)
        self.assertTrue(fits_in_box(product, box))

    def test_fits_smaller(self):
        """Product clearly smaller than box fits without rotation."""
        product = make_product(length=5.0, width=5.0, height=5.0)
        box = make_box(il=20.0, iw=20.0, ih=20.0)
        self.assertTrue(fits_in_box(product, box))

    def test_fits_after_rotation(self):
        """
        Product (L=3, W=1, H=4) does NOT fit in a 4×4×2 box in its default
        orientation (4 > 2 for height), but one rotation makes it fit:

        Default (3,1,4): 3≤4 ✓, 1≤4 ✓, 4≤2 ✗
        (3,4,1):         3≤4 ✓, 4≤4 ✓, 1≤2 ✓  → fits!

        So the product fits only after rotation. fits_in_box must return True.
        """
        product = make_product(length=3.0, width=1.0, height=4.0)
        box = make_box(il=4.0, iw=4.0, ih=2.0)
        self.assertTrue(fits_in_box(product, box))

    def test_does_not_fit_any_rotation(self):
        """A product that is too large in every orientation should not fit."""
        product = make_product(length=25.0, width=25.0, height=25.0)
        box = make_box(il=20.0, iw=20.0, ih=20.0)
        self.assertFalse(fits_in_box(product, box))

    def test_one_dimension_too_large(self):
        """Product fits in two dimensions but not the third, in any rotation."""
        # Product 5×5×30 into box 20×20×20: 30 > 20 will always fail one dim.
        product = make_product(length=5.0, width=5.0, height=30.0)
        box = make_box(il=20.0, iw=20.0, ih=20.0)
        self.assertFalse(fits_in_box(product, box))


# ---------------------------------------------------------------------------
# pack_order tests
# ---------------------------------------------------------------------------

class TestPackOrder(unittest.TestCase):

    def _make_boxes(self):
        """Two box types: Small (cheap) and Large (expensive)."""
        small = make_box(name="Small", il=20.0, iw=20.0, ih=20.0, max_weight=5.0, cost=2.0, bid=1)
        large = make_box(name="Large", il=50.0, iw=50.0, ih=50.0, max_weight=30.0, cost=8.0, bid=2)
        return [small, large]

    def test_pack_single_box(self):
        """
        Two small items that together fit in one Small box (volume + weight).
        Expected: exactly one box used.
        """
        boxes = self._make_boxes()
        p1 = make_product(name="A", length=5.0, width=5.0, height=5.0, weight=1.0, pid=1)
        p2 = make_product(name="B", length=5.0, width=5.0, height=5.0, weight=1.0, pid=2)

        result = pack_order([(p1, 1), (p2, 1)], boxes)

        self.assertIsInstance(result, PackingResult)
        self.assertEqual(len(result.boxes), 1)
        self.assertEqual(result.boxes[0].box.name, "Small")
        self.assertAlmostEqual(result.total_cost, 2.0)

    def test_pack_two_boxes_volume(self):
        """
        Items whose combined volume exceeds a Small box must spill into a second box.

        Small box volume = 20×20×20 = 8000 cm³.
        Each item: 15×15×15 = 3375 cm³.  Two items = 6750 < 8000 → fits.
        Use three items: 3 × 3375 = 10125 > 8000 → forces a second box.
        """
        boxes = self._make_boxes()
        p = make_product(name="BigItem", length=15.0, width=15.0, height=15.0, weight=0.5, pid=1)

        result = pack_order([(p, 3)], boxes)

        self.assertIsInstance(result, PackingResult)
        self.assertEqual(len(result.boxes), 2, "Three 15³ items should require two Small boxes")

    def test_pack_two_boxes_weight(self):
        """
        Items that fit by volume in one Small box but exceed its weight limit
        must be split across two boxes.

        Small box max_weight = 5.0 kg.
        Two items at 3.0 kg each → 6.0 kg > 5.0 kg → two boxes needed.
        Volume: 2 × (5×5×5) = 250 cm³, well within 8000 cm³ volume.
        """
        boxes = self._make_boxes()
        heavy = make_product(name="HeavyItem", length=5.0, width=5.0, height=5.0, weight=3.0, pid=1)

        result = pack_order([(heavy, 2)], boxes)

        self.assertIsInstance(result, PackingResult)
        self.assertEqual(len(result.boxes), 2, "Two 3 kg items should not fit in one 5 kg box")

    def test_pack_no_box_fits(self):
        """
        A product larger than all boxes should return PackingError, not raise an exception.
        """
        boxes = self._make_boxes()
        giant = make_product(name="GiantItem", length=100.0, width=100.0, height=100.0, weight=1.0, pid=99)

        result = pack_order([(giant, 1)], boxes)

        self.assertIsInstance(result, PackingError)
        self.assertIn("GiantItem", result.message)

    def test_greedy_prefers_cheapest_box(self):
        """
        When an item fits in multiple already-open boxes with different costs,
        the greedy algorithm must pick the cheapest one.

        Scenario
        --------
        - CheapBox:  5×5×5, max_weight=20 kg, cost=2.0
        - PriceyBox: 10×10×10, max_weight=2.0 kg, cost=8.0

        Sort order by volume desc: item_big(216) > item_small(8) > tiny(1)

        item_big (6×6×6, 1.4 kg):
          No open boxes. Cheapest viable by dimension:
            CheapBox: 6 > 5 → doesn't fit. PriceyBox: 6 < 10 → fits.
          Only PriceyBox is viable → opens PriceyBox.
          PriceyBox remaining weight: 2.0 - 1.4 = 0.6 kg.

        item_small (2×2×2, 1.4 kg):
          Open boxes: PriceyBox (remaining weight 0.6 < 1.4) → fails weight check.
          No valid open box candidate → open cheapest viable type.
            CheapBox: 2 < 5 → fits dimensionally, cost=2.0. Opens CheapBox.
          CheapBox remaining weight: 20 - 1.4 = 18.6 kg.

        tiny (1×1×1, 0.3 kg):
          Open boxes: CheapBox (0.3 ≤ 18.6 ✓, vol ✓) AND PriceyBox (0.3 ≤ 0.6 ✓, vol ✓).
          Both are valid candidates. Cheapest = CheapBox (cost 2.0 < 8.0).
          → tiny goes to CheapBox. ✓

        This directly verifies the "cheapest open box" preference.
        """
        cheap  = make_box(name="CheapBox",  il=5.0,  iw=5.0,  ih=5.0,  max_weight=20.0, cost=2.0, bid=1)
        pricey = make_box(name="PriceyBox", il=10.0, iw=10.0, ih=10.0, max_weight=2.0,  cost=8.0, bid=2)
        boxes = [cheap, pricey]

        item_big   = make_product(name="BigItem",   length=6.0, width=6.0, height=6.0, weight=1.4, pid=1)
        item_small = make_product(name="SmallItem", length=2.0, width=2.0, height=2.0, weight=1.4, pid=2)
        tiny       = make_product(name="Tiny",      length=1.0, width=1.0, height=1.0, weight=0.3, pid=3)

        result = pack_order([(item_big, 1), (item_small, 1), (tiny, 1)], boxes)

        self.assertIsInstance(result, PackingResult)

        cheap_results  = [br for br in result.boxes if br.box.name == "CheapBox"]
        pricey_results = [br for br in result.boxes if br.box.name == "PriceyBox"]
        self.assertEqual(len(cheap_results),  1, "Expected exactly one CheapBox")
        self.assertEqual(len(pricey_results), 1, "Expected exactly one PriceyBox")

        names_in_cheap  = [item.product_name for item in cheap_results[0].items]
        names_in_pricey = [item.product_name for item in pricey_results[0].items]
        self.assertIn("Tiny",    names_in_cheap,  "Tiny must be in the cheaper CheapBox")
        self.assertNotIn("Tiny", names_in_pricey, "Tiny must NOT be in the expensive PriceyBox")

    def test_empty_order(self):
        """An empty items list should return a PackingResult with no boxes and zero cost."""
        boxes = self._make_boxes()
        result = pack_order([], boxes)
        self.assertIsInstance(result, PackingResult)
        self.assertEqual(len(result.boxes), 0)
        self.assertAlmostEqual(result.total_cost, 0.0)


if __name__ == "__main__":
    unittest.main()
