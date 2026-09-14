from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.base.models.people import Person
from apps.sales.models.customer_models import Customer
from django_currentuser.middleware import get_current_authenticated_user
from apps.base.mixins import SystemLogModelMixin

class KPDMContact(SystemLogModelMixin, GenericAbstract):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="kpdm_contacts", verbose_name='Person')

    class Meta:
        verbose_name = 'KPDM Contact'
        verbose_name_plural = 'KPDM Contacts'
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"KPDM: {self.person.name}"
    
    def save(self, *args, **kwargs):
        if not self.name:  # if display_name is blank
            self.name = f"{self.person.name}"
        super().save(*args, **kwargs)
    
class KPDMCustomer(SystemLogModelMixin, GenericAbstract):
    kpdm = models.ForeignKey(KPDMContact, on_delete=models.CASCADE, related_name='customer_links', verbose_name='KPDM')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='kpdm_links', verbose_name='Customer')
    assigned_by = models.ForeignKey('auth.user', on_delete=models.SET_NULL, null=True, blank=True, editable=False, verbose_name='Assigned by')
    assigned_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Assigned at')

    class Meta:
        unique_together = ('kpdm', 'customer')
        verbose_name = 'KPDM-Customer Link'
        verbose_name_plural = 'KPDM-Customer Links'
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.kpdm.person.name}-{self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.name:  # if display_name is blank
            self.name = f"{self.kpdm}-{self.customer.name}"
        super().save(*args, **kwargs)
