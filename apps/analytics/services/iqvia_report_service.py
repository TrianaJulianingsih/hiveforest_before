from django.db.models import Sum, Count
from apps.analytics.models.iqvia import IQV_ITMATrans, IQV_Corp


# Base queryset, exclude soft deleted rows
def _base_queryset(year=None, corporation_id=None):
    qs = IQV_ITMATrans.objects.filter(deleted=False)
    if year:
        qs = qs.filter(year=year)
    if corporation_id:
        qs = qs.filter(pack__product__company__corporation_id=corporation_id)
    return qs


# Distinct years, for filter dropdown
def get_available_years():
    return list(
        IQV_ITMATrans.objects.filter(deleted=False, year__isnull=False)
        .values_list("year", flat=True)
        .distinct()
        .order_by("year")
    )


# Sort key for 'QTR 1/2020' style label
def quarter_sort_key(label):
    text = str(label or "").strip()
    try:
        head, year = text.split("/")
        return (int(year), int(head.upper().replace("QTR", "").strip()))
    except (ValueError, TypeError):
        return (9999, 9)


# 'QTR 1/2020' becomes '2020 Q1'
def quarter_display(label):
    text = str(label or "").strip()
    try:
        head, year = text.split("/")
        return f"{int(year)} Q{int(head.upper().replace('QTR', '').strip())}"
    except (ValueError, TypeError):
        return text


# Distinct quarters in chronological order, for X axis picker
def get_available_quarters():
    rows = (
        IQV_ITMATrans.objects.filter(deleted=False)
        .exclude(quarter__isnull=True)
        .exclude(quarter="")
        .values_list("quarter", flat=True)
        .distinct()
    )
    return sorted(rows, key=quarter_sort_key)