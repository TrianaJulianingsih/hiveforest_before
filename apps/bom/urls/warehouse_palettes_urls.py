from django.urls import path
from apps.bom.views.warehouse_palettes_views import (
    WarehousePaletteListView,
    WarehousePaletteCreateView,
    WarehousePaletteUpdateView,
    WarehousePaletteDeleteView,
)

urlpatterns = [
    path("", WarehousePaletteListView.as_view(), name="warehouse_palette_list"),
    path("add/", WarehousePaletteCreateView.as_view(), name="warehouse_palette_add"),
    path(
        "<int:pk>/edit/",
        WarehousePaletteUpdateView.as_view(),
        name="warehouse_palette_edit",
    ),
    path(
        "<int:pk>/delete/",
        WarehousePaletteDeleteView.as_view(),
        name="warehouse_palette_delete",
    ),
]
