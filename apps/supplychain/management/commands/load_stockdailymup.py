from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.timezone import now
from apps.supplychain.models.distributions import StDistDaily, Branch, DistributorItem
from datetime import datetime
import mysql.connector
from dateutil.relativedelta import relativedelta
from django.db.models import Max
import os


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--cby", type=int, required=False)  # 🔹 REQUIRED

    def handle(self, *args, **kwargs):
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
            connection = mysql.connector.connect(**mysql_config)
        except Exception as e:
            raise CommandError(f"Failed to connect MySQL: {e}")

        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
                    SELECT *
                    FROM siap_mup.st s 
                    WHERE PERIODE  = (SELECT max(PERIODE) FROM siap_mup.st)
        """
        )
        rows = cursor.fetchall()
        cursor.close()

        cby_id = kwargs["cby"]
        bulk_insert_list = []
        slug_counter = {}

        DISTRIBUTOR_ID = 1
        
        branches = {
            (b.initial, b.distributor_id, b.status): b
            for b in Branch.objects.filter(distributor_id=DISTRIBUTOR_ID)
        }

        distributor_items = {
            di.code.strip(): di.id for di in DistributorItem.objects.all()
        }

        for row in rows:
            row_insert = dict()
            row_insert["kd_prod"] = row["KD_PROD"].strip()
            row_insert["nm_prod"] = row["NM_PROD"].strip()
            row_insert["kd_hrmn"] = row["KD_HRMN"].strip()
            row_insert["nm_hrmn"] = row["NM_HRMN"].strip()
            row_insert["kd_prc"] = row["KD_PRC"].strip()
            row_insert["kd_cab"] = row["KD_CAB"].strip()
            row_insert["id_cab"] = row["ID_CAB"].strip()
            row_insert["nm_cab"] = row["NM_CAB"].strip()
            row_insert["kd_io"] = row["KD_IO"].strip()
            row_insert["lot"] = row["LOT"].strip()
            row_insert["ed"] = (
                datetime.strptime(row["ED"].strip(), "%Y%m%d").date()
                if row["ED"].strip() != ""
                else None
            )
            row_insert["hna"] = float(row["HNA"].strip())
            row_insert["reg"] = row["REG"]
            row_insert["itr"] = row["ITR"]
            row_insert["pp"] = row["PP"]
            row_insert["po"] = row["PO"]
            row_insert["ext"] = row["EXT"]
            row_insert["dmg"] = row["DMG"]
            row_insert["atr"] = row["ATR"]
            row_insert["ket"] = row["KET"]
            row_insert["periode"] = row["PERIODE"]
            # row_insert['tgl_proses'] = datetime.strptime(row['TGL_PROSES'].strip(), "%Y%m%d %H:%M") if row['TGL_PROSES'].strip() != '' else None
            # if row["TGL_PROSES"].strip() != "":
            #     naive_datetime = datetime.strptime(
            #         row["TGL_PROSES"].strip(), "%Y%m%d %H:%M"
            #     )
            #     row_insert["tgl_proses"] = timezone.make_aware(naive_datetime)
            # else:
            #     row_insert["tgl_proses"] = None
            tgl_proses_str = row["TGL_PROSES"].strip()
            if (
                tgl_proses_str
                and tgl_proses_str.replace(" ", "").replace(":", "").isdigit()
            ):
                naive_datetime = datetime.strptime(tgl_proses_str, "%Y%m%d %H:%M")
                row_insert["tgl_proses"] = timezone.make_aware(naive_datetime)
            else:
                row_insert["tgl_proses"] = None

            row_insert["distributor_id"] = 1

            # tgl_proses_code = datetime.strftime(row_insert['tgl_proses'], "%Y%m%d")
            if row_insert["tgl_proses"]:
                tgl_proses_code = row_insert["tgl_proses"].strftime("%Y%m%d")
            else:
                tgl_proses_code = ""

            row_insert["name"] = (
                tgl_proses_code
                + "-"
                + row_insert["nm_prod"]
                + "-"
                + row_insert["kd_hrmn"]
                + "-"
                + row_insert["id_cab"]
            )
            slug = (
                tgl_proses_code
                + "-"
                + row_insert["nm_prod"]
                + "-"
                + row_insert["kd_hrmn"]
                + "-"
                + row_insert["id_cab"]
                + "-"
                + row_insert["lot"]
            )

            if slug in slug_counter:
                slug_counter[slug] += 1
                row_insert["slug"] = slug + "-" + str(slug_counter[slug])
            else:
                slug_counter[slug] = 0
                row_insert["slug"] = slug

            row_insert["status"] = 1
            row_insert["cat"] = now()
            row_insert["cby_id"] = cby_id

            branch_code = (row.get("ID_CAB") or "").strip()
            branch_aliases = {
                "JK1": "JKT1",
                "JK2": "JKT2",
            }
            branch = branches.get(
                (branch_aliases.get(branch_code, branch_code), DISTRIBUTOR_ID, 1)
            )
                
            row_insert["branch"] = branch

            row_insert["distributoritem_id"] = distributor_items.get(
                row_insert["kd_prod"]
            )

            bulk_insert_list.append(StDistDaily(**row_insert))

        mysql_max_date = None
        mysql_max_date_ft = None
        # for row in rows:
        #     if row["TGL_PROSES"] != "":
        #         naive_datetime = datetime.strptime(
        #             rows[0]["TGL_PROSES"].strip(), "%Y%m%d %H:%M"
        #         )
        #         mysql_max_date = timezone.make_aware(naive_datetime)
        #         mysql_max_date_ft = mysql_max_date.strftime("%Y-%m-%d")
        #         break
        for row in rows:
            tgl_proses_str = (row.get("TGL_PROSES") or "").strip()

            if (
                tgl_proses_str
                and tgl_proses_str.replace(" ", "").replace(":", "").isdigit()
            ):
                try:
                    naive_datetime = datetime.strptime(tgl_proses_str, "%Y%m%d %H:%M")
                    mysql_max_date = timezone.make_aware(naive_datetime)
                    mysql_max_date_ft = mysql_max_date.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

        # StDistDaily.objects.filter(tgl_proses__gte=mysql_max_date).delete()
        if mysql_max_date:
            StDistDaily.objects.filter(tgl_proses__gte=mysql_max_date).delete()
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Skip delete: mysql_max_date is None (no valid TGL_PROSES)"
                )
            )

        created_obj = StDistDaily.objects.bulk_create(
            bulk_insert_list,
            batch_size=10000,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Success Inserted: {len(created_obj)} rows.")
        )

        if mysql_max_date and mysql_max_date.day == 1:
            filter_period = mysql_max_date - relativedelta(months=4)
            filter_period_str = filter_period.strftime("%Y%m")

            max_tgl_proses = StDistDaily.objects.filter(
                periode=filter_period_str
            ).aggregate(Max("tgl_proses"))["tgl_proses__max"]

            if max_tgl_proses:
                StDistDaily.objects.filter(
                    periode=filter_period_str, tgl_proses__lt=max_tgl_proses
                ).delete()
