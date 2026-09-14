import uuid

from django.db import connection, transaction
from django.utils import timezone

from apps.analytics.models.iqvia_import import (
    STATE_FAILED,
    STATE_SUCCESS,
    DataCommitHistory,
)
from apps.analytics.services.iqvia_i18n import (
    dim_label,
    dim_labels,
    part,
    render_parts,
    tr,
    tr_format,
)
from apps.analytics.services.iqvia_import_service import (
    COMPANY_CODE_LEN,
    IMPORT_DIMENSIONS,
    PARSE_DASH,
    PARSE_DASH_SPACE,
    PARSE_ITMA,
    PARSE_PACK,
    PARSE_PRODUCT,
    build_slug,
    get_import_dimension,
    get_parent_chain,
)

# Pack and ITMA need a merge step, handled in their own service
DEFERRED_PARSE = [PARSE_PACK, PARSE_ITMA]

# Sample size kept in the history detail column
SAMPLE_LIMIT = 20

# Slug column is unique and 255 wide
SLUG_MAX = 255


# Field names the model really has
def model_fields(model):
    return {f.attname for f in model._meta.concrete_fields}


# True only when the file itself carries a code for this dimension
def supplies_code(cfg):
    if not cfg.get("store_code", True):
        return False
    if cfg["code_col"]:
        return True
    return cfg["parse"] in (PARSE_DASH, PARSE_DASH_SPACE)


# Fields compared to decide update or skip
def get_compare_fields(cfg):
    available = model_fields(cfg["model"])
    fields = ["name"]
    if supplies_code(cfg):
        fields.append("code")
    fields += [p["field"] for p in cfg["parents"]]
    return [f for f in fields if f in available]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: check_parent_tables                                 ║
# ║  Type: Service function                                    ║
# ║  Purpose: Block the file when a parent table is still empty║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_commit_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Returns the list of ancestors that have no data yet
def check_parent_tables(dim_key):
    empty = []
    for parent_key in get_parent_chain(dim_key):
        parent_cfg = IMPORT_DIMENSIONS[parent_key]
        if not parent_cfg["model"].objects.filter(deleted=False).exists():
            empty.append({
                "key": parent_key,
                "label": dim_label(parent_key, parent_cfg["label"]),
            })
    return empty


# Lookup table per parent, archived rows are ignored
def build_parent_maps(cfg):
    maps = {}
    for parent in cfg["parents"]:
        parent_cfg = IMPORT_DIMENSIONS[parent["dim"]]
        rows = parent_cfg["model"].objects.filter(deleted=False).values(
            "id", parent["on"]
        )
        maps[parent["dim"]] = {
            str(r[parent["on"]]).strip().upper(): r["id"]
            for r in rows
            if r[parent["on"]] not in [None, ""]
        }
    return maps


# Resolve one row against the parent maps
# Returns the foreign keys plus the reason it is blocked, if any
def resolve_row_parents(row, cfg, parent_maps):
    values = {}
    blocked = None
    for parent in cfg["parents"]:
        raw = str(row["parents"].get(parent["dim"], "")).strip()
        if not raw:
            if parent["required"]:
                blocked = {
                    "row": row["match"],
                    "parent": parent["dim"],
                    "value": "",
                    "reason": "kosong",
                }
                break
            values[parent["field"]] = None
            continue
        found = parent_maps[parent["dim"]].get(raw.upper())
        if found is None:
            blocked = {
                "row": row["match"],
                "parent": parent["dim"],
                "value": raw,
                "reason": "tidak ketemu",
            }
            break
        values[parent["field"]] = found
    return values, blocked


# Live rows keyed by the match field, archived rows are ignored
def load_existing(cfg):
    rows = cfg["model"].objects.filter(deleted=False)
    return {
        str(getattr(r, cfg["match"]) or "").strip().upper(): r for r in rows
    }


# Slug that no other row is using yet
def unique_slug(base, used):
    base = (base or "row")[:SLUG_MAX]
    if base not in used:
        used.add(base)
        return base
    counter = 2
    while True:
        candidate = f"{base[:SLUG_MAX - 6]}-{counter}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        counter += 1


