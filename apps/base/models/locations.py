from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

class Village(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, verbose_name="District")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude", null=True, blank=True)
    postcode = models.CharField(max_length=6, null=True, blank=True, default="", verbose_name="Postcode")

    class Meta:
        verbose_name = "Village"
        verbose_name_plural = "Villages"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class District(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    regency = models.ForeignKey('Regency', on_delete=models.SET_NULL, null=True, verbose_name="Regency")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude", null=True, blank=True)

    class Meta:
        verbose_name = "District"
        verbose_name_plural = "Districts"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class Regency(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    capital = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Capital")
    iso = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="ISO")
    type = models.ForeignKey('RegencyType', on_delete=models.SET_NULL, null=True, verbose_name="Type")
    province = models.ForeignKey('Province', on_delete=models.SET_NULL, null=True, verbose_name="Province")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude", null=True, blank=True)

    class Meta:
        verbose_name = "Regency"
        verbose_name_plural = "Regencies"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.type} {self.name}"
    
class RegencyType(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")

    class Meta:
        verbose_name = "Regency Type"
        verbose_name_plural = "Regency Types"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class Province(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    shortname = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Shortname")
    initial = models.CharField(max_length=5, null=True, blank=True, default="", verbose_name="Initial")
    capital = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Capital")
    iso = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="ISO")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude", null=True, blank=True)
    island = models.ForeignKey('Island', on_delete=models.SET_NULL, null=True, verbose_name="Island")

    class Meta:
        verbose_name = "Province"
        verbose_name_plural = "Provinces"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class Island(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    iso = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="ISO")

    class Meta:
        verbose_name = "Island"
        verbose_name_plural = "Islands"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
