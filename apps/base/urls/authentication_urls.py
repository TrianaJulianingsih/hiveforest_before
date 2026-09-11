from django.conf import settings
from django.urls import include, path

from apps.base.views.authentication_views import (
    AuthenticationLoginView,
    AuthenticationMFAEnrollView,
    AuthenticationMFAVerifyView,
)


urlpatterns = [
    path("login/", AuthenticationLoginView.as_view(), name="login"),
    path("login/mfa/enroll/", AuthenticationMFAEnrollView.as_view(), name="authentication_mfa_enroll"),
    path("login/mfa/", AuthenticationMFAVerifyView.as_view(), name="authentication_mfa_verify"),
]

if getattr(settings, "OIDC_ENABLED", False):
    urlpatterns.append(
        path("oidc/", include("mozilla_django_oidc.urls"))
    )
