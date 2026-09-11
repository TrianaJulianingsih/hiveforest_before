import csv
from urllib.parse import unquote

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import capfirst
from openpyxl import Workbook

from apps.base.models import Province
from apps.crm.models import (
    Doctor,
    DoctorEducation,
    DoctorPlace,
    DoctorSpeciality,
    Hospital,
)

EXPORT_HEADERS = [
    "No", "Name", "Status", "License", "Start Year", "Start Month",
    "Education", "Place of Practice",
]

HOSPITAL_EXPORT_HEADERS = ["No", "Name", "Type", "Class", "Regency", "Province"]

PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 500, 1000]
DEFAULT_PAGE_SIZE = 10

# Hospital List has ~3k rows (vs. Doctor List's ~280k), so an "all" option here is
# safe to actually render - it would not be for the Doctor List/Analytics tables.
HOSPITAL_PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 500, "all"]


def _crm_breadcrumbs(request):
    # "dashboard" is just a URL namespace prefix for these views, not a real
    # page - skip it so the breadcrumb goes Crm > Hcp instead of
    # Crm > Dashboard > Hcp.
    segments = [s for s in request.path.strip("/").split("/") if s != "dashboard"]
    crumbs = []
    url = ""
    for segment in segments:
        if segment.isdigit():
            continue
        url += f"/{segment}"
        crumbs.append({"name": capfirst(unquote(segment.replace("-", " "))), "url": url})
    return crumbs


def _filter_options(request):
    # Cascading facets: each facet's option list is scoped by the OTHER facet's
    # current selection (but never its own), so picking a Specialization narrows
    # the Province list to provinces that actually have doctors with it, and
    # vice versa - rather than always showing every value regardless of context.
    selected_specialities = request.GET.getlist("specialization")
    selected_provinces = request.GET.getlist("province")

    specialities_qs = DoctorSpeciality.objects.exclude(speciality_desc="")
    if selected_provinces:
        specialities_qs = specialities_qs.filter(doctor__doctorplace__province__name__in=selected_provinces)
    specialities = list(
        specialities_qs.values_list("speciality_desc", flat=True).distinct().order_by("speciality_desc")
    )

    provinces_qs = Province.objects.all()
    if selected_specialities:
        provinces_qs = provinces_qs.filter(
            doctorplace__doctor__doctorspeciality__speciality_desc__in=selected_specialities
        )
    provinces = list(provinces_qs.values_list("name", flat=True).distinct().order_by("name"))

    return specialities, provinces


def _chart_filter_options():
    places = list(
        DoctorPlace.objects.exclude(place_desc="")
        .values_list("place_desc", flat=True)
        .distinct()
        .order_by("place_desc")
    )
    education = list(
        DoctorEducation.objects.exclude(institution__isnull=True)
        .exclude(institution="")
        .values_list("institution", flat=True)
        .distinct()
        .order_by("institution")
    )
    return places, education


def _filtered_doctors(request, include_search=True, search_lookup="icontains"):
    doctors = Doctor.nondeleted_objects.order_by("name")

    query = request.GET.get("q", "").strip()
    if include_search and query:
        doctors = doctors.filter(**{f"name__{search_lookup}": query})

    selected_specialities = request.GET.getlist("specialization")
    if selected_specialities:
        doctors = doctors.filter(doctorspeciality__speciality_desc__in=selected_specialities)

    selected_provinces = request.GET.getlist("province")
    if selected_provinces:
        doctors = doctors.filter(doctorplace__province__name__in=selected_provinces)

    if selected_specialities or selected_provinces:
        doctors = doctors.distinct()

    return doctors, query, selected_specialities, selected_provinces


def _page_size(request, options=PAGE_SIZE_OPTIONS):
    raw = request.GET.get("page_size", DEFAULT_PAGE_SIZE)
    if raw == "all" and "all" in options:
        return "all"
    try:
        page_size = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return page_size if page_size in options else DEFAULT_PAGE_SIZE


