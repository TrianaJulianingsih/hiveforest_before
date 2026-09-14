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
from apps.sales.models.territory_models import KAMArea

@register_if_not_registered(KAMArea)
class KAMAreaAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
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


