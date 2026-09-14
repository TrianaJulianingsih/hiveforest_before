from django.db.models import Q

from apps.analytics.models.iqvia_models import IQV_Pack
from apps.analytics.services.iqvia_dimension_service import (
    BIG_ROWS,
    SEARCH_MIN_CHARS,
    get_dimension,
    is_valid_dimension,
    pack_prefix,
)

# Max options returned in one call
OPTION_LIMIT = 300


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: parse_selection                                     ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Read sel_<dim>=1,2,3 params into a clean dict     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_filter_service.py     ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def parse_selection(request):
    selected = {}
    for param in request.GET:
        if not param.startswith("sel_"):
            continue
        key = param[4:]
        if not is_valid_dimension(key):
            continue
        raw = request.GET.get(param) or ""
        ids = [int(x) for x in raw.split(",") if x.strip().isdigit()]
        if ids:
            selected[key] = ids
    return selected


# Pack queryset narrowed by every selection except one dimension
def build_pack_queryset(selected, exclude_key=None):
    qs = IQV_Pack.objects.filter(deleted=False)
    for key, ids in (selected or {}).items():
        if key == exclude_key:
            continue
        qs = qs.filter(**{f"{pack_prefix(key)}id__in": ids})
    return qs


# How many packs survive the current selection
def count_packs(selected=None):
    return build_pack_queryset(selected).count()


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_options                                         ║
# ║  Type: Service function                                    ║
# ║  Purpose: Option list of one dimension, cascaded by others ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_filter_service.py     ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def get_options(dim_key, selected=None, keyword="", limit=OPTION_LIMIT):
    cfg = get_dimension(dim_key)
    if cfg is None:
        return None

    selected = selected or {}
    keyword = (keyword or "").strip()
    id_field = f"{pack_prefix(dim_key)}id"

    # Only ids that really exist under the current selection
    packs = build_pack_queryset(selected, exclude_key=dim_key)
    valid_ids = (
        packs.filter(**{f"{id_field}__isnull": False})
        .values_list(id_field, flat=True)
        .distinct()
    )

    rows = cfg["model"].objects.filter(deleted=False, id__in=valid_ids)
    total = rows.count()

    # Big list still needs a keyword, small list is served straight away
    if total > BIG_ROWS and len(keyword) < SEARCH_MIN_CHARS:
        return {
            "dim": dim_key,
            "label": cfg["label"],
            "total": total,
            "need_search": True,
            "search_min": SEARCH_MIN_CHARS,
            "truncated": False,
            "items": [],
        }

    if keyword:
        rows = rows.filter(Q(code__icontains=keyword) | Q(name__icontains=keyword))
        total = rows.count()

    # Pull one extra row to detect truncation
    page = list(rows.order_by("code", "name").values("id", "code", "name")[: limit + 1])
    truncated = len(page) > limit
    page = page[:limit]

    items = []
    for row in page:
        code = row["code"] or ""
        name = row["name"] or ""
        items.append(
            {
                "id": row["id"],
                "code": code,
                "name": name,
                "text": f"{code} - {name}".strip(" -"),
            }
        )

    return {
        "dim": dim_key,
        "label": cfg["label"],
        "total": total,
        "need_search": False,
        "search_min": SEARCH_MIN_CHARS,
        "truncated": truncated,
        "items": items,
    }