"""
api/urls.py — URL patterns for the API app.
"""

from django.urls import path
from .views import BoxListView, ProductListView, RecommendBoxView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("boxes/", BoxListView.as_view(), name="box-list"),
    path("recommend-box/", RecommendBoxView.as_view(), name="recommend-box"),
]