# True when any compared field differs
def has_changed(instance, payload, fields):
    for field in fields:
        if getattr(instance, field) != payload.get(field):
            return True
    return False


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_archive                                       ║
# ║  Type: Service function                                    ║
# ║  Purpose: Copy the old values into a soft deleted row      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_commit_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# The live row keeps its id so every child foreign key stays valid
def build_archive(instance, cfg, user, used_slugs):
    model = cfg["model"]
    archive = model()
    for field in model._meta.concrete_fields:
        if field.primary_key:
            continue
        setattr(archive, field.attname, getattr(instance, field.attname))
    archive.deleted = True
    archive.status = 0
    archive.dat = timezone.now()
    archive.dby = user
    base = f"{instance.slug or build_slug(instance.name)}-hist-{uuid.uuid4().hex[:8]}"
    archive.slug = unique_slug(base, used_slugs)
    return archive


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: backfill_company_code                               ║
# ║  Type: Service function                                    ║
# ║  Purpose: Fill company code from the product name suffix   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_commit_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# IQVIA hides the company code in "3TC - GSK", company export has no code
def backfill_company_code(rows, user, dry_run=False):
    from apps.analytics.models.iqvia_models import IQV_Company

    wanted = {}
    for row in rows:
        company = str(row["parents"].get("company", "")).strip().upper()
        code = str(row.get("code", "")).strip().upper()
        if company and code and len(code) <= COMPANY_CODE_LEN:
            wanted[company] = code

    if not wanted:
        return 0, 0

    filled = 0
    still_empty = 0
    to_update = []
    for company in IQV_Company.objects.filter(deleted=False):
        code = wanted.get(str(company.name).strip().upper())
        if code and company.code != code:
            company.code = code
            company.uat = timezone.now()
            company.uby = user
            to_update.append(company)
            filled += 1
        elif not company.code and not code:
            still_empty += 1

    if to_update and not dry_run:
        IQV_Company.objects.bulk_update(to_update, ["code", "uat", "uby"], batch_size=500)
    return filled, still_empty


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: commit_dimension                                    ║
# ║  Type: Service function                                    ║
# ║  Purpose: Insert or update one dimension from parsed rows  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_commit_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# dry_run True returns the same counters without touching the database
# staged_names: {dim_key: set(nama upper)} dari file lain di batch yang sama
def commit_dimension(parsed, dim_key, user=None, file_name="", batch=None,
                     dry_run=False, staged_names=None):
    started = timezone.now()
    cfg = get_import_dimension(dim_key)

    if cfg is None:
        parts = [part("unknown_dimension")]
        return {"state": STATE_FAILED, "message": render_parts(parts),
                "msg_parts": parts}

    if cfg["parse"] in DEFERRED_PARSE:
        parts = [part("multi_file_flow",
                      label=dim_label(dim_key, cfg["label"]))]
        return {"state": STATE_FAILED, "message": render_parts(parts),
                "msg_parts": parts}

    if parsed.get("error"):
        return {"state": STATE_FAILED, "message": parsed["error"]}

    # Gate 1, an ancestor table is still empty
    empty_parents = check_parent_tables(dim_key)
    if empty_parents:
        labels = ", ".join(p["label"] for p in empty_parents)
        parts = [part("parent_empty", labels=labels)]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "empty_parents": empty_parents,
        }

    parent_maps = build_parent_maps(cfg)

    # Rows waiting in the same batch count as present, id is settled on commit
    if staged_names:
        for parent in cfg["parents"]:
            queued = staged_names.get(parent["dim"])
            if not queued:
                continue
            for value in queued:
                parent_maps[parent["dim"]].setdefault(value, -1)

    existing = load_existing(cfg)
    compare_fields = get_compare_fields(cfg)
    available = model_fields(cfg["model"])

    used_slugs = set(
        cfg["model"].objects.exclude(slug=None).values_list("slug", flat=True)
    )

    payloads = []
    blocked = []

    # Gate 2, every row must resolve its required parents
    for row in parsed["rows"]:
        fk_values, block = resolve_row_parents(row, cfg, parent_maps)
        if block:
            blocked.append(block)
            continue
        payload = {"name": row["name"]}
        # A code is written only when the file actually carries one, otherwise
        # an empty cell would wipe codes that backfill_company_code filled in
        if "code" in available and supplies_code(cfg):
            payload["code"] = row["code"]
        payload.update(fk_values)
        payloads.append((row, payload))

    if blocked:
        parents_hit = sorted({b["parent"] for b in blocked})
        labels = dim_labels(parents_hit, IMPORT_DIMENSIONS)
        # Naming the values turns the error into an actionable instruction
        missing_values = sorted({b["value"] for b in blocked if b["value"]})
        preview = ", ".join(missing_values[:5])
        if len(missing_values) > 5:
            preview += tr_format("msg_and_others",
                                 {"n": len(missing_values) - 5})
        parts = [part("orphan_rows", n=len(blocked), labels=labels)]
        if preview:
            parts.append(part("not_registered", preview=preview))
        result = {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0,
            "rows_update": 0,
            "rows_same": 0,
            "rows_archive": 0,
            "orphan_rows": len(blocked),
            "orphan_parent": parents_hit[0],
            "orphan_field": labels,
            "missing_values": missing_values,
            "blocked_sample": blocked[:SAMPLE_LIMIT],
        }
        _write_history(result, cfg, dim_key, parsed, user, file_name, batch,
                       started, dry_run)
        return result

    to_insert = []
    to_archive = []
    to_update = []
    rows_same = 0

    for row, payload in payloads:
        current = existing.get(row["match"])
        if current is None:
            new_row = cfg["model"](**payload)
            new_row.slug = unique_slug(row["slug"], used_slugs)
            new_row.status = 1
            new_row.deleted = False
            new_row.cby = user
            to_insert.append(new_row)
            continue
        if not has_changed(current, payload, compare_fields):
            rows_same += 1
            continue
        if cfg["archive"]:
            to_archive.append(build_archive(current, cfg, user, used_slugs))
        for field, value in payload.items():
            setattr(current, field, value)
        current.uat = timezone.now()
        current.uby = user
        to_update.append(current)

    update_fields = list(compare_fields) + ["uat", "uby"]
    company_filled = 0
    company_empty = 0

    if not dry_run:
        with transaction.atomic():
            if to_archive:
                cfg["model"].objects.bulk_create(to_archive, batch_size=500)
            if to_insert:
                cfg["model"].objects.bulk_create(to_insert, batch_size=500)
            if to_update:
                cfg["model"].objects.bulk_update(
                    to_update, update_fields, batch_size=500
                )
            if cfg["parse"] == PARSE_PRODUCT:
                company_filled, company_empty = backfill_company_code(
                    parsed["rows"], user, dry_run=False
                )
    elif cfg["parse"] == PARSE_PRODUCT:
        company_filled, company_empty = backfill_company_code(
            parsed["rows"], user, dry_run=True
        )

    parts = [part("dim_committed", insert=len(to_insert), update=len(to_update))]
    if to_archive:
        parts.append(part("rows_archived", archive=len(to_archive)))
    if company_empty:
        parts.append(part("company_empty", n=company_empty))

    result = {
        "state": STATE_SUCCESS,
        "message": render_parts(parts),
        "msg_parts": parts,
        "rows_insert": len(to_insert),
        "rows_update": len(to_update),
        "rows_same": rows_same,
        "rows_archive": len(to_archive),
        "orphan_rows": 0,
        "orphan_parent": "",
        "orphan_field": "",
        "company_filled": company_filled,
        "company_empty": company_empty,
        "dry_run": dry_run,
    }
    _write_history(result, cfg, dim_key, parsed, user, file_name, batch,
                   started, dry_run)
    return result


