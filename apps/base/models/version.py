from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django_summernote.fields import SummernoteTextField
from apps.base.models.abstracts import GenericAbstract


# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════
class AppVersion(GenericAbstract):
    version_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d+\.\d+(\.\d+)?$",
                message=_("Version format must be like: 1.0, 1.1, 2.0.1"),
            )
        ],
        verbose_name=_("Version Number"),
        help_text=_("Example: 1.0, 1.1, 2.0.1"),
    )

    release_date = models.DateField(
        verbose_name=_("Release Date"), help_text=_("Release date of this version")
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Release Title"),
        help_text=_("Title of this release"),
        blank=True,
    )

    description = SummernoteTextField(
        verbose_name=_("Description"),
        help_text=_("General description of this release"),
        blank=True,
    )

    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Current Version"),
        help_text=_("Check if this is the current running version"),
    )

    is_major_release = models.BooleanField(
        default=False,
        verbose_name=_("Major Release"),
        help_text=_("Check if this is a major release"),
    )

    class Meta:
        db_table = "base_appversion"
        verbose_name = _("App Version")
        verbose_name_plural = _("App Versions")
        ordering = ["-release_date", "-version_number"]
        indexes = [
            models.Index(fields=["-release_date"]),
            models.Index(fields=["is_current"]),
        ]
        permissions = [
            ("soft_delete", "Can delete version"),
            ("soft_restore", "Can restore deleted version"),
        ]

    def __str__(self):
        return f"{self.version_number} - {self.release_date}"

    def save(self, *args, **kwargs):
        if self.is_current:
            AppVersion.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current_version(cls):
        try:
            return cls.objects.filter(is_current=True).first()
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_latest_version(cls):
        return cls.objects.first()


class VersionFeature(GenericAbstract):
    FEATURE_TYPE_CHOICES = [
        ("new", _("New Feature")),
        ("improvement", _("Improvement")),
        ("bugfix", _("Bug Fix")),
        ("security", _("Security Update")),
        ("deprecation", _("Deprecation")),
    ]

    version = models.ForeignKey(
        AppVersion,
        on_delete=models.CASCADE,
        related_name="features",
        verbose_name=_("Version"),
    )

    feature_type = models.CharField(
        max_length=20,
        choices=FEATURE_TYPE_CHOICES,
        default="new",
        verbose_name=_("Feature Type"),
    )

    title = models.CharField(max_length=200, verbose_name=_("Feature Title"))

    description = SummernoteTextField(verbose_name=_("Description"), blank=True)

    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Order"), help_text=_("Order of feature display")
    )

    class Meta:
        db_table = "base_versionfeature"
        verbose_name = _("Version Feature")
        verbose_name_plural = _("Version Features")
        ordering = ["order", "-cat"]
        permissions = [
            ("soft_delete", "Can delete version feature"),
            ("soft_restore", "Can restore deleted version feature"),
        ]

    def __str__(self):
        return f"{self.version.version_number} - {self.title}"
