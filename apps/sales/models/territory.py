from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.humancapital.models.business import Business
from apps.humancapital.models.structure import Position, Assignment
from apps.base.models.locations import Province, Regency, RegencyType
from apps.sales.models.customer import Customer
from apps.sales.models.sales import RepOffice

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTeam                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales team                               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝         
class SalesTeam(GenericAbstract):
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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/18-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesRegion(GenericAbstract):
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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: Jul/3-2025 by Setiadji                           ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class RegionProvince(GenericAbstract):
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
        unique_together = ('region', 'province')

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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesArea(GenericAbstract):
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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: Jul/4-2025 by Setiadji                           ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class AreaRegency(GenericAbstract):
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
        unique_together = ('area', 'regency')

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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: Jun/18-2025 by Setiadji                          ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SalesTerritory(GenericAbstract):
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
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: Jul/22-2025 by Setiadji                          ║
# ║  Updates:             by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class TerritoryAssignment(GenericAbstract):
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
# ║  Name: KAMArea                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain KAM areas to be mapped to regencies      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\territory.py                      ║
# ║  Created: Jun/20-2025 by Setiadji                          ║
# ║  Updates: Jul/10-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class KAMArea(GenericAbstract):
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