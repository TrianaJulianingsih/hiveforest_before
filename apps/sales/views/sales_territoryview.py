from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.sales.models import SalesRegion, RegionProvince, SalesArea, AreaRegency
from apps.base.models.locations import Island, Province, Regency, RegencyType
from apps.humancapital.models import Business, Organization
from collections import Counter
from django.db.models import Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from datetime import datetime
from collections import defaultdict


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
    provinces = Province.objects.select_related("island").order_by(
        "code", "island__name"
    )
    regions = SalesRegion.objects.select_related(
        "business", "position__organization"
    ).order_by("code")

    regionprovinces = RegionProvince.objects.select_related(
        "province", "region"
    ).order_by("province_id", "region_id", "-id")

    active_map = {}
    for rp in regionprovinces:
        key = (rp.province_id, rp.region_id)
        if key not in active_map:
            active_map[key] = rp

    for region in regions:
        name = region.shortname.strip()
        region.display_shortname = (
            name.replace(" West", "").replace(" East", "").strip()
        )
        region.group_organization = (
            region.position.organization if region.position else None
        )

    shared_province_ids = (
        RegionProvince.objects.filter(status=1)
        .values("province")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("province", flat=True)
    )

    context = {
        "provinces": provinces,
        "regions": regions,
        "active_map": active_map,
        "shared_province_ids": shared_province_ids,
    }
    return render(request, "sales/territory/region_matrix.html", context)


# FaisalS | HF-40 - HF-Sales | Territory Management Module
def parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        return None


# FaisalS | HF-23 - Region Matrix UI
@login_required
@require_POST
def region_matrix_update(request):
    province_id = request.POST.get("province_id")
    region_id = request.POST.get("region_id")
    effective_date = parse_date(request.POST.get("effective"))
    terminated_date = parse_date(request.POST.get("terminated"))
    action = request.POST.get("action")

    if not province_id or not region_id:
        return HttpResponseBadRequest("Missing required data.")

    if request.POST.get("effective") and not effective_date:
        return HttpResponseBadRequest("Invalid effective date format.")
    if request.POST.get("terminated") and not terminated_date:
        return HttpResponseBadRequest("Invalid terminated date format.")

    try:
        province = Province.objects.get(id=province_id)
        region = SalesRegion.objects.get(id=region_id)
    except (Province.DoesNotExist, SalesRegion.DoesNotExist):
        return HttpResponseBadRequest("Province or Region not found.")

    mapping = (
        RegionProvince.objects.filter(province=province, region=region)
        .order_by("-id")
        .first()
    )

    if not mapping:
        if not effective_date:
            return HttpResponseBadRequest(
                "Mapping not found and no effective date provided."
            )

        RegionProvince.objects.create(
            slug=region.slug + "-" + province.shortname.lower(),
            province_id=province_id,
            region_id=region_id,
            effective=effective_date,
            status=1,
            cat=now(),
            cby_id=request.user,
        )
        return JsonResponse({"status": "created"})

    if action == "delete":
        mapping.status = 0
        mapping.dat = now()
        mapping.dby = request.user
    else:
        mapping.status = 0 if terminated_date else 1
        mapping.terminated = terminated_date

    mapping.uat = now()
    mapping.uby = request.user
    mapping.save()

    return JsonResponse({"status": "ok"})


