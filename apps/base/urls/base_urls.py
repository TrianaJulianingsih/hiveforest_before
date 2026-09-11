from django.urls import path
from apps.base.views.missing_data import download_missing_data
from apps.base.views.console import translation_console
from apps.base.views.version_views import version_history, admin_version_history

urlpatterns = [
    path("download_missing_data/", download_missing_data, name="download_missing_data"),
    path("translations/", translation_console, name="translation_console"),
    path(
        "version-history/", version_history, name="version_history"
    ),  # FaisalS | Version History App
]
