"""
inventory/migrations/0002_seed_data.py
--------------------------------------
Data migration: seeds 5 box types and 8 products so the app is immediately
usable after `python manage.py migrate`.

Products are deliberately varied to exercise algorithm edge cases:
  - Tablet (26 cm) is longer than the Small box (25 cm) → forces Medium+.
  - Yoga Mat (62 cm) fits only in Large or XL.
  - Small Appliance (8.5 kg) is too heavy for Small/Medium (5/15 kg cap).
"""

from django.db import migrations


BOXES = [
    # (name, internal_length, internal_width, internal_height, max_weight, cost)
    ("Tiny",   15,  10,  10,  2,  1.50),
    ("Small",  25,  20,  15,  5,  2.50),
    ("Medium", 40,  30,  25, 15,  4.00),
    ("Large",  60,  45,  35, 30,  6.50),
    ("XL",     80,  60,  50, 50,  9.00),
]

PRODUCTS = [
    # (name, length, width, height, weight)
    ("Pen",             14,  1,  1, 0.05),
    ("Notebook",        22, 17,  3, 0.40),
    ("Coffee Mug",      12, 12, 10, 0.35),
    ("Hardcover Book",  24, 16,  4, 0.80),
    ("Tablet",          26, 18,  1, 0.60),   # longer than Small box (25 cm)
    ("Sneakers",        35, 22, 14, 1.20),
    ("Small Appliance", 45, 30, 28, 8.50),
    ("Yoga Mat",        62, 16, 16, 2.00),   # only fits Large / XL
]


def seed_data(apps, schema_editor):
    Box = apps.get_model("inventory", "Box")
    Product = apps.get_model("inventory", "Product")

    for name, il, iw, ih, mw, cost in BOXES:
        Box.objects.create(
            name=name,
            internal_length=il,
            internal_width=iw,
            internal_height=ih,
            max_weight=mw,
            cost=cost,
        )

    for name, length, width, height, weight in PRODUCTS:
        Product.objects.create(
            name=name,
            length=length,
            width=width,
            height=height,
            weight=weight,
        )


def remove_seed_data(apps, schema_editor):
    """Reverse migration: remove seeded records only."""
    Box = apps.get_model("inventory", "Box")
    Product = apps.get_model("inventory", "Product")
    box_names = [row[0] for row in BOXES]
    product_names = [row[0] for row in PRODUCTS]
    Box.objects.filter(name__in=box_names).delete()
    Product.objects.filter(name__in=product_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=remove_seed_data),
    ]
