"""
inventory/serializers.py
------------------------
DRF serializers for Product, Box, and the recommend-box API.
"""

from rest_framework import serializers
from .models import Product, Box


# ---------------------------------------------------------------------------
# Read-only list serializers
# ---------------------------------------------------------------------------

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "length", "width", "height", "weight"]


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = [
            "id",
            "name",
            "internal_length",
            "internal_width",
            "internal_height",
            "max_weight",
            "cost",
        ]


# ---------------------------------------------------------------------------
# Input serializers for POST /api/recommend-box/
# ---------------------------------------------------------------------------

class OrderItemInputSerializer(serializers.Serializer):
    """Validates a single line item: product_id must exist, quantity >= 1."""

    product_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Each item must include a 'product_id'.",
            "invalid": "'product_id' must be a positive integer.",
            "min_value": "'product_id' must be a positive integer.",
        },
    )
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Each item must include a 'quantity'.",
            "invalid": "'quantity' must be a positive integer.",
            "min_value": "'quantity' must be at least 1.",
        },
    )

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Product with id={value} does not exist."
            )
        return value


class RecommendBoxRequestSerializer(serializers.Serializer):
    """Top-level request body: a non-empty list of order items."""

    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("'items' must contain at least one entry.")
        return value


# ---------------------------------------------------------------------------
# Output serializers for POST /api/recommend-box/ (success response)
# ---------------------------------------------------------------------------

class PlacedItemOutputSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()


class BoxResultOutputSerializer(serializers.Serializer):
    box_name = serializers.CharField(source="box.name")
    cost = serializers.FloatField()
    items = PlacedItemOutputSerializer(many=True)


class PackingResultOutputSerializer(serializers.Serializer):
    boxes = BoxResultOutputSerializer(many=True)
    total_cost = serializers.FloatField()
