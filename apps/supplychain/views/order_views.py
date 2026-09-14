from django.shortcuts import render, redirect, get_object_or_404
from apps.supplychain.models.distributions_models import Distributor, Branch
from apps.supplychain.models.distrib_orders_models import OrderHeader, OrderDetail
from apps.supplychain.forms.order_forms import OrderForm, OrderDetailForm, OrderDetailFormSet
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.base.models import SCMPermission
from apps.base.models.utils import get_filtered_model, get_permitted_branches
from django.forms import ValidationError, modelformset_factory
from django.db.models import Count, Sum
from django.utils.formats import localize
from django.utils.translation import activate
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@login_required
def order_list(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Order List",
        description="User accessed Order List view.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    user_locale = getattr(getattr(request.user, 'userprofile', None), 'language', 'en')
    activate(user_locale)
    user = request.user
    orders = get_filtered_model(
        user, OrderHeader, SCMPermission,
        'distributor', 'branch',
        distributor_field='distributor',
        branch_field='branch',
        distributor_related_model=Distributor,
        branch_related_model=Branch
    ).annotate(
        lines=Count('orderdetail'),
        sum_amount=Sum('orderdetail__amount')
    )
    for order in orders:
        order.sum_amount = localize(order.sum_amount)
    
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_add(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST, user=request.user)
        detail_formset = OrderDetailFormSet(request.POST)
        if order_form.is_valid() and detail_formset.is_valid():
            if not any(form.cleaned_data for form in detail_formset):
                detail_formset._non_form_errors = [ValidationError("At least one order detail is required.")]
            else:
                order_header = order_form.save()
                detail_formset.instance = order_header
                order_details = detail_formset.save(commit=False)
                for detail in order_details:
                    detail.order = order_header
                    qty = detail.qty if detail.qty is not None else 0
                    price = detail.price if detail.price is not None else 0                    
                    detail.amount = qty * price
                    detail.save()
                SystemLogService.log(
                    request=request,
                    action=LogAction.CREATE,
                    module="SupplyChain",
                    feature="Order Add",
                    description=f"User created Order: {order_header.name} ({order_header.orderno}).",
                    obj=order_header,
                    status="SUCCESS",
                    log_type="SYSTEM",
                )
                return redirect('supplychain:order_list')

    else:
        order_form = OrderForm(user=request.user)
        detail_formset = OrderDetailFormSet()

    selected_branch = request.GET.get('branch_id')
    branches = get_permitted_branches(request.user)
    
    context = {
        'order_form': order_form,
        'selected_branch': selected_branch,
        'branches': branches,
        'detail_formset': detail_formset,
    }
    return render(request, 'orders/order_add.html', context)


@login_required
def order_edit(request, pk):
    order = get_object_or_404(OrderHeader, pk=pk)
    order_form = OrderForm(request.POST or None, instance=order, user=request.user)
    CustomOrderDetailFormSet = modelformset_factory(OrderDetail, form=OrderDetailForm, extra=0, can_delete=True)
    detail_formset = CustomOrderDetailFormSet(request.POST or None, queryset=OrderDetail.objects.filter(order=order))

    if request.method == 'POST':
        if order_form.is_valid() and detail_formset.is_valid():
            if not any(form.cleaned_data for form in detail_formset):
                detail_formset._non_form_errors = [ValidationError("At least one order detail is required.")]
            else:
                order_header = order_form.save(commit=False)
                order_header.save()
                detail_formset.instance = order_header
                detail_formset.save()
                SystemLogService.log(
                    request=request,
                    action=LogAction.UPDATE,
                    module="SupplyChain",
                    feature="Order Edit",
                    description=f"User updated Order: {order_header.name} ({order_header.orderno}).",
                    obj=order_header,
                    status="SUCCESS",
                    log_type="SYSTEM",
                )
                return redirect('supplychain:order_list')

    selected_branch = order.branch.id if order.branch else None
    branches = get_permitted_branches(request.user)

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
    order = get_object_or_404(OrderHeader, pk=pk)
    order_details = order.orderdetail_set.all()

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Order View Detail",
        description=f"User viewed detail of Order: {order.name}.",
        obj=order,
        status="SUCCESS",
        log_type="SYSTEM",
    )

    context = {
        'order': order,
        'order_details': order_details,
    }
    return render(request, 'orders/order_view.html', context)


@login_required
def order_details(request, order_id):
    order = get_object_or_404(OrderHeader, id=order_id)
    
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
        "details": list(details),
    }

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Order Details API",
        description=f"User fetched JSON details for Order ID: {order_id}.",
        obj=order,
        status="SUCCESS",
        log_type="SYSTEM",
    )
    
    return JsonResponse(data)
