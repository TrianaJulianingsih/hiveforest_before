from django.contrib import admin
from apps.analytics.models.iqvia import IQV_ATC4, IQV_ATC3, IQV_ATC2, IQV_ATC1
from apps.analytics.models.iqvia import IQV_NFC3, IQV_NFC2, IQV_NFC1
from apps.analytics.models.iqvia import IQV_OTC4, IQV_OTC3, IQV_OTC2, IQV_OTC1
from apps.analytics.models.iqvia import IQV_Company, IQV_ComType, IQV_Corp
from apps.analytics.models.iqvia import IQV_RegStat, IQV_EthStat, IQV_EthStatGrp, IQV_BrandDet, IQV_GenFlag
from apps.analytics.models.iqvia import IQV_ITMATrans, IQV_Pack, IQV_Product, IQV_PackForm, IQV_Molecule, IQV_MoleSubFam, IQV_MoleFam
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

# Pandas
from django import forms
import pandas as pd
from django.shortcuts import redirect, render
from django.urls import reverse

class CsvImportForm(forms.Form):
     csv_file = forms.FileField()

@admin.register(IQV_ITMATrans)
class IQV_ITMATransAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) +  BaseModelAdmin.list_display_name + \
        ("quarter", "unit", "valuehna", "date", "year",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "quarter", "unit", "valuehna", "date", "year",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            name_text = row['name']
            name = None  # Default to None if blank
            if pd.notna(name_text) and name_text.strip() != '':
                try:
                    name = IQV_Pack.objects.get(key=name_text)
                except IQV_Pack.DoesNotExist:
                    name = None  # Handle as per your business logic

            # Handle Blank Fields
            code = handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark = handle_blank(row['remark'])
            quarter =  handle_blank(row['quarter'])
            unit = handle_blank(row['unit'])
            valuehna =  handle_blank(row['valuehna'])
            date =  handle_blank(row['date'])
            year =  handle_blank(row['year'])

            IQV_ITMATrans.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                quarter=quarter,
                unit=unit,
                valuehna=valuehna,
                date=date,
                year=year,
                status=row['status']
            )

@admin.register(IQV_Pack)
class IQV_PackAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code","key",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "size", "strength", "launched", "form", "product", "atc4", "otc4", "nfc3",) + \
        ("branddet", "ethstatgrp", "ethstat", "regstat", "molstring", "sales_product",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "key", "initial", "shortname", "size", "strength", "launched", "molstring",)
    list_per_page = 100
    has_pandas_import = True
    fields = BaseModelAdmin.fields + ("launched", "sales_product")
    autocomplete_fields = ("sales_product",)
    dtype_mapping = {
        'code': 'string',
        'atc4': 'string',
        'otc4': 'string',
        'nfc3': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            form_name = row['form']
            form = None  # Default to None if blank
            if pd.notna(form_name) and form_name.strip() != '':
                try:
                    form = IQV_PackForm.objects.get(name=form_name)
                except IQV_PackForm.DoesNotExist:
                    form = None  # Handle as per your business logic

            product_name = row['product']
            product = None  # Default to None if blank
            if pd.notna(product_name) and product_name.strip() != '':
                try:
                    product = IQV_Product.objects.get(name=product_name)
                except IQV_Product.DoesNotExist:
                    product = None  # Handle as per your business logic

            atc4_code = row['atc4']
            atc4 = None  # Default to None if blank
            if pd.notna(atc4_code) and atc4_code.strip() != '':
                try:
                    atc4 = IQV_ATC4.objects.get(code=atc4_code)
                except IQV_ATC4.DoesNotExist:
                    atc4 = None  # Handle as per your business logic

            otc4_code = row['otc4']
            otc4 = None  # Default to None if blank
            if pd.notna(otc4_code) and otc4_code.strip() != '':
                try:
                    otc4 = IQV_OTC4.objects.get(code=otc4_code)
                except IQV_OTC4.DoesNotExist:
                    otc4 = None  # Handle as per your business logic

            nfc3_code = row['nfc3']
            nfc3 = None  # Default to None if blank
            if pd.notna(nfc3_code) and nfc3_code.strip() != '':
                try:
                    nfc3 = IQV_NFC3.objects.get(code=nfc3_code)
                except IQV_NFC3.DoesNotExist:
                    nfc3 = None  # Handle as per your business logic

            branddet_name = row['branddet']
            branddet = None  # Default to None if blank
            if pd.notna(branddet_name) and branddet_name.strip() != '':
                try:
                    branddet = IQV_BrandDet.objects.get(name=branddet_name)
                except IQV_BrandDet.DoesNotExist:
                    branddet = None  # Handle as per your business logic

            ethstatgrp_name = row['ethstatgrp']
            ethstatgrp = None  # Default to None if blank
            if pd.notna(ethstatgrp_name) and ethstatgrp_name.strip() != '':
                try:
                    ethstatgrp = IQV_EthStatGrp.objects.get(name=ethstatgrp_name)
                except IQV_EthStatGrp.DoesNotExist:
                    ethstatgrp = None  # Handle as per your business logic

            ethstat_name = row['ethstat']
            ethstat = None  # Default to None if blank
            if pd.notna(ethstat_name) and ethstat_name.strip() != '':
                try:
                    ethstat = IQV_EthStat.objects.get(name=ethstat_name)
                except IQV_EthStat.DoesNotExist:
                    ethstat = None  # Handle as per your business logic

            regstat_name = row['regstat']
            regstat = None  # Default to None if blank
            if pd.notna(regstat_name) and regstat_name.strip() != '':
                try:
                    regstat = IQV_RegStat.objects.get(name=regstat_name)
                except IQV_RegStat.DoesNotExist:
                    regstat = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            key =  handle_blank(row['key'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])
            size =  handle_blank(row['size'])
            strength =  handle_blank(row['strength'])
            volume =  handle_blank(row['volume'])
            launched =  handle_blank(row['launched'])
            molstring =  handle_blank(row['molstring'])
            sales_product =  handle_blank(row['sales_product'])

            IQV_Pack.objects.create(
                code=code,
                key=key,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                form=form,
                size=size,
                strength=strength,
                volume=volume,
                launched=launched,
                product=product,
                atc4=atc4,
                otc4=otc4,
                nfc3=nfc3,
                branddet=branddet,
                ethstatgrp=ethstatgrp,
                ethstat=ethstat,
                regstat=regstat,
                molstring=molstring,
                sales_product=sales_product,
                status=row['status']
            )

@admin.register(IQV_Product)
class IQV_ProductAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "company",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "company",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            company_name = row['company']
            company = None  # Default to None if blank
            if pd.notna(company_name) and company_name.strip() != '':
                try:
                    company = IQV_Company.objects.get(name=company_name)
                except IQV_Company.DoesNotExist:
                    company = None  # Handle as per your business logic
                    
            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_Product.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                company=company,
                status=row['status']
            )

