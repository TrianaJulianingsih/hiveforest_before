from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.utils.module_loading import import_string
from apps.base.models.utils import build_or_filter
from django.core.exceptions import FieldError, ValidationError

NULL_KEYWORDS = {"__blank__", "blank", "empty", "null", "none", "n/a"}

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AjaxDatatable                                       ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: To render data in list view                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\datatable\views.py                        ║
# ║  Created: May/16-2025 by Setiadji                          ║
# ║  Updated: May/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class AjaxDatatable(View):
    model = None
    columns = []
    queryset = None
    default_order_column = 0
    annotate = {}
    prefetch = []
    select = []

    def get_queryset(self):
        qs = self.model.objects.filter(deleted=False)

        if self.select:
            qs = qs.select_related(*self.select)
        if self.prefetch:
            qs = qs.prefetch_related(*self.prefetch)
        if self.annotate:
            qs = qs.annotate(**self.annotate)

        return qs
    
    # Global search
    def get_search_filter(self, search_value):
        search_q = Q()
        for col in self.columns:
            field = col['field']
            lookup = col.get('lookup', 'icontains')
            search_q |= Q(**{f"{field}__{lookup}": search_value})
        return search_q

    def apply_column_filters(self, qs, request):
        for idx, col in enumerate(self.columns, start=1):
            val = request.GET.get(f"columns[{idx}][search][value]", "").strip()
            if not val:
                continue

            field = col['field']
            lookup = col.get('lookup', 'icontains')
            val_lower = val.lower()

            if val_lower in NULL_KEYWORDS:
                null_field = field
                if field.endswith("__name"):
                    null_field = field[:-6]

                try:
                    qs = qs.filter(Q(**{f"{null_field}__isnull": True}) | Q(**{f"{null_field}": ''}))
                except (ValueError, TypeError, FieldError, ValidationError):
                    # If blank '' is invalid for this field type (e.g. AutoField), fallback to only null
                    qs = qs.filter(**{f"{null_field}__isnull": True})
            else:
                full_field = f"{field}__{lookup}"
                try:
                    if "|" in val:
                        qs = qs.filter(build_or_filter(full_field, val))
                    else:
                        qs = qs.filter(Q(**{full_field: val}))
                except (ValueError, TypeError, FieldError, ValidationError):
                    # Invalid value (e.g. string in integer field) — return no data
                    qs = qs.none()
        return qs

    # Column Ordering
    def get_order_field(self, request):
        col_index = request.GET.get("order[0][column]", str(self.default_order_column))
        order_dir = request.GET.get("order[0][dir]", "asc")

        try:
            col_idx = int(col_index) - 1
            field = self.columns[col_idx]['field']
        except (ValueError, IndexError):
            field = self.columns[self.default_order_column]['field']

        return f"-{field}" if order_dir == "desc" else field

    def format_row(self, obj):
        """Override this in your subclass."""
        return {}

    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get("search[value]", "").strip()

        qs = self.get_queryset()

        if search_value:
            qs = qs.filter(self.get_search_filter(search_value))

        qs = self.apply_column_filters(qs, request)

        total_filtered = qs.count()

        order_field = self.get_order_field(request)
        qs = qs.order_by(order_field)[start:start + length]

        data = [self.format_row(obj) for obj in qs]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": self.model.objects.count(),
            "recordsFiltered": total_filtered,
            "data": data,
        })