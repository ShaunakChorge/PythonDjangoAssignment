"""
api/views.py
------------
Three thin DRF views:
  - ProductListView  — GET /api/products/
  - BoxListView      — GET /api/boxes/
  - RecommendBoxView — POST /api/recommend-box/

RecommendBoxView validates input with DRF serializers, converts DB objects to
pure-Python dataclasses, calls pack_order(), then serializes the result.
All validation errors return 400 with a clear JSON body.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Box, Product
from inventory.serializers import (
    BoxResultOutputSerializer,
    BoxSerializer,
    PackingResultOutputSerializer,
    ProductSerializer,
    RecommendBoxRequestSerializer,
)
from packing.algorithm import pack_order
from packing.models import BoxSpec, PackingError, ProductSpec


class ProductListView(APIView):
    """GET /api/products/ — returns all products."""

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class BoxListView(APIView):
    """GET /api/boxes/ — returns all box types."""

    def get(self, request):
        boxes = Box.objects.all()
        serializer = BoxSerializer(boxes, many=True)
        return Response(serializer.data)


class RecommendBoxView(APIView):
    """
    POST /api/recommend-box/

    Request body:
        { "items": [{ "product_id": <int>, "quantity": <int> }, ...] }

    Success (200):
        { "boxes": [...], "total_cost": <float> }

    Errors (400):
        - Missing or invalid fields
        - quantity < 1
        - unknown product_id
        - product too large to ship
    """

    def post(self, request):
        # --- 1. Validate input ---
        input_serializer = RecommendBoxRequestSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {"error": input_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_items = input_serializer.validated_data["items"]

        # --- 2. Fetch DB objects ---
        product_ids = [item["product_id"] for item in validated_items]
        products_qs = Product.objects.filter(pk__in=product_ids)
        products_map = {p.pk: p for p in products_qs}

        all_boxes = Box.objects.all()

        # --- 3. Convert to pure-Python dataclasses ---
        packing_items: list[tuple[ProductSpec, int]] = []
        for item in validated_items:
            db_product = products_map[item["product_id"]]
            spec = ProductSpec(
                id=db_product.pk,
                name=db_product.name,
                length=float(db_product.length),
                width=float(db_product.width),
                height=float(db_product.height),
                weight=float(db_product.weight),
            )
            packing_items.append((spec, item["quantity"]))

        box_specs: list[BoxSpec] = [
            BoxSpec(
                id=b.pk,
                name=b.name,
                internal_length=float(b.internal_length),
                internal_width=float(b.internal_width),
                internal_height=float(b.internal_height),
                max_weight=float(b.max_weight),
                cost=float(b.cost),
            )
            for b in all_boxes
        ]

        # --- 4. Run algorithm ---
        result = pack_order(packing_items, box_specs)

        # --- 5. Serialize result ---
        if isinstance(result, PackingError):
            return Response(
                {"error": result.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = PackingResultOutputSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
