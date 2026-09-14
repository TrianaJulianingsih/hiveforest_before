from collections import defaultdict
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.base.models.people import Gender
from apps.humancapital.models import Assignment, Employee, Organization, Position

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: application_landing                                 ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: To display landing page                          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\humancapital_views.py       ║
# ║  Created: Jun/2-2025 by Setiadji                           ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def landing(request):
    from apps.base.services.system_log_service import SystemLogService
    from apps.base.models.system_log import LogAction
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Human Capital",
        feature="Human Capital Landing Page",
        description="User viewed the Human Capital landing page.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    # Basic summary stats
    employee_count = Employee.objects.filter(status=1).count()
    organization_count = Organization.objects.filter(status=1).count()
    position_count = Position.objects.filter(status=1).count()
    assignment_count = Assignment.objects.filter(status=1).count()

    context = {
        'employee_count': employee_count,
        'organization_count': organization_count,
        'position_count': position_count,
        'assignment_count': assignment_count,
    }
    return render(request, 'landing.html', context)


def _position_sort_key(position):
    level = position.level
    if level is None:
        level = 999
    return (level, (position.name or '').lower())


def _active_assignments_list(position):
    return list(getattr(position, 'active_assignments', None) or [])


def _assignment_visible_for_display(assignment, as_of):
    """Whether an assignment should appear as holding the position on as_of."""
    if assignment.terminated:
        today = timezone.localdate()
        if as_of < today:
            return assignment.terminated >= as_of
        return assignment.terminated > as_of
    return True


def _row_incumbent_name(assignment):
    """Person line for one assignment (matches legacy primary row: employee, else assignment name)."""
    if not assignment:
        return ''
    n = _employee_name(assignment).strip()
    if n:
        return n
    return (assignment.name or '').strip()


def _employee_name(assignment):
    if not assignment or not assignment.employee:
        return ''
    emp = assignment.employee
    if getattr(emp, 'person', None) and (emp.person.name or '').strip():
        return emp.person.name.strip()
    return (emp.name or '').strip()


def _employee_code(assignment):
    if not assignment or not assignment.employee:
        return ''
    return (assignment.employee.code or '').strip()


def _employee_is_probation(assignment):
    emp = getattr(assignment, 'employee', None) if assignment else None
    return bool(emp) and getattr(emp, 'employment_status', '') == Employee.EMPLOYMENT_PROBATION


def _employee_display_label(name, code=''):
    name = (name or '').strip()
    code = (code or '').strip()
    if name and code:
        return f'{name} - {code}'
    return name or code


def _assignment_title_label(assignment):
    if not assignment or not assignment.title_id:
        return ''
    title = assignment.title
    return (title.name or '').strip() if title else ''


def _assignment_date_iso(assignment, field):
    value = getattr(assignment, field, None)
    return value.strftime('%Y-%m-%d') if value else ''


def _vacant_assignment_for_position(position, as_of=None, vacant_map=None):
    """Most recent ended assignment when the position has no visible incumbent."""
    if as_of is None:
        as_of = timezone.localdate()
    if _incumbents_list(position, as_of):
        return None
    for a in _active_assignments_list(position):
        if a.terminated and not _assignment_visible_for_display(a, as_of):
            return a
    if vacant_map is not None:
        return vacant_map.get(position.id)
    return None


def _build_vacant_assignment_map(position_ids, as_of=None):
    """Batch-load latest ended assignment per position (for vacant seats)."""
    if not position_ids:
        return {}
    if as_of is None:
        as_of = timezone.localdate()
    today = timezone.localdate()
    qs = (
        Assignment.objects.filter(
            position_id__in=position_ids,
            deleted=False,
            terminated__isnull=False,
            terminated__lte=as_of,
        )
        .filter(Q(effective__isnull=True) | Q(effective__lte=as_of))
        .select_related('employee', 'employee__person', 'title')
        .order_by('position_id', '-terminated', '-id')
    )
    if as_of >= today:
        qs = qs.filter(status=1)
    result = {}
    for assignment in qs:
        if assignment.position_id not in result:
            result[assignment.position_id] = assignment
    return result


