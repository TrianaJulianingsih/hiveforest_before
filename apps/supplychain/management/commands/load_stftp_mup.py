# Utandra | Auto-import stok FTP dari DB SUMBER (MySQL) -> RawMUST.
#
# Alternatif fetch_stftp (yang download file ZIP). Di sini data ditarik LANGSUNG
# dari DB sumber FTP -- mirip load_stockdailymup yang baca MySQL MUP. Target &
# transform tetap sama: reuse load_excel_stftp (lewat temp-CSV).
#
# ================================ STATUS ================================
# DB sumber FTP BELUM tersedia. Nama tabel + kolom filter tanggal masih
# PLACEHOLDER (lihat TODO(FTP-DB) di _query_rows). Saat DB ready:
#   1. Isi ENV DB_STFTP_* (lihat di bawah).
#   2. Sesuaikan tabel + kolom/format filter tanggal di _query_rows.
#   3. Pastikan nama kolom hasil SELECT == header CSV/field RawMUST
#      (periode, tgldata, kdcab, kodeprod, ...); kalau beda -> alias di SELECT.
# Fieldnya diharapkan sama persis dgn export CSV FTP, jadi transform tak berubah.
# =======================================================================
#
# Konfigurasi ENV (mirror DB_MUP_*):
#   DB_STFTP_HOST, DB_STFTP_PORT (default 3306), DB_STFTP_USER,
#   DB_STFTP_PASSWORD, DB_STFTP_DATABASE, DB_STFTP_TABLE (opsional; default 'st')
#
# Mode:
#   - default (cron)                 : 1 tanggal = hari ini.
#   - --date YYMMDD                  : 1 tanggal tertentu.
#   - --date-from/--date-to (Y-M-D)  : BACKFILL, loop tiap hari dalam rentang.

import os
import tempfile
from datetime import datetime, timedelta

import mysql.connector
import pandas as pd
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pytz import timezone as pytz_timezone


class Command(BaseCommand):
    help = (
        "Tarik stok FTP dari DB sumber (MySQL) lalu import ke RawMUST via "
        "load_excel_stftp. Alternatif fetch_stftp (download). Default hari ini; "
        "--date-from/--date-to untuk backfill. (DB sumber belum ready: lihat TODO.)"
    )

    user_tz = pytz_timezone(getattr(settings, "DEFAULT_LOG_TIMEZONE", "Asia/Jakarta"))

    def log(self, message):
        timestamp = (
            timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        )
        log_line = f"{timestamp}: {message}"
        print(log_line, flush=True)
        log_file = "/var/log/hiveforest/fetch_stftp_db.log"
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

    def add_arguments(self, parser):
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID yang melakukan import"
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Tanggal tunggal (YYMMDD, mis. 260719). Default: hari ini.",
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
        self.log(f"Fetch(DB) Started for user {cby_id} | {mode}")
        conn = None
        try:
            conn = self._connect()
            summary = self._run(conn, dates, cby_id, options["dry_run"])
            self.log(summary)
            return summary
        except Exception as e:
            self.log(f"Fetch(DB) Failed: {e}")
            raise
        finally:
            if conn is not None:
                conn.close()

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

    def _connect(self):
        """Konek MySQL DB sumber FTP dari ENV (pola load_stockdailymup)."""
        port_raw = os.getenv("DB_STFTP_PORT")
        try:
            port_int = int(port_raw) if port_raw else 3306
        except ValueError:
            raise CommandError(f"DB_STFTP_PORT tidak valid: {port_raw}")

        required = ["DB_STFTP_HOST", "DB_STFTP_USER", "DB_STFTP_PASSWORD", "DB_STFTP_DATABASE"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise CommandError(
                f"ENV MySQL sumber FTP belum lengkap: {', '.join(missing)}. "
                f"DB sumber belum ready?"
            )

        config = {
            "host": os.getenv("DB_STFTP_HOST"),
            "user": os.getenv("DB_STFTP_USER"),
            "password": os.getenv("DB_STFTP_PASSWORD"),
            "database": os.getenv("DB_STFTP_DATABASE"),
            "port": port_int,
        }
        try:
            return mysql.connector.connect(**config)
        except Exception as e:
            raise CommandError(f"Gagal konek MySQL sumber FTP: {e}")

    def _run(self, conn, dates, cby_id, dry_run):
        # Satu tanggal -> teruskan langsung (error diangkat, cron kelihatan merah).
        if len(dates) == 1:
            return self._fetch_one(conn, dates[0], cby_id, dry_run)

        # Backfill: per-hari; kegagalan satu hari tidak menghentikan yang lain.
        ok = skip = fail = 0
        for d in dates:
            try:
                result = self._fetch_one(conn, d, cby_id, dry_run)
                self.log(result)
                if result.startswith("SKIP"):
                    skip += 1
                else:
                    ok += 1
            except Exception as e:
                self.log(f"{d.strftime('%y%m%d')} -> GAGAL: {e}")
                fail += 1
        return (
            f"BACKFILL {dates[0]}..{dates[-1]}: ok={ok}, skip={skip}, gagal={fail} "
            f"(dari {len(dates)} hari)."
        )

    # ── Satu tanggal: query DB -> DataFrame -> temp CSV -> import ─────────────
    def _fetch_one(self, conn, target, cby_id, dry_run):
        yymmdd = target.strftime("%y%m%d")
        rows = self._query_rows(conn, yymmdd)
        if not rows:
            # DB tak punya baris tanggal ini -> tidak diimport, cukup dicatat.
            return f"SKIP {yymmdd}: tidak ada baris di DB sumber utk tanggal ini."

        df = pd.DataFrame(rows)
        with tempfile.TemporaryDirectory(prefix="fetch_stftp_db_") as tmpdir:
            csv_path = os.path.join(tmpdir, f"st{yymmdd}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
            self.log(f"{yymmdd}: {len(df)} baris dari DB sumber -> CSV")

            # Import ke DB (reuse load_excel_stftp -- transform sama dgn jalur file).
            summary = call_command(
                "load_excel_stftp", file=csv_path, cby=cby_id, dry_run=dry_run
            )
            return f"{yymmdd} -> {summary}"

    def _query_rows(self, conn, yymmdd):
        """SELECT baris stok utk 1 tanggal dari DB sumber FTP.

        TODO(FTP-DB): skema DB sumber BELUM tersedia. Saat ready, sesuaikan:
          - `table`       : nama tabel sumber (via ENV DB_STFTP_TABLE).
          - `date_column` : kolom filter tanggal di tabel sumber.
          - `date_value`  : format nilai tanggalnya (di sini diasumsikan YYMMDD,
                            sama spt kolom `tgldata`/`periode` RawMUST).
          - Pastikan nama kolom hasil SELECT == header CSV / field RawMUST
            (periode, tgldata, kdcab, kodeprod, namaprod, klasprod, lot, ...).
            Kalau beda -> alias di SELECT (mis. `SELECT kolom_asli AS kdcab`).
        """
        table = os.getenv("DB_STFTP_TABLE", "st")   # TODO: nama tabel sumber
        date_column = "tgldata"                       # TODO: kolom filter tanggal
        date_value = yymmdd                           # TODO: format nilai tanggal

        query = f"SELECT * FROM {table} WHERE {date_column} = %s"  # TODO: sesuaikan
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, (date_value,))
            return cursor.fetchall()
        finally:
            cursor.close()
