from __future__ import annotations
import json
from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd
from openpyxl.styles import PatternFill
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required

from apps.base.models import WarehousePalette
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction
from apps.base.models.utils import get_permitted_branches
from apps.sales.models.product_models import Product
from apps.supplychain.models.distributions_models import Branch, BranchStock


DateSequence = Sequence[date]


FILL_LOW = PatternFill(fill_type="solid", start_color="e6f3ff", end_color="e6f3ff")
FILL_MEDIUM = PatternFill(fill_type="solid", start_color="fff7d6", end_color="fff7d6")
FILL_HIGH = PatternFill(fill_type="solid", start_color="ffe5ec", end_color="ffe5ec")
FILL_STANDARD = PatternFill(
    fill_type="solid", start_color="FFFFFFFF", end_color="FFFFFFFF"
)


def _default_date_range() -> Tuple[date, date]:
    today = timezone.localdate()
    return today - timedelta(days=6), today


def _normalize_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    parsed = parse_date(value)
    return parsed or fallback


def _branch_identity(branch: Branch) -> Tuple[str, str]:
    code = (branch.initial or branch.code or "").strip().upper()
    description = (branch.shortname or branch.name or code).strip().upper()

    if not code and description:
        code = description
    if not description:
        description = code or str(branch.id)
    if not code:
        code = str(branch.id)

    return code, description


def _build_branch_group_options(
    branches: Sequence[Branch],
    palette_map: Dict[str, Dict[str, object]],
    selected_values: Sequence[str],
) -> List[Dict[str, object]]:
    selected_set = set(selected_values)

    options: List[Dict[str, object]] = []
    for branch in sorted(branches, key=lambda item: _branch_identity(item)):
        palette_code = (branch.initial or branch.code or "").strip().upper()
        palette_entry = palette_map.get(branch.id)
        if palette_entry:
            code = palette_code
            description = palette_entry.get("name") or palette_code
        else:
            code, description = _branch_identity(branch)
        value = str(branch.id)
        label = (
            f"{code} - {description}"
            if code and description and code != description
            else description or code
        )
        options.append(
            {
                "value": value,
                "label": label,
                "selected": value in selected_set,
                "ids": [branch.id],
            }
        )

    return options


def _load_product_metrics(
    names: Iterable[str],
) -> Dict[str, Dict[str, Optional[Decimal]]]:
    normalized_names = {name.strip().lower() for name in names if name}
    if not normalized_names:
        return {}

    metrics: Dict[str, Dict[str, Optional[Decimal]]] = {}
    rows = (
        Product.objects.annotate(name_lower=Lower("name"))
        .filter(name_lower__in=normalized_names)
        .values("name_lower", "size", "box_per_palletac")
    )
    for row in rows:
        key = row["name_lower"]
        metrics[key] = {
            "size": Decimal(row["size"]) if row["size"] else None,
            "box_per_palletac": (
                Decimal(row["box_per_palletac"]) if row["box_per_palletac"] else None
            ),
        }

    return metrics


def _calculate_pallets(
    total_reg: Optional[int],
    size: Optional[Decimal],
    per_pallet: Optional[Decimal],
) -> int:
    if not total_reg:
        return 0
    if not size or size <= 0:
        return 0

    try:
        if not per_pallet or per_pallet <= 0:
            raise InvalidOperation

        value = (Decimal(total_reg) / size) / per_pallet
        return int(value.to_integral_value(rounding="ROUND_CEILING"))
    except (InvalidOperation, ZeroDivisionError):
        return 0


def _date_range_list(start: date, end: date) -> List[date]:
    days = (end - start).days
    if days < 0:
        return []
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def _build_date_groups(date_columns: Sequence[date]) -> List[Dict[str, object]]:
    date_groups: List[Dict[str, object]] = []
    if not date_columns:
        return date_groups

    current_label: Optional[str] = None
    current_dates: List[date] = []
    for day in date_columns:
        label = day.strftime("%b %Y")
        if current_label is None:
            current_label = label
        if label != current_label:
            date_groups.append({"label": current_label, "dates": current_dates})
            current_dates = []
            current_label = label
        current_dates.append(day)
    if current_label is not None:
        date_groups.append({"label": current_label, "dates": current_dates})

    return date_groups


