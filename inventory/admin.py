from django.contrib import admin
from .models import Product, Box


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "length", "width", "height", "weight")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "internal_length",
        "internal_width",
        "internal_height",
        "max_weight",
        "cost",
    )
    search_fields = ("name",)
    ordering = ("cost",)
