from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, When, Value, CharField
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import datetime
from apps.base.models.people import Gender, Person
from apps.base.datatable.views import AjaxDatatable
from apps.base.models.utils import get_nested_attr, toggle_status, soft_delete
from apps.base.views.generic_views import GenericListView, SoftDelete
from apps.base.mixins import ModelMetadataMixin, BatchFieldMixin
from apps.humancapital.models.employee_models import Employee
from apps.humancapital.models.structure_models import Assignment, Position
from apps.humancapital.forms.employee_forms import EmployeePersonForm
from apps.humancapital.views.mixins import HumanCapitalViewLogMixin
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: This                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: To set configuration used in this views          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class This:
    namespace = 'humancapital'
    module = 'human_resource'
    model = Employee
    related1 = Gender
    model_lower = model.__name__.lower()
    related1_lower = related1.__name__.lower()
    form_template =f"{module}/{model_lower}_form.html"
    form_class = EmployeePersonForm
    url_edit = f"{namespace}:{model_lower}-edit"
    url_list = f"{namespace}:{model_lower}-list"
    cascade = 'person'
    # Include related model in batch_fields action, it extend the 'Status' batch_fields
    batch_fields = [
        {
            'name': related1_lower,
            'label': related1.__name__,
            'options': ['Male', 'Female', '__blank__']
        },
        {
            'name': 'employment_status',
            'label': 'Employment',
            'options': ['Regular', 'Probation']
        }
    ]
    ph_1 = 'Use | splitter'
    columns = [
        {'index': 1, 'name': 'id', 'label': 'ID', 'field': 'id', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 2, 'name': 'code', 'label': 'Code', 'field': 'code', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 3, 'name': 'name', 'label': 'Name', 'field': 'name', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 4, 'name': 'description', 'label': 'Description', 'field': 'description', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 5, 'name': f'{related1_lower}', 'label': related1.__name__, 'field': f'{cascade}__{related1_lower}__name', 'type': 'dropdown', 'searchable': True, 'lookup': 'iexact', 'options': [
            {'value': '', 'label': 'All'},
            {'value': 'Male', 'label': 'Male'},
            {'value': 'Female', 'label': 'Female'},
            {'value': '__blank__', 'label': 'Not Set'}
        ]},
        {'index': 6, 'name': 'dob', 'label': 'Birth Date', 'field': f'{cascade}__dob', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 7, 'name': 'national_id', 'label': 'National ID', 'field': f'{cascade}__national_id', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 8, 'name': 'tax_id', 'label': 'Tax ID', 'field': f'{cascade}__tax_id', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 9, 'name': 'hired', 'label': 'Hired', 'field': 'hired', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 10, 'name': 'terminated', 'label': 'Terminated', 'field': 'terminated', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 11, 'name': 'remark', 'label': 'Remark', 'field': 'remark', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 12, 'name': 'employment_status', 'label': 'Employment', 'field': 'employment_status_label', 'type': 'dropdown', 'searchable': True, 'lookup': 'iexact', 'options': [
            {'value': '', 'label': 'All'},
            {'value': 'Regular', 'label': 'Regular'},
            {'value': 'Probation', 'label': 'Probation'},
        ]},
        {'index': 13, 'name': 'status', 'label': 'Status', 'field': 'status_label', 'type': 'dropdown', 'lookup': 'iexact', 'options': [
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
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class List(HumanCapitalViewLogMixin, BatchFieldMixin, ModelMetadataMixin, GenericListView):
    namespace = This.namespace
    model = This.model
    batch_fields = BatchFieldMixin.batch_fields + This.batch_fields
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
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Ajax(AjaxDatatable):
    model = This.model
    default_order_column = 2  # index of 'name'
    select = [This.cascade]
    annotate = {
        'status_label': Case(
            When(status=1, then=Value('Active')),
            When(status=0, then=Value('Inactive')),
            default=Value(''),
            output_field=CharField()
        ),
        'employment_status_label': Case(
            When(employment_status='probation', then=Value('Probation')),
            default=Value('Regular'),
            output_field=CharField()
        ),
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
            row[key] = str(value) or ''
        return row
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: batch_update                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Batch update action in list view                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: ? by Setiadji                                    ║
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

        if field == f'{This.related1_lower}':
            gender_obj = This.related1.objects.filter(name__iexact=value).first()
            if not gender_obj:
                return JsonResponse({'error': f'Invalid {This.related1_lower}'}, status=400)

            for obj_id in ids:
                try:
                    obj = This.model.objects.select_related(This.cascade).get(id=obj_id)
                    related_obj = getattr(obj, This.cascade, None)
                    if related_obj:
                        related_obj.gender = gender_obj
                        related_obj.uat = timezone.now()
                        related_obj.uby = request.user
                        related_obj.save()
                        updated_count += 1
                except This.model.DoesNotExist:
                    continue

        elif field == 'employment_status':
            status_map = {'Regular': 'regular', 'Probation': 'probation'}
            if value not in status_map:
                return JsonResponse({'error': 'Invalid employment status'}, status=400)

            for obj_id in ids:
                try:
                    obj = This.model.objects.get(id=obj_id)
                    obj.employment_status = status_map[value]
                    obj.uat = timezone.now()
                    obj.uby = request.user
                    obj.save()
                    updated_count += 1
                except This.model.DoesNotExist:
                    continue

        elif field == 'status':
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
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def change_status(request, pk):
    obj = get_object_or_404(This.model, pk=pk)
    related_obj = getattr(obj, This.cascade, None)
    _, label = toggle_status(obj, request.user)

    messages.success(request, f"{This.model.__name__} '{related_obj.name}' has been {label}.")
    SystemLogService.log(
        request=request,
        action=LogAction.UPDATE,
        module="Human Capital",
        feature=f"{This.model.__name__} Status Toggle",
        description=f"Toggled status for {This.model.__name__} '{related_obj.name}' to {label}.",
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
# ║  Purpose: Create an employee from the organogram popup     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
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

    first_name = _clean('first_name')
    last_name = _clean('last_name')
    code = _clean('code')
    errors = {}
    if not first_name:
        errors['first_name'] = 'First name is required.'
    if not last_name:
        errors['last_name'] = 'Last name is required.'
    if not code:
        errors['code'] = 'Code is required.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)

    gender_obj = None
    gender_id = _clean('gender')
    if gender_id:
        gender_obj = Gender.objects.filter(pk=gender_id).first()

    try:
        status_val = int(request.POST.get('status') or 1)
    except (TypeError, ValueError):
        status_val = 1

    person = Person(
        first_name=first_name,
        middle_name=_clean('middle_name'),
        last_name=last_name,
        nickname=_clean('nickname'),
        initial=_clean('initial'),
        gender=gender_obj,
        dob=_to_date(request.POST.get('dob')),
        national_id=_clean('national_id'),
        tax_id=_clean('tax_id'),
    )

    employee = Employee(
        person=person,
        code=code,
        hired=_to_date(request.POST.get('hired')),
        terminated=_to_date(request.POST.get('terminated')),
        employment_status=(
            Employee.EMPLOYMENT_PROBATION
            if (_clean('employment_status') or '').lower() == Employee.EMPLOYMENT_PROBATION
            else Employee.EMPLOYMENT_REGULAR
        ),
        description=_clean('description'),
        remark=_clean('remark'),
        status=status_val,
    )

    display_name = person.name or f'{first_name} {last_name}'.strip()
    assigned = False
    assignment_pk = None
    position_pk = None
    position_id_raw = _clean('position_id')

    with transaction.atomic():
        person.save(user=request.user)
        employee.person = person
        employee.save(user=request.user)

        if position_id_raw:
            try:
                position_pk = int(position_id_raw)
            except (TypeError, ValueError):
                return JsonResponse({'ok': False, 'errors': {'position_id': 'Invalid position.'}}, status=400)

            from apps.humancapital.views.humancapital_views import position_is_vacant
            from apps.humancapital.views.assignment_views import (
                _close_assignment_row,
                _create_successor_assignment,
                _parse_modal_date,
            )

            assign_position = Position.objects.filter(pk=position_pk, deleted=False, status=1).first()
            if not assign_position:
                return JsonResponse({'ok': False, 'errors': {'position_id': 'Position not found.'}}, status=400)
            if not position_is_vacant(assign_position):
                return JsonResponse({'ok': False, 'errors': {'position_id': str(_('Position is not vacant.'))}}, status=400)

            effective, err = _parse_modal_date(request.POST.get('effective') or request.POST.get('hired'))
            if err or not effective:
                effective = timezone.localdate()

            old_assignment = None
            assignment_id_raw = _clean('assignment_id')
            if assignment_id_raw:
                try:
                    old_assignment = Assignment.objects.filter(
                        pk=int(assignment_id_raw),
                        position_id=assign_position.id,
                        deleted=False,
                    ).first()
                except (TypeError, ValueError):
                    old_assignment = None

            if old_assignment:
                new_start = effective
                if old_assignment.terminated is None:
                    close_date = new_start - datetime.timedelta(days=1)
                    if old_assignment.effective and close_date < old_assignment.effective:
                        close_date = new_start
                    _close_assignment_row(old_assignment, close_date, request.user)
                result_assignment = _create_successor_assignment(
                    old_assignment, employee, new_start, request.user
                )
            else:
                result_assignment = Assignment(
                    position=assign_position,
                    employee=employee,
                    title=assign_position.title,
                    effective=effective,
                    terminated=None,
                    status=1,
                    cby=request.user,
                    uby=request.user,
                )
                result_assignment.uat = timezone.now()
                result_assignment.save()

            assigned = True
            assignment_pk = result_assignment.pk
            position_pk = assign_position.id

    SystemLogService.log(
        request=request,
        action=LogAction.CREATE,
        module="Human Capital",
        feature=f"{This.model.__name__} Quick Add",
        description=f"Quick added {This.model.__name__} '{display_name}' via organogram modal.",
        log_type="SYSTEM"
    )
    return JsonResponse({
        'ok': True,
        'id': employee.id,
        'name': display_name,
        'code': employee.code,
        'assigned': assigned,
        'assignment_id': assignment_pk,
        'position_id': position_pk,
    })


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Create                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to create a new record                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: May/13-2025 by Setiadji                          ║
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
        kwargs[f'{This.related1_lower}_qs'] = Gender.objects.all()
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
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: May/13-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class Update(HumanCapitalViewLogMixin, UpdateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template

    def get_success_url(self):
        return reverse_lazy(This.url_list)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[f'{This.related1_lower}_qs'] = Gender.objects.all()
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
            related_obj = getattr(original_obj, This.cascade)
            # Clone the person
            cloned_related = related_obj.objects.create(
                first_name=f"Clone of {related_obj.first_name}",
                middle_name=related_obj.middle_name,
                last_name=related_obj.last_name,
                nickname=related_obj.nickname,
                initial=related_obj.initial,
                gender=related_obj.gender,
                dob=related_obj.dob,
                national_id=related_obj.national_id,
                tax_id=related_obj.tax_id,
            )
            # Clone the employee
            cloned_obj = This.model.objects.create(
                person=cloned_related,
                hired=original_obj.hired,
                terminated=original_obj.terminated,
                employment_status=original_obj.employment_status,
                description=original_obj.description,
                remark=original_obj.remark,
                status=original_obj.status,
            )

            messages.success(self.request, f"Cloned from '{related_obj.first_name}' successfully.")

            return redirect(reverse(This.url_edit, kwargs={'pk': cloned_obj.pk}))

        messages.success(self.request, "Changes saved successfully.")
        return response
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Detail                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to see detail of an existing record         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: May/13-2025                                      ║
# ║  Updated: May/23-2025                                      ║
# ╚════════════════════════════════════════════════════════════╝
class Detail(HumanCapitalViewLogMixin, DetailView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs[f'{This.related1_lower}_qs'] = Gender.objects.all()
        kwargs['mode'] = 'view'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'view'
        context[f'{This.model_lower}'] = self.object

        form = This.form_class(instance=self.object, gender_qs=Gender.objects.all())
        for name, field in form.fields.items():
            field.widget.attrs['readonly'] = 'readonly'
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control-plaintext'
        form.fields['status'].disabled = True
        form.fields[f'{This.related1_lower}'].disabled = True

        context['form'] = form
        return context
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SoftDelete                                          ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: Delete View used to delete record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employee_views.py           ║
# ║  Created: May/19-2025 by Setiadji                          ║
# ║  Updated: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class SoftDel(HumanCapitalViewLogMixin, SoftDelete):
    model = This.model
    namespace = This.namespace
    url_list = This.url_list
    cascade = This.cascade
