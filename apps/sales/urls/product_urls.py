from django.urls import path
from apps.sales.views.product_views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

urlpatterns = [
    path("product-module/product/", ProductListView.as_view(), name="product_list"),
    path("product-module/product/add/", ProductCreateView.as_view(), name="product_add"),
    path(
        "product-module/product/<int:pk>/edit/",
        ProductUpdateView.as_view(),
        name="product_edit",
    ),
    path(
        "product-module/product/<int:pk>/delete/",
        ProductDeleteView.as_view(),
        name="product_delete",
    ),
]
