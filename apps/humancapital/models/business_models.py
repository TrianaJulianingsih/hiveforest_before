from django.db import models
from apps.base.models.abstracts import GenericAbstract
from apps.base.mixins import SystemLogModelMixin


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Business                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain business master data                     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\business_models.py         ║
# ║  Created: Jul/8-2026 by GitHub Copilot                     ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
class Business(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Shortname")
    effective = models.DateField(null=True, blank=True, verbose_name="Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name="Terminated")

    class Meta:
        db_table = "humancapital_business"
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        ordering = ("code", "name")
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
