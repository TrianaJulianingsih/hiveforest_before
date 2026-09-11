from django.contrib import admin

from apps.performance.models import (
    EmployeeKPILine,
    EmployeeKPIPeriod,
    LevelObjectiveRule,
    PerformanceGroup,
    PerformanceModel,
    PerformanceObjective,
)


@admin.register(PerformanceModel)
class PerformanceModelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "shortname", "initial", "status")
    search_fields = ("code", "name", "shortname")


@admin.register(PerformanceGroup)
class PerformanceGroupAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "performance_model", "sort_order", "bobot", "initial")
    list_filter = ("performance_model",)
    search_fields = ("code", "name", "shortname")


@admin.register(PerformanceObjective)
class PerformanceObjectiveAdmin(admin.ModelAdmin):
    list_display = ("perf_code", "code", "performance_model", "performance_group")
    list_filter = ("performance_model", "performance_group")
    search_fields = ("code", "perf_code", "objective")


@admin.register(LevelObjectiveRule)
class LevelObjectiveRuleAdmin(admin.ModelAdmin):
    list_display = (
        "period_year",
        "site_code",
        "perf_code",
        "performance_model",
        "performance_group",
        "employee_title",
        "level_name",
    )
    list_filter = ("period_year", "performance_model")
    search_fields = ("perf_code", "level_name", "external_rule_id")


class EmployeeKPILineInline(admin.TabularInline):
    model = EmployeeKPILine
    extra = 0
    raw_id_fields = ("performance_group", "performance_objective")


@admin.register(EmployeeKPIPeriod)
class EmployeeKPIPeriodAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "company_name", "status")
    list_filter = ("year",)
    search_fields = ("employee__name", "company_name")
    raw_id_fields = ("employee",)
    inlines = [EmployeeKPILineInline]


@admin.register(EmployeeKPILine)
class EmployeeKPILineAdmin(admin.ModelAdmin):
    list_display = ("period", "line_no", "indicator", "weight", "performance_group")
    list_filter = ("period__year",)
    search_fields = ("indicator", "external_code")
    raw_id_fields = ("period", "performance_group", "performance_objective")