_OG_NEW_DAYS = 30


def _is_new_as_of(effective_iso, as_of):
    """True when as_of is within 30 days of the assignment effective date."""
    if not effective_iso:
        return False
    if as_of is None:
        as_of = timezone.localdate()
    try:
        eff = date.fromisoformat(str(effective_iso)[:10])
    except ValueError:
        return False
    days = (as_of - eff).days
    return 0 <= days <= _OG_NEW_DAYS


def _incumbents_list(position, as_of=None):
    """One dict per active assignment: display name + job title (may be empty)."""
    if as_of is None:
        as_of = timezone.localdate()
    rows = []
    for a in _active_assignments_list(position):
        if not _assignment_visible_for_display(a, as_of):
            continue
        name = _row_incumbent_name(a).strip()
        code = _employee_code(a)
        effective = _assignment_date_iso(a, 'effective')
        rows.append({
            'name': name,
            'employee_code': code,
            'display_name': _employee_display_label(name, code),
            'title': _assignment_title_label(a).strip(),
            'assignment_id': a.id,
            'employee_id': a.employee_id,
            'effective': effective,
            'terminated': _assignment_date_iso(a, 'terminated'),
            'is_new': bool(name) and _is_new_as_of(effective, as_of),
            'is_probation': bool(name) and _employee_is_probation(a),
        })
    return rows


def _occupied_position_ids(as_of=None):
    """Position IDs with a visible incumbent on as_of."""
    today = timezone.localdate()
    if as_of is None:
        as_of = today
    qs = Assignment.objects.filter(
        deleted=False,
        position_id__isnull=False,
    ).filter(
        Q(effective__isnull=True) | Q(effective__lte=as_of),
    )
    if as_of >= today:
        qs = qs.filter(status=1).filter(
            Q(terminated__isnull=True) | Q(terminated__gt=as_of),
        )
    else:
        qs = qs.filter(
            Q(terminated__isnull=True) | Q(terminated__gte=as_of),
        )
    return set(qs.values_list('position_id', flat=True).distinct())


def position_is_vacant(position, as_of=None):
    """Whether a position has no active incumbent on as_of."""
    if as_of is None:
        as_of = timezone.localdate()
    return position.id not in _occupied_position_ids(as_of)


def vacant_positions_queryset(as_of=None, exclude_position_id=None):
    """Active positions with no incumbent — relocation targets only."""
    qs = Position.objects.filter(deleted=False, status=1).select_related('organization')
    if exclude_position_id:
        qs = qs.exclude(pk=exclude_position_id)
    occupied = _occupied_position_ids(as_of)
    if occupied:
        qs = qs.exclude(pk__in=occupied)
    return qs.order_by('organization__name', 'name', 'id')


def _holder_name(position):
    """All active incumbents (assignment label or employee per row), for exports/API parity."""
    parts = []
    for assignment in _active_assignments_list(position):
        name = (assignment.name or '').strip()
        parts.append(name if name else _employee_name(assignment).strip())
    return '\n'.join(p for p in parts if p)


def _footer_fields(position):
    org = position.organization
    footer_type = ''
    footer_org = ''
    if org:
        footer_org = (org.shortname or org.name or '').strip()
        typ = getattr(org, 'type', None)
        if typ is not None:
            footer_type = (typ.name or '').strip()
    footer_size = '' if position.level is None else str(position.level)
    return footer_type, footer_org, footer_size


def _parse_positive_int(value):
    if value is None or value == '':
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _org_descendant_ids(root_org_id, organizations):
    """Return set of organization PKs: root_org_id and all its active descendants."""
    by_parent = defaultdict(list)
    for org in organizations:
        by_parent[org.parent_id].append(org)
    out = {root_org_id}
    stack = list(by_parent.get(root_org_id, []))
    while stack:
        org = stack.pop()
        if org.id in out:
            continue
        out.add(org.id)
        stack.extend(by_parent.get(org.id, []))
    return out


