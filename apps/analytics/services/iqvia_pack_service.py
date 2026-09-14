import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.analytics.models.iqvia_models import IQV_ITMATrans, IQV_Pack
from apps.analytics.models.iqvia_import import (
    STATE_FAILED,
    STATE_SUCCESS,
)
from apps.analytics.services.iqvia_i18n import (
    dim_labels,
    part,
    render_parts,
    tr_format,
)
from apps.analytics.services.iqvia_commit_service import (
    SAMPLE_LIMIT,
    _write_history,
    build_archive,
    build_parent_maps,
    check_parent_tables,
    unique_slug,
)
from apps.analytics.services.iqvia_import_service import (
    IMPORT_DIMENSIONS,
    PARSE_DASH,
    PARSE_DASH_SPACE,
    build_ethstat_name,
    build_slug,
    clean_text,
    get_import_dimension,
    is_blank,
    normalize_header,
    split_code_name,
)

# Scalar pack columns, model field plus the fallback when the cell is empty
PACK_SCALAR = {
    "Pack Size": ("size", "1.00"),
    "Pack Strength": ("strength", ""),
    "Pack Volume": ("volume", ""),
    "Pack Molecule String": ("molstring", ""),
    "Pack Launch Date": ("launched", ""),
}

# Char limits taken straight from the migration
PACK_MAX_LEN = {"strength": 10, "volume": 10, "molstring": 500, "key": 255}

# Quarter closing dates, IQVIA reports on the last day of the quarter
QUARTER_END = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}

# Restated values below this gap are treated as unchanged
ITMA_TOLERANCE = Decimal("0.1")

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%b %Y", "%Y-%m-%d %H:%M:%S"]


# Company code hides in the Product suffix, "3TC - GSK" gives GSK
def company_code_from_product(raw_product):
    text = clean_text(raw_product)
    if " - " in text:
        return text.rsplit(" - ", 1)[-1].strip().upper()
    return ""


# Decimal or None, thousand separators are stripped first
def to_decimal(value, fallback=None):
    text = str(value).replace(",", "").strip()
    if text in ("", "-", "nan", "None"):
        return fallback
    try:
        return Decimal(text)
    except InvalidOperation:
        return fallback


# Date or None, IQVIA is not consistent about the format
def to_date(value):
    text = clean_text(value)
    if is_blank(text):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


# Closing date and year of a quarter label like "QTR 1/2020"
def quarter_to_date(quarter):
    match = re.search(r"QTR\s*(\d)\s*/\s*(\d{4})", str(quarter), re.IGNORECASE)
    if not match:
        return None, None
    number = int(match.group(1))
    year = int(match.group(2))
    if number not in QUARTER_END:
        return None, None
    return datetime.strptime(f"{year}-{QUARTER_END[number]}", "%Y-%m-%d").date(), year


# Cut a value down to the column width
def fit(value, field):
    limit = PACK_MAX_LEN.get(field)
    text = clean_text(value)
    return text[:limit] if limit else text


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: pack_parent_value                                   ║
# ║  Type: Service function                                    ║
# ║  Purpose: Lookup key for one pack parent, parse applied    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_pack_service.py       ║
# ║  Created: Sep/02-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Merge hands over raw cells, commit_dimension gets them pre parsed
def pack_parent_value(raw, parent):
    text = clean_text(pick(raw, parent["column"]) or "")
    if not text:
        return ""

    # Ethstat is stored as "Title Case (Group)", see build_ethstat_name
    if parent["dim"] == "ethstat":
        group = clean_text(pick(raw, "Ethical Status Group") or "")
        return build_ethstat_name(text, group) if group else text

    # OTC4 arrives as "98A2Z - NOT APPL.NON-ETHIC.REPORT"
    if parent["parse"] in (PARSE_DASH_SPACE, PARSE_DASH):
        code, name = split_code_name(text, parent["parse"])
        return (code or text) if parent["on"] == "code" else (name or text)

    return text


