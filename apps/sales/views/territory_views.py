from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from apps.sales.models.territory_models import SalesRegion, RegionProvince, SalesArea, AreaRegency, TerritoryAssignment, TerritoryAssignmentHistory
from apps.sales.models.customer_models import Customer, CustomerType
from apps.base.models.locations import Island, Province, Regency, RegencyType
from apps.humancapital.models.business_models import Business
from apps.humancapital.models.structure_models import Organization, Assignment, Position
from apps.humancapital.utils import (
    get_user_site_id,
    get_user_assignment,
)
from collections import Counter
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, QueryDict
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from django.urls import reverse
from datetime import datetime
from collections import defaultdict

import re
from uuid import uuid4
from django.db import transaction

from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: region_matrix_view                                  ║
# ║  Type: Function base view                                  ║
# ║  Purpose: View to Region Province Matrix                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\territory_views.py                 ║
# ║  Created: Jul/5-2025 by Setiadji                           ║
# ║  Updates: Jun/15-2026 by Copilot - Site-based filtering    ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def region_matrix_view(request):
    # Get all provinces and regions
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="Region Province Matrix",
        description="User accessed Region Province Matrix view.",
        status="SUCCESS",
        log_type="SYSTEM",
    )

    user_site_id = get_user_site_id(request.user)
    is_admin = request.user.is_superuser or request.user.is_staff
    can_edit_effective_date = can_edit_region_dates(request.user)

    # Allow Admin, HO (site_id==1) and RM to access region matrix
    if not can_manage_region_matrix(request.user):
        return HttpResponseForbidden("Permission denied.")

    provinces = Province.objects.select_related("island").order_by(
        "code", "island__name"
    )
    regions = SalesRegion.objects.select_related(
        "business", "position__organization"
    ).order_by("code")

    regionprovinces = RegionProvince.objects.select_related(
        "province", "region"
    ).order_by("province_id", "region_id", "-id")

    # If user has site_id!=1, apply site-based filtering
    # site_id=1 means full access, site_id=None means no access, site_id=other means filtered
    if user_site_id and user_site_id != 1:
        # Non-full-access user: filter by their site scope
        user_scope = get_user_region_scope(request.user)
        if user_scope is not None:
            provinces = user_scope["provinces"]
            regions = user_scope["regions"]
            regionprovinces = regionprovinces.filter(
                region__in=regions,
                province__in=provinces
            )
    # If user_site_id is None, they have no access, but we won't restrict at view level
    # The query will just return empty results

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
        "is_admin": is_admin,
        "can_edit_effective_date": can_edit_effective_date,
        "user_site_id": user_site_id,
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


def get_user_region_scope(user):
    """
    Get filtered scope (islands, provinces, organizations, regions) for a user.

    Access Control Logic:
    1. is_staff or is_superuser -> Full access (return None)
    2. site_id = 1 (HO) -> Full access (return None)
    3. Otherwise, scope to the region(s) whose SalesRegion.position matches the
       user's active assignment position (exact FK match). Everything else
       (provinces, areas, regencies, business, org) is derived from those
       regions.
    4. No assignment/position, or position not tied to any region -> No access
       (empty scope). Fail-closed: never widen access on a partial match.

    Returns:
    - None: Full access (admin or site_id=1)
    - Filtered scope dict: limited to the user's region(s)
    - Empty scope dict: no access
    """
    def empty_scope():
        return {
            "islands": Island.objects.none(),
            "provinces": Province.objects.none(),
            "businesses": Organization.objects.none(),
            "organizations": Organization.objects.none(),
            "regions": SalesRegion.objects.none(),
            "areas": SalesArea.objects.none(),
            "regencies": Regency.objects.none(),
        }

    # PRIORITY 1: Admin (is_staff or is_superuser) gets full access
    if user.is_superuser or user.is_staff:
        return None

    assignment = get_user_assignment(user)

    # PRIORITY 2: Get user's site_id from assignment
    user_site_id = get_user_site_id(user)

    # PRIORITY 3: site_id=1 → full access
    if user_site_id == 1:
        return None

    # PRIORITY 4: Scope by the position FK directly — the region(s) this user's
    # position manages (SalesRegion.position). Exact match, no name/regex
    # heuristics that can silently fail open. No match -> no access (fail-closed).
    if not assignment or not assignment.position:
        return empty_scope()

    regions = SalesRegion.objects.filter(
        position=assignment.position,
        deleted=False,
        status=1,
    ).select_related("business", "position")

    if not regions.exists():
        return empty_scope()

    region_ids = regions.values_list("id", flat=True)

    active_region_mappings = RegionProvince.objects.filter(
        region_id__in=region_ids,
        deleted=False,
        status=1,
    )
    province_ids = active_region_mappings.values_list(
        "province_id", flat=True
    ).distinct()
    provinces = Province.objects.filter(id__in=province_ids)
    island_ids = provinces.values_list("island_id", flat=True).distinct()

    areas = SalesArea.objects.filter(
        region__in=regions,
        deleted=False,
        status=1,
    )
    regency_ids = AreaRegency.objects.filter(
        area__in=areas,
        deleted=False,
        status=1,
    ).values_list("regency_id", flat=True).distinct()

    # SalesRegion no longer has an `organization` FK; organization is reached
    # through its position (SalesRegion.position -> Position.organization).
    organization_ids = (
        Position.objects.filter(id__in=regions.values_list("position_id", flat=True))
        .exclude(organization_id__isnull=True)
        .values_list("organization_id", flat=True)
        .distinct()
    )

    return {
        "islands": Island.objects.filter(id__in=island_ids),
        "provinces": provinces,
        "businesses": Business.objects.filter(
            id__in=regions.values_list("business_id", flat=True).distinct()
        ),
        "organizations": Organization.objects.filter(id__in=organization_ids),
        "regions": regions,
        "areas": areas,
        "regencies": Regency.objects.filter(id__in=regency_ids),
    }


def has_full_territory_access(user):
    return user.is_superuser or user.is_staff or get_user_site_id(user) == 1


# Role comes from the Assignment -> EmployeeTitle FK. `code` is that table's
# machine-readable key (MR / AM / RM / NSM / KAM / ...), so it is matched
# directly instead of pattern-matching position names. Four legacy titles have
# a blank code ("Regional Manager (Acting)", "Area Manager (Acting)",
# "Manager", "President Director") — treated as a data anomaly to fix in the
# title row, not something to work around here.
TITLE_RM = "RM"
TITLE_AM = "AM"
TITLE_NSM = "NSM"


def get_user_title_code(user):
    title = getattr(get_user_assignment(user), "title", None)
    return (getattr(title, "code", "") or "").strip().upper()


def is_region_manager(user):
    return get_user_title_code(user) == TITLE_RM


def is_area_manager(user):
    return get_user_title_code(user) == TITLE_AM


def is_national_sales_manager(user):
    return get_user_title_code(user) == TITLE_NSM


def can_manage_territory_assignments(user):
    """Admin/HO, NSM, Regional Manager, and Area Manager may change assignments.

    NSM is included, but that is not the same as has_full_territory_access:
    there is an NSM per half of the country (West / East), so they stay scoped
    to their own position subtree rather than seeing everything.
    """
    return has_full_territory_access(user) or get_user_title_code(user) in {
        TITLE_NSM,
        TITLE_RM,
        TITLE_AM,
    }


def can_view_territory_overview(user):
    """Sees the scoped (not personal) summary."""
    return can_manage_territory_assignments(user)


