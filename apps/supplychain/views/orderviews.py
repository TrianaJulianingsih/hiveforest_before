from django.shortcuts import render, redirect, get_object_or_404
from apps.supplychain.models import Distributor, OrderHeader, OrderDetail, Branch
from apps.supplychain.forms.orderforms import OrderForm, OrderDetailFormSet
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.base.models import SCMPermission
from apps.base.models.utils import get_filtered_model, get_permitted_branches
from django.forms import ValidationError
from django.forms import modelformset_factory, inlineformset_factory
from apps.supplychain.forms.orderforms import OrderDetailForm, OrderDetailFormSet
from django.db.models import Count, Sum
from django.utils.formats import localize
from django.utils.translation import activate

@login_required
def order_list(request):
    user_locale = request.user.userprofile.language  # Example: Assume user profile has a language field
    activate(user_locale)  # Set language for current request    
    user = request.user
    orders = get_filtered_model(
        user, OrderHeader, SCMPermission,
        'distributor', 'branch',
        distributor_field='distributor',
        branch_field = 'branch',
        distributor_related_model=Distributor,
        branch_related_model=Branch
    ).annotate(
        lines=Count('orderdetail'), # Line count
        sum_amount=Sum('orderdetail__amount')  # Sum of value
    )
    # Convert total_value using localize function
    for order in orders:
        order.sum_amount = localize(order.sum_amount)
    
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_add(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST, user=request.user)
        #detail_formset = OrderDetailFormSet(request.POST, queryset=OrderDetail.objects.none())
        detail_formset = OrderDetailFormSet(request.POST)
        if order_form.is_valid() and detail_formset.is_valid():
        #if order_form.is_valid():
            if not any(form.cleaned_data for form in detail_formset):  # Check if any details were added
                #detail_formset.add_error(None, "At least one order detail is required.")
                detail_formset._non_form_errors = [ValidationError("At least one order detail is required.")]
            else:
                order_header = order_form.save()
                detail_formset.instance = order_header
                order_details = detail_formset.save(commit=False)
                for detail in order_details:
                    detail.order = order_header  # Link order detail to the order
                    qty = detail.qty if detail.qty is not None else 0
                    price = detail.price if detail.price is not None else 0                    
                    detail.amount = qty * price  # Ensure calculation
                    detail.save()
                return redirect('supplychain:order_list')
        else:
            # Debugging 
            print("Order Form Errors:", order_form.errors) # To check form errors in the console
            print("Formset Errors:", detail_formset.errors) # To check formset errors in the console
            print("Formset Non-Form Errors:", detail_formset.non_form_errors())

    else:
        order_form = OrderForm(user=request.user)
        detail_formset = OrderDetailFormSet()

    # Default selected branch (if any)
    selected_branch = request.GET.get('branch_id')  # Fetch from URL params or user settings
    branches = get_permitted_branches(request.user)
    
    tabs = [
        ('Order Info', [order_form['orderno'], order_form['orderdate'], order_form['orderdue'], order_form['description'], order_form['remark'], order_form['progress']]),
        ('Distributor Info', [order_form['distributor'], order_form['branch']]),
        ('Products', [order_form['ordertype'], order_form['status']]),
    ]
    context = {
        'order_form': order_form,
        'selected_branch': selected_branch,
        'branches': branches,
        #'tabs': tabs,
        'detail_formset': detail_formset,
    }
    return render(request, 'orders/order_add.html', context)

@login_required
def order_edit(request, pk):
    # Fetch the order object by primary key
    order = get_object_or_404(OrderHeader, pk=pk)
    # Create the form and formset instances
    order_form = OrderForm(request.POST or None, instance=order, user=request.user)
    # Ensure no extra empty forms
    OrderDetailFormSet = modelformset_factory(OrderDetail, form=OrderDetailForm, extra=0, can_delete=True)
    detail_formset = OrderDetailFormSet(request.POST or None, queryset=OrderDetail.objects.filter(order=order))

    if request.method == 'POST':
        if order_form.is_valid() and detail_formset.is_valid():
            if not any(form.cleaned_data for form in detail_formset):  # Check if any details were added
                detail_formset._non_form_errors = [ValidationError("At least one order detail is required.")]
            else:
                order_header = order_form.save(commit=False)
                order_header.save()
                detail_formset.instance = order_header
                detail_formset.save()
                return redirect('supplychain:order_list')

        # Debugging
        print("Order Form Errors:", order_form.errors)
        print("Formset Errors:", detail_formset.errors)
        print("Formset Non-Form Errors:", detail_formset.non_form_errors())

    # Default selected branch (if any)
    selected_branch = order.branch.id if order.branch else None
    branches = get_permitted_branches(request.user)
    tabs = [
        ('Order Info', [order_form['orderno'], order_form['orderdate'], order_form['orderdue'], order_form['description'], order_form['remark'], order_form['progress']]),
        ('Distributor Info', [order_form['distributor'], order_form['branch']]),
        ('Products', [order_form['ordertype'], order_form['status']]),
    ]

    # Debugging: Print formset data
    for form in detail_formset:
        print("Form Data:", form.initial)  # Check if 'id' is present in the initial data
        
    context = {
        'order_form': order_form,
        'selected_branch': selected_branch,
        'branches': branches,
        'detail_formset': detail_formset,
        'order': order,
    }
    
    return render(request, 'orders/order_edit.html', context)

@login_required
def order_view(request, pk):
    # Fetch the order object by primary key
    order = get_object_or_404(OrderHeader, pk=pk)
    order_details = order.orderdetail_set.all()

    # Render the template with the forms
    context = {
        'order': order,
        'order_details': order_details,
    }
    return render(request, 'orders/order_view.html', context)

@login_required
def order_details(request, order_id):
    # Fetch the order header
    order = get_object_or_404(OrderHeader, id=order_id)
    
    # Fetch associated order details (assuming a ForeignKey relationship)
    details = OrderDetail.objects.filter(order=order).values(
        "orderline",
        "itemgroup",
        "item__name",
        "qty",
        'uom',
        'price',
        'amount',
        'progress'
    )
    
    data = {
        "id": order.id,
        "name": order.name,
        "status": order.status,
        "details": list(details),  # Include associated details
    }
    
    return JsonResponse(data)