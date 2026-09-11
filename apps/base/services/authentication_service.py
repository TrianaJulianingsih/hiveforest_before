from apps.base.services.entra_service import get_microsoft_login_url, is_oidc_available
from apps.base.services.setting_service import get_authentication_setting


def get_login_context():
    setting = get_authentication_setting()
    microsoft_available = setting.enable_microsoft_login and is_oidc_available()
    return {
        "auth_setting": setting,
        "show_local_login": setting.enable_local_login,
        "show_microsoft_login": setting.enable_microsoft_login,
        "microsoft_login_url": get_microsoft_login_url(),
        "microsoft_login_available": microsoft_available,
    }
