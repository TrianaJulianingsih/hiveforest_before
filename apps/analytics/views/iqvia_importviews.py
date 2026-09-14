import csv
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.analytics.models.iqvia_import import (
    STATE_FAILED,
    DataCommitHistory,
    DataImportStaging,
)
from apps.analytics.services.iqvia_i18n import (
    dim_label,
    part,
    render_parts,
    tr,
    tr_format,
)
from apps.analytics.services.iqvia_commit_service import (
    build_has_data_map,
    commit_dimension,
    get_dimension_status_map,
)
from apps.analytics.services.iqvia_pack_service import commit_itma, commit_pack
from apps.analytics.services.iqvia_import_service import (
    IMPORT_DIMENSIONS,
    PACK_PARTS,
    detect_dimensions,
    resolve_import_targets,
    get_parent_chain,
    build_file_hash,
    get_display_columns,
    get_import_dimension,
    get_import_groups,
    is_valid_import_dimension,
    parse_file,
    relation_name,
)

# Pack and ITMA need their own multi file flow, see Part 3B
DEFERRED_DIMENSIONS = []

MAX_UPLOAD_MB = 25

# Staging older than this belongs to a session that never came back
STAGING_TTL_HOURS = 12

# Dimensions that never serve as a lookup parent inside a batch
NO_KEY_CACHE = ["pack", "itmatrans"]
ALLOWED_EXTENSIONS = {"csv": [".csv"], "excel": [".xlsx", ".xls"]}

# Excel header fill, HiveForest primary
XLS_HEADER_FILL = PatternFill("solid", fgColor="1A472A")


# Display text for a related row, users and master rows differ
def _relation_label(related):
    if related is None:
        return ""
    full_name = getattr(related, "get_full_name", None)
    if callable(full_name):
        return full_name() or getattr(related, "username", "") or str(related.pk)
    return getattr(related, "name", "") or str(related.pk)


# Row dict per dimension, one entry per display column
def _build_rows(page_obj, columns):
    rows = []
    for instance in page_obj:
        row = {}
        for column in columns:
            key = column["key"]
            kind = column["type"]
            if kind in ("fk", "user"):
                row[key] = _relation_label(
                    getattr(instance, relation_name(key), None)
                )
            elif kind == "date":
                value = getattr(instance, key, None)
                row[key] = value.strftime("%d %b %Y %H:%M") if value else ""
            elif kind == "status":
                row[key] = (
                    tr("val_active") if instance.status == 1 else tr("val_inactive")
                )
            else:
                value = getattr(instance, key, None)
                row[key] = "" if value is None else str(value)
        rows.append(row)
    return rows


# Short summary of the newest commit, shown above the table
def _last_commit(dim_key):
    record = (
        DataCommitHistory.objects.filter(deleted=False, dimension=dim_key)
        .order_by("-cat", "-id")
        .first()
    )
    if record is None:
        return None
    user_label = "System"
    if record.cby:
        user_label = record.cby.get_full_name() or record.cby.username
    return {
        "timestamp": record.cat.strftime("%d %b %Y %H:%M"),
        "user": user_label,
        "rows_insert": record.rows_insert,
        "rows_update": record.rows_update,
        "state": record.state,
        "message": record.message,
    }


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_menu                                   ║
# ║  Type: Function base view                                  ║
# ║  Purpose: Main page, cascade dropdown plus raw data table  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_import_menu(request):
    # A reload means the previous session is over, its staging can go
    purge_stale_staging(user=request.user)
    context = {
        "title": "IQVIA Import Data",
        "import_groups": get_import_groups(),
        "dimension_status": get_dimension_status_map(),
        "deferred_dimensions": DEFERRED_DIMENSIONS,
        "pending_map": build_pending_map(),
    }
    return render(request, "analytics/iqvia/import_menu.html", context)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_data                                   ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Paginated raw data for one dimension              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_GET
