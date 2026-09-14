from django.urls import path
from apps.sales.views.territory_views import (
    region_matrix_view,
    region_matrix_update,
    area_matrix_view,
    area_matrix_update,
    ajax_filter_provinces,
    ajax_filter_organizations,
    ajax_filter_regions,
)

urlpatterns = [
    path("territory/region-matrix/", region_matrix_view, name="region_matrix"),
    path(
        "territory/region-matrix/update/",
        region_matrix_update,
        name="region_matrix_update",
    ),
    path("territory/area-matrix/", area_matrix_view, name="area_matrix"),
    path(
        "territory/area-matrix/update/", area_matrix_update, name="area_matrix_update"
    ),
    path("ajax/filter-provinces/", ajax_filter_provinces, name="ajax_filter_provinces"),
    path(
        "ajax/filter-organizations/",
        ajax_filter_organizations,
        name="ajax_filter_organizations",
    ),
    path("ajax/filter-regions/", ajax_filter_regions, name="ajax_filter_regions"),
]
