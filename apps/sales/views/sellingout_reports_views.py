import ast
import calendar
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

# Sellingout report views.
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear, NullIf
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.sales.models.product_models import Product
from apps.sales.models.sales_models import AnnualTarget, SellingOut
from apps.sales.models.territory_models import SalesArea, SalesRegion
from apps.supplychain.models.distributions_models import Branch

MONTHS = [(number, calendar.month_abbr[number]) for number in range(1, 13)]

REPORT_MODELS = [
    ("tmbg", "Period View"),
    ("cibg", "Region View"),
]


def _business_choices():
    """Pasangan (id, label) business aktif dari humancapital_business."""
    from apps.humancapital.models.business_models import Business

    return [
        (business_id, _text_or(code, name))
        for business_id, code, name in Business.objects.filter(
            deleted=False, status=1
        )
        .order_by("code")
        .values_list("id", "code", "name")
    ]


def _cibg_squeeze(value):
    """UPPER + TRIM + buang SEMUA whitespace."""

    return re.sub(r"\s+", "", str(value or "").strip().upper())


def _cibg_branch_key(code, initial, shortname):
    """Kunci pencocokan branch ke sales area."""

    branch_code = _cibg_squeeze(code)
    branch_initial = _cibg_squeeze(initial)

    if "JKT1" in branch_initial:
        return "JAKARTA 1"
    if "JKT2" in branch_initial:
        return "JAKARTA 2"
    if "JKT3" in branch_initial or "DPK" in branch_initial:
        return "JAKARTA 3"
    if branch_code == "BLP" or branch_initial == "BLP":
        return "LAMPUNG"
    return _normalize_cibg_code(shortname)


def _apply_business_scope(queryset, allowed_business_ids, field="business_id"):
    """None = tanpa batas (superuser); set kosong = tidak boleh melihat apa pun."""

    if allowed_business_ids is None:
        return queryset
    business_ids = sorted(int(value) for value in allowed_business_ids)
    if not business_ids:
        return queryset.none()
    return queryset.filter(**{f"{field}__in": business_ids})


def _apply_id_filter(queryset, field, values):
    if not values:
        return queryset
    return queryset.filter(**{f"{field}__in": [int(value) for value in values]})


def _distinct_options(rows):
    """Pasangan (id, label) unik, diurutkan berdasar label. Label kosong dibuang."""

    unique = {(option_id, label) for option_id, label in rows if option_id and label}
    return [
        {"id": option_id, "label": label}
        for option_id, label in sorted(unique, key=lambda item: (item[1], item[0]))
    ]


def _text_or(value, *fallbacks):
    """Pasangan Python dari COALESCE(NULLIF(TRIM(x), ''), ...)."""

    for candidate in (value, *fallbacks):
        text = str(candidate or "").strip()
        if text:
            return text
    return ""


def _quantity_sum():
    return Sum(
        F("qty") * Coalesce(
            NullIf(F("item__salessize"), Value(Decimal("0"))),
            Value(Decimal("1")),
        ),
        output_field=DecimalField(max_digits=30, decimal_places=2),
    )


def _format_number(value, decimals=0):
    """Format a number using the existing English-style report format."""

    value = Decimal(value or 0)
    quantum = Decimal(1).scaleb(-decimals)
    value = value.quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{value:,.{decimals}f}"


def _format_percentage(value):
    if value is None:
        return "-"
    return f"{Decimal(value):,.2f}%"


def _number_cell(value):
    value = Decimal(value or 0)
    if not value:
        return {"display": "-", "full": "-"}
    return {
        "display": _format_number(value),
        "full": _format_number(value, 2),
    }


def _percentage_cell(value):
    trend = ""
    display_value = value
    if value is not None:
        if value > 0:
            trend = "pos"
        elif value < 0:
            trend = "neg"
        display_value = abs(value)
    return {
        "display": _format_percentage(display_value),
        "full": _format_percentage(value),
        "trend": trend,
    }


def _achievement_cell(value):
    trend = ""
    if value is not None:
        trend = "ach-low" if value < Decimal("100") else "ach-high"
    return {
        "display": _format_percentage(value),
        "full": _format_percentage(value),
        "trend": trend,
    }


def _blank_cell():
    return {"display": "", "full": "Belum diisi"}


def _parse_filter_id(value):
    try:
        value = int(str(value or "").strip())
    except (TypeError, ValueError):
        return ""
    return str(value) if value > 0 else ""


def _parse_filter_ids(values):
    parsed = []
    for value in values:
        value = _parse_filter_id(value)
        if value and value not in parsed:
            parsed.append(value)
    return parsed


def _get_allowed_business_ids(user):
    """Return business IDs allowed for the current user's active assignment. """
    
    all_business_ids = {str(business_id) for business_id, _ in _business_choices()}
    if user.is_superuser:
        return None

    try:
        person_id = user.userprofile.person_id
    except (AttributeError, ObjectDoesNotExist):
        return set()

    if not person_id:
        return set()

    # Business is not stored directly on Assignment. The existing territory
    # structure links an assignment's position organization to a region, and
    # the region owns the business.
    from apps.humancapital.models.structure_models import Assignment
    from apps.sales.models.territory_models import SalesRegion

    today = timezone.localdate()
    active_date_filter = (
        (Q(effective__isnull=True) | Q(effective__lte=today))
        & (Q(terminated__isnull=True) | Q(terminated__gte=today))
    )

    organization_ids = (
        Assignment.objects.filter(
            employee__person_id=person_id,
            status=1,
            deleted=False,
        )
        .filter(active_date_filter)
        .exclude(position__organization_id__isnull=True)
        .values_list("position__organization_id", flat=True)
    )

    business_ids = (
        SalesRegion.objects.filter(
            position__organization_id__in=organization_ids,
            status=1,
            deleted=False,
            business_id__in=all_business_ids,
        )
        .filter(active_date_filter)
        .exclude(business_id__isnull=True)
        .values_list("business_id", flat=True)
        .distinct()
    )

    return {str(business_id) for business_id in business_ids}


