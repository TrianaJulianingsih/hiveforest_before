from __future__ import annotations

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

try:  # Optional dependency for precise month math
    from dateutil.relativedelta import relativedelta
except ImportError:  # pragma: no cover - fallback when python-dateutil absent
    relativedelta = None


class Command(BaseCommand):
    help = "Aggregate distributor stock (StDistDaily) into BranchStock master."

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            type=int,
            default=3,
            help="Number of trailing months to aggregate when start-date not provided (default: 3).",
        )
        parser.add_argument(
            "--days",
            type=int,
            help="Optional number of trailing days to aggregate when start-date not provided. Overrides --months when set.",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            help="Optional lower date boundary in YYYY-MM-DD format. Overrides --months.",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="Optional upper date boundary in YYYY-MM-DD format (inclusive). Defaults to today.",
        )

    def handle(self, *args, **options):
        end_date = self._parse_date(options.get("end_date")) or timezone.now().date()
        start_date = self._parse_date(options.get("start_date"))
        months = options["months"]
        days = options.get("days")

        if months is not None and months < 0:
            raise CommandError("months must be zero or positive")
        if days is not None and days < 0:
            raise CommandError("days must be zero or positive")

        if start_date is None:
            if days is not None:
                start_date = end_date - timedelta(days=days)
            elif relativedelta is not None:
                start_date = end_date - relativedelta(months=months)
            else:
                start_date = end_date - timedelta(days=months * 30)

        if start_date > end_date:
            raise CommandError("start-date must be on or before end-date")

        self.stdout.write(
            f"Aggregating branch stock from {start_date.isoformat()} to {end_date.isoformat()}"
        )

        aggregated_rows = self._aggregate_branch_stock(start_date, end_date)
        self.stdout.write(
            self.style.SUCCESS(f"Upserted {aggregated_rows} branch stock rows.")
        )

    def _aggregate_branch_stock(self, start_date, end_date):
        sql = """
            WITH aggregated AS (
                SELECT
                    wp.branch_id,
                    di.product_id,
                    COALESCE(sd.nm_prod, '') AS product_name,
                    p.subgroup_id AS team_id,
                    sps.group_id,
                    (sd.tgl_proses AT TIME ZONE 'Asia/Jakarta')::date AS trx_date,
                    SUM(COALESCE(sd.reg, 0)) AS total_reg
                FROM supplychain_stdistdaily sd
                JOIN supplychain_distributoritem di
                    ON di.id = sd.distributoritem_id
                JOIN base_warehousepalette wp
                    ON wp.branch_id = sd.branch_id
                LEFT JOIN sales_product p
                    ON p.id = di.product_id
                LEFT JOIN sales_productsubgroup sps
                    ON sps.id = p.subgroup_id
                WHERE sd.branch_id IS NOT NULL
                  AND sd.distributoritem_id IS NOT NULL
                  AND (sd.tgl_proses AT TIME ZONE 'Asia/Jakarta')::date BETWEEN %(start_date)s AND %(end_date)s
                                GROUP BY 1, 2, 3, 4, 5, 6
            )
            INSERT INTO supplychain_branchstock (
                name,
                description,
                remark,
                status,
                slug,
                cat,
                cby_id,
                uat,
                uby_id,
                dat,
                dby_id,
                deleted,
                branch_id,
                product_id,
                product_name,
                team_id,
                group_id,
                trx_date,
                total_reg
            )
            SELECT
                CONCAT_WS('-', b.code, COALESCE(p.code, agg.product_name), TO_CHAR(agg.trx_date, 'YYYYMMDD')) AS name,
                '',
                '',
                1,
                NULL,
                NOW(),
                32,
                NULL,
                NULL,
                NULL,
                NULL,
                FALSE,
                agg.branch_id,
                agg.product_id,
                agg.product_name,
                agg.team_id,
                agg.group_id,
                agg.trx_date,
                agg.total_reg
            FROM aggregated agg
            JOIN supplychain_branch b ON b.id = agg.branch_id
            LEFT JOIN sales_product p ON p.id = agg.product_id
            ON CONFLICT (branch_id, product_name, trx_date)
            DO NOTHING;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, {"start_date": start_date, "end_date": end_date})
            # rowcount returns upserts count (number of rows inserted OR updated)
            return cursor.rowcount

    def _parse_date(self, value: str | None):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:  # pragma: no cover - user input branch
            raise CommandError(
                f"Invalid date format '{value}'. Use YYYY-MM-DD."
            ) from exc
