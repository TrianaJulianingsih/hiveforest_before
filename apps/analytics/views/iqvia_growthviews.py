import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.analytics.services.iqvia_dimension_service import (
    get_dimension,
    get_dimension_groups,
    is_valid_dimension,
)
from apps.analytics.services.iqvia_filter_service import parse_selection
from apps.analytics.services.iqvia_growth_service import (
    MAX_BARS,
    PMODE_MAT,
    PMODE_QUARTER,
    PMODE_YEAR,
    get_growth_others,
    get_growth_rows,
    point_label,
)
from apps.analytics.services.iqvia_report_service import get_available_years
from apps.analytics.utils.chart_utils import build_grouped_bar_chart

XLS_HEADER_FILL = PatternFill("solid", fgColor="1A472A")


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_growth                                        ║
# ║  Type: Function base view                                  ║
# ║  Purpose: Growth report page for IQVIA ITMA data           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_growthviews.py           ║
# ║  Created: Aug/26-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_growth(request):
    context = {
        "title": "IQVIA Growth",
        "dimension_groups": get_dimension_groups(),
        "years": get_available_years(),
        "top_limits": [5, 10, 15, 20],
    }
    return render(request, "analytics/iqvia/growth.html", context)


# Read and clean every parameter, shared by chart and export
def _read_growth_params(request):
    dim_key = (request.GET.get("dim") or "").strip()
    if not is_valid_dimension(dim_key):
        return None, "Unknown dimension."

    raw_limit = (request.GET.get("limit") or "10").strip().lower()
    limit_label = f"Top {raw_limit}"
    if raw_limit == "all":
        limit = MAX_BARS
        limit_label = f"All (max {MAX_BARS})"
    elif raw_limit.isdigit():
        limit = int(raw_limit)
        if limit == 0:
            limit_label = "Combined total"
    else:
        limit = 10
        limit_label = "Top 10"

    def _int(name, fallback):
        raw = (request.GET.get(name) or "").strip()
        return int(raw) if raw.isdigit() else fallback

    year_from = _int("year_from", 0)
    year_to = _int("year_to", 0)
    if not year_from or not year_to:
        return None, "Choose both years."

    q_from = _int("q_from", 0)
    q_to = _int("q_to", 0)
    mat = (request.GET.get("mat") or "").strip() == "1"

    if mat:
        if q_from not in (1, 2, 3, 4) or q_to not in (1, 2, 3, 4):
            return None, "MAT needs an anchor quarter on both sides."
        pmode = PMODE_MAT
    elif q_from or q_to:
        # Picking a quarter on one side makes it mandatory on the other
        if q_from not in (1, 2, 3, 4) or q_to not in (1, 2, 3, 4):
            return None, "Pick a quarter on both sides, or leave both empty."
        pmode = PMODE_QUARTER
    else:
        pmode = PMODE_YEAR
        q_from, q_to = 1, 1

    # The later point must not sit before the earlier one
    left = year_from * 4 + (q_from if pmode != PMODE_YEAR else 0)
    right = year_to * 4 + (q_to if pmode != PMODE_YEAR else 0)
    if left > right:
        return None, "The second period must come after the first."

    return (
        {
            "dim_key": dim_key,
            "limit": limit,
            "limit_label": limit_label,
            "pmode": pmode,
            "year_from": year_from,
            "q_from": q_from,
            "year_to": year_to,
            "q_to": q_to,
            "selected": parse_selection(request),
        },
        None,
    )


def _labels(params):
    return (
        point_label(params["pmode"], params["year_from"], params["q_from"]),
        point_label(params["pmode"], params["year_to"], params["q_to"]),
    )


