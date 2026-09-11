from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.base.models.people import Person, Gender

class Employee(GenericAbstract):
    EMPLOYMENT_REGULAR = 'regular'
    EMPLOYMENT_PROBATION = 'probation'
    EMPLOYMENT_STATUS_CHOICES = (
        (EMPLOYMENT_REGULAR, _('Regular')),
        (EMPLOYMENT_PROBATION, _('Probation')),
    )

    person = models.OneToOneField(Person, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Person')
    code = models.CharField(max_length=10, null=False, default="", verbose_name='Code')
    hired = models.DateField(null=True, blank=True, verbose_name= 'Hired')
    terminated = models.DateField(null=True, blank=True, verbose_name= 'Terminated')
    employment_status = models.CharField(
        max_length=12,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default=EMPLOYMENT_REGULAR,
        verbose_name=_('Employment status'),
    )

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.person.name}"
        super().save(*args, **kwargs)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeeTitle                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain title of employee like Staff, Manager    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\employee.py                ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝                
class EmployeeTitle(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default='', verbose_name='Code')
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name='Initial')
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name='Shortname')

    class Meta:
        verbose_name = 'Employee Title'
        verbose_name_plural = 'Employee Titles'
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    # May/23-2025
    def __str__(self):
        return self.name 
