from django import forms
from apps.sales.models.product import Product
from django.contrib import messages


class ProductsForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "remark",
            "slug",
            "code",
            "initial",
            "shortname",
            "size",
            "height",
            "length",
            "width",
            "weight",
            "category",
            "owner",
            "package",
            "subgroup",
            "business",
            "packaging",
            "targetgroup",
            "uom",
            "box_per_palletac",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "initial": forms.TextInput(attrs={"class": "form-control"}),
            "shortname": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
            "size": forms.NumberInput(attrs={"class": "form-control"}),
            "height": forms.NumberInput(attrs={"class": "form-control"}),
            "length": forms.NumberInput(attrs={"class": "form-control"}),
            "width": forms.NumberInput(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(attrs={"class": "form-control"}),
            "box_per_palletac": forms.NumberInput(attrs={"class": "form-control"}),
            "targetgroup": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control select2"}),
            "owner": forms.Select(attrs={"class": "form-control select2"}),
            "package": forms.Select(attrs={"class": "form-control select2"}),
            "subgroup": forms.Select(attrs={"class": "form-control select2"}),
            "business": forms.Select(attrs={"class": "form-control select2"}),
            "packaging": forms.Select(attrs={"class": "form-control select2"}),
            "uom": forms.Select(attrs={"class": "form-control select2"}),
        }
