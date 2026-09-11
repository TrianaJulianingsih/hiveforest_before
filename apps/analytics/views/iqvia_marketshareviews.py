import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.analytics.services.iqvia_dimension_service import (
    MEASURE_UNIT,
    MEASURE_VALUE,
    get_dimension,
    get_dimension_groups,
    is_valid_dimension,
)
from apps.analytics.services.iqvia_filter_service import parse_selection
from apps.analytics.services.iqvia_report_service import get_available_years
from apps.analytics.services.iqvia_share_service import (
    MAX_SLICES, 
    get_share_rows,
    get_share_others,
)
from apps.analytics.utils.chart_utils import build_donut_chart

XLS_HEADER_FILL = PatternFill("solid", fgColor="1A472A")


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_marketshare                                   ║
# ║  Type: Function base view                                  ║
# ║  Purpose: Market share report page for IQVIA ITMA data     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_marketshareviews.py      ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, quarter range + MAT flag    ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_marketshare(request):
    context = {
        "title": "IQVIA Market Share",
        "dimension_groups": get_dimension_groups(),
        "years": get_available_years(),
        "top_limits": [5, 10, 15, 20],
        "measures": [
            {"key": MEASURE_VALUE, "label": "Value HNA"},
            {"key": MEASURE_UNIT, "label": "Unit"},
        ],
    }
    return render(request, "analytics/iqvia/marketshare.html", context)


