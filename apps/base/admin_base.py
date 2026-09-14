from django.contrib import admin, messages
from apps.base.filters import DeletedListFilter, StatusListFilter
from apps.base.admin_utils import delete_item
from django.urls import path, reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
import pandas as pd
import dbfread
from dbfread import DBF
import csv
import io
import os
import tempfile
import chardet
from django.forms import Textarea, TextInput


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: BaseModelAdmin                                      ║
# ║  Type: ModelAdmin                                          ║
# ║  Purpose: Admin site configuration                         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\admin_base.py                             ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class BaseModelAdmin(admin.ModelAdmin):
    list_display_id = ("id",)
    list_display_name = ("name",)
    list_display_info = (
        "description",
        "remark",
    )
    list_display_last = (
        "status",
        "slug",
        "cat",
        "cby",
        "uat",
        "uby",
        "dat",
        "dby",
        "deleted",
    )
    list_display_links = ("name",)
    fields_name = ("name",)
    fields_info = (
        "description",
        "remark",
    )
    fields_last = (
        "status",
        "slug",
        "uat",
        "dat",
        "deleted",
    )
    fields = fields_name + fields_info + fields_last
    search_fields = ("name", "description", "remark")
    readonly_fields = ("cat", "cby", "uat", "uby", "dat", "dby", "deleted")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )
    date_hierarchy = "cat"
    actions_on_top = True
    actions_on_bottom = True
    radio_fields = {"status": admin.VERTICAL}
    save_on_top = True

    delete_view = delete_item(admin.ModelAdmin)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "name" in form.base_fields:
            form.base_fields["name"].widget = TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "style": "width: 300px;",
                    "placeholder": "Full name",
                }
            )
        if "description" in form.base_fields:
            form.base_fields["description"].widget = Textarea(
                attrs={
                    "rows": 2,
                    "class": "form-control form-control-sm",
                    "style": "width: 300px; height:90px;",
                    "placeholder": "Short description",
                }
            )
        return form

    def changelist_view(self, request, extra_context=None):
        try:
            from apps.base.services.system_log_service import SystemLogService
            from apps.base.models.system_log import LogAction
            
            SystemLogService.log(
                request=request,
                action=LogAction.READ,
                module=self.model._meta.app_label.title(),
                feature=self.model._meta.verbose_name_plural.title(),
                description=f"Accessed {self.model._meta.verbose_name_plural.title()} admin list view.",
                status="SUCCESS",
                log_type="SYSTEM"
            )
        except Exception:
            pass
        return super().changelist_view(request, extra_context=extra_context)


