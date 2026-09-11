from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import authentication, exceptions


class InternalServiceAuthentication(authentication.BaseAuthentication):
    """
    Authenticates server-to-server calls from hiveforest-api. The shared secret
    proves the caller is a trusted internal service; the acting user is then
    re-derived from our own DB by id (never trusted from a header claim), so
    is_staff/is_superuser checks downstream are as authoritative as any normal
    Django request.
    """

    def authenticate(self, request):
        key = request.headers.get("X-Internal-Api-Key")
        if not key:
            return None

        if not settings.INTERNAL_API_KEY or key != settings.INTERNAL_API_KEY:
            raise exceptions.AuthenticationFailed("Invalid internal API key.")

        user_id = request.headers.get("X-Acting-User-Id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Missing X-Acting-User-Id.")

        try:
            user = get_user_model().objects.get(pk=int(user_id), is_active=True)
        except (ObjectDoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed("Unknown or inactive acting user.")

        return (user, None)