def _read_share_params(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_dimension(dim_key):
        return None, "Unknown dimension."

    measure = (request.GET.get("measure") or MEASURE_VALUE).strip()
    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE

    raw_limit = (request.GET.get("limit") or "10").strip().lower()
    limit_label = f"Top {raw_limit}"
    if raw_limit == "all":
        limit = MAX_SLICES
        limit_label = f"All (max {MAX_SLICES})"
    elif raw_limit.isdigit():
        limit = int(raw_limit)
    else:
        limit = 10
        limit_label = "Top 10"

    def _int(name, fallback):
        raw = (request.GET.get(name) or "").strip()
        return int(raw) if raw.isdigit() else fallback

    year_from = _int("year_from", 0)
    year_to = _int("year_to", 0)
    if not year_from or not year_to:
        return None, "Choose a valid year range."
    if year_from > year_to:
        return None, "From year must not be after To year."

    q_from = _int("q_from", 1)
    q_to = _int("q_to", 4)
    if q_from not in (1, 2, 3, 4):
        q_from = 1
    if q_to not in (1, 2, 3, 4):
        q_to = 4

    mat = (request.GET.get("mat") or "").strip() == "1"

    return (
        {
            "dim_key": dim_key,
            "measure": measure,
            "limit": limit,
            "limit_label": limit_label,
            "year_from": year_from,
            "q_from": q_from,
            "year_to": year_to,
            "q_to": q_to,
            "mat": mat,
            "selected": parse_selection(request),
        },
        None,
    )


def _measure_label(measure):
    return "Value HNA" if measure == MEASURE_VALUE else "Unit"


# Human readable period, adapts to plain year / refined quarter / MAT
def _period_label(params):
    if params["mat"]:
        return f"MAT as of Q{params['q_to']}/{params['year_to']}"
    if params["q_from"] == 1 and params["q_to"] == 4:
        if params["year_from"] == params["year_to"]:
            return str(params["year_from"])
        return f"{params['year_from']} - {params['year_to']}"
    return f"Q{params['q_from']}/{params['year_from']} - Q{params['q_to']}/{params['year_to']}"


def _export_filename(params, extension):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"iqvia_marketshare_{params['dim_key']}_{stamp}.{extension}"


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_share_data                                    ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Render donut chart plus the share table rows     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_marketshareviews.py      ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, quarter range + MAT flag    ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_share_data(request):
    params, error = _read_share_params(request)
    if error:
        return JsonResponse({"error": error}, status=400)

    rows, grand = get_share_rows(
        params["dim_key"],
        params["measure"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["mat"],
        params["selected"],
        params["limit"],
    )
    if not rows:
        return JsonResponse({"error": "No data for this combination."}, status=200)

    measure_label = _measure_label(params["measure"])
    dim_label = get_dimension(params["dim_key"])["label"]

    return JsonResponse(
        {
            "chart": build_donut_chart(
                [r["label"] for r in rows],
                [r["value"] for r in rows],
                f"{dim_label} Share - {measure_label} ({_period_label(params)})",
                measure_label.upper(),
            ),
            "rows": rows,
            "grand": grand,
            "dim_label": dim_label,
            "measure_label": measure_label,
            "filename": _export_filename(params, "png"),
        }
    )


def _write_csv(header, body, others, filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(header)
    for row in body:
        writer.writerow(row)

    if others:
        writer.writerow([])
        writer.writerow([f"OTHERS DETAIL ({len(others)} items)"])
        for index, row in enumerate(others, start=1):
            writer.writerow([index, row["label"], row["value"], row["share"]])

    return response


def _write_xlsx(header, body, params, dim_label, measure_label, grand, others, filename):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Market Share"

    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = XLS_HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in body:
        sheet.append(row)
    sheet.append(["", "TOTAL", grand, 100.0])
    for cell in sheet[sheet.max_row]:
        cell.font = Font(bold=True)

    if others:
        sheet.append([])
        sheet.append([f"OTHERS DETAIL ({len(others)} items)"])
        sheet.cell(row=sheet.max_row, column=1).font = Font(bold=True, color="6C757D")
        for index, row in enumerate(others, start=1):
            sheet.append([index, row["label"], row["value"], row["share"]])

    for row in sheet.iter_rows(min_row=2, min_col=3, max_col=3):
        for cell in row:
            cell.number_format = "#,##0"
    for row in sheet.iter_rows(min_row=2, min_col=4, max_col=4):
        for cell in row:
            cell.number_format = '0.00"%"'

    sheet.column_dimensions["A"].width = 6
    sheet.column_dimensions["B"].width = 46
    sheet.column_dimensions["C"].width = 20
    sheet.column_dimensions["D"].width = 12
    sheet.freeze_panes = "A2"

    info = workbook.create_sheet("Settings")
    info.append(["Dimension", dim_label])
    info.append(["Measure", measure_label])
    info.append(["Period", _period_label(params)])
    info.append(["Max slices", params["limit_label"]])
    info.append(["Generated", datetime.now().strftime("%d %b %Y %H:%M")])
    if params["selected"]:
        for key, ids in params["selected"].items():
            info.append([f"Filter - {get_dimension(key)['label']}", f"{len(ids)} selected"])
    else:
        info.append(["Filter", "None"])
    for cell in info["A"]:
        cell.font = Font(bold=True)
    info.column_dimensions["A"].width = 30
    info.column_dimensions["B"].width = 55

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_share_export                                  ║
# ║  Type: File download function base view                    ║
# ║  Purpose: Send the share table as xlsx or csv              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_marketshareviews.py      ║
# ║  Created: Aug/24-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_share_export(request):
    params, error = _read_share_params(request)
    if error:
        return HttpResponse(error, status=400)

    file_format = (request.GET.get("format") or "xlsx").strip().lower()
    if file_format not in ("xlsx", "csv"):
        file_format = "xlsx"

    rows, grand = get_share_rows(
        params["dim_key"],
        params["measure"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["mat"],
        params["selected"],
        params["limit"],
    )
    if not rows:
        return HttpResponse("No data for this combination.", status=400)

    others = get_share_others(
        params["dim_key"],
        params["measure"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["mat"],
        params["selected"],
        params["limit"],
    )

    dim_label = get_dimension(params["dim_key"])["label"]
    measure_label = _measure_label(params["measure"])

    header = ["#", dim_label, measure_label, "Share %"]
    body = [
        [index + 1, row["label"], row["value"], row["share"]]
        for index, row in enumerate(rows)
    ]
    filename = _export_filename(params, file_format)

    if file_format == "csv":
        return _write_csv(header, body + [["", "TOTAL", grand, 100.0]], others, filename)
    return _write_xlsx(header, body, params, dim_label, measure_label, grand, others, filename)