from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Value, CharField, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from dal import autocomplete
import json
import datetime
from apps.base.datatable.views import AjaxDatatable
from apps.base.models.utils import get_nested_attr, toggle_status
from apps.base.views.generic_views import GenericListView, SoftDelete
from apps.base.mixins import ModelMetadataMixin, BatchFieldMixin
from apps.humancapital.forms.position_form import PositionForm
from apps.humancapital.models.employee import EmployeeTitle
from apps.humancapital.models.structure import Position, Organization


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: This                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: To set configuration used in this views          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class This:
    namespace = "humancapital"
    module = "organization"
    model = Position
    related1 = EmployeeTitle
    related2 = Organization
    model_lower = model.__name__.lower()
    related1_lower = related1.__name__.lower()
    related2_lower = related2.__name__.lower()
    form_template = f"{namespace}/{module}/{model_lower}_form.html"
    form_class = PositionForm
    url_edit = f"{namespace}:{model_lower}-edit"
    url_list = f"{namespace}:{model_lower}-list"
    related1_opt = (
        [{"value": "", "label": "All"}]
        + [
            {"value": o.name, "label": o.name}
            for o in related1.objects.filter(status=1)
        ]
        + [{"value": "__blank__", "label": "Not Set"}]
    )
    related2_opt = (
        [{"value": "", "label": "All"}]
        + [
            {"value": o.name, "label": o.name}
            for o in related2.objects.filter(status=1)
        ]
        + [{"value": "__blank__", "label": "Not Set"}]
    )
    parent_opt = (
        [{"value": "", "label": "All"}]
        + [{"value": o.name, "label": o.name} for o in model.objects.filter(status=1)]
        + [{"value": "__blank__", "label": "Not Set"}]
    )
    ph_1 = "Use | splitter"
    columns = [
        {
            "index": 1,
            "name": "id",
            "label": "ID",
            "field": "id",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 2,
            "name": "code",
            "label": "Code",
            "field": "code",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 3,
            "name": "name",
            "label": "Name",
            "field": "name",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 4,
            "name": "initial",
            "label": "Initial",
            "field": "initial",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 5,
            "name": "shortname",
            "label": "Shortname",
            "field": "shortname",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 6,
            "name": "level",
            "label": "Level",
            "field": "level",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 7,
            "name": "title__name",
            "label": "Title",
            "field": "title__name",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
            "options": related1_opt,
        },
        {
            "index": 8,
            "name": "parent__name",
            "label": "Parent",
            "field": "parent__name",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
            "options": parent_opt,
        },
        {
            "index": 9,
            "name": f"{related2_lower}__name",
            "label": related2.__name__,
            "field": f"{related2_lower}__name",
            "type": "text",
            "placeholder": ph_1,
            "lookup": "icontains",
            "options": related2_opt,
        },
        {
            "index": 10,
            "name": "description",
            "label": "Description",
            "field": "description",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 11,
            "name": "effective",
            "label": "Effective",
            "field": "effective",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 12,
            "name": "terminated",
            "label": "Terminated",
            "field": "terminated",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 13,
            "name": "remark",
            "label": "Remark",
            "field": "remark",
            "type": "text",
            "placeholder": ph_1,
            "searchable": True,
            "lookup": "icontains",
        },
        {
            "index": 14,
            "name": "status",
            "label": "Status",
            "field": "status_label",
            "type": "dropdown",
            "searchable": True,
            "lookup": "iexact",
            "options": [
                {"value": "", "label": "All"},
                {"value": "Active", "label": "Active"},
                {"value": "Inactive", "label": "Inactive"},
                {"value": "__blank__", "label": "Not Set"},
            ],
        },
    ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: List                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: List View used by generic_list.html              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class List(BatchFieldMixin, ModelMetadataMixin, GenericListView):
    namespace = This.namespace
    model = This.model
    batch_fields = BatchFieldMixin.batch_fields
    columns = This.columns

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["columns"] = self.columns
        return context


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Ajax                                                ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: To render data in list view                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Ajax(AjaxDatatable):
    http_method_names = ["get", "post"]
    model = This.model
    default_order_column = 1  # index of 'name'
    annotate = {
        "status_label": Case(
            When(status=1, then=Value("Active")),
            When(status=0, then=Value("Inactive")),
            default=Value(""),
            output_field=CharField(),
        )
    }

    def post(self, request, *args, **kwargs):
        request.GET = request.POST  # 🔥 mapping POST → GET
        return self.get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.columns = List.columns
        return super().dispatch(request, *args, **kwargs)

    def format_row(self, obj):
        row = {}
        for col in self.columns:
            field = col["field"]
            key = col.get("name", field)  # fallback name
            # value = get_nested_attr(obj, field, '')
            # May/23-2025 | STS
            try:
                value = get_nested_attr(obj, field, "")
            except Exception:
                value = ""
            # Format dates
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = date_format(value, "Y-m-d")

            # Display human-readable choice (e.g., status) only for direct fields
            elif hasattr(obj, f"get_{field}_display"):
                value = getattr(obj, f"get_{field}_display")()

            # row[key] = value or ''
            if field == "employee__title__name":
                row["title"] = str(value)
            else:
                row[key] = str(value) or ""
        return row


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: batch_update                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Batch update action in list view                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@csrf_exempt
def batch_update(request):
    if request.method == "POST":
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
                    obj = This.model.objects.get(id=obj_id)
                    obj.status = status_map[value]
                    obj.uat = timezone.now()
                    obj.uby = request.user
                    obj.save()
                    updated_count += 1
                except This.model.DoesNotExist:
                    continue

        return JsonResponse({"updated": updated_count})
    return JsonResponse({"error": "Invalid method"}, status=405)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: change_status                                       ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Toggle status in edit view and list view         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def change_status(request, pk):
    obj = get_object_or_404(This.model, pk=pk)
    _, label = toggle_status(obj, request.user)

    messages.success(request, f"{This.model.__name__} '{obj.name}' has been {label}.")
    return redirect(
        request.GET.get("next")
        or request.POST.get("next")
        or reverse(This.url_edit, args=[obj.pk])
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: quick_add                                           ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Create a position from the organogram popup      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Returns: JSON so the modal can save without a full reload ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def quick_add(request):
    def _clean(key):
        return (request.POST.get(key) or '').strip()

    def _to_date(value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None

    name = _clean('name')
    code = _clean('code')
    errors = {}
    if not name:
        errors['name'] = 'Name is required.'
    if not code:
        errors['code'] = 'Code is required.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)

    title_obj = None
    title_id = _clean('title')
    if title_id:
        title_obj = EmployeeTitle.objects.filter(pk=title_id, status=1).first()

    parent_obj = None
    parent_id = _clean('parent')
    if parent_id:
        parent_obj = Position.objects.filter(pk=parent_id, deleted=False).first()

    org_obj = None
    org_id = _clean('organization')
    if org_id:
        org_obj = Organization.objects.filter(pk=org_id, deleted=False).first()

    level = None
    level_raw = _clean('level')
    if level_raw:
        try:
            level = int(level_raw)
        except (TypeError, ValueError):
            errors['level'] = 'Level must be a number.'
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

    try:
        status_val = int(request.POST.get('status') or 1)
    except (TypeError, ValueError):
        status_val = 1

    position = Position(
        code=code,
        name=name,
        initial=_clean('initial'),
        shortname=_clean('shortname'),
        level=level,
        title=title_obj,
        parent=parent_obj,
        organization=org_obj,
        effective=_to_date(request.POST.get('effective')),
        terminated=_to_date(request.POST.get('terminated')),
        description=_clean('description'),
        remark=_clean('remark'),
        status=status_val,
    )
    position.save(user=request.user)

    return JsonResponse({
        'ok': True,
        'id': position.id,
        'name': position.name,
        'code': position.code,
        'parent_id': parent_obj.id if parent_obj else None,
        'parent_name': parent_obj.name if parent_obj else '',
        'organization_id': org_obj.id if org_obj else None,
        'organization_name': org_obj.name if org_obj else '',
    })


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: quick_rename                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Rename a position from the organogram card       ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def quick_rename(request, pk):
    name = (request.POST.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'errors': {'name': 'Name is required.'}}, status=400)
    position = Position.objects.filter(pk=pk, deleted=False).first()
    if not position:
        return JsonResponse({'ok': False, 'error': 'Position not found.'}, status=404)
    position.name = name
    position.save(user=request.user)
    return JsonResponse({'ok': True, 'id': position.id, 'name': position.name})


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Create                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to create a new record                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Create(CreateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template

    def get_success_url(self):
        return reverse_lazy(This.url_list)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["title_qs"] = This.related1.objects.filter(status=1)
        kwargs["parent_qs"] = This.model.objects.filter(status=1)
        kwargs[f"{This.related2_lower}_qs"] = This.related2.objects.filter(status=1)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "add"
        return context


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Update                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to update an existing record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Update(UpdateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    success_url = reverse_lazy(This.url_list)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["title_qs"] = This.related1.objects.filter(status=1)
        kwargs["parent_qs"] = This.model.objects.filter(status=1)
        kwargs[f"{This.related2_lower}_qs"] = This.related2.objects.filter(status=1)
        kwargs["mode"] = "edit"  # Pass mode to the form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "edit"
        context[This.model.__name__.lower()] = self.object
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        action = self.request.POST.get("action")

        if action == "apply":
            # Stay on the same update view
            messages.success(self.request, "Changes applied successfully.")
            return redirect(reverse(This.url_edit, kwargs={"pk": self.object.pk}))
        elif action == "clone":
            original_obj = self.object
            EXCLUDE_FIELDS = ["id", "uby", "uat", "cby", "cat"]
            cloned_data = {
                col["field"]: getattr(original_obj, col["field"])
                for col in This.columns
                if hasattr(original_obj, col["field"])
                and col["field"] not in EXCLUDE_FIELDS
            }
            cloned_obj = This.model.objects.create(**cloned_data)
            if "name" in cloned_data:
                cloned_obj.name = f"Clone of {original_obj.name}"
                cloned_obj.save()

            messages.success(
                self.request, f"Clone of {original_obj.name} successfully."
            )
            return redirect(reverse(This.url_edit, kwargs={"pk": cloned_obj.pk}))

        messages.success(self.request, "Changes saved successfully.")
        return response


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Detail                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to see detail of an existing record         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Detail(DetailView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["title_qs"] = This.related1.objects.filter(status=1)
        kwargs["parent_qs"] = This.model.objects.filter(status=1)
        kwargs[f"{This.related2_lower}_qs"] = This.related2.objects.filter(status=1)
        kwargs["mode"] = "view"
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "view"
        context[This.model.__name__.lower()] = self.object

        form = This.form_class(
            instance=self.object,
            title_qs=This.related1.objects.filter(status=1),
            parent_qs=This.model.objects.filter(status=1),
            organization_qs=This.related2.objects.filter(status=1),
        )
        for name, field in form.fields.items():
            field.widget.attrs["readonly"] = "readonly"
            field.widget.attrs["class"] = (
                field.widget.attrs.get("class", "") + " form-control-plaintext"
            )
        form.fields["status"].disabled = True
        form.fields["title"].disabled = True
        form.fields["parent"].disabled = True
        form.fields["organization"].disabled = True

        context["form"] = form
        return context


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SoftDelete                                          ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: Delete View used to delete record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\position_view.py            ║
# ║  Created: May/20-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SoftDel(SoftDelete):
    model = This.model
    namespace = This.namespace
    url_list = This.url_list


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: VacantPositionAutocomplete                          ║
# ║  Purpose: Select2 — vacant positions only (for relocation) ║
# ╚════════════════════════════════════════════════════════════╝
class VacantPositionAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        from apps.humancapital.views.humancapital_view import vacant_positions_queryset
        from django.utils.translation import gettext as _

        if not self.request.user.is_authenticated:
            return Position.objects.none()

        exclude_raw = self.forwarded.get('exclude_position') or self.request.GET.get('exclude_position')
        exclude_id = None
        if exclude_raw not in (None, ''):
            try:
                exclude_id = int(exclude_raw)
            except (ValueError, TypeError):
                exclude_id = None

        qs = vacant_positions_queryset(exclude_position_id=exclude_id)
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q)
                | Q(code__icontains=self.q)
                | Q(organization__name__icontains=self.q)
                | Q(organization__shortname__icontains=self.q)
            )
        return qs

    def get_result_label(self, result):
        from django.utils.translation import gettext as _
        org = result.organization
        area = (org.shortname or org.name or '').strip() if org else ''
        vacant = _('Vacant')
        if area:
            return f'{result.name} — {area} ({vacant})'
        return f'{result.name} ({vacant})'