def _parse_as_of_date(value):
    if value is None or value == '':
        return None
    raw = str(value).strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _assignments_for_organogram(as_of=None):
    """Assignments visible on the organogram for a calendar day."""
    today = timezone.localdate()
    view_date = as_of or today
    qs = (
        Assignment.objects.filter(deleted=False)
        .select_related('employee', 'employee__person', 'title')
        .order_by('id')
    )
    if as_of is None or as_of >= today:
        qs = qs.filter(status=1)
    return qs.filter(
        Q(effective__isnull=True) | Q(effective__lte=view_date),
        Q(terminated__isnull=True) | Q(terminated__gte=view_date),
    )


def _build_assignment_history(org_descendant_ids=None):
    """All assignment tenures for the History tab (current and ended)."""
    today = timezone.localdate()
    vacant_label = str(_('Vacant'))
    qs = (
        Assignment.objects.filter(deleted=False, position_id__isnull=False)
        .select_related(
            'employee',
            'employee__person',
            'title',
            'position',
            'position__organization',
        )
        .order_by('-effective', '-id')
    )
    if org_descendant_ids is not None:
        qs = qs.filter(position__organization_id__in=org_descendant_ids)
    rows = []
    for assignment in qs:
        name = _row_incumbent_name(assignment)
        code = _employee_code(assignment)
        display = _employee_display_label(name, code) or vacant_label
        position = assignment.position
        org = position.organization if position else None
        terminated = assignment.terminated
        rows.append({
            'id': assignment.id,
            'employee_id': assignment.employee_id or 0,
            'employee_name': name,
            'employee_code': code,
            'employee_display': display,
            'position_id': assignment.position_id or 0,
            'position_name': (position.name or '') if position else '',
            'position_code': (position.code or '') if position else '',
            'organization_name': (org.name or '') if org else '',
            'title': _assignment_title_label(assignment),
            'effective': _assignment_date_iso(assignment, 'effective'),
            'terminated': _assignment_date_iso(assignment, 'terminated'),
            'is_current': terminated is None or terminated > today,
        })
    return rows


def _positions_for_organogram(as_of=None):
    """Positions included in the organogram tree for a calendar day."""
    today = timezone.localdate()
    qs = Position.objects.filter(deleted=False)
    if as_of is None or as_of >= today:
        return qs.filter(status=1)
    return qs.filter(
        Q(effective__isnull=True) | Q(effective__lte=as_of),
        Q(terminated__isnull=True) | Q(terminated__gte=as_of),
    )


def _positions_matching_employee_search(positions, query, as_of=None):
    """Positions with an incumbent whose name or NIP matches query."""
    q = (query or '').strip().lower()
    if not q:
        return []
    hits = []
    for position in positions:
        for inc in _incumbents_list(position, as_of):
            name = (inc.get('name') or '').lower()
            code = (inc.get('employee_code') or '').lower()
            display = (inc.get('display_name') or '').lower()
            if q in name or q in code or q in display:
                hits.append(position)
                break
    return hits


def _positions_matching_position_search(positions, query):
    """Positions whose name, code, shortname, or initial matches query."""
    q = (query or '').strip().lower()
    if not q:
        return []
    hits = []
    for position in positions:
        name = (position.name or '').lower()
        code = (position.code or '').lower()
        shortname = (position.shortname or '').lower()
        initial = (position.initial or '').lower()
        if q in name or q in code or q in shortname or q in initial:
            hits.append(position)
    return hits