@admin.register(IQV_PackForm)
class IQV_PackFormAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_PackForm.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )

@admin.register(IQV_Molecule)
class IQV_MoleculeAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "subfamily",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "subfamily",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            subfamily_name = row['subfamily']
            subfamily = None  # Default to None if blank
            if pd.notna(subfamily_name) and subfamily_name.strip() != '':
                try:
                    subfamily = IQV_MoleSubFam.objects.get(name=subfamily_name)
                except IQV_MoleSubFam.DoesNotExist:
                    subfamily = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_Molecule.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                subfamily=subfamily,
                status=row['status']
            )

@admin.register(IQV_MoleSubFam)
class IQV_MoleSubFamAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "family",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "family",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            family_name = row['family']
            family = None  # Default to None if blank
            if pd.notna(family_name) and family_name.strip() != '':
                try:
                    family = IQV_MoleFam.objects.get(name=family_name)
                except IQV_OTC3.DoesNotExist:
                    family = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_MoleSubFam.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                family=family,
                status=row['status']
            )

@admin.register(IQV_MoleFam)
class IQV_MoleFamAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_MoleFam.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )

@admin.register(IQV_Company)
class IQV_CompanyAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "comtype", "corporation",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "comtype", "corporation",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            comtype_name = row['comtype']
            comtype = None  # Default to None if blank
            if pd.notna(comtype_name) and comtype_name.strip() != '':
                try:
                    comtype = IQV_ComType.objects.get(name=comtype_name)
                except IQV_ComType.DoesNotExist:
                    comtype = None  # Handle as per your business logic

            corporation_name = row['corporation']
            corporation = None  # Default to None if blank
            if pd.notna(corporation_name) and corporation_name.strip() != '':
                try:
                    corporation = IQV_Corp.objects.get(name=corporation_name)
                except IQV_Corp.DoesNotExist:
                    corporation = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_Company.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                comtype=comtype,
                corporation=corporation,
                status=row['status']
            )

@admin.register(IQV_RegStat)
class IQV_RegStatAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    fields = BaseModelAdmin.fields +  ("initial",)

@admin.register(IQV_EthStat)
class IQV_EthStatAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial","group",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial","group",)
    fields = BaseModelAdmin.fields +  ("initial","group",)

@admin.register(IQV_EthStatGrp)
class IQV_EthStatGrpAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    fields = BaseModelAdmin.fields +  ("initial",)

@admin.register(IQV_BrandDet)
class IQV_BrandDetAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    fields = BaseModelAdmin.fields +  ("initial",)

