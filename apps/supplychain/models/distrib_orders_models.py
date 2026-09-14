from django.db import models
from apps.base.models.abstracts import GenericAbstract
from apps.base.mixins import SystemLogModelMixin
from apps.supplychain.models.distributions_models import (
    OrderStatus,
    OrderType,
    Distributor,
    Branch,
    DistributorItem,
    DistributorItemGroup,
)
from django.utils.text import slugify


class OrderHeader(SystemLogModelMixin, GenericAbstract):
    distributor = models.ForeignKey(
        'supplychain.Distributor',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Distributor",
    )
    orderno = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="No"
    )
    orderdate = models.DateField(null=True, blank=True, verbose_name="Date")
    orderdue = models.DateField(null=True, blank=True, verbose_name="Due")
    ordertype = models.ForeignKey(
        "supplychain.OrderType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Order Type",
    )
    branch = models.ForeignKey(
        "supplychain.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Branch",
    )
    progress = models.ForeignKey(
        "supplychain.OrderStatus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=1,
        verbose_name="Progress",
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        if self.distributor and self.orderno:
            self.name = f"{self.distributor.code}-{self.orderno}"
        if not self.pk:
            self.progress = OrderStatus.objects.get(id=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrderDetail(SystemLogModelMixin, GenericAbstract):
    order = models.ForeignKey(
        'supplychain.OrderHeader',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Order",
    )
    orderline = models.CharField(
        max_length=3, null=True, blank=True, default="", verbose_name="Line"
    )
    itemgroup = models.ForeignKey(
        "supplychain.DistributorItemGroup",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Group",
    )
    item = models.ForeignKey(
        "supplychain.DistributorItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Item",
    )
    qty = models.IntegerField(null=True, blank=True, verbose_name="Qty")
    uom = models.ForeignKey(
        "base.UoM",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="UoM",
    )
    price = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True, verbose_name="Price"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Amount"
    )
    progress = models.ForeignKey(
        "supplychain.OrderStatus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=1,
        verbose_name="Progress",
    )

    class Meta:
        verbose_name = "Order Detail"
        verbose_name_plural = "Order Details"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug or self.__class__.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            if self.order and self.item:
                base_slug = slugify(f"{self.order.orderno}-{self.item}")
            else:
                base_slug = slugify(f"orderdetail-{self.pk or 'new'}")

            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: DODetail                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain delivery note detail                     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\distrib_orders_models.py    ║
# ║  Created: Jul/14 by Noval                                  ║
# ║  Updates: Jul/23 by Setiadji                               ║
# ╚════════════════════════════════════════════════════════════╝ 
class DODetail(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=100, null=False, default="", verbose_name="Code")
    transaction_number = models.CharField(
        max_length=10, null=True, blank=True, default="", verbose_name="Transaction Number"
    )
    dn_date = models.DateField(null=True, blank=True, verbose_name="DN Date")
    dn_effdate = models.DateField(null=True, blank=True, verbose_name="DN Eff Date")
    dn = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="DN")
    shipto_code = models.CharField(
        max_length=10, null=True, blank=True, default="", verbose_name="Ship To Code"
    )
    shipto_name = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Ship To Name"
    )
    address = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Address"
    )
    inv = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Inv"
    )
    so = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="SO"
    )
    po = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="PO"
    )
    product_line = models.CharField(
        max_length=6, null=True, blank=True, default="", verbose_name="Product Line"
    )
    item_number = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Item Number"
    )
    item = models.ForeignKey(
        'ManufacturingItem',
        on_delete=models.SET_NULL,
        verbose_name="Item",
        null=True,
        blank=True,
    )
    item_description = models.CharField(
        max_length=100, null=True, blank=True, default="", verbose_name="Item Description"
    )
    batch = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Batch"
    )
    qty = models.IntegerField(null=True, blank=True, verbose_name="Qty")
    value_shipped = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Value Shipped"
    )
    uom = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="UOM"
    )
    location = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Location"
    )
    branch = models.ForeignKey(
        'Branch', on_delete=models.SET_NULL, verbose_name="Branch", null=True, blank=True
    )
    match_code = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Matching Code"
    )
    podetail = models.ForeignKey(
        'PODetail', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="PO Detail"
    )
    header = models.ForeignKey(
        'DOHeader', on_delete=models.SET_NULL, verbose_name="Header", null=True, blank=True
    )

    class Meta:
        verbose_name = "Delivery Order Detail"
        verbose_name_plural = "Delivery Order Details"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: PODetail                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain purchase order detail                    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\distrib_orders_models.py    ║
# ║  Created: Jul/17 by Noval                                  ║
# ║  Updates: Jul/18 by Noval                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class PODetail(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=100, null=False, default="", verbose_name="Code")
    nomor_po = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Nomor PO"
    )
    type = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Type"
    )
    harmonisasi = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Harmonisasi"
    )
    cabang = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Cabang"
    )
    branch = models.ForeignKey(
        'Branch', on_delete=models.SET_NULL, verbose_name="Branch", null=True, blank=True
    )
    ord_date = models.DateField(null=True, blank=True, verbose_name="Order Date")
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")
    line = models.CharField(
        max_length=5, null=True, blank=True, default="", verbose_name="Line"
    )
    items = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Items"
    )
    item = models.ForeignKey(
        'DistributorItem', on_delete=models.SET_NULL, verbose_name="Item", null=True, blank=True
    )
    item_description = models.CharField(
        max_length=100, null=True, blank=True, default="", verbose_name="Item Description"
    )
    quantity = models.IntegerField(null=True, blank=True, verbose_name='Quantity')
    satuan = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Satuan"
    )
    hjp = models.IntegerField(null=True, blank=True, verbose_name="HJP")
    jumlah = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name='Jumlah'
    )
    remark = models.CharField(
        max_length=100, null=True, blank=True, default="", verbose_name="Remark"
    )
    progress = models.ForeignKey(
        "supplychain.OrderStatus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=1,
        verbose_name="Progress",
    )
    match_code = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Matching Code"
    )
    header = models.ForeignKey(
        'POHeader', on_delete=models.SET_NULL, verbose_name="Header", null=True, blank=True
    )
    
    class Meta:
        verbose_name = "Purchase Order Detail"
        verbose_name_plural = "Purchase Order Details"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


class DOHeader(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=100, null=False, default="", verbose_name="Code")
    dn_date = models.DateField(null=True, blank=True, verbose_name="DN Date")
    dn = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="DN"
    )
    shipto_code = models.CharField(
        max_length=10, null=True, blank=True, default="", verbose_name="Ship To Code"
    )
    shipto_name = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Ship To Name"
    )
    address = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Adress"
    )
    so = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="SO"
    )

    class Meta:
        verbose_name = "Delivery Order Header"
        verbose_name_plural = "Delivery Order Headers"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


class POHeader(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=100, null=False, default="", verbose_name="Code")
    nomor_po = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Nomor PO"
    )
    type = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Type"
    )
    cabang = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Cabang"
    )
    ord_date = models.DateField(null=True, blank=True, verbose_name="Order Date")
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")

    class Meta:
        verbose_name = "Purchase Order Header"
        verbose_name_plural = "Purchase Order Headers"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
