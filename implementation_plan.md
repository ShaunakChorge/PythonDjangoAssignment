# AI-Assisted Box Selection System — Implementation Plan

A Django + Django REST Framework backend that recommends the optimal
shipping box(es) for an ecommerce order using a greedy, volume/weight-budget
heuristic. The app seeds all reference data on first `migrate`, is immediately
usable, and ships with a full unit + API test suite.

---

## User Review Required

> [!IMPORTANT]
> This plan introduces one design decision beyond the spec: the greedy
> algorithm will track **remaining volume** as a simple scalar budget
> (sum of item volumes ≤ box internal volume). The spec explicitly says
> "NOT true 3D bin-packing," so no spatial placement grid is modelled.
> Please confirm this interpretation is correct.

> [!WARNING]
> Django's data migrations are tied to a specific app's migration history.
> The seed migration will live in the `inventory` app (see structure below).
> If you ever `migrate --run-syncdb` or squash migrations, the seed data
> will re-run. This is standard Django behaviour — just flagging it.

---

## Open Questions

> [!IMPORTANT]
> **Q1 — Python / Django version targets**: Should I pin to a specific
> version pair (e.g., Python 3.12 + Django 5.x)? Or is "latest stable" fine?

> [!IMPORTANT]
> **Q2 — Database**: SQLite (zero-config, fits an assignment) or PostgreSQL?

> [!IMPORTANT]
> **Q3 — "Remaining volume" tie-breaking**: When multiple open boxes have
> the same lowest cost *and* can fit the next item, should I pick the box
> with the *least* remaining space (tightest fit, minimises waste) or the
> *most* (most room for future items)? The spec says "lowest cost"; for
> equal cost I'll default to **least remaining space** unless you prefer
> otherwise.

> [!IMPORTANT]
> **Q4 — Multiple units of the same product, same box**: The spec says expand
> by quantity into individual units. So 3× Product A = three separate "place
> this unit" decisions. Weight check is then per-unit-placed, not per-product.
> Confirming this is the intended behaviour.

> [!IMPORTANT]
> **Q5 — Test output capture**: The spec mentions "a way to capture full
> terminal test output to a text file." I plan to document a one-liner in
> the README (`python -m pytest ... | tee test_output.txt` or
> `python manage.py test ... 2>&1 | tee test_output.txt`). Is that
> sufficient, or do you want an automated script?

---

## Proposed Folder / App Structure

```
boxselector/                    ← Django project root (manage.py lives here)
│
├── boxselector/                ← Django project package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                 ← root URL conf
│   └── wsgi.py
│
├── inventory/                  ← Django app: models, admin, migrations, seed
│   ├── migrations/
│   │   ├── 0001_initial.py     ← auto-generated schema migration
│   │   └── 0002_seed_data.py   ← data migration: 5 boxes + 8 products
│   ├── admin.py                ← registers Product & Box
│   ├── apps.py
│   ├── models.py               ← Product, Box, Order, OrderItem
│   └── serializers.py          ← ProductSerializer, BoxSerializer
│
├── packing/                    ← Pure-Python algorithm (no Django imports)
│   ├── __init__.py
│   ├── models.py               ← dataclasses: ProductSpec, BoxSpec, PlacedItem,
│   │                              BoxResult, PackingResult, PackingError
│   └── algorithm.py            ← fits_in_box(), pack_order()
│
├── api/                        ← DRF views + routing
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py                 ← /api/* URL patterns
│   └── views.py                ← RecommendBoxView, ProductListView, BoxListView
│
├── tests/
│   ├── __init__.py
│   ├── test_algorithm.py       ← unit tests for packing/algorithm.py
│   └── test_api.py             ← API integration tests
│
├── .gitignore
├── README.md
└── requirements.txt
```

**Why three apps?**
- `inventory` owns persistence (models, admin, migrations, seed data).
- `packing` is a pure-Python library — zero Django coupling, trivially
  unit-testable without a database.
- `api` owns HTTP concerns (serializers for request/response, DRF views,
  URL routing). Keeps views thin: fetch from DB → convert to dataclasses
  → call `pack_order()` → serialize result.

---

## Proposed Changes (Implementation Order)

### Phase 1 — Project Scaffolding

#### [NEW] `boxselector/` (Django project)
- `django-admin startproject boxselector .` inside the repo root.
- Configure `settings.py`: `INSTALLED_APPS`, `REST_FRAMEWORK` defaults,
  SQLite DB (or Postgres per Q2 answer).

#### [NEW] `requirements.txt`
```
django>=5.0,<6.0
djangorestframework>=3.15
```
(Pinned ranges so the assignment is reproducible.)

#### [NEW] `.gitignore`
Standard Python + Django gitignore (db.sqlite3, __pycache__, .env, etc.).

---

### Phase 2 — Data Models (`inventory`)

#### [NEW] `inventory/models.py`