# History row, skipped on a dry run
def _write_history(result, cfg, dim_key, parsed, user, file_name, batch,
                   started, dry_run):
    if dry_run:
        return
    duration = int((timezone.now() - started).total_seconds() * 1000)
    DataCommitHistory.objects.create(
        batch=batch or uuid.uuid4(),
        dimension=dim_key,
        dimension_label=cfg["label"],
        table_name=cfg["table"],
        file_name=file_name,
        rows_read=parsed.get("rows_read", 0),
        rows_clean=parsed.get("rows_clean", 0),
        rows_insert=result.get("rows_insert", 0),
        rows_update=result.get("rows_update", 0),
        rows_same=result.get("rows_same", 0),
        rows_noise=parsed.get("rows_noise", 0),
        rows_duplicate=parsed.get("rows_duplicate", 0),
        orphan_rows=result.get("orphan_rows", 0),
        orphan_field=result.get("orphan_field", ""),
        orphan_parent=result.get("orphan_parent", ""),
        state=result["state"],
        message=result.get("message", ""),
        detail={
            # Codes plus numbers, so History can be reread in any language
            "msg": result.get("msg_parts", []),
            "columns": parsed.get("columns", []),
            "code_source": parsed.get("code_source", ""),
            "rows_archive": result.get("rows_archive", 0),
            "blocked_sample": result.get("blocked_sample", []),
            "missing_values": result.get("missing_values", []),
            "company_filled": result.get("company_filled", 0),
            "company_empty": result.get("company_empty", 0),
        },
        duration_ms=duration,
        cby=user,
    )

