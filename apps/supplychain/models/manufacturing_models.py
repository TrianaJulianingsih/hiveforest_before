from django.db import models
from apps.base.models.abstracts import GenericAbstract
from apps.base.mixins import SystemLogModelMixin
from django.utils.text import slugify


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: StockStatus                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain stock status lookup                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\manufacturing_models.py     ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝   
class StockStatus(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Stock Status"
        verbose_name_plural = "Stock Statuses"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ManufacturingItem                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain manufacturing items                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\manufacturing_models.py     ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Aug/5-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝         
class ManufacturingItem(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    subgroup = models.ForeignKey("ManufacturingItemSubGroup", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Subgroup")
    owner = models.ForeignKey("base.Company", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Owner")
    product = models.ForeignKey("sales.Product", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Product")
    deliveryuom = models.ForeignKey("base.UoM", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Delivery UoNM", related_name='mfgitem_delivery_uom')
    stockuom = models.ForeignKey("base.UoM", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Stock UoNM", related_name='mfgitem_stock_uom')

    class Meta:
        verbose_name = "Manufacturing Item"
        verbose_name_plural = "Manufacturing Items"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def clean(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        qs = ManufacturingItem.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ManufacturingItemSubgroup                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain manufacturing item subgroup              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\manufacturing_models.py     ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝  
class ManufacturingItemSubgroup(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    group = models.ForeignKey("ManufacturingItemGroup", on_delete=models.CASCADE, default="", null=True, blank=True, verbose_name="Group")

    class Meta:
        verbose_name = "Manufacturing Item Subgroup"
        verbose_name_plural = "Manufacturing Item Subgroups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ManufacturingItemGroup                              ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain manufacturing item group                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\manufacturing_models.py     ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class ManufacturingItemGroup(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Manufacturing Item Group"
        verbose_name_plural = "Manufacturing Item Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: StMftOts                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain distributor daily stock balance          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\manufacturing_models.py     ║
# ║  Created: Jul/24 by Noval                                  ║
# ║  Updates:       by Noval                                   ║
# ╚════════════════════════════════════════════════════════════╝ 
class StMfgOts(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=225, null=False, verbose_name="Code")
    item_number = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Item Number")
    item = models.ForeignKey('ManufacturingItem', on_delete=models.SET_NULL, verbose_name="Item", null=True, blank=True)
    description = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Description")
    inv_status = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Invoice Status")
    lot_serial = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Lot Serial")
    palet_id = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Palet Id")
    location = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="location")
    exp_date = models.DateField(null=True, blank=True, verbose_name="Exp Date")
    qty_oh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Qty On Hand")
    qty_box = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Qty Box")
    vol_kubik = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Vol Kubik")
    berat_ton = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Berat Ton")
    size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Size")
    size_um = models.CharField(max_length=225, null=True, blank=True, default="", verbose_name="Size UM")
    product_line = models.IntegerField(null=True, blank=True, verbose_name="Product Line")
    stock_type = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Stock Type")

    class Meta:
        verbose_name = "Stock OTS Manufacture"
        verbose_name_plural = "Stock OTS Manufactures"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
