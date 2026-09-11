from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models.abstracts import GenericAbstract
from apps.humancapital.models.employee import EmployeeTitle


class PerformanceModel(GenericAbstract):
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Code"))
    initial = models.CharField(
        max_length=15, blank=True, default="", verbose_name=_("Initial")
    )
    shortname = models.CharField(
        max_length=40, blank=True, default="", verbose_name=_("Short name")
    )

    class Meta:
        verbose_name = _("Performance model")
        verbose_name_plural = _("Performance models")
        ordering = ("code",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
        ]

    def __str__(self):
        return self.name or self.code


class PerformanceGroup(GenericAbstract):
    performance_model = models.ForeignKey(
        PerformanceModel,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name=_("Performance model"),
    )
    code = models.CharField(max_length=20, verbose_name=_("Code"))
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name=_("Order"))
    bobot = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Bobot (%)"),
    )
    initial = models.CharField(
        max_length=15, blank=True, default="", verbose_name=_("Initial")
    )
    shortname = models.CharField(
        max_length=40, blank=True, default="", verbose_name=_("Short name")
    )

    class Meta:
        verbose_name = _("Performance group")
        verbose_name_plural = _("Performance groups")
        ordering = ("performance_model", "sort_order", "code")
        unique_together = [("performance_model", "code")]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
        ]

    def __str__(self):
        return f"{self.performance_model.code}:{self.code}"


class PerformanceObjective(GenericAbstract):

    performance_model = models.ForeignKey(
        PerformanceModel,
        on_delete=models.CASCADE,
        related_name="objectives",
        verbose_name=_("Performance model"),
    )
    performance_group = models.ForeignKey(
        PerformanceGroup,
        on_delete=models.CASCADE,
        related_name="objectives",
        verbose_name=_("Performance group"),
    )
    code = models.CharField(max_length=30, verbose_name=_("Code"))
    perf_code = models.CharField(max_length=30, verbose_name=_("Perf code"))
    level_label = models.CharField(
        max_length=80, blank=True, default="", verbose_name=_("Level label")
    )
    objective = models.TextField(blank=True, default="", verbose_name=_("Objective"))

    class Meta:
        verbose_name = _("Performance objective")
        verbose_name_plural = _("Performance objectives")
        ordering = ("performance_model", "code")
        unique_together = [("performance_model", "code")]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
        ]

    def __str__(self):
        return self.perf_code


class LevelObjectiveRule(GenericAbstract):

    employee_title = models.ForeignKey(
        EmployeeTitle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kpi_level_rules",
        verbose_name=_("Employee title / level"),
    )
    level_name = models.CharField(
        max_length=80,
        blank=True,
        default="",
        verbose_name=_("Level name (fallback)"),
        help_text=_("Used when title FK is not matched."),
    )
    site_code = models.CharField(
        max_length=40, blank=True, default="", verbose_name=_("Site code")
    )
    period_year = models.PositiveIntegerField(verbose_name=_("Period (year)"))
    performance_model = models.ForeignKey(
        PerformanceModel,
        on_delete=models.CASCADE,
        related_name="level_rules",
        verbose_name=_("Performance model"),
    )
    performance_group = models.ForeignKey(
        PerformanceGroup,
        on_delete=models.CASCADE,
        related_name="level_rules",
        verbose_name=_("Performance group"),
    )
    perf_code = models.CharField(max_length=40, verbose_name=_("Perf code"))
    rule_label = models.CharField(
        max_length=120, blank=True, default="", verbose_name=_("Label")
    )
    external_rule_id = models.CharField(
        max_length=40, blank=True, default="", verbose_name=_("External rule id")
    )

    class Meta:
        verbose_name = _("Level objective rule")
        verbose_name_plural = _("Level objective rules")
        ordering = ("period_year", "site_code", "perf_code")
        indexes = [
            models.Index(fields=["period_year", "site_code"]),
        ]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
        ]

    def __str__(self):
        return f"{self.period_year} {self.perf_code}"


class EmployeeKPIPeriod(GenericAbstract):

    employee = models.ForeignKey(
        "humancapital.Employee",
        on_delete=models.CASCADE,
        related_name="kpi_periods",
        verbose_name=_("Employee"),
    )
    year = models.PositiveIntegerField(verbose_name=_("Year"))
    company_name = models.CharField(
        max_length=120, blank=True, default="", verbose_name=_("Company")
    )

    class Meta:
        verbose_name = _("Employee KPI period")
        verbose_name_plural = _("Employee KPI periods")
        unique_together = [("employee", "year")]
        ordering = ("-year", "employee__name")
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
            ("import_kpi", "Can import KPI recap data"),
        ]

    def __str__(self):
        return f"{self.employee} {self.year}"


class EmployeeKPILine(GenericAbstract):
    
    period = models.ForeignKey(
        EmployeeKPIPeriod,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name=_("Period"),
    )
    performance_group = models.ForeignKey(
        PerformanceGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kpi_lines",
        verbose_name=_("Performance group"),
    )
    performance_objective = models.ForeignKey(
        PerformanceObjective,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kpi_lines",
        verbose_name=_("Objective"),
    )
    line_no = models.PositiveIntegerField(default=1, verbose_name=_("Line no"))
    external_code = models.CharField(
        max_length=80,
        blank=True,
        default="",
        verbose_name=_("External code"),
    )
    indicator = models.CharField(max_length=255, verbose_name=_("KPI indicator"))
    uom = models.CharField(max_length=40, blank=True, default="", verbose_name=_("UoM"))
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Weight"),
    )
    target = models.TextField(blank=True, default="", verbose_name=_("Target"))
    achievement = models.TextField(blank=True, default="", verbose_name=_("Achievement"))
    final_score = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Final score"),
    )
    notes = models.CharField(
        max_length=500, blank=True, default="", verbose_name=_("Notes")
    )

    class Meta:
        verbose_name = _("Employee KPI line")
        verbose_name_plural = _("Employee KPI lines")
        ordering = ("period", "line_no")
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore items"),
        ]

    def __str__(self):
        return f"{self.period_id} #{self.line_no} {self.indicator[:40]}"
