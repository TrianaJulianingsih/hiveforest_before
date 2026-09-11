from datetime import datetime, timedelta
from decimal import Decimal
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from django.utils.timezone import now
from pytz import timezone as pytz_timezone

# ═══════════════════════════════════════════════════════════
# Reconciliation check (read-only)
#
#   layer 1 : siap_mup.do  →  sales_rawmuso
#   layer 2 : sales_rawmuso →  sales_sellingout
#
#   ex. command:
#       python manage.py check_so_reconciliation --date-from 2025-06-01 --date-to 2025-12-31
#       python manage.py check_so_reconciliation --days-back 40
#       python manage.py check_so_reconciliation --date-from 2025-06-01 --date-to 2025-12-31 --only-mismatch
#
#   Tanpa argumen tanggal sama sekali, rentang mengikuti pola load_rawmusomup:
#       tgl 1-10  → mundur RAWMUSO_DAYS_BACK (default 40) hari
#       tgl 11+   → dari awal bulan berjalan
# ═══════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)

DISTRIBUTOR_ID = 1
HRDOK_VALID = r"hrdok ~ '^[0-9]{8}$'"
MONTH_THRESHOLD_DAYS = 31
LOG_FILE = "/var/log/hiveforest/check_so_reconciliation.log"

DISTRIBUTOR_CONFIG = {
    "mup": {
        "label": "MUP",
        "id": 1,
        "source_table": "siap_mup.do",
        "source_label": "siap_mup.do",
        "source_date_column": "HRDOK",
        "source_date_mode": "yyyymmdd",
        "source_env_prefix": "DB_MUP",
        "raw_table": "sales_rawmuso",
        "raw_label": "sales_rawmuso",
        "raw_date_column": "hrdok",
        "raw_columns": {
            "qty": "banyak",
            "thna": "thna",
        },
        "combine_procedure": "combine_so_rawmuso",
    },
    "apl": {
        "label": "APL",
        "id": 8,
        "source_table": "Sales",
        "source_label": "APL.Sales",
        "source_date_column": "HRDOK",
        "source_date_mode": "date",
        "source_env_prefix": "DB_APL",
        "raw_table": "sales_rawaplso",
        "raw_label": "sales_rawaplso",
        "raw_date_column": "tanggal",
        "raw_columns": {
            "qty": "qty",
            "thna": "thna",
        },
        "combine_procedure": "combine_so_rawaplso",
    },
}

# Metrik yang bisa dibandingkan (nama kolomnya beda tiap tabel):
#   qty  -> DO.BANYAK | rawmuso.banyak | sellingout.qty
#   thna -> DO.THNA   | rawmuso.thna   | sellingout.grossvalue
METRICS = {
    "qty": {
        "do": "BANYAK", "raw": "banyak", "so": "qty",
        "decimal": False, "label": "qty (banyak / qty)",
    },
    "thna": {
        "do": "THNA", "raw": "thna", "so": "grossvalue",
        "decimal": True, "label": "thna (grossvalue)",
    },
}


# Style Helper
def _fmt(n):
    if n is None:
        return "-"
    return f"{n:,}".replace(",", ".")


def _fmt_signed(n):
    if n is None:
        return "-"
    return f"{'+' if n > 0 else ''}{_fmt(n)}"