# FaisalS | HF-30 - Area Matrix UI
@login_required
def area_matrix_view(request):
    islands = Island.objects.order_by("code")
    provinces = Province.objects.order_by("code")
    regencies = Regency.objects.order_by("code")
    businesses = (
        Business.objects.filter(region_business__isnull=False)
        .distinct()
        .order_by("name")
    )
    organization_ids = (
        SalesRegion.objects.exclude(position__organization_id__isnull=True)
        .values_list("position__organization_id", flat=True)
        .distinct()
    )
    organizations = (
        Organization.objects.filter(id__in=organization_ids)
        .distinct()
        .order_by("name")
    )
    regions = SalesRegion.objects.order_by("code")
    areas = SalesArea.objects.order_by("code")
    active_map = {
        (mapping.regency_id, mapping.area_id): mapping
        for mapping in AreaRegency.objects.select_related("regency", "area").all()
    }

    selected_island_ids = []
    selected_province_ids = []
    selected_business_ids = []
    selected_organization_ids = []
    selected_region_ids = []

    if request.method == "POST":
        try:
            selected_island_ids = list(
                map(
                    int,
                    request.POST.getlist("island[]") or request.POST.getlist("island"),
                )
            )
            selected_province_ids = list(
                map(
                    int,
                    request.POST.getlist("province[]")
                    or request.POST.getlist("province"),
                )
            )
            selected_business_ids = list(
                map(
                    int,
                    request.POST.getlist("business[]")
                    or request.POST.getlist("business"),
                )
            )
            selected_organization_ids = list(
                map(
                    int,
                    request.POST.getlist("organization[]")
                    or request.POST.getlist("organization"),
                )
            )
            selected_region_ids = list(
                map(
                    int,
                    request.POST.getlist("region[]") or request.POST.getlist("region"),
                )
            )
        except ValueError:
            pass

    selected_islands = Island.objects.filter(id__in=selected_island_ids).order_by(
        "code"
    )
    selected_provinces = Province.objects.filter(id__in=selected_province_ids).order_by(
        "code"
    )
    selected_businesses = Business.objects.filter(
        id__in=selected_business_ids
    ).order_by("code")
    selected_organizations = Organization.objects.filter(
        id__in=selected_organization_ids
    ).order_by("code")
    selected_regions = SalesRegion.objects.filter(id__in=selected_region_ids).order_by(
        "code"
    )

    organizations_by_business = {}
    for biz in selected_businesses:
        filtered_orgs = selected_organizations.filter(
            id__in=SalesRegion.objects.filter(
                business=biz,
                position__organization_id__isnull=False,
            ).values_list("position__organization_id", flat=True)
        ).distinct()
        organizations_by_business[str(biz.id)] = list(
            {
                org.id: {"id": org.id, "shortname": org.shortname}
                for org in filtered_orgs
            }.values()
        )

    regions_by_organization = {}
    for org in selected_organizations:
        filtered_regions = selected_regions.filter(
            position__organization=org
        ).distinct()
        regions_by_organization[str(org.id)] = list(
            {
                reg.id: {"id": reg.id, "shortname": reg.shortname}
                for reg in filtered_regions
            }.values()
        )

    areas_by_region = {}
    area_counts_by_region = {}
    for reg in selected_regions:
        areas = SalesArea.objects.filter(region=reg).values(
            "id", "initial", "shortname", "name"
        )
        areas_list = list(areas)
        areas_by_region[str(reg.id)] = areas_list
        area_counts_by_region[str(reg.id)] = len(areas_list) or 1

    area_counts_by_org = {}
    for org in selected_organizations:
        total = 0
        regions = regions_by_organization.get(str(org.id), [])
        for region in regions:
            region_id = region["id"]
            count = area_counts_by_region.get(str(region_id), 1)
            total += count
        area_counts_by_org[str(org.id)] = total or 1

    colspan_by_business = {}
    for biz in selected_businesses:
        total = 0
        orgs = organizations_by_business.get(str(biz.id), [])
        for org in orgs:
            org_id = org["id"]
            count = area_counts_by_org.get(str(org_id), 1)
            total += count
        colspan_by_business[str(biz.id)] = total or 1

    if not selected_island_ids:
        mode = "no_island"
    elif selected_island_ids and not selected_province_ids:
        mode = "island_only"
    elif selected_island_ids and selected_province_ids:
        mode = "island_and_province"
    else:
        mode = "unknown"

    context = {
        "islands": islands,
        "provinces": provinces,
        "regencies": regencies,
        "businesses": businesses,
        "organizations": organizations,
        "regions": regions,
        "selected_island_ids": [str(i) for i in selected_island_ids],
        "selected_province_ids": [str(i) for i in selected_province_ids],
        "selected_business_ids": [str(i) for i in selected_business_ids],
        "selected_organization_ids": [str(i) for i in selected_organization_ids],
        "selected_region_ids": [str(i) for i in selected_region_ids],
        "selected_islands": selected_islands,
        "selected_provinces": selected_provinces,
        "selected_businesses": selected_businesses,
        "selected_organizations": selected_organizations,
        "selected_regions": selected_regions,
        "organizations_by_business": organizations_by_business,
        "regions_by_organization": regions_by_organization,
        "areas_by_region": areas_by_region,
        "area_counts_by_region": area_counts_by_region,
        "area_counts_by_org": area_counts_by_org,
        "colspan_by_business": colspan_by_business,
        "active_map": active_map,
        "mode": mode,
    }

    return render(request, "sales/territory/area_matrix.html", context)


def ajax_filter_provinces(request):
    island_ids = request.GET.getlist("island_ids[]")
    provinces = Province.objects.filter(island_id__in=island_ids).values("id", "name")
    return JsonResponse(list(provinces), safe=False)


