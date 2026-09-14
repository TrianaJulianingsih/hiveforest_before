from django.db.models import Sum

from apps.analytics.models.iqvia_models import IQV_ITMATrans
from apps.analytics.services.iqvia_dimension_service import (
    MAT_WINDOW,
    MEASURE_UNIT,
    MEASURE_VALUE,
    trans_path,
)

OTHERS_LABEL = "Others"
MAX_SLICES = 50


# Transaction queryset narrowed by the filter selection
def _base_queryset(selected=None):
    qs = IQV_ITMATrans.objects.filter(deleted=False)
    for key, ids in (selected or {}).items():
        qs = qs.filter(**{f"{trans_path(key)}__id__in": ids})
    return qs


# Single sortable number for one quarter, quarter is 1 to 4
def _quarter_value(year, quarter):
    return year * 4 + quarter


# 'QTR 2/2022' style label from a sortable quarter number
def _quarter_label(value):
    year = (value - 1) // 4
    quarter = ((value - 1) % 4) + 1
    return f"QTR {quarter}/{year}"


# Every quarter label between two points, inclusive
def _quarters_in_range(year_from, q_from, year_to, q_to):
    start = _quarter_value(year_from, q_from)
    end = _quarter_value(year_to, q_to)
    if start > end:
        start, end = end, start
    return [_quarter_label(v) for v in range(start, end + 1)]


# Trailing 4 quarters ending at the anchor
def _mat_window(year, quarter):
    end = _quarter_value(year, quarter)
    start = end - MAT_WINDOW + 1
    return [_quarter_label(v) for v in range(start, end + 1)]


# MAT ignores the From side entirely, it only needs the anchor
def _apply_period(qs, year_from, q_from, year_to, q_to, mat):
    if mat:
        return qs.filter(quarter__in=_mat_window(year_to, q_to))
    return qs.filter(quarter__in=_quarters_in_range(year_from, q_from, year_to, q_to))


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_share_rows                                      ║
# ║  Type: Service function                                    ║
# ║  Purpose: Value and percentage share per dimension item    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_share_service.py      ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, quarter range + MAT flag    ║
# ╚════════════════════════════════════════════════════════════╝
def get_share_rows(
    dim_key, measure, year_from, q_from, year_to, q_to, mat, selected=None, limit=10
):
    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE

    qs = _apply_period(_base_queryset(selected), year_from, q_from, year_to, q_to, mat)

    path = trans_path(dim_key)
    id_field = f"{path}__id"
    code_field = f"{path}__code"
    name_field = f"{path}__name"

    rows = (
        qs.filter(**{f"{id_field}__isnull": False})
        .values(id_field, code_field, name_field)
        .annotate(total=Sum(measure))
        .order_by("-total")
    )

    items = []
    for row in rows:
        code = row[code_field] or ""
        name = row[name_field] or ""
        label = f"{code} - {name}".strip(" -") or "UNKNOWN"
        items.append({"label": label, "value": float(row["total"] or 0)})

    grand = sum(item["value"] for item in items)
    if grand <= 0:
        return [], 0.0

    if limit and len(items) > limit:
        head = items[:limit]
        rest = sum(item["value"] for item in items[limit:])
        head.append({"label": OTHERS_LABEL, "value": rest})
        items = head

    for item in items:
        item["share"] = round(item["value"] / grand * 100, 2)

    return items, grand

def get_share_others(
    dim_key, measure, year_from, q_from, year_to, q_to, mat, selected=None, limit=10
):
    if not limit:
        return []

    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE

    qs = _apply_period(_base_queryset(selected), year_from, q_from, year_to, q_to, mat)

    path = trans_path(dim_key)
    id_field = f"{path}__id"
    code_field = f"{path}__code"
    name_field = f"{path}__name"

    rows = (
        qs.filter(**{f"{id_field}__isnull": False})
        .values(id_field, code_field, name_field)
        .annotate(total=Sum(measure))
        .order_by("-total")
    )

    items = []
    for row in rows:
        code = row[code_field] or ""
        name = row[name_field] or ""
        label = f"{code} - {name}".strip(" -") or "UNKNOWN"
        items.append({"label": label, "value": float(row["total"] or 0)})

    grand = sum(item["value"] for item in items)
    if grand <= 0 or len(items) <= limit:
        return []

    others_items = items[limit:]
    for item in others_items:
        item["share"] = round(item["value"] / grand * 100, 2)

    return others_items