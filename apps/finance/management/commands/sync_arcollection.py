from django.core.management.base import BaseCommand
from datetime import datetime
import os
import mysql.connector
import psycopg2
from psycopg2.extras import execute_values
from django.db import connection
from apps.base.utils.chronos import hive_dateparser
from django.utils import timezone


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: Command                                               ║
# ║  Type: Management Command                                    ║
# ║  Purpose: Command for syncing AR Collection from mysql       ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\management\commands\sync_arcollection.py ║
# ║  Created: Jun/27-2025 by Setiadji                            ║
# ║  Updates: Jun/27-2025 by Setiadji                            ║
# ╚══════════════════════════════════════════════════════════════╝
class Command(BaseCommand):
    help = "Sync ARCollection from MySQL to PostgreSQL for current month"

    def add_arguments(self, parser):
        parser.add_argument("--cby", type=int, required=True)  # 🔹 REQUIRED

    def handle(self, *args, **options):

        MYSQL_CONFIG = {
            "host": os.environ.get("DB_AR_COLLECTION_HOST"),
            "user": os.environ.get("DB_AR_USER"),
            "password": os.environ.get("DB_AR_PASSWORD"),
            "database": os.environ.get("DB_AR_DATABASE"),
            "port": int(os.environ.get("DB_AR_COLLECTION_PORT", "3306")),
        }

        PG_TABLE = "finance_arcollection"

        cby_id = options["cby"]
        now = timezone.localtime()
        first_day = now.replace(day=1)
        month = first_day.month
        year = first_day.year

        try:
            mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
            mysql_cursor = mysql_conn.cursor(dictionary=True)
            mysql_cursor.execute(
                """SELECT DATE_FROM, DATE_TO, CABANG, USERNAME, TANGGAL, KODE_SALESMAN, KODE_COLLECTOR, KODE_PELANGGAN, NAMA_PELANGGAN, ALAMAT_PELANGGAN,
                    NPWP, NOMOR_FAKTUR, TRX_DATE, TAX_DOCUMENT_NUMBER, NILAI_FAKTUR, DPP_NUMBER, DPP_DATE, COLLECT_AMOUNT, SSP_PPN, SSP_PPH, RECEIPTNUMBER, RECEIPT_DATE,
                    RECEIPT_TYPE, REFERENCE_NUMBER, REFERENCE_DATE, RECEIPT_METHOD, APPLY_AMOUNT, CUSTOMER_TRX_ID, SALDO_AR, TIME_PROSES, CUSTOMER_TRX_ID1, TRX_NUMBER,
                    BATCH_SOURCE_NAME, LINE_NUMBER, LINE_TYPE, ITEM_CODE, QUANTITY_INVOICED, UNIT_SELLING_PRICE, TAX_RATE, AMOUNT, AMOUNT_TAX, AMOUNT_TOTAL, ITEM_DESCRIPTION,
                    PRIMARY_UOM_CODE, PRIMARY_UNIT_OF_MEASURE, IMHRMN, IMHRMN_DESCRIPTION, HARMONISASI, GROUP_PRODUK, PRINCIPAL, KODEVENDOR, KODEVENDOR1, NAMAVENDOR,
                    CUST_CLASS_CODE, JUMLAH_BAYAR, TGLTRANSAKSI, KET_GRUP_1, KET_GRUP_2, MONTH_TRANSAKSI, DATE_PROSES
                FROM ar_collection
                WHERE MONTH(STR_TO_DATE(DATE_FROM, '%d-%b-%Y')) = %s AND YEAR(STR_TO_DATE(DATE_FROM, '%d-%b-%Y')) = %s""",
                (month, year),
            )

            data = mysql_cursor.fetchall()
            self.stdout.write(self.style.WARNING(f"🟡 MySQL rows fetched: {len(data)}"))

            if not data:
                self.stdout.write(self.style.WARNING("⚠️ No data to sync. Exiting."))
                return

            # Step 2: PostgreSQL operations using Django's default connection
            with connection.cursor() as pg_cursor:

                pg_cursor.execute(
                    f"""
                    DELETE FROM {PG_TABLE}
                    WHERE DATE_TRUNC('month', "date_from") = DATE_TRUNC('month', CURRENT_DATE)
                """
                )
                self.stdout.write("🧹 Deleted existing records for current month.")

                insert_query = f"""
                    INSERT INTO {PG_TABLE} ("date_from", "date_to", "cabang", "username", "tanggal", "kode_salesman", "kode_collector", "kode_pelanggan", "nama_pelanggan",
                        "alamat_pelanggan", "npwp", "nomor_faktur", "trx_date", "tax_document_number", "nilai_faktur", "dpp_number", "dpp_date", "collect_amount", "ssp_ppn",
                        "ssp_pph", "receiptnumber", "receipt_date", "receipt_type", "reference_number", "reference_date", "receipt_method", "apply_amount", "customer_trx_id",
                        "saldo_ar", "time_proses", "customer_trx_id1", "trx_number", "batch_source_name", "line_number", "line_type", "item_code", "quantity_invoiced",
                        "unit_selling_price", "tax_rate", "amount", "amount_tax", "amount_total", "item_description", "primary_uom_code", "primary_unit_of_measure", "imhrmn",
                        "imhrmn_description", "harmonisasi", "group_produk", "principal", "kodevendor", "kodevendor1", "namavendor", "cust_class_code", "jumlah_bayar",
                        "tgltransaksi", "ket_grup_1", "ket_grup_2", "month_transaksi", "date_proses", name, status, cat, cby_id, deleted)
                    VALUES %s
                """

                insert_data = [
                    (
                        hive_dateparser(row["DATE_FROM"], raise_error=True),
                        hive_dateparser(row["DATE_TO"], raise_error=True),
                        row["CABANG"],
                        row["USERNAME"],
                        hive_dateparser(row["TANGGAL"], raise_error=True),
                        row["KODE_SALESMAN"],
                        row["KODE_COLLECTOR"],
                        row["KODE_PELANGGAN"],
                        row["NAMA_PELANGGAN"],
                        row["ALAMAT_PELANGGAN"],
                        row["NPWP"],
                        row["NOMOR_FAKTUR"],
                        hive_dateparser(row["TRX_DATE"], raise_error=True),
                        row["TAX_DOCUMENT_NUMBER"],
                        row["NILAI_FAKTUR"],
                        row["DPP_NUMBER"],
                        hive_dateparser(row["DPP_DATE"], raise_error=True),
                        row["COLLECT_AMOUNT"],
                        row["SSP_PPN"],
                        row["SSP_PPH"],
                        row["RECEIPTNUMBER"],
                        hive_dateparser(row["RECEIPT_DATE"], raise_error=True),
                        row["RECEIPT_TYPE"],
                        row["REFERENCE_NUMBER"],
                        hive_dateparser(row["REFERENCE_DATE"], raise_error=True),
                        row["RECEIPT_METHOD"],
                        row["APPLY_AMOUNT"],
                        row["CUSTOMER_TRX_ID"],
                        row["SALDO_AR"],
                        hive_dateparser(row["TIME_PROSES"], raise_error=True),
                        row["CUSTOMER_TRX_ID1"],
                        row["TRX_NUMBER"],
                        row["BATCH_SOURCE_NAME"],
                        row["LINE_NUMBER"],
                        row["LINE_TYPE"],
                        row["ITEM_CODE"],
                        row["QUANTITY_INVOICED"],
                        row["UNIT_SELLING_PRICE"],
                        row["TAX_RATE"],
                        row["AMOUNT"],
                        row["AMOUNT_TAX"],
                        row["AMOUNT_TOTAL"],
                        row["ITEM_DESCRIPTION"],
                        row["PRIMARY_UOM_CODE"],
                        row["PRIMARY_UNIT_OF_MEASURE"],
                        row["IMHRMN"],
                        row["IMHRMN_DESCRIPTION"],
                        row["HARMONISASI"],
                        row["GROUP_PRODUK"],
                        row["PRINCIPAL"],
                        row["KODEVENDOR"],
                        row["KODEVENDOR1"],
                        row["NAMAVENDOR"],
                        row["CUST_CLASS_CODE"],
                        row["JUMLAH_BAYAR"],
                        hive_dateparser(row["TGLTRANSAKSI"], raise_error=True),
                        row["KET_GRUP_1"],
                        row["KET_GRUP_2"],
                        row["MONTH_TRANSAKSI"],
                        hive_dateparser(row["DATE_PROSES"], raise_error=True),
                        f"{row['KODE_PELANGGAN']} {row['NOMOR_FAKTUR']}",
                        1,
                        now,
                        cby_id,
                        False,
                    )
                    for row in data
                ]

                execute_values(pg_cursor, insert_query, insert_data)
                connection.commit()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Sync completed. Inserted: {len(insert_data)} rows."
                    )
                )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Sync failed: {e}"))
        finally:
            if "mysql_cursor" in locals():
                mysql_cursor.close()
            if "mysql_conn" in locals():
                mysql_conn.close()
