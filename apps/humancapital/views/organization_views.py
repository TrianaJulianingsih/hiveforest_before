from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, CharField
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import datetime
from apps.base.datatable.views import AjaxDatatable
from apps.base.models.utils import get_nested_attr, toggle_status
from apps.base.views.generic_views import GenericListView, SoftDelete
from apps.base.mixins import ModelMetadataMixin, BatchFieldMixin
from apps.humancapital.models.structure_models import Organization, OrganizationType
from apps.humancapital.forms.organization_forms import OrganizationForm
from apps.humancapital.views.mixins import HumanCapitalViewLogMixin
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: This                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: To set configuration used in this views          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: Jul/7-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class This:
    namespace = 'humancapital'
    module = 'organization'
    model = Organization
    related1 = OrganizationType
    model_lower = model.__name__.lower()
    related1_lower = related1.__name__.lower()
    form_template =f"{module}/{model_lower}_form.html"
    form_class = OrganizationForm
    url_edit = f"{namespace}:{model_lower}-edit"
    url_list = f"{namespace}:{model_lower}-list"
    related1_opt = [{'value': '', 'label': 'All'}] + [
        {'value': o.name, 'label': o.name} for o in related1.objects.filter(status=1)
        ] + [{'value': '__blank__', 'label': 'Not Set'}]
    parent_opt = [{'value': '', 'label': 'All'}] + [
        {'value': o.name, 'label': o.name} for o in model.objects.filter(status=1)
        ] + [{'value': '__blank__', 'label': 'Not Set'}]
    ph_1 = 'Use | splitter'
    columns = [
        {'index': 1, 'name': 'id', 'label': 'ID', 'field': 'id', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 2, 'name': 'code', 'label': 'Code', 'field': 'code', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 3, 'name': 'name', 'label': 'Name', 'field': 'name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 4, 'name': 'initial', 'label': 'Initial', 'field': 'initial', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 5, 'name': 'shortname', 'label': 'Shortname', 'field': 'shortname', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 6, 'name': 'type__name', 'label': 'Type', 'field': 'type__name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains', 'options': related1_opt},
        {'index': 7, 'name': 'parent__name', 'label': 'Parent', 'field': 'parent__name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains', 'options': parent_opt},
        {'index': 8, 'name': 'description', 'label': 'Description', 'field': 'description', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 9, 'name': 'effective', 'label': 'Effective', 'field': 'effective', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 10, 'name': 'terminated', 'label': 'Terminated', 'field': 'terminated', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 11, 'name': 'remark', 'label': 'Remark', 'field': 'remark', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 12, 'name': 'status', 'label': 'Status', 'field': 'status_label', 'type': 'dropdown','searchable': True, 'lookup': 'iexact', 'options': [
            {'value': '', 'label': 'All'},
            {'value': 'Active', 'label': 'Active'},
            {'value': 'Inactive', 'label': 'Inactive'},
            {'value': '__blank__', 'label': 'Not Set'}
        ]},
    ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: List                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: List View used by generic_list.html              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class List(HumanCapitalViewLogMixin, BatchFieldMixin, ModelMetadataMixin, GenericListView):
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
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Ajax(AjaxDatatable):
    model = This.model
    # default_order_column = 1  # index of 'name'
    default_order_column = 2  # index of 'code'
    default_order_dir = 'asc'
    annotate = {
        'status_label': Case(
            When(status=1, then=Value('Active')),
            When(status=0, then=Value('Inactive')),
            default=Value(''),
            output_field=CharField()
        )
    }

    def dispatch(self, request, *args, **kwargs):
        # Import columns from ListView to avoid duplication
        self.columns = List.columns
        return super().dispatch(request, *args, **kwargs)
    
    # May/23-2025 | STS
    def format_row(self, obj):
        row = {}
        for col in self.columns:
            field = col['field']
            key = col.get('name', field)  # fallback name
            #value = get_nested_attr(obj, field, '')
            # May/23-2025 | STS
            try:
                value = get_nested_attr(obj, field, '')
            except Exception:
                value = ''
            # Format dates
            if isinstance(value, (datetime.date, datetime.datetime)):
                value = date_format(value, 'Y-m-d')

            # Display human-readable choice (e.g., status) only for direct fields
            elif hasattr(obj, f"get_{field}_display"):
                value = getattr(obj, f"get_{field}_display")()

            #row[key] = value or ''
            if field == 'organization__type__name':
                row['type'] = str(value)
            else:
                row[key] = str(value) or ''
        return row

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: batch_update                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Batch update action in list view                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@csrf_exempt
def batch_update(request):
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        ids = json.loads(request.POST.get('ids', '[]'))

        if not field or not value or not ids:
            return JsonResponse({'error': 'Missing data'}, status=400)

        updated_count = 0

        if field == 'status':
            status_map = {'Active': 1, 'Inactive': 0}
            if value not in status_map:
                return JsonResponse({'error': 'Invalid status'}, status=400)

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

        SystemLogService.log(
            request=request,
            action=LogAction.BULK_UPDATE,
            module="Human Capital",
            feature=f"{This.model.__name__} Batch Update",
            description=f"Batch updated {field} to '{value}' for {len(ids)} {This.model.__name__} records.",
            log_type="SYSTEM"
        )
        return JsonResponse({'updated': updated_count})
    return JsonResponse({'error': 'Invalid method'}, status=405)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: change_status                                       ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Toggle status in edit view and list view         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def change_status(request, pk):
    obj = get_object_or_404(This.model, pk=pk)
    _, label = toggle_status(obj, request.user)

    messages.success(request, f"{This.model.__name__} '{obj.name}' has been {label}.")
    SystemLogService.log(
        request=request,
        action=LogAction.UPDATE,
        module="Human Capital",
        feature=f"{This.model.__name__} Status Toggle",
        description=f"Toggled status for {This.model.__name__} '{obj.name}' to {label}.",
        log_type="SYSTEM"
    )
    return redirect(
        request.GET.get('next') or 
        request.POST.get('next') or 
        reverse(This.url_edit, args=[obj.pk])
    )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: quick_add                                           ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Create an organization from the organogram popup ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
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

    type_obj = None
    type_id = _clean('type')
    if type_id:
        type_obj = OrganizationType.objects.filter(pk=type_id, status=1).first()

    parent_obj = None
    parent_id = _clean('parent')
    if parent_id:
        parent_obj = Organization.objects.filter(pk=parent_id, deleted=False).first()

    try:
        status_val = int(request.POST.get('status') or 1)
    except (TypeError, ValueError):
        status_val = 1

    org = Organization(
        code=code,
        name=name,
        initial=_clean('initial'),
        shortname=_clean('shortname'),
        type=type_obj,
        parent=parent_obj,
        effective=_to_date(request.POST.get('effective')),
        terminated=_to_date(request.POST.get('terminated')),
        description=_clean('description'),
        remark=_clean('remark'),
        status=status_val,
    )
    org.save(user=request.user)

    SystemLogService.log(
        request=request,
        action=LogAction.CREATE,
        module="Human Capital",
        feature=f"{This.model.__name__} Quick Add",
        description=f"Quick added {This.model.__name__} '{org.name}' via organogram modal.",
        log_type="SYSTEM"
    )
    return JsonResponse({
        'ok': True,
        'id': org.id,
        'name': org.name,
        'code': org.code,
        'parent_id': parent_obj.id if parent_obj else None,
        'parent_name': parent_obj.name if parent_obj else '',
    })

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Create                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to create a new record                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Create(HumanCapitalViewLogMixin, CreateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template

    def get_success_url(self):
        return reverse_lazy(This.url_list)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type_qs'] = This.related1.objects.filter(status=1)
        kwargs['parent_qs'] = This.model.objects.filter(status=1)
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'add'
        return context

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Update                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to update an existing record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Update(HumanCapitalViewLogMixin, UpdateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    success_url = reverse_lazy(This.url_list)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type_qs'] = This.related1.objects.filter(status=1)
        kwargs['parent_qs'] = This.model.objects.filter(status=1)
        kwargs['mode'] = 'edit'  # Pass mode to the form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'edit'
        context[This.model.__name__.lower()] = self.object
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        action = self.request.POST.get('action')

        if action == 'apply':
            # Stay on the same update view
            messages.success(self.request, "Changes applied successfully.")
            return redirect(reverse(This.url_edit, kwargs={'pk': self.object.pk}))
        elif action == 'clone':
            original_obj = self.object
            EXCLUDE_FIELDS = ['id', 'uby', 'uat', 'cby', 'cat']
            cloned_data = {
                col['field']: getattr(original_obj, col['field'])
                for col in This.columns
                if hasattr(original_obj, col['field']) and col['field'] not in EXCLUDE_FIELDS
            }
            cloned_obj = This.model.objects.create(**cloned_data)
            if 'name' in cloned_data:
                cloned_obj.name = f"Clone of {original_obj.name}"
                cloned_obj.save()

            messages.success(self.request, f"Clone of {original_obj.name} successfully.")
            return redirect(reverse(This.url_edit, kwargs={'pk': cloned_obj.pk}))

        messages.success(self.request, "Changes saved successfully.")
        return response

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Detail                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to see detail of an existing record         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Detail(HumanCapitalViewLogMixin, DetailView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type_qs'] = This.related1.objects.filter(status=1)
        kwargs['parent_qs'] = This.model.objects.filter(status=1)
        kwargs['mode'] = 'view'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'view'
        context[This.model.__name__.lower()] = self.object

        form = This.form_class(instance=self.object, type_qs=This.related1.objects.filter(status=1), parent_qs=This.model.objects.filter(status=1))
        for name, field in form.fields.items():
            field.widget.attrs['readonly'] = 'readonly'
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control-plaintext'
        form.fields['status'].disabled = True
        form.fields['type'].disabled = True
        form.fields['parent'].disabled = True
        
        context['form'] = form
        return context
     
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SoftDelete                                          ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: Delete View used to delete record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\organization_views.py       ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SoftDel(HumanCapitalViewLogMixin, SoftDelete):
    model = This.model
    namespace = This.namespace
    url_list = This.url_list
