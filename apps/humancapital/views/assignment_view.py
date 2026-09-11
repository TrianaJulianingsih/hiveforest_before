from django.db.models import Case, When, Value, CharField, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.translation import gettext as _
from dal import autocomplete
import datetime, json
from apps.base.models.utils import get_nested_attr, toggle_status
from apps.base.views.generic_views import GenericListView, SoftDelete
from apps.base.datatable.views import AjaxDatatable
from apps.base.mixins import BatchFieldMixin, ModelMetadataMixin
from apps.humancapital.models.employee import Employee, EmployeeTitle
from apps.humancapital.models.structure import Assignment, Position
from apps.humancapital.forms.assignment_form import EmployeeAssignmentForm

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: This                                                ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: To set configuration used in this views          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class This:
    namespace = 'humancapital'
    module = 'organization'
    model = Assignment
    related1 = Employee
    related2 = Position
    related3 = EmployeeTitle
    model_lower = model.__name__.lower()
    related1_lower = related1.__name__.lower()
    related2_lower = related2.__name__.lower()
    related3_lower = related3.__name__.lower()
    form_template =f"{namespace}/{module}/{model_lower}_form.html"
    form_class = EmployeeAssignmentForm
    url_edit = f"{namespace}:{model_lower}-edit"
    url_list = f"{namespace}:{model_lower}-list"
    related1_opt = [{'value': '', 'label': 'All'}] + [
        {'value': o['name'], 'label': o['name']}
        for o in related1.objects.filter(status=1).values('name')
        ] + [{'value': '__blank__', 'label': 'Not Set'}]
    related2_opt = [{'value': '', 'label': 'All'}] + [
        {'value': o.name, 'label': o.name} for o in related2.objects.filter(status=1)
        ] + [{'value': '__blank__', 'label': 'Not Set'}]
    related3_opt = [{'value': '', 'label': 'All'}] + [
        {'value': o.name, 'label': o.name} for o in related3.objects.filter(status=1)
        ] + [{'value': '__blank__', 'label': 'Not Set'}]
    ph_1 = 'Use | splitter'
    columns = [
        {'index': 1, 'name': 'id', 'label': 'ID', 'field': 'id', 'type': 'text', 'placeholder': ph_1, 'searchable': True, 'lookup': 'icontains'},
        {'index': 2, 'name': 'code', 'label': 'Code', 'field': 'code', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 3, 'name': 'name', 'label': 'Name', 'field': 'name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 4, 'name': 'initial', 'label': 'Initial', 'field': 'initial', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 5, 'name': 'shortname', 'label': 'Shortname', 'field': 'shortname', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 6, 'name': f'{related1_lower}__name', 'label': related1.__name__, 'field': f'{related1_lower}__name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains', 'options': related1_opt},
        {'index': 7, 'name': f'{related2_lower}__name', 'label': related2.__name__, 'field': f'{related2_lower}__name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains', 'options': related2_opt},
        {'index': 8, 'name': 'title__name', 'label': 'Title', 'field': 'title__name', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains', 'options': related3_opt},
        {'index': 9, 'name': 'description', 'label': 'Description', 'field': 'description', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 10, 'name': 'effective', 'label': 'Effective', 'field': 'effective', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 11, 'name': 'terminated', 'label': 'Terminated', 'field': 'terminated', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 12, 'name': 'remark', 'label': 'Remark', 'field': 'remark', 'type': 'text', 'placeholder': ph_1,'searchable': True, 'lookup': 'icontains'},
        {'index': 13, 'name': 'status', 'label': 'Status', 'field': 'status_label', 'type': 'dropdown', 'searchable': True, 'lookup': 'iexact', 'options': [
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
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
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
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class Ajax(AjaxDatatable):
    model = This.model
    select = [This.related1_lower, This.related2_lower]
    default_order_column = 2  # index of 'name'
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
            if field == 'employee__title__name':
                row['title'] = str(value)
            else:
                row[key] = str(value) or ''
        return row

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: batch_update                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Batch update action in list view                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
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

        return JsonResponse({'updated': updated_count})
    return JsonResponse({'error': 'Invalid method'}, status=405)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: change_status                                       ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Toggle status in edit view and list view         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: May/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def change_status(request, pk):
    obj = get_object_or_404(This.model, pk=pk)
    _, label = toggle_status(obj, request.user)

    messages.success(request, f"{This.model.__name__} '{obj.name}' has been {label}.")
    return redirect(
        request.GET.get('next') or 
        request.POST.get('next') or 
        reverse(This.url_edit, args=[obj.pk])
    )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: quick_assign                                        ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Organogram inline — vacant / dates / assign via   ║
# ║           AJAX POST. Assigning a new employee closes the    ║
# ║           current row and creates a new assignment row.     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: Jun/5-2026 by Copilot                            ║
# ╚════════════════════════════════════════════════════════════╝
def _parse_modal_date(raw):
    value = (raw or '').strip()
    if not value:
        return None, None
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(value, fmt).date(), None
        except ValueError:
            continue
    return None, 'Invalid date format. Use mm/dd/yyyy.'


def _assignment_is_current_incumbent(assignment):
    """Whether assignment holds the position on today's organogram."""
    today = timezone.localdate()
    if assignment.terminated and assignment.terminated <= today:
        return False
    return True


def _close_assignment_row(assignment, close_date, user):
    assignment.terminated = close_date
    assignment.uat = timezone.now()
    assignment.uby = user
    assignment.save()


def _create_successor_assignment(old_assignment, employee, effective, user, position=None):
    target_position = position or old_assignment.position
    new_assignment = Assignment(
        position=target_position,
        employee=employee,
        title=old_assignment.title,
        effective=effective,
        terminated=None,
        status=old_assignment.status,
        cby=user,
        uby=user,
    )
    new_assignment.uat = timezone.now()
    new_assignment.save()
    return new_assignment


def _assignment_response(assignment):
    from apps.humancapital.views.humancapital_view import (
        _employee_code,
        _employee_display_label,
        _employee_is_probation,
        _row_incumbent_name,
    )
    display_name = _row_incumbent_name(assignment)
    employee_code = _employee_code(assignment)
    return {
        'ok': True,
        'employee_id': assignment.employee_id,
        'employee_name': display_name,
        'employee_code': employee_code,
        'employee_display': _employee_display_label(display_name, employee_code),
        'assignment_id': assignment.pk,
        'effective': assignment.effective.strftime('%Y-%m-%d') if assignment.effective else '',
        'terminated': assignment.terminated.strftime('%Y-%m-%d') if assignment.terminated else '',
        'is_probation': _employee_is_probation(assignment),
    }


@login_required
@require_POST
def quick_assign_position(request, pk):
    """Create an assignment for a position that has no assignment row yet."""
    position = get_object_or_404(Position, pk=pk, deleted=False, status=1)
    emp_id_raw = request.POST.get('employee', '').strip()
    if not emp_id_raw:
        return JsonResponse({'ok': False, 'error': str(_('Please select an employee.'))}, status=400)

    try:
        emp_id = int(emp_id_raw)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid employee ID.'}, status=400)

    from apps.humancapital.views.humancapital_view import position_is_vacant
    if not position_is_vacant(position):
        return JsonResponse({'ok': False, 'error': str(_('Position is not vacant.'))}, status=400)

    effective, err = _parse_modal_date(request.POST.get('effective'))
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    employee = get_object_or_404(Employee, pk=emp_id, status=1)
    assignment = Assignment(
        position=position,
        employee=employee,
        title=position.title,
        effective=effective or timezone.localdate(),
        terminated=None,
        status=1,
        cby=request.user,
        uby=request.user,
    )
    assignment.uat = timezone.now()
    assignment.save()
    return JsonResponse(_assignment_response(assignment))


@login_required
@require_POST
def quick_relocate(request, pk):
    """Move active employee from source assignment to a vacant target position."""
    source = get_object_or_404(Assignment, pk=pk, deleted=False)
    if not _assignment_is_current_incumbent(source) or not source.employee_id:
        return JsonResponse({
            'ok': False,
            'error': str(_('This position has no active employee to relocate.')),
        }, status=400)

    target_raw = request.POST.get('target_position_id', '').strip()
    try:
        target_position_id = int(target_raw)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': str(_('Invalid target position.'))}, status=400)

    target_position = get_object_or_404(Position, pk=target_position_id, deleted=False, status=1)
    if target_position.pk == source.position_id:
        return JsonResponse({
            'ok': False,
            'error': str(_('Cannot relocate to the same position.')),
        }, status=400)

    from apps.humancapital.views.humancapital_view import position_is_vacant
    if not position_is_vacant(target_position):
        return JsonResponse({
            'ok': False,
            'error': str(_('Target position is not vacant.')),
        }, status=400)

    effective, err = _parse_modal_date(request.POST.get('effective'))
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    today = timezone.localdate()
    new_start = effective or today
    if source.terminated is None:
        close_date = new_start - datetime.timedelta(days=1)
        if source.effective and close_date < source.effective:
            close_date = new_start
        _close_assignment_row(source, close_date, request.user)

    employee = source.employee
    new_assignment = _create_successor_assignment(
        source, employee, new_start, request.user, position=target_position,
    )

    from apps.humancapital.views.humancapital_view import (
        _employee_code,
        _employee_display_label,
        _employee_is_probation,
        _row_incumbent_name,
    )
    display_name = _row_incumbent_name(new_assignment)
    employee_code = _employee_code(new_assignment)
    org = target_position.organization
    area = (org.shortname or org.name or '') if org else ''
    return JsonResponse({
        'ok': True,
        'reload': True,
        'source_position_id': source.position_id,
        'source_assignment_id': source.pk,
        'target_position_id': target_position.pk,
        'target_assignment_id': new_assignment.pk,
        'target_position_name': target_position.name or '',
        'target_area': area,
        'employee_id': employee.pk,
        'employee_name': display_name,
        'employee_code': employee_code,
        'employee_display': _employee_display_label(display_name, employee_code),
        'effective': new_assignment.effective.strftime('%Y-%m-%d') if new_assignment.effective else '',
        'terminated': '',
        'is_probation': _employee_is_probation(new_assignment),
    })


@login_required
@require_POST
def quick_assign(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, deleted=False)
    emp_id_raw = request.POST.get('employee', '').strip()
    inplace = (request.POST.get('inplace') or '').strip().lower() in ('1', 'true', 'yes')

    effective, err = _parse_modal_date(request.POST.get('effective'))
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)
    terminated, err = _parse_modal_date(request.POST.get('terminated'))
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    result_assignment = assignment

    if emp_id_raw:
        try:
            emp_id = int(emp_id_raw)
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'error': 'Invalid employee ID.'}, status=400)
        employee = get_object_or_404(Employee, pk=emp_id, status=1)

        if inplace:
            # Direct swap on the same assignment row — no close/successor history.
            if not _assignment_is_current_incumbent(assignment):
                return JsonResponse({
                    'ok': False,
                    'error': str(_('Only the current incumbent can be changed in place.')),
                }, status=400)
            assignment.employee = employee
            assignment.uat = timezone.now()
            assignment.uby = request.user
            assignment.save()
            result_assignment = assignment
        elif (
            assignment.employee_id == emp_id
            and _assignment_is_current_incumbent(assignment)
        ):
            assignment.effective = effective or assignment.effective
            assignment.terminated = None
            assignment.uat = timezone.now()
            assignment.uby = request.user
            assignment.save()
            result_assignment = assignment
        else:
            today = timezone.localdate()
            new_start = effective or today
            if assignment.terminated is None:
                close_date = new_start - datetime.timedelta(days=1)
                if assignment.effective and close_date < assignment.effective:
                    close_date = new_start
                _close_assignment_row(assignment, close_date, request.user)

            result_assignment = _create_successor_assignment(
                assignment, employee, new_start, request.user
            )
    else:
        if not terminated:
            return JsonResponse({
                'ok': False,
                'error': str(_('Terminated date is required when marking a position vacant.')),
            }, status=400)
        assignment.effective = effective
        assignment.terminated = terminated
        assignment.uat = timezone.now()
        assignment.uby = request.user
        assignment.save()

    from apps.humancapital.views.humancapital_view import (
        _employee_code,
        _employee_display_label,
        _employee_is_probation,
        _row_incumbent_name,
    )
    display_name = '' if not emp_id_raw else _row_incumbent_name(result_assignment)
    employee_code = _employee_code(result_assignment) if emp_id_raw else ''
    return JsonResponse({
        'ok': True,
        'employee_id': result_assignment.employee_id if emp_id_raw else '',
        'employee_name': display_name,
        'employee_code': employee_code,
        'employee_display': _employee_display_label(display_name, employee_code),
        'assignment_id': result_assignment.pk,
        'previous_assignment_id': assignment.pk if result_assignment.pk != assignment.pk else '',
        'effective': result_assignment.effective.strftime('%Y-%m-%d') if result_assignment.effective else '',
        'terminated': result_assignment.terminated.strftime('%Y-%m-%d') if result_assignment.terminated else '',
        'is_probation': bool(emp_id_raw) and _employee_is_probation(result_assignment),
    })

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Create                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to create a new record                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class Create(CreateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template

    def get_success_url(self):
        return reverse_lazy(This.url_list)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['related1_qs'] = This.related1.objects.filter(status=1)
        kwargs['related2_qs'] = This.related2.objects.filter(status=1)
        kwargs['title_qs'] = This.related3.objects.filter(status=1)
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'add'
        return context

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Detail                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to see detail of an existing record         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class Detail(DetailView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['related1_qs'] = This.related1.objects.filter(status=1)
        kwargs['related2_qs'] = This.related2.objects.filter(status=1)
        kwargs['title_qs'] = This.related3.objects.filter(status=1)
        kwargs['mode'] = 'view'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'view'
        context[This.model.__name__.lower()] = self.object

        form = This.form_class(
            instance=self.object,
            related1_qs=This.related1.objects.filter(status=1),
            related2_qs=This.related2.objects.filter(status=1),
            title_qs=This.related3.objects.filter(status=1),
        )
        for name, field in form.fields.items():
            field.widget.attrs['readonly'] = 'readonly'
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control-plaintext'
        form.fields['status'].disabled = True
        form.fields[This.related1_lower].disabled = True
        form.fields[This.related2_lower].disabled = True
        form.fields['title'].disabled = True

        context['form'] = form
        return context
        
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: Update                                              ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: View to update an existing record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignment_view.py          ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class Update(UpdateView):
    model = This.model
    form_class = This.form_class
    template_name = This.form_template
    success_url = reverse_lazy(This.url_list)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['related1_qs'] = This.related1.objects.filter(status=1)
        kwargs['related2_qs'] = This.related2.objects.filter(status=1)
        kwargs['title_qs'] = This.related3.objects.filter(status=1)
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
# ║  Name: SoftDelete                                          ║
# ║  Type: Class Base View                                     ║
# ║  Purpose: Delete View used to delete record                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\assignments_views.py        ║
# ║  Created: May/22-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
class SoftDel(SoftDelete):
    model = This.model
    namespace = This.namespace
    url_list = This.url_list