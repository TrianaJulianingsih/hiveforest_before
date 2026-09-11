from django.urls import path
from django.contrib.auth import views as auth_views
from apps.base.views.user_views import (
    CustomPasswordResetConfirmView,
    ForcePasswordChangeView,
)

urlpatterns = [
    # START - FaisalS | HF6 - Forgot Password function
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # END - FaisalS | HF6 - Forgot Password function
    # FaisalS | HF-8 - Forced Password Change function
    path(
        "force-change/", ForcePasswordChangeView.as_view(), name="password_force_change"
    ),
]