def _extend_positions_parent_level(positions, positions_all, levels=1):
    """Include direct parent position(s) above the current set (e.g. when org-filtered)."""
    if levels < 1 or not positions:
        return positions
    by_id = {p.id: p for p in positions_all}
    current = list(positions)
    in_set = {p.id for p in current}
    for _ in range(levels):
        parent_ids = {
            p.parent_id
            for p in current
            if p.parent_id and p.parent_id not in in_set
        }
        if not parent_ids:
            break
        added = []
        for pid in parent_ids:
            parent = by_id.get(pid)
            if parent and parent.id not in in_set:
                added.append(parent)
                in_set.add(parent.id)
        if not added:
            break
        current.extend(added)
    return current


def _extend_positions_descendants(positions, positions_all):
    """Include all descendant positions under the current set (for search expand/collapse)."""
    if not positions:
        return positions
    by_parent = defaultdict(list)
    for p in positions_all:
        if p.parent_id:
            by_parent[p.parent_id].append(p)
    current = list(positions)
    in_set = {p.id for p in current}
    queue = [p.id for p in current]
    while queue:
        pid = queue.pop()
        for child in by_parent.get(pid, []):
            if child.id not in in_set:
                current.append(child)
                in_set.add(child.id)
                queue.append(child.id)
    return current


def _narrow_positions_for_search(hits, positions_all):
    """Search result scope: matches + one manager above + full subtree under matches."""
    if not hits:
        return []
    by_id = {p.id: p for p in hits}
    for p in _extend_positions_parent_level(hits, positions_all, levels=1):
        by_id[p.id] = p
    for p in _extend_positions_descendants(hits, positions_all):
        by_id[p.id] = p
    return list(by_id.values())


def _build_position_subtree(position, by_parent, ancestor_ids=None, depth=0, as_of=None, vacant_map=None):
    # Skip edges that would close a cycle in parent links (avoids RecursionError → 500).
    if ancestor_ids is None:
        ancestor_ids = frozenset()
    next_ancestors = ancestor_ids | {position.id}
    raw_children = sorted(by_parent.get(position.id, []), key=_position_sort_key)
    children = []
    for child in raw_children:
        if child.id in next_ancestors:
            continue
        children.append(_build_position_subtree(child, by_parent, next_ancestors, depth + 1, as_of, vacant_map))
    org = position.organization
    organization_label = (org.name if org else '') or ''
    incumbents = _incumbents_list(position, as_of)
    n_inc = len(incumbents)
    if n_inc == 1:
        employee_name = incumbents[0]['name']
        employee_code = incumbents[0]['employee_code']
        employee_display = incumbents[0]['display_name']
        assignment_title = incumbents[0]['title']
        assignment_id = incumbents[0]['assignment_id']
        employee_id = incumbents[0]['employee_id']
        effective = incumbents[0]['effective']
        terminated = incumbents[0]['terminated']
    else:
        vacant_assignment = _vacant_assignment_for_position(position, as_of, vacant_map)
        employee_name = ''
        employee_code = ''
        employee_display = ''
        assignment_title = ''
        employee_id = None
        effective = ''
        terminated = ''
        assignment_id = vacant_assignment.id if vacant_assignment else None
        if vacant_assignment:
            effective = _assignment_date_iso(vacant_assignment, 'effective')
            terminated = _assignment_date_iso(vacant_assignment, 'terminated')
    footer_type, footer_org, footer_size = _footer_fields(position)
    return {
        'id': position.id,
        'depth': depth,
        'name': position.name or '',
        'organization_id': org.id if org else None,
        'organization_label': organization_label,
        'holder_name': _holder_name(position),
        'incumbents': incumbents,
        'incumbent_count': n_inc,
        'employee_name': employee_name,
        'employee_code': employee_code,
        'employee_display': employee_display,
        'assignment_title': assignment_title,
        'assignment_id': assignment_id,
        'employee_id': employee_id,
        'effective': effective,
        'terminated': terminated,
        'is_new': bool(employee_name) and _is_new_as_of(effective, as_of),
        'is_probation': bool(n_inc == 1 and incumbents and incumbents[0].get('is_probation')),
        'footer_type': footer_type,
        'footer_org': footer_org,
        'footer_size': footer_size,
        'area_team': organization_label,
        'children': children,
    }


