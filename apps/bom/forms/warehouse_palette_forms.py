from django import forms
from apps.base.models.warehouse import WarehousePalette
from django.contrib import messages


class WarehousePaletteForm(forms.ModelForm):
    class Meta:
        model = WarehousePalette
        fields = [
            "code",
            "initial",
            "shortname",
            "name",
            "description",
            "slug",
            "company",
            "ambient_capacity",
            "ac_room_capacity",
            "capacity",
            "branch",
        ]
        widgets = (
            {
                field: forms.TextInput(attrs={"class": "form-control"})
                for field in ["code", "initial", "shortname", "name"]
            }
            | {
                "slug": forms.TextInput(
                    attrs={"class": "form-control", "readonly": "readonly"}
                ),
            }
            | {
                "description": forms.Textarea(
                    attrs={"class": "form-control", "rows": 2}
                ),
            }
            | {
                field: forms.NumberInput(attrs={"class": "form-control"})
                for field in [
                    "ambient_capacity",
                    "ac_room_capacity",
                ]
            }
            | {
                "capacity": forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "readonly": "readonly",
                    }
                )
            }
            | {
                "company": forms.Select(attrs={"class": "form-control select2"}),
                "branch": forms.Select(attrs={"class": "form-control select2"}),
            }
        )
