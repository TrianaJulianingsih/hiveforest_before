from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

class Association(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Association"
        verbose_name_plural = "Associations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class HospitalType(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Hospital Type"
        verbose_name_plural = "Hospital Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        