def _orgchart_node_subtitle(node, vacant_label):
    incumbents = node.get('incumbents') or []
    if not incumbents:
        return vacant_label
    if len(incumbents) == 1:
        n = (incumbents[0].get('display_name') or incumbents[0].get('name') or '').strip()
        t = (incumbents[0].get('title') or '').strip()
        if n and t:
            return f'{n} — {t}'
        if n:
            return n
        if t:
            return f'{vacant_label} — {t}'
        return vacant_label
    parts = []
    for i, row in enumerate(incumbents, start=1):
        n = (row.get('display_name') or row.get('name') or '').strip()
        t = (row.get('title') or '').strip()
        if n and t:
            parts.append(f'{i}. {n} — {t}')
        elif n:
            parts.append(f'{i}. {n}')
        elif t:
            parts.append(f'{i}. {vacant_label} — {t}')
        else:
            parts.append(f'{i}. {vacant_label}')
    return '\n'.join(parts)[:500]


def _node_to_orgchart_dict(node, vacant_label, hybrid_threshold):
    raw_children = node.get('children') or []
    children = [_node_to_orgchart_dict(c, vacant_label, hybrid_threshold) for c in raw_children]
    payload = {
        'id': str(node['id']),
        'name': (node.get('name') or '')[:200],
        'title': _orgchart_node_subtitle(node, vacant_label)[:500],
        'area': (node.get('area_team') or '')[:200],
        'organization_id': node.get('organization_id'),
        'organization_name': (node.get('organization_label') or '')[:200],
        'incumbent_count': node.get('incumbent_count') or 0,
        'assignment_id': node.get('assignment_id'),
        'employee_id': node.get('employee_id'),
        'employee_name': (node.get('employee_name') or '')[:200],
        'employee_code': (node.get('employee_code') or '')[:20],
        'employee_display': (node.get('employee_display') or '')[:220],
        'assignment_title': (node.get('assignment_title') or '')[:200],
        'effective': (node.get('effective') or '')[:10],
        'terminated': (node.get('terminated') or '')[:10],
        'is_new': bool(node.get('is_new')),
        'is_probation': bool(node.get('is_probation')),
        'incumbents': [
            {
                'name': (row.get('name') or '')[:200],
                'employee_code': (row.get('employee_code') or '')[:20],
                'display_name': (row.get('display_name') or '')[:220],
                'title': (row.get('title') or '')[:200],
                'assignment_id': row.get('assignment_id'),
                'employee_id': row.get('employee_id'),
                'effective': (row.get('effective') or '')[:10],
                'terminated': (row.get('terminated') or '')[:10],
                'is_new': bool(row.get('is_new')),
                'is_probation': bool(row.get('is_probation')),
            }
            for row in (node.get('incumbents') or [])
        ],
        'children': children,
    }
    # hybrid stacks direct children vertically; limit to leaf tier so deeper levels stay horizontal
    if (
        len(children) >= hybrid_threshold
        and all(not (c.get('children') or []) for c in raw_children)
    ):
        payload['hybrid'] = True
    return payload


