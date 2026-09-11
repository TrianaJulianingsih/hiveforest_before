import csv
from decimal import Decimal
import io
from io import BytesIO

from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Prefetch, Q

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font

from apps.bom.models import FreightCost, FreightCostDetail
from apps.supplychain.models import DistributorItem


REPORT_COLUMNS = [
    ("freight_number", "FREIGHT NUMBER", "freight__name"),
    ("shipping_date", "SHIPPING_DATE", "freight__shipping_date"),
    ("from_location", "FROM_LOCATION", "from_location"),
    ("to_location", "TO_LOCATION", "to_location"),
    ("expedition_name", "EXPEDITION_NAME", "expedition_name"),
    ("expedition_type", "EXPEDITION_TYPE", "expedition_type"),
    ("packaging_type", "PACKAGING_TYPE", "packaging_type_id"),
    ("item_code", "ITEM_CODE", "item_code"),
    ("item_description", "ITEM_DESCRIPTION", "item_description"),
    ("qty_freight", "QTY_FREIGHT", "qty_freight"),
    ("total_weight", "TOTAL_WEIGHT", "total_weight"),
    ("nama_principal", "NAMA_PRINCIPAL", "principal__name"),
    ("group_produk", "GROUP_PRODUK", "group_produk"),
    ("total_freight", "TOTAL_FREIGHT", "total_freight"),
    ("freight_type", "FREIGHT_TYPE", "freight__freight_type"),
    ("total_cost", "TOTAL_COST", "total_cost"),
    ("kode_cab", "KODE_CAB", "kode_cab"),
    ("nama_cab", "NAMA_CAB", "nama_cab"),
    ("item_group", "ItemGroup", "item_group"),
]

DECIMAL_COLUMNS = {"qty_freight", "total_weight", "total_freight", "total_cost"}
EXPORT_CHUNK_SIZE = 5000
EXPORT_PROGRESS_CACHE_TIMEOUT = 60 * 15
EXPORT_PROGRESS_PREPARE_PERCENT = 10
EXPORT_PROGRESS_BUILD_PERCENT = 90
EXPORT_PROGRESS_READY_PERCENT = 95


def get_request_data(request):
    return request.POST if request.method == "POST" else request.GET


def get_export_progress_cache_key(export_token):
    return f"freight_cost_export_progress:{export_token}"


def set_export_progress(export_token, *, percent, message, meta="", state="running"):
    if not export_token:
        return

    bounded_percent = max(0, min(100, int(percent)))
    cache.set(
        get_export_progress_cache_key(export_token),
        {
            "percent": bounded_percent,
            "message": message,
            "meta": meta,
            "state": state,
        },
        EXPORT_PROGRESS_CACHE_TIMEOUT,
    )


def get_export_progress(export_token):
    if not export_token:
        return None
    return cache.get(get_export_progress_cache_key(export_token))


def get_selected_year(request):
    year_value = get_request_data(request).get("year", "").strip()
    return int(year_value) if year_value.isdigit() else None


def get_available_years():
    years = FreightCost.objects.filter(
        deleted=False, shipping_date__isnull=False
    ).dates("shipping_date", "year", order="DESC")
    return [year.year for year in years]


def get_freight_cost_report_queryset(request):
    selected_year = get_selected_year(request)
    queryset = (
        FreightCostDetail.objects.filter(deleted=False, freight__deleted=False)
        .select_related(
            "freight",
            "product",
            "product__subgroup",
            "product__subgroup__group",
            "product_distributor",
            "product_distributor__product",
            "product_distributor__group",
            "packaging_type",
            "principal",
        )
        .prefetch_related(
            Prefetch(
                "product__distributoritem_set",
                queryset=DistributorItem.objects.select_related("group"),
            )
        )
        .order_by("-freight__shipping_date", "freight__name", "item_description", "id")
    )

    if selected_year:
        queryset = queryset.filter(freight__shipping_date__year=selected_year)

    return queryset