def _business_options(allowed_business_ids):
    return [
        {"id": business_id, "label": label}
        for business_id, label in _business_choices()
        if allowed_business_ids is None
        or str(business_id) in allowed_business_ids
    ]


def _normalize_business(value, allowed_business_ids=None):
    value = _parse_filter_id(value)
    valid_business_ids = (
        allowed_business_ids
        if allowed_business_ids is not None
        else {str(business_id) for business_id, _ in _business_choices()}
    )
    return value if value in valid_business_ids else ""


def _resolve_selected_business(value, allowed_business_ids):
    selected_business = _normalize_business(
        value,
        allowed_business_ids,
    )

    # A user assigned to exactly one business should not need to choose it
    # manually. Superusers keep the blank value, which means All Business.
    if (
        not selected_business
        and allowed_business_ids is not None
        and len(allowed_business_ids) == 1
    ):
        return next(iter(allowed_business_ids))

    return selected_business


def _get_filter_options(
    selected_business,
    selected_groups,
    selected_subgroups,
    allowed_business_ids=None,
):
    master = Product.objects.filter(
        deleted=False,
        status=1,
        subgroup__deleted=False,
        subgroup__status=1,
        subgroup__group__deleted=False,
        subgroup__group__status=1,
    )
    master = _apply_business_scope(master, allowed_business_ids)
    if selected_business:
        master = master.filter(business_id=int(selected_business))

    groups = _distinct_options(
        (group_id, _text_or(name, code))
        for group_id, name, code in master.values_list(
            "subgroup__group_id",
            "subgroup__group__name",
            "subgroup__group__code",
        )
    )

    subgroup_scope = _apply_id_filter(master, "subgroup__group_id", selected_groups)
    subgroups = _distinct_options(
        (subgroup_id, _text_or(name))
        for subgroup_id, name in subgroup_scope.values_list(
            "subgroup_id",
            "subgroup__name",
        )
    )

    product_scope = _apply_id_filter(subgroup_scope, "subgroup_id", selected_subgroups)
    product_options = _distinct_options(
        (product_id, _text_or(name))
        for product_id, name in product_scope.values_list("id", "name")
    )

    return {
        "groups": groups,
        "subgroups": subgroups,
        "product_options": product_options,
    }


def _get_product_options(selected_business, allowed_business_ids=None):
    products = Product.objects.filter(deleted=False, status=1)
    products = _apply_business_scope(products, allowed_business_ids)
    if selected_business:
        products = products.filter(business_id=int(selected_business))

    return _distinct_options(
        (product_id, _text_or(name))
        for product_id, name in products.values_list("id", "name")
    )


def _get_available_years():
    # order_by() wajib dikosongkan: Meta.ordering SellingOut ikut masuk ke
    # SELECT pada query DISTINCT, sehingga DISTINCT-nya jadi per (year, name).
    years = (
        SellingOut.objects.filter(status=1, deleted=False)
        .order_by()
        .annotate(year=ExtractYear("invoice_date"))
        .values_list("year", flat=True)
        .distinct()
    )
    return sorted(year for year in years if year is not None)


def _ytd_months(selected_year):
    """Jumlah bulan Year-To-Date: Januari sampai bulan berjalan."""

    today = timezone.localdate()
    if selected_year > today.year:
        return 0
    if selected_year < today.year:
        return 12
    return today.month


def _growth(current_value, previous_value):
    if not previous_value:
        return None
    return (current_value - previous_value) / previous_value * Decimal("100")


def _achievement(actual_value, budget_value):
    if not budget_value:
        return None
    return actual_value / budget_value * Decimal("100")


def _metric_row(
    label, values, total, ytd, percentage=False, row_class="", cell_factory=None
):
    if cell_factory is None:
        cell_factory = _percentage_cell if percentage else _number_cell
    return {
        "label": label,
        "values": [cell_factory(value) for value in values],
        "total": cell_factory(total),
        "ytd": cell_factory(ytd),
        "row_class": row_class,
    }


