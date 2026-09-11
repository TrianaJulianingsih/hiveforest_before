import hashlib

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Inspect or terminate PostgreSQL advisory locks used by PandasImportMixin imports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lock-name",
            required=True,
            help="Full import lock name, e.g. bom.freightcostdetail.pandas_import",
        )
        parser.add_argument(
            "--terminate",
            action="store_true",
            help="Terminate backend sessions currently holding the specified lock.",
        )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("import_lock hanya tersedia untuk PostgreSQL.")

        lock_name = options["lock_name"].strip()
        if not lock_name:
            raise CommandError("--lock-name wajib diisi.")

        lock_id = self._get_lock_id(lock_name)
        lock_rows = self._get_lock_rows(lock_id)

        self.stdout.write(f"lock_name={lock_name}")
        self.stdout.write(f"lock_id={lock_id}")

        if not lock_rows:
            self.stdout.write(self.style.WARNING("Tidak ada holder lock aktif."))
            return

        for row in lock_rows:
            started_at = row["query_start"]
            started_at_text = (
                timezone.localtime(started_at).strftime("%Y-%m-%d %H:%M:%S")
                if started_at is not None
                else "-"
            )
            self.stdout.write(
                " | ".join(
                    [
                        f"pid={row['pid']}",
                        f"user={row['usename']}",
                        f"client={row['client_addr'] or '-'}",
                        f"state={row['state'] or '-'}",
                        f"query_start={started_at_text}",
                        f"granted={row['granted']}",
                        f"query={row['query'] or '-'}",
                    ]
                )
            )

        if not options["terminate"]:
            return

        terminated_pids = []
        with connection.cursor() as cursor:
            for row in lock_rows:
                cursor.execute("SELECT pg_terminate_backend(%s)", [row["pid"]])
                result = cursor.fetchone()
                if result and result[0]:
                    terminated_pids.append(row["pid"])

        if terminated_pids:
            self.stdout.write(
                self.style.SUCCESS(
                    "Terminated backend(s): " + ", ".join(str(pid) for pid in terminated_pids)
                )
            )
            return

        raise CommandError("Lock ditemukan, tetapi backend tidak berhasil dihentikan.")

    def _get_lock_id(self, lock_name):
        digest = hashlib.sha1(lock_name.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    def _get_lock_rows(self, lock_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.pid,
                    a.usename,
                    a.application_name,
                    a.client_addr::text,
                    a.state,
                    a.query_start,
                    a.xact_start,
                    a.state_change,
                    LEFT(a.query, 200) AS query,
                    l.granted
                FROM pg_locks l
                JOIN pg_stat_activity a ON a.pid = l.pid
                WHERE l.locktype = 'advisory'
                  AND ((l.classid::bigint << 32) + l.objid::bigint) = %s
                ORDER BY a.query_start NULLS LAST, a.pid
                """,
                [lock_id],
            )
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]