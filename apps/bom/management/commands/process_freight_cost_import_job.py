import os
import csv
import io

import chardet
import dbfread
import pandas as pd
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from openpyxl import load_workbook

from apps.bom.admin import FreightCostDetailAdmin
from apps.bom.models import FreightCostDetail, FreightCostImportJob


class _LocalUploadFile:
    def __init__(self, file_path, original_filename):
        self.file = open(file_path, "rb")
        self.name = original_filename

    def read(self, *args, **kwargs):
        return self.file.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.file.seek(*args, **kwargs)

    def close(self):
        self.file.close()


class _BackgroundRequest:
    def __init__(self, user):
        self.user = user
        self.session = {}


class Command(BaseCommand):
    help = "Process a background Freight Cost import job."

    def _build_encoding_candidates(self, detected_encoding=None):
        normalized_detected = (detected_encoding or "").strip().lower()
        ordered_encodings = []

        if normalized_detected and normalized_detected not in {"ascii", "us-ascii"}:
            ordered_encodings.append(detected_encoding)

        for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            if encoding not in ordered_encodings:
                ordered_encodings.append(encoding)

        if normalized_detected in {"ascii", "us-ascii"}:
            ordered_encodings.append(detected_encoding)

        return ordered_encodings

    def _detect_csv_config(self, uploaded_file, dtype_mapping):
        uploaded_file.seek(0)
        sample_bytes = uploaded_file.read(262144)
        uploaded_file.seek(0)

        detected_encoding = chardet.detect(sample_bytes).get("encoding") or "utf-8-sig"
        sample_text = None
        encoding_candidates = self._build_encoding_candidates(detected_encoding)
        used_encoding = None
        for encoding in encoding_candidates:
            try:
                sample_text = sample_bytes.decode(encoding)
                used_encoding = encoding
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if sample_text is None:
            raise CommandError("Unable to decode CSV file.")

        lines = sample_text.splitlines()
        first_line = lines[0] if lines else ""
        delimiters = [",", ";", "\t", "|"]
        expected_count = len(dtype_mapping) if dtype_mapping else 0
        candidate_separators = []

        try:
            sniffed_separator = (
                csv.Sniffer()
                .sniff(sample_text[:4096], delimiters="".join(delimiters))
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
                preview = pd.read_csv(
                    io.StringIO(sample_text),
                    sep=separator,
                    engine="python",
                    skipinitialspace=True,
                    keep_default_na=False,
                    nrows=50,
                )
                parsed_columns = len(preview.columns)
                if expected_count and parsed_columns == 1 and expected_count > 1:
                    raise ValueError(
                        f"Detected only 1 column using separator {separator!r}."
                    )

                retry_encodings = [used_encoding]
                for encoding in encoding_candidates:
                    if encoding not in retry_encodings:
                        retry_encodings.append(encoding)
                return {"encodings": retry_encodings, "separator": separator}
            except Exception as exc:
                errors.append(f"sep={separator!r}: {exc}")

        raise CommandError("Unable to parse CSV file. " + " | ".join(errors[:3]))

    def _get_csv_dtype_mapping(self, dtype_mapping):
        csv_dtype_mapping = {}

        for column_name, dtype_value in (dtype_mapping or {}).items():
            normalized_dtype = str(dtype_value).strip().lower()
            if any(
                token in normalized_dtype
                for token in ["int", "float", "double", "decimal", "number"]
            ):
                csv_dtype_mapping[column_name] = "string"
            else:
                csv_dtype_mapping[column_name] = dtype_value

        return csv_dtype_mapping

    def _get_csv_read_options(self, dtype_mapping, csv_config, *, chunk_size=None):
        separator = csv_config["separator"]
        read_options = {
            "sep": separator,
            "skipinitialspace": True,
            "keep_default_na": False,
            "na_filter": False,
            "dtype": self._get_csv_dtype_mapping(dtype_mapping) or None,
        }

        read_options["engine"] = "python" if separator is None else "c"

        if chunk_size is not None:
            read_options["chunksize"] = chunk_size

        return read_options

    def _iter_csv_file_chunks(self, uploaded_file, dtype_mapping, chunk_size):
        csv_config = self._detect_csv_config(uploaded_file, dtype_mapping)
        errors = []
        read_options = self._get_csv_read_options(
            dtype_mapping,
            csv_config,
            chunk_size=chunk_size,
        )

        for encoding in csv_config["encodings"]:
            uploaded_file.seek(0)
            text_stream = io.TextIOWrapper(uploaded_file.file, encoding=encoding, newline="")
            try:
                row_offset = 0
                for chunk in pd.read_csv(text_stream, **read_options):
                    chunk.index = range(row_offset, row_offset + len(chunk.index))
                    row_offset += len(chunk.index)
                    yield chunk
                return
            except UnicodeDecodeError as exc:
                errors.append(f"encoding={encoding!r}: {exc}")
            finally:
                text_stream.detach()
                uploaded_file.seek(0)

        raise CommandError("Unable to decode CSV file. " + " | ".join(errors[:3]))

    def _iter_xlsx_file_chunks(self, uploaded_file, chunk_size):
        uploaded_file.seek(0)
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
        worksheet = workbook.active
        try:
            rows = worksheet.iter_rows(values_only=True)
            header_row = next(rows, None)
            if header_row is None:
                return

            headers = [str(value).upper().strip() if value is not None else "" for value in header_row]
            pending_rows = []
            pending_indices = []

            for excel_row_number, row in enumerate(rows, start=2):
                pending_rows.append(
                    {
                        headers[index]: row[index] if index < len(row) else None
                        for index in range(len(headers))
                    }
                )
                pending_indices.append(excel_row_number - 2)

                if len(pending_rows) >= chunk_size:
                    chunk = pd.DataFrame(pending_rows)
                    chunk.index = pending_indices
                    yield chunk
                    pending_rows = []
                    pending_indices = []

            if pending_rows:
                chunk = pd.DataFrame(pending_rows)
                chunk.index = pending_indices
                yield chunk
        finally:
            workbook.close()
            uploaded_file.seek(0)

    def _normalize_import_dataframe(self, admin_instance, request, data):
        if hasattr(admin_instance, "_normalize_import_dataframe"):
            return admin_instance._normalize_import_dataframe(
                request,
                data,
                admin_instance.dtype_mapping,
                admin_instance.column_mapping,
            )

        if data is None:
            return None

        if not isinstance(data, pd.DataFrame):
            raise CommandError(f"ERROR: Data is not a DataFrame! Got {type(data)} instead.")

        data.columns = data.columns.map(lambda column: str(column).upper().strip())
        data.rename(columns=admin_instance.column_mapping, inplace=True)
        expected_columns = list(admin_instance.dtype_mapping.keys())
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if missing_columns:
            raise CommandError(
                "Missing columns in uploaded file: " + ", ".join(missing_columns)
            )

        return data[expected_columns]

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, required=True)

    def handle(self, *args, **options):
        job = self._get_job(options["job_id"])
        if job.status == FreightCostImportJob.STATUS_COMPLETED:
            self.stdout.write(self.style.WARNING(f"Job {job.pk} already completed."))
            return

        user = self._get_job_user(job)
        admin_instance = FreightCostDetailAdmin(FreightCostDetail, django_admin.site)
        request = _BackgroundRequest(user)

        self._update_job(
            job,
            status=FreightCostImportJob.STATUS_RUNNING,
            started_at=timezone.now(),
            completed_at=None,
            error_message="",
            message="Background import started.",
        )

        admin_instance.message_user = self._build_message_user(job)
        admin_instance._notify_duplicate_report = lambda request_obj, skipped_rows: None
        admin_instance._set_import_progress = self._build_progress_callback(job)

        file_path = job.upload_file.path
        extension = os.path.splitext(job.original_filename)[1].lower()

        try:
            total_rows = self._estimate_total_rows(file_path, extension)
            if total_rows is not None:
                self._update_job(job, total_rows=total_rows)

            if extension in {".csv", ".xlsx"}:
                normalized_chunks = self._iter_normalized_chunks(
                    admin_instance,
                    request,
                    file_path,
                    job.original_filename,
                    extension,
                )
                admin_instance.process_pandas_data_batch_chunks(
                    request,
                    normalized_chunks,
                    batch_size=admin_instance.bulk_insert_batch_size,
                )
            else:
                normalized_data = self._read_normalized_dataframe(
                    admin_instance,
                    request,
                    file_path,
                    extension,
                )
                self._update_job(job, total_rows=len(normalized_data.index))
                admin_instance.process_pandas_data_batch(
                    request,
                    normalized_data,
                    batch_size=admin_instance.bulk_insert_batch_size,
                )

            self._update_job(
                job,
                status=FreightCostImportJob.STATUS_COMPLETED,
                completed_at=timezone.now(),
                message=job.message or "Background import completed.",
            )
        except Exception as exc:
            self._update_job(
                job,
                status=FreightCostImportJob.STATUS_FAILED,
                completed_at=timezone.now(),
                error_message=str(exc),
                message="Background import failed.",
            )
            raise

    def _get_job(self, job_id):
        try:
            return FreightCostImportJob.objects.get(pk=job_id)
        except FreightCostImportJob.DoesNotExist as exc:
            raise CommandError(f"FreightCostImportJob {job_id} not found.") from exc

    def _get_job_user(self, job):
        if job.requested_by_id:
            return get_user_model().objects.filter(pk=job.requested_by_id).first() or AnonymousUser()
        return AnonymousUser()

    def _update_job(self, job, **updates):
        update_fields = []
        for field_name, value in updates.items():
            if getattr(job, field_name) != value:
                setattr(job, field_name, value)
                update_fields.append(field_name)

        if update_fields:
            job.save(update_fields=update_fields)

    def _build_message_user(self, job):
        def _message_user(request, message, level=None):
            self._update_job(job, message=str(message)[:255])
            self.stdout.write(str(message))

        return _message_user

    def _build_progress_callback(self, job):
        def _progress_callback(request, **updates):
            mapped_updates = {}
            for field_name in [
                "processed_rows",
                "created_rows",
                "skipped_rows",
                "chunk_count",
                "total_rows",
                "message",
            ]:
                if field_name in updates:
                    mapped_updates[field_name] = updates[field_name]

            if updates.get("status") == "completed":
                mapped_updates["status"] = FreightCostImportJob.STATUS_COMPLETED
                mapped_updates["completed_at"] = timezone.now()
            elif updates.get("status") == "running":
                mapped_updates["status"] = FreightCostImportJob.STATUS_RUNNING

            self._update_job(job, **mapped_updates)

        return _progress_callback

    def _estimate_total_rows(self, file_path, extension):
        if extension == ".csv":
            with open(file_path, "rb") as handle:
                total_lines = sum(1 for _ in handle)
            return max(total_lines - 1, 0)

        if extension == ".xlsx":
            workbook = load_workbook(file_path, read_only=True, data_only=True)
            try:
                worksheet = workbook.active
                return max((worksheet.max_row or 1) - 1, 0)
            finally:
                workbook.close()

        if extension == ".dbf":
            return sum(1 for _ in dbfread.DBF(file_path))

        return None

    def _iter_normalized_chunks(self, admin_instance, request, file_path, original_filename, extension):
        upload_file = _LocalUploadFile(file_path, original_filename)
        try:
            if extension == ".csv":
                chunk_reader = getattr(admin_instance, "_iter_csv_file_chunks", None) or self._iter_csv_file_chunks
                raw_chunks = chunk_reader(
                    upload_file,
                    admin_instance.dtype_mapping,
                    admin_instance.import_chunk_size,
                )
            elif extension == ".xlsx":
                chunk_reader = getattr(admin_instance, "_iter_xlsx_file_chunks", None) or self._iter_xlsx_file_chunks
                raw_chunks = chunk_reader(
                    upload_file,
                    admin_instance.import_chunk_size,
                )
            else:
                raise CommandError(f"Unsupported chunked file extension: {extension}")

            for chunk in raw_chunks:
                normalized_chunk = self._normalize_import_dataframe(admin_instance, request, chunk)
                if normalized_chunk is None:
                    raise CommandError("Missing columns in uploaded file.")
                yield normalized_chunk
        finally:
            upload_file.close()

    def _read_normalized_dataframe(self, admin_instance, request, file_path, extension):
        if extension == ".xls":
            data = pd.read_excel(file_path, dtype=admin_instance.dtype_mapping)
        elif extension == ".dbf":
            data = pd.DataFrame(iter(dbfread.DBF(file_path)))
        else:
            raise CommandError(f"Unsupported file format: {extension}")

        normalized_data = self._normalize_import_dataframe(admin_instance, request, data)
        if normalized_data is None:
            raise CommandError("Missing columns in uploaded file.")
        return normalized_data