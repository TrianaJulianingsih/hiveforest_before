from importlib.util import find_spec

from django.urls import NoReverseMatch, reverse


def is_oidc_available():
    return find_spec("mozilla_django_oidc") is not None


def get_microsoft_login_url():
    if not is_oidc_available():
        return ""
    try:
        return reverse("oidc_authentication_init")
    except NoReverseMatch:
        return ""