@admin.register(IQV_GenFlag)
class IQV_GenFlagAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    fields = BaseModelAdmin.fields +  ("initial",)

@admin.register(IQV_ComType)
class IQV_ComTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code", "initial",) + BaseModelAdmin.list_display_name + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    fields = BaseModelAdmin.fields +  ("initial",)

@admin.register(IQV_Corp)
class IQV_CorpAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_Corp.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )

@admin.register(IQV_OTC4)
class IQV_OTC4Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "otc3",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "otc3",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'otc3': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        def handle_blank(value):
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            otc3_code = row['otc3']
            otc3 = None  # Default to None if blank
            if pd.notna(otc3_code) and otc3_code.strip() != '':
                try:
                    otc3 = IQV_OTC3.objects.get(code=otc3_code)
                except IQV_OTC3.DoesNotExist:
                    otc3 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_OTC4.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                otc3=otc3,
                status=row['status']
            )

@admin.register(IQV_OTC3)
class IQV_OTC3Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "otc2",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "otc2",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'otc2': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        def handle_blank(value):
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            otc2_code = row['otc2']
            otc2 = None  # Default to None if blank
            if pd.notna(otc2_code) and otc2_code.strip() != '':
                try:
                    otc2 = IQV_OTC2.objects.get(code=otc2_code)
                except IQV_OTC2.DoesNotExist:
                    otc2 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_OTC3.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                otc2=otc2,
                status=row['status']
            )

@admin.register(IQV_OTC2)
class IQV_OTC2Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "otc1",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "otc1",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'otc1': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        def handle_blank(value):
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            otc1_code = row['otc1']
            otc1 = None  # Default to None if blank
            if pd.notna(otc1_code) and otc1_code.strip() != '':
                try:
                    otc1 = IQV_OTC1.objects.get(code=otc1_code)
                except IQV_OTC1.DoesNotExist:
                    otc1 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_OTC2.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                otc1=otc1,
                status=row['status']
            )

@admin.register(IQV_OTC1)
class IQV_OTC1Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_OTC1.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )

@admin.register(IQV_NFC3)
class IQV_NFC3Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "nfc2",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "nfc2",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'nfc2': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            nfc2_code = row['nfc2']
            nfc2 = None  # Default to None if blank
            if pd.notna(nfc2_code) and nfc2_code.strip() != '':
                try:
                    nfc2 = IQV_NFC2.objects.get(code=nfc2_code)
                except IQV_NFC2.DoesNotExist:
                    nfc2 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_NFC3.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                nfc2=nfc2,
                status=row['status']
            )

@admin.register(IQV_NFC2)
class IQV_NFC2Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "nfc1",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "nfc1",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'nfc1': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            nfc1_code = row['nfc1']
            nfc1 = None  # Default to None if blank
            if pd.notna(nfc1_code) and nfc1_code.strip() != '':
                try:
                    nfc1 = IQV_NFC1.objects.get(code=nfc1_code)
                except IQV_NFC1.DoesNotExist:
                    nfc1 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_NFC2.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                nfc1=nfc1,
                status=row['status']
            )

@admin.register(IQV_NFC1)
class IQV_NFC1Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_NFC1.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )

@admin.register(IQV_ATC4)
class IQV_ATC4Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "atc3",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "atc3",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'atc3': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            atc3_code = row['atc3']
            atc3 = None  # Default to None if blank
            if pd.notna(atc3_code) and atc3_code.strip() != '':
                try:
                    atc3 = IQV_ATC3.objects.get(code=atc3_code)
                except IQV_ATC3.DoesNotExist:
                    atc3 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_ATC4.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                atc3=atc3,
                status=row['status']
            )

@admin.register(IQV_ATC3)
class IQV_ATC3Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "atc2",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "atc2",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'atc2': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            atc2_code = row['atc2']
            atc2 = None  # Default to None if blank
            if pd.notna(atc2_code) and atc2_code.strip() != '':
                try:
                    atc2 = IQV_ATC2.objects.get(code=atc2_code)
                except IQV_ATC2.DoesNotExist:
                    atc2 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_ATC3.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                atc2=atc2,
                status=row['status']
            )

@admin.register(IQV_ATC2)
class IQV_ATC2Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "atc1",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "atc1",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
        'atc1': 'string'
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            atc1_code = row['atc1']
            atc1 = None  # Default to None if blank
            if pd.notna(atc1_code) and atc1_code.strip() != '':
                try:
                    atc1 = IQV_ATC1.objects.get(code=atc1_code)
                except IQV_ATC1.DoesNotExist:
                    atc1 = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_ATC2.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                atc1=atc1,
                status=row['status']
            )
            
@admin.register(IQV_ATC1)
class IQV_ATC1Admin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        'code': 'string',
    }
    
    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            IQV_ATC1.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )