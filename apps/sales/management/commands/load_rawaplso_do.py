# FaisalS | HF-28 - APL Selling Out raw data auto import
# Modified by UtandraJ |

import os
import logging
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from django.db import transaction, connection
import pandas as pd
from dbfread import DBF
from apps.sales.models.sales_models import RawAPLSO
from django.contrib.auth import get_user_model
import mysql.connector
from mysql.connector import errors as mysql_errors
from datetime import timedelta, datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


DTYPE_MAPPING = {
    "kode_distributor": "string",
    "type": "string",
    "facno": "string",
    "hrdok": "string",
    "tanggal": "string",
    "kode_produk": "string",
    "produk": "string",
    "nodokjdi": "string",
    "kode_comp": "string",
    "kode_lang": "string",
    "kddokjdi": "string",
    "namaprod": "string",
    "nama_lang": "string",
    "almt_1": "string",
    "tglexp": "string",
    "banyak": "decimal",
    "kodeprod": "string",
    "kode_produk_oi": "string",
    "produk_oi": "string",
    "kode_group_produk": "string",
    "group_produk": "string",
    "kode_subgroup_produk": "string",
    "subgroup_produk": "string",
    "kode_branch": "string",
    "branch": "string",
    "id_branch_oi": "string",
    "kode_branch_oi": "string",
    "branch_oi": "string",
    "kode_outlet": "string",
    "cust_id": "string",
    "outlet": "string",
    "alamat_outlet": "string",
    "kode_outlet_oi": "string",
    "outlet_oi": "string",
    "alamat_outlet_oi": "string",
    "kode_group_outlet": "string",
    "group_outlet": "string",
    "kode_salur": "string",
    "kode_sector": "string",
    "sector": "string",
    "kode_channel": "string",
    "channel": "string",
    "kode_sub_channel": "string",
    "sub_channel": "string",
    "kode_region": "string",
    "region": "string",
    "qty": "decimal",
    "faktor_kali": "decimal",
    "hjp": "decimal",
    "hna": "decimal",
    "harga": "decimal",
    "whse": "string",
    "tanggal_expired": "string",
    "batch": "string",
    "prsnd": "decimal",
    "prsnpot": "decimal",
    "prsnt": "decimal",
    "prsnbp": "decimal",
    "prsnbmp": "decimal",
    "bonus": "decimal",
    "facAcu": "string",
    "kode_team": "string",
    "team": "string",
    "dun": "string",
    "distribute_apks": "string",
    "distributed_id": "string",
    "distributed_name": "string",
    "parent_id": "string",
    "missing_facno": "string",
    "no_order": "string",
    "periode": "string",
    # Field tambahan dari APL.Sales
    "kodejual": "string",
    "kode_kota": "string",
    "kode_type": "string",
    "kodesalur": "string",
    "kode_tend": "string",
    "kode_sales": "string",
    "groupprod": "string",
    "supp": "string",
    "tot1": "decimal",
    "prins": "decimal",
    "prinshna": "decimal",
    "prine": "decimal",
    "prinxtra": "decimal",
    "prinpnel": "decimal",
    "tot2": "decimal",
    "uom": "string",
    "mvgr3": "string",
    "ship_to_p": "string",
    "log_date": "string",
}

NORMALIZE_REMOVE = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]


