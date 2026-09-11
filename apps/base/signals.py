from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from .user_models import ForcePasswordStatus
from apps.base.models.password_policy import PasswordPolicy


# FaisalS | HF-8 - Forced Password Change function
@receiver(post_save, sender=User)
def create_force_password_status(sender, instance, created, **kwargs):
    if created:
        ForcePasswordStatus.objects.create(user=instance, must_change_password=True)


@receiver(user_logged_in)
def check_standard_password_on_login(sender, request, user, **kwargs):
    """
    When a user logs in, check if they are using a standard/default password.
    If so, force a password change.
    """
    if not user:
        return
    raw_password = None
    if request and hasattr(request, "POST"):
        raw_password = request.POST.get("password")

    is_standard = PasswordPolicy.check_user_has_standard_password(
        user, raw_password=raw_password
    )
    if is_standard:
        status, _ = ForcePasswordStatus.objects.get_or_create(user=user)
        status.must_change_password = True
        status.save()
        if request and hasattr(request, "session"):
            request.session["is_standard_password"] = True

