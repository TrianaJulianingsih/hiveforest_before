from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.utils.text import slugify


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Customer                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of customers                        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Customer(GenericAbstract):
    SUBDIST_CHOICES = (
        ("Y", "Yes"),
        ("N", "No"),
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        default="",
        verbose_name="Code",
    )
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Shortname"
    )
    alias = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Alias"
    )
    formername = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Former Name"
    )
    custtype = models.ForeignKey(
        "sales.CustomerType",
        on_delete=models.SET_NULL,
        verbose_name="Type",
        null=True,
        blank=True,
    )
    repoffice = models.ForeignKey(
        "sales.RepOffice",
        on_delete=models.SET_NULL,
        related_name="rep_office_set",
        verbose_name="Rep. Office",
        null=True,
        blank=True,
    )
    station = models.ForeignKey(
        "sales.RepOffice",
        on_delete=models.SET_NULL,
        related_name="station_set",
        verbose_name="Station",
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=19,
        decimal_places=14,
        verbose_name="Longitude",
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=19, decimal_places=14, verbose_name="Latitude", null=True, blank=True
    )
    building = models.CharField(
        max_length=255, null=True, blank=True, default="", verbose_name="Building"
    )
    street = models.CharField(
        max_length=255, null=True, blank=True, default="", verbose_name="Street"
    )
    complex = models.CharField(
        max_length=255, null=True, blank=True, default="", verbose_name="Complex"
    )
    postcode = models.CharField(
        max_length=6, null=True, blank=True, default="", verbose_name="Postcode"
    )
    village = models.ForeignKey(
        "base.Village",
        on_delete=models.SET_NULL,
        verbose_name="Village",
        null=True,
        blank=True,
    )
    district = models.ForeignKey(
        "base.District",
        on_delete=models.SET_NULL,
        verbose_name="District",
        null=True,
        blank=True,
    )
    regency = models.ForeignKey(
        "base.Regency",
        on_delete=models.SET_NULL,
        verbose_name="Regency",
        null=True,
        blank=True,
    )
    province = models.ForeignKey(
        "base.Province",
        on_delete=models.SET_NULL,
        verbose_name="Province",
        null=True,
        blank=True,
    )
    edam_id = models.IntegerField(verbose_name="EDAM_ID", null=True, blank=True)

    subdist = models.CharField(
        max_length=1,
        choices=SUBDIST_CHOICES,
        default="N",
        verbose_name="Sub Distributor",
    )

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.custtype or self.custtype.id != 3:
            self.subdist = "N"

        if not self.code:  # Generate only if not set
            last_customer = (
                Customer.objects.filter(custtype=self.custtype)
                .order_by("-code")
                .first()
            )
            if last_customer and last_customer.code:
                last_number = int(last_customer.code[-8:])  # Extract last 8 digits
            else:
                last_number = 0
            new_number = f"{last_number + 1:08d}"  # Format as 8-digit number
            self.code = f"{self.custtype.code}{new_number}"

        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CustomerType                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of customer types                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
class CustomerType(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )

    class Meta:
        verbose_name = "Customer Type"
        verbose_name_plural = "Customer Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CustomerGroup                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of customer groups                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
class CustomerGroup(GenericAbstract):
    code = models.CharField(max_length=25, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=20, null=True, blank=True, default="", verbose_name="Shortname"
    )
    ctype = models.CharField(max_length=25, null=False, default="", verbose_name="Type")

    class Meta:
        verbose_name = "Customer Group"
        verbose_name_plural = "Customer Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Outlet                                              ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of distributor outlets              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
class Outlet(GenericAbstract):
    code = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        default="",
        verbose_name="Code",
    )
    code1 = models.CharField(
        max_length=25,
        unique=False,
        null=True,
        blank=True,
        default="",
        verbose_name="Code1",
    )
    code2 = models.CharField(
        max_length=25,
        unique=False,
        null=True,
        blank=True,
        default="",
        verbose_name="Code2",
    )
    custtype = models.ForeignKey(
        "sales.CustomerType",
        on_delete=models.SET_NULL,
        verbose_name="Type",
        null=True,
        blank=True,
    )
    distributor = models.ForeignKey(
        "supplychain.Distributor",
        on_delete=models.SET_NULL,
        verbose_name="Distributor",
        null=True,
        blank=True,
    )
    branch = models.ForeignKey(
        "supplychain.Branch",
        on_delete=models.SET_NULL,
        verbose_name="Branch",
        null=True,
        blank=True,
    )
    outletgroup = models.ForeignKey(
        "sales.OutletGroup",
        on_delete=models.SET_NULL,
        verbose_name="Outlet Group",
        null=True,
        blank=True,
    )
    address = models.CharField(
        max_length=255, null=True, blank=True, default="", verbose_name="Address"
    )
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        verbose_name="Customer",
        null=True,
        blank=True,
    )
    edam_id = models.IntegerField(verbose_name="EDAM_ID", null=True, blank=True)

    class Meta:
        verbose_name = "Outlet"
        verbose_name_plural = "Outlets"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        if not self.code:  # Generate only if not set
            last_outlet = (
                Outlet.objects.filter(custtype=self.custtype).order_by("-code").first()
            )
            if last_outlet and last_outlet.code:
                last_number = int(last_outlet.code[-8:])  # Extract last 8 digits
            else:
                last_number = 0
            new_number = f"{last_number + 1:08d}"  # Format as 8-digit number
            self.code = f"OT{self.custtype.code}{new_number}"

        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OutletGroup                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of outlet groups                    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
class OutletGroup(GenericAbstract):
    code = models.CharField(max_length=25, null=False, default="", verbose_name="Code")
    distcode = models.CharField(
        max_length=20, null=False, default="", verbose_name="Dist. Code"
    )
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )
    distributor = models.ForeignKey(
        "supplychain.Distributor",
        on_delete=models.SET_NULL,
        verbose_name="Distributor",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Outlet Group"
        verbose_name_plural = "Outlet Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Satker                                              ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of ecatalog satker                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\customer.py                       ║
# ║  Created: Aug/19-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
class Satker(GenericAbstract):
    name = models.CharField(
        max_length=225, null=False, blank=True, default="", verbose_name="Name"
    )
    jenis_instansi = models.CharField(
        max_length=225, null=True, default=None, verbose_name="Jenis Instansi"
    )
    instansi = models.CharField(
        max_length=225, null=True, default=None, verbose_name="Instansi"
    )
    satuan_kerja = models.CharField(
        max_length=1000, null=True, default=None, verbose_name="Satuan Kerja"
    )
    alamat_satuan_kerja = models.CharField(
        max_length=1000, null=True, default=None, verbose_name="Alamat Satuan Kerja"
    )
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Customer",
    )

    class Meta:
        verbose_name = "Satker"
        verbose_name_plural = "Satker"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        self.name = f"{self.instansi}-{self.satuan_kerja}-{self.alamat_satuan_kerja}"
        self.code = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
