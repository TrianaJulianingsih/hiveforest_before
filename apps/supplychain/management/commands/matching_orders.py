from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--uby', type=int, required=False)  #

    def update_field_dodetail(self, uby_id):
        query = f"""
        WITH tbl_matched AS (
            SELECT 
                dd.id, 
                mfi.id AS item_id,
                br.id AS branch_id,
                CASE WHEN SUBSTRING(TRIM(dd.so) FROM 3) ~ '^\d+$' 
                    AND mfi.id IS NOT NULL 
                    AND mfi.product_id IS NOT NULL 
                THEN
                    CONCAT(
                        SUBSTRING(TRIM(dd.so) FROM 3), '-',
                        br.id,'-',
                        mfi.product_id
                    )
                END AS match_code
            FROM ( 
                SELECT id, so, shipto_code, item_number
                FROM supplychain_dodetail
                WHERE item_id IS NULL OR branch_id IS NULL OR match_code IS NULL OR match_code = ''
            ) dd
            LEFT JOIN supplychain_manufacturingitem mfi
                ON dd.item_number = trim(mfi.code)
            LEFT JOIN (
                SELECT
                    id,
                    trim(value) AS shipto
                FROM supplychain_branch b,
                    regexp_split_to_table(b.shipto, '\|') AS value
                WHERE 
                    b.shipto IS NOT NULL 
                    AND b.shipto <> ''
                    AND status = 1
            ) br
                ON dd.shipto_code = br.shipto
        )
        UPDATE supplychain_dodetail d
        SET
            item_id = COALESCE(tbl.item_id, d.item_id),
            branch_id = COALESCE(tbl.branch_id, d.branch_id),
            match_code = COALESCE(tbl.match_code, d.match_code),
            uat = CURRENT_TIMESTAMP,
            uby_id = {uby_id}
        FROM( 
            SELECT * 
            FROM tbl_matched
            WHERE item_id IS NOT NULL OR 
                branch_id IS NOT NULL OR
                (match_code IS NOT NULL AND match_code != '')
        ) tbl
        WHERE d.id = tbl.id
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
            self.stdout.write(self.style.SUCCESS("Doned Update field dodetail"))
        except Exception as e:
            raise ValueError(f"Failed update field dodetail: {e}")

    def update_field_podetail(self, uby_id):
        query = f"""
        WITH tbl_matched AS (
            SELECT
                pd.id , dit.id AS item_id, br.id AS branch_id,
                CASE WHEN pd.nomor_po IS NOT NULL  
                    AND dit.id IS NOT NULL 
                    AND dit.product_id IS NOT NULL 
                THEN
                    CONCAT(
                        pd.nomor_po, '-',
                        br.id,'-',
                        dit.product_id
                    )
                END AS match_code
            FROM ( 
                SELECT id, nomor_po, items, cabang
                FROM supplychain_podetail
                WHERE 
                    item_id IS NULL OR 
                    branch_id IS NULL OR
                    match_code IS NULL OR 
                    match_code = ''
            ) pd
            LEFT JOIN supplychain_distributoritem dit
                ON pd.items = trim(dit.code)
            LEFT JOIN (
                SELECT
                    id,
                    initial,
                    distributor_id
                FROM supplychain_branch b
                WHERE 
                    status = 1
            ) br
                ON pd.cabang = br.initial AND br.distributor_id = dit.distributor_id
        )

        UPDATE supplychain_podetail d
        SET
            item_id = COALESCE(tbl.item_id, d.item_id),
            branch_id = COALESCE(tbl.branch_id, d.branch_id),
            match_code = COALESCE(tbl.match_code, d.match_code),
            uat = CURRENT_TIMESTAMP,
            uby_id = {uby_id}
        FROM( 
            SELECT id, item_id, branch_id, match_code
            FROM tbl_matched
            WHERE item_id IS NOT NULL OR 
                branch_id IS NOT NULL OR
                (match_code IS NOT NULL AND match_code != '')
        ) tbl
        WHERE d.id = tbl.id;
                
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
            self.stdout.write(self.style.SUCCESS("Doned Update field podetail"))
        except Exception as e:
            raise ValueError(f"Failed update field podetail: {e}")
    
    def matching(self, uby_id):
        query = f"""
        UPDATE supplychain_dodetail tbl_trg
        SET
            podetail_id = tbl_src.po_id,
            uat = CURRENT_TIMESTAMP,
            uby_id = {uby_id}
        FROM (
            SELECT dd.id AS do_id, pd.id AS po_id
            FROM supplychain_dodetail dd
            LEFT JOIN supplychain_podetail pd
                ON dd.match_code = pd.match_code 
            WHERE 
                dd.podetail_id IS NULL AND 
                pd.id IS NOT NULL 
        ) tbl_src
        WHERE 
            tbl_trg.id = tbl_src.do_id
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
            self.stdout.write(self.style.SUCCESS("Doned Matching Between PODetail and DODetail"))
        except Exception as e:
            raise ValueError(f"Failed Matching Between PODetail and DODetail: {e}")

    def handle(self, *args, **kwargs):
        help = "Matching Between DO Detail and PO Detail"

        self.stdout.write(self.style.NOTICE("Start Match Delivery"))
        uby_id = kwargs['uby']

        self.update_field_dodetail(uby_id)
        self.update_field_podetail(uby_id)
        self.matching(uby_id)