from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from pytz import timezone as pytz_timezone
import mysql.connector
from psycopg2.extras import execute_values
from apps.base.utils.chronos import hive_dateparser
from dateutil.relativedelta import relativedelta
import os
import zlib
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Sync ARBalance from MySQL to PostgreSQL for current month"
    user_tz = pytz_timezone(getattr(settings, 'DEFAULT_LOG_TIMEZONE', 'Asia/Jakarta'))

    def log(self, message):
        timestamp = timezone.now().astimezone(self.user_tz).strftime('%Y-%m-%d %H:%M:%S')
        user = getattr(self, 'user', 'None')
        username = user.username if user else 'UnknownUser'

        sync_id = getattr(self, 'sync_id', 'nosync')
        log_line = f"{timestamp}: [{sync_id}] {username}, {message}"
        #print(log_line, flush=True)
        log_file = '/var/log/hiveforest/sync_arbalance.log'
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

    def add_arguments(self, parser):
        parser.add_argument('--cby', type=int, required=True)

    def handle(self, *args, **options):
        cby_id = options['cby']
        # Fetch user object by ID to get username
        try:
            self.user = User.objects.get(id=cby_id)
            username = self.user.username
        except User.DoesNotExist:
            self.user = None
            username = f'UserID_{cby_id}'  # Fallback if user not found
            print(f"Warning: User with ID {cby_id} not found, using fallback username")

        self.sync_id = timezone.now().strftime("%H%M%S") + "-" + str(cby_id)  # for logging
        self.log(f"🚀 Starting ARBalance sync for user {username}")

        now = timezone.now().astimezone(self.user_tz)
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        next_month_start = (now + relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        self.log(f"🗓️  Processing month: {current_month_start.strftime('%Y-%m')}")
        
        # STEP 1 Start the deletion process
        with connection.cursor() as cursor:
            self.log("🧹 Deleting current month data from finance_arbalance...")
            
            cursor.execute("""
                DELETE FROM finance_arbalance
                WHERE date_proses >= %s AND date_proses < %s
            """, [current_month_start, next_month_start])

            deleted_count = cursor.rowcount
            self.log(f"🗑️ Deleted {deleted_count} rows for {current_month_start.strftime('%B %Y')}")

        # STEP 2 Fetch and validate
        MYSQL_CONFIG = {
            "host": os.environ.get("DB_AR_BALANCE_HOST"),
            "user": os.environ.get("DB_AR_USER"),
            "password": os.environ.get("DB_AR_PASSWORD"),
            "database": os.environ.get("DB_AR_DATABASE"),
            "port": int(os.environ.get("DB_AR_BALANCE_PORT", "3306")),
        }
        mysql_conn = None
        mysql_cursor = None

        self.log("📥 Fetching data from MySQL...")

        try:
            mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
            mysql_cursor = mysql_conn.cursor(dictionary=True)

            mysql_cursor.execute("SELECT * FROM ar_outstanding")
            data = mysql_cursor.fetchall()
            row_count = len(data)

            self.log(f"📊 Fetched {row_count} rows from MySQL ar_outstanding")

        except mysql.connector.Error as err:
            self.log(f"❌ MySQL error: {err}")
            raise

        finally:
            if mysql_cursor:
                mysql_cursor.close()
            if mysql_conn:
                mysql_conn.close()

        # STEP 3: Locking
        # Lock key and ID (per month)
        lock_key = f"sync_arbalance_{current_month.strftime('%Y%m')}"
        lock_id = zlib.crc32(lock_key.encode())

        now = timezone.now()
        insert_data = []
        failed_rows = 0

        # STEP 4: Insertion
        for i, row in enumerate(data):
            try:
                insert_data.append((
                    row["TIPE"], row["NC_NP_SEGMENTASI"], row["TRX_NUMBER"], row["PARTY_ID"],
                    row["CUST_ACCOUNT_ID"], row["CUST_ACCOUNT_NUMBER"], row["CUST_ACCOUNT_NAME"],
                    row["ORGANIZATION_NAME"], row["NAME"], row["PARTY_SITE_NAME"], row["CUSTOMER_LOCATION"],
                    row["CUST_CLASS_CODE"], row["STATUS"], row["NAMA_SALESMAN"], row["NAMA_COLLECTOR"],
                    row["PENJAMINAN"], hive_dateparser(row["TRX_DATE"], raise_error=True, tz=self.user_tz),
                    row["PAYMENT_TERMS"], hive_dateparser(row["DUE_DATE"], raise_error=True, tz=self.user_tz),
                    row["UMUR_PIUTANG"], row["TAX_DOCUMENT_NUMBER"], row["ITEM_CATEGORY"], row["ITEM_CODE"],
                    row["ITEM_DESCRIPTION"], row["AMOUNT"], row["TOTAL_APPLIED"], row["BALANCE"],
                    row["CURRENT_DUE"], row["DUE_0_30"], row["DUE_31_60"], row["DUE_61_90"], row["DUE_91_120"],
                    row["DUE_121_150"], row["DUE_151_180"], row["DUE_181_364"], row["DUE_365"],
                    row["DUE_ABOVE_365"], row["DUE_91_180"], row["DUE_181_365"], row["DUE_366_730"],
                    row["DUE_ABOVE_730"], hive_dateparser(row["TANGGAL_HITUNG"], raise_error=True, tz=self.user_tz),
                    row["KC_KP_SEGMENTASI"], hive_dateparser(row["TGLFAKTUR"], raise_error=True, tz=self.user_tz),
                    row["KET_DUE"], row["APPROVAL_PENJAMINAN_DOC_NO"], row["KODEVENDOR"], row["KODEVENDOR1"],
                    row["NAMAVENDOR"], row["GRUP_PRODUK"], row["GROUP_PRODUK"], row["BRANCH"], row["BRANCH_CODE"],
                    row["BRANCH_NAME"], row["KELAS"], row["CEK1"], row["KET_DUE_2"], row["KET_GRUP_1"],
                    row["KET_GRUP_2"], hive_dateparser(row["DATE_PROSES"], raise_error=True).date(),
                    row["MONTH_TRANSAKSI"], hive_dateparser(row["TIME_PROSES"], raise_error=True, tz=self.user_tz),
                    f"{row['TIPE']} {row['TRX_NUMBER']}", 1, now, cby_id, False
                ))
            except Exception as row_error:
                failed_rows += 1
                self.log(f"⚠️ Skipping row {i+1}: {row_error}")

        if failed_rows > 0:
            self.log(f"⚠️ {failed_rows} rows skipped due to errors")

        # 🔐 LOCK → INSERT → UNLOCK
        with connection.cursor() as lock_cursor:
            lock_cursor.execute("SELECT pg_try_advisory_lock(%s)", [lock_id])
            got_lock = lock_cursor.fetchone()[0]

        if not got_lock:
            self.log(f"⏭️ Insert skipped: another sync is inserting for {lock_key}")
            return

        try:
            self.log("📤 Inserting new data...")
            insert_query = """
                INSERT INTO finance_arbalance (
                    tipe, nc_np_segmentasi, trx_number, party_id, cust_account_id,
                    cust_account_number, cust_account_name, organization_name, trxname,
                    party_site_name, customer_location, cust_class_code, ownstatus,
                    nama_salesman, nama_collector, penjaminan, trx_date, payment_terms,
                    due_date, umur_piutang, tax_document_number, item_category, item_code,
                    item_description, amount, total_applied, balance, current_due,
                    due_0_30, due_31_60, due_61_90, due_91_120, due_121_150, due_151_180,
                    due_181_364, due_365, due_above_365, due_91_180, due_181_365,
                    due_366_730, due_above_730, tanggal_hitung, kc_kp_segmentasi, tglfaktur,
                    ket_due, approval_penjaminan_doc_no, kodevendor, kodevendor1, namavendor,
                    grup_produk, group_produk, branch, branch_code, branch_name, kelas,
                    cek1, ket_due_2, ket_group_1, ket_group_2, date_proses, month_transaksi,
                    time_proses, name, status, cat, cby_id, deleted
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """

            total_inserted = 0
            batch_size = 500

            with connection.cursor() as cursor:
                for i in range(0, len(insert_data), batch_size):
                    batch = insert_data[i:i + batch_size]
                    try:
                        execute_values(cursor, insert_query, batch)
                        total_inserted += len(batch)
                    except Exception as e:
                        self.log(f"❌ Failed inserting batch {i}-{i+batch_size}: {e}")
                        raise

            self.log(f"✅ Sync completed successfully after full insert.")
            self.log(f"📊 Total: {len(data)} fetched → {total_inserted} inserted")

        finally:
            with connection.cursor() as unlock_cursor:
                unlock_cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
                self.log(f"🔓 Lock released for {lock_key}")
