from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.base.services.audit_service import mark_logout
from apps.base.services.user_service import get_or_create_user_authentication


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_authentication_profile(sender, instance, created, **kwargs):
    if created:
        get_or_create_user_authentication(instance)


@receiver(user_logged_out)
def capture_logout(sender, request, user, **kwargs):
    if user:
        mark_logout(request, user)
