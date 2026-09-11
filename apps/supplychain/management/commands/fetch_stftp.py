# Utandra | Auto-fetch stok FTP: download ZIP -> DBF -> CSV -> RawMUST
#
# Alur per tanggal:
#   1. Ambil CredentialFTP terbaru (periode YYYYMMDD terbesar) = password aktif.
#   2. Susun URL: {url}/St{YYMMDD}.ZIP  (YYMMDD = tanggal file).
#   3. Download via HTTP NTLM auth (requests + requests-ntlm).
#   4. Ekstrak ZIP -> cari .dbf -> konversi ke CSV (dbfread, pola admin_base.py).
#   5. Panggil command load_excel_stftp untuk parsing + simpan ke DB (reuse).
#
# Mode:
#   - default (cron 23:00 WIB)       : 1 file = tanggal hari ini.
#   - --date YYMMDD                  : 1 file = tanggal tertentu.
#   - --date-from/--date-to (Y-M-D)  : BACKFILL, loop tiap hari dalam rentang.
#
# Tiap tanggal tetap di-hit; kalau file memang tidak ada (HTTP 404) -> tidak
# diimport, cukup dicatat di log, lalu lanjut ke tanggal berikutnya.

import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests
from requests_ntlm import HttpNtlmAuth
from dbfread import DBF
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.base.models.credential_ftp import CredentialFTP