class PandasImportMixin:
    def _read_csv_file(self, uploaded_file, dtype_mapping):
        raw_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        detected_encoding = chardet.detect(raw_bytes).get("encoding") or "utf-8-sig"
        text = None
        for encoding in [detected_encoding, "utf-8-sig", "utf-8", "latin-1"]:
            try:
                text = raw_bytes.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            raise ValueError("Unable to decode CSV file.")

        lines = text.splitlines()
        first_line = lines[0] if lines else ""
        delimiters = [",", ";", "\t", "|"]
        expected_count = len(dtype_mapping) if dtype_mapping else 0
        candidate_separators = []

        try:
            sniffed_separator = (
                csv.Sniffer()
                .sniff(text[:4096], delimiters="".join(delimiters))
                .delimiter
            )
            candidate_separators.append(sniffed_separator)
        except csv.Error:
            pass

        if first_line:
            ordered_delimiters = sorted(
                delimiters,
                key=lambda delimiter: (
                    abs(len(first_line.split(delimiter)) - expected_count)
                    if expected_count
                    else -len(first_line.split(delimiter))
                ),
            )
            for delimiter in ordered_delimiters:
                if delimiter not in candidate_separators:
                    candidate_separators.append(delimiter)

        candidate_separators.append(None)

        errors = []
        for separator in candidate_separators:
            try:
                data = pd.read_csv(
                    io.StringIO(text),
                    sep=separator,
                    engine="python",
                    skipinitialspace=True,
                    keep_default_na=False,
                )

                parsed_columns = len(data.columns)
                if expected_count and parsed_columns == 1 and expected_count > 1:
                    raise ValueError(
                        f"Detected only 1 column using separator {separator!r}."
                    )

                return data
            except Exception as exc:
                errors.append(f"sep={separator!r}: {exc}")

        raise ValueError("Unable to parse CSV file. " + " | ".join(errors[:3]))

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()

            try:
                data = None
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    # # Detect separator (comma or semicolon)
                    # first_bytes = uploaded_file.read(1024)  # Read first 1024 bytes
                    # separator = "," if b"," in first_bytes else ";"
                    # uploaded_file.seek(0)  # Reset file pointer
                    # data = pd.read_csv(uploaded_file, sep=separator, dtype=dtype_mapping)
                    data = self._read_csv_file(uploaded_file, dtype_mapping)

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=dtype_mapping)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(
                                uploaded_file.read()
                            )  # Write the uploaded file content
                            temp_file_path = (
                                temp_file.name
                            )  # Get the temporary file path

                        # ✅ Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            # ✅ Read the DBF file from the temporary path
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )  # Adjust encoding if needed
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(
                            iter(dbf_table)
                        )  # Convert DBF to Pandas DataFrame
                        print(f"✅ Successfully loaded DBF with {len(data)} records.")

                        # ✅ Cleanup: Remove the temporary file after reading
                        os.remove(temp_file_path)
                        print(f"✅ DBF Columns: {data.columns.tolist()}")
                        print(f"✅ First 5 rows:\n{data.head()}")

                    except Exception as e:
                        print(f"❌ Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"🚀 DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"❌ ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data.columns = data.columns.str.upper().str.strip()
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    self.message_user(
                        request,
                        f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                # ✅ Keep only expected columns
                data = data[expected_columns]

                # Process and validate data
                try:
                    import inspect
                    sig = inspect.signature(self.process_pandas_data)
                    if len(sig.parameters) == 1:
                        response = self.process_pandas_data(data) or {}
                    else:
                        response = self.process_pandas_data(request, data) or {}

                    # Log the successful import
                    try:
                        from apps.base.services.system_log_service import SystemLogService
                        from apps.base.models.system_log import LogAction
                        SystemLogService.log_bulk(
                            action=LogAction.BULK_CREATE,
                            model=self.model,
                            affected_count=len(data),
                            request=request,
                            module=self.model._meta.app_label.title(),
                            feature=f"{self.model._meta.verbose_name} Import",
                            description=f"Successfully imported {len(data)} records via file upload ({uploaded_file.name})."
                        )
                    except Exception:
                        pass
                except Exception as e:
                    # Log the failed import
                    try:
                        from apps.base.services.system_log_service import SystemLogService
                        SystemLogService.error(
                            request=request,
                            module=self.model._meta.app_label.title(),
                            feature=f"{self.model._meta.verbose_name} Import",
                            error=e,
                            description=f"Failed to import records via file upload ({uploaded_file.name}): {str(e)}"
                        )
                    except Exception:
                        pass
                    self.message_user(
                        request, f"Error processing data: {e}", level="error"
                    )
                    return HttpResponseRedirect(request.path)

                if response.get("download_csv"):  # ✅ Ensure we check for CSV trigger
                    return JsonResponse({"download_csv": True})

                if not list(messages.get_messages(request)):
                    self.message_user(request, "Data imported successfully.")

                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {"opts": opts, "app_label": opts.app_label}
        return render(request, "admin/pandas_import.html", context)

    def process_pandas_data(self, request, data):
        """
        Override this method in your admin class to process the imported data.
        """
        # raise NotImplementedError("You must implement the `process_pandas_data` method.")
        return {"download_csv": False}  # Ensure it returns a dictionary

    def get_urls(self):
        """
        Add the custom URL for the pandas import functionality.
        """
        opts = self.model._meta
        custom_urls = [
            path(
                "pandas-import/",
                self.admin_site.admin_view(self.pandas_import),
                name=f"{opts.app_label}_{opts.model_name}_pandas_import",
            ),
        ]
        return custom_urls + super().get_urls()
