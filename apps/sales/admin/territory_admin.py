from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import register_if_not_registered, MassActionMixin
from apps.base.filters import StatusListFilter, DeletedListFilter, CustomerMap
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from decimal import Decimal, InvalidOperation
from django.db.models import Count, QuerySet
import os
import tempfile
import chardet
import dbfread
import re
from django.urls import path, reverse
from django.utils.text import slugify
from django import forms
import pandas as pd
import numpy as np
from django.shortcuts import redirect, render

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
from apps.sales.models.territory_models import (
    SalesTeam,
    SalesRegion,
    RegionProvince,
    SalesArea,
    AreaRegency,
    SalesTerritory,
    TerritoryAssignment,
)
from apps.sales.models.sales_models import RepOffice
from apps.sales.models.customer_models import Customer
from apps.humancapital.models.business_models import Business
from apps.humancapital.models.structure_models import Position, Assignment
from apps.base.models.locations import Province, Regency

@register_if_not_registered(SalesTeam)
class SalesTeamAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "business")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")
    ordering = ("code",)
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
                    "business",
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
# ║  Name: SalesRegionAdmin                                    ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesRegion in Admin Site            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/18-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(SalesRegion)
class SalesRegionAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "position",
            "business",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    ordering = ("code",)
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
                    "position",
                    "business",
                    "description",
                    "effective",
                    "terminated",
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
# ║  Name: RegionProvinceAdmin                                 ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering RegionProvince in Admin Site         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/3-2025 by Setiadji                           ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(RegionProvince)
class RegionProvinceAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "region",
            "province",
            "description",
            "effective",
            "terminated",
            "remark",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
        "remark",
    )
    ordering = ("code",)
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
                    "region",
                    "province",
                    "effective",
                    "terminated",
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
# ║  Name: SalesAreaAdmin                                      ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesArea in Admin Site              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/17-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(SalesArea)
class SalesAreaAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "region",
            "repoffice",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    ordering = ("code",)
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
                    "region",
                    "repoffice",
                    "effective",
                    "terminated",
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
# ║  Name: AreaRegencyAdmin                                    ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering AreaRegency in Admin Site            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/4-2025 by Setiadji                           ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(AreaRegency)
class AreaRegencyAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "area",
            "regency",
            "description",
            "effective",
            "terminated",
            "remark",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
        "remark",
    )
    ordering = ("code",)
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
                    "area",
                    "regency",
                    "effective",
                    "terminated",
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
# ║  Name: SalesTerritoryAdmin                                 ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesTerritory in Admin Site         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/18-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(SalesTerritory)
class SalesTerritoryAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "area",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
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
                    "area",
                    "effective",
                    "terminated",
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
# ║  Name: TerritoryAssignmentAdmin                            ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Territory Assignment in Admin Site   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/22-2025 by Setiadji                          ║
# ║  Updates:             by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register_if_not_registered(TerritoryAssignment)
class TerritoryAssignmentAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "assignment",
            "customer",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
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
                    "assignment",
                    "customer",
                    "effective",
                    "terminated",
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


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: KAMAreaAdmin                                        ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering KAMArea in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/17-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