def can_manage_region_matrix(user):
    """Province-to-region mapping is a region-tier tool: Admin/HO, NSM, and RM.
    An Area Manager works below that tier and is deliberately excluded."""
    return has_full_territory_access(user) or get_user_title_code(user) in {
        TITLE_NSM,
        TITLE_RM,
    }


def can_manage_area_matrix(user):
    """Area-to-regency mapping: Admin/HO, NSM, RM, and AM — an area is the
    Area Manager's own tier. MedReps are read-only here."""
    return has_full_territory_access(user) or get_user_title_code(user) in {
        TITLE_NSM,
        TITLE_RM,
        TITLE_AM,
    }


def can_edit_region_dates(user):
    """Return True if user is allowed to edit Effective/Terminate on Region Matrix.

    Allowed: Admin (is_staff/is_superuser), HO (site_id==1), RM (regional manager)
    """
    if user.is_superuser or user.is_staff:
        return True
    if get_user_site_id(user) == 1:
        return True
    return is_region_manager(user)


def can_edit_area_dates(user):
    """Return True if user is allowed to edit Effective/Terminate on Area Matrix.

    Allowed: Admin, HO, RM, AM
    """
    if user.is_superuser or user.is_staff:
        return True
    if get_user_site_id(user) == 1:
        return True
    # RM also allowed on area matrix
    if is_region_manager(user):
        return True
    return is_area_manager(user)


def _reserve_slug(model, desired_slug):
    """Ensure `desired_slug` is free for new record by renaming existing records
    that currently use the same base slug. Old records will be renamed to
    desired_slug-1, desired_slug-2, ... in order of ascending id (oldest first).

    This is done inside a transaction and uses temporary uuids to avoid
    intermediate unique constraint collisions.

    Returns the desired_slug (for convenience).
    """
    # Quick exit if no conflicts
    conflicts = model.objects.filter(slug__startswith=desired_slug).order_by('id')
    if not conflicts.exists():
        return desired_slug

    pks = [c.pk for c in conflicts]

    with transaction.atomic():
        # Temporarily rename all conflicting slugs to unique tmp values
        tmp_map = {}
        for pk in pks:
            obj = model.objects.select_for_update().get(pk=pk)
            tmp = f"__tmp__{uuid4().hex}"
            obj.slug = tmp
            obj.save(update_fields=['slug'])
            tmp_map[pk] = tmp

        # Reassign stable numeric suffixes starting at 1 for oldest first
        for idx, pk in enumerate(pks, start=1):
            obj = model.objects.get(pk=pk)
            obj.slug = f"{desired_slug}-{idx}"
            obj.save(update_fields=['slug'])

    return desired_slug


def get_user_assignment_position_scope(user):
    assignment = get_user_assignment(user)
    position = getattr(assignment, "position", None)
    if not position:
        return Position.objects.none()

    scoped_position_ids = {position.id}
    pending_ids = [position.id]

    while pending_ids:
        child_ids = list(
            Position.objects.filter(
                parent_id__in=pending_ids,
                deleted=False,
                status=1,
            ).values_list("id", flat=True)
        )
        pending_ids = [child_id for child_id in child_ids if child_id not in scoped_position_ids]
        scoped_position_ids.update(pending_ids)

    return Position.objects.filter(
        id__in=scoped_position_ids, deleted=False, status=1
    )


def is_area_mapping_in_user_scope(user, area, regency):
    scope = get_user_region_scope(user)
    if scope is None:
        return True

    return (
        scope["regions"].filter(id=area.region_id).exists()
        and scope["provinces"].filter(id=regency.province_id).exists()
    )


