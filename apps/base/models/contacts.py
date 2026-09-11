from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.utils.text import slugify

class Contact(GenericAbstract):
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="contacts", verbose_name="Person")
    media = models.ForeignKey("ContactMedia", on_delete=models.PROTECT, verbose_name="Media")
    context = models.ForeignKey("ContactContext", on_delete=models.PROTECT, verbose_name="Context")

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:  # if display_name is blank
            self.name = f"{self.person.name} {self.context.name} {self.media.name}"
        super().save(*args, **kwargs)

class PhoneContact(Contact):
    country_code = models.CharField(max_length=5)
    number = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Phone Contact"
        verbose_name_plural = "Phone Contacts"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
            self.name = f"{self.person.name} {self.context.name} {self.media.name} {self.country_code}{self.number}".strip()
            super().save(*args, **kwargs)

class EmailContact(Contact):
    email = models.EmailField()
    
    class Meta:
        verbose_name = "Email Contact"
        verbose_name_plural = "Email Contacts"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
            self.name = f"{self.person.name} {self.context.name} {self.media.name} {self.email}".strip()
            super().save(*args, **kwargs)

class SocialContact(Contact):
    platform = models.ForeignKey("SocialPlatform", on_delete=models.PROTECT, verbose_name='Platform')
    handle = models.CharField(max_length=50, verbose_name='Handle')

    class Meta:
        verbose_name = 'Social Contact'
        verbose_name_plural = 'Social Contacts'    
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
            self.name = f"{self.person.name} {self.context.name} {self.media.name} {self.platform} {self.handle}".strip()
            super().save(*args, **kwargs)

class SocialPlatform(GenericAbstract):
    # 'instagram', 'whatsapp', 'facebook'
    code = models.CharField(max_length=15, unique=True, verbose_name="Code")

    class Meta:
        verbose_name = "Social Platform"
        verbose_name_plural = "Social Platforms"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
    
class ContactMedia(GenericAbstract):
    # 'email', 'phone', 'whatsapp'
    code = models.CharField(max_length=15, unique=True, verbose_name="Code")
    group = models.CharField(max_length=15, null=True, blank=True, verbose_name="Group")

    class Meta:
        verbose_name = "Contact Media"
        verbose_name_plural = "Contact Media"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
    
class ContactContext(GenericAbstract):
    # 'work', 'personal', etc.
    code = models.CharField(max_length=15, unique=True, verbose_name="Code")  

    class Meta:
        verbose_name = "Contact Context"
        verbose_name_plural = "Contact Context"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

class RoleCategory(GenericAbstract):
    code = models.CharField(max_length=15, unique=True, verbose_name='Code')
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")    

    class Meta:
        verbose_name = 'Role Category'
        verbose_name_plural = 'Role Categories'
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name
    
class ContactRole(GenericAbstract):
    code = models.CharField(max_length=15, unique=True, verbose_name='Code')
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial") 
    category = models.ForeignKey(RoleCategory, on_delete=models.CASCADE, related_name='roles')

    class Meta:
        verbose_name = "Contact Role"
        verbose_name_plural = "Contact Roles"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.name}"
