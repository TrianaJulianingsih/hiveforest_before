from django import forms
from dal import autocomplete
from apps.humancapital.models.structure import Organization, OrganizationType

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Organizations                                       ║
# ║  Type: Forms                                               ║
# ║  Purpose: To prepare form for the template                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\forms\organization_form.py        ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: Jul/7-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class OrganizationForm(forms.ModelForm):
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
        })
    )
    name = forms.CharField(
        label='Name',
        required=True,
        widget=forms.TextInput(attrs={
            'required': True,
            'class': 'form-control form-control-sm w-50'
        })
    )
    initial = forms.CharField(
        label='Initial',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 15%;'
        })
    )
    shortname = forms.CharField(
        label='Shortname',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 25%;'
        })
    )
    type = forms.ModelChoiceField(
        label='Type',
        queryset=OrganizationType.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:orgtype-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for a type ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
            }
        )
    )
    parent = forms.ModelChoiceField(
        label='Parent',
        queryset=Organization.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:org-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for an organization ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
            }
        )
    )
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
        model = Organization
        fields = ['code', 'name', 'initial', 'shortname', 'type', 'parent', 'description', 'remark', 'effective', 'terminated', 'status']
        widgets = {
            'type': autocomplete.ModelSelect2(url='humancapital:type-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode", "edit")

        type_qs = kwargs.pop('type_qs', OrganizationType.objects.filter(status=1))
        parent_qs = kwargs.pop('parent_qs', Organization.objects.filter(status=1))
        super().__init__(*args, **kwargs)
        self.fields['type'].queryset = type_qs
        self.fields['parent'].queryset = parent_qs

    def save(self, commit=True):
        organization = super().save(commit=False)
        if commit:
            organization.save()
        return organization