| Model | Fields |
|---|---|
| `Product` | `name` (CharField), `length`, `width`, `height`, `weight` (all DecimalField, positive) |
| `Box` | `name` (CharField), `internal_length`, `internal_width`, `internal_height`, `max_weight`, `cost` (all DecimalField, positive) |
| `Order` | `created_at` (auto DateTimeField) |
| `OrderItem` | `order` (FK→Order), `product` (FK→Product), `quantity` (PositiveIntegerField) |

> [!NOTE]
> Using `DecimalField` (not `FloatField`) for all physical/monetary values to
> avoid IEEE-754 rounding surprises. The algorithm will cast to `float` at the
> boundary before doing math.

#### [NEW] `inventory/admin.py`
Register `Product` and `Box` with `list_display` showing key dimensions.

#### [NEW] `inventory/migrations/0001_initial.py`
Auto-generated by `makemigrations`.

#### [NEW] `inventory/migrations/0002_seed_data.py`
Data migration using `RunPython`. Seeds:

**5 Boxes (small → large)**

| Name | L × W × H (cm) | Max weight (kg) | Cost ($) |
|---|---|---|---|
| Tiny | 15 × 10 × 10 | 2 | 1.50 |
| Small | 25 × 20 × 15 | 5 | 2.50 |
| Medium | 40 × 30 × 25 | 15 | 4.00 |
| Large | 60 × 45 × 35 | 30 | 6.50 |
| XL | 80 × 60 × 50 | 50 | 9.00 |

**8 Products (varied sizes & weights)**

| Name | L × W × H (cm) | Weight (kg) |
|---|---|---|
| Pen | 14 × 1 × 1 | 0.05 |
| Notebook | 22 × 17 × 3 | 0.40 |
| Coffee Mug | 12 × 12 × 10 | 0.35 |
| Hardcover Book | 24 × 16 × 4 | 0.80 |
| Tablet | 26 × 18 × 1 | 0.60 |
| Sneakers | 35 × 22 × 14 | 1.20 |
| Small Appliance | 45 × 30 × 28 | 8.50 |
| Yoga Mat (rolled) | 62 × 16 × 16 | 2.00 |

> [!NOTE]
> "Tablet" (26cm) is deliberately 1 cm longer than the Small box (25cm),
> so it *only* fits in Medium or larger — good for rotation-testing.
> "Yoga Mat" exceeds all box lengths except Large and XL (62 cm), so it
> stress-tests the "find cheapest viable box" path.

---

### Phase 3 — Pure-Python Packing Library (`packing`)

#### [NEW] `packing/models.py` — Dataclasses

```python
@dataclass
class ProductSpec:
    id: int
    name: str
    length: float
    width: float
    height: float
    weight: float

@dataclass
class BoxSpec:
    id: int
    name: str
    internal_length: float
    internal_width: float
    internal_height: float
    max_weight: float
    cost: float

@dataclass
class PlacedItem:
    product_id: int
    product_name: str
    quantity: int          # always 1 here; aggregated in output

@dataclass
class BoxResult:
    box: BoxSpec
    items: list[PlacedItem]
    cost: float

@dataclass
class PackingResult:
    boxes: list[BoxResult]
    total_cost: float

@dataclass
class PackingError:
    message: str           # human-readable; names the unshippable product
```

#### [NEW] `packing/algorithm.py` — Core Logic

**`fits_in_box(product: ProductSpec, box: BoxSpec) -> bool`**
- Generates all 6 axis-aligned permutations of `(L, W, H)`.
- Returns `True` if any permutation satisfies
  `pL ≤ bL and pW ≤ bW and pH ≤ bH`.

**`pack_order(items: list[tuple[ProductSpec, int]], boxes: list[BoxSpec]) -> PackingResult | PackingError`**

```
Step 1  Expand items by quantity → flat list of ProductSpec units.
Step 2  Sort units by volume (L×W×H) descending.
Step 3  Initialise open_boxes = []
        Each entry: { box_spec, remaining_volume, remaining_weight, placed[] }
Step 4  For each unit u:
          candidates = [ob for ob in open_boxes
                        if fits_in_box(u, ob.box_spec)   ← rotation check
                        and u.volume <= ob.remaining_volume
                        and u.weight <= ob.remaining_weight]
          if candidates:
              pick = min(candidates, key=lambda ob: (ob.box_spec.cost,
                                                     ob.remaining_volume))
              place u in pick; decrement remaining_volume and remaining_weight
          else:
              viable = [b for b in boxes if fits_in_box(u, b)]
              if not viable:
                  return PackingError(f"Product '{u.name}' cannot fit …")
              new_box = min(viable, key=lambda b: b.cost)
              open new_box entry; place u; decrement budgets
Step 5  Convert open_boxes → BoxResult list; sum costs → PackingResult
```

> [!NOTE]
> The "remaining volume" check uses scalar volume budget, NOT spatial
> placement. This is the intentional simplification stated in the spec.

