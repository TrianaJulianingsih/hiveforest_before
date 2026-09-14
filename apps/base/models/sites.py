from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Sites                                               ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain site locations for employee placement    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\models\sites.py                           ║
# ║  Created: Jun/15-2026 by Copilot                           ║
# ║  Updates: Jun/15-2026 by Copilot                           ║
# ╚════════════════════════════════════════════════════════════╝
class Sites(GenericAbstract):
    code = models.CharField(max_length=20, null=False, unique=True, default="", verbose_name="Code")

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
