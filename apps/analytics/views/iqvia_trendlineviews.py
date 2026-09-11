import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.analytics.services.iqvia_dimension_service import (
    MEASURE_UNIT,
    MEASURE_VALUE,
    PERIOD_MAT,
    PERIOD_QUARTER,
    PERIOD_YEAR,
    get_dimension,
    get_dimension_groups,
    is_valid_dimension,
)
from apps.analytics.services.iqvia_filter_service import (
    count_packs,
    get_options,
    parse_selection,
)
from apps.analytics.services.iqvia_report_service import (
    get_available_quarters,
    get_available_years,
    quarter_display,
)
from apps.analytics.services.iqvia_trend_service import (
    MAX_SERIES,
    get_trend_export_rows,
    get_trend_series,
)
from apps.analytics.utils.chart_utils import build_multi_line_chart

# Excel header fill, HiveForest primary
XLS_HEADER_FILL = PatternFill("solid", fgColor="1A472A")

# Human readable label for a MAT anchor quarter, 0 means every quarter
MAT_ANCHOR_LABELS = {0: "All quarters", 1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_trendline                                     ║
# ║  Type: Function base view                                  ║
# ║  Purpose: Trendline report page for IQVIA ITMA data        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_trendlineviews.py        ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, MAT anchor                  ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_trendline(request):
    context = {
        "title": "IQVIA Trendline",
        "dimension_groups": get_dimension_groups(),
        "period_bases": [
            {"key": PERIOD_YEAR, "label": "Year"},
            {"key": PERIOD_QUARTER, "label": "Quarter"},
        ],
        "years": get_available_years(),
        "quarters": [
            {"value": q, "label": quarter_display(q)} for q in get_available_quarters()
        ],
        "top_limits": [5, 10, 20, 50],
        "measures": [
            {"key": MEASURE_VALUE, "label": "Value HNA"},
            {"key": MEASURE_UNIT, "label": "Unit"},
        ],
    }
    return render(request, "analytics/iqvia/trendline.html", context)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_options                                       ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Serve cascaded option list for one dimension     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_trendlineviews.py        ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_options(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_dimension(dim_key):
        return JsonResponse({"error": "Unknown dimension"}, status=400)

    selected = parse_selection(request)
    data = get_options(dim_key, selected, request.GET.get("q", ""))
    data["match_packs"] = count_packs(selected)
    return JsonResponse(data)


# Read and clean every chart parameter, shared by chart and export
def _read_trend_params(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_dimension(dim_key):
        return None, "Unknown dimension."

    base = (request.GET.get("base") or PERIOD_YEAR).strip()
    if base not in (PERIOD_YEAR, PERIOD_QUARTER, PERIOD_MAT):
        base = PERIOD_YEAR

    measure = (request.GET.get("measure") or MEASURE_VALUE).strip()
    if measure not in (MEASURE_VALUE, MEASURE_UNIT):
        measure = MEASURE_VALUE

    raw_limit = (request.GET.get("limit") or "10").strip().lower()
    limit_label = f"Top {raw_limit}"
    if raw_limit == "all":
        limit = MAX_SERIES
        limit_label = f"All (max {MAX_SERIES})"
    elif raw_limit.isdigit():
        limit = int(raw_limit)
        if limit == 0:
            limit_label = "Combined total"
    else:
        limit = 10
        limit_label = "Top 10"

    raw_from = (request.GET.get("year_from") or "").strip()
    raw_to = (request.GET.get("year_to") or "").strip()
    if not raw_from.isdigit() or not raw_to.isdigit():
        return None, "Choose a valid year range."

    year_from, year_to = int(raw_from), int(raw_to)
    if year_from > year_to:
        year_from, year_to = year_to, year_from

    # Anchor only means something in MAT mode, 0 stands for every quarter
    raw_anchor = (request.GET.get("mat_anchor") or "").strip()
    mat_anchor = int(raw_anchor) if raw_anchor in ("1", "2", "3", "4") else 0
    if base != PERIOD_MAT:
        mat_anchor = 0

    return (
        {
            "dim_key": dim_key,
            "base": base,
            "measure": measure,
            "limit": limit,
            "limit_label": limit_label,
            "year_from": year_from,
            "year_to": year_to,
            "mat_anchor": mat_anchor,
            "selected": parse_selection(request),
        },
        None,
    )


# Human readable measure name
def _measure_label(measure):
    return "Value HNA" if measure == MEASURE_VALUE else "Unit"


# Human readable granularity, including the MAT anchor when relevant
def _granularity_label(params):
    if params["base"] == PERIOD_YEAR:
        return "Yearly"
    if params["base"] == PERIOD_QUARTER:
        return "Quarterly"
    return f"MAT ({MAT_ANCHOR_LABELS[params['mat_anchor']]})"


# Download name with a timestamp
def _export_filename(params, extension):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"iqvia_trendline_{params['dim_key']}_{stamp}.{extension}"


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_trend_data                                    ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Render the trendline chart as base64 png         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_trendlineviews.py        ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, MAT anchor                  ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_trend_data(request):
    params, error = _read_trend_params(request)
    if error:
        return JsonResponse({"error": error}, status=400)

    labels, series = get_trend_series(
        params["dim_key"],
        params["measure"],
        params["base"],
        params["year_from"],
        params["year_to"],
        params["selected"],
        params["limit"],
        params["mat_anchor"],
    )
    if not labels:
        return JsonResponse({"error": "No data for this combination."}, status=200)

    measure_label = _measure_label(params["measure"])
    mode_tag = f" ({_granularity_label(params)})" if params["base"] == PERIOD_MAT else ""
    title = f"{get_dimension(params['dim_key'])['label']} - {measure_label}{mode_tag}"

    return JsonResponse(
        {
            "chart": build_multi_line_chart(labels, series, title, measure_label),
            "series_count": len(series),
            "point_count": len(labels),
            "filename": _export_filename(params, "png"),
        }
    )


# Comma separated file, BOM so Excel reads UTF-8 correctly
def _write_csv(header, head_rows, others_rows, filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(header)
    for row in head_rows:
        writer.writerow([row[0]] + [round(value, 2) for value in row[1:]])

    if others_rows:
        writer.writerow([])
        writer.writerow([f"OTHERS DETAIL ({len(others_rows)} items)"])
        for row in others_rows:
            writer.writerow([row[0]] + [round(value, 2) for value in row[1:]])
    return response


# Formatted workbook with a second sheet describing the settings
def _write_xlsx(header, head_rows, others_rows, params, dim_label, measure_label, filename):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Trendline"

    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = XLS_HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in head_rows:
        sheet.append(row)

    if others_rows:
        sheet.append([])
        sheet.append([f"OTHERS DETAIL ({len(others_rows)} items)"])
        sheet.cell(row=sheet.max_row, column=1).font = Font(bold=True, color="6C757D")
        for row in others_rows:
            sheet.append(row)

    for row in sheet.iter_rows(min_row=2, min_col=2):
        for cell in row:
            cell.number_format = "#,##0"

    sheet.column_dimensions["A"].width = 42
    for index in range(2, len(header) + 1):
        sheet.column_dimensions[get_column_letter(index)].width = 16
    sheet.freeze_panes = "B2"

    info = workbook.create_sheet("Settings")
    info.append(["Dimension", dim_label])
    info.append(["Measure", measure_label])
    info.append(["Granularity", _granularity_label(params)])
    info.append(["Year range", f"{params['year_from']} - {params['year_to']}"])
    info.append(["Max lines", params["limit_label"]])
    info.append(["Lines shown", len(head_rows)])
    info.append(["Merged into Others", len(others_rows)])
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
# ║  Name: iqvia_trend_export                                  ║
# ║  Type: File download function base view                    ║
# ║  Purpose: Send the chart numbers as xlsx or csv            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_trendlineviews.py        ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: Aug/24-2026 by Akram, MAT anchor                  ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_trend_export(request):
    params, error = _read_trend_params(request)
    if error:
        return HttpResponse(error, status=400)

    file_format = (request.GET.get("format") or "xlsx").strip().lower()
    if file_format not in ("xlsx", "csv"):
        file_format = "xlsx"

    labels, head_rows, others_rows = get_trend_export_rows(
        params["dim_key"],
        params["measure"],
        params["base"],
        params["year_from"],
        params["year_to"],
        params["selected"],
        params["limit"],
        params["mat_anchor"],
    )
    if not labels:
        return HttpResponse("No data for this combination.", status=400)

    dim_label = get_dimension(params["dim_key"])["label"]
    measure_label = _measure_label(params["measure"])
    header = [dim_label] + labels + ["Total"]
    filename = _export_filename(params, file_format)

    if file_format == "csv":
        return _write_csv(header, head_rows, others_rows, filename)
    return _write_xlsx(
        header, head_rows, others_rows, params, dim_label, measure_label, filename
    )