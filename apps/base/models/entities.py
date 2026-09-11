from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

class CompanyOwner(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")
    owntype = models.ForeignKey('base.CompanyOwnership', on_delete=models.CASCADE, verbose_name="Owner")

    class Meta:
        verbose_name = "Company Owner"
        verbose_name_plural = "Company Owners"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class CompanyOwnership(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Company Ownership"
        verbose_name_plural = "Company Ownerships"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class Company(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
