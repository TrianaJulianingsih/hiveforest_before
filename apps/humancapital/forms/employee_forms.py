from django import forms
from apps.base.models.people import Person, Gender
from apps.humancapital.models.employee_models import Employee

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeePersonForm                                  ║
# ║  Type: Forms                                               ║
# ║  Purpose: To prepare form for the template                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\forms\employee_forms.py           ║
# ║  Created: May/09-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class EmployeePersonForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive')
    )
    # Employee fields
    code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'required': False,
            'class': 'form-control form-control-sm',
            'style': 'width: 25%;'
        })
    )
    hired = forms.DateField(
        label='Hired',
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
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm w-auto',
            'style': 'width:15%;'
    }))
    employment_status = forms.ChoiceField(
        label='Employment status',
        choices=Employee.EMPLOYMENT_STATUS_CHOICES,
        initial=Employee.EMPLOYMENT_REGULAR,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm w-auto',
            'style': 'width:25%;'
        })
    )
    
    # Person fields
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'required': True,
            'class': 'form-control form-control-sm w-25'
        })
    )
    middle_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm w-25'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'required': True,
            'class': 'form-control form-control-sm w-25'
        })
    )
    nickname = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'required': False,
            'class': 'form-control form-control-sm w-25'
        })
    )
    initial = forms.CharField(
        required=False,
        label='Initial',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width:15%;',
            'placeholder': '2-3 chars',
        }),
    )
    gender = forms.ModelChoiceField(
        queryset=Gender.objects.all(),
        required=False,
        empty_label='--- Select ---',
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width:15%;'
        })
    )
    dob = forms.DateField(
        label='Birth Date',
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control form-control-sm w-auto',
                'type': 'date',  # Native HTML5 date picker
            },
        ),
    )
    national_id = forms.CharField(
        required=False,
        label='National ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width:25%;',
        }),
    )
    tax_id = forms.CharField(
        required=False,
        label='Tax ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width:25%;',
        }),
    )

    class Meta:
        model = Employee
        fields = ['code', 'hired', 'terminated', 'employment_status', 'description', 'remark', 'status']

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode", "edit")

        gender_qs = kwargs.pop('gender_qs', Gender.objects.all())
        super().__init__(*args, **kwargs)
        self.fields['gender'].queryset = gender_qs

        # Populate initial values from person if instance exists
        if self.instance and self.instance.person:
            person = self.instance.person
            self.fields['first_name'].initial = person.first_name
            self.fields['middle_name'].initial = person.middle_name
            self.fields['last_name'].initial = person.last_name
            self.fields['nickname'].initial = person.nickname
            self.fields['initial'].initial = person.initial
            self.fields['gender'].initial = person.gender
            self.fields['dob'].initial = person.dob
            self.fields['national_id'].initial = person.national_id
            self.fields['tax_id'].initial = person.tax_id

            if mode == 'view':
                for name, field in self.fields.items():
                    widget = field.widget
                    css_class = widget.attrs.get('class', '')
                    widget.attrs['class'] = f"{css_class} form-control form-control-sm"

                    # Select fields must use disabled
                    if isinstance(widget, (forms.Select, forms.RadioSelect)):
                        field.disabled = True
                        widget.attrs['style'] = 'pointer-events: none; background-color: transparent; border: none;'
                    else:
                        widget.attrs['readonly'] = True

    def save(self, commit=True):
        employee = super().save(commit=False)
        person = employee.person or Person()

        person.first_name = self.cleaned_data['first_name']
        person.middle_name = self.cleaned_data['middle_name']
        person.last_name = self.cleaned_data['last_name']
        person.nickname = self.cleaned_data['nickname']
        person.initial = self.cleaned_data['initial']
        person.gender = self.cleaned_data['gender']
        person.dob = self.cleaned_data['dob']
        person.national_id = self.cleaned_data['national_id']
        person.tax_id = self.cleaned_data['tax_id']
        person.save()

        employee.person = person
        if commit:
            employee.save()
        return employee
