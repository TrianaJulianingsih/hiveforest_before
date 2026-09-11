import json

from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.supplychain.models.distributions import StDistDaily
from apps.sales.models.sales import RawAPLSO, RawMUSO
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.sales.form.stock_daily_distributor_form import StockDailyDistributorForm

from django.http import HttpResponseRedirect, JsonResponse
from django.views import View
from django.middleware.csrf import get_token

from django.shortcuts import render


class StockDailyDistributorListView(
    LoginRequiredMixin, PermissionRequiredMixin, ListView
):
    # model = StDistDaily
    template_name = "sales/stock_daily_distributor/list.html"
    # context_object_name = "stdistdaily"
    permission_required = "supplychain.view_stdistdaily"

    def get_queryset(self):
        return StDistDaily.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        last_sync = (
            StDistDaily.objects.order_by("-cat").values_list("cat", flat=True).first()
        )

        context["last_sync"] = last_sync
        return context

    # def get_queryset(self):
    #     return StDistDaily.objects.filter(deleted=False)

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user
    #     context["can_hard_delete"] = user.is_superuser or user.has_perm(
    #         "supplychain.hard_delete_stdistdaily"
    #     )
    #     return context


class StockDailyDistributorDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "supplychain.view_stdistdaily"

    def get(self, request):
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 25))
        search = request.GET.get("search[value]", "")

        user = request.user
        can_edit = user.has_perm("supplychain.change_stdistdaily")
        can_delete = user.has_perm("supplychain.delete_stdistdaily")
        can_soft_delete = user.has_perm("supplychain.soft_delete")

        csrf_token = get_token(request)

        qs_base = StDistDaily.objects.filter(deleted=False)
        qs = qs_base.select_related("branch", "distributor").order_by("cat")

        if search:
            qs = qs.filter(nm_prod__icontains=search)

        total_all = qs_base.count()
        total_filtered = qs.count()
        data = qs[start : start + length]

        rows = []
        for p in data:
            # action_html = ""
            # if can_edit:
            #     action_html += f"""
            #         <a href="/sales/stock-daily-distributor/{p.id}/edit/"
            #            class="btn btn-sm btn-warning text-dark">
            #            <i class="fa fa-edit"></i> Edit
            #         </a>
            #     """
            # if can_delete:
            #     if not p.deleted:
            #         action_html += f"""
            #             <form method="post"
            #                   action="/sales/stock-daily-distributor/{p.id}/delete/"
            #                   style="display:inline"
            #                   class="delete-form">
            #                 <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
            #                 <button type="button"
            #                         class="btn btn-sm btn-danger btn-delete"
            #                         data-name="{p}">
            #                     <i class="fa fa-trash"></i> Delete
            #                 </button>
            #             </form>
            #         """
            #     else:
            #         if can_soft_delete:
            #             action_html += f"""
            #                 <form method="post"
            #                       action="/sales/stock-daily-distributor/{p.id}/delete/"
            #                       style="display:inline">
            #                     <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
            #                     <button type="submit"
            #                             class="btn btn-sm btn-danger">
            #                         <i class="fa fa-trash"></i> Hard Delete
            #                     </button>
            #                 </form>
            #             """
            #         else:
            #             action_html += """
            #                 <span class="badge badge-secondary">
            #                     <i class="fa fa-trash"></i> Deleted
            #                 </span>
            #             """

            rows.append(
                {
                    "name": p.name or "-",
                    "nm_prod": p.nm_prod or "-",
                    "lot": p.lot or "-",
                    "ed": p.ed or "-",
                    "hna": str(p.hna) if p.hna else "0",
                    "periode": p.periode or "-",
                    "branch": p.branch.name if p.branch else "-",
                    "distributor": p.distributor.name if p.distributor else "-",
                    # "action": action_html
                }
            )

        return JsonResponse(
            {
                "draw": draw,
                "recordsTotal": total_all,
                "recordsFiltered": total_filtered,
                "data": rows,
            }
        )


class StockDailyDistributorCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = StDistDaily
    form_class = StockDailyDistributorForm
    template_name = "sales/stock_daily_distributor/form.html"
    success_url = reverse_lazy("sales:stock_daily_distributor_list")
    permission_required = "supplychain.add_stdistdaily"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        messages.success(self.request, _("Data berhasil ditambahkan."))
        return super().form_valid(form)


class StockDailyDistributorUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = StDistDaily
    form_class = StockDailyDistributorForm
    template_name = "sales/stock_daily_distributor/form.html"
    success_url = reverse_lazy("sales:stock_daily_distributor_list")
    permission_required = "supplychain.change_stdistdaily"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        messages.success(self.request, _("Data berhasil diperbarui."))
        return super().form_valid(form)


class StockDailyDistributorDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = StDistDaily
    template_name = "sales/stock_daily_distributor/confirm_delete.html"
    success_url = reverse_lazy("sales:stock_daily_distributor_list")
    permission_required = "supplychain.delete_stdistdaily"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object._request_user = request.user
        if request.user.is_superuser or request.user.has_perm(
            "supplychain.hard_delete_stdistdaily"
        ):
            messages.success(request, _("Stock Daily Distributor berhasil dihapus."))
            return super().delete(request, *args, **kwargs)
        self.object.delete()
        messages.success(request, _("Stock Daily Distributor berhasil dihapus."))

        return HttpResponseRedirect(self.get_success_url())


class RawMupSoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "sales/raw_mup_so/list.html"
    permission_required = "sales.view_rawmuso"

    def get_queryset(self):
        return RawMUSO.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        columns = [
            {"data": "no_order"},
            {"data": "name"},
            {"data": "nm_prod"},
            {"data": "whse"},
            {"data": "nodokjdi"},
            {"data": "hrdok"},
            {"data": "banyak"},
            {"data": "hna"},
            {"data": "thna"},
            {"data": "harga"},
            {"data": "tharga"},
            {"data": "almtlang"},
        ]

        context.update(
            {
                "translation_key": "raw_mup_so",
                "page_title": "Raw MUP-SO",
                "table_id": "raw_mup_so_table",
                "ajax_url": reverse("sales:raw_mup_so_data"),
                "columns_json": json.dumps(columns),
            }
        )

        last_sync = (
            RawMUSO.objects.order_by("-cat").values_list("cat", flat=True).first()
        )
        context["last_sync"] = last_sync

        return context


class RawMupSoDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "sales.view_rawmuso"

    def get(self, request):
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 25))
        search = request.GET.get("search[value]", "")

        user = request.user
        can_edit = user.has_perm("sales.change_rawmuso")
        can_delete = user.has_perm("sales.delete_rawmuso")
        can_soft_delete = user.has_perm("sales.soft_delete")

        csrf_token = get_token(request)

        qs_base = RawMUSO.objects.filter(deleted=False)
        qs = qs_base.order_by("cat")

        if search:
            qs = qs.filter(nmprod__icontains=search)

        total_all = qs_base.count()
        total_filtered = qs.count()
        data = qs[start : start + length]

        rows = []
        for p in data:
            rows.append(
                {
                    "no_order": p.no_order or "-",
                    "name": p.name or "-",
                    "nm_prod": p.nmprod or "-",
                    "whse": p.whse or "-",
                    "nodokjdi": p.nodokjdi or "-",
                    "hrdok": p.hrdok or "-",
                    "banyak": str(p.banyak) if p.banyak else "0",
                    "hna": str(p.hna) if p.hna else "0",
                    "thna": str(p.thna) if p.thna else "0",
                    "harga": str(p.harga) if p.harga else "0",
                    "tharga": str(p.tharga) if p.tharga else "0",
                    "almtlang": (p.nmlang or "") + " - " + (p.almtlang or ""),
                }
            )

        return JsonResponse(
            {
                "draw": draw,
                "recordsTotal": total_all,
                "recordsFiltered": total_filtered,
                "data": rows,
            }
        )


class RawAplSoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "sales/raw_apl_so/list.html"
    permission_required = "sales.view_rawaplso"

    def get_queryset(self):
        return RawAPLSO.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        columns = [
            {"data": "name"},
            {"data": "kode_produk"},
            {"data": "produk"},
            {"data": "outlet"},
            {"data": "alamat_outlet"},
            {"data": "qty"},
            {"data": "faktor_kali"},
            {"data": "hjp"},
            {"data": "hna"},
            {"data": "harga"},
            {"data": "whse"},
            {"data": "tanggal_expired"},
        ]

        context.update(
            {
                "translation_key": "raw_apl_so",
                "page_title": "Raw APL-SO",
                "table_id": "raw_apl_so_table",
                "ajax_url": reverse("sales:raw_apl_so_data"),
                "columns_json": json.dumps(columns),
            }
        )

        last_sync = (
            RawAPLSO.objects.order_by("-cat").values_list("cat", flat=True).first()
        )
        context["last_sync"] = last_sync

        return context


class RawAplSoDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "sales.view_rawaplso"

    def get(self, request):
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 25))
        search = request.GET.get("search[value]", "")

        user = request.user
        can_edit = user.has_perm("sales.change_rawaplso")
        can_delete = user.has_perm("sales.delete_rawaplso")
        can_soft_delete = user.has_perm("sales.soft_delete")

        csrf_token = get_token(request)

        qs_base = RawAPLSO.objects.filter(deleted=False)
        qs = qs_base.order_by("cat")

        if search:
            qs = qs.filter(nmprod__icontains=search)

        total_all = qs_base.count()
        total_filtered = qs.count()
        data = qs[start : start + length]

        rows = []
        for p in data:
            rows.append(
                {
                    "name": p.no_order or "-",
                    "kode_produk": p.kode_produk or "-",
                    "produk": p.produk or "-",
                    "outlet": p.outlet or "-",
                    "alamat_outlet": p.alamat_outlet or "-",
                    "qty": str(p.qty) if p.qty else "0",
                    "faktor_kali": str(p.faktor_kali) if p.faktor_kali else "0",
                    "hjp": str(p.hjp) if p.hjp else "0",
                    "hna": str(p.hna) if p.hna else "0",
                    "harga": str(p.harga) if p.harga else "0",
                    "whse": p.whse or "-",
                    "tanggal_expired": p.tanggal_expired or "-",
                }
            )

        return JsonResponse(
            {
                "draw": draw,
                "recordsTotal": total_all,
                "recordsFiltered": total_filtered,
                "data": rows,
            }
        )