# Column lookup that ignores case and punctuation
def pick(raw, wanted):
    target = normalize_header(wanted)
    for key, value in raw.items():
        if normalize_header(key) == target:
            return value
    return None


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: merge_pack_rows                                     ║
# ║  Type: Service function                                    ║
# ║  Purpose: Outer join every staged pack slice on Pack       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_pack_service.py       ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Blank cells never overwrite, that is what makes a partial upload safe
def merge_pack_rows(parsed_list):
    # Attributes live per pack name, Product decides how many packs that name is
    attrs = {}
    variants = {}
    columns = set()
    parts = []
    totals = {"rows_read": 0, "rows_noise": 0, "rows_duplicate": 0}

    for parsed in parsed_list:
        columns.update(parsed.get("columns") or [])
        parts.append(parsed.get("part") or "unknown")
        for key in totals:
            totals[key] += parsed.get(key, 0)

        for row in parsed.get("rows") or []:
            base = str(row.get("name") or "").strip().upper()
            if not base:
                continue
            bucket = attrs.setdefault(base, {"name": row["name"], "raw": {}})
            product = None
            for column, value in (row.get("raw") or {}).items():
                if is_blank(value):
                    continue
                if normalize_header(str(column)) == "PRODUCT":
                    product = clean_text(value)
                    continue
                # Blank cells never overwrite, that is what keeps a merge safe
                bucket["raw"][column] = value
            if product:
                variants.setdefault(base, {})[
                    company_code_from_product(product)
                ] = product

    merged = {}
    for base, bucket in attrs.items():
        found = variants.get(base)
        if not found:
            merged[base] = {"name": bucket["name"], "raw": dict(bucket["raw"])}
            continue
        for code, product in found.items():
            raw = dict(bucket["raw"])
            raw["Product"] = product
            merged[f"{base}-{code}" if code else base] = {
                "name": bucket["name"], "raw": raw,
            }

    return merged, columns, parts, totals


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: commit_pack                                         ║
# ║  Type: Service function                                    ║
# ║  Purpose: Insert or update packs from many merged slices   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_pack_service.py       ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def commit_pack(parsed_list, user=None, file_names=None, batch=None, dry_run=False):
    started = timezone.now()
    cfg = get_import_dimension("pack")
    file_names = file_names or []

    empty_parents = check_parent_tables("pack")
    if empty_parents:
        labels = ", ".join(p["label"] for p in empty_parents)
        parts = [part("parent_empty", labels=labels)]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "empty_parents": empty_parents,
        }

    merged, columns, parts, totals = merge_pack_rows(parsed_list)
    normalized = {normalize_header(c) for c in columns}
    has_product = normalize_header("Product") in normalized

    # Merging 40k packs is expensive, skip it while slices are still missing
    missing_early = [
        part for column, part in _pack_part_map().items()
        if normalize_header(column) not in normalized
    ]
    if missing_early:
        parts = [part("pack_parts_missing", n=len(missing_early),
                      parts=", ".join(missing_early))]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": 0, "orphan_parent": "", "orphan_field": "",
            "missing_parts": missing_early,
            "parts_loaded": parts,
        }

    # Identity is name plus company code, that is exactly what key holds
    existing = {
        str(row.key or row.name or "").strip().upper(): row
        for row in IQV_Pack.objects.filter(deleted=False)
    }
    new_names = [key for key in merged if key not in existing]

    # A brand new pack without Product would land without any id at all
    if new_names and not has_product:
        parts = [part("pack_no_product", n=len(new_names))]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": len(new_names),
            "orphan_parent": "product",
            "orphan_field": "Product",
            "blocked_sample": [{"row": n, "parent": "product", "value": "",
                                "reason": "kolom Product tidak ada"} for n in new_names[:SAMPLE_LIMIT]],
        }

    parent_maps = build_parent_maps(cfg)
    active_parents = [
        p for p in cfg["parents"] if normalize_header(p["column"]) in normalized
    ]
    active_scalars = {
        column: spec for column, spec in PACK_SCALAR.items()
        if normalize_header(column) in normalized
    }

    used_slugs = set(
        IQV_Pack.objects.exclude(slug=None).values_list("slug", flat=True)
    )

    to_insert = []
    to_update = []
    to_archive = []
    blocked = []
    rows_same = 0
    compare_fields = [p["field"] for p in active_parents] + [
        spec[0] for spec in active_scalars.values()
    ]

    for match_key, bucket in merged.items():
        raw = bucket["raw"]
        payload = {}
        block = None

        for parent in active_parents:
            value = pack_parent_value(raw, parent)
            if not value:
                continue
            found = parent_maps[parent["dim"]].get(value.upper())
            if found is None:
                block = {"row": match_key, "parent": parent["dim"],
                         "value": value, "reason": "tidak ketemu"}
                break
            payload[parent["field"]] = found

        if block:
            blocked.append(block)
            continue

        if "product_id" not in payload and match_key not in existing:
            blocked.append({"row": match_key, "parent": "product",
                            "value": "", "reason": "kosong"})
            continue

        for column, spec in active_scalars.items():
            field, fallback = spec
            value = pick(raw, column)
            if is_blank(value):
                value = fallback
            if field == "size":
                payload[field] = to_decimal(value, Decimal("1.00"))
            elif field == "launched":
                payload[field] = to_date(value)
            else:
                payload[field] = fit(value, field)

        if has_product:
            code = company_code_from_product(pick(raw, "Product") or "")
            payload["key"] = fit(
                f"{bucket['name']}-{code}" if code else bucket["name"], "key"
            )

        current = existing.get(match_key)
        if current is None:
            new_row = IQV_Pack(name=bucket["name"], **payload)
            new_row.slug = unique_slug(build_slug(match_key), used_slugs)
            new_row.status = 1
            new_row.deleted = False
            new_row.cby = user
            to_insert.append(new_row)
            continue

        changed = [
            field for field in payload
            if getattr(current, field) != payload[field]
        ]
        if not changed:
            rows_same += 1
            continue

        if cfg["archive"]:
            to_archive.append(build_archive(current, cfg, user, used_slugs))
        for field, value in payload.items():
            setattr(current, field, value)
        current.uat = timezone.now()
        current.uby = user
        to_update.append(current)

    if blocked:
        parents_hit = sorted({b["parent"] for b in blocked})
        labels = dim_labels(parents_hit, IMPORT_DIMENSIONS)
        missing_values = sorted({b["value"] for b in blocked if b["value"]})
        preview = ", ".join(missing_values[:5])
        if len(missing_values) > 5:
            preview += tr_format("msg_and_others",
                                 {"n": len(missing_values) - 5})
        parts = [part("orphan_packs", n=len(blocked), labels=labels)]
        if preview:
            parts.append(part("not_registered", preview=preview))
        result = {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": len(blocked),
            "orphan_parent": parents_hit[0],
            "orphan_field": labels,
            "missing_values": missing_values,
            "blocked_sample": blocked[:SAMPLE_LIMIT],
        }
        _write_history(result, cfg, "pack", _fake_parsed(totals, columns, parts),
                       user, ", ".join(file_names), batch, started, dry_run)
        return result

    update_fields = list(dict.fromkeys(compare_fields + ["key", "uat", "uby"]))
    update_fields = [f for f in update_fields if hasattr(IQV_Pack, f) or f.endswith("_id")]

    if not dry_run:
        with transaction.atomic():
            if to_archive:
                IQV_Pack.objects.bulk_create(to_archive, batch_size=500)
            if to_insert:
                IQV_Pack.objects.bulk_create(to_insert, batch_size=500)
            if to_update:
                IQV_Pack.objects.bulk_update(to_update, update_fields, batch_size=500)

    missing_parts = [
        part for column, part in _pack_part_map().items()
        if normalize_header(column) not in normalized
    ]

    # Pack must arrive complete, a half filled batch would leave gaps
    if missing_parts:
        parts = [part("pack_parts_missing", n=len(missing_parts),
                      parts=", ".join(missing_parts))]
        result = {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": 0, "orphan_parent": "", "orphan_field": "",
            "missing_parts": missing_parts,
            "parts_loaded": parts,
        }
        _write_history(result, cfg, "pack", _fake_parsed(totals, columns, parts),
                       user, ", ".join(file_names), batch, started, dry_run)
        return result

    msg_parts = [part("pack_committed", insert=len(to_insert),
                      update=len(to_update))]
    if to_archive:
        msg_parts.append(part("rows_archived", archive=len(to_archive)))

    result = {
        "state": STATE_SUCCESS,
        "message": render_parts(msg_parts),
        "msg_parts": msg_parts,
        "rows_insert": len(to_insert),
        "rows_update": len(to_update),
        "rows_same": rows_same,
        "rows_archive": len(to_archive),
        "orphan_rows": 0,
        "orphan_parent": "",
        "orphan_field": "",
        "missing_parts": missing_parts,
        "parts_loaded": parts,
        "dry_run": dry_run,
    }
    _write_history(result, cfg, "pack", _fake_parsed(totals, columns, parts),
                   user, ", ".join(file_names), batch, started, dry_run)
    return result


