import os
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

from apps.finance.models.products import ItemPrice
from apps.sales.models.sales import RawAPPSO


NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")


# Field RawAPPSO <- kolom source APP.
# Header source boleh berbeda pada kapitalisasi, spasi, titik, atau underscore;
# semua dinormalisasi terlebih dahulu sebelum mapping ini dipakai.
RAW_FIELD_TO_SOURCE_COLUMN = {
    "facno": "NODOKJDI",
    "tanggal": "HRDOK",
    "kode_produk": "KODEPROD",
    "produk": "NMPROD",
    "kode_branch": "Kode_cabang",
    "branch": "Nama_Cabang",
    "kode_outlet": "KODELANG",
    "outlet": "NMLANG",
    "alamat_outlet": "ALMTLANG",
    "kode_group_outlet": "Kode_Group",
    "group_outlet": "Nama_Group",
    "qty": "BANYAK",
    "harga": "HARGA",
    "no_order": "NO_ORDER",
}

SOURCE_REQUIRED_FIELDS = (
    "facno",
    "tanggal",
    "kode_produk",
    "produk",
    "kode_branch",
    "branch",
    "kode_outlet",
    "outlet",
    "alamat_outlet",
    "kode_group_outlet",
    "group_outlet",
    "qty",
    "harga",
    "no_order",
)

PRODUCT_LOOKUP_FIELDS = (
    "kode_produk_oi",
    "produk_oi",
)

# Nilainya konsisten di seluruh sales_rawappso (COUNT DISTINCT = 1),
# sehingga cukup mengambil satu nilai non-null dari tabel.
GLOBAL_PRODUCT_LOOKUP_FIELDS = (
    "kode_group_produk",
    "group_produk",
    "kode_subgroup_produk",
    "subgroup_produk",
)

BRANCH_LOOKUP_FIELDS = (
    "id_branch_oi",
    "kode_branch_oi",
    "branch_oi",
)

OUTLET_LOOKUP_FIELDS = (
    "kode_outlet_oi",
    "outlet_oi",
    "alamat_outlet_oi",
)

RAW_FIELDS = (
    "kode_distributor",
    "type",
    "facno",
    "tanggal",
    "kode_produk",
    "produk",
    "kode_produk_oi",
    "produk_oi",
    "kode_group_produk",
    "group_produk",
    "kode_subgroup_produk",
    "subgroup_produk",
    "kode_branch",
    "branch",
    "id_branch_oi",
    "kode_branch_oi",
    "branch_oi",
    "kode_outlet",
    "cust_id",
    "outlet",
    "alamat_outlet",
    "kode_outlet_oi",
    "outlet_oi",
    "alamat_outlet_oi",
    "kode_group_outlet",
    "group_outlet",
    "kode_salur",
    "kode_sector",
    "sector",
    "kode_channel",
    "channel",
    "kode_sub_channel",
    "sub_channel",
    "kode_region",
    "region",
    "qty",
    "faktor_kali",
    "hjp",
    "hna",
    "harga",
    "whse",
    "tanggal_expired",
    "batch",
    "prsnd",
    "prsnpot",
    "prsnt",
    "prsnbp",
    "prsnbmp",
    "bonus",
    "facAcu",
    "kode_team",
    "team",
    "dun",
    "distribute_apks",
    "distributed_id",
    "distributed_name",
    "parent_id",
    "missing_facno",
    "no_order",
    "periode",
)


def normalize_column_name(value):
    return NORMALIZE_PATTERN.sub("", str(value).strip().lower())


def clean_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    value = str(value).strip()
    if value.lower() in {"nan", "none", "null", "na"}:
        return ""
    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]
    return value


def clean_decimal(value, default=None):
    value = clean_text(value)
    if not value:
        return default

    try:
        return Decimal(value.replace(",", ""))
    except (InvalidOperation, ValueError):
        return default


def parse_date(value):
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    value = clean_text(value)
    if not value:
        return None

    if value.isdigit() and len(value) == 8:
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except ValueError:
            pass

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def date_to_code(value):
    parsed = parse_date(value)
    return parsed.strftime("%Y%m%d") if parsed else ""