class Command(BaseCommand):
    help = (
        "Auto import RawAPLSO from APL MySQL, keeping the latest LOG_DATE "
        "row per NODOKJDI and BATCH."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cby", type=int, required=True, help="User ID performing the import"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not write to database, only show summary",
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Bulk create/update batch size"
        )
        parser.add_argument("--limit", type=int, help="Limit rows read (for debugging)")
        parser.add_argument(
            "--query",
            type=str,
            help="Override SELECT query for APL MySQL source (else env DB_APL_QUERY or default table).",
        )
        parser.add_argument(
            "--months-back",
            type=int,
            help="Filter N bulan terakhir berdasarkan kolom tanggal (default env RAWAPLSO_MONTHS_BACK atau 1)",
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
            help="Nama kolom tanggal di sumber (default env RAWAPLSO_DATE_COLUMN atau HRDOK)",
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

    def normalize_column_name(self, field: str) -> str:
        for ch in NORMALIZE_REMOVE:
            field = field.replace(ch, "")
        return field.lower()

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:

        original_cols = df.columns.tolist()
        normalized_map = {self.normalize_column_name(c): c for c in original_cols}

        rename_map = {}
        for model_col in DTYPE_MAPPING.keys():
            norm = self.normalize_column_name(model_col)
            if norm in normalized_map:
                rename_map[normalized_map[norm]] = model_col

        for col in df.columns:
            if (
                self.normalize_column_name(col) == "logdate"
                and "log_date" not in rename_map.values()
            ):
                rename_map[col] = "log_date"
        if rename_map:
            df = df.rename(columns=rename_map)

        for col, col_type in DTYPE_MAPPING.items():
            if col not in df.columns:
                df[col] = "" if col_type == "string" else Decimal("0")

        string_fields = [k for k, v in DTYPE_MAPPING.items() if v == "string"]
        for col in string_fields:
            df[col] = (
                df[col]
                .astype(str)
                .fillna("")
                .str.strip()
                .replace({"nan": "", "None": "", "NULL": ""})
            )

        decimal_fields = [k for k, v in DTYPE_MAPPING.items() if v == "decimal"]
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a", "None", "nan", "NaN"]
        for col in decimal_fields:
            df[col] = df[col].replace(invalid_entries, 0)

            def _cast_decimal(val):
                if val in invalid_entries:
                    return Decimal("0")
                try:
                    return Decimal(str(val).strip())
                except (ValueError, InvalidOperation):
                    return Decimal("0")

            df[col] = df[col].apply(_cast_decimal)

        if "log_date" in df.columns:
            import pandas as pd

            df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")

        def _strip_zeros(val: str) -> str:
            v = (val or "").strip()
            return v.lstrip("0") or "0"

        def _parse_date(val: str) -> str:
            from datetime import datetime

            v = (val or "").strip()
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(v, fmt).strftime("%Y%m%d")
                except Exception:
                    pass
            if len(v) == 8 and v.isdigit():
                return v
            return v.replace("-", "").replace("/", "")

        def _parse_exp(val: str) -> str:
            from datetime import datetime

            v = (val or "").strip()
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(v, fmt).strftime("%Y%m%d")
                except Exception:
                    pass
            if len(v) == 8 and v.isdigit():
                return v
            return ""

        def _fmt_qty(val) -> str:
            try:
                return f"{Decimal(str(val)):.1f}"
            except Exception:
                return "0.0"

        df["tanggal"] = df.get("hrdok", "").apply(_parse_date)
        df["kode_distributor"] = "APL"
        df["type"] = df.get("kddokjdi", "").apply(lambda x: _strip_zeros(str(x)))
        df["facno"] = df.get("nodokjdi", "")

        df["kode_produk"] = df["kode_produk"].where(
            df["kode_produk"].ne(""), df.get("kodeprod", "")
        )

        # Dibaca dari `kodesalur` (TANPA underscore), BUKAN `kode_salur`.
        # Label mengikuti penamaan sales_salestype.
        SECTOR_LABELS = {
            "001": "Regular",
            "002": "eCatalog",
            "003": "Inhealth",
            "004": "Special Price",
        }

        def _sector_last_char(kode_produk):
            trimmed = (kode_produk or "").rstrip()
            return trimmed[-1:] if trimmed else ""

        def _sector_char_pos7(kode_produk):
            kp = kode_produk or ""
            return kp[6:7] if len(kp) >= 7 else ""

        def _determine_sector(kode_salur, kode_produk):
            ks = (kode_salur or "").strip()
            lc = _sector_last_char(kode_produk)
            c7 = _sector_char_pos7(kode_produk)

            matches = []
            if (ks not in ("16", "88", "3A") and lc != "E") or (ks in ("01", "03")):
                matches.append("001")
            if (lc == "E" or ks == "88") and lc != "I":
                matches.append("002")
            if c7 == "I" or ks == "16":
                matches.append("003")
            if ks == "3A":
                matches.append("004")

            # Cocok tepat 1 rule -> pakai. 0 rule (TIDAK_COCOK) atau >1 rule
            # (AMBIGU) -> dibiarkan kosong, JANGAN ditebak. combine_so_rawaplso
            # sudah menangani kode_sector kosong dengan fallback ke harga
            # terbaru tanpa filter salestype.
            return matches[0] if len(matches) == 1 else ""

        sector_codes = [
            _determine_sector(ks, kp)
            for ks, kp in zip(df["kodesalur"], df["kode_produk"])
        ]
        df["kode_sector"] = sector_codes
        df["sector"] = [SECTOR_LABELS.get(c, "") for c in sector_codes]

        unresolved = sector_codes.count("")
        if unresolved:
            self.stdout.write(
                self.style.WARNING(
                    f"Sector tidak ter-assign (ambigu/tidak cocok rule): {unresolved} row "
                    f"dari {len(sector_codes)} -- kode_sector dibiarkan kosong"
                )
            )

        if "namaprod" in df.columns:
            df["produk"] = df["namaprod"].astype(str).fillna("")
        df["kode_branch"] = df.get("kode_comp", df.get("kode_branch", ""))
        df["kode_outlet"] = df.get("kode_lang", "").apply(
            lambda x: _strip_zeros(str(x))
        )
        df["qty"] = df.get("banyak", Decimal("0"))
        if "tglexp" in df.columns:
            df["tanggal_expired"] = df["tglexp"].apply(_parse_exp)
        else:
            df["tanggal_expired"] = ""

        tanggal_fmt = df["tanggal"].astype(str)
        kode_comp_fmt = df["kode_branch"].astype(str)
        nodokjdi_fmt = df.get("nodokjdi", "").astype(str)
        kodeprod_fmt = df["kode_produk"].astype(str)
        kode_lang_trim = df["kode_outlet"].astype(str)
        qty_fmt = df["qty"].apply(_fmt_qty)

        df["name"] = (
            tanggal_fmt + kode_comp_fmt + "-" + nodokjdi_fmt + "-" + kodeprod_fmt
        )
        df["code"] = (
            tanggal_fmt
            + kode_comp_fmt
            + "-"
            + nodokjdi_fmt
            + "-"
            + kodeprod_fmt
            + "-"
            + kode_lang_trim
            + "--"
            + qty_fmt
        )
        df["slug"] = df["code"] + "-" + (df.groupby("code").cumcount()).astype(str)
        return df

    def _deduplicate_latest_nodokjdi_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        before_count = len(df)

        nodokjdi = (
            df["nodokjdi"]
            .astype("string")
            .str.strip()
            .fillna("")
        )
        batch = (
            df["batch"]
            .astype("string")
            .str.strip()
            .fillna("")
        )
        kode_sales = (
            df["kode_sales"]
            .astype("string")
            .str.strip()
            .fillna("")
        )
        df["_nodokjdi_key"] = nodokjdi
        df["_batch_key"] = batch
        df["_kode_sales_key"] = kode_sales

        df = (
            df
            .sort_values(
                by=[
                    "_nodokjdi_key",
                    "_batch_key",
                    "_kode_sales_key",
                    "log_date",
                ],
                ascending=[True, True, True, False],
                na_position="last",
            )
            .drop_duplicates(
                subset=[
                    "_nodokjdi_key",
                    "_batch_key",
                    "_kode_sales_key",
                ],
                keep="first",
            )
            .drop(
                columns=[
                    "_nodokjdi_key",
                    "_batch_key",
                    "_kode_sales_key",
                ]
            )
            .reset_index(drop=True)
        )

        self.stdout.write(
            "Latest per NODOKJDI + BATCH + KODE_SALES: "
            f"before={before_count} | after={len(df)} | "
            f"removed={before_count - len(df)}"
        )

        return df

    def handle(self, *args, **options):
        start_ts = now()
        cby_id = options["cby"]
        dry_run = options.get("dry_run", False)
        batch_size = options.get("batch_size", 1000)
        limit = options.get("limit")
        query_override = options.get("query")
        months_back_opt = options.get("months_back")
        date_from_opt = options.get("date_from")
        date_to_opt = options.get("date_to")
        date_col_opt = options.get("date_col")
        no_date_filter = options.get("no_date_filter")
        date_format_opt = options.get("date_format")

        df = self._fetch_apl_mysql(
            limit=limit,
            query_override=query_override,
            months_back_opt=months_back_opt,
            date_from_opt=date_from_opt,
            date_to_opt=date_to_opt,
            date_col_opt=date_col_opt,
            no_date_filter=no_date_filter,
            date_format_opt=date_format_opt,
        )
        # self.stdout.write(
        #     self.style.NOTICE(f"Fetched RawAPLSO rows from APL MySQL: {len(df)}")
        # )

        df = self._prepare_dataframe(df)
        df = self._deduplicate_latest_nodokjdi_batch(df)
        # self.stdout.write(f"Prepared DataFrame shape: {df.shape}")

        codes = df["code"].tolist()
        existing_codes = set(
            RawAPLSO.objects.filter(code__in=codes).values_list("code", flat=True)
        )
        new_df = df[~df["code"].isin(existing_codes)]
        skipped_df = df[df["code"].isin(existing_codes)]

        self.stdout.write(
            f"Insert-only: new={len(new_df)} | skipped_existing={len(skipped_df)} | total_unique_batch={len(df)}"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry-run: would insert {len(new_df)} new rows; skip {len(skipped_df)} existing codes (total source {len(df)})."
                )
            )
            return

        create_objs = []
        for row in new_df.to_dict(orient="records"):

            log_date_val = row.get("log_date")
            if isinstance(log_date_val, datetime):
                try:
                    if timezone.is_naive(log_date_val):
                        log_date_val = timezone.make_aware(
                            log_date_val, timezone.get_current_timezone()
                        )
                except Exception:

                    if timezone.is_naive(log_date_val):
                        log_date_val = timezone.make_aware(log_date_val)

            create_objs.append(
                RawAPLSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    kode_distributor=row.get("kode_distributor", ""),
                    type=row.get("type", ""),
                    facno=row.get("facno", ""),
                    tanggal=row.get("tanggal", ""),
                    kode_produk=row.get("kode_produk", ""),
                    produk=row.get("produk", ""),
                    kode_produk_oi=row.get("kode_produk_oi", ""),
                    produk_oi=row.get("produk_oi", ""),
                    kode_group_produk=row.get("kode_group_produk", ""),
                    group_produk=row.get("group_produk", ""),
                    kode_subgroup_produk=row.get("kode_subgroup_produk", ""),
                    subgroup_produk=row.get("subgroup_produk", ""),
                    kode_branch=row.get("kode_branch", ""),
                    branch=row.get("branch", ""),
                    id_branch_oi=row.get("id_branch_oi", ""),
                    kode_branch_oi=row.get("kode_branch_oi", ""),
                    branch_oi=row.get("branch_oi", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    cust_id=row.get("cust_id", ""),
                    outlet=row.get("nama_lang", ""),
                    alamat_outlet=row.get("almt_1", ""),
                    kode_outlet_oi=row.get("kode_outlet_oi", ""),
                    outlet_oi=row.get("outlet_oi", ""),
                    alamat_outlet_oi=row.get("alamat_outlet_oi", ""),
                    kode_group_outlet=row.get("kode_group_outlet", ""),
                    group_outlet=row.get("group_outlet", ""),
                    kode_salur=row.get("kode_salur", ""),
                    kode_sector=row.get("kode_sector", ""),
                    sector=row.get("sector", ""),
                    kode_channel=row.get("kode_channel", ""),
                    channel=row.get("channel", ""),
                    kode_sub_channel=row.get("kode_sub_channel", ""),
                    sub_channel=row.get("sub_channel", ""),
                    kode_region=row.get("kode_region", ""),
                    region=row.get("region", ""),
                    qty=row.get("qty", 0),
                    faktor_kali=row.get("faktor_kali", 0),
                    hjp=row.get("hjp", 0),
                    hna=row.get("hna", 0),
                    harga=row.get("harga", 0),
                    whse=row.get("whse", ""),
                    tanggal_expired=row.get("tglexp", ""),
                    batch=row.get("batch", ""),
                    prsnd=row.get("prsnd", 0),
                    prsnpot=row.get("prsnpot", 0),
                    prsnt=row.get("prsnt", 0),
                    prsnbp=row.get("prsnbp", 0),
                    prsnbmp=row.get("prsnbmp", 0),
                    bonus=row.get("bonus", 0),
                    facAcu=row.get("facAcu", ""),
                    kode_team=row.get("kode_team", ""),
                    team=row.get("team", ""),
                    dun=row.get("dun", ""),
                    distribute_apks=row.get("distribute_apks", ""),
                    distributed_id=row.get("distributed_id", ""),
                    distributed_name=row.get("distributed_name", ""),
                    parent_id=row.get("parent_id", ""),
                    missing_facno=row.get("missing_facno", ""),
                    no_order=row.get("no_order", ""),
                    periode=row.get("periode", ""),
                    kodejual=row.get("kodejual", ""),
                    kode_kota=row.get("kode_kota", ""),
                    kode_type=row.get("kode_type", ""),
                    kodesalur=row.get("kodesalur", ""),
                    kode_tend=row.get("kode_tend", ""),
                    kode_sales=row.get("kode_sales", ""),
                    groupprod=row.get("groupprod", ""),
                    supp=row.get("supp", ""),
                    tot1=row.get("tot1", 0),
                    prins=row.get("prins", 0),
                    prinshna=row.get("prinshna", 0),
                    prine=row.get("prine", 0),
                    prinxtra=row.get("prinxtra", 0),
                    prinpnel=row.get("prinpnel", 0),
                    tot2=row.get("tot2", 0),
                    uom=row.get("uom", ""),
                    mvgr3=row.get("mvgr3", ""),
                    ship_to_p=row.get("ship_to_p", ""),
                    log_date=log_date_val,
                    status=1,
                    cby_id=cby_id,
                    cat=now(),
                )
            )
        if create_objs:
            RawAPLSO.objects.bulk_create(create_objs, batch_size=batch_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"{start_ts.strftime('%Y-%m-%d %H:%M:%S')} - Imported RawAPLSO: created {len(create_objs)} | skipped {len(skipped_df)} existing | total source {len(df)}"
            )
        )
        self._auto_sync_apl(start_ts)

    def _auto_sync_apl(self, start_ts):
        # today_str = now().date().strftime("%Y-%m-%d")
        today_str = (now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        sp_user_id = 1
        sp_name = "combine_so_rawaplso"

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

    def _fetch_apl_mysql(
        self,
        limit=None,
        query_override=None,
        months_back_opt=None,
        date_from_opt=None,
        date_to_opt=None,
        date_col_opt=None,
        no_date_filter=False,
        date_format_opt=None,
    ) -> pd.DataFrame:
        required_env = [
            "DB_APL_HOST",
            "DB_APL_USER",
            "DB_APL_PASSWORD",
            "DB_APL_DATABASE",
        ]
        missing = [k for k in required_env if not os.getenv(k)]
        if missing:
            raise CommandError(f"Missing MySQL APL env vars: {', '.join(missing)}")

        host = os.getenv("DB_APL_HOST")
        user = os.getenv("DB_APL_USER")
        password = os.getenv("DB_APL_PASSWORD")
        database = os.getenv("DB_APL_DATABASE")
        port_raw = os.getenv("DB_APL_PORT", "3306")
        try:
            port = int(port_raw)
        except ValueError:
            raise CommandError(f"Invalid DB_APL_PORT value: {port_raw}")

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

        months_back_env = os.getenv("RAWAPLSO_MONTHS_BACK", "1")
        try:
            months_back = int(
                months_back_opt if months_back_opt is not None else months_back_env
            )
        except ValueError:
            months_back = 1

        date_col = (
            date_col_opt or os.getenv("RAWAPLSO_DATE_COLUMN") or "HRDOK"
        ).strip()
        disable_filter = no_date_filter or months_back <= 0
        date_range_override = (date_from_dt is not None) or (date_to_dt is not None)

        date_format_env_flag = os.getenv("RAWAPLSO_DATE_IS_YYYYMMDD", "").strip() == "1"
        if date_format_opt:
            date_format = date_format_opt
        elif date_format_env_flag:
            date_format = "yyyymmdd"
        else:
            date_format = "date"

        def col_expr():
            if date_format == "yyyymmdd":
                return f"STR_TO_DATE({date_col}, '%Y-%m-%d')"
            return date_col

        raw_limit_clause = ""
        if limit and isinstance(limit, int) and limit > 0:
            raw_limit_clause = f" LIMIT {int(limit)}"

        base_query = (
            query_override or os.getenv("DB_APL_QUERY") or "SELECT * FROM Sales s"
        ).strip()
        user_has_where = " where " in base_query.lower()
        if not disable_filter and not user_has_where:
            if date_range_override:

                def col_expr():
                    if date_format == "yyyymmdd":
                        return f"STR_TO_DATE({date_col}, '%Y-%m-%d')"
                    return date_col

                parts = []
                if date_from_dt:
                    parts.append(
                        f"{col_expr()} >= '{date_from_dt.strftime('%Y-%m-%d')}'"
                    )
                if date_to_dt:
                    parts.append(f"{col_expr()} <= '{date_to_dt.strftime('%Y-%m-%d')}'")
                where_expr = " AND ".join(parts)
                if where_expr:
                    base_query += f" WHERE {where_expr}"
            else:
                if date_format == "yyyymmdd":
                    where_expr = f"STR_TO_DATE({date_col}, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL {months_back} MONTH)"
                else:
                    where_expr = f"{date_col} >= DATE_SUB(CURDATE(), INTERVAL {months_back} MONTH)"
                base_query += f" WHERE {where_expr}"

        order_expr = f" ORDER BY {date_col} DESC"
        query = f"{base_query}{order_expr}{raw_limit_clause}"

        debug_mode = os.getenv("RAWAPLSO_DEBUG", "").strip() == "1"
        if debug_mode:
            self.stdout.write(
                self.style.WARNING(f"[RAW APLSO DEBUG] Final SQL: {query}")
            )
            self.stdout.write(
                self.style.WARNING(
                    f"[RAW APLSO DEBUG] Filter active: {not disable_filter}; months_back={months_back}; date_range_override={date_range_override}; date_from={date_from_opt}; date_to={date_to_opt}; date_col={date_col}; date_format={date_format}"
                )
            )

        try:
            conn = mysql.connector.connect(
                host=host, user=user, password=password, database=database, port=port
            )
        except Exception as e:
            raise CommandError(f"Failed to connect APL MySQL: {e}")

        rows = []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
        except KeyboardInterrupt:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            raise CommandError("Fetch aborted by user")
        except (mysql_errors.InterfaceError, mysql_errors.InternalError) as ie:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            raise CommandError(f"MySQL error: {ie}")
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
            msg = "No rows returned from Sales"
            if not disable_filter:
                msg += " (mungkin filter 1 bulan tidak menghasilkan data)"
            self.stdout.write(self.style.WARNING(msg))
            return pd.DataFrame(columns=list(DTYPE_MAPPING.keys()))

        if limit and isinstance(limit, int) and limit > 0:
            rows = rows[:limit]
        df = pd.DataFrame(rows)
        rename_map = {}
        for col in df.columns:
            norm = self.normalize_column_name(col)
            for expected in DTYPE_MAPPING.keys():
                if norm == self.normalize_column_name(expected):
                    rename_map[col] = expected
                    break
        if rename_map:
            df = df.rename(columns=rename_map)
        return df