# Column to slice name, mirrors PACK_PARTS without the Pack key column
def _pack_part_map():
    from apps.analytics.services.iqvia_import_service import PACK_PARTS

    return PACK_PARTS


# History writer expects a parse result shape, build one from the totals
def _fake_parsed(totals, columns, parts):
    return {
        "rows_read": totals["rows_read"],
        "rows_clean": totals["rows_read"] - totals["rows_noise"],
        "rows_noise": totals["rows_noise"],
        "rows_duplicate": totals["rows_duplicate"],
        "columns": sorted(columns),
        "code_source": "n/a",
        "parts": parts,
    }


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: commit_itma                                         ║
# ║  Type: Service function                                    ║
# ║  Purpose: Insert or restate quarterly ITMA transactions    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_pack_service.py       ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Matching is name plus quarter, name is the pack key
def commit_itma(parsed, user=None, file_name="", batch=None, dry_run=False):
    started = timezone.now()
    cfg = get_import_dimension("itmatrans")

    empty_parents = check_parent_tables("itmatrans")
    if empty_parents:
        labels = ", ".join(p["label"] for p in empty_parents)
        parts = [part("parent_empty", labels=labels)]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "empty_parents": empty_parents,
        }

    pack_map = {
        str(key or "").strip().upper(): pack_id
        for pack_id, key in IQV_Pack.objects.filter(deleted=False).values_list("id", "key")
        if key
    }

    # values_list keeps 80k rows as tuples, model instances here cost minutes
    existing = {}
    for row_id, name, quarter, unit, valuehna in IQV_ITMATrans.objects.filter(
        deleted=False
    ).values_list("id", "name", "quarter", "unit", "valuehna"):
        key = f"{str(name or '').upper()}_{str(quarter or '').upper()}"
        existing[key] = (row_id, unit, valuehna)

    used_slugs = set(
        IQV_ITMATrans.objects.exclude(slug=None).values_list("slug", flat=True)
    )

    to_insert = []
    to_update = []
    to_archive = []
    blocked = []
    changed = {}
    rows_same = 0
    rows_skipped = 0
    batch_seen = set()

    for row in parsed.get("rows") or []:
        raw = row["raw"]
        quarter = clean_text(pick(raw, "Quarter") or "")
        if not quarter.upper().startswith("QTR"):
            rows_skipped += 1
            continue

        code = company_code_from_product(pick(raw, "Product") or "")
        name = f"{row['name']}-{code}" if code else row["name"]
        upper_name = name.upper()

        unit = to_decimal(pick(raw, "Units"))
        value_hna = to_decimal(pick(raw, "Values HNA"))
        if unit is None or value_hna is None:
            rows_skipped += 1
            continue

        pack_id = pack_map.get(upper_name)
        if pack_id is None:
            blocked.append({"row": name, "parent": "pack",
                            "value": name, "reason": "key tidak ketemu"})
            continue

        unique_key = f"{upper_name}_{quarter.upper()}"
        # Pivot exports repeat a pack quarter under several Calendar Year labels
        if unique_key in batch_seen:
            rows_skipped += 1
            continue
        batch_seen.add(unique_key)

        current = existing.get(unique_key)
        if current is None:
            date_value, year_value = quarter_to_date(quarter)
            clean_quarter = re.sub(r"[^a-z0-9]+", "", quarter.lower())
            new_row = IQV_ITMATrans(
                name=name, quarter=quarter, unit=unit, valuehna=value_hna,
                date=date_value, year=year_value, pack_id=pack_id,
            )
            new_row.slug = unique_slug(f"{build_slug(name)}-{clean_quarter}", used_slugs)
            new_row.status = 1
            new_row.deleted = False
            new_row.cby = user
            to_insert.append(new_row)
            continue

        row_id, old_unit, old_value = current
        old_unit = old_unit or Decimal("0")
        old_value = old_value or Decimal("0")
        if abs(old_unit - unit) <= ITMA_TOLERANCE and abs(old_value - value_hna) <= ITMA_TOLERANCE:
            rows_same += 1
            continue
        changed[row_id] = (unit, value_hna, pack_id)

    if blocked:
        missing_values = sorted({b["value"] for b in blocked})
        preview = ", ".join(missing_values[:5])
        if len(missing_values) > 5:
            preview += tr_format("msg_and_others",
                                 {"n": len(missing_values) - 5})
        parts = [part("orphan_itma", n=len(blocked))]
        if preview:
            parts.append(part("not_registered", preview=preview))
        result = {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": len(blocked),
            "orphan_parent": "pack",
            "orphan_field": "Pack",
            "missing_values": missing_values,
            "blocked_sample": blocked[:SAMPLE_LIMIT],
        }
        _write_history(result, cfg, "itmatrans", parsed, user, file_name,
                       batch, started, dry_run)
        return result

    # Full objects only for rows that really changed, and only when writing.
    # build_archive touches every field, deferred ones would fire a query each.
    if changed and not dry_run:
        ids = list(changed)
        for start in range(0, len(ids), 5000):
            for current in IQV_ITMATrans.objects.filter(id__in=ids[start:start + 5000]):
                unit, value_hna, pack_id = changed[current.id]
                if cfg["archive"]:
                    to_archive.append(build_archive(current, cfg, user, used_slugs))
                current.unit = unit
                current.valuehna = value_hna
                current.pack_id = pack_id
                current.uat = timezone.now()
                current.uby = user
                to_update.append(current)

        with transaction.atomic():
            if to_archive:
                IQV_ITMATrans.objects.bulk_create(to_archive, batch_size=1000)
            if to_insert:
                IQV_ITMATrans.objects.bulk_create(to_insert, batch_size=1000)
            if to_update:
                IQV_ITMATrans.objects.bulk_update(
                    to_update, ["unit", "valuehna", "pack_id", "uat", "uby"],
                    batch_size=1000,
                )
    elif not dry_run and to_insert:
        with transaction.atomic():
            IQV_ITMATrans.objects.bulk_create(to_insert, batch_size=1000)

    rows_update = len(changed)
    rows_archive = rows_update if cfg["archive"] else 0

    # Skipped rows are parser noise, deliberately left out of the sentence
    msg_parts = [part("itma_committed", insert=len(to_insert), update=rows_update)]
    if rows_archive:
        msg_parts.append(part("values_archived", archive=rows_archive))

    result = {
        "state": STATE_SUCCESS,
        "message": render_parts(msg_parts),
        "msg_parts": msg_parts,
        "rows_insert": len(to_insert),
        "rows_update": rows_update,
        "rows_same": rows_same,
        "rows_archive": rows_archive,
        "rows_skipped": rows_skipped,
        "orphan_rows": 0,
        "orphan_parent": "",
        "orphan_field": "",
        "dry_run": dry_run,
    }
    _write_history(result, cfg, "itmatrans", parsed, user, file_name,
                   batch, started, dry_run)
    return result