from django import forms
from django.forms import modelformset_factory
from apps.supplychain.models.distrib_orders import OrderHeader, OrderDetail
from django.forms import inlineformset_factory
from apps.supplychain.models import Distributor, Branch, OrderType, OrderStatus
from apps.base.models import get_permitted_distributors, get_permitted_branches
from datetime import date

class OrderForm(forms.ModelForm):

    tabs = [
            ('Order Info', ['orderno', 'orderdate', 'orderdue', 'description', 'remark', 'progress']),
            ('Distributor Info', ['distributor', 'branch']),
            ('Products', ['ordertype', 'status']),
        ]
    
    class Meta:
        model = OrderHeader
        fields = ['orderno', 'orderdate', 'orderdue', 'distributor', 'branch', 'ordertype', 'status', 'description', 'remark', 'progress']
        widgets = {
            'distributor': forms.Select(attrs={'id': 'distributorDropdown', 'class': 'form-control', 'style': 'width: 300px;'}),
            'branch': forms.Select(attrs={'id': 'branchDropdown', 'class': 'form-control', 'style': 'width: 200px;'}),
            'ordertype': forms.Select(attrs={'id': 'ordertypeDropdown', 'class': 'form-control', 'style': 'width: 150px;'}),
            'orderno': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '20'}),
            'orderdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'style': 'width: 150px;'}),
            'orderdue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'style': 'width: 150px;'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'remark': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'progress': forms.Select(attrs={'id': 'progressDropdown', 'class': 'form-control', 'style': 'width: 150px;'}),
            'status': forms.Select(attrs={'class': 'form-control', 'style': 'width: 125px;'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # DISTRIBUTORS
        # Set distributor queryset
        if user:
            self.fields['distributor'].queryset = get_permitted_distributors(user)
        else:
            self.fields['distributor'].queryset = Distributor.objects.none()

        # Set the initial distributor value if provided or use the first one
        if 'distributor' in self.initial:
            selected_distributor = self.initial['distributor']
        else:
            selected_distributor = self.fields['distributor'].queryset.first()
        self.fields['distributor'].initial = selected_distributor

        # BRANCHES
        # Filter branches based on selected distributor (if any)
        if selected_distributor:
            self.fields['branch'].queryset = Branch.objects.filter(
                distributor=selected_distributor,
                status=1,
                id__in=get_permitted_branches(user)
            )
        else:
            self.fields['branch'].queryset = Branch.objects.none()

        # Set a default branch if any are available
        if 'branch' in self.initial:
            self.fields['branch'].initial = self.initial['branch']
        elif self.fields['branch'].queryset.exists():
            self.fields['branch'].initial = self.fields['branch'].queryset.first()

        # ORDER TYPES
        # Filter order type  based on selected distributor (if any)
        if selected_distributor:
            self.fields['ordertype'].queryset = OrderType.objects.filter(
                distributor=selected_distributor,
                status=1,
            )
        else:
            self.fields['ordertype'].queryset = OrderType.objects.none()

        # Set a default order type if any are available
        if 'ordertype' in self.initial:
            self.fields['ordertype'].initial = self.initial['ordertype']
        elif self.fields['ordertype'].queryset.exists():
            self.fields['ordertype'].initial = self.fields['ordertype'].queryset.first()

        # Set the default value for 'progress' as 'Draft'
        if not self.instance.pk:  # Check if this is a new order
            self.fields['progress'].queryset = OrderStatus.objects.filter(id=1)
            self.fields['progress'].initial = OrderStatus.objects.get(id=1)

        # Remove the blank option for the dropdown control and set initial date to today
        self.fields['distributor'].empty_label = None
        self.fields['branch'].empty_label = None
        self.fields['ordertype'].empty_label = None
        self.fields['orderdate'].initial = date.today()
        self.fields['orderdue'].initial = date.today()

    def clean_progress(self):
        if not self.instance.pk:  # For new orders
            return OrderStatus.objects.get(id=1)  # Enforce "Draft"
        return self.cleaned_data['progress']

class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail
        fields = ['id', 'orderline', 'itemgroup', 'item', 'qty', 'uom', 'price', 'amount', 'progress', 'status']
        widgets = {
            'orderline': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'itemgroup': forms.Select(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-control select2'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Enter quantity'}),
            'uom': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter price'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),  # Usually calculated
            'progress': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get('qty', 0) or 0
        price = cleaned_data.get('price', 0) or 0
        cleaned_data['amount'] = qty * price  # Safe calculation
        return cleaned_data
    
# Formset for multiple order details
OrderDetailFormSet = inlineformset_factory( 
    OrderHeader,
    OrderDetail,
    fields= ['id', 'orderline', 'itemgroup', 'item', 'qty', 'uom', 'price', 'amount', 'progress', 'status'],  # Or specify fields explicitly
    form=OrderDetailForm,
    extra=1,           # Number of empty forms
    can_delete=True    # Allow deletion
)