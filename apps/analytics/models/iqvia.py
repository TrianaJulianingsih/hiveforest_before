from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.sales.models.product import Product

class IQV_ITMATrans(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    quarter = models.CharField(max_length=20, null=True, default="", verbose_name="Quarter")
    unit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default="", verbose_name="Unit")
    valuehna = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, default="", verbose_name="Value HNA")
    date = models.DateField(null=True, blank=True, default="", verbose_name="Date")
    year = models.IntegerField(null=True, default="", verbose_name=("Year"))

    pack = models.ForeignKey(
        'IQV_Pack',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Pack"
    )
    
    class Meta:
        verbose_name = "ITMA Transaction"
        verbose_name_plural = "ITMA Transactions"
        indexes = [models.Index(fields=["name", "quarter"], name="iqv_itma_name_qtr_idx")]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_Pack(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    key = models.CharField(max_length=255, null=True, default="", verbose_name="Key")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default="", verbose_name="Size")
    strength = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Strength")
    volume = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Volume")
    launched = models.DateField(null=True, blank=True, default="", verbose_name="Launched")
    form = models.ForeignKey('IQV_PackForm', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Form")
    product = models.ForeignKey('IQV_Product', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Product")
    atc4 = models.ForeignKey('IQV_ATC4', on_delete=models.CASCADE, null=True, blank=True, verbose_name="ATC4")
    otc4 = models.ForeignKey('IQV_OTC4', on_delete=models.CASCADE, null=True, blank=True, verbose_name="OTC4")
    nfc3 = models.ForeignKey('IQV_NFC3', on_delete=models.CASCADE, null=True, blank=True, verbose_name="NFC3")
    branddet = models.ForeignKey('IQV_BrandDet', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Brand Detail")
    ethstatgrp = models.ForeignKey('IQV_EthStatGrp', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ethical Status Group")
    ethstat = models.ForeignKey('IQV_EthStat', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Ethical Status")
    regstat = models.ForeignKey('IQV_RegStat', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Registration Status")
    molstring = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Molecule String")
    
    sales_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sales Product"
    )

    class Meta:
        verbose_name = "Pack"
        verbose_name_plural = "Packs"
        indexes = [models.Index(fields=["name"], name="iqv_pack_name_idx")]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_Product(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    company = models.ForeignKey('IQV_Company', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Company")
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_PackForm(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    class Meta:
        verbose_name = "Pack Form"
        verbose_name_plural = "Pack Forms"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_Molecule(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    subfamily = models.ForeignKey('IQV_MoleSubFam', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Sub Family")
    class Meta:
        verbose_name = "Molecule"
        verbose_name_plural = "Molecules"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_MoleSubFam(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    family = models.ForeignKey('IQV_MoleFam', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Family")
    class Meta:
        verbose_name = "Molecule Sub Family"
        verbose_name_plural = "Molecule Sub Families"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_MoleFam(GenericAbstract):
    code = models.CharField(max_length=10, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    class Meta:
        verbose_name = "Molecule Family"
        verbose_name_plural = "Molecule Families"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_Company(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    comtype = models.ForeignKey('IQV_ComType', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Type")
    corporation = models.ForeignKey('IQV_Corp', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Corporation")

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_RegStat(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    
    class Meta:
        verbose_name = "Registration Status"
        verbose_name_plural = "Registration Statuses"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_EthStat(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    group = models.ForeignKey('IQV_EthStatGrp', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Group")
    
    class Meta:
        verbose_name = "Ethical Status"
        verbose_name_plural = "Ethical Statuses"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_EthStatGrp(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
        
    class Meta:
        verbose_name = "Ethical Status Group"
        verbose_name_plural = "Ethical Status Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_BrandDet(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    gen_flag = models.ForeignKey('analytics.IQV_GenFlag', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Gen_Flag")
    
    class Meta:
        verbose_name = "Brand Detail"
        verbose_name_plural = "Brand Details"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_GenFlag(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
        
    class Meta:
        verbose_name = "Generic Flag"
        verbose_name_plural = "Generic Flags"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_ComType(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
        
    class Meta:
        verbose_name = "Company Type"
        verbose_name_plural = "Company Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_Corp(GenericAbstract):
    code = models.CharField(max_length=20, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Corporation"
        verbose_name_plural = "Corporations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_OTC4(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    otc3 = models.ForeignKey('analytics.IQV_OTC3', on_delete=models.CASCADE, null=True, blank=True, verbose_name="OTC3")

    class Meta:
        verbose_name = "OTC4"
        verbose_name_plural = "OTC4"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_OTC3(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    otc2 = models.ForeignKey('analytics.IQV_OTC2', on_delete=models.CASCADE, null=True, blank=True, verbose_name="OTC2")

    class Meta:
        verbose_name = "OTC 3"
        verbose_name_plural = "OTC 3"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_OTC2(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    otc1 = models.ForeignKey('analytics.IQV_OTC1', on_delete=models.CASCADE, null=True, blank=True, verbose_name="OTC1")

    class Meta:
        verbose_name = "OTC 2"
        verbose_name_plural = "OTC 2"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_OTC1(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "OTC 1"
        verbose_name_plural = "OTC 1"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_NFC3(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    nfc2 = models.ForeignKey('analytics.IQV_NFC2', on_delete=models.CASCADE, null=True, blank=True, verbose_name="NFC2")

    class Meta:
        verbose_name = "NFC 3"
        verbose_name_plural = "NFC 3"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_NFC2(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    nfc1 = models.ForeignKey('analytics.IQV_NFC1', on_delete=models.CASCADE, null=True, blank=True, verbose_name="NFC1")

    class Meta:
        verbose_name = "NFC 2"
        verbose_name_plural = "NFC 2"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_NFC1(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "NFC 1"
        verbose_name_plural = "NFC 1"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_ATC4(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    atc3 = models.ForeignKey('analytics.IQV_ATC3', on_delete=models.CASCADE, null=True, blank=True, verbose_name="ATC3")

    class Meta:
        verbose_name = "ATC 4"
        verbose_name_plural = "ATC 4"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_ATC3(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    atc2 = models.ForeignKey('analytics.IQV_ATC2', on_delete=models.CASCADE, null=True, blank=True, verbose_name="ATC1")

    class Meta:
        verbose_name = "ATC 3"
        verbose_name_plural = "ATC 3"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

class IQV_ATC2(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    atc1 = models.ForeignKey('analytics.IQV_ATC1', on_delete=models.CASCADE, null=True, blank=True, verbose_name="ATC1")

    class Meta:
        verbose_name = "ATC 2"
        verbose_name_plural = "ATC 2"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
class IQV_ATC1(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "ATC 1"
        verbose_name_plural = "ATC 1"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
