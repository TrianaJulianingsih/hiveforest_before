from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class LogStatus(models.TextChoices):
    SUCCESS = "SUCCESS", _("Success")
    ERROR = "ERROR", _("Error")

class LogAction(models.TextChoices):
    CREATE = "CREATE", _("Create")
    READ = "READ", _("Read")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")
    LOGIN = "LOGIN", _("Login")
    LOGOUT = "LOGOUT", _("Logout")
    APPROVE = "APPROVE", _("Approve")
    REJECT = "REJECT", _("Reject")
    EXPORT = "EXPORT", _("Export")
    IMPORT = "IMPORT", _("Import")
    CLICK = "CLICK", _("Click")
    API_REQUEST = "API_REQUEST", _("API Request")
    SYSTEM = "SYSTEM", _("System")
    ERROR = "ERROR", _("Error")
    BULK_CREATE = "BULK_CREATE", _("Bulk Create")
    BULK_UPDATE = "BULK_UPDATE", _("Bulk Update")
    BULK_DELETE = "BULK_DELETE", _("Bulk Delete")

class SystemLog(models.Model):
    cat = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Created at"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="system_logs",
        db_index=True,
        verbose_name=_("User")
    )
    action = models.CharField(max_length=50, choices=LogAction.choices, db_index=True, verbose_name=_("Action"))
    module = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name=_("Module"))
    feature = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name=_("Feature"))
    object_type = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name=_("Object Type"))
    object_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_("Object ID"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    status = models.CharField(max_length=20, choices=LogStatus.choices, default=LogStatus.SUCCESS, db_index=True, verbose_name=_("Status"))
    response_code = models.IntegerField(blank=True, null=True, db_index=True, verbose_name=_("Response Code"))
    response_data = models.TextField(blank=True, null=True, verbose_name=_("Response Data"))
    request_method = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Request Method"))
    request_path = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Request Path"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    user_agent = models.TextField(blank=True, null=True, verbose_name=_("User Agent"))
    old_data = models.JSONField(null=True, blank=True, verbose_name=_("Old Data"))
    new_data = models.JSONField(null=True, blank=True, verbose_name=_("New Data"))
    error_message = models.TextField(blank=True, null=True, verbose_name=_("Error Message"))
    stack_trace = models.TextField(blank=True, null=True, verbose_name=_("Stack Trace"))
    metadata = models.JSONField(null=True, blank=True, verbose_name=_("Metadata"))
    log_type = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name=_("Log Type"))

    class Meta:
        db_table = "base_system_log"
        verbose_name = _("System Log")
        verbose_name_plural = _("System Logs")
        ordering = ("-cat",)
        indexes = [
            models.Index(fields=["cat"]),
            models.Index(fields=["user", "cat"]),
            models.Index(fields=["action", "cat"]),
            models.Index(fields=["module", "feature"]),
            models.Index(fields=["status", "cat"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"[{self.cat:%Y-%m-%d %H:%M:%S}] {username} - {self.action} - {self.module} - {self.status}"
