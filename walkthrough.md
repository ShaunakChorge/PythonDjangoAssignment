# Walkthrough — AI-Assisted Box Selection System

## What Was Built

A fully runnable Django 5.2 + DRF 3.17 backend implementing an AI-assisted box
selection system for an ecommerce warehouse, per the hiring assignment spec.

---

## Files Created

```
boxselector/           Django project package
  __init__.py
  settings.py          SQLite DB, DRF configured, both apps registered
  urls.py              Routes /admin/ and /api/
  wsgi.py

inventory/             Persistence layer
  __init__.py
  apps.py
  models.py            Product, Box, Order, OrderItem (DecimalField, Decimal validators)
  admin.py             Product + Box registered with list_display
  serializers.py       Input validation + read/write serializers
  migrations/
    __init__.py
    0001_initial.py    Auto-generated schema migration
    0002_seed_data.py  Seeds 5 boxes + 8 products (reversible RunPython)

packing/               Pure-Python algorithm (zero Django imports)
  __init__.py
  models.py            ProductSpec, BoxSpec, BoxResult, PackingResult, PackingError dataclasses
  algorithm.py         fits_in_box() + pack_order() greedy heuristic

api/                   HTTP layer
  __init__.py
  apps.py
  views.py             ProductListView, BoxListView, RecommendBoxView
  urls.py              /api/products/, /api/boxes/, /api/recommend-box/

tests/
  __init__.py
  test_algorithm.py    11 unit tests (no DB)
  test_api.py          16 integration tests (with DB)

manage.py
requirements.txt       django>=5.2,<6.0  djangorestframework>=3.15,<4.0
.gitignore
README.md
TEST_OUTPUT.md         Committed test output (27/27 pass)
```

---

## Algorithm Summary

**`fits_in_box(product, box)`** — uses `itertools.permutations` to try all 6
axis-aligned rotations. Returns `True` if any rotation satisfies
`p_dim ≤ b_dim` for all three axes.

**`pack_order(items, boxes)`** — greedy heuristic:
1. Expand each `(product, qty)` into individual `ProductSpec` units.
2. Sort units by volume descending.
3. For each unit, find open boxes where unit fits (rotation + remaining volume + remaining weight). Pick cheapest; break ties by tightest fit (least remaining volume).
4. If no open box works, open cheapest viable box type (by dimension only).
5. If no box type fits at all, return `PackingError` (not raise).
6. Aggregate and return `PackingResult`.

---

## API Validation

`POST /api/recommend-box/` validates at the DRF serializer layer:
- `items` key missing → 400
- `items` empty → 400
- `product_id` missing → 400
- `quantity` missing → 400
- `quantity < 1` → 400
- unknown `product_id` → 400 with specific message
- product dimensionally too large → 400 with product name in message

---

## Test Results

```
Ran 27 tests in 0.046s
OK  (27 passed, 0 failures, 0 errors, 0 warnings)
```

| Suite | Tests |
|---|---|
| `BoxListAPITest` | 3 |
| `ProductListAPITest` | 3 |
| `RecommendBoxAPITest` | 10 |
| `TestFitsInBox` | 5 |
| `TestPackOrder` | 6 |

See [TEST_OUTPUT.md](file:///d:/Library/Documents/Projects/Internship/Assignment%20-%20PythonDjango%20%28Tradexa%29/TEST_OUTPUT.md) for the full committed output.

---

## How to Run

```bash
pip install -r requirements.txt
python manage.py migrate        # also seeds boxes + products
python manage.py createsuperuser
python manage.py runserver

# Tests
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt
```

---

## Seed Data

| Box | L×W×H (cm) | Max kg | Cost |
|---|---|---|---|
| Tiny | 15×10×10 | 2 | $1.50 |
| Small | 25×20×15 | 5 | $2.50 |
| Medium | 40×30×25 | 15 | $4.00 |
| Large | 60×45×35 | 30 | $6.50 |
| XL | 80×60×50 | 50 | $9.00 |

| Product | L×W×H (cm) | Weight |
|---|---|---|
| Pen | 14×1×1 | 0.05 kg |
| Notebook | 22×17×3 | 0.40 kg |
| Coffee Mug | 12×12×10 | 0.35 kg |
| Hardcover Book | 24×16×4 | 0.80 kg |
| Tablet *(forces Medium+)* | 26×18×1 | 0.60 kg |
| Sneakers | 35×22×14 | 1.20 kg |
| Small Appliance | 45×30×28 | 8.50 kg |
| Yoga Mat *(forces Large/XL)* | 62×16×16 | 2.00 kg |
