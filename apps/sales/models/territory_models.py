from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.base.mixins import SystemLogModelMixin
from apps.humancapital.models.business_models import Business
from apps.humancapital.models.structure_models import Position, Assignment
from apps.base.models.locations import Province, Regency, RegencyType
from apps.sales.models.customer_models import Customer
from apps.sales.models.sales_models import RepOffice


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTeam                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales team                               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝         
class SalesTeam(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Business", null=True, blank=True)

    class Meta:
        verbose_name = "Sales Team"
        verbose_name_plural = "Sales Teams"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesRegion                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales regions to be mapped to provinces  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/18-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesRegion(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name="Position", null=True, blank=True, related_name="region_position")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Business", null=True, blank=True, related_name="region_business")
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Sales Region"
        verbose_name_plural = "Sales Regions"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RegionProvince                                      ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain region-province mapping                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: Jul/3-2025 by Setiadji                           ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class RegionProvince(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, blank=True, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    region = models.ForeignKey(SalesRegion, on_delete=models.CASCADE, verbose_name="Region",null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name="Province",null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Region Province"
        verbose_name_plural = "Region Provinces"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        # Note: removed unique_together to support versioning/history records
        # (multiple rows per region/province allowed; active record indicated by status)

    def save(self, *args, **kwargs):
        if self.region and self.province:
            self.code = f"{self.region.code}-{self.province.initial}"
            self.name = f"{self.region.name}-{self.province.shortname}"
        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesArea                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales areas to be mapped to regencies    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesArea(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, blank=True, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    region = models.ForeignKey(SalesRegion, on_delete=models.CASCADE, verbose_name="Region", null=True, blank=True)
    repoffice = models.ForeignKey(RepOffice, on_delete=models.CASCADE, verbose_name="Repoffice", null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Sales Area"
        verbose_name_plural = "Sales Areas"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        unique_together = ('region', 'initial')

    def save(self, *args, **kwargs):
        if self.initial and self.region:
            self.code = f"{self.region.code}-{self.initial}"
            self.name = f"{self.region.shortname} - {self.initial}"
        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AreaRegency                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain area-regency mapping                     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: Jul/4-2025 by Setiadji                           ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class AreaRegency(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, blank=True, null=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Shortname")
    area = models.ForeignKey(SalesArea, on_delete=models.CASCADE, verbose_name="Area",null=True, blank=True)
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, verbose_name="Regency",null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Area Regency"
        verbose_name_plural = "Area Regencies"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        # Note: removed unique_together to support versioning/history records
        # (multiple rows per area/regency allowed; active record indicated by status)

    def save(self, *args, **kwargs):
        if self.area and self.regency:
            self.code = f"{self.area.code}-{self.regency.code}"
            self.name = f"{self.area.name}-{self.regency.name}"
        super().save(*args, **kwargs)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTerritory                                      ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales territory to be mapped to districts║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: Jun/18-2025 by Setiadji                          ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesTerritory(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    area = models.ForeignKey('sales.SalesArea', on_delete=models.CASCADE, verbose_name="Area", null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Sales Territory"
        verbose_name_plural = "Sales Territories"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: TerritoryAssignment                                 ║
# ║  Type: Model                                               ║
# ║  Purpose: Map employee assignment to sales territory       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: Jul/22-2025 by Setiadji                          ║
# ║  Updates:             by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class TerritoryAssignment(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=30, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, verbose_name="Assignment", null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, verbose_name="Customer", null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Territory Assignment"
        verbose_name_plural = "Territory Assignments"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: TerritoryAssignmentHistory                         ║
# ║  Type: Model                                              ║
# ║  Purpose: Audit trail for TerritoryAssignment changes     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory.py                    ║
# ║  Created: Jun/18-2026 by GitHub Copilot                   ║
# ╚════════════════════════════════════════════════════════════╝
class TerritoryAssignmentHistory(SystemLogModelMixin, models.Model):
    ACTION_CREATED = "created"
    ACTION_UPDATED = "updated"
    ACTION_INACTIVE = "inactive"
    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_UPDATED, "Updated"),
        (ACTION_INACTIVE, "Set Inactive"),
    ]

    territory_assignment = models.ForeignKey(
        TerritoryAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history_entries",
        verbose_name="Territory Assignment",
    )
    code = models.CharField(max_length=30, blank=True, default="", verbose_name="Code")
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="Name")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Changed By",
    )
    old_assignment = models.ForeignKey(
        Assignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="territory_assignment_history_old_assignment",
        verbose_name="Old Assignment",
    )
    new_assignment = models.ForeignKey(
        Assignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="territory_assignment_history_new_assignment",
        verbose_name="New Assignment",
    )
    old_customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="territory_assignment_history_old_customer",
        verbose_name="Old Customer",
    )
    new_customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="territory_assignment_history_new_customer",
        verbose_name="New Customer",
    )
    old_status = models.IntegerField(null=True, blank=True, verbose_name="Old Status")
    new_status = models.IntegerField(null=True, blank=True, verbose_name="New Status")
    old_effective = models.DateField(null=True, blank=True, verbose_name="Old Effective")
    new_effective = models.DateField(null=True, blank=True, verbose_name="New Effective")
    old_terminated = models.DateField(null=True, blank=True, verbose_name="Old Terminated")
    new_terminated = models.DateField(null=True, blank=True, verbose_name="New Terminated")
    remark = models.CharField(max_length=255, null=True, blank=True, verbose_name="Remark")

    class Meta:
        db_table = "sales_territory_assignment_history"
        verbose_name = "Territory Assignment History"
        verbose_name_plural = "Territory Assignment Histories"
        ordering = ["-changed_at"]

    def __str__(self):
        return (
            f"{self.code or self.name or self.territory_assignment_id} — {self.action} "
            f"by {self.changed_by} at {self.changed_at:%Y-%m-%d %H:%M}"
        )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: KAMArea                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain KAM areas to be mapped to regencies      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory_models.py               ║
# ║  Created: Jun/20-2025 by Setiadji                          ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class KAMArea(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Shortname")
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "KAM Area"
        verbose_name_plural = "KAM Areas"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