def _build_orgchart_bundle(position_tree, vacant_label):
    """Payload for OrgChart: one tree per top-level root (no synthetic __og__ parent)."""
    if not position_tree:
        return None
    hybrid_threshold = getattr(settings, 'ORGANOGRAM_HYBRID_CHILD_THRESHOLD', 4)
    trees = [_node_to_orgchart_dict(n, vacant_label, hybrid_threshold) for n in position_tree]
    return {
        'multi': len(trees) > 1,
        'trees': trees,
    }


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: organogram                                          ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: MVP position tree (parent hierarchy + holder)    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Orphans: parent_id points outside active Position set     ║
# ║  (e.g. inactive parent) → separate subtree list below.     ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def organogram(request):
    from apps.base.services.system_log_service import SystemLogService
    from apps.base.models.system_log import LogAction
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Human Capital",
        feature="Organogram View",
        description="User viewed the position hierarchy organogram.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    today = timezone.localdate()
    as_of_date = _parse_as_of_date(request.GET.get('as_of'))
    if as_of_date and as_of_date > today:
        as_of_date = today
    is_historical_view = as_of_date is not None and as_of_date < today

    assignments_qs = _assignments_for_organogram(as_of_date)
    positions_all = list(
        _positions_for_organogram(as_of_date)
        .select_related('organization', 'organization__type')
        .prefetch_related(
            Prefetch('assignment_set', queryset=assignments_qs, to_attr='active_assignments')
        )
    )

    organizations = list(
        Organization.objects.filter(deleted=False, status=1).order_by('name', 'id')
    )
    org_id_param = _parse_positive_int(request.GET.get('organization'))

    org_descendant_ids = None
    selected_organization_id = None
    if org_id_param is not None and any(o.id == org_id_param for o in organizations):
        selected_organization_id = org_id_param
        org_descendant_ids = _org_descendant_ids(org_id_param, organizations)

    if org_descendant_ids is not None:
        positions = [
            p for p in positions_all if p.organization_id and p.organization_id in org_descendant_ids
        ]
        positions = _extend_positions_parent_level(positions, positions_all, levels=1)
    else:
        positions = positions_all

    search_position = (request.GET.get('position') or '').strip()
    if search_position:
        hits = _positions_matching_position_search(positions, search_position)
        positions = _narrow_positions_for_search(hits, positions_all)

    search_q = (request.GET.get('q') or '').strip()
    if search_q:
        hits = _positions_matching_employee_search(positions, search_q, as_of_date)
        positions = _narrow_positions_for_search(hits, positions_all)

    by_parent = defaultdict(list)
    for p in positions:
        by_parent[p.parent_id].append(p)

    position_ids = {p.id for p in positions}

    roots = [p for p in positions if p.parent_id is None or p.parent_id not in position_ids]
    roots_sorted = sorted(roots, key=_position_sort_key)

    # Count positions shown as extra top-level roots because parent is outside this scope
    # (same rows as in position_tree—do not render a second tree or it duplicates the UI).
    detached_parent_root_count = sum(
        1 for p in positions if p.parent_id is not None and p.parent_id not in position_ids
    )

    vacant_map = _build_vacant_assignment_map([p.id for p in positions], as_of_date)

    position_tree = [
        _build_position_subtree(p, by_parent, as_of=as_of_date, vacant_map=vacant_map)
        for p in roots_sorted
    ]

    filter_applied = bool(selected_organization_id or search_q or search_position)
    selected_organization_name = None
    if selected_organization_id is not None:
        selected_organization_name = next(
            (o.name for o in organizations if o.id == selected_organization_id),
            None,
        )

    vacant_label = str(_('Vacant'))
    organogram_orgchart_data = _build_orgchart_bundle(position_tree, vacant_label)
    organogram_history_data = _build_assignment_history(org_descendant_ids)
    genders = list(Gender.objects.filter(status=1).order_by('name'))

    context = {
        'position_tree': position_tree,
        'organogram_orgchart_data': organogram_orgchart_data,
        'organogram_history_data': organogram_history_data,
        'detached_parent_root_count': detached_parent_root_count,
        'organizations': organizations,
        'genders': genders,
        'selected_organization_id': selected_organization_id,
        'selected_organization_name': selected_organization_name,
        'search_q': search_q,
        'search_position': search_position,
        'filter_applied': filter_applied,
        'as_of_date': as_of_date,
        'as_of_date_iso': as_of_date.isoformat() if as_of_date else '',
        'today_iso': today.isoformat(),
        'is_historical_view': is_historical_view,
        'organogram_read_only': is_historical_view,
    }
    return render(request, 'organogram/organogram.html', context)
