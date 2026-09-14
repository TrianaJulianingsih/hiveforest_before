from django.contrib import admin
from apps.sales.models.product_models import (
    Product,
    ProductPackage,
    ProductCategory,
    ProductSubgroup,
    ProductGroup,
)
from apps.humancapital.models.business_models import Business
from apps.base.models.entities import Company
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import register_if_not_registered, MassActionMixin
from django.urls import reverse
import pandas as pd


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  PRODUCT MODULE                                            ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin\product_admin.py                   ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(Product)
class ProductAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "subgroup",
            "targetgroup",
            "category",
            "packaging",
            "business__initial",
            "owner",
        )
        + (
            "package",
            "size",
            "uom",
            "height",
            "length",
            "width",
            "weight",
            "box_per_palletac",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "subgroup",
                    "targetgroup",
                    "category",
                    "packaging",
                    "business",
                    "owner",
                    "description",
                )
            },
        ),
        (
            "Other Info",
            {
                "fields": (
                    "package",
                    "size",
                    "uom",
                    "height",
                    "length",
                    "width",
                    "weight",
                    "box_per_palletac",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "remark", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    list_per_page = 1000
    dtype_mapping = {"code": "string"}

    def get_search_results(self, request, queryset, search_term):
        qs, use_distinct = super().get_search_results(request, queryset, search_term)
        qs = qs.order_by("code", "name")
        return qs, use_distinct

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        def handle_blank(value):
            if pd.isna(value) or value == "":
                return None
            return value

        for _, row in data.iterrows():
            subgroup_code = row["subgroup"]
            subgroup = ProductSubgroup.objects.get(code=subgroup_code)

            category_name = row["category"]
            category = ProductCategory.objects.get(name=category_name)

            package_code = row["package"]
            package = None
            if pd.notna(package_code) and package_code.strip() != "":
                try:
                    package = ProductPackage.objects.get(code=package_code)
                except ProductPackage.DoesNotExist:
                    package = None

            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            owner_code = row["owner"]
            owner = Company.objects.get(code=owner_code)

            initial = handle_blank(row["initial"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            shortname = handle_blank(row["shortname"])
            targetgroup = handle_blank(row["targetgroup"])

            size = handle_blank(row["size"])
            height = handle_blank(row["height"])
            length = handle_blank(row["length"])
            width = handle_blank(row["width"])
            weight = handle_blank(row["weight"])
            box_per_palletac = handle_blank(row.get("box_per_palletac"))

            Product.objects.create(
                code=row["code"],
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                subgroup=subgroup,
                targetgroup=targetgroup,
                category=category,
                package=package,
                business=business,
                owner=owner,
                size=size,
                height=height,
                length=length,
                width=width,
                weight=weight,
                box_per_palletac=box_per_palletac,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductPackageAdmin                                 ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Package in Admin Site        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin\product_admin.py                   ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(ProductPackage)
class ProductPackageAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductCategoryAdmin                                ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Category in Admin Site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin\product_admin.py                   ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(ProductCategory)
class ProductCategoryAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductSubgroupAdmin                                ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Subgroup in Admin Site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin\product_admin.py                   ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(ProductSubgroup)
class ProductSubgroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("business", "group", "initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "business",
                    "name",
                    "initial",
                    "shortname",
                    "group",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    dtype_mapping = {"code": "string"}

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        for _, row in data.iterrows():
            group_code = row["group"]
            group = ProductGroup.objects.get(code=group_code)

            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            ProductSubgroup.objects.create(
                code=row["code"],
                business=business,
                name=row["name"],
                description=row["description"],
                remark=row["remark"],
                initial=row["initial"],
                shortname=row["shortname"],
                group=group,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductGroupAdmin                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Group in Admin Site          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin\product_admin.py                   ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/22-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(ProductGroup)
class ProductGroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("team", "business", "initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "team",
                    "business",
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    dtype_mapping = {"code": "string"}

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        for _, row in data.iterrows():
            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            ProductGroup.objects.create(
                business=business,
                code=row["code"],
                name=row["name"],
                description=row["description"],
                remark=row["remark"],
                initial=row["initial"],
                shortname=row["shortname"],
                status=row["status"],
            )
