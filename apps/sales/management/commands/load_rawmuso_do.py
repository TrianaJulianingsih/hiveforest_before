from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from apps.sales.models.sales_models import RawMUSO
from apps.base.models.entities import Company
import mysql.connector
from mysql.connector import errors as mysql_errors
import logging
import os
from decimal import Decimal, InvalidOperation

from django.db import connection, IntegrityError
from django.conf import settings


# ═══════════════════════════════════════════════════════════
# FaisalS | HF-10 | MUP Selling Out raw data auto import
# ═══════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)



NUMERIC_FIELDS = {
    "banyak": int,
    "banys": int,
    "hna": Decimal,
    "harga": Decimal,
    "tharga": Decimal,
    "thna": Decimal,
    "ehna": Decimal,
    "prsnpot": Decimal,
    "pharga": Decimal,
    "prsnbp": Decimal,
    "prsnbmp": Decimal,
}

COLUMN_MAPPING = {
    "WHSE": "whse",
    "NO_ORDER": "no_order",
    "NODOKJDI": "nodokjdi",
    "HRDOK": "hrdok",
    "AREA": "area",
    "KODEPOS": "kodepos",
    "GRUPLANG": "gruplang",
    "KODELANG": "kodelang",
    "KDCUST": "kdcust",
    "NMLANG": "nmlang",
    "ALMTLANG": "almtlang",
    "KODESALUR": "kodesalur",
    "KODEPROD": "kodeprod",
    "NMPROD": "nmprod",
    "KLASPROD": "klasprod",
    "NMKLAS1": "nmklas1",
    "NMKLAS2": "nmklas2",
    "BANYAK": "banyak",
    "HNA": "hna",
    "HARGA": "harga",
    "THARGA": "tharga",
    "THNA": "thna",
    "BANYS": "banys",
    "EHNA": "ehna",
    "PRSNPOT": "prsnpot",
    "PHARGA": "pharga",
    "PRSNBP": "prsnbp",
    "PRSNBMP": "prsnbmp",
    "MOM": "mom",
    "NOBAT": "nobat",
    "DUN": "dun",
    "IDPKT": "idpkt",
}


def _clean_numeric(val, caster):
    if val in (None, "", " ", "NULL", "null", "NaN", "nan", "-", "None"):
        if caster is int:
            return 0
        return None
    try:
        if caster is int:
            return int(str(val).strip().split(".")[0])
        return caster(str(val).strip())
    except (ValueError, InvalidOperation):
        return 0 if caster is int else None


def _zero_pad(value: str, width: int) -> str:
    if value is None:
        return ""
    v = str(value).strip()
    if v.isdigit():
        return f"{int(v):0{width}d}"
    return v


def _calculate_pharga(thna, tharga):
    thna_value = thna if thna is not None else Decimal("0")
    tharga_value = tharga if tharga is not None else Decimal("0")
    return thna_value - tharga_value


def _normalize_decimal_key(value):
    if value in (None, "", "NULL", "null"):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _build_validation_key(entry):
    return (
        entry.get("hrdok", ""),
        entry.get("whse", ""),
        entry.get("nodokjdi", ""),
        entry.get("kodeprod", ""),
        entry.get("nobat", ""),
        _normalize_decimal_key(entry.get("hna")),
        _normalize_decimal_key(entry.get("harga")),
        int(entry.get("banyak") or 0),
        int(entry.get("banys") or 0),
    )


def generate_code(
    hrdok, whse, nodokjdi, kodeprod, nobat, hna, harga, banyak, banys, mom
):
    whse_str = _zero_pad(whse, 3)
    nodokjdi_str = _zero_pad(nodokjdi, 7)
    mom_raw = str(mom).strip() if mom else "NA"
    mom_str = _zero_pad(mom_raw, 3) if mom_raw.isdigit() else mom_raw
    hna_value = str(hna) if hna not in [None, "", "NULL"] else "0"
    harga_value = str(harga) if harga not in [None, "", "NULL"] else "0"
    banys_value = str(banys) if banys not in [None, "", "NULL"] else "0"
    return f"{hrdok}-{whse_str}-{nodokjdi_str[-7:]}-{kodeprod}-{nobat}-{hna_value}-{harga_value}-{banyak}-{banys_value}-{mom_str}"


