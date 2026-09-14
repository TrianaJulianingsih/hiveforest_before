import json
from pathlib import Path
import os
from importlib.util import find_spec

import certifi
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, ".env"))
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-9zf7%3wb=q1(xd=f3d^#=qc138j#8gnxe0g4u87g=cm&j#&do!"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")


# Application definition
INSTALLED_APPS = [
    "import_export",
    "dal",
    "dal_select2",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_currentuser",
    "django_extensions",
    "widget_tweaks",
    "rolepermissions",
    "rest_framework",
    "crispy_forms",
    "crispy_bootstrap4",
    "corsheaders",
    "django_summernote",
    # Custom applications
    "apps.base",
    "apps.humancapital",
    "apps.sales",
    "apps.supplychain",
    "apps.crm",
    "apps.finance",
    "apps.analytics",
    "apps.cms.apps.CmsConfig",
    "apps.bom",
    "apps.performance.apps.PerformanceConfig",
]
if find_spec("mozilla_django_oidc") is not None:
    INSTALLED_APPS.append("mozilla_django_oidc")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "apps.base.middleware.PersistLanguageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_currentuser.middleware.ThreadLocalUserMiddleware",
    "apps.base.middleware.ForcePasswordChangeMiddleware",  # FaisalS | HF-8 - Forced Password Change function
    "apps.base.middleware.RequestProviderMiddleware",
    "apps.base.middleware.SystemLogMiddleware",
]

ROOT_URLCONF = "cfg.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.base.context_processors.has_access",
                "apps.base.context_processors.breadcrumbs",
                "apps.base.context_processors.project_settings",
                "apps.base.context_processors.version_context",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "cfg.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get(
            "DB_HIVEFOREST_ENGINE", "django.db.backends.postgresql"
        ),
        "NAME": os.environ.get("DB_HIVEFOREST_DATABASE"),
        "USER": os.environ.get("DB_HIVEFOREST_USER"),
        "PASSWORD": os.environ.get("DB_HIVEFOREST_PASSWORD"),
        "HOST": os.environ.get("DB_HIVEFOREST_HOST"),
        "PORT": os.environ.get("DB_HIVEFOREST_PORT"),
        "OPTIONS": {
            os.environ.get("DB_HIVEFOREST_OPTIONS"): os.environ.get(
                "DB_HIVEFOREST_OPTIONS_VALUE"
            )
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jakarta"
DEFAULT_LOG_TIMEZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True
DATETIME_FORMAT = "Y-m-d H:i"
USE_L10N = False  # Important: disable localization for this to take effect

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
WHITENOISE_USE_FINDERS = env_bool("WHITENOISE_USE_FINDERS", False)
# if DEBUG == False:
#     STATIC_ROOT = os.path.join(BASE_DIR, "static")
# else:
#     STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redirect users to this page after login
LOGIN_REDIRECT_URL = "/"
# Redirect users to the login page after logout
LOGOUT_REDIRECT_URL = "/login/"
# Redirect users to login page if they're not authenticated
LOGIN_URL = "/login/"

IP_CSRF_ENV = os.environ.get("IP_CSRF_ENV", "")
CSRF_TRUSTED_ORIGINS = [
    f"https://{ip.strip()}" for ip in IP_CSRF_ENV.split(",") if ip.strip()
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "verbose",
        },
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.environ.get("LOGGING_FILENAME_DJANGO", "debug.log"),
            "formatter": "verbose",
        },
    },
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000

# SESSION HANDLING
SESSION_COOKIE_AGE = int(os.environ.get("SESSION_COOKIE_AGE", str(1 * 60 * 60)))
SESSION_COOKIE_HTTPONLY = env_bool("SESSION_COOKIE_HTTPONLY", True)
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", True)

# Optional: refresh session expiry on every request
SESSION_SAVE_EVERY_REQUEST = env_bool("SESSION_SAVE_EVERY_REQUEST", True)
# Make session cookies persist even after closing the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool("SESSION_EXPIRE_AT_BROWSER_CLOSE", True)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)

APPEND_SLASH = True

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "PAGE_SIZE": 50,
}

# Shared secret for hiveforest-api's server-to-server calls into apps.crm.api -
# see apps/crm/api/authentication.py. Must match hiveforest-api's INTERNAL_API_KEY.
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")

CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap4"]
CRISPY_TEMPLATE_PACK = "bootstrap4"

PROJECT_NAME = "HiveForest"

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("id", "Indonesia"),
]
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

MODELTRANSLATION_LANGUAGES = ("en", "id")
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = {
    "default": ("en", "id"),
}
MODELTRANSLATION_PREPOPULATE_LANGUAGE = "en"
MODELTRANSLATION_ENABLE_REGISTRATIONS = True

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
# ]

# START - FaisalS | HF-6 - Forgot Password function
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' #Local testing
# DEFAULT_FROM_EMAIL = 'admin@example.com' #Local testing

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

PASSWORD_RESET_TIMEOUT = int(os.environ.get("PASSWORD_RESET_TIMEOUT", "7200"))
# END - FaisalS | HF-6 - Forgot Password function

# FaisalS | HF-8 - Forced Password Change function
FORCE_PASSWORD_EXPIRY_DAYS = int(os.environ.get("FORCE_PASSWORD_EXPIRY_DAYS", "40"))
_raw_standard_passwords = os.environ.get(
    "STANDARD_PASSWORDS",
    "password,password1,password123,password123!,p455w0rd,p455w0rd!,otsuka123,otsuka123!,otsuka@123,12345678,123456789,qwerty,letmein,admin,admin123,welcome,abc123,hiveforest123,hiveforest123!",
)
STANDARD_PASSWORDS = {p.strip().lower() for p in _raw_standard_passwords.split(",") if p.strip()}

# FaisalS | enforce HTTPS, secure cookies, and enable HSTS settings
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
if env_bool("SECURE_SSL_REDIRECT"):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)

OIDC_ENABLED = find_spec("mozilla_django_oidc") is not None
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
if OIDC_ENABLED:
    AUTHENTICATION_BACKENDS.insert(
        0,
        "apps.base.utils.authentication_utils.EntraIDOIDCAuthenticationBackend",
    )

OIDC_RP_CLIENT_ID = os.environ.get("CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
OIDC_TENANT_ID = os.environ.get("TENANT_ID", "common")
OIDC_BASE_ENDPOINT = os.environ.get(
    "OIDC_ENDPOINT",
    f"https://login.microsoftonline.com/{OIDC_TENANT_ID}/oauth2/v2.0",
).rstrip("/")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get(
    "OIDC_AUTHORIZATION_ENDPOINT",
    f"{OIDC_BASE_ENDPOINT}/authorize",
)
OIDC_OP_TOKEN_ENDPOINT = os.environ.get(
    "OIDC_TOKEN_ENDPOINT",
    f"{OIDC_BASE_ENDPOINT}/token",
)
OIDC_OP_USER_ENDPOINT = os.environ.get(
    "OIDC_USER_ENDPOINT",
    "https://graph.microsoft.com/oidc/userinfo",
)
OIDC_OP_JWKS_ENDPOINT = os.environ.get(
    "OIDC_JWKS_ENDPOINT",
    f"https://login.microsoftonline.com/{OIDC_TENANT_ID}/discovery/v2.0/keys",
)
OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO", "RS256")
OIDC_RP_SCOPES = os.environ.get("OIDC_RP_SCOPES", "openid email profile").split()
OIDC_USE_NONCE = env_bool("OIDC_USE_NONCE", True)
OIDC_STORE_ID_TOKEN = env_bool("OIDC_STORE_ID_TOKEN", True)
OIDC_VERIFY_JWT = env_bool("OIDC_VERIFY_JWT", True)
OIDC_STATE_SIZE = int(os.environ.get("OIDC_STATE_SIZE", "32"))
OIDC_NONCE_SIZE = int(os.environ.get("OIDC_NONCE_SIZE", "32"))

import sys
if 'test' in sys.argv:
    # Disable migrations for all apps to bypass migration dependency graph checks
    MIGRATION_MODULES = {
        'admin': None,
        'auth': None,
        'contenttypes': None,
        'sessions': None,
        'messages': None,
        'staticfiles': None,
        'django_currentuser': None,
        'rolepermissions': None,
        'rest_framework': None,
        'django_summernote': None,
        'import_export': None,
        'base': None,
        'humancapital': None,
        'sales': None,
        'supplychain': None,
        'crm': None,
        'finance': None,
        'analytics': None,
        'cms': None,
        'bom': None,
        'performance': None,
    }