def decimal_to_code(value):
    if value is None:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


class Command(BaseCommand):
    help = "Import source APP-SO yang sudah dimapping ke sales_rawappso."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Path file source APP (.csv, .xlsx, atau .xls).",
        )
        parser.add_argument(
            "--sheet",
            default="Transaksi UBT",
            help="Nama sheet Excel source (default: Transaksi UBT).",
        )
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID yang menjalankan import."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hanya membaca dan menampilkan ringkasan; tidak menulis ke database.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Jumlah baris per batch insert/update (default: 1000).",
        )
        parser.add_argument(
            "--limit", type=int, help="Batasi jumlah baris source untuk pengecekan."
        )
        parser.add_argument(
            "--date-from", help="Tanggal awal transaksi (YYYY-MM-DD)."
        )
        parser.add_argument(
            "--date-to", help="Tanggal akhir transaksi (YYYY-MM-DD)."
        )

    def handle(self, *args, **options):
        started_at = now()
        file_path = options["file"]
        cby_id = options["cby"]
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        if batch_size <= 0:
            raise CommandError("--batch-size harus lebih besar dari 0.")

        source_df = self._read_source(file_path, options["sheet"])
        source_df = self._prepare_source(source_df)
        source_df = self._filter_dates(
            source_df,
            options.get("date_from"),
            options.get("date_to"),
        )

        if options.get("limit"):
            if options["limit"] <= 0:
                raise CommandError("--limit harus lebih besar dari 0.")
            source_df = source_df.head(options["limit"]).copy()

        if source_df.empty:
            self.stdout.write(self.style.WARNING("Tidak ada baris source untuk diproses."))
            return

        lookups = self._load_lookups(
            product_codes=set(source_df["kode_produk"]),
            branch_codes=set(source_df["kode_branch"]),
            outlet_codes=set(source_df["kode_outlet"]),
        )
        hjp_lookup = self._load_hjp_lookup(set(source_df["kode_produk"]))

        records = self._build_records(source_df, lookups, hjp_lookup)
        mapping_fields = (
            PRODUCT_LOOKUP_FIELDS
            + GLOBAL_PRODUCT_LOOKUP_FIELDS
            + BRANCH_LOOKUP_FIELDS
            + OUTLET_LOOKUP_FIELDS
        )
        ambiguous_keys = (
            lookups["stats"]["product"]
            + lookups["stats"]["branch"]
            + lookups["stats"]["outlet"]
        )
        null_mapping_fields = [
            field
            for field in mapping_fields
            if any(record[field] is None for record in records)
        ]
        self.stdout.write(
            "Mapping ambigu: "
            f"{ambiguous_keys} key\n"
            f"Kolom dikosongkan ({len(null_mapping_fields)}): "
            f"{', '.join(null_mapping_fields) if null_mapping_fields else '-'}"
        )

        codes = [record["code"] for record in records]
        existing_ids = dict(
            RawAPPSO.objects.filter(code__in=codes).values_list("code", "id")
        )

        new_records = [record for record in records if record["code"] not in existing_ids]
        existing_records = [
            record for record in records if record["code"] in existing_ids
        ]
        duplicate_codes = len(codes) - len(set(codes))
        missing_hjp = sum(record["hjp"] is None for record in records)

        self.stdout.write(
            "APP source rows: "
            f"{len(records)} | new: {len(new_records)} | "
            f"update: {len(existing_records)} | duplicate code in source: {duplicate_codes}"
        )
        self.stdout.write(
            f"HJP tidak ditemukan untuk {missing_hjp} row; nilai akan disimpan NULL."
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry-run selesai. Tidak ada insert/update/delete ke database."
                )
            )
            return

        created_count = 0
        updated_count = 0
        timestamp = now()

        with transaction.atomic():
            create_objects = [
                RawAPPSO(
                    **record,
                    status=1,
                    cby_id=cby_id,
                    cat=timestamp,
                )
                for record in new_records
            ]
            if create_objects:
                RawAPPSO.objects.bulk_create(create_objects, batch_size=batch_size)
                created_count = len(create_objects)

            update_objects = []
            for record in existing_records:
                update_objects.append(
                    RawAPPSO(
                        id=existing_ids[record["code"]],
                        **record,
                        status=1,
                        uby_id=cby_id,
                        uat=timestamp,
                    )
                )

            update_fields = list(RAW_FIELDS) + ["name", "code", "slug", "status", "uby", "uat"]
            if update_objects:
                RawAPPSO.objects.bulk_update(
                    update_objects,
                    update_fields,
                    batch_size=batch_size,
                )
                updated_count = len(update_objects)

        self.stdout.write(
            self.style.SUCCESS(
                f"{started_at.strftime('%Y-%m-%d %H:%M:%S')} - "
                f"RawAPPSO selesai: created={created_count}, updated={updated_count}, "
                f"total={len(records)}"
            )
        )

    def _read_source(self, file_path, sheet_name):
        if not os.path.isfile(file_path):
            raise CommandError(f"File source tidak ditemukan: {file_path}")

        extension = os.path.splitext(file_path)[1].lower()
        try:
            if extension == ".csv":
                with open(file_path, "rb") as source_file:
                    first_bytes = source_file.read(1024)
                separator = "," if b"," in first_bytes else ";"
                return pd.read_csv(
                    file_path,
                    sep=separator,
                    # Baris 1 adalah metadata; header berada di baris 2.
                    skiprows=1,
                    header=0,
                    dtype="string",
                    keep_default_na=False,
                )

            if extension in {".xlsx", ".xls"}:
                # Baris Excel pertama adalah metadata; header berada di baris 2.
                return pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    header=1,
                    dtype="string",
                )

        except Exception as exc:
            raise CommandError(f"Gagal membaca source {file_path}: {exc}") from exc

        raise CommandError(
            f"Format file tidak didukung: {extension}. Gunakan CSV atau XLS/XLSX."
        )

    def _prepare_source(self, data):
        normalized_columns = {}
        duplicate_columns = []
        for column in data.columns:
            normalized = normalize_column_name(column)
            if normalized in normalized_columns:
                duplicate_columns.append(str(column))
            normalized_columns[normalized] = column

        if duplicate_columns:
            raise CommandError(
                "Ada header source yang menjadi duplikat setelah normalisasi: "
                + ", ".join(duplicate_columns)
            )

        rename_map = {}
        for target_field, source_column_name in RAW_FIELD_TO_SOURCE_COLUMN.items():
            normalized_source = normalize_column_name(source_column_name)
            source_column = normalized_columns.get(normalized_source)
            if source_column is not None:
                rename_map[source_column] = target_field

        data = data.rename(columns=rename_map).copy()
        missing = [field for field in SOURCE_REQUIRED_FIELDS if field not in data.columns]
        if missing:
            raise CommandError(
                "Kolom source wajib tidak ditemukan: " + ", ".join(missing)
            )

        for field in SOURCE_REQUIRED_FIELDS:
            data[field] = data[field].map(clean_text)

        data["_tanggal_date"] = data["tanggal"].map(parse_date)
        invalid_dates = data["_tanggal_date"].isna()
        if invalid_dates.any():
            invalid_rows = (data.index[invalid_dates] + 2).tolist()[:10]
            raise CommandError(
                "HRDOK/tanggal tidak dapat dibaca pada row source: "
                + ", ".join(str(row) for row in invalid_rows)
            )

        data["tanggal"] = data["_tanggal_date"].map(
            lambda value: value.strftime("%Y%m%d")
        )
        data["qty"] = data["qty"].map(lambda value: clean_decimal(value, Decimal("0")))
        data["harga"] = data["harga"].map(lambda value: clean_decimal(value, Decimal("0")))
        data = data.reset_index(drop=True)
        return data

    def _filter_dates(self, data, date_from_value, date_to_value):
        date_from = self._parse_argument_date(date_from_value, "--date-from")
        date_to = self._parse_argument_date(date_to_value, "--date-to")
        if date_from and date_to and date_from > date_to:
            raise CommandError("--date-from tidak boleh lebih besar dari --date-to.")

        if date_from:
            data = data[data["_tanggal_date"] >= date_from]
        if date_to:
            data = data[data["_tanggal_date"] <= date_to]
        return data.reset_index(drop=True)

    def _parse_argument_date(self, value, argument_name):
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise CommandError(f"{argument_name} harus berformat YYYY-MM-DD.")
        return parsed

    def _load_lookups(self, product_codes, branch_codes, outlet_codes):
        lookup_fields = (
            "kode_produk",
            *PRODUCT_LOOKUP_FIELDS,
            *GLOBAL_PRODUCT_LOOKUP_FIELDS,
            "kode_branch",
            *BRANCH_LOOKUP_FIELDS,
            "kode_outlet",
            *OUTLET_LOOKUP_FIELDS,
        )
        rows = RawAPPSO.objects.values(*lookup_fields).iterator()

        product_counters = {
            field: defaultdict(Counter) for field in PRODUCT_LOOKUP_FIELDS
        }
        global_product_counters = {
            field: Counter() for field in GLOBAL_PRODUCT_LOOKUP_FIELDS
        }
        branch_counters = {
            field: defaultdict(Counter) for field in BRANCH_LOOKUP_FIELDS
        }
        outlet_counters = {
            field: defaultdict(Counter) for field in OUTLET_LOOKUP_FIELDS
        }

        for row in rows:
            product_code = clean_text(row.get("kode_produk"))
            if product_code in product_codes:
                for field in PRODUCT_LOOKUP_FIELDS:
                    value = clean_text(row.get(field))
                    if value:
                        product_counters[field][product_code][value] += 1

            for field in GLOBAL_PRODUCT_LOOKUP_FIELDS:
                value = clean_text(row.get(field))
                if value:
                    global_product_counters[field][value] += 1

            branch_code = clean_text(row.get("kode_branch"))
            if branch_code in branch_codes:
                for field in BRANCH_LOOKUP_FIELDS:
                    value = clean_text(row.get(field))
                    if value:
                        branch_counters[field][branch_code][value] += 1

            outlet_code = clean_text(row.get("kode_outlet"))
            if outlet_code in outlet_codes:
                for field in OUTLET_LOOKUP_FIELDS:
                    value = clean_text(row.get(field))
                    if value:
                        outlet_counters[field][outlet_code][value] += 1

        def resolve(counters):
            result = {}
            ambiguous = 0
            all_keys = set()
            for counter_by_key in counters.values():
                all_keys.update(counter_by_key.keys())

            for key in all_keys:
                is_ambiguous = any(
                    len(counter_by_key.get(key, Counter())) > 1
                    for counter_by_key in counters.values()
                )

                if is_ambiguous:
                    # Jika salah satu field punya lebih dari satu mapping,
                    # kosongkan seluruh kelompok mapping agar tidak memilih
                    # nilai secara asumsi.
                    result[key] = {field: None for field in counters}
                    ambiguous += 1
                    continue

                result[key] = {
                    field: next(iter(counter_by_key.get(key, Counter())), None)
                    for field, counter_by_key in counters.items()
                }
            return result, ambiguous

        product_lookup, product_ambiguous = resolve(product_counters)
        branch_lookup, branch_ambiguous = resolve(branch_counters)
        outlet_lookup, outlet_ambiguous = resolve(outlet_counters)
        global_product_lookup = {
            field: next(iter(counter), None)
            for field, counter in global_product_counters.items()
        }

        return {
            "product": product_lookup,
            "global_product": global_product_lookup,
            "branch": branch_lookup,
            "outlet": outlet_lookup,
            "stats": {
                "product": product_ambiguous,
                "branch": branch_ambiguous,
                "outlet": outlet_ambiguous,
            },
        }

    def _load_hjp_lookup(self, product_codes):
        prices = ItemPrice.objects.filter(
            distributor_id=9,
            distitem__code__in=product_codes,
            effective__isnull=False,
        ).values(
            "distitem__code",
            "effective",
            "hjp",
        ).order_by("distitem__code", "-effective", "-id")

        lookup = defaultdict(list)
        for row in prices:
            code = clean_text(row.get("distitem__code"))
            if code:
                lookup[code].append((row["effective"], row["hjp"]))
        return lookup

    def _resolve_hjp(self, prices, product_code, transaction_date):
        for effective, hjp in prices.get(product_code, []):
            if effective < transaction_date:
                return hjp
        return None

    def _build_records(self, data, lookups, hjp_lookup):
        records = []
        code_counts = Counter()

        for row in data.to_dict(orient="records"):
            product_code = clean_text(row["kode_produk"])
            branch_code = clean_text(row["kode_branch"])
            outlet_code = clean_text(row["kode_outlet"])
            product_lookup = lookups["product"].get(product_code, {})
            global_product_lookup = lookups["global_product"]
            branch_lookup = lookups["branch"].get(branch_code, {})
            outlet_lookup = lookups["outlet"].get(outlet_code, {})
            transaction_date = row["_tanggal_date"]

            base_code = (
                f"{row['tanggal']}{branch_code}-{row['facno']}-"
                f"{product_code}-{outlet_code}--{decimal_to_code(row['qty'])}"
            )
            occurrence = code_counts[base_code]
            code_counts[base_code] += 1

            record = {
                "name": f"{row['tanggal']}{branch_code}-{row['facno']}-{product_code}",
                "code": base_code,
                "slug": f"{base_code}-{occurrence}",
                "kode_distributor": "APP",
                "type": "8",
                "facno": row["facno"],
                "tanggal": row["tanggal"],
                "kode_produk": product_code,
                "produk": row["produk"],
                "kode_produk_oi": product_lookup.get("kode_produk_oi"),
                "produk_oi": product_lookup.get("produk_oi"),
                "kode_group_produk": global_product_lookup.get("kode_group_produk"),
                "group_produk": global_product_lookup.get("group_produk"),
                "kode_subgroup_produk": global_product_lookup.get("kode_subgroup_produk"),
                "subgroup_produk": global_product_lookup.get("subgroup_produk"),
                "kode_branch": branch_code,
                "branch": row["branch"],
                "id_branch_oi": branch_lookup.get("id_branch_oi"),
                "kode_branch_oi": branch_lookup.get("kode_branch_oi"),
                "branch_oi": branch_lookup.get("branch_oi"),
                "kode_outlet": outlet_code,
                "cust_id": "",
                "outlet": row["outlet"],
                "alamat_outlet": row["alamat_outlet"],
                "kode_outlet_oi": outlet_lookup.get("kode_outlet_oi"),
                "outlet_oi": outlet_lookup.get("outlet_oi"),
                "alamat_outlet_oi": outlet_lookup.get("alamat_outlet_oi"),
                "kode_group_outlet": row["kode_group_outlet"],
                "group_outlet": row["group_outlet"],
                "kode_salur": "",
                "kode_sector": "1",
                "sector": "Regular",
                "kode_channel": "",
                "channel": "",
                "kode_sub_channel": "",
                "sub_channel": "",
                "kode_region": "",
                "region": "",
                "qty": row["qty"],
                "faktor_kali": Decimal("1"),
                "hjp": self._resolve_hjp(hjp_lookup, product_code, transaction_date),
                "hna": None,
                "harga": row["harga"],
                "whse": "",
                "tanggal_expired": "",
                "batch": "",
                "prsnd": Decimal("0"),
                "prsnpot": Decimal("0"),
                "prsnt": Decimal("0"),
                "prsnbp": Decimal("0"),
                "prsnbmp": Decimal("0"),
                "bonus": Decimal("0"),
                "facAcu": "",
                "kode_team": "UBT",
                "team": "UBIT",
                "dun": "",
                "distribute_apks": "",
                "distributed_id": "",
                "distributed_name": "",
                "parent_id": "0",
                "missing_facno": "0",
                "no_order": row["no_order"],
                "periode": row["tanggal"][:6],
            }
            records.append(record)

        return records