def _build_metric_rows(
    previous_values,
    current_values,
    budget_values,
    ytd_months,
    from_month=1,
    to_month=12,
):
    # YTD dihitung dari Januari pada array 12 bulan yang UTUH, sebelum dipotong
    # rentang filter -- kalau dihitung setelah dipotong, nilainya selalu sama
    # dengan Total.
    previous_ytd = sum(previous_values[:ytd_months], Decimal("0"))
    current_ytd = sum(current_values[:ytd_months], Decimal("0"))
    budget_ytd = sum(budget_values[:ytd_months], Decimal("0"))

    month_start = from_month - 1
    month_end = to_month
    previous_values = previous_values[month_start:month_end]
    current_values = current_values[month_start:month_end]
    budget_values = budget_values[month_start:month_end]

    previous_total = sum(previous_values, Decimal("0"))
    current_total = sum(current_values, Decimal("0"))
    budget_total = sum(budget_values, Decimal("0"))

    growth_values = [
        _growth(current, previous)
        for current, previous in zip(current_values, previous_values)
    ]
    growth_total = _growth(current_total, previous_total)
    growth_ytd = _growth(current_ytd, previous_ytd) if ytd_months else None

    achievement_values = [
        _achievement(current, budget)
        for current, budget in zip(current_values, budget_values)
    ]
    achievement_total = _achievement(current_total, budget_total)
    achievement_ytd = _achievement(current_ytd, budget_ytd) if ytd_months else None

    return [
        _metric_row(
            "Pre. Yr Act.",
            previous_values,
            previous_total,
            previous_ytd,
        ),
        _metric_row(
            "Cur. Yr Bud.",
            budget_values,
            budget_total,
            budget_ytd,
            row_class="metric-budget",
        ),
        _metric_row(
            "Cur. Yr Act.",
            current_values,
            current_total,
            current_ytd,
        ),
        _metric_row(
            "Growth %",
            growth_values,
            growth_total,
            growth_ytd,
            percentage=True,
            row_class="metric-highlight",
        ),
        _metric_row(
            "Achiev. %",
            achievement_values,
            achievement_total,
            achievement_ytd,
            row_class="metric-achievement",
            cell_factory=_achievement_cell,
        ),
    ]


def _tokens(value):
    return re.findall(r"\S+", str(value or "").strip())


def _split_product_name(product_name, subgroup_name):
    """Split before the first number so the right column starts with a number."""
    product_name = " ".join(_tokens(product_name))
    subgroup_name = " ".join(_tokens(subgroup_name))

    product_tokens = _tokens(product_name)
    for index, token in enumerate(product_tokens):
        number_match = re.search(r"\d+(?:[.,]\d+)?", token)
        if not number_match:
            continue

        prefix_token = token[:number_match.start()].strip()
        number_token = token[number_match.start():]

        left_tokens = product_tokens[:index]
        if prefix_token:
            left_tokens.append(prefix_token)

        right_tokens = [number_token, *product_tokens[index + 1:]]
        left_part = " ".join(left_tokens).strip() or subgroup_name
        right_part = " ".join(right_tokens).strip()
        return left_part, right_part

    return product_name, ""


def _variant_sort_key(product):
    brand = product["brand"].casefold()
    variant = product["variant"] or product["product_name"]
    variant = variant.casefold()
    number_match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)", variant)

    if number_match:
        number = Decimal(number_match.group(1).replace(",", "."))
        return brand, 0, number, variant

    return brand, 1, Decimal("0"), variant


def _empty_product(
    group_id,
    group_name,
    subgroup_id,
    subgroup_name,
    product_id,
    product_name,
):
    return {
        "group_id": group_id,
        "group_name": group_name or "",
        "subgroup_id": subgroup_id,
        "subgroup_name": subgroup_name or "",
        "product_id": product_id,
        "product_name": product_name or "",
        "value_previous": [Decimal("0")] * 12,
        "value_current": [Decimal("0")] * 12,
        "value_budget": [Decimal("0")] * 12,
        "quantity_previous": [Decimal("0")] * 12,
        "quantity_current": [Decimal("0")] * 12,
        "quantity_budget": [Decimal("0")] * 12,
    }


def _build_product_sections(
    product,
    ytd_months,
    from_month=1,
    to_month=12,
):
    return [
        {
            "label": "Value",
            "unit": "('In Mio Rupiah)",
            "rowspan": 5,
            "rows": _build_metric_rows(
                [
                    value / Decimal("1000000")
                    for value in product["value_previous"]
                ],
                [
                    value / Decimal("1000000")
                    for value in product["value_current"]
                ],
                [
                    value / Decimal("1000000")
                    for value in product["value_budget"]
                ],
                ytd_months,
                from_month,
                to_month,
            ),
        },
        {
            "label": "Quantity",
            "unit": "(tablets)",
            "rowspan": 5,
            "rows": _build_metric_rows(
                product["quantity_previous"],
                product["quantity_current"],
                product["quantity_budget"],
                ytd_months,
                from_month,
                to_month,
            ),
        },
    ]


def _sum_products(
    products,
    group_id,
    group_name,
    subgroup_id,
    subgroup_name,
):
    subtotal = _empty_product(
        group_id,
        group_name,
        subgroup_id,
        subgroup_name or group_name,
        None,
        subgroup_name or group_name,
    )
    for product in products:
        for field in (
            "value_previous",
            "value_current",
            "value_budget",
            "quantity_previous",
            "quantity_current",
            "quantity_budget",
        ):
            subtotal[field] = [
                subtotal_value + product_value
                for subtotal_value, product_value in zip(
                    subtotal[field],
                    product[field],
                )
            ]
    return subtotal


