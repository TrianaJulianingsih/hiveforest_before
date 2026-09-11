from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_currentuser.middleware import get_current_user
from django_currentuser.middleware import get_current_authenticated_user
from .managers import NonDeletedManager
from apps.base.choices import STATUS_CHOICES, Status

class GenericAbstract(models.Model):
    name = models.CharField(max_length=100, null=False, blank=True, default="", verbose_name="Name")
    description = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Description")
    remark = models.CharField(max_length=255, null=True, blank=True, verbose_name="Remark")
    status = models.IntegerField(choices=STATUS_CHOICES, default=Status.ACTIVE.value, verbose_name="Status")
    slug = models.SlugField(max_length=255, default=None, unique=True, blank=True, null=True, verbose_name="Slug")
    cat = models.DateTimeField(
        auto_now_add=True,
        verbose_name= "Created at"
    )
    cby = models.ForeignKey(
        'auth.user',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Created by"
    )
    uat = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Updated at"
    )
    uby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
        null=True,
        blank=True,
        editable=False,
        verbose_name="Updated by"
    )
    dat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted at"
    )
    dby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_deleted",
        null=True,
        blank=True,
        editable=False,
        verbose_name="Deleted by"
    )
    deleted = models.BooleanField(default=False) # Soft Delete flag
    

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        # Slug generation
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        # Handle cby & uby
        user = kwargs.pop('user', get_current_authenticated_user())
        if not self.pk:  # On create
            if user:
                self.cby = user  # Set 'created by'
            self.uat = None  # 'Updated at' should not be set on creation
            self.uby = None  # 'Updated by' should not be set on creation
        else:  # On update
            if user:
                self.uby = user  # Set 'updated by'
            self.uat = timezone.now()  # Always update the 'updated at' timestamp

        if self.status == 'Active':
            self.status = 1
        elif self.status == 'Inactive':
            self.status = 0

        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        user = get_current_user()
        self.deleted = True
        self.dat = timezone.now()
        self.dby = user
        self.save()

    def is_deleted(self):
        return self.deleted

    objects = models.Manager()
    nondeleted_objects = NonDeletedManager()

    class Meta:
        abstract = True
