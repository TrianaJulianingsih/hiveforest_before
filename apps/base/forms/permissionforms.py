from django import forms
from apps.base.models import Role, CMSPermission, SCMPermission
from apps.cms.models import ApplicationList, ModuleList, MenuItem
from apps.supplychain.models.distributions import Distributor, DistributorItemGroup, Branch
from apps.supplychain.models.manufacturing import ManufacturingItemGroup
from django.contrib.admin.widgets import FilteredSelectMultiple

class SCMPermissionForm(forms.ModelForm):
    distributor = forms.ModelMultipleChoiceField(
        queryset=Distributor.objects.all(),
        widget=FilteredSelectMultiple("Distributors", is_stacked=False),
        required=False,
        label="Distributors"
    )

    branch = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        widget=FilteredSelectMultiple("Branches", is_stacked=False),
        required=False,
        label="Branches"
    )

    distitemgroup = forms.ModelMultipleChoiceField(
        queryset=DistributorItemGroup.objects.all(),
        widget=FilteredSelectMultiple("Distributor Item Groups", is_stacked=False),
        required=False,
        label="Distributor Item Groups"
    )

    mfgitemgroup = forms.ModelMultipleChoiceField(
        queryset=ManufacturingItemGroup.objects.all(),
        widget=FilteredSelectMultiple("Manufacturing Item Groups", is_stacked=False),
        required=False,
        label="Manufacturing Item Groups"
    )

    class Meta:
        model = SCMPermission
        fields = ['role',
            'distributor_state', 'distributor',
            'branch_state', 'branch',
            'distitemgroup_state', 'distitemgroup',
            'mfgitemgroup_state', 'mfgitemgroup',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate dropdowns with active choices
        self.fields['distributor'].queryset = Distributor.objects.filter(status=1)
        self.fields['branch'].queryset = Branch.objects.filter(status=1)
        self.fields['distitemgroup'].queryset = DistributorItemGroup.objects.filter(status=1)
        self.fields['mfgitemgroup'].queryset = ManufacturingItemGroup.objects.filter(status=1)

        if self.instance.pk:
            # Prepopulate initial values for many-to-many relationships
            self.fields['distributor'].initial = self.instance.distributor.all()
            self.fields['branch'].initial = self.instance.branch.all()
            self.fields['distitemgroup'].initial = self.instance.distitemgroup.all()
            self.fields['mfgitemgroup'].initial = self.instance.mfgitemgroup.all()

    def save(self, commit=True):
        # Save the applications
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many relationships

            # Handle many-to-many field assignments
            instance.distributor.set(self.cleaned_data['distributor'])
            instance.branch.set(self.cleaned_data['branch'])
            instance.distitemgroup.set(self.cleaned_data['distitemgroup'])
            instance.mfgitemgroup.set(self.cleaned_data['mfgitemgroup'])
        return instance
    
class CMSPermissionForm(forms.ModelForm):
    application = forms.ModelMultipleChoiceField(
        queryset=ApplicationList.objects.all(),
        widget=FilteredSelectMultiple("Applications", is_stacked=False),
        required=False,
        label="Applications"
    )

    module = forms.ModelMultipleChoiceField(
        queryset=ModuleList.objects.all(),
        widget=FilteredSelectMultiple("Module", is_stacked=False),
        required=False,
        label="Modules"
    )

    menu = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.all(),
        widget=FilteredSelectMultiple("Menu", is_stacked=False),
        required=False,
        label="Menu"
    )

    class Meta:
        model = CMSPermission
        fields = ['role',
            'apps_state', 'application',
            'mods_state', 'module',
            'menu_state', 'menu',]  # Use the exact field name from the model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate dropdowns with active choices
        self.fields['application'].queryset = ApplicationList.objects.filter(status=1)
        self.fields['module'].queryset = ModuleList.objects.filter(status=1)
        self.fields['menu'].queryset = MenuItem.objects.filter(status=1)

        if self.instance.pk:
            # Prepopulate initial values for many-to-many relationships
            self.fields['application'].initial = self.instance.application.all()
            self.fields['module'].initial = self.instance.module.all()
            self.fields['menu'].initial = self.instance.menu.all()

    def save(self, commit=True):
        # Save the applications
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many relationships

            # Handle many-to-many field assignments
            instance.application.set(self.cleaned_data['application'])
            instance.module.set(self.cleaned_data['module'])
            instance.menu.set(self.cleaned_data['menu'])            
        return instance