def _paginate_doctors(request):
    doctors, query, selected_specialities, selected_provinces = _filtered_doctors(request)
    doctors = doctors.select_related("person").prefetch_related(
        "doctoreducation_set", "doctorplace_set", "doctorspeciality_set"
    )

    page_size = _page_size(request)
    paginator = Paginator(doctors, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    elided_page_range = list(
        paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    )
    return page_obj, paginator, elided_page_range, query, selected_specialities, selected_provinces, page_size


def _filter_context(request):
    (
        page_obj,
        paginator,
        elided_page_range,
        query,
        selected_specialities,
        selected_provinces,
        page_size,
    ) = _paginate_doctors(request)
    specialities, provinces = _filter_options(request)

    return {
        "breadcrumbs": _crm_breadcrumbs(request),
        "doctors": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "elided_page_range": elided_page_range,
        "query": query,
        "specialities": specialities,
        "provinces": provinces,
        "selected_specialities": selected_specialities,
        "selected_provinces": selected_provinces,
        "selected_filter_count": len(selected_specialities) + len(selected_provinces),
        "page_size": page_size,
        "page_size_options": PAGE_SIZE_OPTIONS,
    }


@login_required
def hcp_filter_options(request):
    # Backs the filter panel's live narrowing: called as the user checks/unchecks
    # boxes (before hitting Confirm), so it reads specialization/province straight
    # off the in-progress panel state passed as query params, not the page's own
    # applied filters - same _filter_options() used for the real page render.
    specialities, provinces = _filter_options(request)
    return JsonResponse({"specialities": specialities, "provinces": provinces})


@login_required
def hcp_list(request):
    context = _filter_context(request)
    context["title"] = "Healthcare Professionals"
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "html_dashboard/hcp_table.html", context)
    return render(request, "html_dashboard/hcp_list.html", context)


@login_required
def hcp_profile_dashboard(request):
    doctor = Doctor.nondeleted_objects.order_by("name").first()
    return redirect("crm:hcp_profile", pk=doctor.pk)


@login_required
def hcp_profile(request, pk):
    doctor = get_object_or_404(Doctor.nondeleted_objects.select_related("person"), pk=pk)
    context = {
        "breadcrumbs": _crm_breadcrumbs(request),
        "doctor": doctor,
        "places": doctor.doctorplace_set.all(),
        "educations": doctor.doctoreducation_set.all(),
        "specialities": doctor.doctorspeciality_set.all(),
        "title": doctor.name,
    }
    return render(request, "html_dashboard/hcp_profile.html", context)


def _hospital_filter_options(request):
    # Cascading facets, same idea as _filter_options(): each facet's option list
    # is scoped by every OTHER selected facet (never its own), so e.g. picking a
    # Type narrows Class/Regency/Province to what actually occurs among
    # hospitals of that type, instead of always listing every value.
    selected_types = request.GET.getlist("type")
    selected_classes = request.GET.getlist("class")
    selected_regencies = request.GET.getlist("regency")
    selected_provinces = request.GET.getlist("province")

    def scoped(exclude):
        qs = Hospital.nondeleted_objects.all()
        if exclude != "type" and selected_types:
            qs = qs.filter(hospitaltype__name__in=selected_types)
        if exclude != "class" and selected_classes:
            qs = qs.filter(hospitalclass__name__in=selected_classes)
        if exclude != "regency" and selected_regencies:
            qs = qs.filter(regency__name__in=selected_regencies)
        if exclude != "province" and selected_provinces:
            qs = qs.filter(province__name__in=selected_provinces)
        return qs

    types = list(
        scoped("type").exclude(hospitaltype__isnull=True).exclude(hospitaltype__name="")
        .values_list("hospitaltype__name", flat=True).distinct().order_by("hospitaltype__name")
    )
    classes = list(
        scoped("class").exclude(hospitalclass__isnull=True).exclude(hospitalclass__name="")
        .values_list("hospitalclass__name", flat=True).distinct().order_by("hospitalclass__name")
    )
    regencies = list(
        scoped("regency").exclude(regency__isnull=True)
        .values_list("regency__name", flat=True).distinct().order_by("regency__name")
    )
    provinces = list(
        scoped("province").exclude(province__isnull=True)
        .values_list("province__name", flat=True).distinct().order_by("province__name")
    )
    return types, classes, regencies, provinces