def get_freight_cost_export_queryset(request):
    selected_year = get_selected_year(request)
    queryset = (
        FreightCostDetail.objects.filter(deleted=False, freight__deleted=False)
        .select_related(
            "freight",
            "product",
            "product__subgroup",
            "product_distributor",
            "product_distributor__product",
            "product_distributor__product__subgroup",
            "product_distributor__product__packaging",
            "product_distributor__group",
            "packaging_type",
            "principal",
        )
        .order_by("freight__burden_type", "-freight__shipping_date", "freight__name", "id")
    )

    if selected_year:
        queryset = queryset.filter(freight__shipping_date__year=selected_year)

    return queryset


def apply_datatable_search(queryset, search_value):
    if not search_value:
        return queryset

    return queryset.filter(
        Q(freight__name__icontains=search_value)
        | Q(from_location__icontains=search_value)
        | Q(to_location__icontains=search_value)
        | Q(kode_cab__icontains=search_value)
        | Q(nama_cab__icontains=search_value)
        | Q(expedition_name__icontains=search_value)
        | Q(expedition_type__icontains=search_value)
        | Q(item_code__icontains=search_value)
        | Q(item_description__icontains=search_value)
        | Q(principal__name__icontains=search_value)
        | Q(group_produk__icontains=search_value)
        | Q(item_group__icontains=search_value)
        | Q(freight__freight_type__icontains=search_value)
    )


def format_report_value(field_name, value):
    if value in (None, ""):
        return "-"
    if field_name == "shipping_date":
        return value.strftime("%d-%b-%Y") if hasattr(value, "strftime") else value
    if field_name in DECIMAL_COLUMNS:
        try:
            return f"{Decimal(value):,.2f}"
        except Exception:
            return value
    return value


def build_datatable_row(detail):
    row_map = build_freight_cost_report_row(detail)
    return {
        field_name: format_report_value(field_name, row_map[field_name])
        for field_name, _, _ in REPORT_COLUMNS
    }


def build_freight_cost_report_row(detail):
    freight = detail.freight
    return {
        "freight_number": freight.name if freight else "",
        "shipping_date": freight.shipping_date if freight else None,
        "from_location": detail.from_location,
        "to_location": detail.to_location,
        "expedition_name": detail.expedition_name,
        "expedition_type": detail.expedition_type,
        "packaging_type": detail.packaging_type_value,
        "item_code": detail.item_code,
        "item_description": detail.item_description,
        "qty_freight": detail.qty_freight,
        "total_weight": detail.total_weight,
        "nama_principal": detail.nama_principal,
        "group_produk": detail.group_produk,
        "total_freight": detail.total_freight,
        "freight_type": freight.freight_type if freight else "",
        "total_cost": detail.total_cost,
        "kode_cab": detail.kode_cab,
        "nama_cab": detail.nama_cab,
        "item_group": detail.item_group_name,
    }


def build_freight_cost_report_rows(queryset):
    rows = []

    for detail in queryset:
        row_map = build_freight_cost_report_row(detail)
        rows.append([row_map[field_name] for field_name, _, _ in REPORT_COLUMNS])

    return rows


def iter_freight_cost_report_rows(queryset, progress_callback=None):
    for detail in queryset.iterator(chunk_size=EXPORT_CHUNK_SIZE):
        yield build_freight_cost_report_row(detail)
        if progress_callback:
            progress_callback()


def get_report_year(queryset):
    detail = queryset.exclude(freight__shipping_date__isnull=True).first()
    if detail and detail.freight and detail.freight.shipping_date:
        return detail.freight.shipping_date.year
    return timezone.localdate().year


def _make_write_only_cell(worksheet, value, *, bold=False, size=None, alignment=None):
    cell = WriteOnlyCell(worksheet, value=value)
    if bold or size:
        cell.font = Font(bold=bold, size=size)
    if alignment:
        cell.alignment = alignment
    return cell


