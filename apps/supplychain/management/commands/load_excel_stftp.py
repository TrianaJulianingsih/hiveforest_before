# Utandra | Import stok distributor dari file CSV/XLSX FTP ke RawMUST
#
# Konversi file CSV export FTP -> RawMUST.
# REPLACE per-periode (hapus semua RawMUST dengan periode yang sama
# args --dry-run for report only
# Referensi: apps/supplychain/management/commands/load_stockdailymup.py (delete+bulk_create).

from decimal import Decimal, InvalidOperation
from datetime import datetime
import os

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import now
from pytz import timezone as pytz_timezone

from apps.supplychain.models.distributions import (
    RawMUST,
    Branch,
    DistributorItem,
)

DTYPE_MAPPING = {
    "kd_prc": "string",
    "periode": "string",
    "io_id": "string",
    "kdcab": "string",
    "nmcab": "string",
    "subinven": "string",
    "klasprod": "string",
    "nmklas": "string",
    "loc": "string",
    "nmloc": "string",
    "lot": "string",
    "ed": "date",
    "kodeprod": "string",
    "namaprod": "string",
    "kemasan": "string",
    "hna": "decimal",
    "sldoawal": "decimal",
    "sldottip": "decimal",
    "sldorusak": "decimal",
    "bapb": "string",
    "bapbttip": "string",
    "beli": "string",
    "realokasi": "string",
    "cnretur": "string",
    "returbnus": "string",
    "faktur": "string",
    "faktbnus": "string",
    "spp": "string",
    "alokasi": "string",
    "cnbeli": "string",
    "mskrusak": "string",
    "klrusak": "string",
    "sppttip": "string",
    "spkirim": "string",
    "spterima": "string",
    "akhir": "integer",
    "atr": "integer",
    "tgldata": "string",
}

invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a", "None", "nan", "NaN"]

# Kolom yang wajib ada di file.
REQUIRED_COLUMNS = [
    "periode",
    "tgldata",
    "kdcab",
    "kodeprod",
    "namaprod",
    "klasprod",
    "lot",
]


class Command(BaseCommand):
    help = (
        "Import stok distributor dari file CSV FTP ke RawMUST (replace per-periode). "
        "Gunakan --dry-run untuk melaporkan jumlah baris tanpa menyentuh DB."
    )

    user_tz = pytz_timezone(getattr(settings, "DEFAULT_LOG_TIMEZONE", "Asia/Jakarta"))

    def log(self, message):
        timestamp = (
            timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        )
        log_line = f"{timestamp}: {message}"
        print(log_line, flush=True)
        log_file = "/var/log/hiveforest/load_excel_stftp.log"
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True, help="Path file CSV FTP")
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID yang melakukan import"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hanya laporkan jumlah baris, tidak menulis DB",
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Batch size bulk_create"
        )
        parser.add_argument(
            "--limit", type=int, help="Batasi jumlah baris diproses (debug)"
        )

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Header CSV -> nama field model (lowercase; header sudah fix sama).
        df = df.rename(columns={c: c.lower().strip() for c in df.columns})

        # 2. Validasi kolom wajib. Harus dicek SEBELUM step 4, karena di sana
        #    kolom yang hilang diisi kosong sehingga error jadi tidak terlihat.
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise CommandError(
                f"Kolom wajib tidak ditemukan di file: {', '.join(missing)}. "
                f"Pastikan file yang di-upload adalah export stok FTP yang benar."
            )

        # 3. Keep hanya kolom model
        keep = [c for c in DTYPE_MAPPING.keys() if c in df.columns]
        df = df[keep].copy()

        # 4. Field model yang tidak ada di file -> isi kosong.
        for col in DTYPE_MAPPING.keys():
            if col not in df.columns:
                df[col] = ""

        # 5. Bersihkan string.
        string_fields = [k for k, v in DTYPE_MAPPING.items() if v == "string"]
        for col in string_fields:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": "", "None": "", "NULL": "", "NaN": ""})
            )

        # 6. Decimal. Kosong/null dibiarkan None
        decimal_fields = [k for k, v in DTYPE_MAPPING.items() if v == "decimal"]

        def _cast_decimal(val):
            v = str(val).strip()
            if v in invalid_entries:
                return None
            try:
                return Decimal(v)
            except (ValueError, InvalidOperation):
                return None

        for col in decimal_fields:
            df[col] = df[col].apply(_cast_decimal)

        # 7. Date (ed) & integer (akhir, atr).
        def _parse_ed(val):
            v = str(val).strip()
            if v in invalid_entries:
                return None
            try:
                return datetime.strptime(v, "%Y%m%d").date()
            except ValueError:
                return None

        def _cast_int(val):
            v = str(val).strip()
            if v in invalid_entries:
                return None
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return None

        df["ed"] = df["ed"].apply(_parse_ed)
        df["akhir"] = df["akhir"].apply(_cast_int)
        df["atr"] = df["atr"].apply(_cast_int)

        # 8. Buang baris kosong (anchor: periode; baris ",,,," pasti kosong).
        df = df[df["periode"] != ""].copy()

        # 9. Build name & slug, mengikuti load_stockdailymup.py:
        #    name = tgl-namaprod-klasprod-kdcab ; slug = name-lot
        #    (baris pertama slug polos, duplikat dapat -1, -2, ...)
        #    important: Di FTP tidak ada TGL_PROSES, jadi pakai tgldata dari file.
        df["name"] = (
            df["tgldata"]
            + "-"
            + df["namaprod"]
            + "-"
            + df["klasprod"]
            + "-"
            + df["kdcab"]
        )
        slug_base = df["name"] + "-" + df["lot"]
        counter = df.groupby(slug_base).cumcount()
        df["slug"] = slug_base.where(counter == 0, slug_base + "-" + counter.astype(str))

        return df

    def handle(self, *args, **options):
        cby_id = options["cby"]
        path = options["file"]
        dry_run = options["dry_run"]

        self.log(
            f"Import Started for user {cby_id} | file={path} | dry_run={dry_run}"
        )
        try:
            summary = self._import(options)
            self.log(summary)
            return summary
        except Exception as e:
            self.log(f"Import Failed: {e}")
            raise

    def _import(self, options):
        path = options["file"]
        cby_id = options["cby"]
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        limit = options.get("limit")

        # Perlakukan file sesuai ekstensi: .csv -> read_csv, .xlsx/.xls -> read_excel.
        p = path.lower()
        if p.endswith((".xlsx", ".xls")):
            reader = lambda: pd.read_excel(path, dtype=str, keep_default_na=False)
        elif p.endswith(".csv"):
            reader = lambda: pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            raise CommandError("Ekstensi tidak didukung (hanya .csv / .xlsx / .xls)")

        try:
            df = reader()
        except FileNotFoundError:
            raise CommandError(f"File tidak ditemukan: {path}")
        except Exception as e:
            raise CommandError(f"Gagal membaca file: {e}")

        df = self._prepare_dataframe(df)
        if limit:
            df = df.head(limit)

        parsed = len(df)
        periodes = sorted(p for p in df["periode"].unique() if p)

        if dry_run:
            existing = RawMUST.objects.filter(periode__in=periodes).count()
            return (
                f"DRY-RUN periode {periodes}: akan hapus {existing} baris lama, "
                f"akan insert {parsed} baris. Tidak ada perubahan DB."
            )

        records = df.to_dict(orient="records")

        # Resolusi FK, mengikuti load_stockdailymup.py
        DISTRIBUTOR_ID = 1

        branches = {
            (b.initial, b.distributor_id, b.status): b
            for b in Branch.objects.filter(distributor_id=DISTRIBUTOR_ID)
        }

        distributor_items = {
            di.code.strip(): di.id for di in DistributorItem.objects.all()
        }

        branch_aliases = {
            "JK1": "JKT1",
            "JK2": "JKT2",
        }

        create_objs = []
        for row in records:
            branch_code = (row.get("kdcab") or "").strip()
            branch = branches.get(
                (branch_aliases.get(branch_code, branch_code), DISTRIBUTOR_ID, 1)
            )

            create_objs.append(
                RawMUST(
                    name=row.get("name", ""),
                    slug=row.get("slug", ""),
                    branch=branch,
                    distributor_id=DISTRIBUTOR_ID,
                    distributoritem_id=distributor_items.get(row.get("kodeprod")),
                    kd_prc=row.get("kd_prc", ""),
                    periode=row.get("periode", ""),
                    io_id=row.get("io_id", ""),
                    kdcab=row.get("kdcab", ""),
                    nmcab=row.get("nmcab", ""),
                    subinven=row.get("subinven", ""),
                    klasprod=row.get("klasprod", ""),
                    nmklas=row.get("nmklas", ""),
                    loc=row.get("loc", ""),
                    nmloc=row.get("nmloc", ""),
                    lot=row.get("lot", ""),
                    ed=row.get("ed"),
                    kodeprod=row.get("kodeprod", ""),
                    namaprod=row.get("namaprod", ""),
                    kemasan=row.get("kemasan", ""),
                    hna=row.get("hna", 0),
                    sldoawal=row.get("sldoawal", 0),
                    sldottip=row.get("sldottip", 0),
                    sldorusak=row.get("sldorusak", 0),
                    bapb=row.get("bapb", ""),
                    bapbttip=row.get("bapbttip", ""),
                    beli=row.get("beli", ""),
                    realokasi=row.get("realokasi", ""),
                    cnretur=row.get("cnretur", ""),
                    returbnus=row.get("returbnus", ""),
                    faktur=row.get("faktur", ""),
                    faktbnus=row.get("faktbnus", ""),
                    spp=row.get("spp", ""),
                    alokasi=row.get("alokasi", ""),
                    cnbeli=row.get("cnbeli", ""),
                    mskrusak=row.get("mskrusak", ""),
                    klrusak=row.get("klrusak", ""),
                    sppttip=row.get("sppttip", ""),
                    spkirim=row.get("spkirim", ""),
                    spterima=row.get("spterima", ""),
                    akhir=row.get("akhir"),
                    atr=row.get("atr"),
                    tgldata=row.get("tgldata", ""),
                    status=1,
                    cby_id=cby_id,
                    cat=now(),
                )
            )

        with transaction.atomic():
            deleted, _ = RawMUST.objects.filter(periode__in=periodes).delete()
            RawMUST.objects.bulk_create(create_objs, batch_size=batch_size)

        return (
            f"Import periode {periodes}: deleted {deleted} baris lama, "
            f"inserted {len(create_objs)} baris."
        )
