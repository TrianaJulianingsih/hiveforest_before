from django.forms.widgets import *
from django.forms import TextInput, Textarea
from django.db import models
from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.filters import StatusListFilter, DeletedListFilter
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
from apps.supplychain.models.distributions_models import (
    Distributor,
    StDistDaily,
    Branch,
    DistributorItem,
)
from apps.base.models.entities import Company

@admin.register(Distributor)
class DistributorAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "company")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "company")


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: StDistDaily                                           ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering StockDailyDistributor in Admin Site    ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Jul/7 by Noval                                     ║
# ║  Updates: Jul/9 by Noval                                     ║
# ╚══════════════════════════════════════════════════════════════╝
@admin.register(StDistDaily)
class StDistDailyAdmin(MassActionMixin, BaseModelAdmin):
    list_select_related = ("branch", "distributor")

    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "kd_prod",
            "nm_prod",
            "kd_hrmn",
            "nm_hrmn",
            "kd_prc",
            "kd_cab",
            "id_cab",
            "nm_cab",
            "branch",
            "kd_io",
            "lot",
            "ed",
            "hna",
            "reg",
            "itr",
            "pp",
            "po",
            "ext",
            "dmg",
            "atr",
            "ket",
            "periode",
            "tgl_proses",
            "distributor",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "kd_prod",
        "nm_prod",
        "kd_hrmn",
        "nm_hrmn",
        "kd_prc",
        "kd_cab",
        "id_cab",
        "nm_cab",
        "branch__name",
        "kd_io",
        "lot",
        "ed",
        "hna",
        "reg",
        "itr",
        "pp",
        "po",
        "ext",
        "dmg",
        "atr",
        "ket",
        "periode",
        "tgl_proses",
        "distributor__code",
        "distributor__name",
        "distributor__initial",
        "distributor__shortname",
    )
    
# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: DODetailAdmin                                         ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering DODetail in Admin Site                 ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Jul/14 by Noval                                    ║
# ║  Updates: Jul/17 by Noval                                    ║
# ╚══════════════════════════════════════════════════════════════╝
