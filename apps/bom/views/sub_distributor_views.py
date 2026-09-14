import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Count, Q
from django.utils.translation import get_language
from apps.sales.models.customer_models import Customer
from apps.base.utils.translation import get_module_translations
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@login_required
def sub_distributor_list(request):
    data = (
        Customer.objects.filter(custtype_id=3, subdist="Y", deleted=False)
        .select_related("custtype", "province", "regency", "district", "station")
        .order_by("name")
    )

    current_lang = get_language()
    t = get_module_translations("sub_distributor", current_lang)

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Sub-Distributor List",
        description="User viewed the Sub-Distributor list.",
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return render(
        request,
        "sub_distributor/list.html",
        {
            "data": data,
            "t": t,
        },
    )


@login_required
def sub_distributor_dashboard(request):
    qs = (
        Customer.objects.filter(custtype_id=3, subdist="Y", deleted=False)
        .select_related("custtype", "province", "regency", "district", "station")
        .order_by("name")
    )

    total_count = qs.count()
    active_count = qs.filter(status=1).count()
    inactive_count = qs.filter(status=0).count()
    active_percentage = (
        round((active_count / total_count * 100), 1) if total_count > 0 else 0
    )
    inactive_percentage = (
        round((inactive_count / total_count * 100), 1) if total_count > 0 else 0
    )

    station_stats = list(
        qs.filter(station__isnull=False)
        .values("station__id", "station__name")
        .annotate(
            total=Count("id"),
            active=Count("id", filter=Q(status=1)),
            inactive=Count("id", filter=Q(status=0)),
        )
        .order_by("-total")
    )
    for s in station_stats:
        s["station_id"] = s.get("station__id")
        s["station_name"] = s.get("station__name")
    station_count = len(station_stats)

    province_stats = list(
        qs.filter(province__isnull=False)
        .values("province__id", "province__name")
        .annotate(
            total=Count("id"),
            active=Count("id", filter=Q(status=1)),
            inactive=Count("id", filter=Q(status=0)),
        )
        .order_by("-total")
    )
    for p in province_stats:
        p["province_id"] = p.get("province__id")
        p["province_name"] = p.get("province__name")
    province_count = len(province_stats)

    # Interactive map coordinates dataset
    map_points = []
    for c in qs:
        if c.latitude is not None and c.longitude is not None:
            try:
                lat = float(c.latitude)
                lng = float(c.longitude)
                if -15.0 <= lat <= 12.0 and 90.0 <= lng <= 145.0:
                    map_points.append(
                        {
                            "id": c.id,
                            "name": c.name,
                            "code": c.code or "-",
                            "shortname": c.shortname or "-",
                            "station": c.station.name if c.station else "-",
                            "province": c.province.name if c.province else "-",
                            "regency": c.regency.name if c.regency else "-",
                            "district": c.district.name if c.district else "-",
                            "street": c.street or "",
                            "lat": lat,
                            "lng": lng,
                            "status": "Active" if c.status else "Inactive",
                            "status_code": 1 if c.status else 0,
                        }
                    )
            except (ValueError, TypeError):
                pass

    top_stations = station_stats[:8]
    station_chart_labels = [s["station_name"] for s in top_stations]
    station_chart_active = [s["active"] for s in top_stations]
    station_chart_inactive = [s["inactive"] for s in top_stations]

    top_provinces = province_stats[:6]
    province_chart_labels = [p["province_name"] for p in top_provinces]
    province_chart_data = [p["total"] for p in top_provinces]

    metrics = {
        "total": total_count,
        "active": active_count,
        "inactive": inactive_count,
        "active_percentage": active_percentage,
        "inactive_percentage": inactive_percentage,
        "stations": station_count,
        "provinces": province_count,
        "mapped_count": len(map_points),
        "unmapped_count": total_count - len(map_points),
    }

    current_lang = get_language()
    t = get_module_translations("sub_distributor", current_lang)

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Sub-Distributor Dashboard",
        description="User viewed the interactive Sub-Distributor Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return render(
        request,
        "sub_distributor/dashboard.html",
        {
            "data": qs,
            "metrics": metrics,
            "station_stats": station_stats,
            "province_stats": province_stats,
            "map_points_json": json.dumps(map_points),
            "station_chart_labels_json": json.dumps(station_chart_labels),
            "station_chart_active_json": json.dumps(station_chart_active),
            "station_chart_inactive_json": json.dumps(station_chart_inactive),
            "province_chart_labels_json": json.dumps(province_chart_labels),
            "province_chart_data_json": json.dumps(province_chart_data),
            "t": t,
        },
    )