def _filtered_hospitals(request):
    hospitals = Hospital.nondeleted_objects.select_related(
        "hospitaltype", "hospitalclass", "province", "regency"
    ).order_by("name")

    query = request.GET.get("q", "").strip()
    if query:
        hospitals = hospitals.filter(name__icontains=query)

    selected_types = request.GET.getlist("type")
    if selected_types:
        hospitals = hospitals.filter(hospitaltype__name__in=selected_types)

    selected_classes = request.GET.getlist("class")
    if selected_classes:
        hospitals = hospitals.filter(hospitalclass__name__in=selected_classes)

    selected_regencies = request.GET.getlist("regency")
    if selected_regencies:
        hospitals = hospitals.filter(regency__name__in=selected_regencies)

    selected_provinces = request.GET.getlist("province")
    if selected_provinces:
        hospitals = hospitals.filter(province__name__in=selected_provinces)

    if selected_types or selected_classes or selected_regencies or selected_provinces:
        hospitals = hospitals.distinct()

    return hospitals, query, selected_types, selected_classes, selected_regencies, selected_provinces


def _paginate_hospitals(request):
    (
        hospitals,
        query,
        selected_types,
        selected_classes,
        selected_regencies,
        selected_provinces,
    ) = _filtered_hospitals(request)

    page_size = _page_size(request, options=HOSPITAL_PAGE_SIZE_OPTIONS)
    if page_size == "all":
        # Paginator.count would otherwise re-run this same COUNT(*) query itself
        # the moment get_page() touches num_pages - seed its cache with the value
        # we already have to avoid counting the queryset twice.
        total_count = hospitals.count()
        paginator = Paginator(hospitals, max(total_count, 1))
        paginator.__dict__["count"] = total_count
    else:
        paginator = Paginator(hospitals, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    elided_page_range = list(
        paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    )
    return (
        page_obj,
        paginator,
        elided_page_range,
        query,
        selected_types,
        selected_classes,
        selected_regencies,
        selected_provinces,
        page_size,
    )


def _hospital_filter_context(request):
    (
        page_obj,
        paginator,
        elided_page_range,
        query,
        selected_types,
        selected_classes,
        selected_regencies,
        selected_provinces,
        page_size,
    ) = _paginate_hospitals(request)
    types, classes, regencies, provinces = _hospital_filter_options(request)

    return {
        "breadcrumbs": _crm_breadcrumbs(request),
        "hospitals": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "elided_page_range": elided_page_range,
        "query": query,
        "types": types,
        "classes": classes,
        "regencies": regencies,
        "provinces": provinces,
        "selected_types": selected_types,
        "selected_classes": selected_classes,
        "selected_regencies": selected_regencies,
        "selected_provinces": selected_provinces,
        "selected_filter_count": (
            len(selected_types) + len(selected_classes) + len(selected_regencies) + len(selected_provinces)
        ),
        "page_size": page_size,
        "page_size_options": HOSPITAL_PAGE_SIZE_OPTIONS,
        "title": "Hospitals",
    }


@login_required
def hospital_list(request):
    context = _hospital_filter_context(request)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "html_dashboard/hospital_table.html", context)
    return render(request, "html_dashboard/hospital_list.html", context)


@login_required
def hospital_filter_options(request):
    # Same live-narrowing purpose as hcp_filter_options() - read the filter
    # panel's in-progress (not yet confirmed) checkbox state from query params.
    types, classes, regencies, provinces = _hospital_filter_options(request)
    return JsonResponse({"types": types, "classes": classes, "regencies": regencies, "provinces": provinces})


@login_required
def hospital_suggest(request):
    hospitals, query, *_ = _filtered_hospitals(request)

    suggestions = []
    if query:
        seen = set()
        for hospital in hospitals.order_by("name")[:30]:
            name = hospital.display_name
            if name not in seen:
                seen.add(name)
                suggestions.append(name)
            if len(suggestions) >= 10:
                break
    return JsonResponse({"suggestions": suggestions})


@login_required
def hospital_profile_dashboard(request):
    hospital = Hospital.nondeleted_objects.order_by("name").first()
    return redirect("crm:hospital_profile", pk=hospital.pk)