def _load_budget(
    products,
    selected_year,
    from_month,
    to_month,
    selected_business,
    selected_groups,
    selected_subgroups,
    selected_products,
    allowed_business_ids,
):
    """Isi value_budget/quantity_budget dari sales_annualtarget.

    Sumbernya per product + bulan + salestype; report tidak memecah salestype,
    jadi keempat sector dijumlahkan. DISTINCT ON dipakai supaya kalau satu
    product+bulan+salestype punya lebih dari satu version, yang terpakai hanya
    version tertinggi -- bukan dijumlahkan (itu akan menggandakan target).

    Produk yang punya target tapi belum ada penjualannya TIDAK diabaikan:
    entry-nya dibuat di sini juga, supaya achievement 0% tetap terlihat alih-alih
    barisnya hilang sama sekali dari report.
    """
    targets = AnnualTarget.objects.filter(
        deleted=False,
        status=1,
        product__subgroup__group__isnull=False,
        date__year=selected_year,
        date__month__gte=from_month,
        date__month__lte=to_month,
    )
    targets = _apply_business_scope(
        targets, allowed_business_ids, field="product__business_id"
    )
    if selected_business:
        targets = targets.filter(product__business_id=int(selected_business))

    targets = _apply_id_filter(targets, "product__subgroup__group_id", selected_groups)
    targets = _apply_id_filter(targets, "product__subgroup_id", selected_subgroups)
    targets = _apply_id_filter(targets, "product_id", selected_products)

    budget_rows = (
        targets.order_by(
            "product_id",
            "date",
            "type_id",
            F("version").desc(nulls_last=True),
        )
        .distinct("product_id", "date", "type_id")
        .values_list(
            "product__subgroup__group_id",
            "product__subgroup__group__name",
            "product__subgroup__group__code",
            "product__subgroup_id",
            "product__subgroup__name",
            "product_id",
            "product__name",
            "date",
            "qty",
            "value",
        )
    )

    for (
        group_id,
        group_name,
        group_code,
        subgroup_id,
        subgroup_name,
        product_id,
        product_name,
        target_date,
        budget_quantity,
        budget_value,
    ) in budget_rows:
        product_name = _text_or(product_name)
        product_key = (subgroup_id, product_id or product_name)
        if product_key not in products:
            products[product_key] = _empty_product(
                group_id,
                _text_or(group_name, group_code),
                subgroup_id,
                _text_or(subgroup_name),
                product_id,
                product_name,
            )

        product = products[product_key]
        product["value_budget"][target_date.month - 1] += Decimal(budget_value or 0)
        product["quantity_budget"][target_date.month - 1] += Decimal(budget_quantity or 0)


def _build_product_rows(
    products,
    ytd_months,
    from_month=1,
    to_month=12,
):
    grouped_products = defaultdict(lambda: defaultdict(list))
    for product in products.values():
        group_key = (product["group_id"], product["group_name"])
        subgroup_key = (product["subgroup_id"], product["subgroup_name"])
        grouped_products[group_key][subgroup_key].append(product)

    product_rows = []
    for (group_id, group_name), subgroup_groups in sorted(
        grouped_products.items(),
        key=lambda item: (item[0][1].casefold(), item[0][0] or 0),
    ):
        all_group_products = []

        for (subgroup_id, subgroup_name), subgroup_products in sorted(
            subgroup_groups.items(),
            key=lambda item: (item[0][1].casefold(), item[0][0] or 0),
        ):
            sorted_products = []

            for product in subgroup_products:
                brand, variant = _split_product_name(
                    product["product_name"],
                    subgroup_name,
                )
                product["brand"] = brand
                product["variant"] = variant
                sorted_products.append(product)

            for product in sorted(sorted_products, key=_variant_sort_key):
                product_rows.append(
                    {
                        "block_class": "",
                        "brand_class": "product-brand",
                        "variant_class": "product-variant",
                        "brand": product["brand"],
                        "variant": product["variant"],
                        "rowspan": 10,
                        "sections": _build_product_sections(
                            product,
                            ytd_months,
                            from_month,
                            to_month,
                        ),
                    }
                )

            all_group_products.extend(subgroup_products)

            if len(subgroup_groups) > 1:
                subtotal = _sum_products(
                    subgroup_products,
                    group_id,
                    group_name,
                    subgroup_id,
                    subgroup_name,
                )
                product_rows.append(
                    {
                        "block_class": "subtotal-row",
                        "brand_class": "subtotal-brand",
                        "variant_class": "subtotal-variant",
                        "brand": "Sub Total",
                        "variant": subgroup_name,
                        "rowspan": 10,
                        "sections": _build_product_sections(
                            subtotal,
                            ytd_months,
                            from_month,
                            to_month,
                        ),
                    }
                )

        group_total = _sum_products(
            all_group_products,
            group_id,
            group_name,
            None,
            None,
        )
        product_rows.append(
            {
                "block_class": "group-total-row",
                "brand_class": "group-total-brand",
                "variant_class": "group-total-variant",
                "brand": group_name,
                "variant": "Total",
                "rowspan": 10,
                "sections": _build_product_sections(
                    group_total,
                    ytd_months,
                    from_month,
                    to_month,
                ),
            }
        )

    return product_rows


def _normalize_cibg_code(value):
    return " ".join(str(value or "").split()).upper()


def _normalize_cibg_shortname_key(value):
    return _normalize_cibg_code(value)


def _parse_cibg_description(value):
    if value is None:
        return set()

    raw_value = str(value).strip()
    if not raw_value:
        return set()

    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        parsed = re.split(r"[,;]", raw_value.strip("[]()"))

    if isinstance(parsed, (list, tuple, set)):
        values = parsed
    else:
        values = [parsed]

    return {
        _normalize_cibg_code(item)
        for item in values
        if _normalize_cibg_code(item)
    }


def _branches_by_cibg_key():
    """Branch aktif dikelompokkan berdasarkan kunci pencocokannya."""
    grouped = defaultdict(list)
    for code, initial, shortname in Branch.objects.filter(
        deleted=False, status=1
    ).values_list("code", "initial", "shortname"):
        grouped[_cibg_branch_key(code, initial, shortname)].append(
            (code, initial, shortname)
        )
    return grouped


