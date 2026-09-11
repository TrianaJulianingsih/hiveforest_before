from django.db import models
from django.utils.translation import gettext_lazy as _
from enum import IntEnum

class Status(IntEnum):
    ACTIVE = 1
    INACTIVE = 0

STATUS_CHOICES = (
    (Status.ACTIVE.value, _('Active')),
    (Status.INACTIVE.value, _('Inactive')),
)

class PermissionState(models.TextChoices):
    ALLOW = "allow", _("Allow Specific")
    ALLOW_ALL = "allow_all", _("Allow All")
    DENY = "deny", _("Deny Specific")
    DENY_ALL = "deny_all", _("Deny All")
    NOT_SET = "not_set", _("Not Set")