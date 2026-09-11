from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from django.utils.translation import get_language
from apps.sales.models.customer import Customer
from apps.base.utils.translation import get_module_translations


@login_required
def sub_distributor_list(request):
    data = (
        Customer.objects.filter(custtype_id=3, subdist="Y", deleted=False)
        .select_related("custtype", "province", "regency", "district", "station")
        .order_by("name")
    )

    current_lang = get_language()
    t = get_module_translations("sub_distributor", current_lang)

    return render(
        request,
        "sub_distributor/list.html",
        {
            "data": data,
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
        error_prefix = (
            "Error updating" if current_lang == "en" else "Kesalahan saat memperbarui"
        )
        return JsonResponse(
            {"success": False, "message": f"{error_prefix}: {str(e)}"}, status=500
        )
