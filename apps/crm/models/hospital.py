import re

from django.db import models
from apps.sales.models.customer import Customer
from apps.base.models.entities import CompanyOwnership, CompanyOwner
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Hospital                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of hospital                         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: Jul/17-2025 by Setiadji                          ║
# ║  Updates: Aug/6-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class Hospital(GenericAbstract):
    # Raw fields
    raw_province = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Province Text")
    raw_city = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="City Text")
    raw_address = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Full Address")
    raw_phone =  models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Phone")
    raw_type = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Type")
    raw_class = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Class")
    raw_blustat = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="BLU Status")
    raw_ownership = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Ownership Text")
    raw_director = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Director")
    raw_landarea = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Land", null=True, blank=True)
    raw_buildingarea = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Building", null=True, blank=True)
    raw_lastupdate = models.DateField(null=True, blank=True, verbose_name= "Last Update")

    # Additional fields
    code = models.CharField(max_length=100, unique=True, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Shortname")
    alias = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Alias")
    formername = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Former Name")
    building = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Building")
    complex = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Complex")
    street = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Street")
    postcode = models.CharField(max_length=6, null=True, blank=True, default="", verbose_name="Postcode")
    longitude = models.DecimalField(max_digits=19, decimal_places=14, verbose_name="Longitude", null=True, blank=True)
    latitude = models.DecimalField(max_digits=19, decimal_places=14, verbose_name="Latitude", null=True, blank=True)

    # Foreign keys
    hospitaltype = models.ForeignKey('crm.HospitalType', on_delete=models.SET_NULL, verbose_name="Type", null=True, blank=True)
    hospitalclass = models.ForeignKey('crm.HospitalClass', on_delete=models.SET_NULL, verbose_name="Class", null=True, blank=True)
    ownership = models.ForeignKey(CompanyOwnership, on_delete=models.SET_NULL, verbose_name="Ownership", null=True, blank=True)
    owner = models.ForeignKey(CompanyOwner, on_delete=models.SET_NULL, verbose_name="Owner", null=True, blank=True)
    village = models.ForeignKey('base.Village', on_delete=models.SET_NULL, verbose_name="Village", null=True, blank=True)
    district = models.ForeignKey('base.District', on_delete=models.SET_NULL, verbose_name="District", null=True, blank=True)
    regency = models.ForeignKey('base.Regency', on_delete=models.SET_NULL, verbose_name="Regency", null=True, blank=True)
    province = models.ForeignKey('base.Province', on_delete=models.SET_NULL, verbose_name="Province", null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, verbose_name="Customer", null=True, blank=True)

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.name}"

    @property
    def display_name(self):
        return re.sub(r"\s+\d+$", "", self.name or "").strip() or self.name

    @property
    def map_search_query(self):
        parts = [self.display_name]
        if self.raw_address:
            parts.append(self.raw_address)
        city = self.raw_city or (self.regency.name if self.regency_id else None)
        if city:
            parts.append(city)
        province = self.raw_province or (self.province.name if self.province_id else None)
        if province:
            parts.append(province)
        return ", ".join(p for p in parts if p)

    def save(self, *args, **kwargs):
        if self.customer:
            self.code = f"{self.code}-{self.name}-{self.customer.id}"
        else:
            self.code = f"{self.code}-{self.name}"
        super().save(*args, **kwargs)

