from django import forms
from apps.supplychain.models.distributions import StDistDaily


class StockDailyDistributorForm(forms.ModelForm):
    class Meta:
        model = StDistDaily
        fields = [
            "name",
            "description",
            "remark",
            "status",
            "kd_prod",
            "nm_prod",
            "kd_hrmn",
            "nm_hrmn",
            "kd_prc",
            "kd_cab",
            "id_cab",
            "nm_cab",
            "kd_io",
            "lot",
            "ed",
            "hna",
            "reg",
            "itr",
            "pp",
            "po",
            "ext",
            "dmg",
            "atr",
            "ket",
            "periode",
            "tgl_proses",
            "branch",
            "distributor",
            "distributoritem",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "remark": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "kd_prod": forms.TextInput(attrs={"class": "form-control"}),
            "nm_prod": forms.TextInput(attrs={"class": "form-control"}),
            "kd_hrmn": forms.TextInput(attrs={"class": "form-control"}),
            "nm_hrmn": forms.TextInput(attrs={"class": "form-control"}),
            "kd_prc": forms.TextInput(attrs={"class": "form-control"}),
            "kd_cab": forms.TextInput(attrs={"class": "form-control"}),
            "id_cab": forms.TextInput(attrs={"class": "form-control"}),
            "nm_cab": forms.TextInput(attrs={"class": "form-control"}),
            "kd_io": forms.TextInput(attrs={"class": "form-control"}),
            "lot": forms.TextInput(attrs={"class": "form-control"}),
            "ed": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tgl_proses": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "hna": forms.NumberInput(attrs={"class": "form-control"}),
            "reg": forms.NumberInput(attrs={"class": "form-control"}),
            "itr": forms.NumberInput(attrs={"class": "form-control"}),
            "pp": forms.NumberInput(attrs={"class": "form-control"}),
            "po": forms.NumberInput(attrs={"class": "form-control"}),
            "ext": forms.NumberInput(attrs={"class": "form-control"}),
            "dmg": forms.NumberInput(attrs={"class": "form-control"}),
            "atr": forms.NumberInput(attrs={"class": "form-control"}),
            "ket": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "periode": forms.TextInput(attrs={"class": "form-control"}),
            "branch": forms.Select(attrs={"class": "form-control select2"}),
            "distributor": forms.Select(attrs={"class": "form-control select2"}),
            "distributoritem": forms.Select(attrs={"class": "form-control select2"}),
        }