class Command(BaseCommand):
    help = (
        "Download stok FTP (ZIP), konversi DBF->CSV, import ke RawMUST via "
        "load_excel_stftp. Default hari ini; --date-from/--date-to untuk backfill."
    )

    user_tz = pytz_timezone(getattr(settings, "DEFAULT_LOG_TIMEZONE", "Asia/Jakarta"))

    def log(self, message):
        # Cukup cetak ke stdout; di cron redirect '>> file' yang menulis ke log
        # (biar tidak dobel dgn self-write). Konsisten dgn command lain.
        timestamp = (
            timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        )
        print(f"{timestamp}: {message}", flush=True)

    def add_arguments(self, parser):
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID yang melakukan import"
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Tanggal file tunggal (YYMMDD, mis. 260719). Default: hari ini.",
        )
        parser.add_argument(
            "--date-from",
            type=str,
            help="BACKFILL: tanggal awal (YYYY-MM-DD). Wajib berpasangan dg --date-to.",
        )
        parser.add_argument(
            "--date-to",
            type=str,
            help="BACKFILL: tanggal akhir (YYYY-MM-DD). Wajib berpasangan dg --date-from.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Teruskan ke load_excel_stftp: parse tanpa menulis DB",
        )

    # ── Entry point ─────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        cby_id = options["cby"]
        dates = self._resolve_dates(options)
        mode = (
            f"backfill {dates[0]}..{dates[-1]} ({len(dates)} hari)"
            if len(dates) > 1
            else str(dates[0])
        )
        self.log(f"Fetch Started for user {cby_id} | {mode}")
        try:
            cred = self._get_credential()
            summary = self._run(cred, dates, cby_id, options["dry_run"])
            self.log(summary)
            return summary
        except Exception as e:
            self.log(f"Fetch Failed: {e}")
            raise

    def _resolve_dates(self, options):
        """Kembalikan daftar tanggal (list of date) yang akan diproses."""
        df_, dt_ = options.get("date_from"), options.get("date_to")
        if df_ or dt_:
            if not (df_ and dt_):
                raise CommandError("--date-from dan --date-to harus diisi berpasangan.")
            try:
                start = datetime.strptime(df_.strip(), "%Y-%m-%d").date()
                end = datetime.strptime(dt_.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise CommandError("Format --date-from/--date-to salah (harus YYYY-MM-DD).")
            if start > end:
                raise CommandError("--date-from tidak boleh setelah --date-to.")
            return [start + timedelta(days=i) for i in range((end - start).days + 1)]

        if options.get("date"):
            try:
                return [datetime.strptime(options["date"].strip(), "%y%m%d").date()]
            except ValueError:
                raise CommandError(
                    f"Format --date salah (harus YYMMDD, mis. 260719): {options['date']}"
                )

        return [timezone.now().astimezone(self.user_tz).date()]

    def _get_credential(self):
        """Kredensial TERBARU (periode YYYYMMDD terbesar). Password server rotasi,
        yang berlaku saat download adalah yang paling baru -- sama untuk semua
        tanggal dalam backfill karena semuanya di-download sekarang."""
        cred = (
            CredentialFTP.nondeleted_objects
            .exclude(periode__isnull=True)
            .exclude(periode="")
            .order_by("-periode", "-cat")
            .first()
        )
        if not cred:
            raise CommandError(
                "Belum ada CredentialFTP terisi. Isi dulu kredensial di admin."
            )
        if not (cred.url and cred.username and cred.password):
            raise CommandError(
                f"CredentialFTP periode {cred.periode} belum lengkap (url/username/password)."
            )
        return cred

    def _run(self, cred, dates, cby_id, dry_run):
        # Satu tanggal -> teruskan langsung (error diangkat, cron kelihatan merah).
        if len(dates) == 1:
            return self._fetch_one(cred, dates[0], cby_id, dry_run)

        # Backfill: per-hari; kegagalan satu hari tidak menghentikan yang lain.
        ok = skip = fail = 0
        for d in dates:
            try:
                result = self._fetch_one(cred, d, cby_id, dry_run)
                self.log(result)
                if result.startswith("SKIP"):
                    skip += 1
                else:
                    ok += 1
            except Exception as e:
                self.log(f"St{d.strftime('%y%m%d')}.ZIP -> GAGAL: {e}")
                fail += 1
        return (
            f"BACKFILL {dates[0]}..{dates[-1]}: ok={ok}, skip={skip}, gagal={fail} "
            f"(dari {len(dates)} hari)."
        )

    # ── Satu tanggal: download -> unzip -> dbf->csv -> import ────────────────
    def _fetch_one(self, cred, target, cby_id, dry_run):
        yymmdd = target.strftime("%y%m%d")
        base = cred.url.strip().rstrip("/")
        filename = f"St{yymmdd}.ZIP"
        url = f"{base}/{filename}"
        self.log(f"Downloading {url}")

        tmpdir = tempfile.mkdtemp(prefix="fetch_stftp_")
        try:
            zip_path = os.path.join(tmpdir, filename)
            try:
                resp = requests.get(
                    url,
                    auth=HttpNtlmAuth(cred.username, cred.password),
                    stream=True,
                    timeout=(15, 180),
                )
            except requests.RequestException as e:
                raise CommandError(f"Gagal konek ke server FTP: {e}")

            if resp.status_code == 404:
                # Tetap di-hit tiap tanggal; kalau server balas 404 (file memang
                # tidak ada) -> tidak diimport, cukup dicatat, bukan error.
                return (
                    f"SKIP {filename}: file tidak ada di server (404). "
                    f"Tidak ada perubahan DB."
                )
            if resp.status_code in (401, 403):
                raise CommandError(
                    f"Auth ditolak ({resp.status_code}) untuk {filename}. "
                    f"Cek username/password CredentialFTP periode {cred.periode}."
                )
            resp.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if not zipfile.is_zipfile(zip_path):
                raise CommandError(
                    f"File terunduh bukan ZIP yang valid ({os.path.getsize(zip_path)} byte). "
                    f"Kemungkinan server mengembalikan halaman error, bukan data."
                )

            # Ekstrak ZIP -> cari .dbf.
            extract_dir = os.path.join(tmpdir, "extract")
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)

            dbf_files = [
                os.path.join(dp, fn)
                for dp, _, fns in os.walk(extract_dir)
                for fn in fns
                if fn.lower().endswith(".dbf")
            ]
            if not dbf_files:
                raise CommandError(f"ZIP {filename} tidak berisi file .dbf.")
            dbf_path = sorted(dbf_files)[0]

            # DBF -> CSV (pola dbfread di admin_base.py).
            table = DBF(
                dbf_path,
                char_decode_errors="replace",
                ignore_missing_memofile=True,
            )
            df = pd.DataFrame(iter(table))
            csv_path = os.path.join(tmpdir, f"st{yymmdd}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
            self.log(f"Converted {os.path.basename(dbf_path)} -> CSV ({len(df)} baris)")

            # Import ke DB (reuse load_excel_stftp).
            summary = call_command(
                "load_excel_stftp", file=csv_path, cby=cby_id, dry_run=dry_run
            )
            return f"{filename} -> {summary}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