def write_sheet_content(worksheet, sheet_title, sheet_subtitle, rows):
    worksheet.append(
        [
            _make_write_only_cell(
                worksheet,
                sheet_title,
                bold=True,
                size=12,
                alignment=Alignment(horizontal="left"),
            )
        ]
    )
    worksheet.append(
        [
            _make_write_only_cell(
                worksheet,
                sheet_subtitle,
                bold=True,
                size=12,
                alignment=Alignment(horizontal="left"),
            )
        ]
    )
    worksheet.append([])
    worksheet.append(
        [
            _make_write_only_cell(worksheet, label, bold=True)
            for _, label, _ in REPORT_COLUMNS
        ]
    )

    for row_map in rows:
        row_values = []
        for field_name, _, _ in REPORT_COLUMNS:
            value = row_map[field_name]
            if field_name in DECIMAL_COLUMNS and value not in (None, ""):
                try:
                    value = float(Decimal(value))
                except Exception:
                    pass
            row_values.append(value if value is not None else "")
        worksheet.append(row_values)


def build_burden_sheet_rows(queryset, burden_type, progress_callback=None):
    return iter_freight_cost_report_rows(
        queryset.filter(freight__burden_type=burden_type),
        progress_callback=progress_callback,
    )


def build_csv_export_content(queryset, progress_callback=None):
    header = ["BURDEN_TYPE"] + [label for _, label, _ in REPORT_COLUMNS]
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(header)

    for detail in queryset.iterator(chunk_size=EXPORT_CHUNK_SIZE):
        row_map = build_freight_cost_report_row(detail)
        burden_type = detail.freight.burden_type if detail.freight else ""
        writer.writerow(
            [burden_type]
            + [format_report_value(field_name, row_map[field_name]) for field_name, _, _ in REPORT_COLUMNS]
        )
        if progress_callback:
            progress_callback()

    return output.getvalue()


def build_export_progress_updater(export_token, total_rows, *, message):
    if not export_token:
        return None

    safe_total_rows = max(total_rows, 1)
    progress_state = {"processed": 0}

    def update_progress(force=False):
        progress_state["processed"] += 1
        processed_rows = min(progress_state["processed"], total_rows)
        if not force and processed_rows % 100 != 0 and processed_rows != total_rows:
            return

        percent = EXPORT_PROGRESS_PREPARE_PERCENT + int(
            (processed_rows / safe_total_rows)
            * (EXPORT_PROGRESS_BUILD_PERCENT - EXPORT_PROGRESS_PREPARE_PERCENT)
        )
        set_export_progress(
            export_token,
            percent=percent,
            message=message,
            meta=f"{processed_rows:,} / {total_rows:,} baris",
        )

    return update_progress


@login_required
def freight_cost_list(request):
    context = {
        "selected_year": get_selected_year(request),
        "year_choices": get_available_years(),
    }
    return render(request, "freight_cost/list.html", context)


@login_required
def freight_cost_data(request):
    request_data = get_request_data(request)
    draw = int(request_data.get("draw", 1))
    start = int(request_data.get("start", 0))
    length = int(request_data.get("length", 25))
    search_value = request_data.get("search[value]", "").strip()
    order_column = int(request_data.get("order[0][column]", 0))
    order_dir = request_data.get("order[0][dir]", "asc")

    base_queryset = get_freight_cost_report_queryset(request)
    total_records = base_queryset.count()
    filtered_queryset = apply_datatable_search(base_queryset, search_value)
    total_filtered = filtered_queryset.count()

    if 0 <= order_column < len(REPORT_COLUMNS):
        order_field = REPORT_COLUMNS[order_column][2]
        if order_field:
            if order_dir == "desc":
                order_field = f"-{order_field}"
            filtered_queryset = filtered_queryset.order_by(order_field)

    if length != -1:
        filtered_queryset = filtered_queryset[start : start + length]

    data = [build_datatable_row(detail) for detail in filtered_queryset]

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
        }
    )