def _filter_zero_only_dates(
    date_columns: Sequence[date],
    summary_rows: List[Dict[str, object]],
    percentage_rows: List[Dict[str, object]],
    grand_totals: List[int],
) -> Tuple[
    List[date], List[Dict[str, object]], List[Dict[str, object]], List[int], List[date]
]:
    if not date_columns or not grand_totals:
        return list(date_columns), summary_rows, percentage_rows, grand_totals, []

    visible_indices = [index for index, total in enumerate(grand_totals) if total != 0]
    if len(visible_indices) == len(date_columns):
        return list(date_columns), summary_rows, percentage_rows, grand_totals, []

    omitted_dates = [
        day for index, day in enumerate(date_columns) if index not in visible_indices
    ]
    filtered_dates = [date_columns[index] for index in visible_indices]
    filtered_totals = [grand_totals[index] for index in visible_indices]

    for row in summary_rows:
        row["values"] = [row["values"][index] for index in visible_indices]

    for row in percentage_rows:
        row["values"] = [row["values"][index] for index in visible_indices]

    return filtered_dates, summary_rows, percentage_rows, filtered_totals, omitted_dates


def _warehouse_palette_map() -> Dict[str, Dict[str, object]]:
    mapping: Dict[str, Dict[str, object]] = {}
    rows = WarehousePalette.objects.values("branch_id", "name", "ambient_capacity")
    for entry in rows:
        branch_id = entry["branch_id"]
        if not branch_id:
            continue
        if branch_id not in mapping:
            mapping[branch_id] = {
                "name": (entry["name"] or "").strip(),
                "capacity": entry["ambient_capacity"] or 0,
            }
    return mapping