@login_required
def hospital_profile(request, pk):
    hospital = get_object_or_404(
        Hospital.nondeleted_objects.select_related(
            "village", "district", "regency", "province", "ownership", "hospitaltype", "hospitalclass"
        ),
        pk=pk,
    )
    doctors = Doctor.nondeleted_objects.none()
    if hospital.customer_id:
        doctors = (
            Doctor.nondeleted_objects.filter(doctorplace__customer_id=hospital.customer_id)
            .distinct()
            .order_by("name")
        )
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        back_url = next_url
    else:
        back_url = reverse("crm:hospital_list")
    context = {
        "breadcrumbs": _crm_breadcrumbs(request),
        "hospital": hospital,
        "back_url": back_url,
        "doctors": doctors,
        "beds": hospital.hospitalbed_set.all(),
        "services": hospital.hospitalservice_set.all(),
        "professionals": hospital.hospitalprofessional_set.all(),
        "title": hospital.display_name,
    }
    return render(request, "html_dashboard/hospital_profile.html", context)


@login_required
def hcp_suggest(request):
    # istartswith (not the list's icontains) so this can use the crm_doctor_active_name_idx
    # b-tree index - a leading-wildcard icontains scan across all ~280k doctors was the
    # actual cause of suggestions feeling slow/unresponsive while typing.
    doctors, query, *_ = _filtered_doctors(request, search_lookup="istartswith")

    suggestions = []
    if query:
        suggestions = list(
            doctors.values_list("name", flat=True).distinct().order_by("name")[:10]
        )
    return JsonResponse({"suggestions": suggestions})


@login_required
def analytics_dashboard(request):
    context = _filter_context(request)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Table pagination only ever changes which 10 rows are shown - the
        # map/charts above it don't depend on the page number, so skip
        # recomputing them entirely for this request.
        return render(request, "html_dashboard/analytics_table.html", context)

    # Stats/map/charts are scoped to Filter (specialization/province) only - the
    # search box lives above the table now and should only narrow the table,
    # not the aggregate numbers above it.
    doctors, *_ = _filtered_doctors(request, include_search=False)

    # One conditional-aggregation query instead of three separate .count() scans
    # over the ~280k-row Doctor table.
    doctor_counts = doctors.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=1)),
        inactive=Count("id", filter=Q(status=0)),
    )
    total = doctor_counts["total"]
    active = doctor_counts["active"]
    inactive = doctor_counts["inactive"]

    # Likewise, one query for both DoctorPlace-derived counts instead of two.
    place_counts = DoctorPlace.objects.filter(doctor__in=doctors).aggregate(
        facilities=Count("place_desc", filter=~Q(place_desc=""), distinct=True),
        regions=Count("province", distinct=True),
    )
    facilities = place_counts["facilities"] or 0
    regions = place_counts["regions"] or 0

    # Each chart also has its own dedicated filter, independent of the global
    # Filter button above - it only narrows what that one chart displays.
    selected_map_provinces = request.GET.getlist("map_province")
    selected_chart_places = request.GET.getlist("chart_places")
    selected_chart_specialities = request.GET.getlist("chart_specialities")
    selected_chart_education = request.GET.getlist("chart_education")
    place_options, education_options = _chart_filter_options()

    province_rows = (
        DoctorPlace.objects.filter(doctor__in=doctors, province__isnull=False)
        .values("province__name", "province__latitude", "province__longitude")
        .annotate(doctor_count=Count("doctor", distinct=True))
        .order_by("-doctor_count")
    )
    if selected_map_provinces:
        province_rows = province_rows.filter(province__name__in=selected_map_provinces)
    province_data = [
        {
            "name": row["province__name"],
            "lat": float(row["province__latitude"]),
            "lng": float(row["province__longitude"]),
            "count": row["doctor_count"],
        }
        for row in province_rows
    ]

    places_qs = (
        DoctorPlace.objects.filter(doctor__in=doctors)
        .exclude(place_desc="")
        .values("place_desc")
        .annotate(doctor_count=Count("doctor", distinct=True))
        .order_by("-doctor_count")
    )
    places_qs = places_qs.filter(place_desc__in=selected_chart_places) if selected_chart_places else places_qs[:8]
    top_places = [
        {"label": row["place_desc"], "count": row["doctor_count"]} for row in places_qs
    ]

    specialities_qs = (
        DoctorSpeciality.objects.filter(doctor__in=doctors)
        .exclude(speciality_desc="")
        .values("speciality_desc")
        .annotate(doctor_count=Count("doctor", distinct=True))
        .order_by("-doctor_count")
    )
    specialities_qs = (
        specialities_qs.filter(speciality_desc__in=selected_chart_specialities)
        if selected_chart_specialities
        else specialities_qs[:8]
    )
    top_specialities = [
        {"label": row["speciality_desc"], "count": row["doctor_count"]}
        for row in specialities_qs
    ]

    education_qs = (
        DoctorEducation.objects.filter(doctor__in=doctors)
        .exclude(institution__isnull=True)
        .exclude(institution="")
        .values("institution")
        .annotate(doctor_count=Count("doctor", distinct=True))
        .order_by("-doctor_count")
    )
    education_qs = (
        education_qs.filter(institution__in=selected_chart_education)
        if selected_chart_education
        else education_qs[:8]
    )
    top_education = [
        {"label": row["institution"], "count": row["doctor_count"]}
        for row in education_qs
    ]

    context.update({
        "total_count": total,
        "active_count": active,
        "inactive_count": inactive,
        "facility_count": facilities,
        "region_count": regions,
        "province_data": province_data,
        "top_places": top_places,
        "top_specialities": top_specialities,
        "top_education": top_education,
        "place_options": place_options,
        "education_options": education_options,
        "selected_map_provinces": selected_map_provinces,
        "selected_chart_places": selected_chart_places,
        "selected_chart_specialities": selected_chart_specialities,
        "selected_chart_education": selected_chart_education,
        "title": "Doctor Dashboard",
    })
    return render(request, "html_dashboard/analytics_dashboard.html", context)