# ============================================================
#  Name: build_has_data_map
#  Type: Service helper
#  Purpose: One round trip instead of 26 exists() calls
# ------------------------------------------------------------
#  Path: apps\analytics\services\iqvia_commit_service.py
#  Created: Sep/04-2026 by Akram
#  Updates: ?
# ============================================================
# Table names come from the model meta, never from user input
def build_has_data_map():
    keys = list(IMPORT_DIMENSIONS)
    try:
        quote = connection.ops.quote_name
        parts = [
            f"(SELECT EXISTS(SELECT 1 FROM "
            f"{quote(IMPORT_DIMENSIONS[k]['model']._meta.db_table)} "
            f"WHERE deleted = false))"
            for k in keys
        ]
        with connection.cursor() as cursor:
            cursor.execute("SELECT " + ", ".join(parts))
            return dict(zip(keys, cursor.fetchone()))
    except Exception:
        # Any backend that dislikes the union falls back to one query each
        return {
            k: IMPORT_DIMENSIONS[k]["model"].objects.filter(deleted=False).exists()
            for k in keys
        }
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_dimension_status_map                            ║
# ║  Type: Service function                                    ║
# ║  Purpose: Flag per dimension for the cascade dropdown      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_commit_service.py     ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Calendar quarter, not a rolling window. A late import still lands in the
# quarter it was run, so the badge clears on Jan 1, Apr 1, Jul 1 and Oct 1.
def quarter_of(moment):
    return moment.year, (moment.month - 1) // 3 + 1


# flag: "empty" grey badge, "warning" red badge, "ok" no badge
def get_dimension_status_map():
    now_quarter = quarter_of(timezone.localtime(timezone.now()))
    latest_by_dim = {}
    for record in DataCommitHistory.objects.filter(deleted=False).order_by(
        "dimension", "-cat", "-id"
    ):
        latest_by_dim.setdefault(record.dimension, record)

    has_data_map = build_has_data_map()
    status = {}
    for key, cfg in IMPORT_DIMENSIONS.items():
        has_data = has_data_map.get(key, False)
        record = latest_by_dim.get(key)
        # imported means committed through this module in the current quarter,
        # last quarter's import no longer counts as done
        imported = bool(
            record
            and record.state == STATE_SUCCESS
            and quarter_of(timezone.localtime(record.cat)) == now_quarter
        )
        if record and record.state == STATE_FAILED:
            flag = "warning"
            message = record.message
        elif not has_data:
            flag = "empty"
            message = tr("err_no_data_yet")
        else:
            flag = "ok"
            message = ""
        status[key] = {
            "flag": flag,
            "message": message,
            "imported": imported,
            "orphan_rows": record.orphan_rows if record else 0,
        }
    return status