class HospitalBed(GenericAbstract):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Hospital Bed                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain number of bed in hospital                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: Aug/6-2025 by Setiadji                           ║
# ║  Updates: Aug/8-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝    
    hospital = models.ForeignKey('crm.Hospital', on_delete=models.SET_NULL, verbose_name="Hospital", null=True, blank=True)
    raw_bedno = models.PositiveIntegerField(verbose_name = "No", help_text="")
    raw_bedclass = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Class")
    raw_beds = models.PositiveIntegerField(null=True, blank=True, verbose_name = "Amount", help_text="Number of beds")

    class Meta:
        verbose_name = "Hospital Bed"
        verbose_name_plural = "Hospital Beds"
        ordering = ('raw_bedno',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if self.hospital:
            self.name = f"{self.hospital}-{self.raw_bedno}"
        else:
            self.name = f"{self.raw_bedno}"
        super().save(*args, **kwargs)

class HospitalService(GenericAbstract):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Hospital Service                                    ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain services in hospital                     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: Aug/7-2025 by Setiadji                           ║
# ║  Updates: Aug/8-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
    hospital = models.ForeignKey('crm.Hospital', on_delete=models.SET_NULL, verbose_name="Hospital", null=True, blank=True)
    raw_serviceno = models.PositiveIntegerField(verbose_name = "No", help_text="")
    raw_service = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Service Name")

    class Meta:
        verbose_name = "Hospital Service"
        verbose_name_plural = "Hospital Services"
        ordering = ('raw_serviceno',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if self.hospital:
            self.name = f"{self.hospital}-{self.raw_serviceno}"
        else:
            self.name = f"{self.raw_serviceno}"
        super().save(*args, **kwargs)

class HospitalProfessional(GenericAbstract):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Hospital Professional                               ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain perofessional in hospital                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: Aug/7-2025 by Setiadji                           ║
# ║  Updates: Aug/8-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝    
    hospital = models.ForeignKey('crm.Hospital', on_delete=models.SET_NULL, verbose_name="Hospital", null=True, blank=True)
    raw_profno = models.PositiveIntegerField(verbose_name = "No", help_text="")
    raw_profgroup = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Professional Group")
    raw_professional = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Professional Name")
    raw_profs = models.PositiveIntegerField(null=True, blank=True, verbose_name = "Amount", help_text="Number of professionals")

    class Meta:
        verbose_name = "Hospital Professional"
        verbose_name_plural = "Hospital Professionals"
        ordering = ('raw_profno',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if self.hospital:
            self.name = f"{self.hospital}-{self.raw_profno}"
        else:
            self.name = f"{self.raw_profno}"
        super().save(*args, **kwargs)

class Association(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Association"
        verbose_name_plural = "Associations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalType                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of hospital                         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: by Setiadji                                      ║
# ║  Updates: Jul/17-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class HospitalType(GenericAbstract):
    HOSPITAL_TYPE_GROUP_CHOICES = [
        ('general', 'General Hospital'),
        ('special', 'Special Hospital'),
    ]

    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    type_group = models.CharField(
        max_length=10,
        choices=HOSPITAL_TYPE_GROUP_CHOICES,
        help_text="Whether this type is general or special"
    )

    class Meta:
        verbose_name = "Hospital Type"
        verbose_name_plural = "Hospital Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalClass                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain list of hospital                         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\models\hospital.py                         ║
# ║  Created: Jul/29-2025 by Setiadji                          ║
# ║  Updates:  by Setiadji                                     ║
# ╚════════════════════════════════════════════════════════════╝
class HospitalClass(GenericAbstract):
    CLASS_GROUP_CHOICES = [
        ('general', 'General Hospital'),
        ('special', 'Special Hospital'),
    ]

    classgroup = models.CharField(
        verbose_name = 'Class Group',
        max_length=10,
        choices=CLASS_GROUP_CHOICES,
        help_text="Whether this class applies to General or Special hospitals"
    )
    classcode = models.CharField(
        verbose_name = 'Class',
        max_length=15,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('D Pratama', 'D Pratama'), ('Not Stated', 'Not Stated')],
        help_text="Class level: A, B, C, D, D Pratama, or Not Stated"
    )
    min_beds = models.PositiveIntegerField(
        verbose_name = "Min Beds",
        help_text="Minimum number of inpatient beds required for this class"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Hospital Class"
        verbose_name_plural = "Hospital Classes"
        unique_together = ('classgroup', 'classcode')
        ordering = ['classgroup', 'order']

    def __str__(self):
        return self.name 

    def save(self, *args, **kwargs):
        self.name =  f"{self.get_classgroup_display()} - Class {self.classcode}"
        super().save(*args, **kwargs)