class Command(BaseCommand):
    help = "Import / upsert RawMUSO records from MySQL siap_mup.do"

    def add_arguments(self, parser):
        parser.add_argument("--cby", type=int, required=True, help="User ID (creator)")
        parser.add_argument(
            "--dry-run", action="store_true", help="Only show counts; no DB writes"
        )
        parser.add_argument(
            "--limit", type=int, help="Limit number of rows fetched from source"
        )
        parser.add_argument(
            "--months-back",
            type=int,
            help="Filter N bulan terakhir berdasarkan kolom tanggal (default dari env RAWMUSO_MONTHS_BACK atau 1)",
        )
        parser.add_argument(
            "--days-back",
            type=int,
            help="Filter N hari terakhir berdasarkan kolom tanggal (overrides --months-back or env).",
        )
        parser.add_argument(
            "--date-from",
            type=str,
            help="Filter tanggal awal (YYYY-MM-DD). Jika diberikan bersama --date-to akan override months-back.",
        )
        parser.add_argument(
            "--date-to",
            type=str,
            help="Filter tanggal akhir (YYYY-MM-DD). Bisa dipakai sendiri atau dengan --date-from.",
        )
        parser.add_argument(
            "--date-col",
            type=str,
            help="Nama kolom tanggal di sumber (default env RAWMUSO_DATE_COLUMN atau HRDOK)",
        )
        parser.add_argument(
            "--no-date-filter",
            action="store_true",
            help="Matikan filter tanggal (ambil semua data)",
        )
        parser.add_argument(
            "--date-format",
            type=str,
            choices=["date", "datetime", "yyyymmdd"],
            help="Format kolom tanggal bila bukan tipe DATE/DATETIME; yyyymmdd akan pakai STR_TO_DATE",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Run validation checks only (no DB updates/deletes).",
        )

    def _auto_sync_mup(self, start_ts):
        today_str = now().date().strftime("%Y-%m-%d")
        sp_user_id = 1
        sp_name = "combine_so_rawmuso"

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CALL {sp_name}(%s, %s, %s)", [today_str, today_str, sp_user_id]
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{start_ts.strftime('%Y-%m-%d %H:%M:%S')} - Auto sync ke 'sales_sellingout' sukses: {sp_name}({today_str}, {today_str}, user_id={sp_user_id})"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"{start_ts.strftime('%Y-%m-%d %H:%M:%S')} - Auto sync ke 'sales_sellingout' gagal: {e}"
                )
            )

    def handle(self, *args, **options):
        cby_id = options["cby"]
        dry_run = options.get("dry_run", False)
        limit = options.get("limit")
        start_ts = now()

        port_raw = os.getenv("DB_MUP_PORT")
        try:
            port_int = int(port_raw) if port_raw else 3306
        except ValueError:
            raise CommandError(f"Invalid DB_MUP_PORT value: {port_raw}")

        required_keys = [
            "DB_MUP_HOST",
            "DB_MUP_USER",
            "DB_MUP_PASSWORD",
            "DB_MUP_DATABASE",
        ]
        missing = [k for k in required_keys if not os.getenv(k)]
        if missing:
            raise CommandError(f"Missing MySQL env vars: {', '.join(missing)}")

        mysql_config = {
            "host": os.getenv("DB_MUP_HOST"),
            "user": os.getenv("DB_MUP_USER"),
            "password": os.getenv("DB_MUP_PASSWORD"),
            "database": os.getenv("DB_MUP_DATABASE"),
            "port": port_int,
        }

        try:
            conn = mysql.connector.connect(**mysql_config)
        except Exception as e:
            raise CommandError(f"Failed to connect MySQL: {e}")

        rows = []
        raw_limit_clause = ""
        if limit and isinstance(limit, int) and limit > 0:
            raw_limit_clause = f" LIMIT {int(limit)}"

        date_from_opt = options.get("date_from")
        date_to_opt = options.get("date_to")

        from datetime import datetime

        def _valid_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except Exception:
                return None

        date_from_dt = _valid_date(date_from_opt) if date_from_opt else None
        date_to_dt = _valid_date(date_to_opt) if date_to_opt else None
        if date_from_opt and not date_from_dt:
            raise CommandError(
                f"Invalid --date-from format (expected YYYY-MM-DD): {date_from_opt}"
            )
        if date_to_opt and not date_to_dt:
            raise CommandError(
                f"Invalid --date-to format (expected YYYY-MM-DD): {date_to_opt}"
            )

        months_back_opt = options.get("months_back")
        months_back_env = os.getenv("RAWMUSO_MONTHS_BACK")
        try:
            months_back = int(
                months_back_opt
                if months_back_opt is not None
                else (months_back_env if months_back_env is not None else 1)
            )
        except ValueError:
            months_back = 1

        days_back_opt = options.get("days_back")
        days_back_env = os.getenv("RAWMUSO_DAYS_BACK", "40")
        days_back = None
        if days_back_opt is not None:
            try:
                days_back = int(days_back_opt)
            except Exception:
                days_back = None
        else:
            try:
                days_back = int(days_back_env) if days_back_env is not None else None
            except Exception:
                days_back = None

        date_col_opt = options.get("date_col")
        date_col = (date_col_opt or os.getenv("RAWMUSO_DATE_COLUMN") or "HRDOK").strip()

        disable_filter = options.get("no_date_filter") or (
            (days_back is None) and months_back <= 0
        )
        date_range_override = (date_from_dt is not None) or (date_to_dt is not None)

        today_date = now().date()
        if not date_range_override and not disable_filter:
            try:
                if today_date.day <= 10:
                    if days_back is None:
                        try:
                            days_back = int(os.getenv("RAWMUSO_DAYS_BACK", "40"))
                        except Exception:
                            days_back = 40
                    date_from_dt = today_date - timedelta(days=days_back)
                    date_to_dt = today_date
                else:
                    date_from_dt = today_date.replace(day=1)
                    date_to_dt = today_date
                date_range_override = True
            except Exception:
                pass

        date_format_opt = options.get("date_format")
        date_format_env_flag = os.getenv("RAWMUSO_DATE_IS_YYYYMMDD", "").strip() == "1"
        if date_format_opt:
            date_format = date_format_opt
        elif date_format_env_flag:
            date_format = "yyyymmdd"
        else:
            date_format = "date"

        base_query = "SELECT * FROM siap_mup.do s"
        if not disable_filter:
            if date_range_override:
                parts = []
                if date_from_dt:
                    if date_format == "yyyymmdd":
                        parts.append(
                            f"{date_col} >= '{date_from_dt.strftime('%Y%m%d')}'"
                        )
                    else:
                        parts.append(
                            f"{date_col} >= '{date_from_dt.strftime('%Y-%m-%d')}'"
                        )
                if date_to_dt:
                    if date_format == "yyyymmdd":
                        parts.append(f"{date_col} <= '{date_to_dt.strftime('%Y%m%d')}'")
                    else:
                        parts.append(
                            f"{date_col} <= '{date_to_dt.strftime('%Y-%m-%d')}'"
                        )
                where_expr = " AND ".join(parts)
                base_query += f" WHERE {where_expr}"
            else:
                if days_back is not None:
                    if date_format == "yyyymmdd":
                        where_expr = f"{date_col} >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL {days_back} DAY),'%Y%m%d')"
                    else:
                        where_expr = f"{date_col} >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)"
                else:
                    if date_format == "yyyymmdd":
                        where_expr = f"{date_col} >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL {months_back} MONTH),'%Y%m%d')"
                    else:
                        where_expr = f"{date_col} >= DATE_SUB(CURDATE(), INTERVAL {months_back} MONTH)"
                base_query += f" WHERE {where_expr}"

        order_expr = f" ORDER BY {date_col} DESC"
        query = f"{base_query}{order_expr}{raw_limit_clause}"

        fallback_limit_env = os.getenv("RAWMUSO_FALLBACK_LIMIT")
        fallback_limit = None
        if fallback_limit_env:
            try:
                fallback_limit = int(fallback_limit_env)
            except ValueError:
                logger.warning(
                    f"Invalid RAWMUSO_FALLBACK_LIMIT value '{fallback_limit_env}' (must be int); ignoring."
                )
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            for r in cursor:
                rows.append(r)
        except KeyboardInterrupt:
            logger.warning(
                "Import aborted by user (KeyboardInterrupt); cleaning up gracefully."
            )
            try:
                for _ in cursor:
                    pass
            except Exception:
                pass
            cursor.close()
            conn.close()
            self.stdout.write(
                self.style.WARNING(
                    "Aborted by user. Partial fetch discarded; no changes made."
                )
            )
            return
        except (mysql_errors.InterfaceError, mysql_errors.InternalError) as ie:
            logger.warning(
                f"Streaming fetch error ({ie}); attempting buffered fallback."
            )
            try:
                try:
                    cursor.close()
                except Exception:
                    pass
                conn.close()
                conn = mysql.connector.connect(**mysql_config)
                cursor = conn.cursor(dictionary=True, buffered=True)
                buffer_query = query
                if fallback_limit and not limit:
                    buffer_query = f"SELECT * FROM siap_mup.do s LIMIT {fallback_limit}"
                cursor.execute(buffer_query)
                rows = cursor.fetchall()
            except Exception as e2:
                try:
                    cursor.close()
                    conn.close()
                except Exception:
                    pass
                raise CommandError(f"Buffered fallback failed: {e2}")
        except Exception as e:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            raise CommandError(f"Query failed: {e}")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

        if not rows:
            msg = "No rows returned from siap_mup.do"
            if not disable_filter:
                msg += " (kemungkinan filter tanggal terlalu ketat atau format kolom salah)"
            self.stdout.write(self.style.WARNING(msg))
            return

        if limit:
            rows = rows[:limit]

        valid_company_ids = set(Company.objects.values_list("id", flat=True))
        missing_principle_prefixes = set()

        code_counts = {}
        to_create = []
        for r in rows:
            data = {}
            for col, val in r.items():
                key = col.upper().strip()
                if key in COLUMN_MAPPING:
                    field = COLUMN_MAPPING[key]
                    if field in NUMERIC_FIELDS:
                        data[field] = _clean_numeric(val, NUMERIC_FIELDS[field])
                    else:
                        data[field] = (
                            str(val).strip() if val not in [None, "NULL"] else ""
                        )
            hrdok = data.get("hrdok", "")
            whse = data.get("whse", "")
            nodokjdi = data.get("nodokjdi", "") 
            kodeprod = data.get("kodeprod", "")
            nobat = data.get("nobat", "")
            hna = data.get("hna")
            harga = data.get("harga")
            banyak_val = data.get("banyak", 0)
            banys_val = data.get("banys", 0)
            mom = data.get("mom", "NA")
            base_code = generate_code(
                hrdok,
                whse,
                nodokjdi,
                kodeprod,
                nobat,
                hna,
                harga,
                banyak_val,
                banys_val,
                mom,
            )

            cnt = code_counts.get(base_code, 0)
            if cnt == 0:
                code = base_code
            else:
                code = f"{base_code}-{cnt}"
            code_counts[base_code] = cnt + 1

            name = f"{hrdok}{_zero_pad(whse,3)}-{_zero_pad(nodokjdi,7)}-{kodeprod}"
            klasprod = data.get("klasprod") or ""
            if klasprod.startswith("001"):
                candidate = 1
            elif klasprod.startswith("002"):
                candidate = 2
            else:
                candidate = None

            principle_id = None
            if candidate is not None and candidate in valid_company_ids:
                principle_id = candidate
            elif candidate is not None:
                missing_principle_prefixes.add(candidate)

            entry = {
                "code": code,
                "name": name,
                "mom": mom,
                "whse": whse,
                "hrdok": hrdok,
                "nodokjdi": nodokjdi,
                "no_order": data.get("no_order", ""),
                "area": data.get("area", ""),
                "kodepos": data.get("kodepos", ""),
                "gruplang": data.get("gruplang", ""),
                "kodelang": data.get("kodelang", ""),
                "kdcust": data.get("kdcust", ""),
                "nmlang": data.get("nmlang", ""),
                "almtlang": data.get("almtlang", ""),
                "kodesalur": data.get("kodesalur", ""),
                "kodeprod": kodeprod,
                "nmprod": data.get("nmprod", ""),
                "klasprod": klasprod,
                "nmklas1": data.get("nmklas1", ""),
                "nmklas2": data.get("nmklas2", ""),
                "nobat": nobat,
                "dun": data.get("dun", ""),
                "idpkt": data.get("idpkt", ""),
                "principle_id": principle_id,
                "banyak": data.get("banyak") or 0,
                "tharga": data.get("tharga") or 0,
                "thna": data.get("thna") or 0,
                "banys": data.get("banys") or 0,
                "prsnbp": data.get("prsnbp") or 0,
                "prsnbmp": data.get("prsnbmp") or 0,
                "hna": hna,
                "harga": harga,
                "ehna": data.get("ehna"),
                "prsnpot": data.get("prsnpot"),
            }
            entry["pharga"] = _calculate_pharga(
                entry.get("thna"), entry.get("tharga")
            )
            to_create.append(entry)

        validation_keys = {_build_validation_key(d) for d in to_create}
        existing_validation_keys = set(
            RawMUSO.objects.filter(
                hrdok__in={key[0] for key in validation_keys},
                whse__in={key[1] for key in validation_keys},
                nodokjdi__in={key[2] for key in validation_keys},
                kodeprod__in={key[3] for key in validation_keys},
                nobat__in={key[4] for key in validation_keys},
            ).values_list(
                "hrdok",
                "whse",
                "nodokjdi",
                "kodeprod",
                "nobat",
                "hna",
                "harga",
                "banyak",
                "banys",
            )
        )
        normalized_existing_validation_keys = {
            (
                hrdok,
                whse,
                nodokjdi,
                kodeprod,
                nobat,
                _normalize_decimal_key(hna),
                _normalize_decimal_key(harga),
                int(banyak or 0),
                int(banys or 0),
            )
            for hrdok, whse, nodokjdi, kodeprod, nobat, hna, harga, banyak, banys in existing_validation_keys
        }
        seen_validation_keys = set()
        new_to_create = []
        skipped_existing = []
        for d in to_create:
            validation_key = _build_validation_key(d)
            if (
                validation_key in normalized_existing_validation_keys
                or validation_key in seen_validation_keys
            ):
                skipped_existing.append(d)
                continue
            seen_validation_keys.add(validation_key)
            new_to_create.append(d)

        self.stdout.write(
            f"Insert-only: new={len(new_to_create)} | skipped_existing={len(skipped_existing)} | total_unique_batch={len(rows)}"
        )

        validate_only_flag = options.get("validate_only", False)

        if dry_run:
            if missing_principle_prefixes:
                logger.warning(
                    "Principle IDs referenced but not found: %s (FK skipped)",
                    ",".join(str(x) for x in sorted(missing_principle_prefixes)),
                )
            self.stdout.write(
                self.style.WARNING(
                    f"Dry-run: would insert {len(to_create)} new rows; skip {len(skipped_existing)} existing codes (total source {len(rows)})."
                )
            )
            try:
                self._validate_back_to_source(
                    to_create, mysql_config, mark_dby_id=32, validate_only=True
                )
            except Exception as e:
                logger.warning("Back-validation (dry-run) failed: %s", e)
            return

        create_objs = []
        for d in new_to_create:
            create_objs.append(
                RawMUSO(
                    code=d.get("code", ""),
                    name=d.get("name", ""),
                    slug=d.get("code", ""),
                    whse=d.get("whse", ""),
                    hrdok=d.get("hrdok", ""),
                    nodokjdi=d.get("nodokjdi", ""),
                    no_order=d.get("no_order", ""),
                    area=d.get("area", ""),
                    kodepos=d.get("kodepos", ""),
                    gruplang=d.get("gruplang", ""),
                    kodelang=d.get("kodelang", ""),
                    kdcust=d.get("kdcust", ""),
                    nmlang=d.get("nmlang", ""),
                    almtlang=d.get("almtlang", ""),
                    kodesalur=d.get("kodesalur", ""),
                    kodeprod=d.get("kodeprod", ""),
                    nmprod=d.get("nmprod", ""),
                    klasprod=d.get("klasprod", ""),
                    nmklas1=d.get("nmklas1", ""),
                    nmklas2=d.get("nmklas2", ""),
                    banyak=d.get("banyak"),
                    banys=d.get("banys"),
                    hna=d.get("hna"),
                    harga=d.get("harga"),
                    tharga=d.get("tharga"),
                    thna=d.get("thna"),
                    ehna=d.get("ehna"),
                    prsnpot=d.get("prsnpot"),
                    pharga=d.get("pharga"),
                    prsnbp=d.get("prsnbp"),
                    prsnbmp=d.get("prsnbmp"),
                    mom=d.get("mom", "NA"),
                    nobat=d.get("nobat", ""),
                    dun=d.get("dun", ""),
                    idpkt=d.get("idpkt", ""),
                    principle_id=d.get("principle_id"),
                    status=1,
                    cby_id=cby_id,
                    cat=now(),
                )
            )

        if create_objs:
            self.stdout.write(f"Inserting {len(create_objs)} aggregated new records...")
            try:
                RawMUSO.objects.bulk_create(create_objs, batch_size=5000)
            except IntegrityError as ie:
                self.stdout.write(
                    self.style.WARNING(
                        f"IntegrityError during bulk_create RawMUSO: {ie}. Attempting sequence repair & retry once."
                    )
                )
                self._repair_rawmuso_sequence()
                try:
                    RawMUSO.objects.bulk_create(
                        create_objs, batch_size=5000, ignore_conflicts=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Retry bulk_create (ignore_conflicts) completed after sequence repair."
                        )
                    )
                except IntegrityError as ie2:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Retry bulk_create failed: {ie2}. Aborting remaining insert."
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Unexpected error during bulk_create RawMUSO: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"{start_ts.strftime('%Y-%m-%d %H:%M:%S')} - Imported RawMUSO: created {len(create_objs)} | skipped {len(skipped_existing)} existing | total source {len(rows)}"
            )
        )

        try:
            self._validate_back_to_source(
                to_create,
                mysql_config,
                mark_dby_id=32,
                validate_only=validate_only_flag,
            )
        except Exception as e:
            logger.warning("Back-validation step failed: %s", e)

        self._auto_sync_mup(start_ts)

    def _repair_rawmuso_sequence(self):
        engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
        if "postgresql" not in engine:
            return
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id),0) FROM sales_rawmuso")
                max_id = cursor.fetchone()[0] or 0
                cursor.execute("SELECT pg_get_serial_sequence('sales_rawmuso','id')")
                seq_row = cursor.fetchone()
                if not seq_row or not seq_row[0]:
                    return
                seq_name = seq_row[0]
                cursor.execute("SELECT last_value FROM %s" % seq_name)
                last_val = cursor.fetchone()[0]
                if last_val < max_id:
                    cursor.execute("SELECT setval(%s, %s, true)", [seq_name, max_id])
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Sequence repair skipped/failed: {e}")
            )

    def _validate_back_to_source(
        self, created_entries, mysql_config, mark_dby_id=32, validate_only=False
    ):
        if not created_entries:
            return
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor(dictionary=True)
        except Exception as e:
            logger.warning("Back-validation MySQL connect failed: %s", e)
            return

        tmp_rows = []
        for e in created_entries:
            code = e.get("code")
            if not code:
                continue
            hrdok = e.get("hrdok") or ""
            whse = e.get("whse") or ""
            nodokjdi = e.get("nodokjdi") or ""
            kodeprod = e.get("kodeprod") or ""
            nobat = e.get("nobat") or ""
            hna_str = str(e.get("hna")) if e.get("hna") is not None else "0"
            harga_str = str(e.get("harga")) if e.get("harga") is not None else "0"
            try:
                banyak_int = int(e.get("banyak") or 0)
            except Exception:
                banyak_int = 0
            try:
                banys_int = int(e.get("banys") or 0)
            except Exception:
                banys_int = 0
            agg_banyak = e.get("banyak") or 0
            agg_tharga = e.get("tharga") or 0
            agg_thna = e.get("thna") or 0
            agg_banys = e.get("banys") or 0
            tmp_rows.append(
                (
                    code,
                    hrdok,
                    whse,
                    nodokjdi,
                    kodeprod,
                    nobat,
                    hna_str,
                    harga_str,
                    banyak_int,
                    banys_int,
                    agg_banyak,
                    agg_tharga,
                    agg_thna,
                    agg_banys,
                )
            )

        if not tmp_rows:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            return

        try:
            cursor.execute(
                """
                CREATE TEMPORARY TABLE IF NOT EXISTS tmp_rawmuso (
                    code VARCHAR(255),
                    hrdok VARCHAR(32),
                    whse VARCHAR(16),
                    nodokjdi VARCHAR(32),
                    kodeprod VARCHAR(128),
                    nobat VARCHAR(128),
                    hna_str VARCHAR(64),
                    harga_str VARCHAR(64),
                    banyak_int BIGINT,
                    banys_int BIGINT,
                    agg_banyak DECIMAL(20,6),
                    agg_tharga DECIMAL(20,6),
                    agg_thna DECIMAL(20,6),
                    agg_banys DECIMAL(20,6)
                ) ENGINE=MEMORY;
                """
            )
        except Exception as e:
            logger.exception(
                "Failed to create temporary table for back-validation: %s", e
            )
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            return

        batch_size = 1000
        try:
            for i in range(0, len(tmp_rows), batch_size):
                batch = tmp_rows[i : i + batch_size]
                placeholders = ",".join(
                    ["(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" for _ in batch]
                )
                sql = (
                    "INSERT INTO tmp_rawmuso (code,hrdok,whse,nodokjdi,kodeprod,nobat,hna_str,harga_str,banyak_int,banys_int,agg_banyak,agg_tharga,agg_thna,agg_banys) VALUES "
                    + placeholders
                )
                flat_values = []
                for row in batch:
                    flat_values.extend(row)
                cursor.execute(sql, flat_values)

            check_sql = (
                "SELECT DISTINCT t.code "
                "FROM tmp_rawmuso t "
                "JOIN `siap_mup`.`do` s ON "
                "s.HRDOK = t.hrdok AND s.WHSE = t.whse AND s.NODOKJDI = t.nodokjdi AND "
                "s.KODEPROD = t.kodeprod AND s.NOBAT = t.nobat AND "
                "COALESCE(CAST(s.HNA AS CHAR),'0') = t.hna_str AND COALESCE(CAST(s.HARGA AS CHAR),'0') = t.harga_str AND "
                "COALESCE(CAST(s.BANYAK AS CHAR),'0') = CAST(t.banyak_int AS CHAR) AND COALESCE(CAST(s.BANYS AS CHAR),'0') = CAST(t.banys_int AS CHAR)"
            )

            cursor.execute(check_sql)
            results = cursor.fetchall()
            found_codes = set()
            for row in results:
                code = row.get("code")
                if code:
                    found_codes.add(code)

            all_codes = [r[0] for r in tmp_rows]
            source_codes = set(all_codes)
            missing_codes = source_codes - found_codes

            if validate_only:
                self.stdout.write(
                    self.style.WARNING(
                        f"Back-validation (select-only): total_source={len(all_codes)} | found_in_do={len(found_codes)} | not_in_do={len(missing_codes)}"
                    )
                )
            else:
                if source_codes:
                    to_soft_delete = []

                    if to_soft_delete:
                        deleted_count = RawMUSO.objects.filter(
                            code__in=to_soft_delete
                        ).update(deleted=True, status=0, dat=now(), dby_id=mark_dby_id)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Soft deleted {deleted_count} old codes (no longer in source): {', '.join(to_soft_delete)}"
                            )
                        )

                existing_in_db = set(
                    RawMUSO.objects.filter(code__in=list(source_codes)).values_list(
                        "code", flat=True
                    )
                )
                missing_in_db = source_codes - existing_in_db
                if missing_in_db:
                    code_map = {
                        e.get("code"): e for e in created_entries if e.get("code")
                    }
                    insert_objs = []
                    for code in missing_in_db:
                        d = code_map.get(code)
                        if not d:
                            continue
                        insert_objs.append(
                            RawMUSO(
                                code=d.get("code", ""),
                                name=d.get("name", ""),
                                slug=d.get("code", ""),
                                whse=d.get("whse", ""),
                                hrdok=d.get("hrdok", ""),
                                nodokjdi=d.get("nodokjdi", ""),
                                no_order=d.get("no_order", ""),
                                area=d.get("area", ""),
                                kodepos=d.get("kodepos", ""),
                                gruplang=d.get("gruplang", ""),
                                kodelang=d.get("kodelang", ""),
                                kdcust=d.get("kdcust", ""),
                                nmlang=d.get("nmlang", ""),
                                almtlang=d.get("almtlang", ""),
                                kodesalur=d.get("kodesalur", ""),
                                kodeprod=d.get("kodeprod", ""),
                                nmprod=d.get("nmprod", ""),
                                klasprod=d.get("klasprod", ""),
                                nmklas1=d.get("nmklas1", ""),
                                nmklas2=d.get("nmklas2", ""),
                                banyak=d.get("banyak"),
                                banys=d.get("banys"),
                                hna=d.get("hna"),
                                harga=d.get("harga"),
                                tharga=d.get("tharga"),
                                thna=d.get("thna"),
                                ehna=d.get("ehna"),
                                prsnpot=d.get("prsnpot"),
                                pharga=d.get("pharga"),
                                prsnbp=d.get("prsnbp"),
                                prsnbmp=d.get("prsnbmp"),
                                mom=d.get("mom", "NA"),
                                nobat=d.get("nobat", ""),
                                dun=d.get("dun", ""),
                                idpkt=d.get("idpkt", ""),
                                principle_id=d.get("principle_id"),
                                status=1,
                                cby_id=mark_dby_id,
                                cat=now(),
                            )
                        )

                    if insert_objs:
                        try:
                            RawMUSO.objects.bulk_create(insert_objs, batch_size=5000)
                        except Exception:
                            pass

                db_count = RawMUSO.objects.filter(
                    code__in=list(source_codes), status=1, deleted=False
                ).count()
                source_count = len(source_codes)
                if source_count != db_count:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Row count mismatch: source={source_count} | RawMUSO(status=1, deleted=False)={db_count} | diff={source_count - db_count}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Row count OK: source={source_count} = RawMUSO(status=1)={db_count}"
                        )
                    )

                if missing_codes:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Codes with no exact match in DO (may be stale data): {len(missing_codes)} codes"
                        )
                    )

        except Exception as e:
            logger.exception("Back-validation temp-table process failed: %s", e)
        finally:
            try:
                cursor.execute("DROP TEMPORARY TABLE IF EXISTS tmp_rawmuso")
            except Exception:
                pass
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