def ajax_filter_organizations(request):
    business_ids = request.GET.getlist("business_ids[]")
    organization_ids = (
        SalesRegion.objects.filter(
            business_id__in=business_ids,
            position__organization_id__isnull=False,
        )
        .values_list("position__organization_id", flat=True)
        .distinct()
    )
    organizations = (
        Organization.objects.filter(id__in=organization_ids)
        .distinct()
        .order_by("shortname")
    )

    org_list = [{"id": org.id, "shortname": org.shortname} for org in organizations]
    return JsonResponse(org_list, safe=False)


def ajax_filter_regions(request):
    org_ids = request.GET.getlist("organization_ids[]")
    regions = (
        SalesRegion.objects.filter(position__organization_id__in=org_ids)
        .select_related("position", "position__organization")
        .order_by("code")
        .distinct()
    )

    region_list = [{"id": reg.id, "shortname": reg.shortname} for reg in regions]
    return JsonResponse(region_list, safe=False)


# FaisalS | HF-30 - Area Matrix UI
@login_required
@require_POST
def area_matrix_update(request):
    regency_id = request.POST.get("regency_id")
    area_id = request.POST.get("area_id")
    effective_date = parse_date(request.POST.get("effective"))
    terminated_date = parse_date(request.POST.get("terminated"))
    action = request.POST.get("action")
    bulk_mode = request.POST.get("bulk_mode")
    bulk_operation = request.POST.get("bulk_operation")

    if not regency_id or not area_id:
        return HttpResponseBadRequest("Missing required data.")

    if request.POST.get("effective") and not effective_date:
        return HttpResponseBadRequest("Invalid effective date format.")
    if request.POST.get("terminated") and not terminated_date:
        return HttpResponseBadRequest("Invalid terminated date format.")

    try:
        regency = Regency.objects.get(id=regency_id)
        area = SalesArea.objects.get(id=area_id)
    except (Regency.DoesNotExist, SalesArea.DoesNotExist):
        return HttpResponseBadRequest("Regency or Area not found.")

    mapping = (
        AreaRegency.objects.filter(regency=regency, area=area).order_by("-id").first()
    )

    if bulk_mode == "true":
        if bulk_operation == "activate":
            if not mapping or mapping.status == 0:
                if not effective_date:
                    effective_date = now().date()

                if not mapping:
                    AreaRegency.objects.create(
                        initial=f"{area.initial}-{regency.code}",
                        shortname=f"{area.initial}-{regency.type.code}. {regency.name}",
                        regency_id=regency_id,
                        area_id=area_id,
                        effective=effective_date,
                        status=1,
                        terminated=None,
                        cat=now(),
                        cby_id=request.user,
                    )
                    return JsonResponse(
                        {"status": "created", "operation": bulk_operation}
                    )
                else:
                    mapping.status = 1
                    mapping.effective = effective_date
                    mapping.terminated = None
                    mapping.uat = now()
                    mapping.uby = request.user
                    mapping.save()
                    return JsonResponse(
                        {"status": "updated", "operation": bulk_operation}
                    )
            else:
                return JsonResponse(
                    {"status": "no_change", "operation": bulk_operation}
                )

        elif bulk_operation == "deactivate":
            if mapping and mapping.status == 1:
                if not terminated_date:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Termination date required for deactivation",
                        }
                    )

                mapping.status = 0
                mapping.terminated = terminated_date
                mapping.uat = now()
                mapping.uby = request.user
                mapping.save()
                return JsonResponse({"status": "updated", "operation": bulk_operation})
            else:
                return JsonResponse(
                    {"status": "no_change", "operation": bulk_operation}
                )
        else:
            return JsonResponse({"status": "invalid_operation"})

    if not mapping:
        if not effective_date:
            return HttpResponseBadRequest(
                "Mapping not found and no effective date provided."
            )

        AreaRegency.objects.create(
            initial=f"{area.initial}-{regency.code}",
            shortname=f"{area.initial}-{regency.type.code}. {regency.name}",
            regency_id=regency_id,
            area_id=area_id,
            effective=effective_date,
            status=1,
            cat=now(),
            cby_id=request.user,
        )
        return JsonResponse({"status": "created"})

    if action == "delete":
        mapping.status = 0
        mapping.dat = now()
        mapping.dby = request.user
    else:
        mapping.status = 0 if terminated_date else 1
        mapping.terminated = terminated_date

    mapping.uat = now()
    mapping.uby = request.user
    mapping.save()

    return JsonResponse({"status": "ok"})
