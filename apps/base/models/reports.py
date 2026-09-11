from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

class PeriodTemplate(GenericAbstract):
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('cyclical', 'Cyclical (4 mos.)'),
        ('semesterly', 'Semesterly (6 mos.)'),
        ('annually', 'Annually'),
    ]

    period = models.CharField(max_length=50, choices=PERIOD_CHOICES, null="True", default="monthly", verbose_name="Period")
    version = models.CharField(max_length=15, null=True, default="", verbose_name="Version")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")
    start_month = models.PositiveIntegerField(verbose_name="Start Month")  # 1 = January, 12 = December
    start_day = models.PositiveIntegerField(verbose_name="Start Day")
    end_month = models.PositiveIntegerField(verbose_name="End Month")
    end_day = models.PositiveIntegerField(verbose_name="End Day")

    class Meta:
        verbose_name = "Period Template"
        verbose_name_plural = "Period Templates"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


    def get_name_display_custom(self):
        # Manually get display value for 'name' since it is inherited
        return dict(self.PERIOD_CHOICES).get(self.name, self.name)

    def __str__(self):
        return f"{self.period} ({self.get_name_display_custom()})"
