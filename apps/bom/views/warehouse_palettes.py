from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.base.models.warehouse import WarehousePalette
from apps.bom.forms import WarehousePaletteForm


class WarehousePaletteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = WarehousePalette
    template_name = "bom/warehouse_palettes/list.html"
    context_object_name = "palettes"
    permission_required = "base.view_warehousepalette"

    def get_queryset(self):
        return WarehousePalette.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["can_hard_delete"] = user.is_superuser or user.has_perm(
            "base.hard_delete_warehousepalette"
        )
        return context


class WarehousePaletteCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = WarehousePalette
    form_class = WarehousePaletteForm
    template_name = "bom/warehouse_palettes/form.html"
    success_url = reverse_lazy("bom:warehouse_palettes:warehouse_palette_list")
    permission_required = "base.add_warehousepalette"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        return super().form_valid(form)


class WarehousePaletteUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = WarehousePalette
    form_class = WarehousePaletteForm
    template_name = "bom/warehouse_palettes/form.html"
    success_url = reverse_lazy("bom:warehouse_palettes:warehouse_palette_list")
    permission_required = "base.change_warehousepalette"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        return super().form_valid(form)


class WarehousePaletteDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = WarehousePalette
    success_url = reverse_lazy("bom:warehouse_palettes:warehouse_palette_list")
    permission_required = "base.delete_warehousepalette"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object._request_user = request.user
        from django.contrib import messages

        # Admin: hard delete (DB removal)
        if request.user.is_superuser or request.user.has_perm(
            "base.hard_delete_warehousepalette"
        ):
            messages.success(request, "Warehouse Palette berhasil dihapus.")
            return super().delete(request, *args, **kwargs)
        # Non-admin: soft delete (set deleted=True)
        self.object.delete()
        messages.success(request, "Warehouse Palette berhasil dihapus.")
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())
