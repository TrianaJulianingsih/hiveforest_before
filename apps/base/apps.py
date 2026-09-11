from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.base"
    verbose_name = "Base Application"

    def ready(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        import apps.base.authentication_signals  # noqa: F401
        import apps.base.signals  # noqa: F401

        Permission._meta.verbose_name = "Permission"
        Permission._meta.verbose_name_plural = "Permissions"
        ContentType._meta.verbose_name = "Content Type"
        ContentType._meta.verbose_name_plural = "Content Types"
