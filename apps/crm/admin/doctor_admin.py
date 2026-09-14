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
from apps.base.models import Province, Regency, Person
from apps.crm.models.hcps_models import Doctor, DoctorEducation, DoctorPlace, DoctorSpeciality, Specialization
from apps.base.filters import DeletedListFilter, StatusListFilter

# CRM | HCP
# __________________________

@admin.register(Doctor)
class DoctorAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("profile_picture", "prefix", "person__name", "suffix", "license", "start_year", "start_month", "private_practice", "source_id",) + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("prefix", "person__name", "suffix", "license", "start_year", "start_month", "private_practice", "source_id",)
    list_per_page = 1000
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
        'prefix',
    )
    has_pandas_import = True
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name','person', 'prefix', 'suffix', 'license', 'start_year', 'start_month',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug'),
            'description': 'System related information.',
        }),
    )

    doctor_column_mapping = {
        'ID' : 'source_id',
        'Prefix' : 'prefix',
        'First Name' : 'first_name',
        'Midle Name' : 'mid_name',
        'Last Name' : 'last_name',
        'Suffix' : 'suffix',
        'License' : 'license',
        'Start Year': 'start_year',
        'Start Month' : 'start_month',
        'Private Practice' : 'private_practice'
    }
    education_column_mapping = {
        'ID' : 'source_id',
        'University': 'institution',
        'Completed Year' : 'completed_year',
        'Completed Month' : 'completed_month'
    }
    place_column_mapping = {
        'ID' : 'source_id',
        'Province' : 'province_desc',
        'City' : 'city_desc',
        'Place' : 'place_desc'
    }
    speciality_column_mapping = {
        'ID' : 'source_id',
        'Specialty' : 'speciality_desc'
    }

    doctor_dtype_mapping = {
        'source_id' : 'string',
        'prefix' : 'string',
        'first_name' : 'string',
        'mid_name' : 'string',
        'last_name' : 'string',
        'suffix' : 'string',
        'license' : 'string',
        'start_year' : 'int64',
        'start_month' : 'int64',
        'private_practice' : 'string'
    }
    education_dtype_mapping = {
        'source_id' : 'string',
        'institution' : 'string',
        'completed_year' : 'int64',
        'completed_month' : 'int64'
    }
    place_dtype_mapping = {
        'source_id' : 'string',
        'province_desc' : 'string',
        'city_desc' : 'string',
        'place_desc' : 'string'
    }
    speciality_dtype_mapping = {
        'source_id' : 'string',
        'speciality_desc' : 'string'
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

    def normalize_column_name(self,field):
            # remove special characters and convert to lowercase
            characters_to_remove = [' ', '.', '_', '-','(',')','%','!','"',"'"]
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
    
    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            all_data = None
            try:
                if file_extension in [".xls", ".xlsx"]:
                    df_doctor = pd.read_excel(uploaded_file, sheet_name='Doctors', dtype=str)
                    df_education = pd.read_excel(uploaded_file, sheet_name='Education', dtype=str)
                    df_place = pd.read_excel(uploaded_file, sheet_name='Practice', dtype=str)
                    df_speciality = pd.read_excel(uploaded_file, sheet_name='Specialty', dtype=str)
                    all_data = {
                        'df_doctor': df_doctor,
                        'df_education': df_education,
                        'df_place' : df_place,
                        'df_speciality' : df_speciality
                    }

                else:
                    self.message_user(request, f"Unsupported file format: {file_extension}", level="error")
                    return HttpResponseRedirect(request.path)
                
                if all_data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)
                
                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(request, all_data)  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")
            
            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,
        }
        return render(request, "admin/pandas_import.html", context)
    
    def bulk_update_insert(self, request, data, model, unique_key, list_insert_columns, list_update_columns = False, doctor_data = False):
        try:
            if not list_update_columns:
                list_update_columns = list_insert_columns

            # [1] Normalize and dedupe on the unique key
            data = data.copy()
            data[unique_key] = (
                data[unique_key]
                .fillna('')
                .astype(str)
                .str.strip()
            )
            data = data[data[unique_key] != ''].copy()
            data = data.drop_duplicates(subset=[unique_key], keep='last')

            user_by = request.user if request.user.is_authenticated else None
            data = data.replace({np.nan: None})
            filter_values = list(data[unique_key].unique())
            filter_kwargs = {f"{unique_key}__in": filter_values}
            existing_pairs = model.objects.filter(**filter_kwargs).values_list(unique_key, "id")
            existing_codes = {str(k): v for (k, v) in existing_pairs}  # [2] cast DB key to str
            data["exists"] = data[unique_key].isin(set(existing_codes.keys()))
            # Split into Updates & Inserts
            existing_records = data[data["exists"]]
            new_records = data[~data["exists"]]

            # Insert new records
            with transaction.atomic():
                if not new_records.empty:
                    if doctor_data: 
                        person_id_map = dict()
                        created_person_slugs = set()

                        for row in new_records.to_dict(orient='records'):
                            # Pull names (note: source uses 'mid_name')
                            first = (row.get('first_name') or '').strip()
                            last = (row.get('last_name') or '').strip()
                            lic    = (row.get('license')    or '').strip()

                            # build the SAME key as df_doctor['person_name_ref']
                            map_key = '|'.join([first, last, lic])

                            # Build slug base from full name
                            base_name = f"{first} {last}".strip() or 'person'
                            base_slug = slugify(base_name) or 'person'

                            # Ensure unique slug (DB + current batch)
                            slug = base_slug
                            i = 2
                            while slug in created_person_slugs or Person.objects.filter(slug=slug).exists():
                                slug = f"{base_slug}-{i}"
                                i += 1
                            created_person_slugs.add(slug)

                            person = Person(
                                first_name = row.get('first_name', None),
                                middle_name = None,
                                last_name = row.get('last_name', None),
                                slug = slug,
                                status = 1,
                                cby = user_by,
                                cat = now()
                            )
                            person.save()
                            person_id_map[map_key] = person.id
                    
                        new_records['person_id'] = new_records['person_name_ref'].map(person_id_map)
                        new_records.replace({np.nan: None}, inplace=True)

                    # [4] Ensure no duplicate unique_key in the insert set
                    new_records = new_records.drop_duplicates(subset=[unique_key], keep='last')

                    list_bulk_insert = []
                    for row in new_records[list_insert_columns].to_dict(orient='records'):
                        list_bulk_insert.append(model(
                            **row,
                            status = 1,
                            cby = user_by,
                            cat = now()
                    ))
                    model.objects.bulk_create(list_bulk_insert, batch_size=1000)

                if not existing_records.empty:
                    list_bulk_update = []
                    for row in existing_records[list_update_columns].to_dict(orient='records'):
                        pk = existing_codes[str(row[unique_key])]  # [3] cast to str to match dict key
                        list_bulk_update.append(model(
                            **row,
                            id=pk,
                            status=1,
                            uby=user_by,
                            uat=now()
                        ))
                    
                    updated_obj =  model.objects.bulk_update(
                                list_bulk_update,
                                list_update_columns + ['uat', 'uby_id'],
                                batch_size = 1000
                            )
        except Exception as e:
            raise ValueError(f"Error on bulk upsert process {e}")
    
    def process_pandas_data_batch(self, request, data, batch_size=1000):
        ## PROCESS DOCTOR
        try:
            doctor_column_mapping = getattr(self, 'doctor_column_mapping', {})
            doctor_dtype_mapping = getattr(self, 'doctor_dtype_mapping', {})

            # Prepare Records
            df_doctor = data['df_doctor']
            df_doctor.rename(columns=doctor_column_mapping, inplace=True)

            # None value if column not exist
            for col in doctor_dtype_mapping.keys():
                if col not in df_doctor.columns:
                    df_doctor[col] = None

            # Validate data type
            for col, dtype in doctor_dtype_mapping.items():
                if dtype == 'date':
                    df_doctor[col] = pd.to_datetime(df_doctor[col], errors='coerce')
                else:
                    df_doctor[col] = df_doctor[col].astype(dtype)

            df_doctor['name'] = df_doctor[['prefix','first_name', 'mid_name', 'last_name', 'suffix']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
            df_doctor['code'] = df_doctor['name'] + '-' + df_doctor['license']
            df_doctor['slug'] = df_doctor['code'].apply(slugify)
            # Column reference to Person model        
            df_doctor['person_name_ref'] = (
                df_doctor[['first_name', 'last_name', 'license']]
                .fillna('')
                .agg('|'.join, axis=1)
                .str.replace(r'\s+', ' ', regex=True)
                .str.strip()
            )
            # Upsert Records
            self.bulk_update_insert(request,
                                    data = df_doctor,
                                    model = Doctor,
                                    unique_key ='code',
                                    list_insert_columns = ['prefix','suffix','license','start_year','start_month', 'private_practice', 'source_id', 'person_id',
                                                            'slug','code','name'],
                                    list_update_columns = ['prefix','suffix','license','start_year','start_month', 'private_practice', 'source_id', 'slug','code','name'],
                                    doctor_data = True
            )

            self.message_user(request, "Completed processing of Doctor data")
        
        except Exception as e:
            raise ValueError(f"Error processing of Doctor data {e}")
        
        ## Doctor Codes for reference
        doctor_codes = dict(
                    Doctor.objects.all().values_list("source_id", "id")
        )
        doctor_names = dict(
                    Doctor.objects.all().values_list("id", "name")
        )
        person_names = dict(
            Doctor.objects.all().values_list("id", "person__name")
        )
        
        ## PROCESS EDUCATION
        try:
            education_column_mapping = getattr(self, 'education_column_mapping', {})
            education_dtype_mapping = getattr(self, 'education_dtype_mapping', {})

            # Prepare Records
            df_education = data['df_education']
            df_education.rename(columns=education_column_mapping, inplace=True)

            for col, dtype in education_dtype_mapping.items():
                if dtype == 'date':
                    df_education[col] = pd.to_datetime(df_education[col], errors='coerce')
                else:
                    df_education[col] = df_education[col].astype(dtype)
            
            df_education['doctor_id'] = df_education['source_id'].map(doctor_codes)
            df_education['name'] = df_education['doctor_id'].map(doctor_names)
            df_education['person_name'] = df_education['doctor_id'].map(person_names)
            # 🚫 Drop education rows that don't map to any doctor
            df_education = df_education[df_education['doctor_id'].notna()].copy()

            # 🧼 Clean parts to avoid 'na' / '<na>' turning into identical slugs
            for c in ['person_name', 'institution', 'completed_year', 'completed_month']:
                if c in df_education.columns:
                    df_education[c] = (
                        df_education[c]
                        .fillna('')
                        .astype(str)
                        .replace({'<NA>':'', 'NaN':'', 'nan':'', 'N/A':'', 'n/a':'', 'None':''}, regex=False)
                        .str.strip()
                    )

            # 🧱 Build a stable base string for the slug (doctor + institution + year+month)
            df_education['slug_base'] = (
                df_education['doctor_id'].astype(int).astype(str) + '-' +
                df_education['person_name'] + '-' +
                df_education['institution'] + '-' +
                df_education['completed_year'] + df_education['completed_month']
            ).str.replace(r'[-\s]+', '-', regex=True).str.strip('-')

            # 🔤 Slugify + fallback if empty
            df_education['slug'] = df_education['slug_base'].apply(slugify)
            empty_mask = df_education['slug'].eq('')
            df_education.loc[empty_mask, 'slug'] = (
                'edu-' + df_education.loc[empty_mask, 'doctor_id'].astype(int).astype(str)
            )

            # 🔁 Ensure uniqueness within this batch: add -2, -3, ... for duplicates
            dup_idx = df_education.groupby('slug').cumcount()
            mask = dup_idx > 0
            df_education.loc[mask, 'slug'] = (
                df_education.loc[mask, 'slug'] + '-' + (dup_idx[mask] + 1).astype(str)
            )

            # Cleanup helper column
            df_education.drop(columns=['slug_base'], inplace=True)
            
            self.bulk_update_insert(request,
                                    data = df_education,
                                    model = DoctorEducation,
                                    unique_key ='slug',
                                    list_insert_columns = list(education_dtype_mapping.keys()) + ['slug','name', 'doctor_id'])
            self.message_user(request, "Completed processing of Doctor Education data.")
        except Exception as e:
            raise ValueError(f"Error processing of Doctor Education data {e}")
        
        ## PROCESS PLACE
        try:
            place_column_mapping = getattr(self, 'place_column_mapping', {})
            place_dtype_mapping = getattr(self, 'place_dtype_mapping', {})

            # Prepare Records
            df_place = data['df_place']
            df_place.rename(columns=place_column_mapping, inplace=True)

            for col, dtype in place_dtype_mapping.items():
                if dtype == 'date':
                    df_place[col] = pd.to_datetime(df_place[col], errors='coerce')
                else:
                    df_place[col] = df_place[col].astype(dtype)

            df_place['doctor_id'] = df_place['source_id'].map(doctor_codes)
            df_place['name'] = df_place['doctor_id'].map(doctor_names)
            df_place['person_name'] = df_place['doctor_id'].map(person_names)

            # Keep only rows that map to a doctor
            df_place = df_place[df_place['doctor_id'].notna()].copy()

            # Clean text parts to avoid 'na'/'<na>' collisions
            for c in ['person_name', 'place_desc', 'city_desc', 'province_desc']:
                if c in df_place.columns:
                    df_place[c] = (
                        df_place[c]
                        .fillna('')
                        .astype(str)
                        .replace({'<NA>':'', 'NaN':'', 'nan':'', 'N/A':'', 'n/a':'', 'None':''}, regex=False)
                        .str.strip()
                    )

            # Base for slug
            df_place['slug_base'] = (
                df_place['doctor_id'].astype(int).astype(str) + '-' +
                df_place['person_name'] + '-' +
                df_place['place_desc'] + '-' +
                df_place['city_desc'] + '-' +
                df_place['province_desc']
            ).str.replace(r'[-\s]+', '-', regex=True).str.strip('-')

            # Slugify + fallback if empty
            df_place['slug'] = df_place['slug_base'].apply(slugify)
            empty_mask = df_place['slug'].eq('')
            df_place.loc[empty_mask, 'slug'] = 'place-' + df_place.loc[empty_mask, 'doctor_id'].astype(int).astype(str)

            # Ensure uniqueness within this batch: add -2, -3... per (doctor_id, slug)
            dup_idx = df_place.groupby(['doctor_id','slug']).cumcount()
            mask = dup_idx > 0
            df_place.loc[mask, 'slug'] = df_place.loc[mask, 'slug'] + '-' + (dup_idx[mask] + 1).astype(str)

            df_place.drop(columns=['slug_base'], inplace=True)

            # Matching Province 
            province_df = pd.DataFrame(Province.objects.values('id', 'name'))
            province_df.rename(columns={'id': 'province_id', 'name':'province_name'}, inplace=True)
            province_df['province_name'] = province_df['province_name'].str.replace(' ','',regex=False).str.lower() 
            df_place['province_ref'] =  df_place['province_desc'].str.replace(' ','',regex=False).str.lower()
            df_place = df_place.merge(province_df, how='left', left_on='province_ref', right_on='province_name')

            # Matching City
            regency_df = pd.DataFrame(Regency.objects.values('id', 'name', 'province_id'))
            regency_df.rename(columns={'id': 'regency_id', 'name':'regency_name'}, inplace=True)
            regency_df['regency_name'] = regency_df['regency_name'].str.replace(' ','',regex=False).str.lower()
            df_place['regency_ref'] =  df_place['city_desc'].str.replace(' ','',regex=False).str.lower()
            df_place = df_place.merge(regency_df, how='left', left_on=['province_id','regency_ref'], right_on=['province_id','regency_name'])
            df_place['city_id'] = df_place['regency_id']

            self.bulk_update_insert(request,
                                    data = df_place,
                                    model = DoctorPlace,
                                    unique_key = 'slug',
                                    list_insert_columns = list(place_dtype_mapping.keys()) + ['slug','name', 'doctor_id', 'province_id', 'city_id']
            )

            self.message_user(request, "Completed processing of Doctor Place data.")

        except Exception as e:
            raise ValueError(f"Error processing of Doctor Place data {e}")
        
        ## PROCESS SPECIALITY
        try:
            speciality_column_mapping = getattr(self, 'speciality_column_mapping', {})
            speciality_dtype_mapping = getattr(self, 'speciality_dtype_mapping', {})

            # Prepare Records
            df_speciality = data['df_speciality']
            df_speciality.rename(columns=speciality_column_mapping, inplace=True)

            # Ensure required columns exist (mirror Doctor)
            for col in speciality_dtype_mapping.keys():
                if col not in df_speciality.columns:
                    df_speciality[col] = None

            # Dtypes        
            for col, dtype in speciality_dtype_mapping.items():
                if dtype == 'date':
                    df_speciality[col] = pd.to_datetime(df_speciality[col], errors='coerce')
                else:
                    df_speciality[col] = df_speciality[col].astype(dtype)
            
             # Map references
            df_speciality['doctor_id'] = df_speciality['source_id'].map(doctor_codes)
            df_speciality['name'] = df_speciality['doctor_id'].map(doctor_names)
            df_speciality['person_name'] = df_speciality['doctor_id'].map(person_names)

            # Keep rows that map to a doctor
            df_speciality = df_speciality[df_speciality['doctor_id'].notna()].copy()

            # Clean text parts
            for c in ['person_name', 'speciality_desc']:
                if c in df_speciality.columns:
                    df_speciality[c] = (
                        df_speciality[c]
                        .fillna('')
                        .astype(str)
                        .replace({'<NA>':'', 'NaN':'', 'nan':'', 'N/A':'', 'n/a':'', 'None':''}, regex=False)
                        .str.strip()
                    )

            # 🔑 Build speciality_ref (needed for merge)
            df_speciality['speciality_ref'] = (
                df_speciality['speciality_desc']
                .fillna('')
                .astype(str)
                .str.replace(' ', '', regex=False)
                .str.lower()
            )

            # Slug base + uniqueness
            df_speciality['slug_base'] = (
                df_speciality['doctor_id'].astype(int).astype(str) + '-' +
                df_speciality['person_name'] + '-' +
                df_speciality['speciality_desc']
            ).str.replace(r'[-\s]+', '-', regex=True).str.strip('-')

            df_speciality['slug'] = df_speciality['slug_base'].apply(slugify)
            empty_mask = df_speciality['slug'].eq('')
            df_speciality.loc[empty_mask, 'slug'] = 'spec-' + df_speciality.loc[empty_mask, 'doctor_id'].astype(int).astype(str)

            dup_idx = df_speciality.groupby(['doctor_id','slug']).cumcount()
            mask = dup_idx > 0
            df_speciality.loc[mask, 'slug'] = df_speciality.loc[mask, 'slug'] + '-' + (dup_idx[mask] + 1).astype(str)

            df_speciality.drop(columns=['slug_base'], inplace=True)

             # Match to Specialization master
            specialization_df = pd.DataFrame(Specialization.objects.values('id', 'name'))
            specialization_df.rename(columns={'id': 'speciality_id', 'name':'specialization_name'}, inplace=True)
            specialization_df['specialization_name'] = specialization_df['specialization_name'].str.replace(' ','',regex=False).str.lower() 

            df_speciality = df_speciality.merge(
                specialization_df,
                how='left',
                left_on='speciality_ref',
                right_on='specialization_name'
            )

            self.bulk_update_insert(
                request,
                data = df_speciality, 
                model = DoctorSpeciality,
                unique_key = 'slug', 
                list_insert_columns = list(speciality_dtype_mapping.keys()) + ['slug','name', 'doctor_id', 'speciality_id']
            )

            self.message_user(request, "Completed processing of Doctor Speciality data.")
        except Exception as e:
            raise ValueError(f"Error processing of Doctor Speciality data {e}")

@admin.register(DoctorEducation)
class DoctorEducationAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("doctor", "institution", "completed_year", "completed_month") + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("institution",)
    search_fields = ("doctor__name", "institution", "completed_year", "completed_month",)
    list_per_page = 1000
    has_pandas_import = True
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('doctor', 'institution', 'completed_year', 'completed_month', 'name',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug'),
            'description': 'System related information.',
        }),
    )

@admin.register(DoctorPlace)
class DoctorPlaceAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("doctor", "province_desc", "province",  "city_desc", "city", "place_desc", "customer",) + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("place_desc",)
    search_fields = ("doctor__first_name", "doctor__mid_name", "doctor__last_name", "province_desc", "province__name", "city_desc", "regency__name", "place_desc", "customer__name",)
    list_per_page = 1000
    has_pandas_import = True
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('doctor', 'province_desc', 'province', 'city_desc', 'city', 'place_desc', 'customer', 'name',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug'),
            'description': 'System related information.',
        }),
    )

@admin.register(DoctorSpeciality)
class DoctorSpecialityAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("doctor", "speciality_desc","speciality__name") + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("speciality_desc",)
    search_fields = ("doctor__first_name", "doctor__mid_name", "doctor__last_name", "speciality_desc", "speciality__name",)
    list_per_page = 1000
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('name', 'doctor', 'speciality_desc', 'speciality',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )
