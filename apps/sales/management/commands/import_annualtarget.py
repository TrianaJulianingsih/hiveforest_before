import calendar
import os
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from django.utils.timezone import now

from apps.sales.models.product import Product
from apps.sales.models.sales import AnnualTarget, SalesType


MONTHS = [calendar.month_abbr[number].upper() for number in range(1, 13)]
MONTH_NUM = {month: index + 1 for index, month in enumerate(MONTHS)}

ID_COLUMNS = ["NIP", "NAMA", "KODE_PRODUK", "PRODUK", "TAHUN"]

SECTOR_ALIAS = {
    "REGULER": "001", "REGULAR": "001", "1": "001", "001": "001",
    "BPJS": "002", "ECATALOG": "002", "2": "002", "002": "002",
    "INHEALTH": "003", "3": "003", "003": "003",
    "SPECIAL": "004", "SPECIAL PRICE": "004", "4": "004", "004": "004",
}

SECTOR_TO_SALESTYPE_ID = {
    "001": 1,   # Regular
    "002": 3,   # eCatalog
    "003": 5,   # Inhealth
    "004": 8,   # Special Price
}

SECTOR_LABEL = {
    "001": "Regular",
    "002": "eCatalog",
    "003": "Inhealth",
    "004": "Special Price",
}

QTY_MAX = 2_147_483_647
VALUE_MAX = Decimal("9999999999999.99")

BLANK_VALUES = {"", "-", "NAN", "NONE", "NULL", "N/A"}


def normalize_header(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(value).strip().upper())


def to_decimal(value):
    """Angka source ditulis sebagai ' 4,597.18 ' dan nol ditulis sebagai ' - '."""
    text = str(value).strip().replace(",", "")
    if text.upper() in BLANK_VALUES:
        return Decimal("0")
    try:
        return Decimal(text)
    except Exception:
        return Decimal("0")


def normalize_product_name(value):
    """Kunci pencocokan produk: lowercase, buang SEMUA spasi."""

    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", "", str(value).strip().lower())


def normalize_sector(value):
    text = normalize_header(value)
    if text in SECTOR_ALIAS:
        return SECTOR_ALIAS[text]
    digits = text.replace(".0", "")
    if digits.isdigit():
        return SECTOR_ALIAS.get(digits.zfill(3))
    return None


