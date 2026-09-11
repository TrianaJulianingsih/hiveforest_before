from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.sales.models.customer import Outlet
from apps.supplychain.models.distributions import Distributor
from django.db.models import Q

@login_required
def outlet_list_view(request):
    distributors = Distributor.objects.all()
    outlets = Outlet.objects.select_related('branch', 'customer', 'distributor', 'custtype', 'outletgroup').all()[:100]
    return render(request, 'sales/outlet_list.html', {'outlet_list': outlets, 'distributors': distributors})

@login_required
def distributor_data(request):
    distributors = Distributor.objects.all()
    data = [{"id": distributor.id, "text": distributor.initial} for distributor in distributors]
    return JsonResponse(data, safe=False)

def build_or_filter(field_lookup, values):
    q_objects = Q()
    for val in values.split("|"):
        val = val.strip()
        if val:
            q_objects |= Q(**{field_lookup: val})
    return q_objects

@login_required
def outlet_ajax(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    # Start with full queryset, optimized with select_related
    queryset = Outlet.objects.select_related(
        'distributor', 'branch', 'custtype', 'customer', 'outletgroup'
    )

    # Global search
    search_value = request.GET.get('search[value]', '').strip()
    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) |
            Q(code__icontains=search_value) |
            Q(distributor__initial__icontains=search_value) |
            Q(branch__name__icontains=search_value) |
            Q(custtype__code__icontains=search_value) |
            Q(customer__name__icontains=search_value) |
            Q(outletgroup__name__icontains=search_value) |
            Q(address__icontains=search_value)
        )

    # Column filter: Outlet, Distributor
    name_colfilter = request.GET.get("columns[3][search][value]")
    if name_colfilter:
        queryset = queryset.filter(build_or_filter("name__icontains", name_colfilter))

    distributor_colfilter = request.GET.get("columns[4][search][value]")
    if distributor_colfilter:
        queryset = queryset.filter(build_or_filter("distributor__initial__icontains", distributor_colfilter))

    branch_colfilter = request.GET.get("columns[5][search][value]")
    if branch_colfilter:
        queryset = queryset.filter(build_or_filter("branch__name__icontains", branch_colfilter))

    custtype_colfilter = request.GET.get("columns[6][search][value]")
    if custtype_colfilter:
        queryset = queryset.filter(build_or_filter("custtype__code__icontains", custtype_colfilter))

    customer_colfilter = request.GET.get("columns[7][search][value]")
    if customer_colfilter:
        queryset = queryset.filter(build_or_filter("customer__name__icontains", customer_colfilter))

    outletgroup_colfilter = request.GET.get("columns[8][search][value]")
    if outletgroup_colfilter:
        queryset = queryset.filter(build_or_filter("outletgroup__name__icontains", outletgroup_colfilter))

    address_colfilter = request.GET.get("columns[11][search][value]")
    if address_colfilter:
        queryset = queryset.filter(build_or_filter("address__icontains", address_colfilter))

    # 🧭 Ordering
    order_col_index = request.GET.get('order[0][column]', '3')  # default to 'name' column
    order_dir = request.GET.get('order[0][dir]', 'asc')
    column_map = {
        '1': 'id',
        '2': 'code',
        '3': 'name',
        '4': 'distributor__initial',
        '5': 'branch__name',
        '6': 'custtype__code',
        '7': 'customer__name',
        '8': 'outletgroup__name',
        '9': 'code1',
        '10': 'code2',
        '11': 'address',
    }
    order_field = column_map.get(order_col_index, 'name')
    if order_dir == 'desc':
        order_field = '-' + order_field
    queryset = queryset.order_by(order_field)
    
    # 📊 Total after filter
    total_filtered = queryset.count()

    # 📦 Paginate after filtering
    queryset = queryset[start:start + length]

    # ✅ Prepare data
    data = []
    for outlet in queryset:
        data.append({
            'id': outlet.id,
            'code': outlet.code,
            'name': outlet.name,
            'distributor': outlet.distributor.initial if outlet.distributor else '',
            'branch': outlet.branch.name if outlet.branch else '',
            'type': outlet.custtype.code if outlet.custtype else '',
            'customer': outlet.customer.name if outlet.customer else '',
            'group': outlet.outletgroup.name if outlet.outletgroup else '',
            'code1': outlet.code1,
            'code2': outlet.code2,
            'address': outlet.address,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': Outlet.objects.count(),
        'recordsFiltered': total_filtered,
        'data': data  # Return as a list of objects, not a list of lists
    })