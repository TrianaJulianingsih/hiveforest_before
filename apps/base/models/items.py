from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

class UoM(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "UoM"
        verbose_name_plural = "UoM"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
