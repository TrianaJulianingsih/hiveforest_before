from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseBadRequest

from apps.base.models.utils import soft_delete


class GenericListView(LoginRequiredMixin, TemplateView):
    template_name = "base/generic_list.html"
    login_url = reverse_lazy('login')  # or your actual login route

    columns = []
    batch_fields = []
    page_title = ''
    card_title = ''
    add_url = ''
    custom_js = ''
    table_id = ''
    tbody_id = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'columns': self.columns,
            'vis_col': [col['label'] for col in self.columns],
            'page_title': self.page_title,
            'card_title': self.card_title,
            'add_url': self.add_url,
            'custom_js': self.custom_js,
            'table_id': self.table_id,
            'tbody_id': self.tbody_id,
            'batch_fields': self.batch_fields,
        })
        return context

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SoftDelete                                          ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: Soft delete in edit view and list view           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\views\generic_views.py                    ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
class SoftDelete(LoginRequiredMixin, View):
    model = None  # Required
    namespace = None  # Required
    url_list = None  # Required
    cascade = []

    def post(self, request, pk):
        if not self.model or not self.namespace or not self.url_list:
            return HttpResponseBadRequest("SoftDelete not properly configured.")

        obj = get_object_or_404(self.model, pk=pk)
        deleted = soft_delete(obj, request.user, cascade=self.cascade if self.cascade else [])

        try:
            name = obj.person.name
        except AttributeError:
            name = str(obj)

        if not deleted:
            messages.info(request, f"{self.model.__name__} '{name}' is already deleted.")
        else:
            messages.success(request, f"{self.model.__name__} '{name}' and related data were deleted.")

        return redirect(reverse(self.url_list))
