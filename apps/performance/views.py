from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from apps.humancapital.models import Assignment, Employee
from apps.performance.forms import (
    EmployeeKPIPeriodManualForm,
    get_kpi_line_formset,
)
from apps.performance.models import (
    EmployeeKPILine,
    EmployeeKPIPeriod,
    PerformanceModel,
)


def can_manual_kpi(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return user.has_perm("performance.add_employeekpiperiod") or user.has_perm(
        "performance.change_employeekpiperiod"
    )


def _save_kpi_lines_only(formset):
    for obj in formset.deleted_objects:
        obj.delete()
    instances = formset.save(commit=False)
    for line in instances:
        if not (line.indicator or "").strip():
            if line.pk:
                line.delete()
            continue
        if not line.name:
            line.name = (line.indicator or "KPI")[:100]
        line.status = 1
        line.save()
    formset.save_m2m()


def _assignment_context(employee):
    """Prefer current assignment (active by dates), else latest by effective."""
    qs = Assignment.objects.filter(
        employee=employee,
        deleted=False,
        status=1,
    ).select_related(
        "position",
        "position__organization",
        "title",
        "employee",
        "employee__person",
    )
    assign = qs.order_by("-effective").first()
    if not assign:
        return {}
    pos = assign.position
    org = pos.organization if pos else None
    person = employee.person
    name = person.name if person else employee.name
    loc = ""
    if org:
        loc = getattr(org, "remark", "") or ""
    level_name = ""
    if assign.title:
        level_name = assign.title.name
    elif pos and pos.title_id:
        level_name = pos.title.name if pos.title else ""
    return {
        "employee_name": name,
        "position_name": pos.name if pos else "",
        "organization_name": org.name if org else "",
        "level_name": level_name,
        "site_label": loc or _("Head Office"),
        "period_year": None,
    }


@login_required
def kpi_dashboard(request):
    """Landing: shortcuts, counts, and setup notes."""
    today_y = date.today().year
    can_import = request.user.has_perm("performance.import_kpi") or request.user.is_staff
    ctx = {
        "default_year": today_y,
        "period_count": EmployeeKPIPeriod.objects.filter(deleted=False).count(),
        "line_count": EmployeeKPILine.objects.filter(deleted=False).count(),
        "model_count": PerformanceModel.objects.filter(deleted=False).count(),
        "can_import": can_import,
        "can_manual": can_manual_kpi(request.user),
    }
    return render(request, "performance/kpi_dashboard.html", ctx)


@login_required
def individual_view(request):
    employee_id = request.GET.get("employee") or request.GET.get("employee_id")
    year_str = request.GET.get("year")
    default_year = date.today().year
    employees = Employee.objects.filter(deleted=False, status=1).select_related(
        "person"
    ).order_by("name")

    ctx = {
        "employees": employees,
        "selected_employee_id": None,
        "year": None,
        "default_year": default_year,
        "header": {},
        "lines": [],
        "period": None,
        "company_name": "",
        "can_import": request.user.has_perm("performance.import_kpi")
        or request.user.is_staff,
        "can_manual": can_manual_kpi(request.user),
        "period_pk": None,
    }

    if not employee_id or not year_str:
        ctx["year"] = int(year_str) if year_str and str(year_str).isdigit() else default_year
        return render(request, "performance/individual_view.html", ctx)

    try:
        year = int(year_str)
        eid = int(employee_id)
    except (TypeError, ValueError):
        messages.error(request, _("Invalid employee or year."))
        ctx["year"] = default_year
        return render(request, "performance/individual_view.html", ctx)

    employee = Employee.objects.filter(pk=eid, deleted=False).select_related(
        "person"
    ).first()
    if not employee:
        messages.error(request, _("Employee not found."))
        ctx["year"] = year
        return render(request, "performance/individual_view.html", ctx)

    header = _assignment_context(employee)
    header["period_year"] = year

    period = (
        EmployeeKPIPeriod.objects.filter(employee=employee, year=year)
        .prefetch_related(
            Prefetch(
                "lines",
                queryset=EmployeeKPILine.objects.filter(deleted=False, status=1)
                .select_related(
                    "performance_group",
                    "performance_objective",
                    "performance_group__performance_model",
                )
                .order_by("line_no"),
            )
        )
        .first()
    )

    lines = []
    if period:
        ctx["period"] = period
        ctx["company_name"] = period.company_name
        for line in period.lines.all():
            pg = line.performance_group
            po = line.performance_objective
            if po and po.objective:
                strategic = po.objective
            elif pg:
                strategic = pg.name
            else:
                strategic = ""
            lines.append(
                {
                    "line_no": line.line_no,
                    "code": pg.code if pg else "",
                    "strategic_objective": strategic,
                    "kpi_id": line.external_code or "",
                    "indicator": line.indicator,
                    "uom": line.uom,
                    "weight": line.weight,
                    "target": line.target,
                    "achievement": line.achievement,
                    "final_score": line.final_score,
                    "notes": line.notes,
                    "perf_initial": pg.initial if pg else "",
                }
            )

    ctx.update(
        {
            "selected_employee_id": eid,
            "year": year,
            "header": header,
            "lines": lines,
            "can_manual": can_manual_kpi(request.user),
            "period_pk": period.pk if period else None,
        }
    )
    return render(request, "performance/individual_view.html", ctx)


@login_required
def import_view(request):
    if not request.user.has_perm("performance.import_kpi"):
        if not request.user.is_staff:
            messages.error(request, _("You do not have permission to import KPI data."))
            return redirect("performance:individual")

    if request.method == "POST" and request.FILES.get("file"):
        from apps.performance.services.import_recap import import_kpi_workbook

        f = request.FILES["file"]
        replace_lines = request.POST.get("replace_lines") == "on"
        result = import_kpi_workbook(f, replace_lines=replace_lines)
        for m in result.messages[:200]:
            messages.info(request, m)
        for e in result.errors[:50]:
            messages.error(request, e)
        if result.ok:
            messages.success(request, _("Import finished."))
        else:
            messages.warning(request, _("Import completed with errors."))
        return redirect("performance:import")

    can_import = request.user.has_perm("performance.import_kpi") or request.user.is_staff
    return render(
        request,
        "performance/import_kpi.html",
        {
            "can_import": can_import,
            "can_manual": can_manual_kpi(request.user),
        },
    )


@login_required
def period_manual_create(request):
    if not can_manual_kpi(request.user):
        messages.error(request, _("You do not have permission to edit KPI periods."))
        return redirect("performance:dashboard")

    LineFormSet = get_kpi_line_formset(extra=2)
    period = None
    if request.method == "POST":
        period_form = EmployeeKPIPeriodManualForm(request.POST)
        if period_form.is_valid():
            period = period_form.save(commit=False)
            period.name = f"{period.employee.name} {period.year}"
            period.status = 1
            period.save()
            formset = LineFormSet(request.POST, instance=period)
            if formset.is_valid():
                _save_kpi_lines_only(formset)
                messages.success(request, _("KPI period and lines saved."))
                return redirect("performance:period_manual_edit", pk=period.pk)
            messages.error(
                request,
                _("Correct the KPI lines below (header was saved)."),
            )
        else:
            formset = LineFormSet()
    else:
        initial = {"year": date.today().year}
        eid = request.GET.get("employee")
        y = request.GET.get("year")
        if eid and str(eid).isdigit():
            initial["employee"] = int(eid)
        if y and str(y).isdigit():
            initial["year"] = int(y)
        period_form = EmployeeKPIPeriodManualForm(initial=initial)
        formset = LineFormSet()

    return render(
        request,
        "performance/manual_period_form.html",
        {
            "period_form": period_form,
            "formset": formset,
            "is_create": not getattr(period, "pk", None),
            "period": period,
        },
    )


@login_required
def period_manual_edit(request, pk):
    if not can_manual_kpi(request.user):
        messages.error(request, _("You do not have permission to edit KPI periods."))
        return redirect("performance:dashboard")

    period = get_object_or_404(
        EmployeeKPIPeriod.objects.filter(deleted=False),
        pk=pk,
    )
    LineFormSet = get_kpi_line_formset(extra=1)

    if request.method == "POST":
        period_form = EmployeeKPIPeriodManualForm(request.POST, instance=period)
        formset = LineFormSet(request.POST, instance=period)
        if period_form.is_valid() and formset.is_valid():
            period = period_form.save(commit=False)
            period.name = f"{period.employee.name} {period.year}"
            period.save()
            _save_kpi_lines_only(formset)
            messages.success(request, _("KPI period saved."))
            return redirect("performance:period_manual_edit", pk=period.pk)
    else:
        period_form = EmployeeKPIPeriodManualForm(instance=period)
        formset = LineFormSet(instance=period)

    return render(
        request,
        "performance/manual_period_form.html",
        {
            "period_form": period_form,
            "formset": formset,
            "is_create": False,
            "period": period,
        },
    )


@login_required
def period_list(request):
    """Browse KPI periods (manual / import)."""
    if not request.user.is_authenticated:
        return redirect("login")
    periods = (
        EmployeeKPIPeriod.objects.filter(deleted=False)
        .select_related("employee")
        .prefetch_related("lines")
        .order_by("-year", "employee__name")
    )
    return render(
        request,
        "performance/period_list.html",
        {
            "periods": periods,
            "can_manual": can_manual_kpi(request.user),
        },
    )
