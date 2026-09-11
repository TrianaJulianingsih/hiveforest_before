from django.db.models import Sum

from apps.analytics.models.iqvia import IQV_ITMATrans
from apps.analytics.services.iqvia_dimension_service import (
    MAT_WINDOW,
    MEASURE_UNIT,
    MEASURE_VALUE,
    PERIOD_MAT,
    PERIOD_QUARTER,
    PERIOD_YEAR,
    trans_path,
)
from apps.analytics.services.iqvia_report_service import (
    quarter_display,
    quarter_sort_key,
)

# Hard ceiling so the chart stays readable
MAX_SERIES = 50
OTHERS_LABEL = "Others"


# Transaction queryset narrowed by the filter selection
def _base_queryset(selected=None):
    qs = IQV_ITMATrans.objects.filter(deleted=False)
    for key, ids in (selected or {}).items():
        qs = qs.filter(**{f"{trans_path(key)}__id__in": ids})
    return qs


# Chronological order, year is numeric while quarter needs parsing
def _sort_periods(keys, base):
    clean = [k for k in keys if k not in (None, "")]
    if base == PERIOD_YEAR:
        return sorted(clean)
    return sorted(clean, key=quarter_sort_key)


# X axis label for one period key
def _period_label(key, base):
    if base == PERIOD_YEAR:
        return str(key)
    return quarter_display(key)


# Absolute quarter number, used to test for gaps
def _quarter_index(label):
    year, quarter = quarter_sort_key(label)
    return year * 4 + quarter


# True when the window has no missing quarter
def _is_consecutive(window):
    previous = None
    for label in window:
        current = _quarter_index(label)
        if previous is not None and current != previous + 1:
            return False
        previous = current
    return True


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: _mat_windows                                        ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Quarters that own a complete rolling window      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_trend_service.py      ║
# ║  Created: Aug/24-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, add anchor quarter          ║
# ╚════════════════════════════════════════════════════════════╝
def _mat_windows(keys, year_from, anchor=None):
    windows = []
    for index, key in enumerate(keys):
        year, quarter = quarter_sort_key(key)
        if year < year_from:
            continue
        # Anchor keeps only the windows that end on one specific quarter
        if anchor and quarter != anchor:
            continue
        start = index - MAT_WINDOW + 1
        if start < 0:
            continue
        window = keys[start : index + 1]
        # An incomplete window would understate the total, skip the point
        if len(window) == MAT_WINDOW and _is_consecutive(window):
            windows.append((key, window))
    return windows


# Group every row of one dimension, shared by chart and export
def _collect(dim_key, measure, base, year_from, year_to, selected=None):
    period_field = "year" if base == PERIOD_YEAR else "quarter"
    qs = _base_queryset(selected)

    # MAT reaches into the previous year to complete the first window
    low = year_from - 1 if base == PERIOD_MAT else year_from
    qs = qs.filter(year__gte=low, year__lte=year_to)

    path = trans_path(dim_key)
    id_field = f"{path}__id"
    code_field = f"{path}__code"
    name_field = f"{path}__name"

    rows = (
        qs.filter(**{f"{id_field}__isnull": False})
        .values(id_field, code_field, name_field, period_field)
        .annotate(total=Sum(measure))
    )

    bucket = {}
    grand = {}
    names = {}
    period_keys = set()
    for row in rows:
        key = row[id_field]
        period = row[period_field]
        value = float(row["total"] or 0)
        period_keys.add(period)
        bucket.setdefault(key, {})[period] = value
        grand[key] = grand.get(key, 0.0) + value
        if key not in names:
            code = row[code_field] or ""
            name = row[name_field] or ""
            names[key] = f"{code} - {name}".strip(" -") or str(key)

    return period_keys, bucket, grand, names