@login_required
def branchstock_summary_dashboard(request: HttpRequest) -> HttpResponse:
    context = _branchstock_summary_core(
        request, is_admin=False, default_select_all=True
    )

    summary_rows = context.get("summary_rows", [])
    date_columns = context.get("date_columns", [])
    grand_totals = context.get("grand_totals_list", [])
    total_capacity = context.get("total_capacity", 0)

    # Detailed statistics for dashboard
    branch_cards = []
    latest_date_str = (
        date_columns[-1].strftime("%d %b %Y") if date_columns else "-"
    )
    latest_total_stock = grand_totals[-1] if grand_totals else 0

    for s_row in summary_rows:
        code = s_row.get("branch_code", "")
        desc = s_row.get("branch_description", "")
        cap = s_row.get("warehouse_capacity", 0) or 0
        vals = s_row.get("values", [])
        latest_val = vals[-1] if vals else 0
        avg_val = round(sum(vals) / len(vals), 1) if vals else 0
        max_val = max(vals) if vals else 0
        min_val = min(vals) if vals else 0

        if cap > 0:
            util_pct = round((latest_val / cap * 100), 1)
        else:
            util_pct = 0.0

        if cap <= 0:
            status = "no_capacity"
            status_label = "No Capacity Set"
            badge_class = "secondary"
            color_hex = "#6c757d"
        elif util_pct >= 100:
            status = "critical"
            status_label = "Over Capacity"
            badge_class = "danger"
            color_hex = "#dc3545"
        elif util_pct >= 70:
            status = "warning"
            status_label = "High Load"
            badge_class = "warning"
            color_hex = "#ffc107"
        elif util_pct >= 30:
            status = "optimal"
            status_label = "Optimal"
            badge_class = "success"
            color_hex = "#198754"
        else:
            status = "low"
            status_label = "Low Stock"
            badge_class = "info"
            color_hex = "#0dcaf0"

        branch_cards.append(
            {
                "code": code,
                "description": desc,
                "capacity": cap,
                "latest_stock": latest_val,
                "avg_stock": avg_val,
                "max_stock": max_val,
                "min_stock": min_val,
                "utilization_pct": util_pct,
                "status": status,
                "status_label": status_label,
                "badge_class": badge_class,
                "color": color_hex,
                "values": vals,
            }
        )

    # Summary KPI counts
    total_branches = len(branch_cards)
    critical_count = sum(1 for b in branch_cards if b["status"] == "critical")
    warning_count = sum(1 for b in branch_cards if b["status"] == "warning")
    optimal_count = sum(1 for b in branch_cards if b["status"] == "optimal")
    low_count = sum(1 for b in branch_cards if b["status"] == "low")
    no_capacity_count = sum(1 for b in branch_cards if b["status"] == "no_capacity")

    overall_utilization_pct = (
        round((latest_total_stock / total_capacity * 100), 1)
        if total_capacity > 0
        else 0.0
    )

    # Top 10 Branches by Stock
    top_stock_branches = sorted(
        branch_cards, key=lambda x: x["latest_stock"], reverse=True
    )[:10]

    # Top Branches by Utilization %
    top_util_branches = sorted(
        [b for b in branch_cards if b["capacity"] > 0],
        key=lambda x: x["utilization_pct"],
        reverse=True,
    )[:10]

    # Trend Chart Data
    trend_labels = [d.strftime("%d %b") for d in date_columns]
    trend_stock_data = grand_totals
    trend_capacity_data = [total_capacity for _ in date_columns]

    # Status Doughnut Data
    status_chart_labels = [
        "Over Capacity (≥100%)",
        "High Load (70-99%)",
        "Optimal (30-69%)",
        "Low (<30%)",
    ]
    status_chart_data = [
        critical_count,
        warning_count,
        optimal_count,
        low_count,
    ]
    status_chart_colors = ["#dc3545", "#ffc107", "#198754", "#0dcaf0"]

    # Top Stock Chart Data
    top_stock_labels = [b["description"][:20] for b in top_stock_branches]
    top_stock_values = [b["latest_stock"] for b in top_stock_branches]
    top_stock_capacities = [b["capacity"] for b in top_stock_branches]

    # Top Utilization Chart Data
    top_util_labels = [b["description"][:20] for b in top_util_branches]
    top_util_values = [b["utilization_pct"] for b in top_util_branches]
    top_util_colors = [b["color"] for b in top_util_branches]

    dashboard_data = {
        "latest_date_str": latest_date_str,
        "latest_total_stock": latest_total_stock,
        "total_capacity": total_capacity,
        "overall_utilization_pct": overall_utilization_pct,
        "total_branches": total_branches,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "optimal_count": optimal_count,
        "low_count": low_count,
        "no_capacity_count": no_capacity_count,
        "branch_cards": branch_cards,
        "top_stock_branches": top_stock_branches,
        "top_util_branches": top_util_branches,
        # JSON serialized for charts
        "trend_labels_json": json.dumps(trend_labels),
        "trend_stock_json": json.dumps(trend_stock_data),
        "trend_capacity_json": json.dumps(trend_capacity_data),
        "status_chart_labels_json": json.dumps(status_chart_labels),
        "status_chart_data_json": json.dumps(status_chart_data),
        "status_chart_colors_json": json.dumps(status_chart_colors),
        "top_stock_labels_json": json.dumps(top_stock_labels),
        "top_stock_values_json": json.dumps(top_stock_values),
        "top_stock_capacities_json": json.dumps(top_stock_capacities),
        "top_util_labels_json": json.dumps(top_util_labels),
        "top_util_values_json": json.dumps(top_util_values),
        "top_util_colors_json": json.dumps(top_util_colors),
    }

    context.update(
        {
            "title": "Branch Stock Summary Dashboard",
            "subtitle": "Branch Warehouse Capacity & Stock Monitoring Dashboard",
            "dash": dashboard_data,
        }
    )

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Branch Stock Summary Dashboard",
        description="User viewed the Branch Stock Summary Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )

    return render(request, "branchstock/dashboard.html", context)


