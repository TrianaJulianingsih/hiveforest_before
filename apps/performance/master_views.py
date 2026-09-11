import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, CharField, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

from apps.base.datatable.views import AjaxDatatable
from apps.base.mixins import BatchFieldMixin
from apps.base.models.utils import get_nested_attr, toggle_status
from apps.base.views.generic_views import GenericListView, SoftDelete
from apps.performance.forms import PerformanceGroupForm, PerformanceModelForm
from apps.performance.models import PerformanceGroup, PerformanceModel

PH = "Use | splitter"
STATUS_OPTS = [
    {"value": "", "label": "All"},
    {"value": "Active", "label": "Active"},
    {"value": "Inactive", "label": "Inactive"},
    {"value": "__blank__", "label": "Not Set"},
]


# ── Performance Model ────────────────────────────────────────────────────────

class ModelThis:
    namespace = "performance"
    module = "model"
    model = PerformanceModel
    model_lower = "performancemodel"
    form_class = PerformanceModelForm
    form_template = "performance/model/performancemodel_form.html"
    url_list = "performance:model_list"
    url_edit = "performance:model_edit"
    columns = [
        {"index": 1, "name": "id", "label": "ID", "field": "id", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 2, "name": "code", "label": "Code", "field": "code", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 3, "name": "name", "label": "Name", "field": "name", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 4, "name": "initial", "label": "Initial", "field": "initial", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 5, "name": "shortname", "label": "Shortname", "field": "shortname", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 6, "name": "description", "label": "Description", "field": "description", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 7, "name": "status", "label": "Status", "field": "status_label", "type": "dropdown", "searchable": True, "lookup": "iexact", "options": STATUS_OPTS},
    ]


class ModelList(BatchFieldMixin, GenericListView):
    model = ModelThis.model
    columns = ModelThis.columns
    batch_fields = BatchFieldMixin.batch_fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "columns": self.columns,
            "vis_col": [col["label"] for col in self.columns],
            "page_title": "HiveForest | Performance Models",
            "card_title": "Performance Models List",
            "add_url": reverse_lazy("performance:model_create"),
            "custom_js": "custom/js/performancemodel_list.js",
            "table_id": "performancemodel_table",
            "tbody_id": "performancemodel-list-body",
            "batch_fields": self.batch_fields,
        })
        return context


class ModelAjax(AjaxDatatable):
    model = ModelThis.model
    default_order_column = 2
    default_order_dir = "asc"
    annotate = {
        "status_label": Case(
            When(status=1, then=Value("Active")),
            When(status=0, then=Value("Inactive")),
            default=Value(""),
            output_field=CharField(),
        )
    }

    def dispatch(self, request, *args, **kwargs):
        self.columns = ModelList.columns
        return super().dispatch(request, *args, **kwargs)

    def format_row(self, obj):
        row = {}
        for col in self.columns:
            field = col["field"]
            key = col.get("name", field)
            try:
                value = get_nested_attr(obj, field, "")
            except Exception:
                value = ""
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = date_format(value, "Y-m-d")
            elif hasattr(obj, f"get_{field}_display"):
                value = getattr(obj, f"get_{field}_display")()
            row[key] = str(value) if value is not None else ""
        return row


