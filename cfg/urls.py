from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView

from apps.base import apps
from apps.base.views.version_views import admin_version_history
from . import views
from apps.base.views.profileview import profile_view
from apps.base.views.user_views import CustomPasswordChangeView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from apps.base.admin import admin
from .views import custom_404
from django.conf.urls import handler404
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from apps.humancapital.views.assignment_view import Ajax as AssignmentAjax
from apps.humancapital.views.organization_view import Ajax as OrganizationAjax
from apps.humancapital.views.position_view import Ajax as PositionAjax
from apps.humancapital.views.humancapital_view import organogram as OrganogramView
from apps.base.views.authentication_views import AuthenticationAdminLoginView


def admin_redirect(request):
    if not request.user.is_authenticated:
        return redirect(f"/login/?next={request.path}")
    # Redirect to 'next' if provided, otherwise go to /admin/
    next_url = request.GET.get("next", "/admin/")
    return redirect(next_url)


handler404 = custom_404

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "summernote/", include("django_summernote.urls")
    ),  # FaisalS | Version History App
    path("humancapital/assignment/ajax/", AssignmentAjax.as_view(), name="assignment-ajax-fallback"),
    path("humancapital/organization/ajax/", OrganizationAjax.as_view(), name="organization-ajax-fallback"),
    path("humancapital/position/ajax/", PositionAjax.as_view(), name="position-ajax-fallback"),
    path("humancapital/organogram/", OrganogramView, name="organogram-fallback"),
    path("api/v1/crm/", include("apps.crm.api.urls")),
]
urlpatterns += i18n_patterns(
    path("admin/login/", AuthenticationAdminLoginView.as_view(), name="admin_login"),
    path(
        "admin/base/version-history/",
        admin_version_history,
        name="admin_version_history",
    ),  # FaisalS | Version History App
    path("admin/", admin.site.urls),
    path("admin_redirect/", admin_redirect),
    path("", include("apps.base.urls.authentication_urls")),
    path("", include("apps.base.urls")),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("pandas-import/", views.pandas_import, name="pandas_import"),
    path("profile/", profile_view, name="profile"),
    # path(
    #     "profile/password-change/",
    #     auth_views.PasswordChangeView.as_view(
    #         template_name="registration/password_change_form.html"
    #     ),
    path(
        "profile/password-change/",
        CustomPasswordChangeView.as_view(),
        name="password_change",
    ),  # FaisalS | Password Change
    path(
        "profile/password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),  # FaisalS | Password Change
    path("base/", include("apps.base.urls.base_urls")),
    path("supplychain/", include("apps.supplychain.urls.supplychain_urls")),
    path("bom/", include("apps.bom.urls.bom_urls")),
    path("crm/", include("apps.crm.urls.crm_urls")),
    path("sales/", include(("apps.sales.urls.sales_urls", "sales"), namespace="sales")),
    path("humancapital/", include("apps.humancapital.urls.humancapital_urls")),
    path("performance/", include("apps.performance.urls")),
    # <!-- Akram | IQVIA Report Module URLs -->
    path("analytics/", include("apps.analytics.urls.analytics_urls")),
    # <!-- // Akram | IQVIA Report Module URLs -->
    path("finance/", include("apps.finance.urls.finance_urls")),
    path(
        "users/", include("apps.base.urls.user_urls")
    ),  # FaisalS | HF-8 - Forced Password Change function
    path(
        "cms/", include("apps.cms.urls.dashboard_urls")
    ),  # FaisalS | HF-77 - Master Dashboard Iframe
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
