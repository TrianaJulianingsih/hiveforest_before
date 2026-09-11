from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.sales.models.product import Product
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.sales.form.products_form import ProductsForm


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    template_name = "sales/product/list.html"
    context_object_name = "products"
    permission_required = "sales.view_product"

    def get_queryset(self):
        return Product.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["can_hard_delete"] = user.is_superuser or user.has_perm(
            "sales.hard_delete_product"
        )
        return context


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductsForm
    template_name = "sales/product/form.html"
    success_url = reverse_lazy("sales:product_list")
    permission_required = "sales.add_product"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductsForm
    template_name = "sales/product/form.html"
    success_url = reverse_lazy("sales:product_list")
    permission_required = "sales.change_product"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = "sales/product/confirm_delete.html"
    success_url = reverse_lazy("sales:product_list")
    permission_required = "sales.delete_product"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object._request_user = request.user
        if request.user.is_superuser or request.user.has_perm(
            "sales.hard_delete_product"
        ):
            messages.success(request, _("Product berhasil dihapus."))
            return super().delete(request, *args, **kwargs)
        self.object.delete()
        messages.success(request, _("Product berhasil dihapus."))
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())