def _get_cibg_region_definitions():
    region_rows = list(
        SalesRegion.objects.filter(business_id=1, deleted=False, status=1)
        .order_by("code")
        .values_list("id", "name", "code", "shortname", "description")
    )

    area_records = (
        SalesArea.objects.filter(
            deleted=False,
            status=1,
            region__business_id=1,
            region__deleted=False,
            region__status=1,
        )
        .order_by("initial")
        .values_list("region_id", "initial", "shortname")
    )

    branches_by_key = _branches_by_cibg_key()

    area_rows = []
    for region_id, area_initial, area_shortname in area_records:
        matched = branches_by_key.get(_normalize_cibg_code(area_shortname), [])
        if not matched:
            area_rows.append(
                (region_id, area_initial, area_shortname, None, None, None, None)
            )
            continue
        for code, initial, shortname in sorted(
            matched, key=lambda branch: str(branch[2] or "")
        ):
            area_rows.append(
                (
                    region_id,
                    area_initial,
                    area_shortname,
                    code,
                    initial,
                    shortname,
                    _cibg_branch_key(code, initial, shortname),
                )
            )

    region_definitions = []
    for (
        region_id,
        region_name,
        region_code,
        region_shortname,
        description,
    ) in region_rows:
        description_codes = _parse_cibg_description(description)
        branches = []

        for (
            area_region_id,
            area_initial,
            area_shortname,
            branch_code,
            branch_initial,
            branch_shortname,
            mapped_branch_key,
        ) in area_rows:
            area_code = _normalize_cibg_code(area_initial)
            if not area_code:
                continue

            branch_reference_codes = set()
            for branch_reference in (branch_code, branch_initial):
                normalized_reference = _normalize_cibg_code(
                    branch_reference
                )
                if not normalized_reference:
                    continue
                branch_reference_codes.add(normalized_reference)
                branch_reference_codes.update(
                    code
                    for code in re.split(r"[/,;]", normalized_reference)
                    if code
                )

            accepted_description_codes = {
                area_code,
                *branch_reference_codes,
            }
            if description_codes:
                if not description_codes.intersection(
                    accepted_description_codes
                ):
                    continue
            elif area_region_id != region_id:
                continue

            branch_key = (
                _normalize_cibg_shortname_key(mapped_branch_key)
                or _normalize_cibg_shortname_key(area_shortname)
            )
            if not branch_key:
                continue
            branch_label = (
                _normalize_cibg_code(area_shortname)
                or _normalize_cibg_code(branch_shortname)
            )
            if not any(
                branch["key"] == branch_key
                for branch in branches
            ):
                branches.append(
                    {
                        "key": branch_key,
                        "label": branch_label,
                        "area_initial": area_code,
                    }
                )

        region_definitions.append(
            {
                "id": region_id,
                "name": region_name or region_code or "(NO REGION)",
                "code": region_code or "",
                "parent_name": region_shortname or "",
                "description_codes": description_codes,
                "branches": branches,
            }
        )

    return region_definitions


def _empty_cibg_values():
    return {
        "current_unit": Decimal("0"),
        "current_value": Decimal("0"),
        "previous_unit": Decimal("0"),
        "previous_value": Decimal("0"),
    }


def _add_cibg_values(target, source):
    for field in target:
        target[field] += source[field]


def _cibg_values_for_month(branch_data, month):
    return branch_data.get(month, _empty_cibg_values()).copy()


def _cibg_metric_row(label, values, row_class=""):
    growth_unit = _growth(
        values["current_unit"],
        values["previous_unit"],
    )
    growth_value = _growth(
        values["current_value"],
        values["previous_value"],
    )

    return {
        "label": label,
        "row_class": row_class,
        "target_unit": _blank_cell(),
        "target_value": _blank_cell(),
        "sales_unit": _number_cell(values["current_unit"]),
        "sales_value": _number_cell(
            values["current_value"] / Decimal("1000000")
        ),
        "achievement_unit": _blank_cell(),
        "achievement_value": _blank_cell(),
        "previous_unit": _number_cell(values["previous_unit"]),
        "previous_value": _number_cell(
            values["previous_value"] / Decimal("1000000")
        ),
        "growth_unit": _percentage_cell(growth_unit),
        "growth_value": _percentage_cell(growth_value),
    }


def _cibg_region_summary_group(region):
    region_text = " ".join(
        [
            str(region.get("code") or ""),
            str(region.get("name") or ""),
            str(region.get("parent_name") or ""),
        ]
    ).upper()

    if "WEST" in region_text:
        return "WEST"
    if "EAST" in region_text:
        return "EAST"

    match = re.search(r"(?:REGION|R)\s*0?(\d{1,2})\b", region_text)
    if not match:
        return ""

    region_number = int(match.group(1))
    if 1 <= region_number <= 5:
        return "WEST"
    if 6 <= region_number <= 10:
        return "EAST"
    return ""