@login_required
def branchstock_summary_user(request):
    context = _branchstock_summary_core(request, is_admin=False)

    is_export = (
        request.POST.get("export") == "excel" or request.GET.get("export") == "excel"
    )
    if is_export and (context["summary_rows"] or context["percentage_rows"]):
        SystemLogService.log(
            request=request,
            action=LogAction.EXPORT,
            module="BOM",
            feature="Branch Stock Summary User Report",
            description="User exported the Branch Stock Summary User report to Excel.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return _export_summary_excel(context)

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Branch Stock Summary User Report",
        description="User viewed the Branch Stock Summary User report.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    return render(request, "branchstock/summary.html", context)


@staff_member_required
def branchstock_summary(request: HttpRequest) -> HttpResponse:
    context = _branchstock_summary_core(request, is_admin=True)

    if (
        request.method == "POST"
        and request.POST.get("export") == "excel"
        and context["summary_rows"]
    ):
        SystemLogService.log(
            request=request,
            action=LogAction.EXPORT,
            module="BOM",
            feature="Branch Stock Summary Admin Report",
            description="Admin exported the Branch Stock Summary Admin report to Excel.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return _export_summary_excel(context)

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Branch Stock Summary Admin Report",
        description="Admin viewed the Branch Stock Summary Admin report.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    return render(request, "branchstock/admin/summary.html", context)


def _branchstock_summary_core(
    request: HttpRequest, *, is_admin: bool, default_select_all: bool = False
) -> dict:
    default_start, default_end = _default_date_range()

    start_date = default_start
    end_date = default_end
    selected_branch_ids = []
    selected_branch_values = []
    filters_applied = False

    palette_map = _warehouse_palette_map()
    palette_branch_ids = set(palette_map.keys())

    permitted_branch_qs = get_permitted_branches(request.user).order_by("code")
    permitted_branch_ids = list(permitted_branch_qs.values_list("id", flat=True))

    if palette_branch_ids:
        # Filter permitted branches to those with warehouse palettes
        branchstock_ids = [bid for bid in permitted_branch_ids if bid in palette_branch_ids]
        if not branchstock_ids:
            branchstock_ids = permitted_branch_ids
    else:
        branchstock_ids = permitted_branch_ids

    branchstock_id_set = set(branchstock_ids)

    request_data = None
    if request.method == "POST":
        request_data = request.POST
    elif request.method == "GET" and any(
        key in request.GET for key in ["branch_id[]", "start_date", "end_date"]
    ):
        request_data = request.GET

    if request_data is not None:
        selected_branch_values = [v for v in request_data.getlist("branch_id[]") if v]

        branch_id_set = set()
        for raw in selected_branch_values:
            for part in raw.split(","):
                if part.strip().isdigit():
                    branch_id_set.add(int(part.strip()))

        selected_branch_ids = sorted(
            i for i in branch_id_set if i in branchstock_id_set
        )
        if not selected_branch_ids:
            selected_branch_ids = sorted(branchstock_ids)
            selected_branch_values = [str(i) for i in selected_branch_ids]

        start_date = _normalize_date(request_data.get("start_date"), default_start)
        end_date = _normalize_date(request_data.get("end_date"), default_end)

        if end_date < start_date:
            start_date, end_date = end_date, start_date

        filters_applied = True
    elif default_select_all and branchstock_ids:
        selected_branch_ids = sorted(branchstock_ids)
        selected_branch_values = [str(i) for i in selected_branch_ids]
        start_date = default_start
        end_date = default_end
        filters_applied = True

    branch_queryset = Branch.objects.filter(id__in=branchstock_ids)
    branch_options = _build_branch_group_options(
        branch_queryset, palette_map, selected_branch_values
    )

    date_columns = _date_range_list(start_date, end_date)

    date_groups: List[Dict[str, object]] = _build_date_groups(date_columns)

    summary_rows: List[Dict[str, object]] = []
    percentage_rows: List[Dict[str, object]] = []
    grand_totals: List[int] = [0 for _ in date_columns]
    total_capacity = 0
    omitted_zero_dates: List[date] = []
    export_date_columns: List[date] = list(date_columns)
    export_summary_rows: List[Dict[str, object]] = []
    export_percentage_rows: List[Dict[str, object]] = []

    if filters_applied and selected_branch_ids and date_columns:
        from django.db.models import Sum

        qs = list(
            BranchStock.objects.filter(
                branch_id__in=selected_branch_ids,
                trx_date__range=(start_date, end_date),
            )
            .values("branch_id", "trx_date", "group_id", "product_id")
            .annotate(total_reg_sum=Sum("total_reg"))
        )

        branch_info: Dict[int, Dict[str, object]] = {}
        for branch in Branch.objects.filter(id__in=selected_branch_ids):
            palette_code = (branch.initial or branch.code or "").strip().upper()
            palette_entry = palette_map.get(branch.id, {})
            if palette_entry:
                code = palette_code
                description = (palette_entry.get("name") or palette_code).strip()
                capacity = palette_entry.get("capacity", 0) or 0
            else:
                code, description = _branch_identity(branch)
                capacity = 0
            branch_info[branch.id] = {
                "code": code,
                "description": description,
                "capacity": capacity,
            }
        totals: Dict[int, Dict[date, int]] = {
            branch_id: {day: 0 for day in date_columns}
            for branch_id in selected_branch_ids
        }

        product_ids = {row["product_id"] for row in qs if row["product_id"]}
        product_map = {
            p["id"]: {
                "size": Decimal(p["size"]) if p["size"] else None,
                "box_per_palletac": (
                    Decimal(p["box_per_palletac"]) if p["box_per_palletac"] else None
                ),
            }
            for p in Product.objects.filter(id__in=product_ids).values(
                "id", "size", "box_per_palletac"
            )
        }

        for row in qs:
            branch_id = row["branch_id"]
            trx_date = row["trx_date"]
            group_id = row["group_id"]
            # product_key = (row["product_name"] or "").strip().lower()
            product_id = row["product_id"]
            total_reg = row["total_reg_sum"]
            # metrics = name_map.get(
            #     product_key, {"size": None, "box_per_palletac": None}
            # )
            metrics = product_map.get(
                product_id, {"size": None, "box_per_palletac": None}
            )
            pallets = _calculate_pallets(
                total_reg, metrics.get("size"), metrics.get("box_per_palletac")
            )
            if pallets <= 0:
                continue
            if branch_id in totals and trx_date in totals[branch_id]:
                totals[branch_id][trx_date] += pallets
        for branch_id in selected_branch_ids:
            info = branch_info.get(branch_id)
            if not info:
                continue
            values = [totals[branch_id][day] for day in date_columns]
            code = info["code"]
            description = info["description"]
            capacity = info.get("capacity", 0) or 0
            summary_rows.append(
                {
                    "branch_code": code,
                    "branch_description": description,
                    "warehouse_capacity": capacity,
                    "values": values,
                    "total": sum(values),
                }
            )
        # summary_rows.sort(key=lambda item: item["branch_code"] or "")
        summary_rows.sort(key=lambda item: item["branch_description"] or "")
        grand_totals = [0 for _ in date_columns]
        total_capacity = 0
        for entry in summary_rows:
            values = entry["values"]
            capacity = entry.get("warehouse_capacity", 0) or 0
            percent_values: List[Decimal] = []
            if capacity:
                for value in values:
                    try:
                        percent = (
                            (Decimal(value) / Decimal(capacity)) * Decimal(100)
                        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    except InvalidOperation:
                        percent = Decimal("0")
                    percent_values.append(percent)
            else:
                percent_values = [Decimal("0") for _ in values]
            combined_values = [
                {"value": raw_value, "percent": percent}
                for raw_value, percent in zip(values, percent_values)
            ]
            percentage_rows.append(
                {
                    "branch_code": entry["branch_code"],
                    "branch_description": entry["branch_description"],
                    "warehouse_capacity": capacity,
                    "values": combined_values,
                }
            )
            for index, value in enumerate(values):
                grand_totals[index] += value
            total_capacity += capacity

        export_date_columns = list(date_columns)
        export_summary_rows = deepcopy(summary_rows)
        export_percentage_rows = deepcopy(percentage_rows)

        (
            date_columns,
            summary_rows,
            percentage_rows,
            grand_totals,
            omitted_zero_dates,
        ) = _filter_zero_only_dates(
            date_columns,
            summary_rows,
            percentage_rows,
            grand_totals,
        )
        date_groups = _build_date_groups(date_columns)

    context = {
        "title": "Branch Stock Summary",
        "subtitle": "Branch Stock Summary",
        "branch_options": branch_options,
        "start_date": start_date,
        "end_date": end_date,
        "filters_applied": filters_applied,
        "date_columns": date_columns,
        "export_date_columns": export_date_columns,
        "summary_rows": summary_rows,
        "export_summary_rows": export_summary_rows,
        "percentage_rows": percentage_rows,
        "export_percentage_rows": export_percentage_rows,
        "date_groups": date_groups,
        "omitted_zero_dates": omitted_zero_dates,
        "grand_totals_list": grand_totals,
        "total_capacity": total_capacity,
        "grand_total_all": sum(grand_totals) if grand_totals else 0,
    }

    if is_admin:
        context["breadcrumbs_url"] = reverse("admin:app_list", kwargs={"app_label": "supplychain"})
        context["breadcrumbs"] = [{"name": "Supply Chain Application", "url": context["breadcrumbs_url"]}]
    else:
        context["breadcrumbs_url"] = "/bom"
        context["breadcrumbs"] = [{"name": "Supply Chain", "url": "/bom"}]

    return context


def _export_summary_excel(context: Dict[str, object]) -> HttpResponse:
    summary_rows: List[Dict[str, object]] = context.get("export_summary_rows") or context.get("summary_rows", [])  # type: ignore[assignment]
    percentage_rows: List[Dict[str, object]] = context.get("export_percentage_rows") or context.get("percentage_rows", [])  # type: ignore[assignment]
    date_columns: DateSequence = context.get("export_date_columns") or context["date_columns"]  # type: ignore[assignment]

    headers = ["Branch Code", "Branch Description", "Warehouse Capacity (pallet)"]
    date_headers = [day.strftime("%d %b %Y") for day in date_columns]
    headers.extend(date_headers)

    summary_records: List[Dict[str, object]] = []
    for row in summary_rows:
        record: Dict[str, object] = {
            "Branch Code": row["branch_code"],
            "Branch Description": row["branch_description"],
            "Warehouse Capacity (pallet)": row["warehouse_capacity"],
        }
        for header, value in zip(date_headers, row["values"]):
            record[header] = value
        summary_records.append(record)

    percentage_records: List[Dict[str, object]] = []
    for row in percentage_rows:
        record = {
            "Branch Code": row["branch_code"],
            "Branch Description": row["branch_description"],
            "Warehouse Capacity (pallet)": row["warehouse_capacity"],
        }
        for header, cell_data in zip(date_headers, row["values"]):
            percent = cell_data.get("percent", 0)
            record[header] = f"{percent:.1f}%"
        percentage_records.append(record)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        workbook = writer.book
        worksheet = workbook.create_sheet("Summary")
        if (
            "Sheet" in workbook.sheetnames
            and workbook["Sheet"].max_row == 1
            and workbook["Sheet"].max_column == 1
        ):
            workbook.remove(workbook["Sheet"])

        current_row = 1
        col_offset = 4

        if summary_records:
            worksheet.cell(row=current_row, column=1, value="Unit Pallet")
            summary_frame = pd.DataFrame(summary_records, columns=headers)
            summary_frame.to_excel(
                writer,
                index=False,
                sheet_name="Summary",
                startrow=current_row,
            )
            current_row += len(summary_records) + 3

        if percentage_records:
            worksheet.cell(row=current_row, column=1, value="% Capacity")
            percentage_frame = pd.DataFrame(percentage_records, columns=headers)
            percentage_frame.to_excel(
                writer,
                index=False,
                sheet_name="Summary",
                startrow=current_row,
            )

            percent_table_data_row = current_row + 2
            for row_idx, row in enumerate(
                percentage_rows, start=percent_table_data_row
            ):
                for col_idx, cell_data in enumerate(row["values"], start=col_offset):
                    percent = cell_data["percent"]
                    cell = worksheet.cell(row=row_idx, column=col_idx)

                    if percent < 30:
                        cell.fill = FILL_LOW
                    elif percent >= 70 and percent < 100:
                        cell.fill = FILL_MEDIUM
                    elif percent >= 100:
                        cell.fill = FILL_HIGH
                    else:
                        cell.fill = FILL_STANDARD

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=branchstock_summary.xlsx"
    return response
