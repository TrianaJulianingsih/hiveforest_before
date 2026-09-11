from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.humancapital.models import Employee
from apps.performance.models import (
    EmployeeKPILine,
    EmployeeKPIPeriod,
    PerformanceGroup,
    PerformanceModel,
    PerformanceObjective,
)

STATUS_CHOICES = ((1, "Active"), (0, "Inactive"))


class PerformanceModelForm(forms.ModelForm):
    code = forms.CharField(
        label=_("Code"),
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 15%;"}),
    )
    name = forms.CharField(
        label=_("Name"),
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm w-50"}),
    )
    initial = forms.CharField(
        label=_("Initial"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 15%;"}),
    )
    shortname = forms.CharField(
        label=_("Shortname"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 25%;"}),
    )
    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control form-control-sm", "placeholder": _("Short description"), "style": "height: 70px;"}
        ),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control form-control-sm w-auto", "style": "width:15%;"}),
    )

    class Meta:
        model = PerformanceModel
        fields = ("code", "name", "initial", "shortname", "description", "status")

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        if not code:
            raise forms.ValidationError(_("Code is required."))
        qs = PerformanceModel.objects.filter(code=code, deleted=False)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("A performance model with this code already exists."))
        return code


class PerformanceGroupForm(forms.ModelForm):
    code = forms.CharField(
        label=_("Code"),
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 15%;"}),
    )
    name = forms.CharField(
        label=_("Name"),
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm w-50"}),
    )
    performance_model = forms.ModelChoiceField(
        label=_("Performance model"),
        queryset=PerformanceModel.objects.none(),
        widget=forms.Select(attrs={"class": "form-control form-control-sm w-50"}),
    )
    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control form-control-sm", "placeholder": _("Short description"), "style": "height: 70px;"}
        ),
    )
    bobot = forms.DecimalField(
        label=_("Bobot (%)"),
        required=True,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm w-auto", "min": 0, "max": 100, "step": "0.01", "style": "width: 10%;"}
        ),
    )
    sort_order = forms.IntegerField(
        label=_("Sort order"),
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm w-auto", "min": 0, "style": "width: 10%;"}),
    )
    initial = forms.CharField(
        label=_("Initial"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 15%;"}),
    )
    shortname = forms.CharField(
        label=_("Shortname"),
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "style": "width: 25%;"}),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control form-control-sm w-auto", "style": "width:15%;"}),
    )

    class Meta:
        model = PerformanceGroup
        fields = (
            "performance_model",
            "code",
            "name",
            "description",
            "bobot",
            "sort_order",
            "initial",
            "shortname",
            "status",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["performance_model"].queryset = PerformanceModel.objects.filter(
            deleted=False, status=1
        ).order_by("code")

    def clean(self):
        cleaned = super().clean()
        perf_model = cleaned.get("performance_model")
        code = cleaned.get("code")
        if perf_model and code:
            qs = PerformanceGroup.objects.filter(
                performance_model=perf_model, code=code, deleted=False
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    _("A performance group with this code already exists for the selected model.")
                )
        return cleaned


class EmployeeKPIPeriodManualForm(forms.ModelForm):
    class Meta:
        model = EmployeeKPIPeriod
        fields = ("employee", "year", "company_name")
        widgets = {
            "employee": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "year": forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "min": 2000, "max": 2100}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": _("Company")}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = Employee.objects.filter(
            deleted=False, status=1
        ).select_related("person").order_by("name")
        self.fields["employee"].label = _("Employee")
        self.fields["year"].label = _("Year")
        self.fields["company_name"].label = _("Company name")

    def clean(self):
        cleaned = super().clean()
        emp = cleaned.get("employee")
        year = cleaned.get("year")
        if emp and year:
            qs = EmployeeKPIPeriod.objects.filter(employee=emp, year=year, deleted=False)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    _("A KPI period for this employee and year already exists.")
                )
        return cleaned


class EmployeeKPILineManualForm(forms.ModelForm):
    class Meta:
        model = EmployeeKPILine
        fields = (
            "line_no",
            "external_code",
            "performance_group",
            "performance_objective",
            "indicator",
            "uom",
            "weight",
            "target",
            "achievement",
            "final_score",
            "notes",
        )
        widgets = {
            "line_no": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": 1}),
            "external_code": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "performance_group": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "performance_objective": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "indicator": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "uom": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "weight": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "target": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
            "achievement": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
            "final_score": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "notes": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["performance_group"].queryset = PerformanceGroup.objects.filter(
            deleted=False, status=1
        ).select_related("performance_model").order_by(
            "performance_model__code", "sort_order", "code"
        )
        self.fields["performance_group"].required = False
        self.fields["performance_objective"].queryset = PerformanceObjective.objects.filter(
            deleted=False, status=1
        ).select_related("performance_group").order_by("code")
        self.fields["performance_objective"].required = False
        self.fields["line_no"].label = _("No.")
        self.fields["external_code"].label = _("External code / KPI ID")
        self.fields["performance_group"].label = _("Performance group")
        self.fields["performance_objective"].label = _("Objective (optional)")
        self.fields["indicator"].label = _("KPI indicator")
        self.fields["uom"].label = _("UoM")
        self.fields["weight"].label = _("Weight")
        self.fields["target"].label = _("Target")
        self.fields["achievement"].label = _("Achievement")
        self.fields["final_score"].label = _("Final score")
        self.fields["notes"].label = _("Notes / Keterangan")


def get_kpi_line_formset(extra=1):
    return inlineformset_factory(
        EmployeeKPIPeriod,
        EmployeeKPILine,
        form=EmployeeKPILineManualForm,
        extra=extra,
        can_delete=True,
        min_num=0,
        validate_min=False,
    )
