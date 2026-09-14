from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.supplychain.models.distributions_models import Branch
from apps.supplychain.forms.branch_forms import BranchForm
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction
from django.http import HttpResponseRedirect


class BranchListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Branch
    template_name = "branch/list.html"
    context_object_name = "branches"
    permission_required = "supplychain.view_branch"

    def get(self, request, *args, **kwargs):
        SystemLogService.log(
            request=request,
            action=LogAction.READ,
            module="SupplyChain",
            feature="Branch List",
            description="User accessed Branch List view.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Branch.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["can_hard_delete"] = user.is_superuser or user.has_perm(
            "supplychain.hard_delete_branch"
        )
        return context


class BranchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = "branch/form.html"
    success_url = reverse_lazy("supplychain:branch_list")
    permission_required = "supplychain.add_branch"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        SystemLogService.log(
            request=self.request,
            action=LogAction.CREATE,
            module="SupplyChain",
            feature="Branch Create",
            description=f"User created Branch: {obj.name} ({obj.code}).",
            obj=obj,
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return super().form_valid(form)


class BranchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = "branch/form.html"
    success_url = reverse_lazy("supplychain:branch_list")
    permission_required = "supplychain.change_branch"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj._request_user = self.request.user
        obj.save()
        SystemLogService.log(
            request=self.request,
            action=LogAction.UPDATE,
            module="SupplyChain",
            feature="Branch Update",
            description=f"User updated Branch: {obj.name} ({obj.code}).",
            obj=obj,
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return super().form_valid(form)


class BranchDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Branch
    success_url = reverse_lazy("supplychain:branch_list")
    permission_required = "supplychain.delete_branch"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object._request_user = request.user
        branch_name = self.object.name
        branch_code = self.object.code
        if request.user.is_superuser or request.user.has_perm(
            "supplychain.hard_delete_branch"
        ):
            messages.success(request, _("Branch berhasil dihapus."))
            response = super().delete(request, *args, **kwargs)
        else:
            self.object.delete()
            messages.success(request, _("Branch berhasil dihapus."))
            response = HttpResponseRedirect(self.get_success_url())

        SystemLogService.log(
            request=request,
            action=LogAction.DELETE,
            module="SupplyChain",
            feature="Branch Delete",
            description=f"User deleted Branch: {branch_name} ({branch_code}).",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return response
