from django import forms
from apps.supplychain.models.distributions import Branch


class BranchsForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            "name",
            "slug",
            "code",
            "initial",
            "shortname",
            "address",
            "has_sales",
            "has_stock",
            "has_order",
            "distributor",
            "type",
            "shipto",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "initial": forms.TextInput(attrs={"class": "form-control"}),
            "shortname": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "has_sales": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_stock": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_order": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "distributor": forms.Select(attrs={"class": "form-select select2"}),
            "type": forms.Select(attrs={"class": "form-select select2"}),
            "shipto": forms.TextInput(attrs={"class": "form-control"}),
        }
