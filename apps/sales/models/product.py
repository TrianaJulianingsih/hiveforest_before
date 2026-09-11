from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.humancapital.models.business import Business
from apps.base.models.items import UoM
from apps.sales.models.territory import SalesTeam


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Product                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of products                         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\product.py                        ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Product(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    subgroup = models.ForeignKey(
        "ProductSubgroup",
        on_delete=models.CASCADE,
        verbose_name="Subgroup",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        "ProductCategory",
        on_delete=models.CASCADE,
        verbose_name="Category",
        null=True,
        blank=True,
    )
    packaging = models.ForeignKey(
        "ProductPackage",
        on_delete=models.CASCADE,
        verbose_name="Packaging",
        null=True,
        blank=True,
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        verbose_name="Business",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        "base.Company",
        on_delete=models.CASCADE,
        verbose_name="Owner",
        null=True,
        blank=True,
    )
    height = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Height", null=True, blank=True
    )
    length = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Length", null=True, blank=True
    )
    width = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Width", null=True, blank=True
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Weight", null=True, blank=True
    )
    box_per_palletac = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Box / Pallet AC",
        null=True,
        blank=True,
    )
    package = models.ForeignKey(
        "base.UoM",
        on_delete=models.SET_NULL,
        verbose_name="Package",
        null=True,
        blank=True,
        related_name="products_as_package",
    )
    uom = models.ForeignKey(
        UoM,
        on_delete=models.SET_NULL,
        verbose_name="UoM",
        null=True,
        blank=True,
        related_name="products_as_uom",
    )
    size = models.IntegerField(default="", verbose_name="Size", null=True, blank=True)
    targetgroup = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Target Group"
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductPackage                                      ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of product packages                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\product.py                        ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ProductPackage(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )

    class Meta:
        verbose_name = "Product Package"
        verbose_name_plural = "Product Packages"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductCategory                                     ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list product categories                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\product.py                        ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ProductCategory(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductSubgroup                                     ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list product subgroups                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\product.py                        ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ProductSubgroup(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )
    group = models.ForeignKey("ProductGroup", on_delete=models.CASCADE)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        verbose_name="Business",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Product Subgroup"
        verbose_name_plural = "Product Subgroups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductGroup                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of product groups                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\product.py                        ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ProductGroup(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(
        max_length=7, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=12, null=True, blank=True, default="", verbose_name="Shortname"
    )
    team = models.ForeignKey(
        SalesTeam, on_delete=models.SET_NULL, verbose_name="Team", null=True, blank=True
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        verbose_name="Business",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
