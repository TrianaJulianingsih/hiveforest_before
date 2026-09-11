from django.contrib import admin
from apps.base.models import Province, Regency, Person
from apps.base.models import CompanyOwnership, CompanyOwner
from apps.crm.models.hospital import Association, HospitalType, HospitalClass, Hospital, HospitalBed, HospitalService, HospitalProfessional
from apps.crm.models.hcps import Specialization, Doctor, DoctorEducation, DoctorPlace, DoctorSpeciality
from apps.crm.models.kpdm import KPDMContact, KPDMCustomer
from apps.sales.models.customer import Customer
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from django.forms import ModelChoiceField
# Pandas
from django import forms
import pandas as pd
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.timezone import now
import numpy as np ## new
import os ## new
from django.utils.text import slugify
from django.db import transaction
import traceback

class CsvImportForm(forms.Form):
     csv_file = forms.FileField()

# CRM | KMPDM
# __________________________

@admin.register(KPDMContact)
class KPDMContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = ('name', 'person',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('person', 'name', 'description', 'remark')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug', 'cat', 'cby', 'uat', 'uby', 'dat', 'dby', 'deleted'),
            'description': 'System related information.',
        }),
    )

@admin.register(KPDMCustomer)
class KPDMCustomerAdmin(admin.ModelAdmin):
    list_display = ['kpdm', 'customer', 'assigned_by', 'assigned_at']
    autocomplete_fields = ['kpdm', 'customer']
    search_fields = ['kpdm__person__name', 'customer__name', 'customer__code']
    ordering = ['kpdm__person__name']
    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # custom filtering here could break it
        return queryset, use_distinct


    class Media:
        css = {
            'all': ('static/admin/css/widget.css',)  # load custom css
        }
    #def get_search_results(self, request, queryset, search_term):
    #    if "autocomplete" in request.path:  # Detect if request is from an autocomplete field
    #        queryset = queryset.filter(name__icontains=search_term)#

    #    return super().get_search_results(request, queryset, search_term)
    
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('kpdm', 'customer')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug',),
            'description': 'System related information.',
        }),
    )

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

            user_by = request.user if request.user.is_authenticated else None
            data = data.replace({np.nan: None})
            filter_kwargs = {f"{unique_key}__in": data[unique_key]}
            existing_codes = dict(
                                    model.objects.filter(**filter_kwargs).values_list(unique_key, "id")
                                )

            data["exists"] = data[unique_key].isin(set(existing_codes.keys()))
            # Split into Updates & Inserts
            existing_records = data[data["exists"]]
            new_records = data[~data["exists"]]

            # Insert new records
            with transaction.atomic():
                if not new_records.empty:
                    if doctor_data: 
                        person_id_map = dict()
                        for row in new_records.to_dict(orient='records'):
                            person = Person(
                                first_name = row.get('first_name', None),
                                middle_name = row.get('middle_name', None),
                                last_name = row.get('last_name', None),
                                status = 1,
                                cby = user_by,
                                cat = now()
                            )
                            person.save()
                            person_id_map[person.name] = person.id
                    
                        new_records['person_id'] = new_records['person_name_ref'].map(person_id_map)
                        new_records.replace({np.nan: None})

                    list_bulk_insert = []
                    for row in new_records[list_insert_columns].to_dict(orient='records'):
                        list_bulk_insert.append(model(
                            **row,
                            status = 1,
                            cby = user_by,
                            cat = now()
                    ))

                    created_obj = model.objects.bulk_create(
                                list_bulk_insert,
                                batch_size = 1000,
                            )

                if not existing_records.empty:
                    list_bulk_update = [
                                model( **row, 
                                        id = existing_codes.get(row[unique_key]),
                                        status = 1,
                                        uby = user_by,
                                        uat = now()
                                        ) for row in existing_records[list_update_columns].to_dict(orient='records')]
                    
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
            df_doctor['person_name_ref'] = df_doctor[['first_name', 'mid_name', 'last_name']] \
                            .apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
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
            df_education['slug'] = (df_education['doctor_id'].astype(str) +'-'+ \
                                    df_education['person_name'] + '-' + \
                                    df_education['institution'] + '-' + \
                                    df_education['completed_year'].astype(str) + df_education['completed_month'].astype(str)
                                    ).apply(slugify)
            
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
            df_place['slug'] = (df_place['doctor_id'].astype(str) + '-' + \
                                df_place['person_name'] + '-' + \
                                df_place['place_desc'] + '-' + \
                                df_place['city_desc'] + '-' + \
                                df_place['province_desc']
                                ).apply(slugify)
            
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

            for col, dtype in speciality_dtype_mapping.items():
                if dtype == 'date':
                    df_speciality[col] = pd.to_datetime(df_speciality[col], errors='coerce')
                else:
                    df_speciality[col] = df_speciality[col].astype(dtype)
            
            df_speciality['doctor_id'] = df_speciality['source_id'].map(doctor_codes)
            df_speciality['name'] = df_speciality['doctor_id'].map(doctor_names)
            df_speciality['person_name'] = df_speciality['doctor_id'].map(person_names)
            df_speciality['slug'] = (df_speciality['doctor_id'].astype(str) +'-'+ \
                                    df_speciality['person_name'] +'-'+ \
                                    df_speciality['speciality_desc']
                                    ).apply(slugify)
            df_speciality['speciality_ref'] = df_speciality['speciality_desc'].str.replace(' ','').str.lower()

            specialization_df = pd.DataFrame(Specialization.objects.values('id', 'name'))
            specialization_df.rename(columns={'id': 'speciality_id', 'name':'specialization_name'}, inplace=True)
            specialization_df['specialization_name'] = specialization_df['specialization_name'].str.replace(' ','',regex=False).str.lower() 

            df_speciality = df_speciality.merge(specialization_df, how='left', left_on='speciality_ref', right_on='specialization_name')

            self.bulk_update_insert(request,
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
    search_fields = ("doctor__first_name", "doctor__mid_name", "doctor__last_name", "institution", "completed_year", "completed_month",)
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

@admin.register(Specialization)
class SpecializationAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "title",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname", "title",)
    list_per_page = 1000
    has_pandas_import = True

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
            title =  handle_blank(row['title'])

            Specialization.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                title=title,
                status=row['status']
            )

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
        ('raw_kode', 'raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    search_fields = BaseModelAdmin.search_fields + (
        'code', 'name', 'raw_kode', 'raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class', 'raw_phone', 'raw_blustat', 'raw_onwership',
        'raw_director', 'raw_landarea', 'raw_buildingarea', 'raw_lastupdate', 'initial', 'shortname', 'alias', 'formername', 'building', 'complex',
        'street', 'postcode', 'longitude', 'latitude'
        )
    list_filter = ('raw_type',) # Add filter by group
    list_per_page = 1000
    has_pandas_import = True

    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'raw_kode', 'raw_province', 'raw_city', 'raw_address', 'raw_type', 'raw_class', 'raw_phone', 'raw_blustat',
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
        'raw_kode' : 'raw_kode', 'raw_name' : 'name', 'raw_province' : 'raw_province', 'raw_city' : 'raw_city', 'raw_address' : 'raw_address',
        'raw_phone' : 'raw_phone', 'raw_type' : 'raw_type', 'raw_class': 'raw_class', 'raw_blustat' : 'raw_blustat', 'raw_ownership' : 'raw_ownership',
        'raw_director' : 'raw_director', 'raw_landarea' : 'raw_landarea', 'raw_buildingarea' : 'raw_buildingarea', 'raw_lastupdate' : 'raw_lastupdate',
        'initial' : 'initial', 'shortname' : 'shortname', 'alias' : 'alias', 'formername' : 'formername', 'building' : 'building', 'complex' : 'complex',
        'street' : 'street', 'postcode' : 'postcode', 'longitude' : 'longitude', 'latitude' : 'latitude', 'hospitaltype' : 'hospitaltype',
        'hospitalclass' : 'hospitalclass', 'ownership' : 'ownership', 'owner' : 'owner', 'village' : 'village', 'district': 'district', 'regency' : 'regency',
        'province' : 'province', 'customer' : 'customer'
    }

    hospital_dtype_mapping = {
        'name' : 'string', 'raw_kode' : 'string', 'raw_province' : 'string', 'raw_city' : 'string', 'raw_address' : 'string', 'raw_phone' : 'string',
        'raw_type' : 'string', 'raw_class': 'string', 'raw_blustat' : 'string', 'raw_ownership' : 'string', 'raw_director' : 'string', 'raw_landarea' : 'float',
        'raw_buildingarea' : 'float', 'raw_lastupdate' : 'date', 'initial' : 'string', 'shortname' : 'string', 'alias' : 'string', 'formername' : 'string',
        'building' : 'string', 'complex' : 'string', 'street' : 'string', 'postcode' : 'string', 'longitude' : 'float', 'latitude' : 'float',
        'hospitaltype' : 'string', 'hospitalclass' : 'string', 'ownership' : 'string', 'owner' : 'string', 'village' : 'Int64', 'district': 'Int64',
        'regency' : 'string', 'province' : 'string', 'customer' : 'Int64'
    }

    bed_column_mapping = {
        'raw_kode' : 'raw_kode', 'raw_bedno' : 'raw_bedno', 'raw_bedclass' : 'raw_bedclass', 'raw_beds' : 'raw_beds'
    }

    bed_dtype_mapping = {
        'raw_kode' : 'string', 'raw_bedno' : 'Int64', 'raw_bedclass' : 'string', 'raw_beds' : 'Int64'
    }

    service_column_mapping = {
        'raw_kode' : 'raw_kode', 'raw_serviceno' : 'raw_serviceno', 'raw_service' : 'raw_service'
    }

    service_dtype_mapping = {
        'raw_kode' : 'string', 'raw_serviceno' : 'Int64', 'raw_service' : 'string'
    }

    professional_column_mapping = {
        'raw_kode' : 'raw_kode', 'raw_profno' : 'raw_profno', 'raw_profgroup' : 'raw_profgroup', 'raw_professional' : 'raw_professional', 'raw_profs' : 'raw_profs'
    }

    professional_dtype_mapping = {
        'raw_kode' : 'string', 'raw_profno' : 'Int64', 'raw_profgroup' : 'string', 'raw_professional' : 'string', 'raw_profs' : 'Int64'
    }

    def changelist_view(self, request, extra_context=None):
            opts = self.model._meta
            pandas_import_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_pandas_import")
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

    def get_foreign_key_mappings(self):
        """
        Create mappings for foreign key fields from code to ID
        """
        mappings = {}
        
        # Hospital Type mapping (code -> id)
        if hasattr(self.model, 'hospitaltype'):
            try:
                # Assuming your HospitalType model has a 'code' field
                mappings['hospitaltype'] = dict(
                    HospitalType.objects.all().values_list('code', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create hospitaltype mapping: {e}")
        
        # Hospital Class mapping (code -> id) 
        if hasattr(self.model, 'hospitalclass'):
            try:
                mappings['hospitalclass'] = dict(
                    HospitalClass.objects.all().values_list('name', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create hospitalclass mapping: {e}")
        
        # Ownership mapping (code -> id)
        if hasattr(self.model, 'ownership'):
            try:
                mappings['ownership'] = dict(
                    CompanyOwnership.objects.all().values_list('code', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create ownership mapping: {e}")

        # Owner mapping (code -> id)
        if hasattr(self.model, 'owner'):
            try:
                mappings['owner'] = dict(
                    CompanyOwnership.objects.all().values_list('code', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create owner mapping: {e}")

        # Regency mapping (code -> id)
        if hasattr(self.model, 'regency'):
            try:
                mappings['regency'] = dict(
                    Regency.objects.all().values_list('code', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create regency mapping: {e}")

        # Prvince mapping (code -> id)
        if hasattr(self.model, 'province'):
            try:
                mappings['province'] = dict(
                    Province.objects.all().values_list('code', 'id')
                )
            except Exception as e:
                print(f"Warning: Could not create province mapping: {e}")

        # Add more foreign key mappings as needed
        
        return mappings

    def process_foreign_key_lookups(self, df, foreign_key_mappings):
        """
        Convert foreign key codes to IDs in the DataFrame
        """
        for field_name, code_to_id_mapping in foreign_key_mappings.items():
            if field_name in df.columns:
                # Create a new column with '_id' suffix for the foreign key
                fk_field = f"{field_name}_id"
                
                # Map codes to IDs
                df[fk_field] = df[field_name].map(code_to_id_mapping)
                
                # Optional: Log missing mappings
                missing_codes = df[df[field_name].notna() & df[fk_field].isna()][field_name].unique()
                if len(missing_codes) > 0:
                    print(f"Warning: Could not find {field_name} IDs for codes: {missing_codes}")
        
        return df

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
                    df_hospital = pd.read_excel(uploaded_file, sheet_name='Hospital', dtype=str)
                    df_bed = pd.read_excel(uploaded_file, sheet_name='Bed', dtype=str)
                    df_service = pd.read_excel(uploaded_file, sheet_name='Service', dtype=str)
                    df_professional = pd.read_excel(uploaded_file, sheet_name='Professional', dtype=str)
                    all_data = {
                        'df_hospital': df_hospital,
                        'df_bed': df_bed,
                        'df_service' : df_service,
                        'df_professional' : df_professional
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
                traceback.print_exc()
                #self.message_user(request, f"Error importing data: {e}", level="error")
                # More informative message for Django Admin
                self.message_user(
                    request,
                    f"Error importing data: {e}\nType: {type(e).__name__}",
                    level="error"
                )
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,
        }
        return render(request, "admin/pandas_import.html", context)

    def bulk_update_insert(self, request, data, model, unique_key, list_insert_columns, list_update_columns = False, hospital_data = False):
        try:
            if not list_update_columns:
                list_update_columns = list_insert_columns

            user_by = request.user if request.user.is_authenticated else None
            data = data.replace({np.nan: None})
            filter_kwargs = {f"{unique_key}__in": data[unique_key]}
            existing_codes = dict(
                                    model.objects.filter(**filter_kwargs).values_list(unique_key, "id")
                                )

            data["exists"] = data[unique_key].isin(set(existing_codes.keys()))
            # Split into Updates & Inserts
            existing_records = data[data["exists"]]
            new_records = data[~data["exists"]]

            # Insert new records
            with transaction.atomic():
                if not new_records.empty:
                    list_bulk_insert = []
                    for row in new_records[list_insert_columns].to_dict(orient='records'):
                        list_bulk_insert.append(model(
                            **row,
                            status = 1,
                            cby = user_by,
                            cat = now()
                    ))

                    created_obj = model.objects.bulk_create(
                                list_bulk_insert,
                                batch_size = 1000,
                            )

                if not existing_records.empty:
                    list_bulk_update = [
                        model( **row, 
                                id = existing_codes.get(row[unique_key]),
                                status = 1,
                                uby = user_by,
                                uat = now()
                                ) for row in existing_records[list_update_columns].to_dict(orient='records')]
                    
                    updated_obj =  model.objects.bulk_update(
                        list_bulk_update,
                        list_update_columns + ['uat', 'uby_id'],
                        batch_size = 1000
                    )
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

            # Validate data type
            # for col, dtype in hospital_dtype_mapping.items():
            #     if dtype == 'date':
            #         df_hospital[col] = pd.to_datetime(df_hospital[col], errors='coerce')
            #     else:
            #         df_hospital[col] = df_hospital[col].astype(dtype)
            for col, dtype in hospital_dtype_mapping.items():
                try:
                    if dtype == 'date':
                        df_hospital[col] = pd.to_datetime(df_hospital[col], errors='coerce')
                    else:
                        df_hospital[col] = df_hospital[col].astype(dtype)
                except Exception as e:
                    import traceback
                    traceback.print_exc()  # to server log
                    self.message_user(
                        request,
                        f"Error converting column '{col}': {e} | Type: {type(e).__name__}",
                        level="error"
                    )
                    return HttpResponseRedirect(request.path)

            df_hospital['name'] = df_hospital[['name','raw_kode']].apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
            df_hospital['slug'] = df_hospital['name'].apply(slugify)

            # 🆕 NEW: Handle foreign key lookups
            foreign_key_mappings = self.get_foreign_key_mappings()
            df_hospital = self.process_foreign_key_lookups(df_hospital, foreign_key_mappings)

            # Update the column lists to include the new _id fields for Django ForeignKeys
            base_columns = ['raw_kode','name','raw_province','raw_city','raw_address', 'raw_phone', 'raw_type', 
                        'raw_class', 'raw_blustat', 'raw_ownership','raw_director','raw_landarea', 
                        'raw_buildingarea', 'raw_lastupdate', 'initial', 'shortname', 'alias', 'formername',
                        'building', 'complex', 'street', 'postcode', 'longitude','latitude', 'slug']

            # Add foreign key ID fields that were created from code lookups
            # These match Django's automatic naming: hospitaltype → hospitaltype_id
            fk_from_codes = []
            for fk_field in ['hospitaltype_id', 'hospitalclass_id', 'ownership_id', 'owner_id', 'regency_id', 'province_id']:
                if fk_field in df_hospital.columns:
                    fk_from_codes.append(fk_field)

            # Add direct ID fields - these are also ForeignKeys but you provide IDs directly
            # Django naming: village → village_id, district → district_id, customer → customer_id
            direct_id_fields = []
            for base_field in ['village', 'district', 'customer']:
                id_field = f"{base_field}_id"
                if base_field in df_hospital.columns:
                    # Rename the column to match Django's naming convention
                    df_hospital.rename(columns={base_field: id_field}, inplace=True)
                    direct_id_fields.append(id_field)
            
            all_columns = base_columns + fk_from_codes + direct_id_fields

            # Upsert Records
            self.bulk_update_insert(request,
                data = df_hospital,
                model = Hospital,
                unique_key ='raw_kode',
                list_insert_columns = all_columns,
                list_update_columns = all_columns,
                hospital_data = True
            )

            self.message_user(request, "Completed processing of Hospital data")
        
        except Exception as e:
            raise ValueError(f"Error processing of Hospital data {e}")
        
        ## Doctor Codes for reference
        hospital_codes = dict(
                    Hospital.objects.all().values_list("raw_kode", "id")
        )
        hospital_names = dict(
                    Hospital.objects.all().values_list("id", "name")
        )
        
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
            
            df_bed['hospital_id'] = df_bed['raw_kode'].map(hospital_codes)
            df_bed['name'] = df_bed['hospital_id'].map(hospital_names)
            df_bed['slug'] = (df_bed['hospital_id'].astype(str) +'-'+ \
                df_bed['raw_bedno'].astype(str) + '-' + df_bed['raw_bedclass']).apply(slugify)
            
            self.bulk_update_insert(request, data = df_bed, model = HospitalBed, unique_key ='slug',
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

            df_service['hospital_id'] = df_service['raw_kode'].map(hospital_codes)
            df_service['name'] = df_service['hospital_id'].map(hospital_names)
            df_service['slug'] = (df_service['hospital_id'].astype(str) + '-' + \
                df_service['raw_serviceno'].astype(str) + '-' + df_service['raw_service']).apply(slugify)
            
            self.bulk_update_insert(request, data = df_service, model = HospitalService, unique_key = 'slug',
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
            
            df_professional['hospital_id'] = df_professional['raw_kode'].map(hospital_codes)
            df_professional['name'] = df_professional['hospital_id'].map(hospital_names)
            df_professional['slug'] = (df_professional['hospital_id'].astype(str) +'-'+ \
                df_professional['raw_profno'].astype(str) + '-' + df_professional['raw_professional']).apply(slugify)

            self.bulk_update_insert(request, data = df_professional, model = HospitalProfessional, unique_key = 'slug', 
                list_insert_columns = list(professional_dtype_mapping.keys()) + ['slug','name', 'hospital_id'])
            self.message_user(request, "Completed processing of Hospital Professional data.")
        except Exception as e:
            raise ValueError(f"Error processing of Hospital Professional data {e}")

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

@admin.register(Association)
class AssociationAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True

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

            Association.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )


