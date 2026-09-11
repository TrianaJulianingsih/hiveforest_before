from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.utils.text import slugify

class Person(GenericAbstract):
    salutation = models.ForeignKey("Salutation", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=50, verbose_name='First Name')
    middle_name = models.CharField(max_length=75, blank=True, null=True, verbose_name='Middle Name')
    last_name = models.CharField(max_length=50, verbose_name='Last Name', blank=True, null=True)
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    nickname = models.CharField(max_length=25, blank=True, null=True, verbose_name='Nick Name')
    gender = models.ForeignKey('base.Gender', on_delete=models.PROTECT, null=True, blank=True, verbose_name="Gender")
    dob = models.DateField(null=True, blank=True, verbose_name= 'Date of Birth')
    national_id = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='National ID')
    tax_id = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name='Tax ID')
    roles = models.ManyToManyField('base.ContactRole', blank=True, related_name='people', verbose_name='Contact Roles')
    
    @property
    def full_name(self):
        return ' '.join(filter(None, [self.first_name, self.middle_name, self.last_name]))

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('name').verbose_name = 'Display Name'

    def save(self, *args, **kwargs):
        if not self.name:  # if display_name is blank
            parts = [self.first_name, self.middle_name, self.last_name]
            self.name = ' '.join(filter(None, parts))
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class Salutation(GenericAbstract):
    code = models.CharField(max_length=30, null=True, verbose_name="Code")  # e.g., "mr", "mrs", "bpk", "ibu", "san"
    initial = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Initial")

    class Meta:
        verbose_name = "Salutation"
        verbose_name_plural = "Salutations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    
class Gender(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="M", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Gender"
        verbose_name_plural = "Genders"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
