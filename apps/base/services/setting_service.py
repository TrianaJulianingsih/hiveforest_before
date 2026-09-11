from apps.base.models.authentication_models import AuthenticationSetting


def get_authentication_setting():
    return AuthenticationSetting.get_solo()
