from decimal import Decimal, InvalidOperation
import csv
import io
import os
import subprocess
import sys
import unicodedata

import pandas as pd
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django import forms
from django.forms import NumberInput, TextInput
from django.shortcuts import render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import CSV, XLSX

from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.models.entities import Company
from apps.bom.models import (
    FreightCost,
    FreightCostDetail,
    FreightCostImportJob,
)
from apps.bom.models.resources import FreightCostDetailReportResource
from apps.sales.models.product import Product, ProductPackage, ProductSubgroup
from apps.supplychain.models.distributions import DistributorItem, DistributorItemGroup


MISSING_FREIGHT = object()


class FreightCostDetailInlineForm(forms.ModelForm):
    group_produk = forms.ModelChoiceField(
        queryset=DistributorItemGroup.objects.filter(deleted=False).order_by("name"),
        required=False,
        label="Group Produk",
    )
    item_group = forms.ModelChoiceField(
        queryset=ProductSubgroup.objects.all().order_by("name"),
        required=False,
        label="Item Group",
    )
    packaging_type = forms.ModelChoiceField(
        queryset=ProductPackage.objects.all().order_by("name"),
        required=False,
        label="Packaging Type",
    )

    class Meta:
        model = FreightCostDetail
        fields = "__all__"

    class Media:
        js = ("custom/bom/freightcost_item_group_autofill.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group_produk = None
        subgroup = None
        packaging = None
        resolved_product = self.instance.product
        distributor_item = self.instance.product_distributor if self.instance else None

        if not distributor_item and resolved_product:
            distributor_item = (
                resolved_product.distributoritem_set.select_related("group", "product")
                .filter(group__deleted=False)
                .first()
            )

        if not resolved_product and distributor_item and distributor_item.product:
            resolved_product = distributor_item.product

        if self.instance and self.instance.pk and self.instance.group_produk:
            group_produk = DistributorItemGroup.objects.filter(
                name=self.instance.group_produk, deleted=False
            ).first()

        if not group_produk and distributor_item:
            if distributor_item and distributor_item.group:
                group_produk = distributor_item.group

        if self.instance and self.instance.pk and self.instance.item_group:
            subgroup = ProductSubgroup.objects.filter(
                name=self.instance.item_group
            ).first()

        if not subgroup and resolved_product and resolved_product.subgroup:
            subgroup = resolved_product.subgroup

        if self.instance and self.instance.pk:
            packaging = self.instance.resolved_packaging

        self.initial["group_produk"] = group_produk.pk if group_produk else ""
        self.initial["item_group"] = subgroup.pk if subgroup else ""
        self.initial["packaging_type"] = packaging.pk if packaging else ""
        self.fields["group_produk"].initial = group_produk.pk if group_produk else ""
        self.fields["item_group"].initial = subgroup.pk if subgroup else ""
        self.fields["packaging_type"].initial = packaging.pk if packaging else ""

    def clean_group_produk(self):
        group_produk = self.cleaned_data.get("group_produk")
        return group_produk.name if group_produk else ""

    def clean_item_group(self):
        subgroup = self.cleaned_data.get("item_group")
        return subgroup.name if subgroup else ""


class FreightCostDetailInline(admin.StackedInline):
    model = FreightCostDetail
    form = FreightCostDetailInlineForm
    extra = 1
    autocomplete_fields = ("product", "product_distributor", "principal")
    fieldsets = (
        (
            "Item Information",
            {
                "fields": (
                    ("product", "product_distributor"),
                    ("packaging_type", "principal"),
                    "group_produk",
                    "item_group",
                ),
            },
        ),
        (
            "Quantity & Cost",
            {
                "fields": (
                    ("qty_freight", "total_weight"),
                    ("total_freight", "total_cost"),
                ),
            },
        ),
    )
    formfield_overrides = {
        models.CharField: {
            "widget": TextInput(attrs={"style": "width: 100%; max-width: 420px;"})
        },
        models.DecimalField: {"widget": NumberInput(attrs={"style": "width: 220px;"})},
    }


class FreightCostAdminForm(forms.ModelForm):
    class Meta:
        model = FreightCost
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["name"].label = "Freight Number"

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Freight number wajib diisi.")
        return name


class FreightCabangFilter(SimpleListFilter):
    title = "Cabang"
    parameter_name = "nama_cab"

    def lookups(self, request, model_admin):
        cabangs = (
            FreightCostDetail.objects.exclude(nama_cab__isnull=True)
            .exclude(nama_cab="")
            .values_list("nama_cab", flat=True)
            .distinct()
            .order_by("nama_cab")
        )
        return [(cabang, cabang) for cabang in cabangs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(nama_cab=self.value())
        return queryset


@admin.register(FreightCost)
class FreightCostAdmin(MassActionMixin, BaseModelAdmin):
    form = FreightCostAdminForm
    fields = None
    readonly_fields = BaseModelAdmin.readonly_fields
    prepopulated_fields = {}
    change_list_template = "admin/bom/freightcost/change_list.html"
    fieldsets = (
        (
            "Freight Header",
            {
                "fields": (
                    "name",
                    ("shipping_date", "freight_type", "burden_type"),
                    "description",
                    "remark",
                ),
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "status",
                    "slug",
                    "cat",
                    "cby",
                    "uat",
                    "uby",
                    "dat",
                    "dby",
                    "deleted",
                ),
            },
        ),
    )
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + ("shipping_date", "freight_type", "burden_type")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    search_fields = BaseModelAdmin.search_fields + (
        "freight_type",
        "burden_type",
    )
    list_filter = BaseModelAdmin.list_filter + (
        ("shipping_date", admin.DateFieldListFilter),
        "freight_type",
        "burden_type",
    )
    inlines = [FreightCostDetailInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "template-download/",
                self.admin_site.admin_view(self.template_download_view),
                name="bom_freightcost_template_download",
            ),
            path(
                "product-subgroup/<int:product_id>/",
                self.admin_site.admin_view(self.product_subgroup_lookup_view),
                name="bom_freightcost_product_subgroup",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["background_import_url"] = reverse(
            "admin:bom_freightcostdetail_background_import"
        )
        extra_context["template_download_url"] = reverse(
            "admin:bom_freightcost_template_download"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def template_download_view(self, request):
        headers = [
            "FREIGHT NUMBER",
            "SHIPPING_DATE",
            "FROM_LOCATION",
            "TO_LOCATION",
            "EXPEDITION_NAME",
            "EXPEDITION_TYPE",
            "PACKAGING_TYPE",
            "ITEM_CODE",
            "ITEM_DESCRIPTION",
            "QTY_FREIGHT",
            "TOTAL_WEIGHT",
            "NAMA_PRINCIPAL",
            "GROUP_PRODUK",
            "TOTAL_FREIGHT",
            "FREIGHT_TYPE",
            "TOTAL_COST",
            "kode_cab",
            "nama_cab",
            "ItemGroup",
            "burden_type",
        ]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="freight_cost_template.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(headers)
        return response

    def product_subgroup_lookup_view(self, request, product_id):
        product = (
            Product.objects.select_related("subgroup", "packaging")
            .filter(pk=product_id)
            .first()
        )
        subgroup = product.subgroup if product else None
        packaging = product.packaging if product else None
        group_produk_id = None
        group_produk = ""
        if product:
            distributor_item = (
                product.distributoritem_set.select_related("group")
                .filter(group__deleted=False)
                .first()
            )
            if distributor_item and distributor_item.group:
                group_produk_id = distributor_item.group.id
                group_produk = distributor_item.group.name
        return JsonResponse(
            {
                "product_id": product_id,
                "subgroup_id": subgroup.id if subgroup else None,
                "subgroup_name": subgroup.name if subgroup else "",
                "packaging_id": packaging.id if packaging else None,
                "packaging_name": packaging.name if packaging else "",
                "group_produk_id": group_produk_id,
                "group_produk_name": group_produk,
            }
        )


@admin.register(FreightCostDetail)
class FreightCostDetailAdmin(
    PandasImportMixin, MassActionMixin, BaseModelAdmin, ImportExportModelAdmin
):
    duplicate_report_cache_timeout = 60 * 30
    change_list_template = "admin/bom/freightcostdetail/change_list.html"
    background_import_template = "admin/bom/freightcostdetail/background_import.html"
    resource_class = FreightCostDetailReportResource
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]
    has_pandas_import = True
    has_batch_upload = True
    auto_batch_threshold = 5000
    import_chunk_size = 5000
    bulk_insert_batch_size = 5000
    background_job_extensions = {".csv", ".xlsx", ".xls", ".dbf"}
    background_job_list_limit = 20
    list_per_page = 1000
    list_select_related = (
        "freight",
        "product",
        "product_distributor",
        "product_distributor__product",
        "packaging_type",
        "principal",
    )
    autocomplete_fields = ("freight", "product", "product_distributor", "principal")
    readonly_fields = BaseModelAdmin.readonly_fields
    search_fields = BaseModelAdmin.search_fields + (
        "freight__name",
        "from_location",
        "to_location",
        "expedition_name",
        "expedition_type",
        "item_code",
        "item_description",
        "kode_cab",
        "nama_cab",
        "product__code",
        "product__name",
        "product_distributor__code",
        "product_distributor__name",
        "principal__name",
        "freight__freight_type",
    )
    list_filter = BaseModelAdmin.list_filter + (
        ("freight__shipping_date", admin.DateFieldListFilter),
        FreightCabangFilter,
        "freight__freight_type",
    )
    list_display = (
        "id",
        "get_freight_number",
        "get_shipping_date",
        "get_from_location",
        "get_to_location",
        "get_expedition_name",
        "get_packaging_type",
        "item_code",
        "item_description",
        "qty_freight",
        "total_weight",
        "get_nama_principal",
        "group_produk",
        "total_freight",
        "get_freight_type",
        "total_cost",
        "get_kode_cab",
        "get_nama_cab",
        "get_item_group",
    )
    list_display_links = ("get_freight_number",)

    dtype_mapping = {
        "FREIGHT NUMBER": "string",
        "SHIPPING_DATE": "string",
        "FROM_LOCATION": "string",
        "TO_LOCATION": "string",
        "EXPEDITION_NAME": "string",
        "EXPEDITION_TYPE": "string",
        "PACKAGING_TYPE": "string",
        "ITEM_CODE": "string",
        "ITEM_DESCRIPTION": "string",
        "QTY_FREIGHT": "float64",
        "TOTAL_WEIGHT": "float64",
        "NAMA_PRINCIPAL": "string",
        "GROUP_PRODUK": "string",
        "TOTAL_FREIGHT": "float64",
        "FREIGHT_TYPE": "string",
        "BURDEN_TYPE": "string",
        "TOTAL_COST": "float64",
        "KODE_CAB": "string",
        "NAMA_CAB": "string",
        "ITEMGROUP": "string",
    }
    column_mapping = {
        "BURDEN TYPE": "BURDEN_TYPE",
    }

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "background-import/",
                self.admin_site.admin_view(self.background_import_view),
                name="bom_freightcostdetail_background_import",
            ),
            path(
                "download-duplicate-report/",
                self.admin_site.admin_view(self.download_duplicate_report_view),
                name="bom_freightcostdetail_download_duplicate_report",
            ),
        ]
        return custom_urls + urls

    def has_add_permission(self, request):
        return False

    def has_import_permission(self, request):
        return False

    def has_export_permission(self, request):
        return False

    def _get_duplicate_report_cache_key(self, request):
        session_key = getattr(request.session, "session_key", None)
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        return f"freight_cost_duplicate_report:{session_key}"

    def _store_duplicate_report(self, request, skipped_rows):
        if not skipped_rows:
            cache.delete(self._get_duplicate_report_cache_key(request))
            return None

        report_rows = []
        all_columns = []

        for row_data in skipped_rows:
            raw_row = dict(row_data.get("raw_row") or {})
            raw_row["EXCEL_ROW"] = row_data.get("excel_row")
            raw_row["SKIP_REASON"] = "Exact duplicate row in import file"
            report_rows.append(raw_row)

            for column_name in raw_row.keys():
                if column_name not in all_columns:
                    all_columns.append(column_name)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report_rows)

        cache.set(
            self._get_duplicate_report_cache_key(request),
            output.getvalue(),
            self.duplicate_report_cache_timeout,
        )
        return reverse("admin:bom_freightcostdetail_download_duplicate_report")

    def _notify_duplicate_report(self, request, skipped_rows):
        report_url = self._store_duplicate_report(request, skipped_rows)
        if not report_url:
            return

        messages.warning(
            request,
            mark_safe(
                f"{len(skipped_rows)} baris duplikat identik dilewati. "
                f"<a href='{report_url}' target='_blank'>Download duplicate rows</a>"
            ),
        )

    def download_duplicate_report_view(self, request):
        csv_content = cache.get(self._get_duplicate_report_cache_key(request))
        if not csv_content:
            self.message_user(
                request,
                "Tidak ada laporan duplikat yang tersedia atau laporan sudah kedaluwarsa.",
                level=messages.WARNING,
            )
            return HttpResponse(status=404)

        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="freight_cost_duplicate_rows.csv"'
        return response

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = False
        return super().changelist_view(request, extra_context=extra_context)

    def _get_background_import_jobs(self):
        return FreightCostImportJob.objects.select_related("requested_by")[: self.background_job_list_limit]

    def _spawn_background_import_job(self, job):
        command = [
            sys.executable,
            os.fspath(settings.BASE_DIR / "manage.py"),
            "process_freight_cost_import_job",
            "--job-id",
            str(job.pk),
        ]
        popen_kwargs = {
            "cwd": os.fspath(settings.BASE_DIR),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }

        if os.name == "nt":
            popen_kwargs["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        else:
            popen_kwargs["start_new_session"] = True

        return subprocess.Popen(command, **popen_kwargs)

    def background_import_view(self, request):
        background_import_url = reverse("admin:bom_freightcostdetail_background_import")
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level=messages.ERROR)
                return HttpResponseRedirect(background_import_url)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension not in self.background_job_extensions:
                self.message_user(
                    request,
                    f"Unsupported file format: {file_extension}",
                    level=messages.ERROR,
                )
                return HttpResponseRedirect(background_import_url)

            requested_by = request.user if request.user.is_authenticated else None
            job = FreightCostImportJob.objects.create(
                upload_file=uploaded_file,
                original_filename=os.path.basename(uploaded_file.name),
                requested_by=requested_by,
                status=FreightCostImportJob.STATUS_QUEUED,
                message="Job queued. Waiting for background worker.",
            )

            try:
                process = self._spawn_background_import_job(job)
            except Exception as exc:
                job.status = FreightCostImportJob.STATUS_FAILED
                job.error_message = str(exc)
                job.message = "Failed to start background import job."
                job.completed_at = timezone.now()
                job.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "message",
                        "completed_at",
                    ]
                )
                self.message_user(
                    request,
                    f"Failed to start background import: {exc}",
                    level=messages.ERROR,
                )
            else:
                job.background_pid = process.pid
                job.message = "Background import started on server."
                job.save(update_fields=["background_pid", "message"])
                self.message_user(
                    request,
                    f"Background import started. Job ID: {job.pk}",
                    level=messages.SUCCESS,
                )

            return HttpResponseRedirect(background_import_url)

        return render(
            request,
            self.background_import_template,
            self._get_background_import_context(request),
        )

    def _get_background_import_context(self, request):
        jobs = list(self._get_background_import_jobs())
        return {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "app_label": self.model._meta.app_label,
            "title": "Freight Cost Background Import",
            "jobs": jobs,
            "active_job_count": sum(
                1
                for job in jobs
                if job.status in {
                    FreightCostImportJob.STATUS_QUEUED,
                    FreightCostImportJob.STATUS_RUNNING,
                }
            ),
            "allowed_extensions": ", ".join(sorted(self.background_job_extensions)),
            "changelist_url": reverse("admin:bom_freightcostdetail_changelist"),
            "legacy_import_url": reverse("admin:bom_freightcostdetail_pandas_import"),
        }

    @admin.display(description="FREIGHT NUMBER", ordering="freight__name")
    def get_freight_number(self, obj):
        return obj.freight.name if obj.freight else ""

    @admin.display(description="SHIPPING_DATE", ordering="freight__shipping_date")
    def get_shipping_date(self, obj):
        return obj.freight.shipping_date if obj.freight else None

    @admin.display(description="FROM_LOCATION", ordering="from_location")
    def get_from_location(self, obj):
        return obj.from_location

    @admin.display(description="TO_LOCATION", ordering="to_location")
    def get_to_location(self, obj):
        return obj.to_location

    @admin.display(description="EXPEDITION_NAME", ordering="expedition_name")
    def get_expedition_name(self, obj):
        return obj.expedition_name

    @admin.display(description="PACKAGING_TYPE", ordering="packaging_type_id")
    def get_packaging_type(self, obj):
        return obj.packaging_type_value

    @admin.display(description="ItemGroup", ordering="item_group")
    def get_item_group(self, obj):
        return obj.item_group_name

    @admin.display(description="NAMA_PRINCIPAL", ordering="principal__name")
    def get_nama_principal(self, obj):
        return obj.nama_principal

    @admin.display(description="FREIGHT_TYPE", ordering="freight__freight_type")
    def get_freight_type(self, obj):
        return obj.freight.freight_type if obj.freight else ""

    @admin.display(description="kode_cab", ordering="kode_cab")
    def get_kode_cab(self, obj):
        return obj.kode_cab

    @admin.display(description="nama_cab", ordering="nama_cab")
    def get_nama_cab(self, obj):
        return obj.nama_cab

    def _clean_text(self, value):
        if value is None or pd.isna(value):
            return ""
        text = unicodedata.normalize("NFKC", str(value))
        text = (
            text.replace("\u00a0", " ")
            .replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
            .replace("\ufeff", "")
        )
        return text.strip()

    def _clean_decimal(self, value):
        if value is None or pd.isna(value) or value == "":
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError):
                return None
        if isinstance(value, str):
            value = self._clean_text(value).replace(" ", "")

            if not value:
                return None

            if "," in value and "." in value:
                if value.rfind(",") > value.rfind("."):
                    value = value.replace(".", "").replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "," in value:
                parts = value.split(",")
                value = f"{''.join(parts[:-1])}.{parts[-1]}" if len(parts) > 1 else value
            elif "." in value:
                parts = value.split(".")
                if len(parts) == 2 and len(parts[1]) == 3 and all(part.isdigit() for part in parts):
                    value = "".join(parts)
                elif len(parts) > 2:
                    decimal_part = parts[-1]
                    integer_part = "".join(parts[:-1])
                    if len(decimal_part) in {1, 2}:
                        value = f"{integer_part}.{decimal_part}"
                    else:
                        value = f"{integer_part}{decimal_part}"
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _clean_date(self, value):
        if value is None or pd.isna(value) or value == "":
            return None
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return None
        return parsed.date()

    def _normalize_lookup_text(self, value):
        return " ".join(self._clean_text(value).lower().split())

    def _get_product(self, item_code, item_description):
        item_code = self._clean_text(item_code)
        item_description = self._clean_text(item_description)

        if item_code.isdigit():
            product = Product.objects.filter(pk=int(item_code)).first()
            if product:
                return product

        product = Product.objects.filter(code__iexact=item_code).first()
        if product:
            return product

        if item_description:
            product = Product.objects.filter(name__iexact=item_description).first()
            if product:
                return product

        return None

    def _get_distributor_item(self, item_code, item_description):
        item_code = self._clean_text(item_code)
        item_description = self._clean_text(item_description)

        queryset = DistributorItem.objects.select_related(
            "product", "group", "product__subgroup", "product__packaging"
        )

        if item_code.isdigit():
            distributor_item = queryset.filter(pk=int(item_code)).first()
            if distributor_item:
                return distributor_item

        if item_code:
            distributor_item = queryset.filter(code__iexact=item_code).first()
            if distributor_item:
                return distributor_item

        if item_description:
            distributor_item = queryset.filter(name__iexact=item_description).first()
            if distributor_item:
                return distributor_item

        return None

    def _get_packaging(self, packaging_value):
        packaging_value = self._clean_text(packaging_value)
        if not packaging_value:
            return None

        if packaging_value.isdigit():
            packaging = ProductPackage.objects.filter(pk=int(packaging_value)).first()
            if packaging:
                return packaging

        return ProductPackage.objects.filter(
            Q(code__iexact=packaging_value)
            | Q(name__iexact=packaging_value)
            | Q(initial__iexact=packaging_value)
            | Q(shortname__iexact=packaging_value)
        ).first()

    def _get_principal(self, principal_value):
        principal_value = self._clean_text(principal_value)
        if not principal_value:
            return None

        if principal_value.isdigit():
            principal = Company.objects.filter(pk=int(principal_value)).first()
            if principal:
                return principal

        return Company.objects.filter(
            Q(code__iexact=principal_value)
            | Q(name__iexact=principal_value)
            | Q(initial__iexact=principal_value)
            | Q(shortname__iexact=principal_value)
        ).first()

    def _prepare_import_row(self, index, row):
        excel_row = index + 2
        freight_number = self._clean_text(row.get("FREIGHT NUMBER"))
        if not freight_number:
            raise ValueError(f"Row {excel_row}: FREIGHT NUMBER wajib diisi.")

        return {
            "excel_row": excel_row,
            "raw_row": row,
            "freight_number": freight_number,
            "shipping_date": self._clean_date(row.get("SHIPPING_DATE")),
            "from_location": self._clean_text(row.get("FROM_LOCATION")),
            "to_location": self._clean_text(row.get("TO_LOCATION")),
            "expedition_name": self._clean_text(row.get("EXPEDITION_NAME")),
            "expedition_type": self._clean_text(row.get("EXPEDITION_TYPE")),
            "freight_type": self._clean_text(row.get("FREIGHT_TYPE")),
            "burden_type": self._clean_text(
                row.get("BURDEN_TYPE")
                or row.get("BURDEN TYPE")
                or row.get("Burden Type")
                or row.get("burden_type")
            ),
            "kode_cab": self._clean_text(row.get("KODE_CAB") or row.get("kode_cab")),
            "nama_cab": self._clean_text(row.get("NAMA_CAB") or row.get("nama_cab")),
            "item_code": self._clean_text(row.get("ITEM_CODE")),
            "item_description": self._clean_text(row.get("ITEM_DESCRIPTION")),
            "group_produk": self._clean_text(row.get("GROUP_PRODUK")),
            "packaging_value": row.get("PACKAGING_TYPE"),
            "principal_value": row.get("NAMA_PRINCIPAL"),
            "qty_freight": self._clean_decimal(row.get("QTY_FREIGHT")),
            "total_weight": self._clean_decimal(row.get("TOTAL_WEIGHT")),
            "total_freight": self._clean_decimal(row.get("TOTAL_FREIGHT")),
            "total_cost": self._clean_decimal(row.get("TOTAL_COST")),
            "item_group": self._clean_text(row.get("ITEMGROUP") or row.get("ItemGroup")),
        }

    def _normalize_burden_type(self, burden_type):
        burden_type = self._clean_text(burden_type)
        if burden_type == FreightCost.BURDEN_TYPE_OU_LEGACY:
            return FreightCost.BURDEN_TYPE_OI
        if burden_type in dict(FreightCost.BURDEN_TYPE_CHOICES):
            return burden_type
        return FreightCost.BURDEN_TYPE_OI

    def _build_import_row_signature(self, row_data):
        return (
            self._clean_text(row_data.get("freight_number")),
            row_data.get("shipping_date"),
            self._clean_text(row_data.get("from_location")),
            self._clean_text(row_data.get("to_location")),
            self._clean_text(row_data.get("expedition_name")),
            self._clean_text(row_data.get("expedition_type")),
            self._clean_text(row_data.get("freight_type")),
            self._normalize_burden_type(row_data.get("burden_type")),
            self._clean_text(row_data.get("kode_cab")),
            self._clean_text(row_data.get("nama_cab")),
            self._clean_text(row_data.get("item_code")),
            self._clean_text(row_data.get("item_description")),
            self._clean_text(row_data.get("group_produk")),
            self._clean_text(row_data.get("packaging_value")),
            self._clean_text(row_data.get("principal_value")),
            row_data.get("qty_freight"),
            row_data.get("total_weight"),
            row_data.get("total_freight"),
            row_data.get("total_cost"),
            self._clean_text(row_data.get("item_group")),
        )

    def _validate_no_duplicate_detail_rows(self, prepared_rows, seen_signatures=None):
        seen_signatures = seen_signatures if seen_signatures is not None else set()
        filtered_rows = []
        skipped_rows = []

        for row_data in prepared_rows:
            signature = self._build_import_row_signature(row_data)
            if signature in seen_signatures:
                skipped_rows.append(row_data)
                continue

            seen_signatures.add(signature)
            filtered_rows.append(row_data)

        return filtered_rows, skipped_rows

    def _build_detail_duplicate_signature(self, detail_payload):
        return (
            self._clean_text(detail_payload.get("name")),
            self._clean_text(detail_payload.get("description")),
            self._clean_text(detail_payload.get("remark")),
            detail_payload["freight"].pk if detail_payload.get("freight") else None,
            detail_payload.get("qty_freight"),
            detail_payload.get("total_weight"),
            self._clean_text(detail_payload.get("item_group")),
            detail_payload.get("total_freight"),
            detail_payload.get("total_cost"),
            detail_payload.get("packaging_type_id"),
            detail_payload["principal"].pk if detail_payload.get("principal") else None,
            detail_payload["product"].pk if detail_payload.get("product") else None,
            self._clean_text(detail_payload.get("group_produk")),
            (
                detail_payload["product_distributor"].pk
                if detail_payload.get("product_distributor")
                else None
            ),
            self._clean_text(detail_payload.get("expedition_name")),
            self._clean_text(detail_payload.get("expedition_type")),
            self._clean_text(detail_payload.get("from_location")),
            self._clean_text(detail_payload.get("item_code")),
            self._clean_text(detail_payload.get("item_description")),
            self._clean_text(detail_payload.get("kode_cab")),
            self._clean_text(detail_payload.get("nama_cab")),
            self._clean_text(detail_payload.get("to_location")),
        )

    def _get_cached_product(self, row_data, cache):
        cache_key = (row_data["item_code"], row_data["item_description"])
        if cache_key not in cache:
            cache[cache_key] = self._get_product(*cache_key)
        return cache[cache_key]

    def _get_cached_distributor_item(self, row_data, cache):
        cache_key = (row_data["item_code"], row_data["item_description"])
        if cache_key not in cache:
            cache[cache_key] = self._get_distributor_item(*cache_key)
        return cache[cache_key]

    def _get_cached_product_distributor(self, product, cache):
        if not product:
            return None

        cache_key = product.pk
        if cache_key not in cache:
            cache[cache_key] = (
                DistributorItem.objects.select_related(
                    "product", "group", "product__subgroup", "product__packaging"
                )
                .filter(product=product)
                .order_by("id")
                .first()
            )
        return cache[cache_key]

    def _get_cached_packaging(self, packaging_value, cache):
        cache_key = self._clean_text(packaging_value)
        if cache_key not in cache:
            cache[cache_key] = self._get_packaging(packaging_value)
        return cache[cache_key]

    def _resolve_import_packaging(self, row_data, cache):
        packaging_value = self._clean_text(row_data["packaging_value"])
        if not packaging_value:
            return {"packaging": None, "packaging_type_id": None}

        if packaging_value.isdigit():
            return {"packaging": None, "packaging_type_id": int(packaging_value)}

        return {
            "packaging": self._get_cached_packaging(packaging_value, cache),
            "packaging_type_id": None,
        }

    def _get_cached_principal(self, principal_value, cache):
        cache_key = self._clean_text(principal_value)
        if cache_key not in cache:
            cache[cache_key] = self._get_principal(principal_value)
        return cache[cache_key]

    def _get_freight_cache_key(self, freight_number):
        return self._normalize_lookup_text(freight_number)

    def _resolve_freight(self, row_data, cache):
        cache_key = self._get_freight_cache_key(row_data["freight_number"])
        freight = cache.get(cache_key)
        if freight is MISSING_FREIGHT:
            freight = FreightCost.objects.create(name=cache_key)
            cache[cache_key] = freight
        elif freight is None:
            freight = (
                FreightCost.objects.annotate(name_ci=Lower("name"))
                .filter(name_ci=cache_key)
                .order_by("id")
                .first()
            )
            if freight is None:
                freight = FreightCost.objects.create(name=cache_key)
            cache[cache_key] = freight

        normalized_burden_type = self._normalize_burden_type(row_data["burden_type"])
        needs_save = freight.pk is None

        if freight.shipping_date != row_data["shipping_date"]:
            freight.shipping_date = row_data["shipping_date"]
            needs_save = True
        if freight.freight_type != row_data["freight_type"]:
            freight.freight_type = row_data["freight_type"]
            needs_save = True
        if freight.burden_type != normalized_burden_type:
            freight.burden_type = normalized_burden_type
            needs_save = True

        if needs_save:
            freight.save()
        return freight

    def _resolve_chunk_freights(self, prepared_rows, cache):
        latest_rows_by_key = {}

        for row_data in prepared_rows:
            cache_key = self._get_freight_cache_key(row_data["freight_number"])
            if cache_key:
                latest_rows_by_key[cache_key] = row_data

        resolved_freights = {}
        for cache_key, row_data in latest_rows_by_key.items():
            resolved_freights[cache_key] = self._resolve_freight(
                row_data=row_data,
                cache=cache,
            )

        return resolved_freights

    def _delete_existing_details_for_freights(self, freights):
        freight_ids = [freight.pk for freight in freights if freight and freight.pk]
        if freight_ids:
            FreightCostDetail.objects.filter(freight_id__in=freight_ids).delete()

    def _iter_prepared_row_chunks(self, data, chunk_size=None):
        chunk_size = max(int(chunk_size or self.import_chunk_size), 1)
        total_rows = len(data.index)

        for start_index in range(0, total_rows, chunk_size):
            chunk = data.iloc[start_index : start_index + chunk_size]
            chunk_indices = chunk.index.tolist()
            chunk_records = chunk.to_dict("records")
            yield [
                self._prepare_import_row(row_index, row)
                for row_index, row in zip(chunk_indices, chunk_records)
            ]

    def _prefill_product_cache(self, prepared_rows, cache):
        pending_keys = []
        product_ids = set()
        product_codes = set()
        product_names = set()

        for row_data in prepared_rows:
            cache_key = (row_data["item_code"], row_data["item_description"])
            if cache_key in cache:
                continue

            pending_keys.append(cache_key)
            item_code = self._clean_text(row_data["item_code"])
            item_description = self._clean_text(row_data["item_description"])
            normalized_code = self._normalize_lookup_text(item_code)
            normalized_description = self._normalize_lookup_text(item_description)

            if item_code.isdigit():
                product_ids.add(int(item_code))
            if normalized_code:
                product_codes.add(normalized_code)
            if normalized_description:
                product_names.add(normalized_description)

        if not pending_keys:
            return

        products_by_id = {}
        products_by_code = {}
        products_by_name = {}

        product_query = Product.objects.select_related("subgroup", "packaging")
        product_filters = Q()
        if product_ids:
            product_filters |= Q(pk__in=product_ids)
        if product_codes:
            product_filters |= Q(code_ci__in=product_codes)
        if product_names:
            product_filters |= Q(name_ci__in=product_names)

        if product_filters:
            for product in product_query.annotate(
                code_ci=Lower("code"),
                name_ci=Lower("name"),
            ).filter(product_filters):
                products_by_id[product.pk] = product
                normalized_code = self._normalize_lookup_text(product.code)
                normalized_name = self._normalize_lookup_text(product.name)
                if normalized_code and normalized_code not in products_by_code:
                    products_by_code[normalized_code] = product
                if normalized_name and normalized_name not in products_by_name:
                    products_by_name[normalized_name] = product

        for item_code, item_description in pending_keys:
            product = None
            normalized_code = self._normalize_lookup_text(item_code)
            normalized_description = self._normalize_lookup_text(item_description)

            if item_code.isdigit():
                product = products_by_id.get(int(item_code))
            if product is None and normalized_code:
                product = products_by_code.get(normalized_code)
            if product is None and normalized_description:
                product = products_by_name.get(normalized_description)

            cache[(item_code, item_description)] = product

    def _prefill_distributor_item_cache(self, prepared_rows, cache):
        pending_keys = []
        distributor_ids = set()
        distributor_codes = set()
        distributor_names = set()

        for row_data in prepared_rows:
            cache_key = (row_data["item_code"], row_data["item_description"])
            if cache_key in cache:
                continue

            pending_keys.append(cache_key)
            item_code = self._clean_text(row_data["item_code"])
            item_description = self._clean_text(row_data["item_description"])
            normalized_code = self._normalize_lookup_text(item_code)
            normalized_description = self._normalize_lookup_text(item_description)

            if item_code.isdigit():
                distributor_ids.add(int(item_code))
            if normalized_code:
                distributor_codes.add(normalized_code)
            if normalized_description:
                distributor_names.add(normalized_description)

        if not pending_keys:
            return

        distributor_items_by_id = {}
        distributor_items_by_code = {}
        distributor_items_by_name = {}

        distributor_query = DistributorItem.objects.select_related(
            "product", "group", "product__subgroup", "product__packaging"
        )
        distributor_filters = Q()
        if distributor_ids:
            distributor_filters |= Q(pk__in=distributor_ids)
        if distributor_codes:
            distributor_filters |= Q(code_ci__in=distributor_codes)
        if distributor_names:
            distributor_filters |= Q(name_ci__in=distributor_names)

        if distributor_filters:
            for distributor_item in distributor_query.annotate(
                code_ci=Lower("code"),
                name_ci=Lower("name"),
            ).filter(distributor_filters):
                distributor_items_by_id[distributor_item.pk] = distributor_item
                normalized_code = self._normalize_lookup_text(distributor_item.code)
                normalized_name = self._normalize_lookup_text(distributor_item.name)
                if normalized_code and normalized_code not in distributor_items_by_code:
                    distributor_items_by_code[normalized_code] = distributor_item
                if normalized_name and normalized_name not in distributor_items_by_name:
                    distributor_items_by_name[normalized_name] = distributor_item

        for item_code, item_description in pending_keys:
            distributor_item = None
            normalized_code = self._normalize_lookup_text(item_code)
            normalized_description = self._normalize_lookup_text(item_description)

            if item_code.isdigit():
                distributor_item = distributor_items_by_id.get(int(item_code))
            if distributor_item is None and normalized_code:
                distributor_item = distributor_items_by_code.get(normalized_code)
            if distributor_item is None and normalized_description:
                distributor_item = distributor_items_by_name.get(normalized_description)

            cache[(item_code, item_description)] = distributor_item

    def _prefill_packaging_cache(self, prepared_rows, cache):
        pending_keys = []
        packaging_ids = set()
        packaging_values = set()

        for row_data in prepared_rows:
            cache_key = self._clean_text(row_data["packaging_value"])
            if cache_key in cache:
                continue

            pending_keys.append(cache_key)
            normalized_value = self._normalize_lookup_text(cache_key)
            if cache_key.isdigit():
                packaging_ids.add(int(cache_key))
            if normalized_value:
                packaging_values.add(normalized_value)

        if not pending_keys:
            return

        packaging_by_id = {}
        packaging_by_value = {}
        packaging_filters = Q()
        if packaging_ids:
            packaging_filters |= Q(pk__in=packaging_ids)
        if packaging_values:
            packaging_filters |= (
                Q(code_ci__in=packaging_values)
                | Q(name_ci__in=packaging_values)
                | Q(initial_ci__in=packaging_values)
                | Q(shortname_ci__in=packaging_values)
            )

        if packaging_filters:
            for packaging in ProductPackage.objects.annotate(
                code_ci=Lower("code"),
                name_ci=Lower("name"),
                initial_ci=Lower("initial"),
                shortname_ci=Lower("shortname"),
            ).filter(packaging_filters):
                packaging_by_id[packaging.pk] = packaging
                for candidate in [
                    packaging.code,
                    packaging.name,
                    packaging.initial,
                    packaging.shortname,
                ]:
                    normalized_candidate = self._normalize_lookup_text(candidate)
                    if normalized_candidate and normalized_candidate not in packaging_by_value:
                        packaging_by_value[normalized_candidate] = packaging

        for cache_key in pending_keys:
            packaging = None
            normalized_value = self._normalize_lookup_text(cache_key)
            if cache_key.isdigit():
                packaging = packaging_by_id.get(int(cache_key))
            if packaging is None and normalized_value:
                packaging = packaging_by_value.get(normalized_value)
            cache[cache_key] = packaging

    def _prefill_principal_cache(self, prepared_rows, cache):
        pending_keys = []
        principal_ids = set()
        principal_values = set()

        for row_data in prepared_rows:
            cache_key = self._clean_text(row_data["principal_value"])
            if cache_key in cache:
                continue

            pending_keys.append(cache_key)
            normalized_value = self._normalize_lookup_text(cache_key)
            if cache_key.isdigit():
                principal_ids.add(int(cache_key))
            if normalized_value:
                principal_values.add(normalized_value)

        if not pending_keys:
            return

        principal_by_id = {}
        principal_by_value = {}
        principal_filters = Q()
        if principal_ids:
            principal_filters |= Q(pk__in=principal_ids)
        if principal_values:
            principal_filters |= (
                Q(code_ci__in=principal_values)
                | Q(name_ci__in=principal_values)
                | Q(initial_ci__in=principal_values)
                | Q(shortname_ci__in=principal_values)
            )

        if principal_filters:
            for principal in Company.objects.annotate(
                code_ci=Lower("code"),
                name_ci=Lower("name"),
                initial_ci=Lower("initial"),
                shortname_ci=Lower("shortname"),
            ).filter(principal_filters):
                principal_by_id[principal.pk] = principal
                for candidate in [
                    principal.code,
                    principal.name,
                    principal.initial,
                    principal.shortname,
                ]:
                    normalized_candidate = self._normalize_lookup_text(candidate)
                    if normalized_candidate and normalized_candidate not in principal_by_value:
                        principal_by_value[normalized_candidate] = principal

        for cache_key in pending_keys:
            principal = None
            normalized_value = self._normalize_lookup_text(cache_key)
            if cache_key.isdigit():
                principal = principal_by_id.get(int(cache_key))
            if principal is None and normalized_value:
                principal = principal_by_value.get(normalized_value)
            cache[cache_key] = principal

    def _prefill_product_distributor_cache(self, prepared_rows, product_cache, cache):
        product_ids = set()

        for row_data in prepared_rows:
            product = product_cache.get((row_data["item_code"], row_data["item_description"]))
            if product and product.pk and product.pk not in cache:
                product_ids.add(product.pk)

        if not product_ids:
            return

        distributors_by_product = {}
        for distributor_item in (
            DistributorItem.objects.select_related(
                "product", "group", "product__subgroup", "product__packaging"
            )
            .filter(product_id__in=product_ids)
            .order_by("product_id", "id")
        ):
            distributors_by_product.setdefault(distributor_item.product_id, distributor_item)

        for product_id in product_ids:
            cache[product_id] = distributors_by_product.get(product_id)

    def _prefill_freight_cache(self, prepared_rows, cache):
        pending_names = set()

        for row_data in prepared_rows:
            cache_key = self._get_freight_cache_key(row_data["freight_number"])
            if cache_key and cache_key not in cache:
                pending_names.add(cache_key)

        if not pending_names:
            return

        for pending_name in pending_names:
            cache[pending_name] = MISSING_FREIGHT

        for freight in FreightCost.objects.annotate(
            name_ci=Lower("name")
        ).filter(name_ci__in=pending_names):
            cache_key = self._get_freight_cache_key(freight.name)
            cache[cache_key] = freight

    def _prefill_relation_caches(self, prepared_rows, caches):
        self._prefill_product_cache(prepared_rows, caches["products"])
        self._prefill_distributor_item_cache(prepared_rows, caches["distributor_items"])
        self._prefill_packaging_cache(prepared_rows, caches["packaging"])
        self._prefill_principal_cache(prepared_rows, caches["principals"])
        self._prefill_product_distributor_cache(
            prepared_rows,
            caches["products"],
            caches["product_distributors"],
        )
        self._prefill_freight_cache(prepared_rows, caches["freights"])

    def _process_batch_chunks(self, request, prepared_row_chunks, batch_size=None):
        caches = {
            "products": {},
            "distributor_items": {},
            "product_distributors": {},
            "packaging": {},
            "principals": {},
            "freights": {},
        }
        created_rows = 0
        null_product_rows = 0
        distributor_fallback_rows = 0
        processed_freights = set()
        seen_detail_signatures = set()
        skipped_duplicate_rows = 0
        skipped_duplicate_details = []
        created_at = timezone.now()
        user_by = request.user if request.user.is_authenticated else None
        batch_size = batch_size or self.bulk_insert_batch_size
        processed_rows = 0
        chunk_count = 0

        self._set_import_progress(
            request,
            status="running",
            phase="processing",
            processed_rows=0,
            created_rows=0,
            skipped_rows=0,
            chunk_count=0,
            message="Menyiapkan import freight cost.",
        )

        for prepared_rows in prepared_row_chunks:
            if not prepared_rows:
                continue

            chunk_count += 1

            with transaction.atomic():
                self._prefill_relation_caches(prepared_rows, caches)
                chunk_freights = self._resolve_chunk_freights(
                    prepared_rows,
                    caches["freights"],
                )
                freights_to_clear = []
                for freight in chunk_freights.values():
                    if freight.pk in processed_freights:
                        continue

                    processed_freights.add(freight.pk)
                    freights_to_clear.append(freight)

                self._delete_existing_details_for_freights(freights_to_clear)
                detail_instances = []

                for row_data in prepared_rows:
                    freight = chunk_freights[
                        self._get_freight_cache_key(row_data["freight_number"])
                    ]

                    resolved_relations = self._resolve_row_relations(row_data, caches)

                    if (
                        resolved_relations["distributor_item"]
                        and not resolved_relations["product_found"]
                    ):
                        distributor_fallback_rows += 1

                    if (
                        not resolved_relations["product"]
                        and not resolved_relations["distributor_item"]
                    ):
                        null_product_rows += 1

                    detail_payload = self._build_detail_payload(
                        row_data=row_data,
                        freight=freight,
                        product=resolved_relations["product"],
                        distributor_item=resolved_relations["distributor_item"],
                        principal=resolved_relations["principal"],
                        packaging=resolved_relations["packaging"],
                        packaging_type_id=resolved_relations["packaging_type_id"],
                        user_by=user_by,
                        created_at=created_at,
                    )

                    detail_signature = self._build_detail_duplicate_signature(detail_payload)
                    if detail_signature in seen_detail_signatures:
                        skipped_duplicate_rows += 1
                        skipped_duplicate_details.append(row_data)
                        continue

                    seen_detail_signatures.add(detail_signature)
                    detail_instances.append(self._build_detail_instance(detail_payload))
                    created_rows += 1

                if detail_instances:
                    FreightCostDetail.objects.bulk_create(
                        detail_instances,
                        batch_size=batch_size,
                    )

            processed_rows += len(prepared_rows)
            self._set_import_progress(
                request,
                status="running",
                phase="processing",
                processed_rows=processed_rows,
                created_rows=created_rows,
                skipped_rows=skipped_duplicate_rows,
                chunk_count=chunk_count,
                message=(
                    f"Chunk {chunk_count} selesai. "
                    f"{processed_rows} baris dibaca, {created_rows} detail diproses."
                ),
            )

        self._notify_duplicate_report(request, skipped_duplicate_details)
        self._set_import_progress(
            request,
            status="completed",
            phase="completed",
            processed_rows=processed_rows,
            created_rows=created_rows,
            skipped_rows=skipped_duplicate_rows,
            chunk_count=chunk_count,
            message=(
                f"Import freight cost selesai. {created_rows} detail diproses, "
                f"{skipped_duplicate_rows} duplikat dilewati."
            ),
        )
        self.message_user(
            request,
            f"Import freight cost berhasil. {created_rows} detail baris diproses. {skipped_duplicate_rows} baris duplikat identik dilewati. {distributor_fallback_rows} baris memakai relasi Distributor Item. {null_product_rows} baris disimpan tanpa Product/Distributor Item.",
            level=messages.SUCCESS,
        )
        return {"download_csv": False}

    def _build_detail_payload(
        self,
        row_data,
        freight,
        product,
        distributor_item,
        principal,
        packaging,
        packaging_type_id,
        user_by,
        created_at,
    ):
        resolved_product = (
            product
            or (
                distributor_item.product
                if distributor_item and distributor_item.product
                else None
            )
        )

        return {
            "freight": freight,
            "product": product,
            "product_distributor": distributor_item,
            "item_code": row_data["item_code"],
            "item_description": row_data["item_description"],
            "from_location": row_data["from_location"],
            "to_location": row_data["to_location"],
            "expedition_name": row_data["expedition_name"],
            "expedition_type": row_data["expedition_type"],
            "kode_cab": row_data["kode_cab"],
            "nama_cab": row_data["nama_cab"],
            "packaging_type_id": (
                packaging_type_id if packaging_type_id is not None else (packaging.pk if packaging else None)
            ),
            "principal": principal,
            "qty_freight": row_data["qty_freight"],
            "total_weight": row_data["total_weight"],
            "group_produk": (
                row_data["group_produk"]
                or (
                    distributor_item.group.name
                    if distributor_item and distributor_item.group
                    else ""
                )
            ),
            "item_group": (
                resolved_product.subgroup.name
                if resolved_product and resolved_product.subgroup
                else row_data["item_group"]
            ),
            "total_freight": row_data["total_freight"],
            "total_cost": row_data["total_cost"],
            "name": row_data["item_code"] or row_data["item_description"] or "",
            "description": row_data["item_description"] or None,
            "remark": (
                row_data["raw_row"].get("GROUP_PRODUK")
                if not pd.isna(row_data["raw_row"].get("GROUP_PRODUK"))
                else None
            ),
            "status": 1,
            "cby": user_by,
            "cat": created_at,
            "deleted": False,
        }

    def _build_detail_instance(self, detail_payload):
        return FreightCostDetail(**detail_payload)

    def _resolve_row_relations(self, row_data, caches):
        product = self._get_cached_product(row_data, caches["products"])
        product_found = product is not None
        distributor_item = self._get_cached_product_distributor(
            product, caches["product_distributors"]
        )

        if not distributor_item:
            distributor_item = self._get_cached_distributor_item(
                row_data, caches["distributor_items"]
            )

        if not product and distributor_item and distributor_item.product:
            product = distributor_item.product

        packaging_resolution = self._resolve_import_packaging(
            row_data,
            caches["packaging"],
        )

        principal = self._get_cached_principal(
            row_data["principal_value"], caches["principals"]
        )
        if self._clean_text(row_data["principal_value"]) and not principal:
            raise ValueError(
                f"Row {row_data['excel_row']}: Principal tidak ditemukan untuk NAMA_PRINCIPAL '{row_data['principal_value']}'."
            )

        return {
            "product": product,
            "product_found": product_found,
            "distributor_item": distributor_item,
            "packaging": packaging_resolution["packaging"],
            "packaging_type_id": packaging_resolution["packaging_type_id"],
            "principal": principal,
        }

    def process_pandas_data(self, request, data):
        if self._should_use_batch_processing(request, data):
            return self.process_pandas_data_batch(
                request,
                data,
                batch_size=self.bulk_insert_batch_size,
            )

        prepared_rows = [
            self._prepare_import_row(index, row) for index, row in data.iterrows()
        ]

        caches = {
            "products": {},
            "distributor_items": {},
            "product_distributors": {},
            "packaging": {},
            "principals": {},
            "freights": {},
        }
        processed_freights = set()
        created_rows = 0
        null_product_rows = 0
        distributor_fallback_rows = 0
        skipped_duplicate_rows = 0
        seen_detail_signatures = set()
        skipped_duplicate_details = []
        created_at = timezone.now()
        user_by = request.user if request.user.is_authenticated else None

        with transaction.atomic():
            for row_data in prepared_rows:
                freight = self._resolve_freight(
                    row_data=row_data,
                    cache=caches["freights"],
                )

                if freight.pk not in processed_freights:
                    freight.details.all().delete()
                    processed_freights.add(freight.pk)

                resolved_relations = self._resolve_row_relations(row_data, caches)
                if (
                    resolved_relations["distributor_item"]
                    and not resolved_relations["product_found"]
                ):
                    distributor_fallback_rows += 1

                if not resolved_relations["product"] and not resolved_relations["distributor_item"]:
                    null_product_rows += 1

                detail_payload = self._build_detail_payload(
                    row_data=row_data,
                    freight=freight,
                    product=resolved_relations["product"],
                    distributor_item=resolved_relations["distributor_item"],
                    principal=resolved_relations["principal"],
                    packaging=resolved_relations["packaging"],
                    packaging_type_id=resolved_relations["packaging_type_id"],
                    user_by=user_by,
                    created_at=created_at,
                )

                detail_signature = self._build_detail_duplicate_signature(detail_payload)
                if detail_signature in seen_detail_signatures:
                    skipped_duplicate_rows += 1
                    skipped_duplicate_details.append(row_data)
                    continue

                seen_detail_signatures.add(detail_signature)
                FreightCostDetail.objects.create(**detail_payload)
                created_rows += 1

        self._notify_duplicate_report(request, skipped_duplicate_details)
        self.message_user(
            request,
            f"Import freight cost berhasil. {created_rows} detail baris diproses. {skipped_duplicate_rows} baris duplikat identik dilewati. {distributor_fallback_rows} baris memakai relasi Distributor Item. {null_product_rows} baris disimpan tanpa Product/Distributor Item.",
            level=messages.SUCCESS,
        )
        return {"download_csv": False}

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        return self._process_batch_chunks(
            request,
            prepared_row_chunks=self._iter_prepared_row_chunks(data),
            batch_size=batch_size,
        )

    def process_pandas_data_batch_chunks(self, request, data_chunks, batch_size=1000):
        prepared_row_chunks = (
            prepared_rows
            for data in data_chunks
            for prepared_rows in self._iter_prepared_row_chunks(
                data,
                chunk_size=len(data.index) or self.import_chunk_size,
            )
        )
        return self._process_batch_chunks(
            request,
            prepared_row_chunks=prepared_row_chunks,
            batch_size=batch_size,
        )
