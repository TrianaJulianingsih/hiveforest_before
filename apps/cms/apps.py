from django.apps import AppConfig


class CmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cms'
    verbose_name = "Content Management System"

    def ready(self):
        import apps.cms.translation  # Register modeltranslation        
        import apps.cms.signals.structures  # Import the signals module