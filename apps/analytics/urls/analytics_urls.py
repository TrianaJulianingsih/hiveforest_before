from django.urls import path

from apps.analytics.views.iqvia_growthviews import (
    iqvia_growth,
    iqvia_growth_data,
    iqvia_growth_export,
)

from apps.analytics.views.iqvia_marketshareviews import (
    iqvia_marketshare,
    iqvia_share_data,
    iqvia_share_export,
)

from apps.analytics.views.iqvia_trendlineviews import (
    iqvia_options,
    iqvia_trend_data,
    iqvia_trend_export,
    iqvia_trendline,
)

from apps.analytics.views.iqvia_importviews import (
    iqvia_import_cancel,
    iqvia_import_commit,
    iqvia_import_data,
    iqvia_import_discard,
    iqvia_import_export,
    iqvia_import_history,
    iqvia_import_menu,
    iqvia_import_upload,
)

app_name = "analytics"

urlpatterns = [
    # <!-- Akram | IQVIA Import Module URLs -->
    path("iqvia/import-menu", iqvia_import_menu, name="iqvia_import_menu"),
    path("iqvia/import-data", iqvia_import_data, name="iqvia_import_data"),
    path("iqvia/import-upload", iqvia_import_upload, name="iqvia_import_upload"),
    path("iqvia/import-commit", iqvia_import_commit, name="iqvia_import_commit"),
    path("iqvia/import-cancel", iqvia_import_cancel, name="iqvia_import_cancel"),
    path("iqvia/import-discard", iqvia_import_discard, name="iqvia_import_discard"),
    path("iqvia/import-history", iqvia_import_history, name="iqvia_import_history"),
    path("iqvia/import-export", iqvia_import_export, name="iqvia_import_export"),
    # <!-- // Akram | IQVIA Import Module URLs -->

    # <!-- Akram | IQVIA Report Module URLs -->
    path("iqvia/trendline", iqvia_trendline, name="iqvia_trendline"),
    path("iqvia/options", iqvia_options, name="iqvia_options"),
    path("iqvia/trend-data", iqvia_trend_data, name="iqvia_trend_data"),
    path("iqvia/trend-export", iqvia_trend_export, name="iqvia_trend_export"),
    path("iqvia/market-share", iqvia_marketshare, name="iqvia_marketshare"),
    path("iqvia/share-data", iqvia_share_data, name="iqvia_share_data"),
    path("iqvia/share-export", iqvia_share_export, name="iqvia_share_export"),
    path("iqvia/growth", iqvia_growth, name="iqvia_growth"),
    path("iqvia/growth-data", iqvia_growth_data, name="iqvia_growth_data"),
    path("iqvia/growth-export", iqvia_growth_export, name="iqvia_growth_export"),
    # <!-- // Akram | IQVIA Report Module URLs -->
]