---

### Phase 4 — REST API (`api`)

#### [NEW] `inventory/serializers.py`

- `ProductSerializer` — all fields, read-only.
- `BoxSerializer` — all fields, read-only.
- `OrderItemInputSerializer` — `product_id` (int), `quantity` (int ≥ 1).
- `RecommendBoxRequestSerializer` — `items: list[OrderItemInputSerializer]`.
- `PlacedItemOutputSerializer`, `BoxResultOutputSerializer`,
  `PackingResultOutputSerializer` — nested output shape.

#### [NEW] `api/views.py`

| View | Method | Endpoint | Logic |
|---|---|---|---|
| `ProductListView` | GET | `/api/products/` | `Product.objects.all()` → serializer |
| `BoxListView` | GET | `/api/boxes/` | `Box.objects.all()` → serializer |
| `RecommendBoxView` | POST | `/api/recommend-box/` | validate input → fetch DB objects → convert to dataclasses → `pack_order()` → serialize or return 400 |

**`POST /api/recommend-box/` — request body**
```json
{
  "items": [
    { "product_id": 3, "quantity": 2 },
    { "product_id": 7, "quantity": 1 }
  ]
}
```

**Success response (200)**
```json
{
  "boxes": [
    {
      "box_name": "Medium",
      "cost": "4.00",
      "items": [
        { "product_name": "Coffee Mug", "quantity": 2 },
        { "product_name": "Notebook",   "quantity": 1 }
      ]
    }
  ],
  "total_cost": "4.00"
}
```

**Error response (400)**
```json
{
  "error": "Product 'Yoga Mat (rolled)' cannot fit in any available box."
}
```

#### [NEW] `api/urls.py` + `boxselector/urls.py`
Wire `/api/` to `api.urls`.

---

### Phase 5 — Tests

#### [NEW] `tests/test_algorithm.py` — Unit Tests (no DB)

| Test | Covers |
|---|---|
| `test_fits_exact_dimensions` | Product fits without rotation |
| `test_fits_after_rotation` | Product only fits after rotating (e.g., 1×5×3 into a 4×4×2 box) |
| `test_does_not_fit_any_rotation` | Product is too large in all orientations |
| `test_pack_single_box` | Small order fits entirely in one box |
| `test_pack_two_boxes_volume` | Order volume exceeds one box → two boxes used |
| `test_pack_two_boxes_weight` | Weight limit forces a second box even when volume would fit |
| `test_pack_no_box_fits` | A product exceeds all boxes → returns `PackingError`, no exception |
| `test_greedy_prefers_cheapest_box` | Among eligible open boxes, cheapest is chosen |

#### [NEW] `tests/test_api.py` — API Integration Tests (Django TestCase + DRF APIClient)

| Test | Covers |
|---|---|
| `test_products_list` | GET `/api/products/` → 200, returns ≥ 8 items |
| `test_boxes_list` | GET `/api/boxes/` → 200, returns ≥ 5 items |
| `test_recommend_valid_order` | POST with shippable items → 200 + valid structure |
| `test_recommend_no_fit_error` | POST with product too large → 400 + `"error"` key |
| `test_recommend_invalid_input` | POST with malformed body → 400 |

---

### Phase 6 — Deliverables

#### [NEW] `README.md`
Sections:
1. **Overview** — what the project does
2. **Setup** — `pip install -r requirements.txt`, `migrate`, `runserver`
3. **API Reference** — endpoint table with sample curl commands
4. **Running Tests** — `python manage.py test tests` and the tee one-liner:
   ```bash
   python manage.py test tests 2>&1 | tee test_output.txt
   ```
5. **Algorithm Notes** — brief description of the greedy heuristic and
   its deliberate limitations

---

## Implementation Order Summary

```
1. Scaffold project + requirements.txt + .gitignore
2. inventory app: models → makemigrations → admin
3. inventory app: seed data migration (0002_seed_data.py)
4. packing library: dataclasses → algorithm
5. Unit tests for packing (Phase 5 test_algorithm.py) — run & pass before touching DRF
6. inventory serializers + api app: views + URLs
7. API tests (Phase 5 test_api.py)
8. README.md
9. Final end-to-end smoke test
```

---

## Verification Plan

### Automated Tests
```bash
# Run full suite and capture to file
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt
```

Expected: all tests pass, zero errors, zero failures.

### Manual Verification
- Browse `http://127.0.0.1:8000/admin/` — confirm Product and Box models
  are visible and seeded.
- `GET http://127.0.0.1:8000/api/products/` — 8 products returned.
- `GET http://127.0.0.1:8000/api/boxes/` — 5 boxes returned.
- `POST http://127.0.0.1:8000/api/recommend-box/` with a valid multi-item
  body — confirm box breakdown and total cost.
- `POST` with a product whose dimensions exceed all boxes — confirm 400 +
  human-readable error message.
