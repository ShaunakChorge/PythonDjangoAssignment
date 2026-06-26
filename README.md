# AI-Assisted Box Selection System

A Django + Django REST Framework backend that recommends the optimal shipping
box(es) for an ecommerce order using a greedy, volume/weight-budget heuristic.

---

## Overview

Given an order of products (each with L × W × H dimensions and weight), the
system picks the fewest, cheapest boxes that can physically contain all items.

Key design choices:
- **6-rotation fit check**: tries all axis-aligned orientations of each product.
- **Scalar volume budget**: not true 3D spatial bin-packing (intentional simplification).
- **Greedy heuristic**: sort by volume descending → place into cheapest open box that fits → open cheapest viable box type if none open works.
- **Pure-Python algorithm**: `packing/` has zero Django imports — independently unit-testable.

---

## Requirements

- Python 3.12+
- pip

---

## Setup

```bash
# 1. Clone / enter the project directory
cd "Assignment - PythonDjango (Tradexa)"

# 2. (Recommended) Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations (creates DB + seeds 5 boxes and 8 products)
python manage.py migrate

# 5. (Optional) Create a superuser to browse the admin
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`.
The Django admin is at `http://127.0.0.1:8000/admin/`.

---

## API Reference

### `GET /api/products/`

Returns all products in the database.

**Response 200**
```json
[
  {
    "id": 1,
    "name": "Pen",
    "length": "14.0000",
    "width": "1.0000",
    "height": "1.0000",
    "weight": "0.0500"
  }
]
```

---

### `GET /api/boxes/`

Returns all box types in the database.

**Response 200**
```json
[
  {
    "id": 1,
    "name": "Tiny",
    "internal_length": "15.0000",
    "internal_width": "10.0000",
    "internal_height": "10.0000",
    "max_weight": "2.0000",
    "cost": "1.5000"
  }
]
```

---

### `POST /api/recommend-box/`

Recommends boxes for an order.

**Request body**
```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

**Validation rules**
| Rule | HTTP response |
|---|---|
| `items` key missing | 400 |
| `items` is an empty list | 400 |
| `product_id` missing | 400 |
| `quantity` missing | 400 |
| `quantity < 1` | 400 |
| `product_id` not in DB | 400 |
| Product too large for any box | 400 |

**Success response 200**
```json
{
  "boxes": [
    {
      "box_name": "Small",
      "cost": 2.5,
      "items": [
        { "product_name": "Pen", "quantity": 2 },
        { "product_name": "Coffee Mug", "quantity": 1 }
      ]
    }
  ],
  "total_cost": 2.5
}
```

**Error response 400**
```json
{
  "error": "Product 'GiantItem' cannot fit in any available box in any orientation. It cannot be shipped."
}
```

**Example curl**
```bash
curl -s -X POST http://127.0.0.1:8000/api/recommend-box/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]}'
```

---

## Running Tests

```bash
# Run all tests with verbose output
python manage.py test tests --verbosity=2

# Run only algorithm unit tests (no DB needed but Django sets up anyway)
python manage.py test tests.test_algorithm --verbosity=2

# Run only API integration tests
python manage.py test tests.test_api --verbosity=2

# Capture full output to a file (PowerShell)
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt

# Capture full output to a file (bash/zsh)
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt
```

Test output is also committed to the repo as [`TEST_OUTPUT.md`](./TEST_OUTPUT.md).

---

## Project Structure

```
boxselector/          Django project package (settings, urls, wsgi)
inventory/            Models (Product, Box, Order, OrderItem), admin, migrations, serializers
packing/              Pure-Python algorithm (no Django imports)
  ├── models.py       Dataclasses: ProductSpec, BoxSpec, BoxResult, PackingResult, PackingError
  └── algorithm.py    fits_in_box(), pack_order()
api/                  DRF views and URL routing
tests/
  ├── test_algorithm.py   Unit tests (no DB)
  └── test_api.py         Integration tests (with DB)
manage.py
requirements.txt
README.md
TEST_OUTPUT.md        Committed test run output
```

---

## Algorithm Notes

The greedy heuristic is a deliberate simplification of the bin-packing problem:

1. **Rotation check** (`fits_in_box`): tries all 6 axis-aligned permutations of the
   product's L/W/H against the box's internal dimensions. Returns `True` if any
   rotation satisfies all three `product_dim ≤ box_dim` constraints.

2. **Greedy assignment** (`pack_order`):
   - Expands each order item by quantity into individual units.
   - Sorts units by volume (largest first).
   - For each unit, finds the cheapest already-open box where the unit fits
     (rotation + remaining scalar volume + remaining weight budget). On cost
     ties, prefers the box with least remaining volume (tightest fit).
   - If no open box works, opens the cheapest box type that can fit the unit.
   - If no box type fits the unit at all, returns a `PackingError` with the
     product name — no exception is raised.

3. **Not 3D bin-packing**: remaining capacity is tracked as a scalar volume
   budget, not a 3D spatial grid. This is intentional.
