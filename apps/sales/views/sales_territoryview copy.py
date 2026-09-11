from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.sales.models import SalesRegion, RegionProvince, SalesArea, AreaRegency
from apps.base.models.locations import Province, Regency, RegencyType
from collections import defaultdict, Counter
from django.http import JsonResponse,  HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from datetime import datetime

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: region_matrix_view                                  ║
# ║  Type: Function base view                                  ║
# ║  Purpose: View to Region Province Matrix                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\sales_territoryview.py             ║
# ║  Created: Jul/5-2025 by Setiadji                           ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def region_matrix_view(request):
    provinces = Province.objects.select_related('island').order_by('code', 'island__name')
    regions = SalesRegion.objects.select_related('organization').order_by('code', 'organization__initial')
    regionprovinces = RegionProvince.objects.select_related('province', 'region').all()    
    active_map = {
        (rp.province.id, rp.region.id): rp
        for rp in regionprovinces
    }

    # Add side attribute based on name suffix
    for region in regions:
        name = region.shortname.strip()
        region.display_shortname = name.replace(' West', '').replace(' East', '').strip()

    # Count how many times each province appears in active_map
    counter = Counter(pid for pid, _ in active_map)
    shared_province_ids = {pid for pid, count in counter.items() if count > 1}

    context = {
        'provinces': provinces,
        'regions': regions,
        'active_map': active_map,
        'shared_province_ids': shared_province_ids,
    }
    return render(request, 'sales/territory/region_matrix.html', context)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: region_matrix_update                                ║
# ║  Type: Function base view                                  ║
# ║  Purpose: Update to Region Province Matrix                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\sales_territoryview.py             ║
# ║  Created: Jul/5-2025 by Setiadji                           ║
# ║  Updates: Jul/8-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def region_matrix_update(request):
    province_id = request.POST.get("province_id")
    region_id = request.POST.get("region_id")
    terminated_str = request.POST.get("terminated")

    if not province_id or not region_id:
        return HttpResponseBadRequest("Missing required data.")
    
    if terminated_str:
        try:
            terminated_date = datetime.strptime(terminated_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid terminated date format.")

    try:
        province = Province.objects.get(id=province_id)
        region = SalesRegion.objects.get(id=region_id)
    except (Province.DoesNotExist, SalesRegion.DoesNotExist):
        return HttpResponseBadRequest("Province or Region not found.")

    # Get the latest mapping (if exists)
    mapping_qs = RegionProvince.objects.filter(province=province, region=region).order_by("-id")
    mapping = mapping_qs.first()
    
    qs = RegionProvince.objects.filter(province=province, region=region, status=1)
    if not qs.exists():
        return HttpResponseBadRequest("No active mapping found.")

    mapping = qs.latest("id")
    mapping.terminated = terminated_date
    mapping.status = 0
    mapping.uat = now()
    mapping.uby = request.user
    mapping.save()

    return JsonResponse({"status": "ok"})

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: area_matrix_view                                    ║
# ║  Type: Function base view                                  ║
# ║  Purpose: View to Area Regency Matrix                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\sales_territoryview.py             ║
# ║  Created: Jul/11-2025 by Setiadji                          ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def area_matrix_view(request):
    regencies = Regency.objects.select_related('province__island').order_by('province__island__name', 'province__name', 'name')
    areas = SalesArea.objects.select_related('region').order_by('code', 'region__initial')
    arearegencies = AreaRegency.objects.select_related('regency', 'area').all()

    active_map = {
        (ar.regency.id, ar.area.id): ar
        for ar in arearegencies
    }

    # Clean display names
    for area in areas:
        name = area.shortname.strip()
        area.display_shortname = name.replace(' West', '').replace(' East', '').strip()

    # Detect regencies mapped to more than one area
    counter = Counter(rid for rid, _ in active_map)
    shared_regency_ids = {rid for rid, count in counter.items() if count > 1}

    # Group regencies by island > province
    grouped_data = defaultdict(lambda: defaultdict(list))
    for regency in regencies:
        island = regency.province.island
        province = regency.province
        grouped_data[island][province].append(regency)

    context = {
        'areas': areas,
        'grouped_data': grouped_data,
        'active_map': active_map,
        'shared_regency_ids': shared_regency_ids,
    }
    return render(request, 'sales/territory/area_matrix.html', context)