def iqvia_import_data(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_import_dimension(dim_key):
        return JsonResponse({"error": tr("err_unknown_dimension")}, status=400)

    cfg = get_import_dimension(dim_key)
    search = (request.GET.get("q") or "").strip()
    page_number = int(request.GET.get("page") or 1)
    page_size = min(int(request.GET.get("page_size") or 25), 200)

    columns = get_display_columns(dim_key)
    relations = [
        relation_name(c["key"]) for c in columns if c["type"] in ("fk", "user")
    ]
    queryset = cfg["model"].objects.filter(deleted=False)
    if relations:
        queryset = queryset.select_related(*relations)

    fields = {f.attname for f in cfg["model"]._meta.concrete_fields}
    if search:
        condition = Q(name__icontains=search)
        if "code" in fields:
            condition |= Q(code__icontains=search)
        queryset = queryset.filter(condition)

    sort_key = (request.GET.get("sort") or "").strip()
    sort_dir = (request.GET.get("dir") or "asc").strip().lower()
    valid = {c["key"] for c in columns}
    if sort_key not in valid:
        sort_key = "code" if cfg["match"] == "code" else "name"
    # Foreign keys sort by the related row name, not the raw id.
    # cby and uby point at auth.User, which has username instead of name.
    if sort_key in ("cby_id", "uby_id"):
        order_field = relation_name(sort_key) + "__username"
    elif sort_key.endswith("_id"):
        order_field = relation_name(sort_key) + "__name"
    else:
        order_field = sort_key
    queryset = queryset.order_by(
        f"-{order_field}" if sort_dir == "desc" else order_field
    )

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    parents = [
        {"key": p["dim"],
         "label": dim_label(p["dim"], IMPORT_DIMENSIONS[p["dim"]]["label"])}
        for p in cfg["parents"]
    ]
    return JsonResponse(
        {
            "dimension": dim_key,
            "label": dim_label(dim_key, cfg["label"]),
            "columns": columns,
            "rows": _build_rows(page_obj, columns),
            "parents": parents,
            "total": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "num_pages": paginator.num_pages,
            "sort": sort_key,
            "dir": sort_dir,
            "archived_count": cfg["model"].objects.filter(deleted=True).count(),
            "last_commit": _last_commit(dim_key),
            "deferred": dim_key in DEFERRED_DIMENSIONS,
        }
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_upload                                 ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Parse, validate and stage one uploaded file       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Nothing is written to the master tables here, only staged
@login_required
@require_POST
def iqvia_import_upload(request):
    dim_key = (request.POST.get("dim") or "").strip()
    file_type = (request.POST.get("file_type") or "").strip().lower()
    batch_raw = (request.POST.get("batch") or "").strip()
    uploaded = request.FILES.get("file")

    # dim_key may be a single dimension or a classification family
    if not resolve_import_targets(dim_key):
        return JsonResponse({"error": tr("err_unknown_dimension")}, status=400)

    if dim_key in DEFERRED_DIMENSIONS and dim_key in IMPORT_DIMENSIONS:
        cfg = get_import_dimension(dim_key)
        return JsonResponse(
            {
                "error": tr_format(
                    "err_deferred_flow",
                    {"label": dim_label(dim_key, cfg["label"])},
                )
            },
            status=400,
        )

    if file_type not in ALLOWED_EXTENSIONS:
        return JsonResponse({"error": tr("err_pick_file_type")}, status=400)

    if uploaded is None:
        return JsonResponse({"error": tr("err_no_file")}, status=400)

    extension = "." + uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
    if extension not in ALLOWED_EXTENSIONS[file_type]:
        return JsonResponse(
            {"error": tr_format(
                "err_extension",
                {"extensions": ", ".join(ALLOWED_EXTENSIONS[file_type])},
            )},
            status=400,
        )

    if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
        return JsonResponse(
            {"error": tr_format("err_too_large", {"mb": MAX_UPLOAD_MB})}, status=400
        )

    raw_bytes = uploaded.read()
    file_hash = build_file_hash(raw_bytes)
    batch_id = batch_raw or str(uuid.uuid4())

    # Same bytes uploaded twice in the same session, do nothing twice
    if DataImportStaging.objects.filter(
        batch=batch_id, file_hash=file_hash, deleted=False
    ).exists():
        return JsonResponse(
            {
                "duplicate": True,
                "batch": batch_id,
                "message": tr("err_duplicate_file"),
            }
        )

    # One pivot can hold several levels, take all of them
    detected, detect_error = detect_dimensions(raw_bytes, file_type, dim_key)
    if detect_error or not detected:
        return JsonResponse(
            {"error": detect_error or tr("err_no_dimension_detected")},
            status=400,
        )

    # Parents already queued in this batch should not look missing
    staged_names = build_staged_names(batch_id)
    for key in detected:
        staged_names.setdefault(key, set())

    # Keys are cached only for dimensions another file may look up
    key_cache = {}
    parsed_by_dim = {}
    previews = []
    for key in detected:
        parsed = parse_file(raw_bytes, file_type, key)
        parsed_by_dim[key] = parsed
        if parsed.get("error"):
            return JsonResponse(
                {
                    "error": (dim_label(key, IMPORT_DIMENSIONS[key]["label"])
                              + ": " + parsed["error"]),
                    "found_columns": parsed.get("found_columns"),
                    "found_cells": parsed.get("found_cells"),
                },
                status=400,
            )
        # A multi level file covers its own parents too
        staged_names[key].update(item["match"] for item in parsed["rows"])
        if key not in NO_KEY_CACHE:
            key_cache[key] = sorted(staged_names[key])
        if key == "pack":
            # Pack is judged after the row is saved, see below
            preview = {"state": STATE_FAILED, "message": "", "missing_parts": []}
        elif key == "itmatrans":
            preview = commit_itma(
                parsed, user=request.user, file_name=uploaded.name,
                batch=batch_id, dry_run=True,
            )
        else:
            preview = commit_dimension(
                parsed, key, user=request.user, file_name=uploaded.name,
                batch=batch_id, dry_run=True, staged_names=staged_names,
            )
        previews.append(
            {
                "dimension": key,
                "label": dim_label(key, IMPORT_DIMENSIONS[key]["label"]),
                "state": preview["state"],
                "message": preview["message"],
                "rows_clean": parsed["rows_clean"],
                "rows_insert": preview.get("rows_insert", 0),
                "rows_update": preview.get("rows_update", 0),
                "rows_same": preview.get("rows_same", 0),
                "rows_archive": preview.get("rows_archive", 0),
                "orphan_rows": preview.get("orphan_rows", 0),
                "orphan_field": preview.get("orphan_field", ""),
                "orphan_parent": preview.get("orphan_parent", ""),
                "missing_values": preview.get("missing_values", []),
                "missing_parts": preview.get("missing_parts", []),
            }
        )

    # Reuse what the loop above already produced, the file is big
    parsed = parsed_by_dim[detected[0]]

    uploaded.seek(0)
    try:
        staging = DataImportStaging.objects.create(
            batch=batch_id,
            dimension=detected[0],
            file=uploaded,
            file_name=uploaded.name,
            file_hash=file_hash,
            file_type=file_type,
            rows_read=parsed["rows_read"],
            columns={"columns": parsed["columns"], "dimensions": detected},
            summary={
                "dimensions": detected,
                "part": parsed.get("part"),
                "previews": previews,
                "keys": key_cache,
            },
            stage="ready",
            cby=request.user,
        )
    except IntegrityError:
        # Lost a race against a double click, the first upload already won
        return JsonResponse(
            {
                "duplicate": True,
                "batch": batch_id,
                "message": tr("err_duplicate_file"),
                "files": build_batch_state(batch_id),
                "pending": build_pending_map(batch_id),
            }
        )
    # Pack needs the row on disk first, only then can the merge see all slices
    if "pack" in detected:
        pack_preview = _pack_slice_preview(
            batch_id, None, request.user, uploaded.name
        )
        for item in previews:
            if item["dimension"] != "pack":
                continue
            item["state"] = pack_preview["state"]
            item["message"] = pack_preview["message"]
            item["rows_insert"] = pack_preview.get("rows_insert", 0)
            item["rows_update"] = pack_preview.get("rows_update", 0)
            item["rows_same"] = pack_preview.get("rows_same", 0)
            item["rows_archive"] = pack_preview.get("rows_archive", 0)
            item["missing_parts"] = pack_preview.get("missing_parts", [])
            # Without these the blocker can only ever say "Pack", never the cause
            item["orphan_rows"] = pack_preview.get("orphan_rows", 0)
            item["orphan_parent"] = pack_preview.get("orphan_parent", "")
            item["orphan_field"] = pack_preview.get("orphan_field", "")
            item["missing_values"] = pack_preview.get("missing_values", [])[:20]
        staging.summary = dict(staging.summary or {}, previews=previews)
        staging.save(update_fields=["summary"])

    # Only files actually waiting on one of the new dimensions get re-checked
    refreshed = {str(staging.id): previews}
    arrived = set(detected)
    pack_rows = []
    pack_wanted = False

    for row in DataImportStaging.objects.filter(batch=batch_id, stage="ready", deleted=False):
        if row.id == staging.id:
            continue
        stored = (row.summary or {}).get("previews") or []
        waiting = any(p.get("orphan_parent") in arrived for p in stored)

        # Pack merges 14 files, one shared preview is built after this loop so
        # the merge runs once instead of once per slice
        if all(d in ("pack", "itmatrans") for d in _staged_dimensions(row)):
            if "pack" in _staged_dimensions(row):
                pack_rows.append(row)
                pack_wanted = pack_wanted or waiting
            refreshed[str(row.id)] = stored
            continue

        if not waiting:
            refreshed[str(row.id)] = stored
            continue

        others = build_staged_names(batch_id, skip_id=row.id)
        raw_other = row.file.read()
        items = []
        for dim in _staged_dimensions(row):
            parsed_other = parse_file(raw_other, row.file_type, dim)
            if parsed_other.get("error"):
                continue
            others.setdefault(dim, set()).update(
                item["match"] for item in parsed_other["rows"]
            )
            result = commit_dimension(
                parsed_other, dim, user=request.user, file_name=row.file_name,
                batch=batch_id, dry_run=True, staged_names=others,
            )
            items.append(
                {
                    "dimension": dim,
                    "label": dim_label(dim, IMPORT_DIMENSIONS[dim]["label"]),
                    "state": result["state"],
                    "message": result["message"],
                    "rows_clean": parsed_other["rows_clean"],
                    "rows_insert": result.get("rows_insert", 0),
                    "rows_update": result.get("rows_update", 0),
                    "rows_same": result.get("rows_same", 0),
                    "rows_archive": result.get("rows_archive", 0),
                    "orphan_rows": result.get("orphan_rows", 0),
                    "orphan_field": result.get("orphan_field", ""),
                    "orphan_parent": result.get("orphan_parent", ""),
                    "missing_values": result.get("missing_values", []),
                    "missing_parts": result.get("missing_parts", []),
                }
            )
        row.summary = dict(row.summary or {}, previews=items)
        row.save(update_fields=["summary"])
        refreshed[str(row.id)] = items

    # One merge for the whole slice set, shared by every pack row
    if pack_wanted and pack_rows:
        shared = _pack_slice_preview(batch_id, None, request.user, "")
        for row in pack_rows:
            items = []
            for item in (row.summary or {}).get("previews") or []:
                if item.get("dimension") == "pack":
                    item = dict(
                        item,
                        state=shared["state"],
                        message=shared["message"],
                        rows_insert=shared.get("rows_insert", 0),
                        rows_update=shared.get("rows_update", 0),
                        rows_same=shared.get("rows_same", 0),
                        rows_archive=shared.get("rows_archive", 0),
                        missing_parts=shared.get("missing_parts", []),
                        orphan_rows=shared.get("orphan_rows", 0),
                        orphan_parent=shared.get("orphan_parent", ""),
                        orphan_field=shared.get("orphan_field", ""),
                        missing_values=shared.get("missing_values", [])[:20],
                    )
                items.append(item)
            row.summary = dict(row.summary or {}, previews=items)
            row.save(update_fields=["summary"])
            refreshed[str(row.id)] = items

    return JsonResponse(
        {
            "batch": batch_id,
            "staging_id": staging.id,
            "refreshed": refreshed,
            "dimension": detected[0],
            "label": ", ".join(
                dim_label(k, IMPORT_DIMENSIONS[k]["label"]) for k in detected
            ),
            "file_name": uploaded.name,
            "detected": detected,
            "previews": previews,
            "files": build_batch_state(batch_id),
            "pending": build_pending_map(batch_id),
        }
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_commit                                 ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Write the staged file into the master table       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_POST
def iqvia_import_commit(request):
    batch_id = (request.POST.get("batch") or "").strip()
    if not batch_id:
        return JsonResponse({"error": tr("err_no_batch")}, status=400)

    staged = list(
        DataImportStaging.objects.filter(
            batch=batch_id, stage="ready", deleted=False
        ).order_by("id")
    )
    if not staged:
        return JsonResponse({"error": tr("err_nothing_to_submit")}, status=400)

    # One file can feed several levels, one level can span several files
    by_dimension = {}
    for row in staged:
        for dim in _staged_dimensions(row):
            by_dimension.setdefault(dim, []).append(row)

    # Parents first, otherwise a child would never find its foreign key
    ordered = sorted(by_dimension, key=lambda k: IMPORT_DIMENSIONS[k]["level"])

    results = []
    failed_rows = set()

    # One row can feed several levels, a FieldFile only reads to EOF once
    raw_cache = {}
    lost = []
    for row in staged:
        try:
            raw_cache[row.id] = row.file.read()
        except (FileNotFoundError, OSError, ValueError):
            lost.append(row)

    # A staging row without its file on disk can never be committed
    if lost:
        for row in lost:
            row.delete()
        names = ", ".join(row.file_name for row in lost)
        return JsonResponse(
            {
                "error": tr("err_staging_file_lost",
                            f"File staging hilang dari disk: {names}. Silakan upload ulang."),
                "files": build_batch_state(batch_id),
                "pending": build_pending_map(batch_id),
            },
            status=400,
        )

    for dim_key in ordered:
        rows = by_dimension[dim_key]
        parsed_list = []
        parse_error = None
        for row in rows:
            parsed = parse_file(raw_cache[row.id], row.file_type, dim_key)
            if parsed.get("error"):
                parse_error = parsed["error"]
                break
            parsed_list.append(parsed)

        if parse_error:
            results.append(
                {
                    "dimension": dim_key,
                    "label": dim_label(dim_key, IMPORT_DIMENSIONS[dim_key]["label"]),
                    "result": {"state": STATE_FAILED, "message": parse_error},
                }
            )
            failed_rows.update(row.id for row in rows)
            continue

        names = ", ".join(row.file_name for row in rows)
        if dim_key == "pack":
            result = commit_pack(
                parsed_list, user=request.user,
                file_names=[row.file_name for row in rows],
                batch=batch_id, dry_run=False,
            )
        elif dim_key == "itmatrans":
            result = commit_itma(
                parsed_list[0], user=request.user, file_name=names,
                batch=batch_id, dry_run=False,
            )
        else:
            result = commit_dimension(
                parsed_list[0], dim_key, user=request.user, file_name=names,
                batch=batch_id, dry_run=False,
            )

        results.append(
            {
                "dimension": dim_key,
                "label": dim_label(dim_key, IMPORT_DIMENSIONS[dim_key]["label"]),
                "result": result,
            }
        )
        if result["state"] == STATE_FAILED:
            failed_rows.update(row.id for row in rows)

    # A file is only dropped when every dimension inside it succeeded
    for row in staged:
        if row.id not in failed_rows:
            row.file.delete(save=False)
            row.delete()

    failed = [r for r in results if r["result"]["state"] == STATE_FAILED]
    child_dims = []
    for dim_key in ordered:
        child_dims += [
            {"key": key, "label": dim_label(key, cfg["label"])}
            for key, cfg in IMPORT_DIMENSIONS.items()
            if any(p["dim"] == dim_key for p in cfg["parents"])
            and key not in ordered
        ]

    return JsonResponse(
        {
            "batch": batch_id,
            "results": results,
            "failed_count": len(failed),
            "child_dimensions": child_dims,
            "files": build_batch_state(batch_id),
            "dimension_status": get_dimension_status_map(),
            "pending": build_pending_map(batch_id),
        }
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_cancel                                 ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Drop every staged file for a batch                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Nothing was written to the master tables yet, so there is no rollback
@login_required
@require_POST
def iqvia_import_cancel(request):
    batch_id = (request.POST.get("batch") or "").strip()
    staging_id = (request.POST.get("staging_id") or "").strip()
    if not batch_id:
        return JsonResponse({"error": tr("err_no_batch")}, status=400)

    staged = DataImportStaging.objects.filter(batch=batch_id, deleted=False)
    # One id means drop a single file, no id means drop the whole batch
    if staging_id:
        staged = staged.filter(id=staging_id)

    removed = staged.count()
    for row in staged:
        row.file.delete(save=False)
    staged.delete()

    return JsonResponse(
        {
            "cancelled": True,
            "batch": batch_id,
            "removed": removed,
            "files": build_batch_state(batch_id),
            "pending": build_pending_map(batch_id),
        }
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_history                                ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Commit log for the History tab, newest first      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_GET
def iqvia_import_history(request):
    dim_key = (request.GET.get("dim") or "").strip()
    page_number = int(request.GET.get("page") or 1)
    page_size = min(int(request.GET.get("page_size") or 20), 100)

    search = (request.GET.get("q") or "").strip()

    queryset = DataCommitHistory.objects.filter(deleted=False).select_related("cby")
    if dim_key:
        queryset = queryset.filter(dimension=dim_key)
    if search:
        queryset = queryset.filter(
            Q(dimension_label__icontains=search)
            | Q(file_name__icontains=search)
            | Q(message__icontains=search)
            | Q(cby__first_name__icontains=search)
            | Q(cby__last_name__icontains=search)
            | Q(cby__username__icontains=search)
        )

    # Column key to the model field it actually orders on
    SORT_FIELDS = {
        "timestamp": "cat",
        "dimension_label": "dimension_label",
        "file_name": "file_name",
        "user": "cby__username",
        "rows_insert": "rows_insert",
        "rows_update": "rows_update",
        "rows_same": "rows_same",
        "orphan_rows": "orphan_rows",
        "state": "state",
    }
    sort_key = (request.GET.get("sort") or "").strip()
    sort_dir = (request.GET.get("dir") or "desc").strip().lower()
    if sort_key not in SORT_FIELDS:
        sort_key = "timestamp"
    order_field = SORT_FIELDS[sort_key]
    # id breaks ties, without it pagination can repeat or drop a row
    queryset = queryset.order_by(
        f"-{order_field}" if sort_dir == "desc" else order_field, "-id"
    )

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    rows = []
    for record in page_obj:
        user_label = "System"
        if record.cby:
            user_label = record.cby.get_full_name() or record.cby.username
        rows.append(
            {
                "id": record.id,
                # Every dimension in one submit shares this, the Commit view groups on it
                "batch": str(record.batch),
                "dimension": record.dimension,
                "dimension_label": record.dimension_label,
                "file_name": record.file_name,
                "timestamp": record.cat.strftime("%d %b %Y %H:%M"),
                "date": record.cat.strftime("%d %b %Y"),
                "time": record.cat.strftime("%H:%M"),
                "user": user_label,
                "rows_insert": record.rows_insert,
                "rows_update": record.rows_update,
                "rows_same": record.rows_same,
                "rows_archive": (record.detail or {}).get("rows_archive", 0),
                "rows_noise": record.rows_noise,
                "rows_duplicate": record.rows_duplicate,
                "orphan_rows": record.orphan_rows,
                "state": record.state,
                "message": record.message,
                # Codes plus numbers, the browser rebuilds the sentence.
                # Empty on rows written before this existed, message is the fallback.
                "msg": (record.detail or {}).get("msg", []),
                "missing_values": (record.detail or {}).get("missing_values", []),
            }
        )

    return JsonResponse(
        {
            "rows": rows,
            "total": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "num_pages": paginator.num_pages,
            "sort": sort_key,
            "dir": sort_dir,
        }
    )

# Queryset shared by the table view and the export view
def _dimension_queryset(dim_key, columns, search):
    cfg = get_import_dimension(dim_key)
    relations = [
        relation_name(c["key"]) for c in columns if c["type"] in ("fk", "user")
    ]
    queryset = cfg["model"].objects.filter(deleted=False)
    if relations:
        queryset = queryset.select_related(*relations)

    fields = {f.attname for f in cfg["model"]._meta.concrete_fields}
    if search:
        condition = Q(name__icontains=search)
        if "code" in fields:
            condition |= Q(code__icontains=search)
        queryset = queryset.filter(condition)

    order_field = "code" if cfg["match"] == "code" else "name"
    return queryset.order_by(order_field)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_export                                 ║
# ║  Type: File download function base view                    ║
# ║  Purpose: Send the raw data table as xlsx or csv           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
@require_GET
def iqvia_import_export(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_import_dimension(dim_key):
        return HttpResponse(tr("err_unknown_dimension"), status=400)

    file_format = (request.GET.get("format") or "xlsx").strip().lower()
    if file_format not in ("xlsx", "csv"):
        file_format = "xlsx"

    cfg = get_import_dimension(dim_key)
    columns = get_display_columns(dim_key)
    queryset = _dimension_queryset(dim_key, columns, (request.GET.get("q") or "").strip())
    rows = _build_rows(queryset, columns)

    header = [c["label"] for c in columns]
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"iqvia_{dim_key}_{stamp}.{file_format}"

    if file_format == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(header)
        for row in rows:
            writer.writerow([row[c["key"]] for c in columns])
        return response

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = dim_label(dim_key, cfg["label"])[:31]

    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = XLS_HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in rows:
        sheet.append([row[c["key"]] for c in columns])

    for index in range(1, len(header) + 1):
        sheet.column_dimensions[get_column_letter(index)].width = 22
    sheet.freeze_panes = "A2"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_batch_state                                   ║
# ║  Type: Helper function                                     ║
# ║  Purpose: One card per dimension, files listed inside it   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: Sep/01-2026 by Akram, grouped by dimension       ║
# ╚════════════════════════════════════════════════════════════╝
# One file feeding four levels makes four cards, fourteen pack
# slices make a single card holding fourteen file rows
def build_batch_state(batch_id):
    staged = list(
        DataImportStaging.objects.filter(
            batch=batch_id, stage="ready", deleted=False
        ).order_by("id")
    )

    staged_dims = set()
    pack_slices = set()
    by_dim = {}
    for row in staged:
        dims = _staged_dimensions(row)
        staged_dims.update(dims)
        part = (row.summary or {}).get("part")
        if part:
            pack_slices.add(part)
        for dim in dims:
            by_dim.setdefault(dim, []).append(row)

    groups = []
    for dim in sorted(by_dim, key=lambda k: IMPORT_DIMENSIONS[k]["level"]):
        rows = by_dim[dim]
        cfg = IMPORT_DIMENSIONS[dim]

        chain = []
        for parent_key in get_parent_chain(dim):
            parent_cfg = IMPORT_DIMENSIONS[parent_key]
            if dim == "pack":
                slice_name = PACK_PARENT_SLICE.get(parent_key)
                if slice_name is None:
                    # Ancestor reached through Product, not a slice of its own
                    status = "ok" if "pack_product" in pack_slices else "waiting"
                elif slice_name in pack_slices:
                    status = "ok"
                else:
                    status = "waiting"
            elif parent_cfg["model"].objects.filter(deleted=False).exists():
                status = "ok"
            elif parent_key in staged_dims:
                status = "staged"
            else:
                status = "missing"
            chain.append(
                {
                    "key": parent_key,
                    "label": dim_label(parent_key, parent_cfg["label"]),
                    "status": status,
                }
            )

        files = []
        for row in rows:
            others = [d for d in _staged_dimensions(row) if d != dim]
            files.append(
                {
                    "staging_id": row.id,
                    "file_name": row.file_name,
                    "rows_read": row.rows_read,
                    "part": (row.summary or {}).get("part"),
                    "shared_with": [
                        dim_label(d, IMPORT_DIMENSIONS[d]["label"]) for d in others
                    ],
                }
            )

        preview = None
        for row in rows:
            for item in (row.summary or {}).get("previews") or []:
                if item.get("dimension") == dim:
                    preview = item

        entry = {
            "dimension": dim,
            "label": dim_label(dim, cfg["label"]),
            "files": files,
            "chain": chain,
            "preview": preview,
            "blocked": any(c["status"] == "missing" for c in chain),
        }

        if dim == "pack":
            entry["slices"] = [
                {"part": part, "have": part in pack_slices}
                for part in PACK_PARTS.values()
            ]
            entry["slice_have"] = len(pack_slices)
            entry["slice_total"] = len(PACK_PARTS)

        groups.append(entry)

    return groups

# Dimensions a staged file feeds, older rows only stored a column list
def _staged_dimensions(row):
    payload = row.columns
    if isinstance(payload, dict) and payload.get("dimensions"):
        return payload["dimensions"]
    return [row.dimension]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_pending_map                                   ║
# ║  Type: Helper function                                     ║
# ║  Purpose: How many ancestors of each dimension are empty   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# self counts the dimension itself, chain counts every ancestor above it
def build_pending_map(batch_id=None):
    has_data_map = build_has_data_map()
    covered = {key for key, has in has_data_map.items() if has}

    staged = set()
    if batch_id:
        for row in DataImportStaging.objects.filter(batch=batch_id, stage="ready", deleted=False):
            staged.update(_staged_dimensions(row))

    pending = {}
    for key in IMPORT_DIMENSIONS:
        missing = [
            p for p in get_parent_chain(key)
            if p not in covered and p not in staged
        ]
        pending[key] = {
            "self": 0 if (key in covered or key in staged) else 1,
            "chain": len(missing),
            "missing": [
                {"key": p, "label": dim_label(p, IMPORT_DIMENSIONS[p]["label"])}
                for p in missing
            ],
        }
    return pending


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_staged_names                                  ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Match keys carried by other files in the batch   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: Sep/01-2026 by Akram, reads the cached summary   ║
# ╚════════════════════════════════════════════════════════════╝
# Reads what upload already stored, no file is opened here
def build_staged_names(batch_id, skip_id=None):
    names = {}
    if not batch_id:
        return names
    rows = DataImportStaging.objects.filter(batch=batch_id, stage="ready", deleted=False)
    if skip_id:
        rows = rows.exclude(id=skip_id)
    for row in rows:
        cached = (row.summary or {}).get("keys") or {}
        for dim, values in cached.items():
            names.setdefault(dim, set()).update(values)
    return names


# Every pack slice in the batch plus the one being uploaded right now
def _collect_pack_parsed(batch_id, raw_bytes, file_type, skip_current=False):
    collected = []
    for row in DataImportStaging.objects.filter(batch=batch_id, stage="ready", deleted=False):
        if "pack" not in _staged_dimensions(row):
            continue
        try:
            raw_row = row.file.read()
        except Exception:
            # Row survived but the media file is gone, drop it
            row.delete()
            continue
        parsed = parse_file(raw_row, row.file_type, "pack")
        if not parsed.get("error"):
            collected.append(parsed)
    if not skip_current:
        current = parse_file(raw_bytes, file_type, "pack")
        if not current.get("error"):
            collected.append(current)
    return collected


# Which pack slices the batch holds, read from the cached summary only
def _pack_slices_in_batch(batch_id, extra_part=None):
    have = {extra_part} if extra_part else set()
    for row in DataImportStaging.objects.filter(batch=batch_id, stage="ready", deleted=False):
        part = (row.summary or {}).get("part")
        if part:
            have.add(part)
    return have


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: _pack_slice_preview                                 ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Cheap pack preview while slices are incomplete   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Sep/01-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Merging 40k packs is only worth it once every slice has arrived
def _pack_slice_preview(batch_id, current_part, user, file_name):
    have = _pack_slices_in_batch(batch_id, current_part)
    missing = [part for part in PACK_PARTS.values() if part not in have]

    if missing:
        parts = [part("pack_parts_missing", n=len(missing),
                      parts=", ".join(missing))]
        return {
            "state": STATE_FAILED,
            "message": render_parts(parts),
            "msg_parts": parts,
            "rows_insert": 0, "rows_update": 0, "rows_same": 0, "rows_archive": 0,
            "orphan_rows": 0, "orphan_parent": "", "orphan_field": "",
            "missing_parts": missing,
        }

    # All fourteen are in and saved, read every slice from staging
    return commit_pack(
        _collect_pack_parsed(batch_id, None, None, skip_current=True),
        user=user, file_names=[file_name], batch=batch_id, dry_run=True,
    )

# Pack parent to the slice that carries it, order follows PACK_PARTS
PACK_PARENT_SLICE = {
    "product": "pack_product",
    "packform": "pack_packform",
    "regstat": "pack_regstat",
    "ethgrp": "pack_ethstatgrp",
    "ethstat": "pack_ethstat",
    "branddet": "pack_branddet",
    "atc4": "pack_atc4",
    "otc4": "pack_otc4",
    "nfc3": "pack_nfc3",
}

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: purge_stale_staging                                 ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Drop staging left behind by abandoned sessions   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# keep_batch survives the sweep, it is the batch the page still owns
def purge_stale_staging(user=None, keep_batch=None):
    cutoff = timezone.now() - timedelta(hours=STAGING_TTL_HOURS)
    # Without deleted=False the sweep keeps reprocessing its own tombstones
    rows = DataImportStaging.objects.filter(cat__lt=cutoff, deleted=False)
    if user is not None:
        rows = rows.filter(cby=user)
    if keep_batch:
        rows = rows.exclude(batch=keep_batch)

    removed = 0
    for row in rows:
        row.file.delete(save=False)
        row.delete()
        removed += 1

    # Staging is transient, tombstones past the TTL are dropped for real
    # QuerySet.delete() bypasses GenericAbstract.delete(), so this is a hard delete
    DataImportStaging.objects.filter(cat__lt=cutoff, deleted=True).delete()
    return removed

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_import_discard                                ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Beacon target for a page that is being unloaded  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_importviews.py           ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# sendBeacon cannot read a reply, so this stays deliberately small
@login_required
@require_POST
def iqvia_import_discard(request):
    batch_id = (request.POST.get("batch") or "").strip()
    if not batch_id:
        return JsonResponse({"discarded": 0})

    rows = DataImportStaging.objects.filter(
        batch=batch_id, cby=request.user, deleted=False
    )
    removed = 0
    for row in rows:
        row.file.delete(save=False)
        row.delete()
        removed += 1
    return JsonResponse({"discarded": removed})