def _related_first_map(queryset, value_field):
    """Build {doctor_id: value} using the first related row per doctor (by pk),
    matching the semantics of RelatedManager.first(). These related tables are
    small (a few thousand rows) compared to Doctor (280k+), so it's cheaper to
    load them once into a dict than to prefetch per-row across the whole export.
    """
    mapping = {}
    for doctor_id, value in queryset.order_by("doctor_id", "pk").values_list("doctor_id", value_field):
        if doctor_id not in mapping:
            mapping[doctor_id] = value
    return mapping


def _export_rows(request):
    doctors, *_ = _filtered_doctors(request)

    education_map = _related_first_map(
        DoctorEducation.objects.exclude(institution__isnull=True).exclude(institution=""),
        "institution",
    )
    place_map = _related_first_map(
        DoctorPlace.objects.exclude(place_desc=""),
        "place_desc",
    )

    rows = doctors.values_list("id", "name", "status", "license", "start_year", "start_month")
    for index, (doctor_id, name, status, license_no, start_year, start_month) in enumerate(
        rows.iterator(chunk_size=5000), start=1
    ):
        yield [
            index,
            name,
            "Active" if status == 1 else "Inactive",
            license_no or "-",
            start_year if start_year is not None else "-",
            start_month if start_month is not None else "-",
            education_map.get(doctor_id, "-"),
            place_map.get(doctor_id, "-"),
        ]


@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="healthcare_professionals.csv"'

    writer = csv.writer(response)
    writer.writerow(EXPORT_HEADERS)
    for row in _export_rows(request):
        writer.writerow(row)
    return response


@login_required
def export_excel(request):
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Healthcare Professionals")
    sheet.append(EXPORT_HEADERS)
    for row in _export_rows(request):
        sheet.append(row)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="healthcare_professionals.xlsx"'
    workbook.save(response)
    return response


def _hospital_export_rows(request):
    hospitals, *_ = _filtered_hospitals(request)
    for index, hospital in enumerate(hospitals.iterator(chunk_size=1000), start=1):
        yield [
            index,
            hospital.display_name,
            hospital.hospitaltype.name if hospital.hospitaltype_id else "-",
            hospital.hospitalclass.name if hospital.hospitalclass_id else "-",
            hospital.regency.name if hospital.regency_id else (hospital.raw_city or "-"),
            hospital.province.name if hospital.province_id else (hospital.raw_province or "-"),
        ]


@login_required
def hospital_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="hospitals.csv"'

    writer = csv.writer(response)
    writer.writerow(HOSPITAL_EXPORT_HEADERS)
    for row in _hospital_export_rows(request):
        writer.writerow(row)
    return response


@login_required
def hospital_export_excel(request):
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Hospitals")
    sheet.append(HOSPITAL_EXPORT_HEADERS)
    for row in _hospital_export_rows(request):
        sheet.append(row)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="hospitals.xlsx"'
    workbook.save(response)
    return response
