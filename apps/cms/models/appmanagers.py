from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltranslation.utils import get_language
from apps.base.models.abstracts import GenericAbstract

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ApplicationList                                     ║
# ║  Purpose: Mantain application list in CMS                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\cms\models\appmanagers.py                      ║
# ║  Created: ?                                                ║
# ║  Updated: May/30-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ApplicationList(GenericAbstract):
    code = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Shortname")
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon for UI rendering
    order = models.PositiveIntegerField(default=0)  # Ordering menus

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        value = getattr(self, f"shortname_{get_language()}", None)
        return value or self.shortname or str(self.id)
