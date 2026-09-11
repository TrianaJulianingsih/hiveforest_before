from django.db.models import Sum

from apps.analytics.models.iqvia import IQV_ITMATrans
from apps.analytics.services.iqvia_dimension_service import (
    MAT_WINDOW,
    MEASURE_VALUE,
    trans_path,
)

OTHERS_LABEL = "Others"
MAX_BARS = 50

# Growth always compares two points, never a series
PMODE_YEAR = "year"
PMODE_QUARTER = "quarter"
PMODE_MAT = "mat"


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


# Trailing 4 quarters ending at the anchor
def _mat_window(year, quarter):
    end = _quarter_value(year, quarter)
    start = end - MAT_WINDOW + 1
    return [_quarter_label(v) for v in range(start, end + 1)]


# Narrow to ONE point in time, whichever of the 3 modes
def _point_queryset(qs, pmode, year, quarter):
    if pmode == PMODE_QUARTER:
        return qs.filter(quarter=_quarter_label(_quarter_value(year, quarter)))
    if pmode == PMODE_MAT:
        return qs.filter(quarter__in=_mat_window(year, quarter))
    return qs.filter(year=year)


# Readable caption for one point, used as the bar legend
def point_label(pmode, year, quarter):
    if pmode == PMODE_QUARTER:
        return f"Q{quarter}/{year}"
    if pmode == PMODE_MAT:
        return f"MAT Q{quarter}/{year}"
    return str(year)


# Totals per dimension item at one point in time
def _totals_at(dim_key, selected, pmode, year, quarter):
    qs = _point_queryset(_base_queryset(selected), pmode, year, quarter)

    path = trans_path(dim_key)
    id_field = f"{path}__id"
    code_field = f"{path}__code"
    name_field = f"{path}__name"

    rows = (
        qs.filter(**{f"{id_field}__isnull": False})
        .values(id_field, code_field, name_field)
        .annotate(total=Sum(MEASURE_VALUE))
    )

    totals = {}
    names = {}
    for row in rows:
        key = row[id_field]
        totals[key] = float(row["total"] or 0)
        if key not in names:
            code = row[code_field] or ""
            name = row[name_field] or ""
            names[key] = f"{code} - {name}".strip(" -") or str(key)
    return totals, names


# Percent change, guarding the divide by zero case
def _growth(before, after):
    if before > 0:
        return round((after - before) / before * 100, 2), None
    if after > 0:
        return None, "New"
    return 0.0, None


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_growth_rows                                     ║
# ║  Type: Service function                                    ║
# ║  Purpose: Two point comparison per dimension item          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_growth_service.py     ║
# ║  Created: Aug/26-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def get_growth_rows(
    dim_key, pmode, year_from, q_from, year_to, q_to, selected=None, limit=10
):
    if pmode not in (PMODE_YEAR, PMODE_QUARTER, PMODE_MAT):
        pmode = PMODE_YEAR

    before_map, names_a = _totals_at(dim_key, selected, pmode, year_from, q_from)
    after_map, names_b = _totals_at(dim_key, selected, pmode, year_to, q_to)

    names = dict(names_a)
    names.update(names_b)

    # Combined total, the whole market collapsed into one pair of bars
    if not limit:
        before = sum(before_map.values())
        after = sum(after_map.values())
        pct, tag = _growth(before, after)
        return [
            {
                "label": "Combined total",
                "before": before,
                "after": after,
                "growth": pct,
                "growth_tag": tag,
                "is_others": False,
            }
        ]

    keys = set(before_map) | set(after_map)
    items = []
    for key in keys:
        items.append(
            {
                "key": key,
                "label": names.get(key, str(key)),
                "before": before_map.get(key, 0.0),
                "after": after_map.get(key, 0.0),
            }
        )

    # Biggest at the latest point wins the limited slots
    items.sort(key=lambda x: x["after"], reverse=True)
    cap = min(limit, MAX_BARS)
    head, tail = items[:cap], items[cap:]

    rows = []
    for item in head:
        pct, tag = _growth(item["before"], item["after"])
        rows.append(
            {
                "label": item["label"],
                "before": item["before"],
                "after": item["after"],
                "growth": pct,
                "growth_tag": tag,
                "is_others": False,
            }
        )

    # Everything past the cap collapses into one Others pair
    if tail:
        before = sum(x["before"] for x in tail)
        after = sum(x["after"] for x in tail)
        pct, tag = _growth(before, after)
        rows.append(
            {
                "label": f"{OTHERS_LABEL} ({len(tail)} items)",
                "before": before,
                "after": after,
                "growth": pct,
                "growth_tag": tag,
                "is_others": True,
            }
        )

    return rows


# Detail behind the Others bar, largest first, for export only
def get_growth_others(
    dim_key, pmode, year_from, q_from, year_to, q_to, selected=None, limit=10
):
    if not limit:
        return []

    before_map, names_a = _totals_at(dim_key, selected, pmode, year_from, q_from)
    after_map, names_b = _totals_at(dim_key, selected, pmode, year_to, q_to)
    names = dict(names_a)
    names.update(names_b)

    items = []
    for key in set(before_map) | set(after_map):
        items.append(
            {
                "label": names.get(key, str(key)),
                "before": before_map.get(key, 0.0),
                "after": after_map.get(key, 0.0),
            }
        )
    items.sort(key=lambda x: x["after"], reverse=True)

    rows = []
    for item in items[min(limit, MAX_BARS):]:
        pct, tag = _growth(item["before"], item["after"])
        rows.append(
            {
                "label": item["label"],
                "before": item["before"],
                "after": item["after"],
                "growth": pct,
                "growth_tag": tag,
            }
        )
    return rows