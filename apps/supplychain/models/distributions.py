from django.db import models
from apps.base.models.abstracts import GenericAbstract
from apps.base.models.entities import Company
from django.utils.text import slugify


class OrderStatus(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )

    class Meta:
        verbose_name = "Distributor Order Status"
        verbose_name_plural = "Distributor Order Statuses"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


class OrderType(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    distributor = models.ForeignKey(
        "Distributor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Distributor",
    )

    class Meta:
        verbose_name = "Distributor Order Type"
        verbose_name_plural = "Distributor Order Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


class DistributorItem(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    distributor = models.ForeignKey(
        "Distributor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Distributor",
    )
    product = models.ForeignKey(
        "sales.Product",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Product",
    )
    group = models.ForeignKey(
        "DistributorItemGroup",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Group",
    )
    salesuom = models.ForeignKey(
        "base.UoM",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Sales UOM",
        related_name=("distitem_sales_uom"),
    )
    stockuom = models.ForeignKey(
        "base.UoM",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Stock UOM",
        related_name=("distitem_stock_uom"),
    )
    orderuom = models.ForeignKey(
        "base.UoM",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Order UOM",
        related_name=("distitem_order_uom"),
    )
    salessize = models.IntegerField(null=True, blank=True, verbose_name="Sales Size")
    stocksize = models.IntegerField(null=True, blank=True, verbose_name="Stock Size")
    ordersize = models.IntegerField(null=True, blank=True, verbose_name="Order Size")

    class Meta:
        verbose_name = "Distributor Item"
        verbose_name_plural = "Distributor Items"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.code} {self.name} ({self.distributor.initial})"
        # return f"{self.code} {self.name}"

    def clean(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        qs = DistributorItem.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DistributorItemGroup(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    distributor = models.ForeignKey(
        "Distributor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Distributor",
    )

    class Meta:
        verbose_name = "Distributor Item Group"
        verbose_name_plural = "Distributor Item Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Branch                                              ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain distributor branches                     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\distributions.py            ║
# ║  Created: Setiadji                                         ║
# ║  Updates: Jul/17-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Branch(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    distributor = models.ForeignKey(
        "Distributor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Distributor",
    )
    type = models.ForeignKey(
        "BranchType",
        on_delete=models.CASCADE,
        default="",
        null=True,
        blank=True,
        verbose_name="Type",
    )
    address = models.CharField(
        max_length=255, null=True, blank=True, default="", verbose_name="Address"
    )
    has_sales = models.BooleanField(
        default=False, null=True, blank=True, verbose_name="Has Sales"
    )
    has_stock = models.BooleanField(
        default=False, null=True, blank=True, verbose_name="Has Stock"
    )
    has_order = models.BooleanField(
        default=False, null=True, blank=True, verbose_name="Has Order"
    )
    shipto = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="ShipTo"
    )

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name


class BranchType(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )

    class Meta:
        verbose_name = "Branch Type"
        verbose_name_plural = "Branch Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


class Distributor(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="Company", null=True, blank=True
    )

    class Meta:
        verbose_name = "Distributor"
        verbose_name_plural = "Distributors"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: StDistDaily                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain distributor daily stock balanc           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\distributions.py            ║
# ║  Created: Jul/7 by Noval                                   ║
# ║  Updates: Jul/9 by Noval                                   ║
# ╚════════════════════════════════════════════════════════════╝
class StDistDaily(GenericAbstract):
    kd_prod = models.CharField(
        max_length=6, null=True, blank=True, default="", verbose_name="Kode Prod"
    )
    nm_prod = models.CharField(
        max_length=40, null=True, blank=True, default="", verbose_name="Nanma Prod"
    )
    kd_hrmn = models.CharField(
        max_length=9, null=True, blank=True, default="", verbose_name="Kode Hrmn"
    )
    nm_hrmn = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Nama Hrmn"
    )
    kd_prc = models.CharField(
        max_length=3, null=True, blank=True, default="", verbose_name="Kode Prc"
    )
    kd_cab = models.CharField(
        max_length=3, null=True, blank=True, default="", verbose_name="Kode Cabang"
    )
    id_cab = models.CharField(
        max_length=3, null=True, blank=True, default="", verbose_name="Id Cabang"
    )
    nm_cab = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Nama Cabang"
    )
    kd_io = models.CharField(
        max_length=9, null=True, blank=True, default="", verbose_name="Kode IO"
    )
    lot = models.CharField(
        max_length=35, null=True, blank=True, default="", verbose_name="Lot"
    )
    ed = models.DateField(null=True, blank=True, verbose_name="ED")
    hna = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="HNA"
    )
    reg = models.IntegerField(null=True, blank=True, verbose_name="Reg")
    itr = models.IntegerField(null=True, blank=True, verbose_name="ITR")
    pp = models.IntegerField(null=True, blank=True, verbose_name="PP")
    po = models.IntegerField(null=True, blank=True, verbose_name="PO")
    ext = models.IntegerField(null=True, blank=True, verbose_name="EXT")
    dmg = models.IntegerField(null=True, blank=True, verbose_name="DMG")
    atr = models.IntegerField(null=True, blank=True, verbose_name="ATR")
    ket = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Keterangan"
    )
    periode = models.CharField(
        max_length=8, null=True, blank=True, default="", verbose_name="Periode"
    )
    tgl_proses = models.DateTimeField(null=True, blank=True, verbose_name="Tgl Proses")

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_daily",
        verbose_name="Branch",
    )

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        verbose_name="Distributor",
        null=True,
        blank=True,
    )

    distributoritem = models.ForeignKey(
        DistributorItem,
        on_delete=models.SET_NULL,
        verbose_name="Distributor Item",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Stock Daily Distributor"
        verbose_name_plural = "Stock Daily Distributor"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Name: RawMUST                                                       ║
# ║  Type: Model                                                         ║
# ║  Purpose: Contain distributor daily stock balance from FPT           ║
# ╟──────────────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\models\distributions.py                      ║
# ║  Created: Jul/21 by Utandra                                          ║
# ║  Updates: -                                                          ║
# ╚══════════════════════════════════════════════════════════════════════╝
    
class RawMUST(GenericAbstract):
         
    kd_prc = models.CharField( 
        max_length=3, null=True, blank=True, default="", verbose_name="Kode PRC"
    )
    periode = models.CharField( # from 6 to 8
        max_length=8, null=True, blank=True, default="", verbose_name="Periode"
    )
    io_id = models.CharField(
        max_length=9, null=True, blank=True, default="", verbose_name="Kode IO"
    )
    kdcab = models.CharField(
        max_length=3, null=True, blank=True, default="", verbose_name="Kode/ID Cabang"
    )
    nmcab = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Nama Cabang"
    )
    subinven = models.CharField( ## ga ada di ST (MUP)
        max_length=15, null=True, blank=True, default="", verbose_name="Sub Inventori"
    )
    klasprod = models.CharField(
        max_length=9, null=True, blank=True, default="", verbose_name="Klas Prod / Kode Hrmn"
    )
    nmklas = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Nama Klas/ Nama Hrmn"
    )
    loc = models.CharField( ## ga ada di ST (MUP)
        max_length=15, null=True, blank=True, default="", verbose_name="Loc"
    )
    nmloc = models.CharField( ## ga ada di ST (MUP)
        max_length=30, null=True, blank=True, default="", verbose_name="Nama Loc"
    )
    lot = models.CharField(
        max_length=35, null=True, blank=True, default="", verbose_name="Lot"
    )
    ed = models.DateField(null=True, blank=True, verbose_name="ED")
    kodeprod = models.CharField(
        max_length=8, null=True, blank=True, default="", verbose_name="Kode Prod"
    )
    namaprod = models.CharField(
        max_length=40, null=True, blank=True, default="", verbose_name="Nama Prod"
    )
    kemasan = models.CharField( ## ga ada di ST (MUP)
        max_length=15, null=True, blank=True, default="", verbose_name="Kemasan"
    )
    hna = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="HNA"
    )
    sldoawal = models.DecimalField( ## ga ada di ST (MUP)
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Saldo Awal"
    )
    sldottip = models.DecimalField( ## ga ada di ST (MUP)
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Saldo Ttip"
    )
    sldorusak = models.DecimalField( ## ga ada di ST (MUP)
        max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Saldo Rusak"
    )
    bapb = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="BAPB"
    )
    bapbttip = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="BAPB TTIP"
    )
    beli = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Beli"
    )
    realokasi = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Realokasi"
    )
    cnretur = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="CN Retur"
    )
    returbnus = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Retur Bnus"
    )
    faktur = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Faktur"
    )
    faktbnus = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Faktur Bnus"
    )
    spp = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Beli"
    )
    alokasi = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="Alokasi"
    )
    cnbeli = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="CN Beli"
    )
    mskrusak = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="MSK Rusak"
    )
    klrusak = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="KL Rusak"
    )
    sppttip = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="SPP Ttip"
    )
    spkirim = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="SP Kirim"
    )
    spterima = models.CharField( ## ga ada di ST (MUP)
        max_length=5, null=True, blank=True, verbose_name="SP Terima"
    )
    akhir = models.IntegerField(null=True, blank=True, verbose_name="Akhir")
    atr = models.IntegerField(null=True, blank=True, verbose_name="ATR")
    tgldata = models.CharField( # from tgldata ftp
        max_length=8, null=True, blank=True, default="", verbose_name="Tanggal Data"
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="raw_must",
        verbose_name="Branch",
    )

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        verbose_name="Distributor",
        null=True,
        blank=True,
    )

    distributoritem = models.ForeignKey(
        DistributorItem,
        on_delete=models.SET_NULL,
        verbose_name="Distributor Item",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Raw MUST"
        verbose_name_plural = "Raw MUST"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
    ]
    
class BranchStock(GenericAbstract):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="stock_summaries",
        verbose_name="Branch",
    )
    product = models.ForeignKey(
        "sales.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_stock_entries",
        verbose_name="Product",
    )
    product_name = models.CharField(
        max_length=255,
        verbose_name="Product Name",
        help_text="Product label captured from stock source.",
    )
    team = models.ForeignKey(
        "sales.ProductSubgroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_stock_entries",
        verbose_name="Team",
    )
    group = models.ForeignKey(
        "sales.ProductGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_stock_entries",
        verbose_name="Group",
    )
    trx_date = models.DateField(verbose_name="Transaction Date")
    total_reg = models.BigIntegerField(default=0, verbose_name="Total Reg")

    class Meta:
        verbose_name = "Branch Stock"
        verbose_name_plural = "Branch Stocks"
        ordering = ("-trx_date", "branch__code", "product_name")
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "product_name", "trx_date"],
                name="supplychain_branchstock_unique_snapshot",
            )
        ]
        indexes = [
            models.Index(
                fields=["branch", "trx_date"], name="branchstock_branch_date_idx"
            ),
            models.Index(
                fields=["trx_date", "product_name"], name="branchstock_date_product_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.name:
            branch_code = self.branch.code if self.branch else "NA"
            product_code = self.product.code if self.product else self.product_name
            self.name = f"{branch_code}-{product_code}-{self.trx_date.isoformat()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch} — {self.product_name} ({self.trx_date})"