# FaisalS | HF-23 - Region Matrix UI
# Updates: Jun/11-2026 by FaisalS — role-based access control
@login_required
@require_POST
def region_matrix_update(request):
    province_id = request.POST.get("province_id")
    region_id = request.POST.get("region_id")
    action = request.POST.get("action")
    is_admin = request.user.is_superuser or request.user.is_staff
    can_edit_effective_date = can_edit_region_dates(request.user)

    # Allow Admin, HO and RM
    if not can_manage_region_matrix(request.user):
        return HttpResponseForbidden("Permission denied.")

    if not province_id or not region_id:
        return HttpResponseBadRequest("Missing required data.")

    # Non-admin is not permitted to perform the inactive action
    if action == "inactive" and not is_admin:
        return HttpResponseBadRequest("Permission denied.")

    effective_date = parse_date(request.POST.get("effective"))
    terminated_date = parse_date(request.POST.get("terminated"))

    # Validate dates only when a non-empty value is submitted
    if can_edit_effective_date and ("effective" in request.POST and request.POST.get("effective") != "") and not effective_date:
        return HttpResponseBadRequest("Invalid effective date format.")
    if ("terminated" in request.POST and request.POST.get("terminated") != "") and not terminated_date:
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
        # Creating a new mapping requires a non-empty effective date field
        if not ("effective" in request.POST and request.POST.get("effective") != "") or not effective_date:
            return HttpResponseBadRequest(
                "Mapping not found and no effective date provided."
            )

        desired_slug = region.slug + "-" + province.shortname.lower()
        try:
            _reserve_slug(RegionProvince, desired_slug)
        except Exception:
            # best-effort: if reserve fails, append uuid to avoid blocking
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        mapping = RegionProvince.objects.create(
            slug=desired_slug,
            province_id=province_id,
            region_id=region_id,
            effective=effective_date,
            status=1,
            cat=now(),
            cby_id=request.user,
        )
        SystemLogService.log(
            request=request,
            action=LogAction.CREATE,
            module="Sales",
            feature="Region Province Matrix",
            description=f"Created mapping for Province {province.name} and Region {region.name}.",
            obj=new_mapping,
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({"status": "created"})

    if action == "delete":
        mapping.status = 0
        mapping.dat = now()
        mapping.dby = request.user
        log_act = LogAction.DELETE
        desc = f"Deleted mapping for Province {province.name} and Region {region.name}."
    else:
        mapping.status = 0 if terminated_date else 1
        mapping.terminated = terminated_date
        log_act = LogAction.UPDATE
        desc = f"Updated mapping for Province {province.name} and Region {region.name}."

    if action == "inactive":
        # Versioning for inactive: mark current record as history, then insert a
        # new record with status=0 (inactive). This preserves ID history.
        old_status = mapping.status
        old_effective = mapping.effective
        old_terminated = mapping.terminated

        # Deactivate existing record (history)
        mapping.status = 0
        mapping.uat = now()
        mapping.uby = request.user
        mapping.save()

        # Create new inactive record mirroring the mapping but with status=0
        desired_slug = region.slug + "-" + province.shortname.lower()
        try:
            _reserve_slug(RegionProvince, desired_slug)
        except Exception:
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        new_mapping = RegionProvince.objects.create(
            slug=desired_slug,
            province_id=province_id,
            region_id=region_id,
            effective=None,
            terminated=None,
            status=0,
            cat=now(),
            cby_id=request.user,
        )

        # RegionProvinceHistory removed: historical records no longer maintained
        return JsonResponse({"status": "inactivated"})
    else:
        # Versioning: deactivate current active record, then insert new record
        mapping.status = 0
        mapping.uat = now()
        mapping.uby = request.user
        mapping.save()

        # Determine new values
        new_effective = old_effective
        # Only update effective when user provided a non-empty value
        if can_edit_effective_date and ("effective" in request.POST and request.POST.get("effective") != ""):
            new_effective = effective_date

        new_terminated = old_terminated
        if ("terminated" in request.POST and request.POST.get("terminated") != ""):
            new_terminated = terminated_date

        # New record status: terminated -> 0, else 1
        new_status = 0 if new_terminated else 1

        # If new record will be active, ensure an effective date was provided
        if new_status == 1 and not new_effective:
            return HttpResponseBadRequest("Effective date required for activation.")

        desired_slug = region.slug + "-" + province.shortname.lower()
        try:
            _reserve_slug(RegionProvince, desired_slug)
        except Exception:
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        new_mapping = RegionProvince.objects.create(
            slug=desired_slug,
            province_id=province_id,
            region_id=region_id,
            effective=new_effective,
            terminated=new_terminated,
            status=new_status,
            cat=now(),
            cby_id=request.user,
        )

        # RegionProvinceHistory removed: historical records no longer maintained

    SystemLogService.log(
        request=request,
        action=log_act,
        module="Sales",
        feature="Region Province Matrix",
        description=desc,
        obj=mapping,
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return JsonResponse({"status": "ok"})


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: region_matrix_history                               ║
# ║  Type: Function base view (AJAX)                           ║
# ║  Purpose: Return audit trail for a province/region pair    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\sales_territoryview.py             ║
# ║  Created: Jun/11-2026 by FaisalS                           ║
# ╚════════════════════════════════════════════════════════════╝
# RegionProvinceHistory endpoint removed — history tables were dropped


# FaisalS | HF-30 - Area Matrix UI
# UtandraJ | 
@login_required
def area_matrix_view(request):
    if not can_manage_area_matrix(request.user):
        return HttpResponseForbidden("Permission denied.")

    user_site_id = get_user_site_id(request.user)
    is_admin = request.user.is_superuser or request.user.is_staff
    
    # Get user's region scope based on site_id
    # site_id=1 → return None (full access)
    # site_id!=1 → return filtered dict
    # site_id=None → return empty dict
    region_scope = get_user_region_scope(request.user)

    # If region_scope is None, user has full access (site_id=1 or is_admin)
    # If region_scope is dict, use it for filtering (site_id!=1)
    if region_scope is None:
        # Full access user: can see all options
        islands = Island.objects.order_by("code")
        provinces = Province.objects.order_by("code")
        businesses = Business.objects.filter(region_business__isnull=False).distinct().order_by("name")
        organization_ids = (
            SalesRegion.objects.exclude(position__organization_id__isnull=True)
            .values_list("position__organization_id", flat=True)
            .distinct()
        )
        organizations = Organization.objects.filter(id__in=organization_ids).distinct().order_by("name")
        regions = SalesRegion.objects.order_by("code")
    else:
        # Filtered access user: restricted to their assigned regions/provinces/organizations
        islands = region_scope["islands"].order_by("code")
        provinces = region_scope["provinces"].order_by("code")
        businesses = region_scope["businesses"].distinct().order_by("name")
        organizations = region_scope["organizations"].distinct().order_by("name")
        regions = region_scope["regions"].order_by("code")
    
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="Area Regency Matrix",
        description="User accessed Area Regency Matrix view.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    
    regencies = Regency.objects.order_by("code")
    areas = SalesArea.objects.filter(region__in=regions).order_by("code")
    # Build active_map from AreaRegency ordered so the newest record per
    # (regency, area) pair is used. We iterate and take the first occurrence
    # for each key (newest due to -id ordering) to avoid showing stale data.
    active_map = {}
    area_mappings_qs = (
        AreaRegency.objects.select_related("regency", "area").order_by("regency_id", "area_id", "-id")
    )
    for mapping in area_mappings_qs:
        key = (mapping.regency_id, mapping.area_id)
        if key not in active_map:
            active_map[key] = mapping
    shared_regency_ids = (
        AreaRegency.objects.filter(status=1)
        .values("regency")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("regency", flat=True)
    )

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

    selected_islands = islands.filter(id__in=selected_island_ids).order_by(
        "code"
    )
    selected_provinces = provinces.filter(id__in=selected_province_ids).order_by(
        "code"
    )
    selected_businesses = Business.objects.filter(
        id__in=selected_business_ids
    ).order_by("code")
    selected_organizations = organizations.filter(
        id__in=selected_organization_ids
    ).order_by("code")
    selected_regions = regions.filter(id__in=selected_region_ids).order_by(
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
        "shared_regency_ids": shared_regency_ids,
        "mode": mode,
        "is_admin": request.user.is_superuser or request.user.is_staff,
        "user_site_id": get_user_site_id(request.user),
        "can_edit_effective_date": can_edit_area_dates(request.user),
    }

    return render(request, "sales/territory/area_matrix.html", context)


def ajax_filter_provinces(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="AJAX Filter Provinces",
        description="User filtered provinces via AJAX.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    island_ids = request.GET.getlist("island_ids[]")
    region_scope = get_user_region_scope(request.user)
    provinces = Province.objects.filter(island_id__in=island_ids)
    if region_scope is not None:
        provinces = provinces.filter(id__in=region_scope["provinces"].values_list("id", flat=True))
    provinces = provinces.values("id", "name")
    return JsonResponse(list(provinces), safe=False)


def ajax_filter_organizations(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="AJAX Filter Organizations",
        description="User filtered organizations via AJAX.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    business_ids = request.GET.getlist("business_ids[]")
    region_scope = get_user_region_scope(request.user)
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
    if region_scope is not None:
        organizations = organizations.filter(id__in=region_scope["organizations"].values_list("id", flat=True))

    org_list = [{"id": org.id, "shortname": org.shortname} for org in organizations]
    return JsonResponse(org_list, safe=False)


def ajax_filter_regions(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="AJAX Filter Regions",
        description="User filtered regions via AJAX.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    org_ids = request.GET.getlist("organization_ids[]")
    region_scope = get_user_region_scope(request.user)
    regions = (
        SalesRegion.objects.filter(position__organization_id__in=org_ids)
        .select_related("position", "position__organization")
        .order_by("code")
        .distinct()
    )
    if region_scope is not None:
        regions = regions.filter(id__in=region_scope["regions"].values_list("id", flat=True))

    region_list = [{"id": reg.id, "shortname": reg.shortname} for reg in regions]
    return JsonResponse(region_list, safe=False)


@login_required
def ajax_filter_territory_regencies(request):
    """Live Province -> Regency cascade for Territory Assignment (no page
    reload needed, unlike the rest of that page which is plain GET+Apply).
    Scoped the same way as the matrix itself (get_scoped_assignable_customers,
    NOT get_user_region_scope) so an Area Manager only sees regencies that
    actually have customers in their own territory scope."""
    province_ids = request.GET.getlist("province_ids[]")
    if not province_ids:
        return JsonResponse([], safe=False)

    customers = get_scoped_assignable_customers(request.user).filter(
        province_id__in=province_ids
    )
    regency_ids = customers.values_list("regency_id", flat=True).distinct()
    regencies = Regency.objects.filter(id__in=regency_ids).order_by("name")
    data = [{"id": r.id, "name": r.name} for r in regencies]
    return JsonResponse(data, safe=False)


# FaisalS | HF-30 - Area Matrix UI
@login_required
@require_POST
def area_matrix_update(request):
    if not can_manage_area_matrix(request.user):
        return HttpResponseForbidden("Permission denied.")

    regency_id = request.POST.get("regency_id")
    area_id = request.POST.get("area_id")
    effective_date = parse_date(request.POST.get("effective"))
    terminated_date = parse_date(request.POST.get("terminated"))
    action = request.POST.get("action")
    bulk_mode = request.POST.get("bulk_mode")
    bulk_operation = request.POST.get("bulk_operation")
    is_admin = request.user.is_superuser or request.user.is_staff
    can_edit_effective_date = can_edit_area_dates(request.user)

    if not regency_id or not area_id:
        return HttpResponseBadRequest("Missing required data.")

    if action == "delete" and not is_admin:
        return HttpResponseBadRequest("Permission denied.")

    # Validate dates only when a non-empty value is submitted
    if can_edit_effective_date and ("effective" in request.POST and request.POST.get("effective") != "") and not effective_date:
        return HttpResponseBadRequest("Invalid effective date format.")
    if ("terminated" in request.POST and request.POST.get("terminated") != "") and not terminated_date:
        return HttpResponseBadRequest("Invalid terminated date format.")

    try:
        regency = Regency.objects.get(id=regency_id)
        area = SalesArea.objects.get(id=area_id)
    except (Regency.DoesNotExist, SalesArea.DoesNotExist):
        return HttpResponseBadRequest("Regency or Area not found.")

    if not is_area_mapping_in_user_scope(request.user, area, regency):
        return HttpResponseForbidden("Permission denied.")

    mapping = (
        AreaRegency.objects.filter(regency=regency, area=area).order_by("-id").first()
    )

    if bulk_mode == "true":
        if bulk_operation == "activate":
            if not mapping:
                if not effective_date:
                    effective_date = now().date()

                desired_slug = f"{area.initial}-{regency.code}"
                try:
                    _reserve_slug(AreaRegency, desired_slug)
                except Exception:
                    desired_slug = desired_slug + "-" + uuid4().hex[:8]

                if not mapping:
                    new_mapping = AreaRegency.objects.create(
                        slug=desired_slug,
                        initial=f"{area.initial}-{regency.code}",
                        shortname=f"{area.initial}-{regency.type.code if hasattr(regency, 'type') and regency.type else ''}. {regency.name}",
                        regency_id=regency_id,
                        area_id=area_id,
                        effective=effective_date,
                        status=1,
                        terminated=None,
                        cat=now(),
                        cby_id=request.user,
                    )
                    SystemLogService.log(
                        request=request,
                        action=LogAction.CREATE,
                        module="Sales",
                        feature="Area Regency Matrix",
                        description=f"Bulk activated mapping for Regency {regency.name} and Area {area.name}.",
                        obj=new_mapping,
                        status="SUCCESS",
                        log_type="SYSTEM",
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
                    SystemLogService.log(
                        request=request,
                        action=LogAction.UPDATE,
                        module="Sales",
                        feature="Area Regency Matrix",
                        description=f"Bulk reactivated mapping for Regency {regency.name} and Area {area.name}.",
                        obj=mapping,
                        status="SUCCESS",
                        log_type="SYSTEM",
                    )
                    return JsonResponse(
                        {"status": "updated", "operation": bulk_operation}
                    )
            else:
                return JsonResponse(
                    {"status": "no_change", "operation": bulk_operation}
                )
                # AreaRegencyHistory removed: historical records no longer maintained
                return JsonResponse({"status": "created", "operation": bulk_operation})

            # mapping exists: if inactive -> create a new active version
            if mapping and mapping.status == 0:
                if not effective_date:
                    effective_date = now().date()

                # deactivate existing (already inactive) but still record history and insert new
                old_status = mapping.status
                old_effective = mapping.effective
                old_terminated = mapping.terminated

                desired_slug = f"{area.initial}-{regency.code}"
                try:
                    _reserve_slug(AreaRegency, desired_slug)
                except Exception:
                    desired_slug = desired_slug + "-" + uuid4().hex[:8]

                new_mapping = AreaRegency.objects.create(
                    slug=desired_slug,
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
                # AreaRegencyHistory removed: historical records no longer maintained
                return JsonResponse({"status": "created", "operation": bulk_operation})
            else:
                return JsonResponse({"status": "no_change", "operation": bulk_operation})
            

        elif bulk_operation == "deactivate":
            if mapping and mapping.status == 1:
                if not terminated_date:
                    return JsonResponse({
                        "status": "error",
                        "message": "Termination date required for deactivation",
                    })

                old_status = mapping.status
                old_effective = mapping.effective
                old_terminated = mapping.terminated

                # Deactivate existing record (mark as history)
                mapping.status = 0
                mapping.uat = now()
                mapping.uby = request.user
                mapping.save()

                desired_slug = f"{area.initial}-{regency.code}"
                try:
                    _reserve_slug(AreaRegency, desired_slug)
                except Exception:
                    desired_slug = desired_slug + "-" + uuid4().hex[:8]

                # Insert new inactive record with provided terminated date
                new_mapping = AreaRegency.objects.create(
                    slug=desired_slug,
                    initial=f"{area.initial}-{regency.code}",
                    shortname=f"{area.initial}-{regency.type.code}. {regency.name}",
                    regency_id=regency_id,
                    area_id=area_id,
                    effective=None,
                    terminated=terminated_date,
                    status=0,
                    cat=now(),
                    cby_id=request.user,
                )
                # AreaRegencyHistory removed: historical records no longer maintained
                
                SystemLogService.log(
                    request=request,
                    action=LogAction.UPDATE,
                    module="Sales",
                    feature="Area Regency Matrix",
                    description=f"Bulk deactivated mapping for Regency {regency.name} and Area {area.name}.",
                    obj=mapping,
                    status="SUCCESS",
                    log_type="SYSTEM",
                )
                return JsonResponse({"status": "updated", "operation": bulk_operation})
            else:
                return JsonResponse({"status": "no_change", "operation": bulk_operation})
        else:
            return JsonResponse({"status": "invalid_operation"})

    if not mapping:
        # Creating a new mapping requires a non-empty effective date field
        if not ("effective" in request.POST and request.POST.get("effective") != "") or not effective_date:
            return HttpResponseBadRequest(
                "Mapping not found and no effective date provided."
            )

        desired_slug = f"{area.initial}-{regency.code}"
        try:
            _reserve_slug(AreaRegency, desired_slug)
        except Exception:
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        mapping = AreaRegency.objects.create(
            slug=desired_slug,
            initial=f"{area.initial}-{regency.code}",
            shortname=f"{area.initial}-{regency.type.code if hasattr(regency, 'type') and regency.type else ''}. {regency.name}",
            regency_id=regency_id,
            area_id=area_id,
            effective=effective_date,
            status=1,
            cat=now(),
            cby_id=request.user,
        )
        SystemLogService.log(
            request=request,
            action=LogAction.CREATE,
            module="Sales",
            feature="Area Regency Matrix",
            description=f"Created mapping for Regency {regency.name} and Area {area.name}.",
            obj=new_mapping,
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({"status": "created"})

    if action == "delete":
        mapping.status = 0
        mapping.dat = now()
        mapping.dby = request.user
        log_act = LogAction.DELETE
        desc = f"Deleted mapping for Regency {regency.name} and Area {area.name}."
    else:
        mapping.status = 0 if terminated_date else 1
        mapping.terminated = terminated_date
        log_act = LogAction.UPDATE
        desc = f"Updated mapping for Regency {regency.name} and Area {area.name}."

    if action == "delete":
        # Versioning for delete/inactive: mark current record as history, then
        # insert a new record with status=0 so old id remains as history.
        old_status = mapping.status
        old_effective = mapping.effective
        old_terminated = mapping.terminated

        # Deactivate existing record (history)
        mapping.status = 0
        mapping.uat = now()
        mapping.uby = request.user
        mapping.save()

        desired_slug = f"{area.initial}-{regency.code}"
        try:
            _reserve_slug(AreaRegency, desired_slug)
        except Exception:
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        new_mapping = AreaRegency.objects.create(
            slug=desired_slug,
            initial=f"{area.initial}-{regency.code}",
            shortname=f"{area.initial}-{regency.type.code}. {regency.name}",
            regency_id=regency_id,
            area_id=area_id,
            effective=None,
            terminated=None,
            status=0,
            cat=now(),
            cby_id=request.user,
        )

        # AreaRegencyHistory removed: historical records no longer maintained
        return JsonResponse({"status": "inactivated"})
    else:
        # Versioning: deactivate old record and create new one
        mapping.status = 0
        mapping.uat = now()
        mapping.uby = request.user
        mapping.save()

        new_effective = old_effective
        # Only update effective when user provided a non-empty value
        if can_edit_effective_date and ("effective" in request.POST and request.POST.get("effective") != ""):
            new_effective = effective_date

        new_terminated = old_terminated
        if ("terminated" in request.POST and request.POST.get("terminated") != ""):
            new_terminated = terminated_date

        new_status = 0 if new_terminated else 1

        # If new record will be active, ensure an effective date was provided
        if new_status == 1 and not new_effective:
            return HttpResponseBadRequest("Effective date required for activation.")

        desired_slug = f"{area.initial}-{regency.code}"
        try:
            _reserve_slug(AreaRegency, desired_slug)
        except Exception:
            desired_slug = desired_slug + "-" + uuid4().hex[:8]

        new_mapping = AreaRegency.objects.create(
            slug=desired_slug,
            initial=f"{area.initial}-{regency.code}",
            shortname=f"{area.initial}-{regency.type.code}. {regency.name}",
            regency_id=regency_id,
            area_id=area_id,
            effective=new_effective,
            terminated=new_terminated,
            status=new_status,
            cat=now(),
            cby_id=request.user,
        )

        # AreaRegencyHistory removed: historical records no longer maintained

    SystemLogService.log(
        request=request,
        action=log_act,
        module="Sales",
        feature="Area Regency Matrix",
        description=desc,
        obj=mapping,
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return JsonResponse({"status": "ok"})


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: area_matrix_history                                 ║
# ║  Type: Function base view (AJAX)                           ║
# ║  Purpose: Return audit trail for an area/regency pair      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\views\sales_territoryview.py             ║
# ║  Created: Jun/11-2026 by FaisalS                           ║
# ╚════════════════════════════════════════════════════════════╝
# AreaRegencyHistory endpoint removed — history tables were dropped



# ╔════════════════════════════════════════════════════════════╗
# ║  Territory Assignment (2026-08-21 — merged view + assign)   ║
# ║  Single page, matching the Region Matrix / Area Matrix       ║
# ║  pattern: one customer-centric table that both shows the     ║
# ║  current MedRep (view) and lets a scoped user check off       ║
# ║  customers and bulk-assign them to one MedRep (write).        ║
# ║  Previously this was 2 separate pages/tabs; the user flagged  ║
# ║  that as redundant navigation and asked for one page, so the  ║
# ║  old flat per-assignment report view and the standalone       ║
# ║  assign page were combined here.                              ║
# ╚════════════════════════════════════════════════════════════╝

def get_user_territory_province_scope(user):
    """Return provinces mapped to the user's region or area position."""
    if has_full_territory_access(user):
        return None

    assignment = get_user_assignment(user)
    position = getattr(assignment, "position", None)
    user_position = position
    visited_ids = set()

    # Positions ABOVE the region tier (NSM, Sales Director) own several
    # SalesRegions through their descendants, so walking up finds nothing and
    # the scope would come back empty. Take the union of every region in their
    # own subtree instead — which keeps an NSM inside their own half of the
    # country rather than handing them everything. A Regional Manager matches
    # here too (their own position is the region's), which is the same result
    # the walk-up produced; only Area Manager and below fall through to it.
    if user_position:
        subtree_regions = SalesRegion.objects.filter(
            position__in=get_user_assignment_position_scope(user),
            deleted=False,
            status=1,
        )
        if subtree_regions.exists():
            province_ids = RegionProvince.objects.filter(
                region__in=subtree_regions, deleted=False, status=1
            ).values_list("province_id", flat=True)
            return Province.objects.filter(id__in=province_ids).distinct()

    while position and position.id not in visited_ids:
        visited_ids.add(position.id)
        regions = SalesRegion.objects.filter(
            position=position, deleted=False, status=1
        )
        if regions.exists():
            if position.id != user_position.id:
                area_initial = str(user_position.initial or "").strip().upper()
                area_initial = area_initial.rsplit("-", 1)[-1]
                area_keys = []
                for key in (
                    area_initial,
                    re.sub(r"\.\d+$", "", area_initial),
                    re.sub(r"\d+$", "", area_initial),
                ):
                    if key and key not in area_keys:
                        area_keys.append(key)

                for area_key in area_keys:
                    areas = list(
                        SalesArea.objects.filter(
                            region__in=regions,
                            initial__iexact=area_key,
                            deleted=False,
                            status=1,
                        )[:2]
                    )
                    if len(areas) > 1:
                        return Province.objects.none()
                    if areas:
                        area = areas[0]
                        regency_ids = AreaRegency.objects.filter(
                            area=area,
                            deleted=False,
                            status=1,
                            regency_id__isnull=False,
                        ).values_list("regency_id", flat=True)
                        province_ids = Regency.objects.filter(
                            id__in=regency_ids,
                            province_id__isnull=False,
                        ).values_list("province_id", flat=True)
                        return Province.objects.filter(id__in=province_ids).distinct()
                return Province.objects.none()

            province_ids = RegionProvince.objects.filter(
                region__in=regions, deleted=False, status=1
            ).values_list("province_id", flat=True)
            return Province.objects.filter(id__in=province_ids).distinct()
        position = position.parent

    return Province.objects.none()



def is_assignment_in_user_position_scope(user, assignment):
    """Fail-closed check: is the target Assignment's position the user's own
    position or one of its descendants (get_user_assignment_position_scope)?
    Full-access users (admin/staff/site_id==1) bypass this."""
    if has_full_territory_access(user):
        return True
    user_assignment = get_user_assignment(user)
    if (
        user_assignment
        and user_assignment.position_id
        and user_assignment.position_id == assignment.position_id
    ):
        return False
    scoped_positions = get_user_assignment_position_scope(user)
    return scoped_positions.filter(id=assignment.position_id).exists()


def get_scoped_assignable_customers(user):
    """Customers inside the logged-in user's territory province scope."""
    customers = Customer.nondeleted_objects.select_related(
        "province", "regency", "district"
    )
    provinces = get_user_territory_province_scope(user)
    if provinces is not None:
        customers = customers.filter(province__in=provinces)
    return customers


def _territory_assignment_status(record, as_of_date):
    if record.effective and record.effective > as_of_date:
        return "upcoming"
    if (
        (record.terminated and record.terminated <= as_of_date)
        or (record.status != 1 and not record.terminated)
    ):
        return "ended"
    return "active"


def _territory_assignment_address(customer):
    parts = [
        customer.building,
        customer.street,
        customer.complex,
        customer.district.name if customer.district else None,
        customer.regency.name if customer.regency else None,
        customer.province.name if customer.province else None,
        customer.postcode,
    ]
    address = []
    for part in parts:
        value = str(part or "").strip()
        if value and value not in address:
            address.append(value)
    return ", ".join(address) or "-"


def _assignment_is_active_on(assignment, as_of_date):
    return (
        assignment
        and not assignment.deleted
        and assignment.status == 1
        and (not assignment.effective or assignment.effective <= as_of_date)
        and (not assignment.terminated or assignment.terminated > as_of_date)
    )


@login_required
def territory_assignment_summary_view(request):
    """Read-only territory assignments, scoped to the logged-in user's role.

    One row remains one TerritoryAssignment, so a customer assigned to multiple
    MedReps is intentionally displayed more than once.
    """
    today = now().date()
    as_of_date = today
    search = request.GET.get("q", "").strip()

    def selected_integer_ids(name):
        values = []
        for raw_value in request.GET.getlist(name):
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                continue
            if value > 0 and value not in values:
                values.append(value)
        return values

    selected_status = request.GET.get("status", "active").strip().lower()
    if selected_status not in {"active", "upcoming", "ended", "all"}:
        selected_status = "active"

    selected_custtype_ids = selected_integer_ids("custtype")
    selected_regency_ids = selected_integer_ids("regency")
    selected_position_ids = selected_integer_ids("position")

    is_full_access = has_full_territory_access(request.user)
    can_manage = can_manage_territory_assignments(request.user)
    # Wider than can_manage: NSM sees the whole scope below them, read-only.
    is_personal_view = not can_view_territory_overview(request.user)
    user_assignment = get_user_assignment(request.user)

    records = (
        TerritoryAssignment.objects.filter(
            deleted=False,
            assignment__isnull=False,
            customer__isnull=False,
            assignment__deleted=False,
            assignment__position__deleted=False,
            customer__deleted=False,
        )
        .select_related(
            "assignment",
            "assignment__employee",
            "assignment__position",
            "customer",
            "customer__custtype",
            "customer__province",
            "customer__regency",
            "customer__district",
        )
    )

    if not is_full_access:
        user_position_id = getattr(user_assignment, "position_id", None)
        if not user_position_id:
            records = records.none()
        elif is_personal_view:
            # Territory follows the position/seat. A replacement MR therefore
            # sees customers previously attached to the same position.
            records = records.filter(assignment__position_id=user_position_id)
        else:
            scoped_position_ids = (
                get_user_assignment_position_scope(request.user)
                .exclude(id=user_position_id)
                .values_list("id", flat=True)
            )
            scoped_customer_ids = get_scoped_assignable_customers(
                request.user
            ).values_list("id", flat=True)
            records = records.filter(
                assignment__position_id__in=scoped_position_ids,
                customer_id__in=scoped_customer_ids,
            )

    # Keep filter choices tied to the user's authorized scope, but independent
    # from the current filter selection so the inline filter bar always offers
    # every valid choice available to this user.
    option_records = records

    custtype_options = list(
        option_records.exclude(customer__custtype_id__isnull=True)
        .values("customer__custtype_id", "customer__custtype__name")
        .distinct()
        .order_by("customer__custtype__name")
    )
    regency_options = list(
        option_records.exclude(customer__regency_id__isnull=True)
        .values("customer__regency_id", "customer__regency__name")
        .distinct()
        .order_by("customer__regency__name")
    )
    position_options = list(
        option_records.exclude(assignment__position_id__isnull=True)
        .values("assignment__position_id", "assignment__position__name")
        .distinct()
        .order_by("assignment__position__name")
    )

    option_position_ids = [
        option["assignment__position_id"] for option in position_options
    ]
    current_holder_by_position = {}
    if option_position_ids:
        current_holders = (
            Assignment.objects.filter(
                position_id__in=option_position_ids,
                deleted=False,
                status=1,
            )
            .filter(Q(effective__isnull=True) | Q(effective__lte=as_of_date))
            .filter(Q(terminated__isnull=True) | Q(terminated__gt=as_of_date))
            .select_related("employee", "position")
            .order_by("position_id", "-effective", "-id")
        )
        for assignment in current_holders:
            current_holder_by_position.setdefault(
                assignment.position_id, assignment
            )

    medrep_options = []
    for option in position_options:
        position_id = option["assignment__position_id"]
        current_holder = current_holder_by_position.get(position_id)
        medrep_options.append(
            {
                "id": position_id,
                "name": (
                    current_holder.employee.name
                    if current_holder and current_holder.employee
                    else option["assignment__position__name"] or "-"
                ),
                "position": option["assignment__position__name"] or "-",
            }
        )
    medrep_options.sort(key=lambda item: (item["name"] or "").lower())

    if selected_status == "active":
        records = (
            records.filter(
                Q(effective__isnull=True) | Q(effective__lte=as_of_date)
            )
            .filter(Q(terminated__isnull=True) | Q(terminated__gt=as_of_date))
            .exclude(status=0, terminated__isnull=True)
        )
    elif selected_status == "upcoming":
        records = records.filter(effective__gt=as_of_date)
    elif selected_status == "ended":
        records = records.filter(
            Q(terminated__lte=as_of_date)
            | Q(status=0, terminated__isnull=True)
        )

    if search:
        records = records.filter(
            Q(customer__code__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(customer__shortname__icontains=search)
            | Q(customer__alias__icontains=search)
            | Q(customer__custtype__name__icontains=search)
            | Q(customer__province__name__icontains=search)
            | Q(customer__regency__name__icontains=search)
            | Q(customer__district__name__icontains=search)
            | Q(assignment__employee__name__icontains=search)
            | Q(assignment__position__name__icontains=search)
        )

    if selected_custtype_ids:
        records = records.filter(customer__custtype_id__in=selected_custtype_ids)
    if selected_regency_ids:
        records = records.filter(customer__regency_id__in=selected_regency_ids)
    if selected_position_ids:
        records = records.filter(
            assignment__position_id__in=selected_position_ids
        )

    records = records.order_by(
        "customer__regency__name",
        "customer__name",
        "assignment__employee__name",
        "-effective",
        "-id",
    )
    paginator = Paginator(records, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    page_records = list(page_obj.object_list)
    position_ids = {
        record.assignment.position_id
        for record in page_records
        if record.assignment and record.assignment.position_id
    }
    current_by_position = {}
    if position_ids:
        current_assignments = (
            Assignment.objects.filter(
                position_id__in=position_ids,
                deleted=False,
                status=1,
            )
            .filter(Q(effective__isnull=True) | Q(effective__lte=as_of_date))
            .filter(Q(terminated__isnull=True) | Q(terminated__gt=as_of_date))
            .select_related("employee", "position")
            .order_by("position_id", "-effective", "-id")
        )
        for assignment in current_assignments:
            current_by_position.setdefault(assignment.position_id, assignment)

    rows = []
    for record in page_records:
        record_status = _territory_assignment_status(record, as_of_date)
        display_assignment = record.assignment
        if (
            record_status == "active"
            and record.assignment.position_id
            and not _assignment_is_active_on(record.assignment, as_of_date)
        ):
            display_assignment = current_by_position.get(
                record.assignment.position_id, record.assignment
            )
        rows.append(
            {
                "record": record,
                "customer": record.customer,
                "display_assignment": display_assignment,
                "status": record_status,
                "address": _territory_assignment_address(record.customer),
            }
        )

    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)
    if is_personal_view:
        employee_name = (
            user_assignment.employee.name
            if user_assignment and user_assignment.employee
            else request.user.get_username()
        )
        position_name = (
            user_assignment.position.name
            if user_assignment and user_assignment.position
            else "-"
        )
        page_title = "My Territory Assignments"
        page_subtitle = f"Customers assigned to {employee_name} · {position_name}"
    else:
        page_title = "Assignment Summary"
        page_subtitle = "Read-only customer and MedRep assignment overview."

    context = {
        "page_title": page_title,
        "page_subtitle": page_subtitle,
        "rows": rows,
        "page_obj": page_obj,
        "filter_query": query_without_page.urlencode(),
        "search": search,
        "selected_status": selected_status,
        "selected_custtype_ids": [str(value) for value in selected_custtype_ids],
        "selected_regency_ids": [str(value) for value in selected_regency_ids],
        "selected_position_ids": [str(value) for value in selected_position_ids],
        "custtype_options": custtype_options,
        "regency_options": regency_options,
        "medrep_options": medrep_options,
        "has_filters": bool(
            search
            or selected_custtype_ids
            or selected_regency_ids
            or selected_position_ids
            or selected_status != "active"
        ),
        "show_medrep": not is_personal_view,
        "can_manage": can_manage,
    }
    return render(
        request,
        "sales/territory/territory_assignment_summary.html",
        context,
    )


@login_required
def territory_assignment_view(request):
    """Matrix page (2026-08-21): rows = customer grouped by regency, columns =
    MedRep (Assignment) within the user's own position subtree, cell = click
    to assign/unassign — same interaction model as Region Matrix / Area
    Matrix, replacing the earlier DataTable+checkbox UI (user asked for a
    matrix people can just click through, not another data table)."""
    if not can_manage_territory_assignments(request.user):
        return redirect("sales:territory_assignment_summary")

    is_full_access = has_full_territory_access(request.user)
    user_assignment = get_user_assignment(request.user)
    scoped_positions = get_user_assignment_position_scope(request.user)

    assignment_options = (
        Assignment.objects.filter(
            position_id__in=scoped_positions.values_list("id", flat=True),
            status=1,
            terminated__isnull=True,
            deleted=False,
            position__deleted=False,
            position__status=1,
        )
        .select_related("employee", "position")
        .order_by("position__name", "employee__name")
    )
    if not is_full_access and user_assignment and user_assignment.position_id:
        assignment_options = assignment_options.exclude(
            position_id=user_assignment.position_id
        )
    # A pure admin/HO account usually has no Employee/Assignment of their own,
    # so get_user_assignment_position_scope resolves to nothing for them. Fall
    # back to every active Assignment so full-access users are not left with
    # an empty matrix (same "admin/HO bypasses scoping" convention already
    # used for read access elsewhere on this page).
    if not assignment_options.exists() and is_full_access:
        assignment_options = (
            Assignment.objects.filter(
                status=1,
                terminated__isnull=True,
                deleted=False,
                position__deleted=False,
                position__status=1,
            )
            .select_related("employee", "position")
            .order_by("position__name", "employee__name")
        )

    base_customers = get_scoped_assignable_customers(request.user)

    province_options = list(
        Province.objects.filter(id__in=base_customers.values_list("province_id", flat=True))
        .distinct()
        .order_by("name")
    )
    custtype_options = CustomerType.nondeleted_objects.order_by("name")

    selected_province_ids = [v for v in request.GET.getlist("province") if v]
    selected_custtype_ids = [v for v in request.GET.getlist("custtype") if v]
    selected_regency_ids = [v for v in request.GET.getlist("regency") if v]
    selected_medrep_ids = [v for v in request.GET.getlist("medrep") if v]

    if not selected_province_ids and not is_full_access and len(province_options) == 1:
        selected_province_ids = [str(province_options[0].id)]

    # Regency cascades from Province: only meaningful (and only populated)
    # once a Province is picked, same idea as Area Matrix's Island->Province
    # cascade — narrows the matrix further within the chosen province(s).
    # No AJAX needed here since Apply already does a full page reload, so
    # this can just be computed server-side from the current GET params.
    regency_options = Regency.objects.none()
    if selected_province_ids:
        regency_options = (
            Regency.objects.filter(
                id__in=base_customers.filter(
                    province_id__in=selected_province_ids
                ).values_list("regency_id", flat=True)
            )
            .distinct()
            .order_by("name")
        )
        # Drop any selected regency that doesn't actually belong to the
        # currently selected province(s) — e.g. stale query params left over
        # from switching Province — so it can't silently zero out the
        # matrix by intersecting with a regency outside the new province.
        valid_regency_ids = {str(r.id) for r in regency_options}
        selected_regency_ids = [v for v in selected_regency_ids if v in valid_regency_ids]

    matrix_ready = bool(
        selected_province_ids and selected_regency_ids and selected_custtype_ids
    )

    medrep_options = list(assignment_options)
    valid_medrep_ids = {str(option.id) for option in medrep_options}
    selected_medrep_ids = [
        value for value in selected_medrep_ids if value in valid_medrep_ids
    ]
    if selected_medrep_ids:
        selected_medrep_id_set = set(selected_medrep_ids)
        assignment_options = [
            option
            for option in medrep_options
            if str(option.id) in selected_medrep_id_set
        ]
    else:
        assignment_options = medrep_options

    # Load the matrix only after all primary filters are selected.
    # Rows per page. Nothing is dropped any more — the matrix is paged, so
    # every customer is reachable. A flat [:300] cut used to silently hide the
    # remainder, which also made each regency tab's badge count "rows that
    # survived the cut" rather than customers in that regency: widening the
    # Customer Type filter could make a tab's number go DOWN (Banda Aceh
    # 100 -> 59), because regencies earlier in the alphabet ate the budget.
    MATRIX_PAGE_SIZE = 300
    regency_groups = []
    total_customer_count = 0
    page_obj = None
    base_query = ""

    if matrix_ready:
        customers = base_customers.filter(province_id__in=selected_province_ids)
        if selected_regency_ids:
            customers = customers.filter(regency_id__in=selected_regency_ids)
        if selected_custtype_ids:
            customers = customers.filter(custtype_id__in=selected_custtype_ids)
        customers = customers.select_related(
            "province", "regency", "district", "custtype"
        ).order_by("regency__name", "name")

        # Pagination links have to carry the current filters. The page strips
        # its own query string after load, so links are rebuilt from the
        # server's view of the filters rather than read back off the URL.
        filter_params = QueryDict(mutable=True)
        filter_params.setlist("province", selected_province_ids)
        filter_params.setlist("regency", selected_regency_ids)
        filter_params.setlist("custtype", selected_custtype_ids)
        filter_params.setlist("medrep", selected_medrep_ids)
        base_query = filter_params.urlencode()

        paginator = Paginator(customers, MATRIX_PAGE_SIZE)
        total_customer_count = paginator.count

        # Clamp rather than catch: num_pages is always >= 1 (an empty result
        # still has a valid first page), so a clamped number can never make
        # paginator.page() raise, whatever junk arrives in ?page=.
        try:
            page_number = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page_number = 1
        page_number = max(1, min(page_number, paginator.num_pages))
        page_obj = paginator.page(page_number)
        customers = list(page_obj.object_list)

        # A customer can hold several MedRep seats at once. Prefer the exact
        # Assignment on the record; fall back to another active Assignment on
        # the same position only when that tenure has ended, so a successor
        # inherits the customers without rewriting history.
        option_ids = {option.id for option in assignment_options}
        position_to_option = {}
        for option in assignment_options:
            if option.position_id and option.position_id not in position_to_option:
                position_to_option[option.position_id] = option.id

        active_by_customer = defaultdict(set)
        for ta in TerritoryAssignment.objects.select_related("assignment").filter(
            customer__in=customers,
            status=1,
            terminated__isnull=True,
            deleted=False,
        ):
            if not ta.assignment_id:
                continue
            if ta.assignment_id in option_ids:
                active_by_customer[ta.customer_id].add(ta.assignment_id)
            else:
                inherited = position_to_option.get(ta.assignment.position_id)
                if inherited:
                    active_by_customer[ta.customer_id].add(inherited)

        current_regency_id = "__unset__"
        current_group = None
        for customer in customers:
            regency_id = customer.regency_id
            if regency_id != current_regency_id:
                current_group = {"regency": customer.regency, "rows": []}
                regency_groups.append(current_group)
                current_regency_id = regency_id
            current_group["rows"].append(
                {
                    "customer": customer,
                    "active_option_ids": active_by_customer.get(customer.id, set()),
                }
            )

    context = {
        "is_admin": is_full_access,
        "can_edit_effective_date": True,
        "page_title": "Territory Assignment",
        "card_title_text": "Sales Territory Assignment",
        "empty_message_text": "No customers found for your scope.",
        "save_url": reverse("sales:territory_assignment_assign_save"),
        "summary_url": reverse("sales:territory_assignment_summary"),
        "regency_ajax_url": reverse("sales:ajax_filter_territory_regencies"),
        "assignment_options": assignment_options,
        "medrep_options": medrep_options,
        "regency_groups": regency_groups,
        "province_options": province_options,
        "regency_options": regency_options,
        "custtype_options": custtype_options,
        "selected_province_ids": selected_province_ids,
        "selected_regency_ids": selected_regency_ids,
        "selected_custtype_ids": selected_custtype_ids,
        "selected_medrep_ids": selected_medrep_ids,
        "matrix_ready": matrix_ready,
        "total_customer_count": total_customer_count,
        "page_obj": page_obj,
        "base_query": base_query,
        "matrix_page_size": MATRIX_PAGE_SIZE,
        "today": now().date(),
        "show_sync_info": False,
    }
    return render(request, "sales/territory/territory_assignment.html", context)


def _territory_assignment_history_snapshot(obj):
    return {
        "assignment": obj.assignment,
        "customer": obj.customer,
        "status": obj.status,
        "effective": obj.effective,
        "terminated": obj.terminated,
        "remark": obj.remark,
    }


def _create_territory_assignment_history(request, obj, action, old_snapshot=None):
    old_snapshot = old_snapshot or {}
    TerritoryAssignmentHistory.objects.create(
        territory_assignment=obj,
        code=obj.code or "",
        name=obj.name or "",
        action=action,
        changed_by=request.user,
        old_assignment=old_snapshot.get("assignment"),
        new_assignment=obj.assignment,
        old_customer=old_snapshot.get("customer"),
        new_customer=obj.customer,
        old_status=old_snapshot.get("status"),
        new_status=obj.status,
        old_effective=old_snapshot.get("effective"),
        new_effective=obj.effective,
        old_terminated=old_snapshot.get("terminated"),
        new_terminated=obj.terminated,
        remark=old_snapshot.get("remark") or obj.remark,
    )


@login_required
@require_POST
def territory_assignment_assign_save(request):
    if not can_manage_territory_assignments(request.user):
        return HttpResponseForbidden(
            "Only Area Managers, Regional Managers, and administrators may manage assignments."
        )

    action = request.POST.get("action", "assign")
    assignment_id = request.POST.get("assignment_id")
    effective_date = parse_date(request.POST.get("effective"))
    raw_customer_ids = request.POST.getlist("customer_ids[]") or request.POST.getlist(
        "customer_ids"
    )

    if not raw_customer_ids:
        return HttpResponseBadRequest("Select at least one customer.")
    if not effective_date:
        return HttpResponseBadRequest("Effective date is required.")
    if action not in {"assign", "unassign"}:
        return HttpResponseBadRequest("Invalid action.")
    if not assignment_id:
        return HttpResponseBadRequest("Select a target MedRep.")

    try:
        customer_ids = [int(cid) for cid in raw_customer_ids]
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid customer id.")

    customers = list(Customer.nondeleted_objects.filter(id__in=customer_ids))
    if len(customers) != len(set(customer_ids)):
        return HttpResponseBadRequest("One or more customers were not found.")

    allowed_customer_ids = set(
        get_scoped_assignable_customers(request.user)
        .filter(id__in=customer_ids)
        .values_list("id", flat=True)
    )
    if len(allowed_customer_ids) != len(customers):
        outside_scope = next(
            customer for customer in customers if customer.id not in allowed_customer_ids
        )
        return HttpResponseForbidden(
            f"Customer {outside_scope.name or outside_scope.id} is outside your scope."
        )

    try:
        target_assignment = Assignment.objects.select_related(
            "employee", "position"
        ).get(
            id=assignment_id,
            status=1,
            terminated__isnull=True,
            deleted=False,
            position__deleted=False,
            position__status=1,
        )
    except Assignment.DoesNotExist:
        return HttpResponseBadRequest("Assignment (MedRep) not found or not active.")

    # Server-side guard: reject even if the picker/UI let this slip through.
    if not is_assignment_in_user_position_scope(request.user, target_assignment):
        return HttpResponseForbidden("You are not allowed to assign to this MedRep.")

    changed = 0
    skipped = 0
    changed_customer_ids = []

    # An assignment belongs to the MedRep seat (Position), while Assignment is
    # the employee's tenure in that seat. This lets a replacement inherit the
    # same territory without rewriting historical records.
    target_position_id = target_assignment.position_id

    # Unassign only the clicked customer + MedRep seat relationship. Other
    # overlapping MedRep assignments for the same customer remain active.
    if action == "unassign":
        with transaction.atomic():
            for customer in customers:
                current_records = list(
                    TerritoryAssignment.objects.select_for_update()
                    .select_related("assignment", "customer")
                    .filter(
                        customer=customer,
                        assignment__position_id=target_position_id,
                        status=1,
                        terminated__isnull=True,
                        deleted=False,
                    )
                    .order_by("-effective", "-id")
                )
                if not current_records:
                    skipped += 1
                    continue

                for current in current_records:
                    old_snapshot = _territory_assignment_history_snapshot(current)
                    current.status = 0
                    current.terminated = effective_date
                    current.save()
                    _create_territory_assignment_history(
                        request,
                        current,
                        TerritoryAssignmentHistory.ACTION_INACTIVE,
                        old_snapshot,
                    )
                changed += 1
                changed_customer_ids.append(customer.id)

        return JsonResponse(
            {
                "status": "updated" if changed else "no_change",
                "changed": changed,
                "skipped": skipped,
                "changed_customer_ids": changed_customer_ids,
            }
        )

    assignment_label = (
        target_assignment.name or target_assignment.shortname or target_assignment.code or str(target_assignment.id)
    )

    with transaction.atomic():
        for customer in customers:
            already_assigned = (
                TerritoryAssignment.objects.select_for_update()
                .filter(
                    customer=customer,
                    assignment__position_id=target_position_id,
                    status=1,
                    terminated__isnull=True,
                    deleted=False,
                )
                .exists()
            )

            if already_assigned:
                skipped += 1
                continue

            customer_code = customer.code or str(customer.id)
            new_record = TerritoryAssignment(
                code=f"{customer_code}-{target_assignment.id}"[:30],
                name=f"{customer.name} - {assignment_label}"[:255],
                initial=customer_code[:30],
                shortname=assignment_label[:30],
                assignment=target_assignment,
                customer=customer,
                effective=effective_date,
                terminated=None,
                status=1,
                deleted=False,
            )
            new_record.save()
            _create_territory_assignment_history(
                request, new_record, TerritoryAssignmentHistory.ACTION_CREATED
            )
            changed += 1
            changed_customer_ids.append(customer.id)

    return JsonResponse(
        {
            "status": "updated" if changed else "no_change",
            "changed": changed,
            "skipped": skipped,
            "changed_customer_ids": changed_customer_ids,
        }
    )