class Command(BaseCommand):
    help = (
        "Import target tahunan dari file Excel (regular-only dan/atau per-sector) "
        "ke sales_annualtarget. Target di-SUM lintas NIP karena AnnualTarget tidak "
        "menyimpan dimensi orang."
    )

    def add_arguments(self, parser):
        parser.add_argument("--reg-unit", help="File qty target regular (csv/xlsx/xlsb).")
        parser.add_argument("--reg-value", help="File value target regular.")
        parser.add_argument("--sector-unit", help="File qty target per-sector.")
        parser.add_argument("--sector-value", help="File value target per-sector.")
        parser.add_argument(
            "--sheet-reg-unit",
            default="c126_TargetMaster_reg_unit",
            help="Sheet qty regular kalau file Excel (default: c126_TargetMaster_reg_unit).",
        )
        parser.add_argument(
            "--sheet-reg-value",
            default="c126_TargetMaster_reg_value",
            help="Sheet value regular kalau file Excel (default: c126_TargetMaster_reg_value).",
        )
        parser.add_argument("--sheet-sector-unit", help="Sheet qty per-sector kalau file Excel.")
        parser.add_argument("--sheet-sector-value", help="Sheet value per-sector kalau file Excel.")
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID yang menjalankan import."
        )
        parser.add_argument(
            "--target-version",
            type=int,
            default=1,
            help="Nilai AnnualTarget.version (default: 1).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Baca, agregasi, dan validasi saja; tidak menulis ke database.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Baris per batch (default: 1000)."
        )

    def handle(self, *args, **options):
        started_at = now()
        version = options["target_version"]
        batch_size = options["batch_size"]

        if batch_size <= 0:
            raise CommandError("--batch-size harus lebih besar dari 0.")

        frames = []

        if options["reg_unit"] or options["reg_value"]:
            if not (options["reg_unit"] and options["reg_value"]):
                raise CommandError("--reg-unit dan --reg-value harus diisi berpasangan.")
            self.stdout.write("Membaca target regular...")
            frames.append(
                self._read_regular(
                    options["reg_unit"],
                    options["sheet_reg_unit"],
                    options["reg_value"],
                    options["sheet_reg_value"],
                )
            )

        if options["sector_unit"] or options["sector_value"]:
            if not (options["sector_unit"] and options["sector_value"]):
                raise CommandError("--sector-unit dan --sector-value harus diisi berpasangan.")
            self.stdout.write("Membaca target per-sector...")
            frames.append(
                self._read_sector(
                    options["sector_unit"],
                    options["sheet_sector_unit"],
                    options["sector_value"],
                    options["sheet_sector_value"],
                )
            )

        if not frames:
            raise CommandError(
                "Minimal satu pasang file wajib diisi: --reg-unit/--reg-value "
                "dan/atau --sector-unit/--sector-value."
            )

        source = pd.concat(frames, ignore_index=True)
        aggregated = self._aggregate(source)
        records = self._build_records(aggregated, version)

        self.stdout.write(
            f"Baris siap import: {len(records)} | "
            f"produk unik: {len({r['product_id'] for r in records})}"
        )

        if options["dry_run"]:
            self._print_preview(records)
            self.stdout.write(
                self.style.WARNING("Dry-run selesai. Tidak ada tulisan ke database.")
            )
            return

        created, updated = self._write(records, options["cby"], batch_size)
        self.stdout.write(
            self.style.SUCCESS(
                f"{started_at.strftime('%Y-%m-%d %H:%M:%S')} - AnnualTarget selesai: "
                f"created={created}, updated={updated}, total={len(records)}"
            )
        )

    # ------------------------------------------------------------------ read

    def _read_table(self, file_path, sheet_name, header):
        """Baca satu tabel. CSV tidak punya sheet, jadi sheet_name diabaikan."""
        if not os.path.isfile(file_path):
            raise CommandError(f"File tidak ditemukan: {file_path}")

        extension = os.path.splitext(file_path)[1].lower()
        label = file_path if extension == ".csv" else f"{file_path} sheet '{sheet_name}'"

        try:
            if extension == ".csv":
                with open(file_path, "rb") as source_file:
                    sample = source_file.read(8192)
                separator = ";" if sample.count(b";") > sample.count(b",") else ","
                return pd.read_csv(
                    file_path,
                    sep=separator,
                    dtype=str,
                    keep_default_na=False,
                    header=header,
                )

            if sheet_name is None:
                raise CommandError(
                    f"{file_path} adalah file Excel, jadi nama sheet-nya wajib diisi "
                    "lewat --sheet-* yang sesuai."
                )
            return pd.read_excel(
                file_path, sheet_name=sheet_name, dtype=str, header=header
            )
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"Gagal membaca {label}: {exc}") from exc

    def _read_regular(self, unit_path, unit_sheet, value_path, value_sheet):
        qty = self._read_regular_sheet(unit_path, unit_sheet, "qty")
        value = self._read_regular_sheet(value_path, value_sheet, "value")
        merged = qty.merge(
            value, on=ID_COLUMNS + ["BULAN", "SECTOR"], how="outer"
        )
        merged["_source"] = "regular"
        return merged

    def _read_regular_sheet(self, file_path, sheet_name, value_name):
        data = self._read_table(file_path, sheet_name, header=0)
        data.columns = [normalize_header(column) for column in data.columns]

        missing = [column for column in ID_COLUMNS + MONTHS if column not in data.columns]
        if missing:
            raise CommandError(
                f"Kolom wajib tidak ada di {os.path.basename(file_path)}: {', '.join(missing)}. "
                f"Kolom yang terbaca: {', '.join(data.columns)}"
            )

        long_form = data.melt(
            id_vars=ID_COLUMNS,
            value_vars=MONTHS,
            var_name="BULAN",
            value_name=value_name,
        )
        long_form[value_name] = long_form[value_name].map(to_decimal)
        long_form["SECTOR"] = "001"
        self.stdout.write(f"  {os.path.basename(file_path)} [{value_name}]: {len(long_form)} baris")
        return long_form

    def _read_sector(self, unit_path, unit_sheet, value_path, value_sheet):
        qty = self._read_sector_sheet(unit_path, unit_sheet, "qty")
        value = self._read_sector_sheet(value_path, value_sheet, "value")
        merged = qty.merge(
            value, on=ID_COLUMNS + ["BULAN", "SECTOR"], how="outer"
        )
        merged["_source"] = "sector"
        return merged

    def _read_sector_sheet(self, file_path, sheet_name, value_name):
        """Baca sheet per-sector: 2 baris header, cell bulan di-merge.

        Baris 1: NIP NAMA KODE_PRODUK PRODUK TAHUN | JAN (merge 4 kolom) | FEB | ...
        Baris 2:                                   | Reguler BPJS Inhealth Special | 001 002 003 004 | ...
        """
        raw = self._read_table(file_path, sheet_name, header=None)
        label = os.path.basename(file_path)
        if len(raw) < 3:
            raise CommandError(f"{label} terlalu pendek untuk header 2 baris.")

        header_month = raw.iloc[0].tolist()
        header_sector = raw.iloc[1].tolist()

        id_positions = {}
        value_positions = []
        current_month = None

        for position in range(len(header_month)):
            top = normalize_header(header_month[position])
            if top in ID_COLUMNS:
                id_positions[top] = position
                continue
            if top in MONTH_NUM:
                current_month = top
            sector = normalize_sector(header_sector[position])
            if current_month and sector:
                value_positions.append((position, current_month, sector))

        missing = [column for column in ID_COLUMNS if column not in id_positions]
        if missing:
            raise CommandError(
                f"Kolom identitas tidak ada di {label}: {', '.join(missing)}. "
                "Pastikan header memang di baris 1-2 dan tidak ada baris judul di atasnya."
            )
        if not value_positions:
            raise CommandError(
                f"Tidak ada kolom bulan/sector yang terbaca di {label}. "
                "Kemungkinan besar posisi baris header bergeser."
            )

        body = raw.iloc[2:].reset_index(drop=True)
        identity = pd.DataFrame(
            {column: body.iloc[:, position] for column, position in id_positions.items()}
        )

        blocks = []
        for position, month, sector in value_positions:
            block = identity.copy()
            block["BULAN"] = month
            block["SECTOR"] = sector
            block[value_name] = body.iloc[:, position].map(to_decimal)
            blocks.append(block)

        long_form = pd.concat(blocks, ignore_index=True)

        sector_per_month = long_form.groupby("BULAN")["SECTOR"].nunique()
        unexpected = sector_per_month[sector_per_month != len(SECTOR_TO_SALESTYPE_ID)]
        if not unexpected.empty:
            raise CommandError(
                f"{label}: jumlah sector per bulan tidak {len(SECTOR_TO_SALESTYPE_ID)} "
                f"untuk bulan {', '.join(unexpected.index)}. Header kemungkinan bergeser."
            )

        self.stdout.write(
            f"  {label} [{value_name}]: {len(long_form)} baris "
            f"({len(value_positions)} kolom bulan x sector)"
        )
        return long_form

    # ------------------------------------------------------- aggregate/build

    def _aggregate(self, source):
        """SUM lintas NIP. Pembulatan qty dilakukan SEKALI setelah dijumlahkan."""
        for column in ("qty", "value"):
            if column not in source.columns:
                raise CommandError(f"Kolom '{column}' tidak terbentuk saat parsing.")
            source[column] = source[column].map(
                lambda item: item if isinstance(item, Decimal) else to_decimal(item)
            )

        source["_produk_key"] = source["PRODUK"].map(normalize_product_name)

        blank = source[source["_produk_key"] == ""]
        if not blank.empty:
            raise CommandError(
                f"{len(blank)} baris punya kolom PRODUK kosong sehingga tidak bisa "
                "dicocokkan ke sales_product."
            )

        grouped = (
            source.groupby(["_produk_key", "TAHUN", "BULAN", "SECTOR"], as_index=False)
            .agg(
                qty_raw=("qty", "sum"),
                value_raw=("value", "sum"),
                jumlah_nip=("NIP", "nunique"),
                produk=("PRODUK", "first"),
                kode_produk=("KODE_PRODUK", "first"),
                jumlah_kode=("KODE_PRODUK", "nunique"),
            )
        )
        self.stdout.write(
            f"Agregasi: {len(source)} baris source -> {len(grouped)} baris "
            f"(SUM lintas {source['NIP'].nunique()} NIP)"
        )

        multi_code = grouped[grouped["jumlah_kode"] > 1]
        if not multi_code.empty:
            contoh = multi_code.drop_duplicates("_produk_key").head(10)
            self.stdout.write(
                self.style.WARNING(
                    f"{multi_code['_produk_key'].nunique()} nama produk memiliki lebih dari "
                    "satu KODE_PRODUK dan dijumlahkan jadi satu target:"
                )
            )
            for row in contoh.to_dict(orient="records"):
                self.stdout.write(
                    f"  '{row['produk']}' ({row['jumlah_kode']} kode berbeda)"
                )

        return grouped

    def _build_records(self, aggregated, version):
        products = self._resolve_products(aggregated)

        salestypes = {
            salestype.id: salestype
            for salestype in SalesType.objects.filter(
                id__in=set(SECTOR_TO_SALESTYPE_ID.values())
            )
        }
        for sector, salestype_id in SECTOR_TO_SALESTYPE_ID.items():
            salestype = salestypes.get(salestype_id)
            if salestype is None:
                raise CommandError(
                    f"SalesType id={salestype_id} (sector {sector} {SECTOR_LABEL[sector]}) "
                    "tidak ada di sales_salestype."
                )
            if not (salestype.code or "").strip():
                raise CommandError(
                    f"SalesType id={salestype_id} ({salestype.name}) punya code kosong; "
                    "code dipakai membentuk AnnualTarget.code sehingga tidak boleh kosong."
                )
            self.stdout.write(
                f"  sector {sector} {SECTOR_LABEL[sector]} -> SalesType "
                f"id={salestype.id} code='{salestype.code}' name='{salestype.name}'"
            )

        records = []
        seen_codes = {}
        skipped = []

        for row in aggregated.to_dict(orient="records"):
            sector = row["SECTOR"]
            if sector not in SECTOR_TO_SALESTYPE_ID:
                raise CommandError(f"Sector tidak dikenal: {sector}")

            product = products.get(row["_produk_key"])
            if product is None:
                skipped.append(row)
            salestype = salestypes[SECTOR_TO_SALESTYPE_ID[sector]]

            try:
                year = int(float(str(row["TAHUN"]).strip()))
            except (TypeError, ValueError):
                raise CommandError(
                    f"TAHUN tidak terbaca sebagai angka: '{row['TAHUN']}' "
                    f"(produk {row['produk']})"
                )
            target_date = date(year, MONTH_NUM[row["BULAN"]], 1)

            qty = int(Decimal(row["qty_raw"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if abs(qty) > QTY_MAX:
                raise CommandError(
                    f"qty {qty} melebihi batas integer untuk {product.code} {target_date}."
                )

            value = Decimal(row["value_raw"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if abs(value) > VALUE_MAX:
                raise CommandError(
                    f"value {value} melebihi decimal(15,2) untuk {product.code} {target_date}."
                )

            date_code = target_date.strftime("%Y%m%d")
            product_code = (
                product.code.strip()
                if product is not None
                else str(row["kode_produk"]).strip() or row["_produk_key"][:40]
            )
            code = f"{date_code}-{product_code}-{salestype.code}-{version}"
            name = f"{date_code}-{product_code}-{salestype.code}"

            if code in seen_codes:
                previous = seen_codes[code]
                raise CommandError(
                    f"Key bentrok di dalam batch: '{code}' muncul dua kali "
                    f"(sebelumnya produk {previous['produk']} bulan {previous['bulan']}, "
                    f"sekarang {row['produk']} bulan {row['BULAN']}). "
                    "Kemungkinan produk yang sama ada di file regular DAN file sector."
                )
            seen_codes[code] = {"produk": row["produk"], "bulan": row["BULAN"]}

            records.append(
                {
                    "code": code,
                    "name": name,
                    "date": target_date,
                    "product_id": product.id if product is not None else None,
                    "type_id": salestype.id,
                    "qty": qty,
                    "price": None,
                    "value": value,
                    "version": version,
                    "targetgroup": (product.targetgroup or "").strip() if product else "",
                    "description": f"Target {year} {SECTOR_LABEL[sector]}",
                }
            )

        if skipped:
            total_qty = sum(Decimal(row["qty_raw"]) for row in skipped)
            total_value = sum(Decimal(row["value_raw"]) for row in skipped)
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(skipped)} baris tetap diimport dengan product_id NULL "
                    f"(total qty {total_qty}, value {total_value}). "
                    "Set product-nya manual setelah import."
                )
            )

        if not records:
            raise CommandError("Tidak ada satu pun baris yang bisa diimport.")

        return records

    def _resolve_products(self, aggregated):
        """Cocokkan PRODUK di file ke sales_product.name yang dinormalisasi."""

        wanted = set(aggregated["_produk_key"])

        candidates = {}
        for product in Product.objects.filter(deleted=False).only(
            "id", "name", "code", "targetgroup"
        ):
            key = normalize_product_name(product.name)
            if key in wanted:
                candidates.setdefault(key, []).append(product)

        sample = (
            aggregated.drop_duplicates("_produk_key")
            .set_index("_produk_key")[["produk", "kode_produk"]]
            .to_dict(orient="index")
        )

        missing = sorted(key for key in wanted if key not in candidates)
        ambiguous = sorted(key for key, found in candidates.items() if len(found) > 1)

        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(missing)} nama produk tidak ketemu di sales_product.name "
                    "-> product_id NULL:"
                )
            )
            for key in missing:
                self.stdout.write(
                    f"  '{sample[key]['produk']}' (KODE_PRODUK {sample[key]['kode_produk']})"
                )

        if ambiguous:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(ambiguous)} nama produk cocok ke LEBIH DARI SATU baris "
                    "sales_product, tidak ditebak -> product_id NULL:"
                )
            )
            for key in ambiguous:
                kandidat = ", ".join(
                    f"id={product.id} code={product.code} name='{product.name}'"
                    for product in candidates[key]
                )
                self.stdout.write(f"  '{sample[key]['produk']}' cocok ke {kandidat}")

        resolved = {key: found[0] for key, found in candidates.items() if len(found) == 1}
        self.stdout.write(
            f"\nProduk tercocokkan lewat nama: {len(resolved)} dari {len(wanted)}"
        )
        return resolved

    def _print_preview(self, records, limit=15):
        self.stdout.write(f"\nContoh {min(limit, len(records))} baris:")
        for record in records[:limit]:
            self.stdout.write(
                f"  {record['code']} | qty={record['qty']} | value={record['value']}"
            )

    # ----------------------------------------------------------------- write

    def _write(self, records, cby_id, batch_size):
        codes = [record["code"] for record in records]
        existing_ids = dict(
            AnnualTarget.objects.filter(code__in=codes).values_list("code", "id")
        )

        new_records = [record for record in records if record["code"] not in existing_ids]
        old_records = [record for record in records if record["code"] in existing_ids]
        timestamp = now()

        with transaction.atomic():
            if new_records:
                AnnualTarget.objects.bulk_create(
                    [
                        AnnualTarget(
                            **record,
                            slug=slugify(record["code"]),
                            status=1,
                            cby_id=cby_id,
                            cat=timestamp,
                        )
                        for record in new_records
                    ],
                    batch_size=batch_size,
                )

            if old_records:
                AnnualTarget.objects.bulk_update(
                    [
                        AnnualTarget(
                            id=existing_ids[record["code"]],
                            **{
                                key: value
                                for key, value in record.items()
                                if key != "code"
                            },
                            status=1,
                            uby_id=cby_id,
                            uat=timestamp,
                        )
                        for record in old_records
                    ],
                    [
                        "name",
                        "date",
                        "product_id",
                        "type_id",
                        "qty",
                        "price",
                        "value",
                        "version",
                        "targetgroup",
                        "description",
                        "status",
                        "uby",
                        "uat",
                    ],
                    batch_size=batch_size,
                )

        return len(new_records), len(old_records)