def _build_cibg_rows(product_regions, month, region_definitions):
    rows = []
    west_total = _empty_cibg_values()
    east_total = _empty_cibg_values()
    grand_total = _empty_cibg_values()
    summary_last_index = {}

    for index, region in enumerate(region_definitions):
        summary_group = _cibg_region_summary_group(region)
        if summary_group:
            summary_last_index[summary_group] = index

    for index, region in enumerate(region_definitions):
        region_id = region["id"]
        region_data = product_regions.get(region_id, {})
        branch_data = region_data.get("branches", {})
        region_total = _empty_cibg_values()

        for branch in region["branches"]:
            branch_key = branch["key"]
            branch_values = _cibg_values_for_month(
                branch_data.get(branch_key, {}),
                month,
            )
            rows.append(_cibg_metric_row(branch["label"], branch_values))
            _add_cibg_values(region_total, branch_values)

        rows.append(
            _cibg_metric_row(
                region["name"],
                region_total,
                "cibg-region-total",
            )
        )

        summary_group = _cibg_region_summary_group(region)
        if summary_group == "WEST":
            _add_cibg_values(west_total, region_total)
        elif summary_group == "EAST":
            _add_cibg_values(east_total, region_total)
        _add_cibg_values(grand_total, region_total)

        if summary_group == "WEST" and summary_last_index.get("WEST") == index:
            rows.append(
                _cibg_metric_row(
                    "NSM WEST",
                    west_total,
                    "cibg-nsm-total",
                )
            )
        elif summary_group == "EAST" and summary_last_index.get("EAST") == index:
            rows.append(
                _cibg_metric_row(
                    "NSM EAST",
                    east_total,
                    "cibg-nsm-total",
                )
            )

    rows.append(
        _cibg_metric_row(
            "TOTAL",
            grand_total,
            "cibg-grand-total",
        )
    )

    return rows


def _build_cibg_product_reports(
    product_data,
    from_month,
    to_month,
    region_definitions,
):
    product_reports = []
    for product_id, product in sorted(
        product_data.items(),
        key=lambda item: item[1]["product_name"].casefold(),
    ):
        months = []
        for month_number, month_label in MONTHS[from_month - 1:to_month]:
            months.append(
                {
                    "number": month_number,
                    "label": month_label,
                    "rows": _build_cibg_rows(
                        product["regions"],
                        month_number,
                        region_definitions,
                    ),
                }
            )
        product_reports.append(
            {
                "product_id": product_id,
                "product_name": product["product_name"],
                "months": months,
            }
        )

    return product_reports


def _render_cibg_report(request, base_context, allowed_business_ids):
    display_report = request.GET.get("display") == "1"
    available_years = []

    if display_report:
        available_years = _get_available_years()

    selected_year = request.GET.get("year", "").strip()
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = (
            available_years[-1]
            if available_years
            else timezone.localdate().year
        )

    if selected_year < 2 or selected_year > 9998:
        selected_year = (
            available_years[-1]
            if available_years
            else timezone.localdate().year
        )

    if available_years and selected_year not in available_years:
        selected_year = available_years[-1]

    selected_business = _resolve_selected_business(
        request.GET.get("business_id"),
        allowed_business_ids,
    )

    default_to_month = timezone.localdate().month
    selected_from_month = _parse_filter_id(
        request.GET.get("from_month")
    ) or "1"
    selected_to_month = _parse_filter_id(
        request.GET.get("to_month")
    ) or str(default_to_month)
    selected_from_month = min(int(selected_from_month), 12)
    selected_to_month = min(int(selected_to_month), 12)
    if selected_from_month > selected_to_month:
        selected_from_month = 1
        selected_to_month = default_to_month

    selected_products = _parse_filter_ids(
        request.GET.getlist("product_ids")
    )

    common_context = {
        **base_context,
        "years": available_years or [selected_year],
        "businesses": _business_options(allowed_business_ids),
        "month_options": [
            {"number": number, "label": label}
            for number, label in MONTHS
        ],
        "selected_year": selected_year,
        "selected_business": selected_business,
        "selected_from_month": selected_from_month,
        "selected_to_month": selected_to_month,
        "selected_from_month_label": MONTHS[selected_from_month - 1][1],
        "selected_to_month_label": MONTHS[selected_to_month - 1][1],
        "selected_products": selected_products,
        "product_options": [],
    }

    if not display_report:
        template_name = (
            "sales/reports/_sellingout_filters.html"
            if request.GET.get("partial") == "1"
            else "sales/reports/sellingout-reports.html"
        )
        return render(
            request,
            template_name,
            common_context,
        )

    product_options = _get_product_options(
        selected_business,
        allowed_business_ids,
    )
    date_from = date(selected_year - 1, selected_from_month, 1)
    if selected_to_month == 12:
        date_to = date(selected_year + 1, 1, 1)
    else:
        date_to = date(selected_year, selected_to_month + 1, 1)

    sales = SellingOut.objects.filter(
        invoice_date__gte=date_from,
        invoice_date__lt=date_to,
        status=1,
        deleted=False,
        item__product__isnull=False,
    )
    sales = _apply_business_scope(
        sales, allowed_business_ids, field="item__product__business_id"
    )
    if selected_business:
        sales = sales.filter(item__product__business_id=int(selected_business))
    sales = _apply_id_filter(sales, "item__product_id", selected_products)

    region_definitions = _get_cibg_region_definitions()
    branch_region_map = {
        branch["key"]: region["id"]
        for region in region_definitions
        for branch in region["branches"]
    }
    region_by_id = {
        region["id"]: region
        for region in region_definitions
    }
    branch_keys = {
        branch_id: _cibg_branch_key(code, initial, shortname)
        for branch_id, code, initial, shortname in Branch.objects.filter(
            deleted=False, status=1
        ).values_list("id", "code", "initial", "shortname")
    }
    allowed_branch_ids = [
        branch_id
        for branch_id, branch_key in branch_keys.items()
        if branch_key in branch_region_map
    ]

    if allowed_branch_ids:
        result_rows = (
            sales.filter(branch_id__in=allowed_branch_ids)
            .order_by()
            .annotate(
                year=ExtractYear("invoice_date"),
                month=ExtractMonth("invoice_date"),
            )
            .values(
                "item__product_id",
                "item__product__name",
                "branch_id",
                "year",
                "month",
            )
            .annotate(hjp_value=Sum("hjpvalue"), quantity=_quantity_sum())
            .order_by("item__product__name", "branch_id", "year", "month")
        )
    else:
        result_rows = []

    selected_product_ids = {
        int(product_id)
        for product_id in selected_products
    }
    product_data = {
        option["id"]: {
            "product_name": option["label"],
            "regions": {},
        }
        for option in product_options
        if option["id"] in selected_product_ids
    }
    for row in result_rows:
        product_id = row["item__product_id"]
        product = product_data.setdefault(
            product_id,
            {
                "product_name": _text_or(row["item__product__name"]),
                "regions": {},
            },
        )
        year = row["year"]
        month = row["month"]
        hjp_value = row["hjp_value"]
        quantity = row["quantity"]
        branch_key = branch_keys.get(row["branch_id"], "")
        region_id = branch_region_map.get(branch_key)
        if region_id is None:
            continue
        region_definition = region_by_id[region_id]
        region_name = region_definition["name"]
        parent_name = region_definition["parent_name"]
        region_key = region_id
        region = product["regions"].setdefault(
            region_key,
            {
                "region_name": region_name,
                "parent_name": parent_name,
                "branches": {},
            },
        )
        branch_data = region["branches"].setdefault(branch_key, {})
        values = branch_data.setdefault(month, _empty_cibg_values())
        if year == selected_year:
            values["current_value"] += Decimal(hjp_value or 0)
            values["current_unit"] += Decimal(quantity or 0)
        elif year == selected_year - 1:
            values["previous_value"] += Decimal(hjp_value or 0)
            values["previous_unit"] += Decimal(quantity or 0)

    product_reports = _build_cibg_product_reports(
        product_data,
        selected_from_month,
        selected_to_month,
        region_definitions,
    )

    report_context = {
        **common_context,
        "report_ready": True,
        "product_options": product_options,
        "product_reports": product_reports,
        "show_product_tabs": len(product_reports) > 1,
        "previous_year": selected_year - 1,
        "title": f"Region View - {selected_year}",
    }
    if request.GET.get("partial") == "report":
        return render(
            request,
            "sales/reports/_sellingout_result.html",
            report_context,
        )

    return render(
        request,
        "sales/reports/sellingout-reports.html",
        report_context,
    )