# Turn raw buckets into the final X axis keys and per item values
def _shape(period_keys, bucket, base, year_from, anchor=None):
    keys = _sort_periods(period_keys, base)

    if base != PERIOD_MAT:
        return keys, {k: v for k, v in bucket.items()}, keys

    windows = _mat_windows(keys, year_from, anchor)
    out_keys = [key for key, _window in windows]
    rolled = {}
    for item_key, row in bucket.items():
        rolled[item_key] = {
            key: sum(row.get(step, 0.0) for step in window) for key, window in windows
        }
    return out_keys, rolled, out_keys


# Recount totals after MAT reshaping so the ranking stays honest
def _rank(bucket, keys):
    grand = {}
    for item_key, row in bucket.items():
        grand[item_key] = sum(row.get(period, 0.0) for period in keys)
    return sorted(grand.items(), key=lambda kv: kv[1], reverse=True)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_trend_series                                    ║
# ║  Type: Service function                                    ║
# ║  Purpose: Build X labels and one series per dimension item ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_trend_service.py      ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, year range, MAT and anchor  ║
# ╚════════════════════════════════════════════════════════════╝
def get_trend_series(
    dim_key, measure, base, year_from, year_to, selected=None, limit=10, mat_anchor=None
):
    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE
    if base not in (PERIOD_YEAR, PERIOD_QUARTER, PERIOD_MAT):
        base = PERIOD_YEAR

    period_keys, bucket, _grand, names = _collect(
        dim_key, measure, base, year_from, year_to, selected
    )
    keys, shaped, _out = _shape(period_keys, bucket, base, year_from, mat_anchor)
    if not keys:
        return [], []

    labels = [_period_label(k, base) for k in keys]

    # Combined total, everything merged into a single line
    if not limit:
        merged = [0.0] * len(keys)
        for row in shaped.values():
            for index, period in enumerate(keys):
                merged[index] += row.get(period, 0.0)
        return labels, [
            {"label": "Combined total", "values": merged, "is_others": False}
        ]

    ranked = _rank(shaped, keys)
    cap = min(limit, MAX_SERIES)
    head, tail = ranked[:cap], ranked[cap:]

    series = []
    for key, _total in head:
        row = shaped.get(key, {})
        series.append(
            {
                "label": names.get(key, str(key)),
                "values": [row.get(p, 0.0) for p in keys],
                "is_others": False,
            }
        )

    # Everything past the cap collapses into one grey line
    if tail:
        merged = [0.0] * len(keys)
        for key, _total in tail:
            row = shaped.get(key, {})
            for index, period in enumerate(keys):
                merged[index] += row.get(period, 0.0)
        series.append(
            {
                "label": f"{OTHERS_LABEL} ({len(tail)} items)",
                "values": merged,
                "is_others": True,
            }
        )

    return labels, series


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_trend_export_rows                               ║
# ║  Type: Service function                                    ║
# ║  Purpose: Full detail for export, Others listed one by one ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_trend_service.py      ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, year range, MAT and anchor  ║
# ╚════════════════════════════════════════════════════════════╝
def get_trend_export_rows(
    dim_key, measure, base, year_from, year_to, selected=None, limit=10, mat_anchor=None
):
    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE
    if base not in (PERIOD_YEAR, PERIOD_QUARTER, PERIOD_MAT):
        base = PERIOD_YEAR

    period_keys, bucket, _grand, names = _collect(
        dim_key, measure, base, year_from, year_to, selected
    )
    keys, shaped, _out = _shape(period_keys, bucket, base, year_from, mat_anchor)
    if not keys:
        return [], [], []

    labels = [_period_label(k, base) for k in keys]
    ranked = _rank(shaped, keys)
    cap = min(limit, MAX_SERIES) if limit else len(ranked)

    def to_row(entry):
        row = shaped.get(entry[0], {})
        values = [row.get(p, 0.0) for p in keys]
        return [names.get(entry[0], str(entry[0]))] + values + [sum(values)]

    head_rows = [to_row(entry) for entry in ranked[:cap]]
    others_rows = [to_row(entry) for entry in ranked[cap:]]
    return labels, head_rows, others_rows