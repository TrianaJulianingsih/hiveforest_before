from .dashboard_views import sales_dashboard, ecatalog_dashboard, iqvia_itma_dashboard
from .data_views import outlet_list_view, distributor_data, outlet_ajax
from .territory_views import (
    region_matrix_view,
    region_matrix_update,
    area_matrix_view,
    area_matrix_update,
    ajax_filter_provinces,
    ajax_filter_organizations,
    ajax_filter_regions,
)
from .sync_views import sync_so
from .product_views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)
from .sales_views import (
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

__all__ = [
    "sales_dashboard",
    "ecatalog_dashboard",
    "iqvia_itma_dashboard",
    "outlet_list_view",
    "distributor_data",
    "outlet_ajax",
    "region_matrix_view",
    "region_matrix_update",
    "area_matrix_view",
    "area_matrix_update",
    "ajax_filter_provinces",
    "ajax_filter_organizations",
    "ajax_filter_regions",
    "sync_so",
    "ProductListView",
    "ProductCreateView",
    "ProductUpdateView",
    "ProductDeleteView",
    "StockDailyDistributorListView",
    "StockDailyDistributorDataView",
    "StockDailyDistributorCreateView",
    "StockDailyDistributorUpdateView",
    "StockDailyDistributorDeleteView",
    "RawMupSoListView",
    "RawMupSoDataView",
    "RawAplSoListView",
    "RawAplSoDataView",
]
