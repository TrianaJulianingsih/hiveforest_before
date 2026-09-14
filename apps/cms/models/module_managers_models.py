from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.base.mixins import SystemLogModelMixin
from apps.cms.models.app_managers_models import ApplicationList

class ModuleList(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="Shortname")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="Icon")  # Icon for UI rendering
    application = models.ForeignKey('cms.ApplicationList', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Application")
    order = models.PositiveIntegerField(default=0)  # Ordering menus

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    # def save(self, *args, **kwargs):
    #     if self.application:
    #         self.description = f"{self.name} in {self.application.name}"
    #     if self.initial:
    #         self.code = f"{self.application.code}-{self.initial}"
    #     super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if self.application and self.initial:
            self.code = f"{self.application.code}-{self.initial}"
        self.description = f"{self.name} in {self.application.name}" if self.application else self.description
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.shortname} | {self.application}"