class ModelCreate(LoginRequiredMixin, CreateView):
    model = ModelThis.model
    form_class = ModelThis.form_class
    template_name = ModelThis.form_template
    login_url = reverse_lazy("login")

    def get_success_url(self):
        return reverse_lazy(ModelThis.url_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "add"
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Performance model created successfully."))
        return super().form_valid(form)


class ModelUpdate(LoginRequiredMixin, UpdateView):
    model = ModelThis.model
    form_class = ModelThis.form_class
    template_name = ModelThis.form_template
    login_url = reverse_lazy("login")
    success_url = reverse_lazy(ModelThis.url_list)

    def get_queryset(self):
        return ModelThis.model.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "edit"
        context["performancemodel"] = self.object
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Performance model saved successfully."))
        return super().form_valid(form)


class ModelSoftDelete(SoftDelete):
    model = ModelThis.model
    namespace = ModelThis.namespace
    url_list = ModelThis.url_list


@login_required
@csrf_exempt
def model_batch_update(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    field = request.POST.get("field")
    value = request.POST.get("value")
    ids = json.loads(request.POST.get("ids", "[]"))
    if not field or not value or not ids:
        return JsonResponse({"error": "Missing data"}, status=400)
    updated_count = 0
    if field == "status":
        status_map = {"Active": 1, "Inactive": 0}
        if value not in status_map:
            return JsonResponse({"error": "Invalid status"}, status=400)
        for obj_id in ids:
            try:
                obj = ModelThis.model.objects.get(id=obj_id, deleted=False)
                obj.status = status_map[value]
                obj.uat = timezone.now()
                obj.uby = request.user
                obj.save()
                updated_count += 1
            except ModelThis.model.DoesNotExist:
                continue
    return JsonResponse({"updated": updated_count})


@login_required
@require_POST
def model_change_status(request, pk):
    obj = get_object_or_404(ModelThis.model, pk=pk, deleted=False)
    _, label = toggle_status(obj, request.user)
    messages.success(request, f"Performance model '{obj.name or obj.code}' has been {label}.")
    return redirect(request.GET.get("next") or request.POST.get("next") or reverse(ModelThis.url_edit, args=[obj.pk]))


# ── Performance Group ────────────────────────────────────────────────────────

class GroupThis:
    namespace = "performance"
    module = "group"
    model = PerformanceGroup
    model_lower = "performancegroup"
    form_class = PerformanceGroupForm
    form_template = "performance/group/performancegroup_form.html"
    url_list = "performance:group_list"
    url_edit = "performance:group_edit"
    columns = [
        {"index": 1, "name": "id", "label": "ID", "field": "id", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 2, "name": "code", "label": "Code", "field": "code", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 3, "name": "name", "label": "Name", "field": "name", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 4, "name": "description", "label": "Description", "field": "description", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 5, "name": "bobot", "label": "Bobot (%)", "field": "bobot", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 6, "name": "performance_model__code", "label": "Model", "field": "performance_model__code", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 7, "name": "sort_order", "label": "Order", "field": "sort_order", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 8, "name": "initial", "label": "Initial", "field": "initial", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 9, "name": "shortname", "label": "Shortname", "field": "shortname", "type": "text", "placeholder": PH, "searchable": True, "lookup": "icontains"},
        {"index": 10, "name": "status", "label": "Status", "field": "status_label", "type": "dropdown", "searchable": True, "lookup": "iexact", "options": STATUS_OPTS},
    ]


class GroupList(BatchFieldMixin, GenericListView):
    model = GroupThis.model
    columns = GroupThis.columns
    batch_fields = BatchFieldMixin.batch_fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "columns": self.columns,
            "vis_col": [col["label"] for col in self.columns],
            "page_title": "HiveForest | Performance Groups",
            "card_title": "Performance Groups List",
            "add_url": reverse_lazy("performance:group_create"),
            "custom_js": "custom/js/performancegroup_list.js",
            "table_id": "performancegroup_table",
            "tbody_id": "performancegroup-list-body",
            "batch_fields": self.batch_fields,
        })
        return context


class GroupAjax(AjaxDatatable):
    model = GroupThis.model
    default_order_column = 2
    default_order_dir = "asc"
    select = ["performance_model"]
    annotate = {
        "status_label": Case(
            When(status=1, then=Value("Active")),
            When(status=0, then=Value("Inactive")),
            default=Value(""),
            output_field=CharField(),
        )
    }

    def dispatch(self, request, *args, **kwargs):
        self.columns = GroupList.columns
        return super().dispatch(request, *args, **kwargs)

    def format_row(self, obj):
        row = {}
        for col in self.columns:
            field = col["field"]
            key = col.get("name", field)
            try:
                value = get_nested_attr(obj, field, "")
            except Exception:
                value = ""
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = date_format(value, "Y-m-d")
            elif hasattr(obj, f"get_{field}_display"):
                value = getattr(obj, f"get_{field}_display")()
            row[key] = str(value) if value is not None else ""
        return row


class GroupCreate(LoginRequiredMixin, CreateView):
    model = GroupThis.model
    form_class = GroupThis.form_class
    template_name = GroupThis.form_template
    login_url = reverse_lazy("login")

    def get_success_url(self):
        return reverse_lazy(GroupThis.url_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "add"
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Performance group created successfully."))
        return super().form_valid(form)


class GroupUpdate(LoginRequiredMixin, UpdateView):
    model = GroupThis.model
    form_class = GroupThis.form_class
    template_name = GroupThis.form_template
    login_url = reverse_lazy("login")
    success_url = reverse_lazy(GroupThis.url_list)

    def get_queryset(self):
        return GroupThis.model.objects.filter(deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "edit"
        context["performancegroup"] = self.object
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Performance group saved successfully."))
        return super().form_valid(form)


class GroupSoftDelete(SoftDelete):
    model = GroupThis.model
    namespace = GroupThis.namespace
    url_list = GroupThis.url_list


@login_required
@csrf_exempt
def group_batch_update(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    field = request.POST.get("field")
    value = request.POST.get("value")
    ids = json.loads(request.POST.get("ids", "[]"))
    if not field or not value or not ids:
        return JsonResponse({"error": "Missing data"}, status=400)
    updated_count = 0
    if field == "status":
        status_map = {"Active": 1, "Inactive": 0}
        if value not in status_map:
            return JsonResponse({"error": "Invalid status"}, status=400)
        for obj_id in ids:
            try:
                obj = GroupThis.model.objects.get(id=obj_id, deleted=False)
                obj.status = status_map[value]
                obj.uat = timezone.now()
                obj.uby = request.user
                obj.save()
                updated_count += 1
            except GroupThis.model.DoesNotExist:
                continue
    return JsonResponse({"updated": updated_count})


@login_required
@require_POST
def group_change_status(request, pk):
    obj = get_object_or_404(GroupThis.model, pk=pk, deleted=False)
    _, label = toggle_status(obj, request.user)
    messages.success(request, f"Performance group '{obj.name or obj.code}' has been {label}.")
    return redirect(request.GET.get("next") or request.POST.get("next") or reverse(GroupThis.url_edit, args=[obj.pk]))
