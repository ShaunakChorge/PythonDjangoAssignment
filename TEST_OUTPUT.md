# Test Output

Full output of `python manage.py test tests --verbosity=2` captured on 2026-06-26.

```
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 27 test(s).
Operations to perform:
  Synchronize unmigrated apps: api, messages, rest_framework, staticfiles
  Apply all migrations: admin, auth, contenttypes, inventory, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying inventory.0001_initial... OK
  Applying inventory.0002_seed_data... OK
test_boxes_list_has_expected_fields (tests.test_api.BoxListAPITest.test_boxes_list_has_expected_fields)
Each box entry has the required fields. ... ok
test_boxes_list_returns_200 (tests.test_api.BoxListAPITest.test_boxes_list_returns_200)
Endpoint returns HTTP 200. ... ok
test_boxes_list_returns_seeded_data (tests.test_api.BoxListAPITest.test_boxes_list_returns_seeded_data)
At least 5 boxes exist after migrations run. ... ok
test_products_list_has_expected_fields (tests.test_api.ProductListAPITest.test_products_list_has_expected_fields)
Each product entry has the required fields. ... ok
test_products_list_returns_200 (tests.test_api.ProductListAPITest.test_products_list_returns_200)
Endpoint returns HTTP 200. ... ok
test_products_list_returns_seeded_data (tests.test_api.ProductListAPITest.test_products_list_returns_seeded_data)
At least 8 products exist after migrations run. ... ok
test_empty_items_list_returns_400 (tests.test_api.RecommendBoxAPITest.test_empty_items_list_returns_400)
Request body with an empty 'items' list -> 400. ... ok
test_missing_items_key_returns_400 (tests.test_api.RecommendBoxAPITest.test_missing_items_key_returns_400)
Request body missing the 'items' key -> 400. ... ok
test_missing_product_id_field_returns_400 (tests.test_api.RecommendBoxAPITest.test_missing_product_id_field_returns_400)
Omitting product_id field entirely -> 400. ... ok
test_missing_quantity_field_returns_400 (tests.test_api.RecommendBoxAPITest.test_missing_quantity_field_returns_400)
Omitting quantity field entirely -> 400. ... ok
test_no_fit_returns_400_with_error_key (tests.test_api.RecommendBoxAPITest.test_no_fit_returns_400_with_error_key)
A product that cannot fit in any box returns HTTP 400 with an 'error' key. ... ok
test_quantity_negative_returns_400 (tests.test_api.RecommendBoxAPITest.test_quantity_negative_returns_400)
quantity=-1 violates min_value=1 -> 400. ... ok
test_quantity_zero_returns_400 (tests.test_api.RecommendBoxAPITest.test_quantity_zero_returns_400)
quantity=0 violates min_value=1 -> 400. ... ok
test_total_cost_is_sum_of_box_costs (tests.test_api.RecommendBoxAPITest.test_total_cost_is_sum_of_box_costs)
total_cost in response equals the sum of individual box costs. ... ok
test_unknown_product_id_returns_400 (tests.test_api.RecommendBoxAPITest.test_unknown_product_id_returns_400)
A product_id that does not exist in the DB -> 400 with clear message. ... ok
test_valid_order_returns_200_and_correct_structure (tests.test_api.RecommendBoxAPITest.test_valid_order_returns_200_and_correct_structure)
A valid order with shippable items returns 200 and the expected structure. ... ok
test_does_not_fit_any_rotation (tests.test_algorithm.TestFitsInBox.test_does_not_fit_any_rotation)
A product that is too large in every orientation should not fit. ... ok
test_fits_after_rotation (tests.test_algorithm.TestFitsInBox.test_fits_after_rotation)
Product (L=3, W=1, H=4) does NOT fit in a 4x4x2 box in its default ... ok
test_fits_exact_dimensions (tests.test_algorithm.TestFitsInBox.test_fits_exact_dimensions)
Product with the exact same dimensions as the box should fit. ... ok
test_fits_smaller (tests.test_algorithm.TestFitsInBox.test_fits_smaller)
Product clearly smaller than box fits without rotation. ... ok
test_one_dimension_too_large (tests.test_algorithm.TestFitsInBox.test_one_dimension_too_large)
Product fits in two dimensions but not the third, in any rotation. ... ok
test_empty_order (tests.test_algorithm.TestPackOrder.test_empty_order)
An empty items list should return a PackingResult with no boxes and zero cost. ... ok
test_greedy_prefers_cheapest_box (tests.test_algorithm.TestPackOrder.test_greedy_prefers_cheapest_box)
When an item fits in multiple already-open boxes with different costs, ... ok
test_pack_no_box_fits (tests.test_algorithm.TestPackOrder.test_pack_no_box_fits)
A product larger than all boxes should return PackingError, not raise an exception. ... ok
test_pack_single_box (tests.test_algorithm.TestPackOrder.test_pack_single_box)
Two small items that together fit in one Small box (volume + weight). ... ok
test_pack_two_boxes_volume (tests.test_algorithm.TestPackOrder.test_pack_two_boxes_volume)
Items whose combined volume exceeds a Small box must spill into a second box. ... ok
test_pack_two_boxes_weight (tests.test_algorithm.TestPackOrder.test_pack_two_boxes_weight)
Items that fit by volume in one Small box but exceed its weight limit ... ok
----------------------------------------------------------------------
Ran 27 tests in 0.046s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```

**Result: 27 passed, 0 failures, 0 errors, 0 warnings.**

| Test Module | Tests | Result |
|---|---|---|
| `tests.test_api.BoxListAPITest` | 3 | ✅ All pass |
| `tests.test_api.ProductListAPITest` | 3 | ✅ All pass |
| `tests.test_api.RecommendBoxAPITest` | 10 | ✅ All pass |
| `tests.test_algorithm.TestFitsInBox` | 5 | ✅ All pass |
| `tests.test_algorithm.TestPackOrder` | 6 | ✅ All pass |

**Total: 27 / 27**

---

To reproduce this output yourself:

```bash
# Windows PowerShell
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt

# bash/zsh
python manage.py test tests --verbosity=2 2>&1 | tee test_output.txt
```
