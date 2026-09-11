from django.shortcuts import render
from apps.base.models.version import AppVersion
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from apps.base.models.permissions import CMSPermission

# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════


@login_required
def version_history(request):
    versions = AppVersion.objects.prefetch_related("features").all()
    current_version = AppVersion.get_current_version()

    context = {
        "versions": versions,
        "current_version": current_version,
        "page_title": "Version History",
    }

    return render(request, "base/version_history.html", context)



@login_required
def admin_version_history(request):
    # # Cek permission admin (akses menu admin)
    # if not CMSPermission.has_permission(request.user, menu="admin_version_history"):
    #     raise PermissionDenied("You do not have permission to access this page.")

    versions = AppVersion.objects.prefetch_related("features").all()
    current_version = AppVersion.get_current_version()

    context = {
        "versions": versions,
        "current_version": current_version,
        "page_title": "Version History",
    }

    return render(request, "admin/base/version_history.html", context)
