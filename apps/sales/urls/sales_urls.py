from django.urls import path
from apps.sales.views.data_views import (
    outlet_list_view,
    outlet_ajax,
    distributor_data,
)
from apps.sales.views.territory_views import (
    region_matrix_view,
    region_matrix_update,
    area_matrix_view,
    area_matrix_update,
    
    ajax_filter_provinces,
    ajax_filter_organizations,
    ajax_filter_regions,
    ajax_filter_territory_regencies,
    territory_assignment_view,
    territory_assignment_summary_view,
    territory_assignment_assign_save,
)
from apps.sales.views.sync_views import sync_so, import_rawappso
from apps.sales.views.recon_export_views import export_so_reconciliation
from apps.sales.views.sellingout_reports_views import (
    sellingout_reports,
    sellingout_filter_options,
    sellingout_year_options,
)
from apps.sales.views.product_views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

from apps.sales.views.sales_views import (
    StockDailyDistributorListView,
    StockDailyDistributorDataView,
    StockDailyDistributorCreateView,
    StockDailyDistributorUpdateView,
    StockDailyDistributorDeleteView,
    RawMupSoListView,
    RawMupSoDataView,
    RawAplSoListView,
    RawAplSoDataView,
)
from .dashboard_urls import urlpatterns as dashboard_patterns
from .territory_urls import urlpatterns as territory_patterns
from .product_urls import urlpatterns as product_patterns

app_name = "sales"

urlpatterns = [
    path("outlets/", outlet_list_view, name="outlet_list"),
    path("outlet/ajax/", outlet_ajax, name="outlet_ajax"),
    path("distributors/", distributor_data, name="distributor_data"),
    path("sync-so/", sync_so, name="sync-so"),
    path("import/raw-app-so/", import_rawappso, name="import_rawappso"),
    path("recon/export-so/", export_so_reconciliation, name="export_so_recon"),
    path(
        "reports/selling-out",
        sellingout_reports,
        name="sellingout_reports",
    ),
    path(
        "reports/selling-out/filter-options/",
        sellingout_filter_options,
        name="sellingout_filter_options",
    ),
    path(
        "reports/selling-out/year-options/",
        sellingout_year_options,
        name="sellingout_year_options",
    ),

    # <!-- FaisalS | HF-30 - Area Matrix UI -->
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
    # History endpoints removed
    # <!-- // FaisalS | HF-30 - Area Matrix UI -->

    path("ajax/filter-provinces/", ajax_filter_provinces, name="ajax_filter_provinces"),
    path(
        "ajax/filter-organizations/",
        ajax_filter_organizations,
        name="ajax_filter_organizations",
    ),
    path("ajax/filter-regions/", ajax_filter_regions, name="ajax_filter_regions"),
    path(
        "ajax/filter-territory-regencies/",
        ajax_filter_territory_regencies,
        name="ajax_filter_territory_regencies",
    ),

    # <!-- FaisalS | Product Module URLs -->
    path("product-module/product/", ProductListView.as_view(), name="product_list"),
    path(
        "product-module/product/add/", ProductCreateView.as_view(), name="product_add"
    ),
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
    # <!-- // FaisalS | Product Module URLs -->
    
    # <!-- FaisalS | Stock Daily Distributor Module URLs -->
    path(
        "sales-module/stock-daily-distributor/",
        StockDailyDistributorListView.as_view(),
        name="stock_daily_distributor_list",
    ),
    path(
        "sales-module/stock-daily-distributor/data/",
        StockDailyDistributorDataView.as_view(),
        name="stock_daily_distributor_data",
    ),
    
    # Raw MUP-SO Module URLs
    path(
        "sales-module/raw-mu-so/",
        RawMupSoListView.as_view(),
        name="raw_mup_so_list",
    ),
    path(
        "sales-module/raw-mu-so/data/",
        RawMupSoDataView.as_view(),
        name="raw_mup_so_data",
    ),

    # Raw APL-SO Module URLs
    path(
        "sales-module/raw-apl-so/",
        RawAplSoListView.as_view(),
        name="raw_apl_so_list",
    ),
    path(
        "sales-module/raw-apl-so/data/",
        RawAplSoDataView.as_view(),
        name="raw_apl_so_data",
    ),
    # <!-- // FaisalS | Raw APL-SO Module URLs -->
    
    path(
        "territory/territory-assignment/",
        territory_assignment_view,
        name="territory_assignment",
    ), # FaisalS | Territory Assignment Module URLs
    path(
        "territory/territory-assignment/summary/",
        territory_assignment_summary_view,
        name="territory_assignment_summary",
    ),
    path(
        "territory/territory-assignment/assign/save/",
        territory_assignment_assign_save,
        name="territory_assignment_assign_save",
    ),
]

urlpatterns += dashboard_patterns + territory_patterns + product_patterns

