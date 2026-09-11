from django.urls import path
from apps.sales.views.sales_dashboardviews import (
    sales_dashboard,
    ecatalog_dashboard,
    iqvia_itma_dashboard,
)
from apps.sales.views.sales_dataviews import (
    outlet_list_view,
    outlet_ajax,
    distributor_data,
)
from apps.sales.views.sales_territoryview import (
    region_matrix_view,
    region_matrix_update,
    area_matrix_view,
    area_matrix_update,
    ajax_filter_provinces,
    ajax_filter_organizations,
    ajax_filter_regions,
)
from apps.sales.views.sync import import_rawappso, sync_so
from apps.sales.views.recon_export import export_so_reconciliation
from apps.sales.views.sellingout_reports import (
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
)

from apps.sales.views.sales_views import (
    RawMupSoListView,
    RawMupSoDataView,
    RawAplSoListView,
    RawAplSoDataView,
)

app_name = "sales"

urlpatterns = [
    path("bi/dashboard/sales", sales_dashboard, name="sales_dashboard"),
    path("bi/dashboard/ecatalog", ecatalog_dashboard, name="ecatalog_dashboard"),
    path("bi/dashboard/iqvia_itma", iqvia_itma_dashboard, name="iqvia_itma_dashboard"),
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
    # <!-- // FaisalS | HF-30 - Area Matrix UI -->

    path("ajax/filter-provinces/", ajax_filter_provinces, name="ajax_filter_provinces"),
    path(
        "ajax/filter-organizations/",
        ajax_filter_organizations,
        name="ajax_filter_organizations",
    ),
    path("ajax/filter-regions/", ajax_filter_regions, name="ajax_filter_regions"),

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
    # path(
    #     "sales-module/stock-daily-distributor/add/",
    #     StockDailyDistributorCreateView.as_view(),
    #     name="stock_daily_distributor_add",
    # ),
    # path(
    #     "sales-module/stock-daily-distributor/<int:pk>/edit/",
    #     StockDailyDistributorUpdateView.as_view(),
    #     name="stock_daily_distributor_edit",
    # ),
    # path(
    #     "sales-module/stock-daily-distributor/<int:pk>/delete/",
    #     StockDailyDistributorDeleteView.as_view(),
    #     name="stock_daily_distributor_delete",
    # ),
    # <!-- // FaisalS | Stock Daily Distributor Module URLs -->
    # <!-- FaisalS | Raw MUP-SO Module URLs -->
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
    # <!-- // FaisalS | Raw MUP-SO Module URLs -->
    # <!-- FaisalS | Raw APL-SO Module URLs -->
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
]

urlpatterns += []