def _export_filename(params, extension):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"iqvia_growth_{params['dim_key']}_{stamp}.{extension}"


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_growth_data                                   ║
# ║  Type: Ajax function base view                             ║
# ║  Purpose: Render the grouped bar chart plus table rows     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_growthviews.py           ║
# ║  Created: Aug/26-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_growth_data(request):
    params, error = _read_growth_params(request)
    if error:
        return JsonResponse({"error": error}, status=400)

    rows = get_growth_rows(
        params["dim_key"],
        params["pmode"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["selected"],
        params["limit"],
    )
    if not rows:
        return JsonResponse({"error": "No data for this combination."}, status=200)

    label_a, label_b = _labels(params)
    dim_label = get_dimension(params["dim_key"])["label"]

    # Short caption drawn above each pair of bars
    captions = []
    for row in rows:
        if row["growth_tag"]:
            captions.append(row["growth_tag"])
        elif row["growth"] > 0:
            captions.append(f"+{row['growth']:.1f}%")
        else:
            captions.append(f"{row['growth']:.1f}%")

    return JsonResponse(
        {
            "chart": build_grouped_bar_chart(
                [r["label"] for r in rows],
                [r["before"] for r in rows],
                [r["after"] for r in rows],
                label_a,
                label_b,
                f"{dim_label} Growth - {label_a} vs {label_b}",
                "Value HNA",
                captions,
            ),
            "rows": rows,
            "label_a": label_a,
            "label_b": label_b,
            "dim_label": dim_label,
            "filename": _export_filename(params, "png"),
        }
    )


# One table row shaped for export
def _export_row(index, row):
    growth = row["growth_tag"] if row["growth"] is None else row["growth"]
    return [index, row["label"], row["before"], row["after"], growth]


def _write_csv(header, body, others, filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(header)
    for row in body:
        writer.writerow(row)

    # Items merged into the Others bar are still listed one by one
    if others:
        writer.writerow([])
        writer.writerow([f"OTHERS DETAIL ({len(others)} items)"])
        for index, row in enumerate(others, start=1):
            writer.writerow(_export_row(index, row))
    return response


def _write_xlsx(header, body, others, params, dim_label, filename):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Growth"

    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = XLS_HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in body:
        sheet.append(row)

    if others:
        sheet.append([])
        sheet.append([f"OTHERS DETAIL ({len(others)} items)"])
        sheet.cell(row=sheet.max_row, column=1).font = Font(bold=True, color="6C757D")
        for index, row in enumerate(others, start=1):
            sheet.append(_export_row(index, row))

    for row in sheet.iter_rows(min_row=2, min_col=3, max_col=4):
        for cell in row:
            cell.number_format = "#,##0"

    sheet.column_dimensions["A"].width = 6
    sheet.column_dimensions["B"].width = 46
    sheet.column_dimensions["C"].width = 22
    sheet.column_dimensions["D"].width = 22
    sheet.column_dimensions["E"].width = 12
    sheet.freeze_panes = "A2"

    label_a, label_b = _labels(params)
    info = workbook.create_sheet("Settings")
    info.append(["Dimension", dim_label])
    info.append(["Measure", "Value HNA"])
    info.append(["Period mode", params["pmode"].upper()])
    info.append(["Compared", f"{label_a} vs {label_b}"])
    info.append(["Max bars", params["limit_label"]])
    info.append(["Bars shown", len(body)])
    info.append(["Merged into Others", len(others)])
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
# ║  Name: iqvia_growth_export                                 ║
# ║  Type: File download function base view                    ║
# ║  Purpose: Send the growth table as xlsx or csv             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\views\iqvia_growthviews.py           ║
# ║  Created: Aug/26-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
@login_required
def iqvia_growth_export(request):
    params, error = _read_growth_params(request)
    if error:
        return HttpResponse(error, status=400)

    file_format = (request.GET.get("format") or "xlsx").strip().lower()
    if file_format not in ("xlsx", "csv"):
        file_format = "xlsx"

    rows = get_growth_rows(
        params["dim_key"],
        params["pmode"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["selected"],
        params["limit"],
    )
    if not rows:
        return HttpResponse("No data for this combination.", status=400)

    others = get_growth_others(
        params["dim_key"],
        params["pmode"],
        params["year_from"],
        params["q_from"],
        params["year_to"],
        params["q_to"],
        params["selected"],
        params["limit"],
    )

    dim_label = get_dimension(params["dim_key"])["label"]
    label_a, label_b = _labels(params)
    header = ["#", dim_label, label_a, label_b, "Growth %"]
    body = [
        _export_row(index, row)
        for index, row in enumerate(rows, start=1)
        if not row["is_others"]
    ]
    filename = _export_filename(params, file_format)

    if file_format == "csv":
        return _write_csv(header, body, others, filename)
    return _write_xlsx(header, body, others, params, dim_label, filename)