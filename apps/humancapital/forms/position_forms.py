from django import forms
from dal import autocomplete
from apps.humancapital.models.employee_models import Employee, EmployeeTitle
from apps.humancapital.models.structure_models import Position, Organization

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Positions                                           ║
# ║  Type: Forms                                               ║
# ║  Purpose: To prepare form for the template                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\forms\position_forms.py           ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class PositionForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive')
    )
    code = forms.CharField(
        label='Code',
        required=True,
        widget=forms.TextInput(attrs={
            'required': False,
            'class': 'form-control form-control-sm',
            'style': 'width: 10%;'
    }))
    name = forms.CharField(
        label='Name',
        required=True,
        widget=forms.TextInput(attrs={
            'required': True,
            'class': 'form-control form-control-sm w-50'
    }))
    initial = forms.CharField(
        label='Initial',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 15%;'
    }))
    shortname = forms.CharField(
        label='Shortname',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 15%;'
    }))
    level = forms.IntegerField(
        label='Level',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 15%;'
    }))
    title = forms.ModelChoiceField(
        label='Title',
        queryset=EmployeeTitle.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:emptitle-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for a title ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
    }))
    parent = forms.ModelChoiceField(
        label='Parent',
        queryset=Position.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:pos-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for a position ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
    }))
    organization = forms.ModelChoiceField(
        label='Organization',
        queryset=Organization.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:org-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for an organization  ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
    }))
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Short description',
                'style': 'height: 70px;'
            },
        ),
    )
    remark = forms.CharField(
        label='Remark',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Short remark',
                'style': 'height: 70px;'
    }))
    effective = forms.DateField(
        label='Effective',
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control form-control-sm w-auto',
                'type': 'date',  # Native HTML5 date picker
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d']
    )
    terminated = forms.DateField(
        label='Terminated',
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control form-control-sm w-auto',
                'type': 'date',  # Native HTML5 date picker
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d']
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm w-auto',
            'style': 'width:15%;'
    }))

    class Meta:
        model = Position
        fields = ['code', 'name', 'initial', 'shortname', 'level', 'title', 'parent', 'organization', 'description', 'remark', 'effective', 'terminated', 'status']

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode", "edit")

        title_qs = kwargs.pop('title_qs', EmployeeTitle.objects.filter(status=1))
        parent_qs = kwargs.pop('parent_qs', Position.objects.filter(status=1))
        organization_qs = kwargs.pop('organization_qs', Organization.objects.filter(status=1))
        super().__init__(*args, **kwargs)
        self.fields['title'].queryset = title_qs
        self.fields['parent'].queryset = parent_qs
        self.fields['organization'].queryset = organization_qs

    def save(self, commit=True):
        position = super().save(commit=False)
        if commit:
            position.save()
        return position

    def clean_level(self):
        data = self.cleaned_data.get('level')
        return data if data is not None else None
