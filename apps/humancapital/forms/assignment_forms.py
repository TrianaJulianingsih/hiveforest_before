from django import forms
from dal import autocomplete
from apps.humancapital.models.employee_models import Employee, EmployeeTitle
from apps.humancapital.models.structure_models import Position, Assignment

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeeAssignmentForm                              ║
# ║  Type: Forms                                               ║
# ║  Purpose: To prepare form for the template                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\forms\assignment_forms.py         ║
# ║  Created: May/21-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class EmployeeAssignmentForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive')
    )
    code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'required': False,
            'class': 'form-control form-control-sm',
            'style': 'width: 25%;'
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
            'style': 'width: 15%;'
        })
    )
    employee = forms.ModelChoiceField(
        label='Employee',
        queryset=Employee.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:emp-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for an employee...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
            }
        )
    )
    position = forms.ModelChoiceField(
        label='Position',
        queryset=Position.objects.filter(status=1),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='humancapital:pos-autocomplete',  # this must match your URL name
            attrs={
                'data-placeholder': 'Search for a position ...',
                'data-minimum-input-length': 2,
                'data-theme': 'bootstrap4',
                'data-width': '50%;',
            }
        )
    )
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
    description = forms.CharField(
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
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm w-auto',
            'style': 'width:15%;'
    }))
    
    class Meta:
        model = Assignment
        fields = ['code', 'name', 'initial', 'shortname', 'employee', 'position', 'title', 'description', 'remark', 'effective', 'terminated', 'status']
        widgets = {
            'employee': autocomplete.ModelSelect2(url='humancapital:employee-autocomplete'),
            'position': autocomplete.ModelSelect2(url='humancapital:position-autocomplete'),
            'title': autocomplete.ModelSelect2(url='humancapital:employeetitle-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode", "edit")

        title_qs = kwargs.pop('title_qs', EmployeeTitle.objects.filter(status=1))
        related1_qs = kwargs.pop('related1_qs', Employee.objects.filter(status=1))
        related2_qs = kwargs.pop('related2_qs', Position.objects.filter(status=1))

        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = related1_qs
        self.fields['position'].queryset = related2_qs
        self.fields['title'].queryset = title_qs

    def save(self, commit=True):
        assignment = super().save(commit=False)
        if commit:
            assignment.save()
        return assignment