@login_required
def sellingout_reports(request):
    allowed_business_ids = _get_allowed_business_ids(request.user)
    selected_model = request.GET.get("model", "").strip().lower()
    model_choices = [
        {"value": value, "label": label}
        for value, label in REPORT_MODELS
    ]

    base_context = {
        "title": "Sellingout Reports",
        "model_choices": model_choices,
        "selected_model": selected_model,
        "report_ready": False,
    }

    if selected_model not in {model[0] for model in REPORT_MODELS}:
        return render(
            request,
            "sales/reports/sellingout-reports.html",
            base_context,
        )

    if selected_model == "cibg":
        return _render_cibg_report(
            request,
            base_context,
            allowed_business_ids,
        )

    display_report = request.GET.get("display") == "1"
    available_years = []

    if display_report:
        available_years = _get_available_years()

    selected_year = request.GET.get("year", "").strip()
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = (
            available_years[-1]
            if available_years
            else timezone.localdate().year
        )

    if selected_year < 2 or selected_year > 9998:
        selected_year = (
            available_years[-1]
            if available_years
            else timezone.localdate().year
        )

    if available_years and selected_year not in available_years:
        selected_year = available_years[-1]

    selected_business = _resolve_selected_business(
        request.GET.get("business_id"),
        allowed_business_ids,
    )

    default_to_month = timezone.localdate().month
    selected_from_month = _parse_filter_id(
        request.GET.get("from_month")
    ) or "1"
    selected_to_month = _parse_filter_id(
        request.GET.get("to_month")
    ) or str(default_to_month)

    selected_from_month = min(int(selected_from_month), 12)
    selected_to_month = min(int(selected_to_month), 12)
    if selected_from_month > selected_to_month:
        selected_from_month = 1
        selected_to_month = default_to_month

    selected_groups = _parse_filter_ids(request.GET.getlist("group_ids"))
    selected_subgroups = _parse_filter_ids(
        request.GET.getlist("subgroup_ids")
    )
    selected_products = _parse_filter_ids(
        request.GET.getlist("product_ids")
    )

    if not display_report:
        context = {
            **base_context,
            "years": available_years or [selected_year],
            "businesses": _business_options(allowed_business_ids),
            "selected_year": selected_year,
            "selected_business": selected_business,
            "month_options": [
                {"number": number, "label": label}
                for number, label in MONTHS
            ],
            "selected_from_month": selected_from_month,
            "selected_to_month": selected_to_month,
            "selected_from_month_label": MONTHS[selected_from_month - 1][1],
            "selected_to_month_label": MONTHS[selected_to_month - 1][1],
            "groups": [],
            "subgroups": [],
            "product_options": [],
            "selected_groups": selected_groups,
            "selected_subgroups": selected_subgroups,
            "selected_products": selected_products,
        }
        template_name = (
            "sales/reports/_sellingout_filters.html"
            if request.GET.get("partial") == "1"
            else "sales/reports/sellingout-reports.html"
        )
        return render(
            request,
            template_name,
            context,
        )

    filter_context = _get_filter_options(
        selected_business,
        selected_groups,
        selected_subgroups,
        allowed_business_ids,
    )
    filter_context.update(
        {
            "selected_groups": selected_groups,
            "selected_subgroups": selected_subgroups,
            "selected_products": selected_products,
        }
    )

    ytd_months = _ytd_months(selected_year)

    date_from = date(selected_year - 1, selected_from_month, 1)
    if selected_to_month == 12:
        date_to = date(selected_year + 1, 1, 1)
    else:
        date_to = date(selected_year, selected_to_month + 1, 1)

    sales = SellingOut.objects.filter(
        invoice_date__gte=date_from,
        invoice_date__lt=date_to,
        status=1,
        deleted=False,
        item__product__subgroup__group__isnull=False,
    )
    sales = _apply_business_scope(
        sales, allowed_business_ids, field="item__product__business_id"
    )
    if selected_business:
        sales = sales.filter(item__product__business_id=int(selected_business))

    sales = _apply_id_filter(sales, "item__product__subgroup__group_id", selected_groups)
    sales = _apply_id_filter(sales, "item__product__subgroup_id", selected_subgroups)
    sales = _apply_id_filter(sales, "item__product_id", selected_products)

    result_rows = (
        sales.order_by()
        .annotate(
            year=ExtractYear("invoice_date"),
            month=ExtractMonth("invoice_date"),
        )
        .values(
            "item__product__subgroup__group_id",
            "item__product__subgroup__group__name",
            "item__product__subgroup__group__code",
            "item__product__subgroup_id",
            "item__product__subgroup__name",
            "item__product_id",
            "item__product__name",
            "year",
            "month",
        )
        .annotate(hjp_value=Sum("hjpvalue"), quantity=_quantity_sum())
    )

    products = {}

    for row in result_rows:
        group_id = row["item__product__subgroup__group_id"]
        group_name = _text_or(
            row["item__product__subgroup__group__name"],
            row["item__product__subgroup__group__code"],
        )
        subgroup_id = row["item__product__subgroup_id"]
        subgroup_name = _text_or(row["item__product__subgroup__name"])
        product_id = row["item__product_id"]
        product_name = _text_or(row["item__product__name"])
        year = row["year"]
        month = row["month"]
        hjp_value = row["hjp_value"]
        quantity = row["quantity"]

        product_key = (subgroup_id, product_id or product_name)
        if product_key not in products:
            products[product_key] = _empty_product(
                group_id,
                group_name,
                subgroup_id,
                subgroup_name,
                product_id,
                product_name,
            )

        product = products[product_key]
        product["subgroup_name"] = subgroup_name or product["subgroup_name"]
        product["product_name"] = product_name or product["product_name"]

        if (
            year == selected_year
            and selected_from_month <= month <= selected_to_month
        ):
            product["value_current"][month - 1] += Decimal(hjp_value or 0)
            product["quantity_current"][month - 1] += Decimal(quantity or 0)
        elif (
            year == selected_year - 1
            and selected_from_month <= month <= selected_to_month
        ):
            product["value_previous"][month - 1] += Decimal(hjp_value or 0)
            product["quantity_previous"][month - 1] += Decimal(quantity or 0)

    _load_budget(
        products,
        selected_year,
        selected_from_month,
        selected_to_month,
        selected_business,
        selected_groups,
        selected_subgroups,
        selected_products,
        allowed_business_ids,
    )

    product_rows = _build_product_rows(
        products,
        ytd_months,
        selected_from_month,
        selected_to_month,
    )

    display_months = MONTHS[selected_from_month - 1:selected_to_month]

    context = {
        "title": f"Period View - {selected_year}",
        "model_choices": model_choices,
        "selected_model": selected_model,
        "report_ready": True,
        "months": [
            {"number": number, "label": label}
            for number, label in display_months
        ],
        "month_options": [
            {"number": number, "label": label}
            for number, label in MONTHS
        ],
        "years": available_years or [selected_year],
        "businesses": _business_options(allowed_business_ids),
        "selected_year": selected_year,
        "selected_business": selected_business,
        "selected_from_month": selected_from_month,
        "selected_to_month": selected_to_month,
        "selected_from_month_label": MONTHS[selected_from_month - 1][1],
        "selected_to_month_label": MONTHS[selected_to_month - 1][1],
        **filter_context,
        "products": product_rows,
        "table_colspan": len(display_months) + 6,
        "ytd_month_label": MONTHS[ytd_months - 1][1] if ytd_months else "-",
    }
    if request.GET.get("partial") == "report":
        return render(
            request,
            "sales/reports/_sellingout_result.html",
            context,
        )

    return render(request, "sales/reports/sellingout-reports.html", context)


@login_required
def sellingout_filter_options(request):
    allowed_business_ids = _get_allowed_business_ids(request.user)
    selected_business = _resolve_selected_business(
        request.GET.get("business_id"),
        allowed_business_ids,
    )
    if request.GET.get("products_only") == "1":
        return JsonResponse(
            {
                "product_options": _get_product_options(
                    selected_business,
                    allowed_business_ids,
                )
            }
        )

    selected_groups = _parse_filter_ids(request.GET.getlist("group_ids"))
    selected_subgroups = _parse_filter_ids(
        request.GET.getlist("subgroup_ids")
    )

    return JsonResponse(
        _get_filter_options(
            selected_business,
            selected_groups,
            selected_subgroups,
            allowed_business_ids,
        )
    )


@login_required
def sellingout_year_options(request):
    return JsonResponse({"years": _get_available_years()})
