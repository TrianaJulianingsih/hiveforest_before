from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.contrib.auth.models import Permission, Group
from apps.cms.models.modmanagers import ModuleList


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Menu Item                                           ║
# ║  Type: Concrete model                                      ║
# ║  Purpose: To register menu system                          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\cms\models\menusystem.py                       ║
# ║  Created:                                                  ║
# ║  Updated: Jun/3-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class MenuItem(GenericAbstract):
    code = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Code"
    )
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=25, null=True, blank=True, default="", verbose_name="Shortname"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, related_name="children"
    )  # Submenu hierarchy
    application = models.ForeignKey(
        "cms.ApplicationList", on_delete=models.CASCADE, blank=True, null=True
    )
    module = models.ForeignKey(
        "cms.ModuleList", on_delete=models.CASCADE, blank=True, null=True
    )
    icon = models.CharField(
        max_length=50, blank=True, null=True
    )  # Icon for UI rendering
    url = models.CharField(
        max_length=255, blank=True, null=True
    )  # URL link to navigate
    order = models.PositiveIntegerField(default=0)  # Ordering menus
    iframe_url = models.TextField(
        blank=True, null=True, verbose_name="Dashboard IFrame URL"
    )  # URL dashboard per menu

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
        ordering = ["parent__id", "order"]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
