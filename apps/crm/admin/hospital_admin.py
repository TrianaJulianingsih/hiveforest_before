import os
import traceback
import pandas as pd
import numpy as np
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.timezone import now
from django.utils.text import slugify

from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.models import Province, Regency, CompanyOwnership, CompanyOwner
from apps.crm.models.hospital_models import HospitalType, HospitalClass, Hospital, HospitalBed, HospitalService, HospitalProfessional
from apps.sales.models.customer_models import Customer
from apps.base.filters import DeletedListFilter, StatusListFilter

# CRM | Hospitals
# __________________________

@admin.register(HospitalType)
class HospitalTypeAdmin(MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HopitalTypeAdmin                                    ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering HospitalType in Admin Site           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/17-2025 by Setiadji                          ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝  
    list_display = BaseModelAdmin.list_display_id + ('code',) + BaseModelAdmin.list_display_name + \
        ('initial', 'shortname', 'type_group',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    search_fields = BaseModelAdmin.search_fields + ('code', 'initial', 'shortname', 'type_group',)
    list_filter = ('type_group',)                     # Add filter by group
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'initial', 'shortname', 'type_group', 'description',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )


@admin.register(HospitalClass)
class HospitalClassAdmin(MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HopitalClassAdmin                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering HospitalClass in Admin Site          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/29-2025 by Setiadji                          ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝  
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('classgroup', 'classcode', 'min_beds', 'order',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    search_fields = BaseModelAdmin.search_fields + ('classgroup', 'classcode',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('classgroup', 'classcode', 'min_beds', 'order', 'name')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

@admin.register(Hospital)
class HospitalAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalAdmin                                       ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Hospital in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\admin.py                                   ║
# ║  Created: Jul/29-2025 by Setiadji                          ║
# ║  Updates: Aug/7-2025  by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
    list_display = BaseModelAdmin.list_display_id + ('code',) + BaseModelAdmin.list_display_name + \
        ('raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    search_fields = BaseModelAdmin.search_fields + (
        'code', 'name', 'raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class', 'raw_phone', 'raw_blustat', 'raw_ownership',
        'raw_director', 'raw_landarea', 'raw_buildingarea', 'raw_lastupdate', 'initial', 'shortname', 'alias', 'formername', 'building', 'complex',
        'street', 'postcode', 'longitude', 'latitude'
        )
    list_filter = ('raw_type',) # Add filter by group
    list_per_page = 1000
    has_pandas_import = True

    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class', 'raw_phone', 'raw_blustat',
                       'raw_ownership', 'raw_director', 'raw_landarea', 'raw_buildingarea', 'raw_lastupdate')
        }),
        ('Address Info', {
            'fields': ('building', 'complex', 'street', 'postcode', 'village', 'district', 'regency', 'province', 'longitude', 'latitude',)
        }),
        ('Other Info', {
            'fields': ('initial', 'shortname', 'alias', 'formername', 'hospitaltype', 'hospitalclass', 'ownership', 'owner', 'customer')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

    hospital_column_mapping = {
        'raw_kode' : 'code', 'raw_name' : 'name', 'raw_province' : 'raw_province', 'raw_city' : 'raw_city', 'raw_address' : 'raw_address',
        'raw_phone' : 'raw_phone', 'raw_type' : 'raw_type', 'raw_class': 'raw_class', 'raw_blustat' : 'raw_blustat', 'raw_ownership' : 'raw_ownership',
        'raw_director' : 'raw_director', 'raw_landarea' : 'raw_landarea', 'raw_buildingarea' : 'raw_buildingarea', 'raw_lastupdate' : 'raw_lastupdate',
        'initial' : 'initial', 'shortname' : 'shortname', 'alias' : 'alias', 'formername' : 'formername', 'building' : 'building', 'complex' : 'complex',
        'street' : 'street', 'postcode' : 'postcode', 'longitude' : 'longitude', 'latitude' : 'latitude', 'hospitaltype' : 'hospitaltype',
        'hospitalclass' : 'hospitalclass', 'ownership' : 'ownership', 'owner' : 'owner', 'village' : 'village', 'district': 'district', 'regency' : 'regency',
        'province' : 'province', 'customer' : 'customer'
    }

    hospital_dtype_mapping = {
        'code' : 'string', 'name' : 'string', 'raw_province' : 'string', 'raw_city' : 'string', 'raw_address' : 'string', 'raw_phone' : 'string',
        'raw_type' : 'string', 'raw_class': 'string', 'raw_blustat' : 'string', 'raw_ownership' : 'string', 'raw_director' : 'string', 'raw_landarea' : 'float',
        'raw_buildingarea' : 'float', 'raw_lastupdate' : 'date', 'initial' : 'string', 'shortname' : 'string', 'alias' : 'string', 'formername' : 'string',
        'building' : 'string', 'complex' : 'string', 'street' : 'string', 'postcode' : 'string', 'longitude' : 'float', 'latitude' : 'float',
        'hospitaltype' : 'string', 'hospitalclass' : 'string', 'ownership' : 'string', 'owner' : 'string', 'village' : 'Int64', 'district': 'Int64',
        'regency' : 'string', 'province' : 'string', 'customer' : 'Int64'
    }

    bed_column_mapping = {
        'raw_kode' : 'code', 'raw_bedno' : 'raw_bedno', 'raw_bedclass' : 'raw_bedclass', 'raw_beds' : 'raw_beds'
    }

    bed_dtype_mapping = {
        'code' : 'string', 'raw_bedno' : 'Int64', 'raw_bedclass' : 'string', 'raw_beds' : 'Int64'
    }

    service_column_mapping = {
        'raw_kode' : 'code', 'raw_serviceno' : 'raw_serviceno', 'raw_service' : 'raw_service'
    }

    service_dtype_mapping = {
        'code' : 'string', 'raw_serviceno' : 'Int64', 'raw_service' : 'string'
    }

    professional_column_mapping = {
        'raw_kode' : 'code', 'raw_profno' : 'raw_profno', 'raw_profgroup' : 'raw_profgroup', 'raw_professional' : 'raw_professional', 'raw_profs' : 'raw_profs'
    }

    professional_dtype_mapping = {
        'code' : 'string', 'raw_profno' : 'Int64', 'raw_profgroup' : 'string', 'raw_professional' : 'string', 'raw_profs' : 'Int64'
    }

    def changelist_view(self, request, extra_context=None):
        # This is to display if this model has Pandas Import and give the link for pandas import
        opts = self.model._meta
        pandas_import_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_pandas_import")
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def normalize_column_name(self,field):
        # Remove special characters and convert to lowercase
        if field is None:
            return ''
        field = str(field)  # ensure it's a string
        characters_to_remove = [' ', '.', '_', '-', '(', ')', '%', '!', '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, '')
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]
        return fix_column_mapping

    def prepare_fk_columns(self, df, model, fk_mappings=None, request=None, id_fields=None):
        id_fields = set(id_fields or set())

        def _clean_str(s):
            return s.astype('string').str.strip().replace({'': None, '-': None, '--': None, '—': None, 'N/A': None, 'NA': None, 'NULL': None, 'None': None})

        def _dynamic_maps(RelModel):
            code_map, name_map = {}, {}
            if hasattr(RelModel, '_meta'):
                if any(getattr(f, 'name', '') == 'code' for f in RelModel._meta.get_fields()):
                    code_map = {str(c).strip().upper(): i for c, i in RelModel.objects.values_list('code', 'id')}
                if any(getattr(f, 'name', '') == 'name' for f in RelModel._meta.get_fields()):
                    name_map = {str(n).strip().upper(): i for n, i in RelModel.objects.values_list('name', 'id')}
            return code_map, name_map

        for f in model._meta.get_fields():
            if not getattr(f, 'many_to_one', False) or not getattr(f, 'concrete', False):
                continue

            field   = f.name          # 'customer', 'district', 'province', ...
            attname = f.attname       # 'customer_id', 'district_id', ...

            if field not in df.columns:
                continue

            # --- ID path (ONLY for whitelisted fields) ---
            if field in id_fields:
                # Respect your dtype step: if already Int64, just copy through; else coerce safely
                if str(df[field].dtype) == 'Int64':
                    df[attname] = df[field]
                else:
                    df[attname] = pd.to_numeric(df[field], errors='coerce').astype('Int64')
                # (optional) warn if some non-empty values could not become ints
                if request:
                    raw = _clean_str(df[field])
                    bad = raw[(raw.notna()) & df[attname].isna()].unique()
                    if len(bad):
                        sample = ', '.join(map(str, bad[:10])); more = '...' if len(bad) > 10 else ''
                        self.message_user(request, f"{field}: {len(bad)} invalid IDs skipped (sample: {sample}{more})", level=messages.WARNING)
                continue

            # --- CODE/NAME path for all other FKs ---
            src = _clean_str(df[field]).str.upper()
            mapped = None
            if fk_mappings and field in fk_mappings:
                mapped = src.map(fk_mappings[field])

            try:
                RelModel = f.remote_field.model
                code_map, name_map = _dynamic_maps(RelModel)
                m2 = src.map(code_map)
                mapped = mapped.fillna(m2) if mapped is not None else m2
                m3 = src.map(name_map)
                mapped = mapped.fillna(m3) if mapped is not None else m3
            except Exception as e:
                if request:
                    self.message_user(request, f"FK mapping error for {field}: {e}", level=messages.ERROR)

            df[attname] = mapped

        return df

    def get_foreign_key_mappings(self, request=None):
        """
        Create mappings for foreign key fields from code to ID
        """
        def norm(x):
            if x is None:
                return None
            return str(x).strip().upper()
        
        mappings = {}

        def warn(msg):
            if request:
                self.message_user(request, msg, level=messages.WARNING)
            else:
                print(f"Warning: {msg}")

        # Hospital Type
        if hasattr(self.model, 'hospitaltype'):
            try:
                mappings['hospitaltype'] = {norm(code): id_ for code, id_ in HospitalType.objects.values_list('code', 'id')}
            except Exception as e:
                warn(f"Could not create hospitaltype mapping: {e}")

        # Hospital Class (name -> id)
        if hasattr(self.model, 'hospitalclass'):
            try:
                mappings['hospitalclass'] = {norm(name): id_ for name, id_ in HospitalClass.objects.values_list('name', 'id')}
            except Exception as e:
                warn(f"Could not create hospitalclass mapping: {e}")

        # Ownership
        if hasattr(self.model, 'ownership'):
            try:
                mappings['ownership'] = {norm(code): id_ for code, id_ in CompanyOwnership.objects.values_list('code', 'id')}
            except Exception as e:
                warn(f"Could not create ownership mapping: {e}")

        # Owner
        if hasattr(self.model, 'owner'):
            try:
                mappings['owner'] = {norm(code): id_ for code, id_ in CompanyOwner.objects.values_list('code', 'id')}
            except Exception as e:
                warn(f"Could not create owner mapping: {e}")

        # Regency
        if hasattr(self.model, 'regency'):
            try:
                mappings['regency'] = {norm(code): id_ for code, id_ in Regency.objects.values_list('code', 'id')}
            except Exception as e:
                warn(f"Could not create regency mapping: {e}")

        # Province
        if hasattr(self.model, 'province'):
            try:
                mappings['province'] = {norm(code): id_ for code, id_ in Province.objects.values_list('code', 'id')}
            except Exception as e:
                warn(f"Could not create province mapping: {e}")

        return mappings

    def process_foreign_key_lookups(self, df, foreign_key_mappings=None, request=None):
        """
        Robust FK mapper:
        - Tries provided mapping first (usually code; hospitalclass may be name).
        - Falls back to dynamic DB lookups: code -> id, then name -> id.
        - For HospitalClass, also tries "last segment after '-'" to handle labels like 'General Hospital - Class B'.
        """

        def _norm_series(s):
            s = s.astype('string')
            s = s.str.strip().str.upper()
            return s.replace({'': None})

        def _has_field(Model, field):
            return any(getattr(f, 'name', None) == field for f in Model._meta.get_fields())

        # FK fields we want to process (present in Hospital sheet)
        fk_fields = ['hospitaltype', 'hospitalclass', 'ownership', 'owner', 'regency', 'province']

        for field_name in fk_fields:
            if field_name not in df.columns:
                continue

            fk_field = f"{field_name}_id"
            norm_col = _norm_series(df[field_name])
            mapped = None

            # 1) Try provided mapping first (if any)
            if foreign_key_mappings and field_name in foreign_key_mappings:
                mapped = norm_col.map(foreign_key_mappings[field_name])

            # 2) Dynamic fallback by introspecting the related model
            try:
                rel = self.model._meta.get_field(field_name).remote_field
                RelModel = rel.model

                # Build and try code map
                if _has_field(RelModel, 'code'):
                    code_map = {str(c).strip().upper(): i for c, i in RelModel.objects.values_list('code', 'id')}
                    mapped2 = norm_col.map(code_map)
                    mapped = mapped.fillna(mapped2) if mapped is not None else mapped2

                # Build and try name map (plain)
                if _has_field(RelModel, 'name'):
                    name_map = {str(n).strip().upper(): i for n, i in RelModel.objects.values_list('name', 'id')}
                    mapped2 = norm_col.map(name_map)
                    mapped = mapped.fillna(mapped2) if mapped is not None else mapped2

                # Special cleaner for HospitalClass: take last segment after '-' or '–'
                if field_name == 'hospitalclass' and _has_field(RelModel, 'name'):
                    norm_col2 = norm_col.str.replace('–', '-', regex=False).str.split('-').str[-1].str.strip()
                    mapped2 = norm_col2.map(name_map)  # reuse name_map built above
                    mapped = mapped.fillna(mapped2) if mapped is not None else mapped2

            except Exception as e:
                if request:
                    self.message_user(request, f"FK mapping error for {field_name}: {e}", level=messages.ERROR)

            # 3) Write results without clobbering existing IDs
            if fk_field in df.columns:
                df[fk_field] = df[fk_field].where(df[fk_field].notna(), mapped)
            else:
                df[fk_field] = mapped

            # 4) Admin warning for any unmapped values that were present
            present = norm_col.notna()
            missing_vals = norm_col[present & df[fk_field].isna()].unique()
            if request and len(missing_vals):
                sample = ', '.join(map(str, missing_vals[:10]))
                more = '...' if len(missing_vals) > 10 else ''
                self.message_user(
                    request,
                    f"{field_name}: {len(missing_vals)} values not mapped (sample: {sample}{more})",
                    level=messages.WARNING
                )

        return df

    def bulk_update_insert(self, request, data, model, unique_key, list_insert_columns, list_update_columns = False, hospital_data = False):
        try:
            if not list_update_columns: list_update_columns = list_insert_columns

            # Only keep columns that exist on the model
            model_field_names = set()
            for f in model._meta.get_fields():
                n = getattr(f, 'name', None)
                a = getattr(f, 'attname', None)
                if n: model_field_names.add(n)
                if a: model_field_names.add(a)
            list_insert_columns = [c for c in list_insert_columns if c in model_field_names]
            list_update_columns = [c for c in list_update_columns if c in model_field_names]

            user_by = request.user if request.user.is_authenticated else None
            data = data.replace({np.nan: None})

            # Build map unique_key -> id
            filter_kwargs = {f"{unique_key}__in": data[unique_key]}
            existing_map = dict(model.objects.filter(**filter_kwargs).values_list(unique_key, "id"))

            data["__exists"] = data[unique_key].isin(existing_map.keys())
            existing_records = data[data["__exists"]]
            new_records = data[~data["__exists"]]

            created = updated = 0
            with transaction.atomic():
                if not new_records.empty:
                    objs = [
                        model(**row, status=1, cby=user_by, cat=now())
                        for row in new_records[list_insert_columns].to_dict(orient='records')
                    ]
                    model.objects.bulk_create(objs, batch_size=1000)
                    created = len(objs)

                if not existing_records.empty:
                    objs = []
                    for row in existing_records[list_update_columns].to_dict(orient='records'):
                        # attach pk for bulk_update
                        row_id = existing_map.get(row[unique_key])
                        if row_id:
                            objs.append(model(id=row_id, **row, status=1, uby=user_by, uat=now()))
                    if objs:
                        model.objects.bulk_update(objs, list_update_columns + ['uat', 'uby'], batch_size=1000)
                        updated = len(objs)

            self.message_user(request, f"{model.__name__}: inserted {created}, updated {updated}.", level=messages.INFO)
            return {"inserted": created, "updated": updated}

        except Exception as e:
            raise ValueError(f"Error on bulk upsert process {e}")

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        ## PROCESS HOSPITAL
        try:
            hospital_column_mapping = getattr(self, 'hospital_column_mapping', {})
            hospital_dtype_mapping = getattr(self, 'hospital_dtype_mapping', {})

            # Prepare Records
            df_hospital = data['df_hospital']
            df_hospital.rename(columns=hospital_column_mapping, inplace=True)

            # None value if column not exist
            for col in hospital_dtype_mapping.keys():
                if col not in df_hospital.columns:
                    df_hospital[col] = None

            for col, dtype in hospital_dtype_mapping.items():
                try:
                    if dtype == 'date':
                        df_hospital[col] = pd.to_datetime(df_hospital[col], errors='coerce')
                    elif dtype == 'Int64':  # nullable integer
                        df_hospital[col] = pd.to_numeric(df_hospital[col], errors='coerce').astype('Int64')
                    else:
                        df_hospital[col] = df_hospital[col].astype(dtype)
                except Exception as e:
                    traceback.print_exc()
                    self.message_user(request, f"Error converting column '{col}': {e} | Type: {type(e).__name__}", level=messages.ERROR)
                    return HttpResponseRedirect(request.path)

            df_hospital['name'] = df_hospital[['name','code']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
            df_hospital['slug'] = df_hospital['name'].apply(slugify)

            # 🆕 NEW: Handle foreign key lookups
            fk_maps = self.get_foreign_key_mappings(request)
            df_hospital = self.prepare_fk_columns(
                df_hospital,
                Hospital,
                fk_mappings=fk_maps,
                request=request,
                id_fields={'customer', 'district', 'village'}
            )

            # Update the column lists to include the new _id fields for Django ForeignKeys
            base_columns = ['code','name','raw_province','raw_city','raw_address', 'raw_phone', 'raw_type', 
                        'raw_class', 'raw_blustat', 'raw_ownership','raw_director','raw_landarea', 
                        'raw_buildingarea', 'raw_lastupdate', 'initial', 'shortname', 'alias', 'formername',
                        'building', 'complex', 'street', 'postcode', 'longitude','latitude', 'slug']
            # include every *_id produced by the helper (covers customer_id + others)
            id_columns = [c for c in df_hospital.columns if c.endswith('_id')]
            all_columns = base_columns + id_columns
            
            sample = df_hospital[['code','customer_id','district_id', 'village_id']].head(3).to_dict(orient='records')
            self.message_user(request, f"Sample IDs → {sample}", level=messages.INFO)

            # Upsert Records
            self.bulk_update_insert(
                request,
                data = df_hospital,
                model = Hospital,
                unique_key ='code',
                list_insert_columns = all_columns,
                list_update_columns = all_columns,
                hospital_data = True
            )

            self.message_user(request, "Completed processing of Hospital data", level=messages.INFO)
        
        except Exception as e:
            raise ValueError(f"Error processing of Hospital data {e}")
        
        ## Hospital Codes for reference
        hospital_codes = dict(Hospital.objects.all().values_list("code", "id"))
        hospital_names = dict(Hospital.objects.all().values_list("id", "name"))
        
        ## PROCESS HOSPITAL BED
        try:
            bed_column_mapping = getattr(self, 'bed_column_mapping', {})
            bed_dtype_mapping = getattr(self, 'bed_dtype_mapping', {})

            # Prepare Records
            df_bed = data['df_bed']
            df_bed.rename(columns=bed_column_mapping, inplace=True)

            for col, dtype in bed_dtype_mapping.items():
                if dtype == 'date':
                    df_bed[col] = pd.to_datetime(df_bed[col], errors='coerce')
                else:
                    df_bed[col] = df_bed[col].astype(dtype)

            # Map hospital_id by code        
            df_bed['hospital_id'] = df_bed['code'].map(hospital_codes)
            missing = df_bed[df_bed['hospital_id'].isna()]['code'].dropna().unique()
            if len(missing) > 0:
                self.message_user(
                    request,
                    f"Bed rows skipped: {len(missing)} unmatched hospital code(s) (sample: {', '.join(map(str, missing[:10]))}{'...' if len(missing)>10 else ''})",
                    level=messages.WARNING
                )
            df_bed = df_bed[df_bed['hospital_id'].notna()]

            df_bed['name'] = df_bed['hospital_id'].map(hospital_names)
            df_bed['slug'] = (df_bed['hospital_id'].astype(str) + '-' + df_bed['raw_bedno'].astype(str) + '-' + df_bed['raw_bedclass']).apply(slugify)

            self.bulk_update_insert(
                request,
                data = df_bed,
                model = HospitalBed,
                unique_key ='slug',
                list_insert_columns = list(bed_dtype_mapping.keys()) + ['slug', 'name', 'hospital_id'])
            
            self.message_user(request, "Completed processing of Hospital Bed data.")

        except Exception as e:
            raise ValueError(f"Error processing of Hospital Bed data {e}")
        
        ## PROCESS HOSPITAL SERVICE
        try:
            service_column_mapping = getattr(self, 'service_column_mapping', {})
            service_dtype_mapping = getattr(self, 'service_dtype_mapping', {})

            # Prepare Records
            df_service = data['df_service']
            df_service.rename(columns=service_column_mapping, inplace=True)

            for col, dtype in service_dtype_mapping.items():
                if dtype == 'date':
                    df_service[col] = pd.to_datetime(df_service[col], errors='coerce')
                else:
                    df_service[col] = df_service[col].astype(dtype)

            df_service['hospital_id'] = df_service['code'].map(hospital_codes)
            missing = df_service[df_service['hospital_id'].isna()]['code'].dropna().unique()
            if len(missing) > 0:
                self.message_user(
                    request,
                    f"Bed rows skipped: {len(missing)} unmatched hospital code(s) (sample: {', '.join(map(str, missing[:10]))}{'...' if len(missing)>10 else ''})",
                    level=messages.WARNING
                )
            df_service = df_service[df_service['hospital_id'].notna()]

            df_service['name'] = df_service['hospital_id'].map(hospital_names)
            df_service['slug'] = (df_service['hospital_id'].astype(str) + '-' + df_service['raw_serviceno'].astype(str) + '-' + df_service['raw_service']).apply(slugify)
            
            self.bulk_update_insert(
                request,
                data = df_service,
                model = HospitalService,
                unique_key = 'slug',
                list_insert_columns = list(service_dtype_mapping.keys()) + ['slug','name', 'hospital_id'])

            self.message_user(request, "Completed processing of Hospital Service data.")

        except Exception as e:
            raise ValueError(f"Error processing of Hospital Service data {e}")
        
        ## PROCESS HOSPITAL PROFESSIONAL
        try:
            professional_column_mapping = getattr(self, 'professional_column_mapping', {})
            professional_dtype_mapping = getattr(self, 'professional_dtype_mapping', {})

            # Prepare Records
            df_professional = data['df_professional']
            df_professional.rename(columns=professional_column_mapping, inplace=True)

            for col, dtype in professional_dtype_mapping.items():
                if dtype == 'date':
                    df_professional[col] = pd.to_datetime(df_professional[col], errors='coerce')
                else:
                    df_professional[col] = df_professional[col].astype(dtype)
            
            df_professional['hospital_id'] = df_professional['code'].map(hospital_codes)
            missing = df_professional[df_professional['hospital_id'].isna()]['code'].dropna().unique()
            if len(missing) > 0:
                self.message_user(
                    request,
                    f"Bed rows skipped: {len(missing)} unmatched hospital code(s) (sample: {', '.join(map(str, missing[:10]))}{'...' if len(missing)>10 else ''})",
                    level=messages.WARNING
                )
            df_professional = df_professional[df_professional['hospital_id'].notna()]

            df_professional['name'] = df_professional['hospital_id'].map(hospital_names)
            df_professional['slug'] = (df_professional['hospital_id'].astype(str) + '-' + df_professional['raw_profno'].astype(str) + '-' + df_professional['raw_professional']).apply(slugify)

            self.bulk_update_insert(request, data = df_professional, model = HospitalProfessional, unique_key = 'slug', 
                list_insert_columns = list(professional_dtype_mapping.keys()) + ['slug','name', 'hospital_id'])
            self.message_user(request, "Completed processing of Hospital Professional data.")
        except Exception as e:
            raise ValueError(f"Error processing of Hospital Professional data {e}")

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level=messages.ERROR)
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            all_data = None
            try:
                if file_extension not in [".xls", ".xlsx"]:
                    self.message_user(request, f"Unsupported file format: {file_extension}", level=messages.ERROR)
                    return HttpResponseRedirect(request.path)

                # Read ALL sheets once
                wanted = ["Hospital", "Bed", "Service", "Professional"]
                try:
                    sheets = pd.read_excel(
                        uploaded_file,
                        sheet_name=wanted,
                        dtype=str,           # start as str; we’ll cast later
                        engine="openpyxl"    # optional; fine for xlsx
                    )
                except ValueError as ve:
                    # Typically: "Worksheet named '...' not found"
                    self.message_user(request, f"{ve}", level=messages.ERROR)
                    return HttpResponseRedirect(request.path)

                all_data = {
                    'df_hospital': sheets.get("Hospital"),
                    'df_bed': sheets.get("Bed"),
                    'df_service': sheets.get("Service"),
                    'df_professional': sheets.get("Professional"),
                }

                # Basic presence check
                missing = [k for k, v in all_data.items() if v is None]
                if missing:
                    self.message_user(request, f"Missing required sheet(s): {', '.join(missing)}", level=messages.ERROR)
                    return HttpResponseRedirect(request.path)

                self.message_user(request, "Processing data...", level=messages.INFO)
                response = self.process_pandas_data_batch(request, all_data)

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.", level=messages.SUCCESS)
                return HttpResponseRedirect("..")
            
            except Exception as e:
                traceback.print_exc()
                self.message_user(request, f"Error importing data: {e}\nType: {type(e).__name__}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,
        }
        return render(request, "admin/pandas_import.html", context)

@admin.register(HospitalBed)
class HospitalBedAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalBedAdmin                                    ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering HospitalBed in Admin Site            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\admin.py                                   ║
# ║  Created: Aug/6-2025 by Setiadji                           ║
# ║  Updates: Aug/7-2025  by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('hospital','raw_bedno','raw_bedclass','raw_beds',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('hospital',)
    search_fields = BaseModelAdmin.search_fields + ('hospital__name', 'raw_bedno','raw_bedclass','raw_beds',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('hospital', 'name', 'raw_bedno','raw_bedclass','raw_beds',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

@admin.register(HospitalService)
class HospitalServiceAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalServiceAdmin                                ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering HospitalService in Admin Site        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\admin.py                                   ║
# ║  Created: Aug/7-2025 by Setiadji                           ║
# ║  Updates: Aug/ -2025  by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('hospital','raw_serviceno', 'raw_service',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('hospital',)
    search_fields = BaseModelAdmin.search_fields + ('hospital__name', 'raw_serviceno', 'raw_service',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('hospital', 'name', 'raw_serviceno', 'raw_service',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

@admin.register(HospitalProfessional)
class HospitalProfessionalAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: HospitalProfessionalAdmin                           ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering HospitalProfessional in Admin Site   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\crm\admin.py                                   ║
# ║  Created: Aug/7-2025 by Setiadji                           ║
# ║  Updates: Aug/ -2025  by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('hospital','raw_profno', 'raw_profgroup', 'raw_professional', 'raw_profs',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('hospital',)
    search_fields = BaseModelAdmin.search_fields + ('hospital__name', 'raw_profno', 'raw_profgroup', 'raw_professional', 'raw_profs',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('hospital', 'name', 'raw_profno', 'raw_profgroup', 'raw_professional', 'raw_profs',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )
