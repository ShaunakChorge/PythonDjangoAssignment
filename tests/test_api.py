"""
tests/test_api.py
-----------------
API integration tests using Django's TestCase and DRF's APIClient.

These tests use the real database (seeded via migrations in setUp) and
exercise the full request → view → algorithm → response pipeline.

Run with: python manage.py test tests.test_api --verbosity=2
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from inventory.models import Box, Product


class ProductListAPITest(TestCase):
    """GET /api/products/"""

    def setUp(self):
        self.client = APIClient()

    def test_products_list_returns_200(self):
        """Endpoint returns HTTP 200."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_products_list_returns_seeded_data(self):
        """At least 8 products exist after migrations run."""
        response = self.client.get("/api/products/")
        self.assertGreaterEqual(len(response.data), 8)

    def test_products_list_has_expected_fields(self):
        """Each product entry has the required fields."""
        response = self.client.get("/api/products/")
        first = response.data[0]
        for field in ("id", "name", "length", "width", "height", "weight"):
            self.assertIn(field, first)


class BoxListAPITest(TestCase):
    """GET /api/boxes/"""

    def setUp(self):
        self.client = APIClient()

    def test_boxes_list_returns_200(self):
        """Endpoint returns HTTP 200."""
        response = self.client.get("/api/boxes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_boxes_list_returns_seeded_data(self):
        """At least 5 boxes exist after migrations run."""
        response = self.client.get("/api/boxes/")
        self.assertGreaterEqual(len(response.data), 5)

    def test_boxes_list_has_expected_fields(self):
        """Each box entry has the required fields."""
        response = self.client.get("/api/boxes/")
        first = response.data[0]
        for field in ("id", "name", "internal_length", "internal_width",
                      "internal_height", "max_weight", "cost"):
            self.assertIn(field, first)


class RecommendBoxAPITest(TestCase):
    """POST /api/recommend-box/"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/recommend-box/"

        # Grab real seeded product IDs — use lightweight ones that fit easily
        # Pen (14×1×1, 0.05 kg) and Notebook (22×17×3, 0.40 kg)
        # Both fit comfortably in a Small box (25×20×15).
        self.pen = Product.objects.get(name="Pen")
        self.notebook = Product.objects.get(name="Notebook")

    def test_valid_order_returns_200_and_correct_structure(self):
        """A valid order with shippable items returns 200 and the expected structure."""
        payload = {
            "items": [
                {"product_id": self.pen.pk, "quantity": 2},
                {"product_id": self.notebook.pk, "quantity": 1},
            ]
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn("boxes", data)
        self.assertIn("total_cost", data)
        self.assertGreater(len(data["boxes"]), 0)

        # Each box result has expected fields
        box_result = data["boxes"][0]
        self.assertIn("box_name", box_result)
        self.assertIn("cost", box_result)
        self.assertIn("items", box_result)

    def test_no_fit_returns_400_with_error_key(self):
        """
        A product that cannot fit in any box returns HTTP 400 with an 'error' key.
        We create an oversized product on-the-fly (not in seed data).
        """
        giant = Product.objects.create(
            name="GiantTestProduct",
            length=999,
            width=999,
            height=999,
            weight=1,
        )
        payload = {"items": [{"product_id": giant.pk, "quantity": 1}]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("GiantTestProduct", response.data["error"])

    def test_missing_items_key_returns_400(self):
        """Request body missing the 'items' key → 400."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_items_list_returns_400(self):
        """Request body with an empty 'items' list → 400."""
        response = self.client.post(self.url, {"items": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_product_id_returns_400(self):
        """A product_id that does not exist in the DB → 400 with clear message."""
        payload = {"items": [{"product_id": 999999, "quantity": 1}]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_quantity_zero_returns_400(self):
        """quantity=0 violates min_value=1 → 400."""
        payload = {"items": [{"product_id": self.pen.pk, "quantity": 0}]}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quantity_negative_returns_400(self):
        """quantity=-1 violates min_value=1 → 400."""
        payload = {"items": [{"product_id": self.pen.pk, "quantity": -1}]}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_product_id_field_returns_400(self):
        """Omitting product_id field entirely → 400."""
        payload = {"items": [{"quantity": 2}]}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_quantity_field_returns_400(self):
        """Omitting quantity field entirely → 400."""
        payload = {"items": [{"product_id": self.pen.pk}]}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_total_cost_is_sum_of_box_costs(self):
        """total_cost in response equals the sum of individual box costs."""
        payload = {
            "items": [
                {"product_id": self.pen.pk, "quantity": 1},
            ]
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        computed_sum = sum(b["cost"] for b in data["boxes"])
        self.assertAlmostEqual(float(data["total_cost"]), float(computed_sum), places=4)