class Command(BaseCommand):
    help = (
        "Cek rekonsiliasi source → raw → sales_sellingout. "
        "Read-only. Default menjalankan kedua layer secara sekuensial."
    )

    user_tz = pytz_timezone(getattr(settings, "DEFAULT_LOG_TIMEZONE", "Asia/Jakarta"))

    # ── Output helper ───────────────────────────────────────
    # Semua tulisan lewat _w(): tampil di terminal (berwarna) sekaligus
    # tercatat ke file log (polos, tanpa ANSI escape).

    def _w(self, message="", style=None):
        self.stdout.write(style(message) if style else message)
        self._log_buffer.append(message)

    def _flush_log(self, exit_code):
        if not self._log_buffer:
            return
        stamp = timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        status = "MISMATCH" if exit_code else "OK"
        header = f"{stamp}: ═══ RUN {status} ═══"
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(header + "\n")
                for line in self._log_buffer:
                    f.write(line + "\n")
                f.write("\n")
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: Could not write to log file {LOG_FILE}: {e}"
                )
            )

    # ── Arguments ───────────────────────────────────────────

    def add_arguments(self, parser):
        parser.add_argument("--date-from", type=str, help="Tanggal awal (YYYY-MM-DD)")
        parser.add_argument("--date-to", type=str, help="Tanggal akhir (YYYY-MM-DD)")
        parser.add_argument(
            "--days-back",
            type=int,
            default=None,
            help=(
                "Mundur N hari dari hari ini. Bila tidak diisi, rentang mengikuti "
                "pola load_rawmusomup (tgl 1-10 → 40 hari, tgl 11+ → awal bulan)."
            ),
        )
        parser.add_argument(
            "--layer1",
            action="store_true",
            help="Jalankan HANYA layer 1 (siap_mup.do → sales_rawmuso)",
        )
        parser.add_argument(
            "--layer2",
            action="store_true",
            help="Jalankan HANYA layer 2 (sales_rawmuso → sales_sellingout)",
        )
        parser.add_argument(
            "--only-mismatch",
            action="store_true",
            help="Tampilkan hanya periode yang selisihnya != 0",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help=(
                "Hanya keluarkan output bila ditemukan mismatch. "
                "Cocok untuk cron agar log tidak penuh baris OK."
            ),
        )
        parser.add_argument(
            "--log-file",
            action="store_true",
            help=(
                f"Tulis juga ke {LOG_FILE} (default: hanya stdout, konsisten dgn "
                f"command lain; di cron biarkan redirect '>> file' yang menulis)."
            ),
        )
        parser.add_argument(
            "--metric",
            choices=list(METRICS.keys()),
            default="qty",
            help="Field yang dibandingkan: qty (banyak) atau thna (grossvalue). Default: qty.",
        )
        parser.add_argument(
            "--distributor",
            choices=list(DISTRIBUTOR_CONFIG.keys()),
            default="mup",
            help="Distributor yang dicek: mup atau apl. Default: mup.",
        )

    # ── Entry point ─────────────────────────────────────────

    def handle(self, *args, **options):
        self._log_buffer = []
        self._summary = {}
        self._distributor = options["distributor"]
        self._cfg = DISTRIBUTOR_CONFIG[self._distributor]
        self._metric_name = options["metric"]
        self._m = METRICS[options["metric"]]  # kolom & tipe metrik yang dibandingkan

        if self._distributor == "apl" and options["metric"] != "qty":
            raise CommandError(
                "Untuk distributor APL saat ini hanya metric qty yang didukung."
            )

        if options["layer1"] and options["layer2"]:
            raise CommandError(
                "--layer1 dan --layer2 tidak bisa dipakai bersamaan. "
                "Tanpa flag apa pun, keduanya sudah dijalankan sekuensial."
            )

        # Mode quiet: tahan output, keluarkan hanya bila mismatch.
        quiet = options["quiet"]
        real_stdout = self.stdout
        if quiet:
            from io import StringIO
            from django.core.management.base import OutputWrapper

            self.stdout = OutputWrapper(StringIO())

        exit_code = 0
        try:
            exit_code = self._run(options)
        except SystemExit as e:
            exit_code = e.code if isinstance(e.code, int) else 1
        finally:
            # Header + timestamp dicetak ke STDOUT juga, supaya redirect cron
            # (>> file) menangkap jejak kapan run-nya jalan & status-nya, bukan
            # cuma isinya. Jadi log dari cron sama lengkapnya dgn self-log.
            stamp = timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
            run_header = f"{stamp}: ═══ RUN {'MISMATCH' if exit_code else 'OK'} ═══"
            if quiet:
                buffered = self.stdout._out.getvalue()
                self.stdout = real_stdout
                self.stdout.write(run_header)
                if exit_code:
                    self.stdout.write(buffered)
                else:
                    # Tetap beri jejak walau tidak ada masalah, supaya
                    # terlihat bahwa pengecekan memang berjalan hari itu.
                    self.stdout.write(self.style.SUCCESS(self._summary_line()))
            else:
                self.stdout.write(run_header)
            self.stdout.write("")  # pemisah antar-run di file log
            if options["log_file"]:
                if quiet and not exit_code:
                    self._log_buffer = [self._summary_line()]
                self._flush_log(exit_code)

        if exit_code:
            raise SystemExit(exit_code)

    def _summary_line(self):
        """Ringkasan satu baris — dipakai di mode --quiet ketika semuanya OK,
        supaya log harian tetap punya bukti bahwa pengecekan berjalan."""
        s = self._summary
        periode = s.get("periode", "-")
        parts = [f"OK — {periode}"]
        if "l1_left" in s:
            parts.append(
                f"L1 {self._cfg['source_label']}={_fmt(s['l1_left'])}="
                f"{self._cfg['raw_label']}={_fmt(s['l1_right'])}"
            )
        if "l2_left" in s:
            parts.append(
                f"L2 {self._cfg['raw_label']}={_fmt(s['l2_left'])}="
                f"so={_fmt(s['l2_right'])}"
            )
        parts.append("diff=0")
        return " | ".join(parts)

    def _run(self, options):
        date_from, date_to = self._resolve_range(options)
        span_days = (date_to - date_from).days + 1
        granularity = "month" if span_days > MONTH_THRESHOLD_DAYS else "day"

        run_l1 = not options["layer2"]
        run_l2 = not options["layer1"]
        sequential = run_l1 and run_l2

        self._summary["periode"] = f"{date_from} s/d {date_to}"

        self._header(date_from, date_to, span_days, granularity, run_l1, run_l2)

        exit_code = 0

        # ── layer 1 ─────────────────────────────────────────
        if run_l1:
            try:
                layer1 = self._check_source_to_raw(date_from, date_to)
            except Exception as e:
                logger.error("layer 1 (source→raw) gagal dijalankan: %s", e)
                self._w(
                    f"\n── layer 1: {self._cfg['source_label']} → "
                    f"{self._cfg['raw_label']} ──\n  GAGAL — "
                    f"{e}",
                    self.style.ERROR,
                )
                if sequential:
                    self._w(
                        "\nProses dihentikan. Perbaiki akses/kondisi sumber "
                        "dulu, atau jalankan ulang dengan --layer2 bila "
                        "ingin memeriksa layer 2 saja.\n",
                        self.style.WARNING,
                    )
                return 2

            self._render_layer1(layer1)
            self._summary["l1_left"] = layer1["qty_left"]
            self._summary["l1_right"] = layer1["qty_right"]

            rows1 = self._per_period_layer1(layer1, granularity)
            self._render_periods_layer1(rows1, options["only_mismatch"], granularity)

            if layer1["diff"] != 0:
                exit_code = 1
                logger.error(
                    "layer 1 MISMATCH %s s/d %s: do=%s raw=%s diff=%s",
                    date_from,
                    date_to,
                    layer1["qty_left"],
                    layer1["qty_right"],
                    layer1["diff"],
                )
                if sequential:
                    self._w(
                        "\nProses dihentikan di layer 1. Selisih di tahap "
                        "import harus dibereskan lebih dulu — menilai layer 2 "
                        "di atas data yang belum lengkap hanya akan "
                        "menyesatkan.\n"
                        "Bila tetap ingin melihat layer 2, jalankan dengan "
                        "--layer2.",
                        self.style.WARNING,
                    )
                    self._w(f"\nExit code: {exit_code}")
                    return exit_code

        # ── layer 2 ─────────────────────────────────────────
        if run_l2:
            layer2 = self._check_raw_to_so(date_from, date_to)
            breakdown = self._breakdown(date_from, date_to)
            self._render_layer2(layer2, breakdown)
            self._summary["l2_left"] = layer2["qty_left"]
            self._summary["l2_right"] = layer2["qty_right"]

            if layer2["diff"] != 0:
                exit_code = 1
                logger.error(
                    "layer 2 MISMATCH %s s/d %s: raw=%s so=%s diff=%s",
                    date_from,
                    date_to,
                    layer2["qty_left"],
                    layer2["qty_right"],
                    layer2["diff"],
                )

            rows = self._per_period(date_from, date_to, granularity)
            self._render_periods(rows, options["only_mismatch"], granularity)
            self._render_saran(rows, breakdown)

        self._w(f"\nExit code: {exit_code}")
        return exit_code

    # ── Helpers ─────────────────────────────────────────────

    def _resolve_range(self, options):
        df, dt_ = options.get("date_from"), options.get("date_to")

        def parse(s, label):
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                raise CommandError(f"Format {label} salah (harus YYYY-MM-DD): {s}")

        if df or dt_:
            if not (df and dt_):
                raise CommandError("--date-from dan --date-to harus diisi berpasangan")
            date_from, date_to = parse(df, "--date-from"), parse(dt_, "--date-to")
            if date_from > date_to:
                raise CommandError("--date-from tidak boleh setelah --date-to")
            return date_from, date_to

        today = now().date()

        # --days-back eksplisit menang atas pola default
        if options.get("days_back") is not None:
            return today - timedelta(days=options["days_back"]), today

        # Ikuti pola load_rawmusomup: tgl 1-10 mundur N hari, tgl 11+ awal bulan
        try:
            days_back = int(os.getenv("RAWMUSO_DAYS_BACK", "40"))
        except (TypeError, ValueError):
            days_back = 40

        if today.day <= 10:
            return today - timedelta(days=days_back), today
        return today.replace(day=1), today

    def _fetchone(self, sql, params):
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    # ── Ekspresi kolom per metrik ───────────────────────────
    # Kolomnya beda tiap tabel (lihat METRICS). DO = MySQL, rawmuso/sellingout = PG.

    def _do_sum(self):  # ekspresi utk di-SUM di source MySQL
        m = self._m
        return f"CAST({m['do']} AS {'DECIMAL(30,4)' if m['decimal'] else 'SIGNED'})"

    def _raw_col(self, prefix=""):  # kolom raw source (PG), optional alias
        m = self._m
        raw_column = self._cfg["raw_columns"][self._metric_name]
        return f"{prefix}{raw_column}::{'NUMERIC' if m['decimal'] else 'BIGINT'}"

    def _so_col(self, prefix=""):  # kolom sellingout (PG)
        return f"{prefix}{self._m['so']}"

    def _raw_valid(self, prefix=""):
        column = f"{prefix}{self._cfg['raw_date_column']}"
        return f"{column} ~ '^[0-9]{{8}}$'"

    def _raw_date_expr(self, prefix=""):
        column = f"{prefix}{self._cfg['raw_date_column']}"
        return f"TO_DATE({column}, 'YYYYMMDD')"

    @staticmethod
    def _normalize_period_key(value):
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y%m%d")

        value = str(value).strip()
        if len(value) == 10 and value[4] == "-" and value[7] == "-":
            return value.replace("-", "")
        return value.replace("-", "").replace("/", "")

    def _num(self, v):  # cast hasil SUM ke tipe yang tepat (int / Decimal)
        return Decimal(str(v or 0)) if self._m["decimal"] else int(v or 0)

    # ── layer 1: siap_mup.do → sales_rawmuso ────────────────

    def _apl_latest_source_cte(self, do_sum, source_date_column):
        """Build the APL source query using latest LOG_DATE per composite key."""
        return f"""
            WITH ranked AS (
                SELECT
                    {source_date_column} AS source_date,
                    {do_sum} AS qty,
                    TRIM(COALESCE(NODOKJDI, '')) AS nodokjdi,
                    TRIM(COALESCE(BATCH, '')) AS batch,
                    TRIM(COALESCE(KODE_SALES, '')) AS kode_sales,
                    LOG_DATE,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            TRIM(COALESCE(NODOKJDI, '')),
                            TRIM(COALESCE(BATCH, '')),
                            TRIM(COALESCE(KODE_SALES, ''))
                        ORDER BY (LOG_DATE IS NULL), LOG_DATE DESC
                    ) AS rn
                FROM {self._cfg['source_table']}
                WHERE {source_date_column} BETWEEN %s AND %s
            ), selected AS (
                SELECT source_date, qty
                FROM ranked
                WHERE rn = 1
            )
        """

    def _check_source_to_raw(self, date_from, date_to):
        import mysql.connector

        env_prefix = self._cfg["source_env_prefix"]
        required = [
            f"{env_prefix}_HOST",
            f"{env_prefix}_USER",
            f"{env_prefix}_PASSWORD",
            f"{env_prefix}_DATABASE",
        ]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise CommandError(f"Env MySQL belum lengkap: {', '.join(missing)}")

        cfg = {
            "host": os.getenv(f"{env_prefix}_HOST"),
            "user": os.getenv(f"{env_prefix}_USER"),
            "password": os.getenv(f"{env_prefix}_PASSWORD"),
            "database": os.getenv(f"{env_prefix}_DATABASE"),
            "port": int(os.getenv(f"{env_prefix}_PORT") or 3306),
        }

        conn = mysql.connector.connect(**cfg)
        try:
            cur = conn.cursor()
            do_sum = self._do_sum()
            source_table = self._cfg["source_table"]
            source_date_column = self._cfg["source_date_column"]
            if self._cfg["source_date_mode"] == "yyyymmdd":
                date_params = [
                    date_from.strftime("%Y%m%d"),
                    date_to.strftime("%Y%m%d"),
                ]
            else:
                date_params = [date_from, date_to]

            if self._distributor == "apl":
                cur.execute(
                    self._apl_latest_source_cte(do_sum, source_date_column)
                    + " SELECT COALESCE(SUM(qty), 0), COUNT(*) FROM selected",
                    date_params,
                )
            else:
                cur.execute(
                    f"SELECT COALESCE(SUM({do_sum}),0), COUNT(*) "
                    f"FROM {source_table} "
                    f"WHERE {source_date_column} BETWEEN %s AND %s",
                    date_params,
                )
            qty_source, rows_source = cur.fetchone()

            # Rincian per tanggal source
            if self._distributor == "apl":
                cur.execute(
                    self._apl_latest_source_cte(do_sum, source_date_column)
                    + " SELECT source_date, COALESCE(SUM(qty), 0) "
                    "FROM selected GROUP BY source_date",
                    date_params,
                )
            else:
                cur.execute(
                    f"SELECT {source_date_column}, COALESCE(SUM({do_sum}),0) "
                    f"FROM {source_table} "
                    f"WHERE {source_date_column} BETWEEN %s AND %s "
                    f"GROUP BY {source_date_column}",
                    date_params,
                )
            source_by_hrdok = {
                self._normalize_period_key(h): self._num(q)
                for h, q in cur.fetchall()
                if h
            }
            cur.close()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        raw_table = self._cfg["raw_table"]
        raw_valid = self._raw_valid()
        raw_date_expr = self._raw_date_expr()
        raw_date_column = self._cfg["raw_date_column"]
        raw_sum = f"SUM({self._raw_col()})"
        qty_raw, rows_raw = self._fetchone(
            f"""
            SELECT COALESCE({raw_sum},0), COUNT(*)
            FROM {raw_table}
            WHERE {raw_valid}
              AND {raw_date_expr} BETWEEN %s AND %s
              AND status = 1 AND deleted = false
            """,
            [date_from, date_to],
        )

        # Rincian raw per tanggal (dinormalisasi agar sebanding dengan source)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {raw_date_column}, COALESCE({raw_sum},0)
                FROM {raw_table}
                WHERE {raw_valid}
                  AND {raw_date_expr} BETWEEN %s AND %s
                  AND status = 1 AND deleted = false
                GROUP BY {raw_date_column}
                """,
                [date_from, date_to],
            )
            raw_by_hrdok = {
                self._normalize_period_key(h): self._num(q)
                for h, q in cursor.fetchall()
                if h
            }

        qty_source, qty_raw = self._num(qty_source), self._num(qty_raw)
        return {
            "qty_left": qty_source,
            "qty_right": qty_raw,
            "rows_left": rows_source or 0,
            "rows_right": rows_raw or 0,
            "diff": qty_source - qty_raw,
            "source_by_hrdok": source_by_hrdok,
            "raw_by_hrdok": raw_by_hrdok,
        }

    def _per_period_layer1(self, layer1, granularity):
        """Gabungkan agregat sumber & rawmuso per periode (dilakukan di Python
        karena kedua sisi berasal dari server database yang berbeda)."""
        src = layer1.get("source_by_hrdok") or {}
        raw = layer1.get("raw_by_hrdok") or {}

        def bucket(hrdok):
            if granularity == "month":
                return f"{hrdok[:4]}-{hrdok[4:6]}"
            return f"{hrdok[:4]}-{hrdok[4:6]}-{hrdok[6:8]}"

        agg = {}
        for hrdok, qty in src.items():
            if len(hrdok) != 8 or not hrdok.isdigit():
                continue
            agg.setdefault(bucket(hrdok), [0, 0])[0] += qty
        for hrdok, qty in raw.items():
            if len(hrdok) != 8 or not hrdok.isdigit():
                continue
            agg.setdefault(bucket(hrdok), [0, 0])[1] += qty

        return [
            (periode, vals[0], vals[1], vals[0] - vals[1])
            for periode, vals in sorted(agg.items())
        ]

    # ── layer 2: sales_rawmuso → sales_sellingout ───────────

    def _check_raw_to_so(self, date_from, date_to):
        raw_table = self._cfg["raw_table"]
        qty_raw, rows_raw = self._fetchone(
            f"""
            SELECT COALESCE(SUM({self._raw_col()}),0), COUNT(*)
            FROM {raw_table}
            WHERE {self._raw_valid()}
              AND {self._raw_date_expr()} BETWEEN %s AND %s
              AND status = 1 AND deleted = false
            """,
            [date_from, date_to],
        )

        qty_so, rows_so = self._fetchone(
            f"""
            SELECT COALESCE(SUM({self._so_col()}),0), COUNT(*)
            FROM sales_sellingout
            WHERE distributor_id = %s
              AND invoice_date BETWEEN %s AND %s
            AND status = 1 AND deleted = false
            """,
            [self._cfg["id"], date_from, date_to],
        )

        qty_raw, qty_so = self._num(qty_raw), self._num(qty_so)
        return {
            "qty_left": qty_raw,
            "qty_right": qty_so,
            "rows_left": rows_raw or 0,
            "rows_right": rows_so or 0,
            "diff": qty_raw - qty_so,
        }

    # ── Penguraian penyebab ─────────────────────────────────

    def _breakdown(self, date_from, date_to):
        raw_table = self._cfg["raw_table"]
        missing_qty, missing_rows = self._fetchone(
            f"""
            SELECT COALESCE(SUM({self._raw_col('r.')}),0), COUNT(*)
            FROM {raw_table} r
            WHERE {self._raw_valid('r.')}
              AND {self._raw_date_expr('r.')} BETWEEN %s AND %s
              AND r.status = 1 AND r.deleted = false
              AND NOT EXISTS (
                  SELECT 1 FROM sales_sellingout so
                  WHERE so.raw_id = r.id
                    AND so.distributor_id = %s
                    AND so.status = 1 AND so.deleted = false
              )
            """,
            [date_from, date_to, self._cfg["id"]],
        )

        orphan_qty, orphan_rows = self._fetchone(
            f"""
            SELECT COALESCE(SUM(ss.qty),0), COUNT(*)
            FROM sales_sellingout ss
            WHERE ss.distributor_id = %s
              AND ss.invoice_date BETWEEN %s AND %s
              AND ss.status = 1 AND ss.deleted = false
              AND NOT EXISTS (
                  SELECT 1 FROM {raw_table} r WHERE r.id = ss.raw_id
              )
            """,
            [self._cfg["id"], date_from, date_to],
        )

        inactive_qty, inactive_rows = self._fetchone(
            f"""
            SELECT COALESCE(SUM(ss.qty),0), COUNT(*)
            FROM sales_sellingout ss
            JOIN {raw_table} r ON r.id = ss.raw_id
            WHERE ss.distributor_id = %s
              AND ss.invoice_date BETWEEN %s AND %s
              AND ss.status = 1 AND ss.deleted = false
              AND (r.status != 1 OR r.deleted = true)
            """,
            [self._cfg["id"], date_from, date_to],
        )

        return {
            "missing_qty": int(missing_qty or 0),
            "missing_rows": missing_rows or 0,
            "orphan_qty": int(orphan_qty or 0),
            "orphan_rows": orphan_rows or 0,
            "inactive_qty": int(inactive_qty or 0),
            "inactive_rows": inactive_rows or 0,
        }

    # ── Rincian per periode ─────────────────────────────────

    def _per_period(self, date_from, date_to, granularity):
        raw_table = self._cfg["raw_table"]
        raw_date_expr = self._raw_date_expr("r.")
        raw_valid = self._raw_valid("r.")
        if granularity == "month":
            bucket_raw = f"DATE_TRUNC('month', {raw_date_expr})::date"
            bucket_so = "DATE_TRUNC('month', ss.invoice_date)::date"
        else:
            bucket_raw = raw_date_expr
            bucket_so = "ss.invoice_date"

        # Dihitung lewat CTE + hash join, bukan correlated subquery per baris,
        # supaya tidak meledak di rentang lebar.
        sql = f"""
        WITH so_all AS (
            SELECT ss.raw_id, {bucket_so} AS periode, {self._so_col('ss.')} AS qty
            FROM sales_sellingout ss
            WHERE ss.distributor_id = %s
              AND ss.invoice_date BETWEEN %s AND %s
              AND ss.status = 1 AND ss.deleted = false
        ),
        so_linked AS (
            SELECT DISTINCT raw_id FROM so_all WHERE raw_id IS NOT NULL
        ),
        raw_all AS (
            SELECT r.id, {bucket_raw} AS periode, {self._raw_col('r.')} AS qty
            FROM {raw_table} r
            WHERE {raw_valid}
              AND {raw_date_expr} BETWEEN %s AND %s
              AND r.status = 1 AND r.deleted = false
        ),
        raw_agg AS (
            SELECT ra.periode,
                   SUM(ra.qty) AS qty,
                   SUM(CASE WHEN sl.raw_id IS NULL THEN ra.qty ELSE 0 END)
                       AS qty_missing
            FROM raw_all ra
            LEFT JOIN so_linked sl ON sl.raw_id = ra.id
            GROUP BY 1
        ),
        so_agg AS (
            SELECT sa.periode,
                   SUM(sa.qty) AS qty,
                   SUM(CASE WHEN r.id IS NULL THEN sa.qty ELSE 0 END) AS qty_orphan
            FROM so_all sa
            LEFT JOIN {raw_table} r ON r.id = sa.raw_id
            GROUP BY 1
        )
        SELECT COALESCE(raw_agg.periode, so_agg.periode) AS periode,
               COALESCE(raw_agg.qty,0) AS qty_raw,
               COALESCE(so_agg.qty,0)  AS qty_so,
               COALESCE(raw_agg.qty,0) - COALESCE(so_agg.qty,0) AS diff,
               COALESCE(raw_agg.qty_missing,0) AS qty_missing,
               COALESCE(so_agg.qty_orphan,0)   AS qty_orphan
        FROM raw_agg
        FULL OUTER JOIN so_agg ON so_agg.periode = raw_agg.periode
        ORDER BY 1
        """
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [
                    self._cfg["id"],
                    date_from,
                    date_to,
                    date_from,
                    date_to,
                ]
            )
            return cursor.fetchall()

    # ── Rendering ───────────────────────────────────────────

    def _header(self, date_from, date_to, span_days, granularity, run_l1, run_l2):
        if run_l1 and run_l2:
            layer = "1 → 2 (sekuensial)"
        elif run_l1:
            layer = "1 saja"
        else:
            layer = "2 saja"

        self._w("\n═══ RECONCILIATION CHECK ═══")
        self._w(f"Periode     : {date_from} s/d {date_to} ({span_days} hari)")
        self._w(
            f"Distributor : {self._cfg['label']} ({self._cfg['id']})"
        )
        self._w(f"layer       : {layer}")
        self._w(
            f"Rincian     : per {'bulan' if granularity == 'month' else 'tanggal'}"
            + (
                f" (otomatis, rentang > {MONTH_THRESHOLD_DAYS} hari)"
                if granularity == "month"
                else ""
            )
        )

    def _render_layer1(self, r):
        ok = r["diff"] == 0
        status = "✓ OK" if ok else "✗ MISMATCH"
        source_value_label = "do" if self._distributor == "mup" else "source"
        self._w(
            f"\n── layer 1: {self._cfg['source_label']} → "
            f"{self._cfg['raw_label']} ──"
        )
        self._w(
            f"  {source_value_label}={_fmt(r['qty_left'])}  "
            f"raw={_fmt(r['qty_right'])}  "
            f"diff={_fmt_signed(r['diff'])}   {status}",
            self.style.SUCCESS if ok else self.style.ERROR,
        )
        if r["diff"] > 0:
            self._w(
                f"  arah: {self._cfg['raw_label']} KEKURANGAN — "
                "ada baris sumber yang belum ter-import."
            )
        elif r["diff"] < 0:
            self._w(
                f"  arah: {self._cfg['raw_label']} KELEBIHAN — "
                "kemungkinan baris sudah dihapus/diubah di source "
                f"tapi masih aktif di {self._cfg['raw_label']}."
            )

    def _render_periods_layer1(self, rows, only_mismatch, granularity):
        shown = [r for r in rows if (not only_mismatch or r[3] != 0)]
        label = " (mismatch saja)" if only_mismatch else ""
        satuan = "BULAN" if granularity == "month" else "TANGGAL"
        self._w(f"\n  ── layer 1 — RINCIAN PER {satuan}{label} ──")

        if not shown:
            self._w("    (tidak ada periode yang perlu ditampilkan)")
            return

        source_qty_label = "QTY_DO" if self._distributor == "mup" else "QTY_SOURCE"
        self._w(
            f"    {'PERIODE':<12}{source_qty_label:>16}"
            f"{'QTY_RAW':>16}{'DIFF':>14}"
        )
        for periode, qty_src, qty_raw, diff in shown:
            line = (
                f"    {periode:<12}{_fmt(qty_src):>16}{_fmt(qty_raw):>16}"
                f"{_fmt_signed(diff):>14}"
            )
            self._w(line, self.style.ERROR if diff else None)

    def _render_layer2(self, r, b):
        ok = r["diff"] == 0
        status = "✓ OK" if ok else "✗ MISMATCH"
        self._w(
            f"\n── layer 2: {self._cfg['raw_label']} → "
            "sales_sellingout ──"
        )
        self._w(
            f"  raw={_fmt(r['qty_left'])}  so={_fmt(r['qty_right'])}  "
            f"diff={_fmt_signed(r['diff'])}   {status}",
            self.style.SUCCESS if ok else self.style.ERROR,
        )
        self._w(
            f"    ├─ raw aktif tanpa SO   : {_fmt(b['missing_qty']):>12} qty / "
            f"{_fmt(b['missing_rows'])} baris"
        )
        self._w(
            f"    ├─ SO orphan (raw_id ✗) : {_fmt(b['orphan_qty']):>12} qty / "
            f"{_fmt(b['orphan_rows'])} baris"
        )
        self._w(
            f"    ├─ SO dari raw nonaktif : {_fmt(b['inactive_qty']):>12} qty / "
            f"{_fmt(b['inactive_rows'])} baris"
        )

        expected = b["missing_qty"] - b["orphan_qty"] - b["inactive_qty"]
        sisa = r["diff"] - expected
        if sisa == 0:
            self._w(
                f"    └─ balance check        : OK ({_fmt(b['missing_qty'])} − "
                f"{_fmt(b['orphan_qty'])} − {_fmt(b['inactive_qty'])} = "
                f"{_fmt_signed(r['diff'])})"
            )
        else:
            self._w(
                f"    └─ balance check        : TIDAK BALANCE — "
                f"{_fmt_signed(sisa)} qty belum terjelaskan. Kemungkinan ada "
                f"baris SO yang qty-nya berbeda dari raw-nya.",
                self.style.WARNING,
            )

    def _render_periods(self, rows, only_mismatch, granularity):
        shown = [r for r in rows if (not only_mismatch or r[3] != 0)]
        label = " (mismatch saja)" if only_mismatch else ""
        satuan = "BULAN" if granularity == "month" else "TANGGAL"
        self._w(f"\n── RINCIAN PER {satuan}{label} ──")

        if not shown:
            self._w("  (tidak ada periode yang perlu ditampilkan)")
            return

        self._w(
            f"  {'PERIODE':<12}{'QTY_RAW':>14}{'QTY_SO':>14}"
            f"{'DIFF':>14}{'MISSING':>12}{'ORPHAN':>12}"
        )
        for periode, qty_raw, qty_so, diff, missing, orphan in shown:
            line = (
                f"  {str(periode):<12}{_fmt(qty_raw):>14}{_fmt(qty_so):>14}"
                f"{_fmt_signed(diff):>14}{_fmt(missing):>12}{_fmt(orphan):>12}"
            )
            self._w(line, self.style.ERROR if diff else None)

    def _render_saran(self, rows, b):
        saran = []
        bermasalah = [r[0] for r in rows if r[4] > 0]
        if bermasalah:
            saran.append(
                f"{len(bermasalah)} periode punya raw tanpa SO. Backfill:\n"
                f"      CALL {self._cfg['combine_procedure']} "
                f"('{min(bermasalah)}', '{max(bermasalah)}', 1);"
            )
        if b["orphan_qty"] > 0:
            saran.append(
                f"{_fmt(b['orphan_rows'])} baris SO orphan ({_fmt(b['orphan_qty'])} "
                f"qty) perlu cleanup — soft-delete SO yang raw_id-nya tidak ada. "
                f"WAJIB pakai filter distributor_id = {self._cfg['id']}."
            )
        if b["inactive_qty"] > 0:
            saran.append(
                f"{_fmt(b['inactive_rows'])} baris SO berasal dari raw nonaktif — "
                f"propagasi flag deleted gagal, perlu ditinjau."
            )

        self._w("\n── SARAN ──")
        if not saran:
            self._w("  Tidak ada tindakan yang diperlukan. Data sinkron.")
        else:
            for s in saran:
                self._w(f"  • {s}")