@login_required
def sub_distributor_add(request):
    search_query = request.GET.get("search", "")
    customers = []

    if search_query:
        customers = (
            Customer.objects.filter(custtype_id=3, deleted=False)
            .filter(models.Q(subdist="N") | models.Q(subdist__isnull=True))
            .filter(
                models.Q(name__icontains=search_query)
                | models.Q(code__icontains=search_query)
                | models.Q(shortname__icontains=search_query)
            )
            .select_related("province", "regency", "district", "station")
            .order_by("name")[:20]
        )

    current_lang = get_language()
    t = get_module_translations("sub_distributor", current_lang)

    context = {
        "search_query": search_query,
        "customers": customers,
        "t": t,
    }

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Sub-Distributor Add Form",
        description=f"User searched for customers to add as sub-distributor with query '{search_query}'." if search_query else "User viewed the Sub-Distributor Add page.",
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return render(request, "sub_distributor/add.html", context)


@login_required
@require_POST
def sub_distributor_save(request):
    try:
        current_lang = get_language()
        t = get_module_translations("sub_distributor", current_lang)

        customer_id = request.POST.get("customer_id")

        if not customer_id:
            error_msg = (
                "Customer ID is required."
                if current_lang == "en"
                else "Customer ID wajib diisi."
            )
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        obj = get_object_or_404(Customer, id=customer_id, custtype_id=3)

        obj.subdist = "Y"
        obj.save(update_fields=["subdist"])

        SystemLogService.log(
            request=request,
            action=LogAction.UPDATE,
            module="BOM",
            feature="Sub-Distributor Maintenance",
            obj=obj,
            description=f"User added customer '{obj.name}' as sub-distributor.",
            status="SUCCESS",
            log_type="SYSTEM",
        )

        if current_lang == "id":
            success_msg = f'"{obj.name}" telah ditambahkan sebagai Sub-Distributor.'
        else:
            success_msg = f'"{obj.name}" has been added as Sub-Distributor.'

        return JsonResponse(
            {
                "success": True,
                "message": success_msg,
                "redirect_url": "/bom/customer-maintenance/sub-distributor/",
            }
        )

    except Exception as e:
        SystemLogService.error(
            request=request,
            module="BOM",
            feature="Sub-Distributor Maintenance",
            error=e,
            description="Failed to add customer as sub-distributor.",
        )
        error_prefix = "Error" if current_lang == "en" else "Kesalahan"
        return JsonResponse(
            {"success": False, "message": f"{error_prefix}: {str(e)}"}, status=500
        )


@login_required
@require_POST
def sub_distributor_update_subdist(request, id):
    try:
        current_lang = get_language()

        obj = get_object_or_404(Customer, id=id, custtype_id=3)

        subdist_value = request.POST.get("subdist")

        if subdist_value not in ["Y", "N"]:
            error_msg = (
                "Invalid value. Must be Y or N."
                if current_lang == "en"
                else "Nilai tidak valid. Harus Y atau N."
            )
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        obj.subdist = subdist_value
        obj.save(update_fields=["subdist"])

        SystemLogService.log(
            request=request,
            action=LogAction.UPDATE,
            module="BOM",
            feature="Sub-Distributor Maintenance",
            obj=obj,
            description=f"User updated sub-distributor status for customer '{obj.name}' to '{subdist_value}'.",
            status="SUCCESS",
            log_type="SYSTEM",
        )

        if current_lang == "id":
            status_text = "Ya" if subdist_value == "Y" else "Tidak"
            success_msg = f"Status Sub-Distributor diperbarui menjadi {status_text}."
        else:
            status_text = "Yes" if subdist_value == "Y" else "No"
            success_msg = f"Sub-distributor status updated to {status_text}."

        return JsonResponse(
            {"success": True, "message": success_msg, "subdist": subdist_value}
        )

    except Exception as e:
        SystemLogService.error(
            request=request,
            module="BOM",
            feature="Sub-Distributor Maintenance",
            error=e,
            description="Failed to update sub-distributor status.",
        )
        error_prefix = (
            "Error updating" if current_lang == "en" else "Kesalahan saat memperbarui"
        )
        return JsonResponse(
            {"success": False, "message": f"{error_prefix}: {str(e)}"}, status=500
        )
