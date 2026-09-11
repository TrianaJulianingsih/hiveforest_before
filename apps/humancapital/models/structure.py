from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.humancapital.models.employee import EmployeeTitle

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Assignment                                          ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain assignment in the company                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\structure.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/1-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝      
class Assignment(GenericAbstract):
    code = models.CharField(max_length=30, blank=True, null=True, unique=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=40, null=True, blank=True, default="", verbose_name="Shortname")
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    position = models.ForeignKey('Position', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Position")
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Employee")
    title = models.ForeignKey(EmployeeTitle, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Title")

    class Meta:
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        if self.effective and self.position and self.employee:
            yymm = self.effective.strftime('%y%m')
            self.code = f"{self.position.code}-{self.employee.code}-{yymm}"

        if self.employee and self.position and hasattr(self.employee, 'person'):
            self.name = f"{self.employee.person.name}, {self.position.name}"

        super().save(*args, **kwargs)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Position                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain positions in the company                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\structure.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/19-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝          
class Position(GenericAbstract):
    code = models.CharField(max_length=15, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    level = models.IntegerField(null=True, blank=True, default=None, verbose_name="Level")
    title = models.ForeignKey(EmployeeTitle, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Title")
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    parent = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="Parent")
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Organization")

    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positions"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Organization                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain organization in the company              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\structure.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/6-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝     
class Organization(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Shortname")
    type = models.ForeignKey('OrganizationType', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Type")
    parent = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Parent")
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    terminated = models.DateField(null=True, blank=True, verbose_name= "Terminated")
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def get_children_tree(self):
        children = Organization.objects.filter(parent=self, deleted=False, status=1)
        return {
            'id': self.id,
            'name': self.name,
            'children': [child.get_children_tree() for child in children]
        }

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Organization Type                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain organization type  in the company        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\structure.py               ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝              
class OrganizationType(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")

    class Meta:
        verbose_name = "Organization Type"
        verbose_name_plural = "Organization Types"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
