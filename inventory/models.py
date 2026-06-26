from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    """A product with physical dimensions and weight."""

    name = models.CharField(max_length=200)
    length = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    width = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    height = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    weight = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.length}×{self.width}×{self.height} cm, {self.weight} kg)"


class Box(models.Model):
    """A shipping box with internal dimensions, weight capacity, and cost."""

    name = models.CharField(max_length=200)
    internal_length = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    internal_width = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    internal_height = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    max_weight = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    cost = models.DecimalField(
        max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )

    class Meta:
        ordering = ["cost"]

    def __str__(self):
        return (
            f"{self.name} ({self.internal_length}×{self.internal_width}×"
            f"{self.internal_height} cm, max {self.max_weight} kg, ${self.cost})"
        )


class Order(models.Model):
    """A customer order (no customer info needed per spec)."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} @ {self.created_at:%Y-%m-%d %H:%M}"


class OrderItem(models.Model):
    """A line item in an order: a product and its quantity."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity}× {self.product.name} (Order #{self.order_id})"