@login_required
def freight_cost_export_progress(request):
    export_token = request.GET.get("export_token", "").strip()
    progress_data = get_export_progress(export_token)

    if progress_data is None:
        return JsonResponse(
            {
                "found": False,
                "percent": 0,
                "message": "Menunggu proses export dimulai...",
                "meta": "",
                "state": "pending",
            }
        )

    return JsonResponse({"found": True, **progress_data})


@login_required
def freight_cost_export(request):
    export_format = request.GET.get("format", "xlsx").strip().lower()
    export_token = request.GET.get("export_token", "").strip()
    set_export_progress(
        export_token,
        percent=0,
        message="Menyiapkan file export...",
        meta="Mengambil data dari server...",
    )

    queryset = get_freight_cost_export_queryset(request)
    total_rows = queryset.count()
    report_year = get_report_year(queryset)
    set_export_progress(
        export_token,
        percent=EXPORT_PROGRESS_PREPARE_PERCENT,
        message="Menyiapkan file export...",
        meta=f"{total_rows:,} baris ditemukan",
    )

    try:
        if export_format == "csv":
            progress_callback = build_export_progress_updater(
                export_token,
                total_rows,
                message="Menyusun file CSV...",
            )
            csv_content = build_csv_export_content(
                queryset,
                progress_callback=progress_callback,
            )
            csv_bytes = csv_content.encode("utf-8")
            set_export_progress(
                export_token,
                percent=EXPORT_PROGRESS_READY_PERCENT,
                message="File CSV siap diunduh.",
                meta=f"Ukuran file {len(csv_bytes):,} byte",
            )

            response = HttpResponse(
                csv_bytes,
                content_type="text/csv; charset=utf-8",
            )
            response["Content-Disposition"] = 'attachment; filename="freight_cost_report.csv"'
            response["Content-Length"] = str(len(csv_bytes))
            return response

        workbook = Workbook(write_only=True)

        progress_callback = build_export_progress_updater(
            export_token,
            total_rows,
            message="Menyusun workbook Excel...",
        )

        oi_sheet = workbook.create_sheet(title="OI BURDEN")
        write_sheet_content(
            oi_sheet,
            "PT MERAPI UTAMA PHARMA",
            f"KLAIM ONGKOS ANGKUT PRODUK ONE OTSUKA {report_year}",
            build_burden_sheet_rows(
                queryset,
                FreightCost.BURDEN_TYPE_OI,
                progress_callback=progress_callback,
            ),
        )

        mup_sheet = workbook.create_sheet(title="MUP BURDEN")
        write_sheet_content(
            mup_sheet,
            "PT MERAPI UTAMA PHARMA",
            f"ONGKOS ANGKUT PRODUK OTSUKA {report_year} (MUP BURDEN)",
            build_burden_sheet_rows(
                queryset,
                FreightCost.BURDEN_TYPE_MUP,
                progress_callback=progress_callback,
            ),
        )

        set_export_progress(
            export_token,
            percent=EXPORT_PROGRESS_BUILD_PERCENT,
            message="Menyimpan workbook Excel...",
            meta=f"{total_rows:,} baris diproses",
        )

        output = BytesIO()
        workbook.save(output)
        file_size = output.tell()

        set_export_progress(
            export_token,
            percent=EXPORT_PROGRESS_READY_PERCENT,
            message="File Excel siap diunduh.",
            meta=f"Ukuran file {file_size:,} byte",
        )

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="freight_cost_report.xlsx"'
        response["Content-Length"] = str(file_size)
        return response
    except Exception:
        set_export_progress(
            export_token,
            percent=0,
            message="Export gagal diproses.",
            meta="Silakan coba kembali.",
            state="failed",
        )
        raise
