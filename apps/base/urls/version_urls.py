from django.urls import path
from apps.base.views.version_views import admin_version_history

# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════

urlpatterns = [
    path("", admin_version_history, name="admin_version_history"),
]
