# ============================================================
#  Name: seed_analytics_import
#  Type: Management command
#  Purpose: Run the translation seeder without opening DBeaver
# ------------------------------------------------------------
#  Path: apps\analytics\management\commands\seed_analytics_import.py
#  Created: Sep/07-2026 by Akram
#  Updates: ?
# ============================================================
# The SQL file stays the single source of truth, this only executes it
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

MODULE = "analytics_import"
DEFAULT_SQL = os.path.join(
    "apps", "analytics", "seeders", "seed_analytics_import.sql"
)

COUNT_SQL = """
SELECT
    (SELECT count(*) FROM base_translation_key k
       JOIN base_translation_module m ON m.id = k.module_id
      WHERE m.code = %s),
    (SELECT count(*) FROM base_translation t
       JOIN base_translation_key k ON k.id = t.translation_key_id
       JOIN base_translation_module m ON m.id = k.module_id
      WHERE m.code = %s)
"""


class Command(BaseCommand):
    help = "Seed the analytics_import translation module from its SQL file"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=None, help="Path to the SQL file")
        parser.add_argument("--cby", type=int, default=1, help="User id for cby_id")
        parser.add_argument(
            "--no-cache-clear", action="store_true",
            help="Skip clearing the translation cache",
        )

    def counts(self):
        with connection.cursor() as cursor:
            cursor.execute(COUNT_SQL, [MODULE, MODULE])
            return cursor.fetchone()

    def handle(self, *args, **options):
        path = options["file"] or os.path.join(settings.BASE_DIR, DEFAULT_SQL)
        if not os.path.exists(path):
            raise CommandError(f"SQL file not found: {path}")

        # cby_id is hardcoded in the SQL, a missing user breaks the insert
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM auth_user WHERE id = %s", [options["cby"]])
            if cursor.fetchone() is None:
                raise CommandError(
                    f"User id {options['cby']} not found. "
                    f"Pick an existing id and adjust cby_id in the SQL file."
                )

        before = self.counts()
        self.stdout.write(f"Before : {before[0]} keys, {before[1]} translations")

        sql = open(path, encoding="utf-8").read()
        # The file carries its own BEGIN and COMMIT
        with connection.cursor() as cursor:
            cursor.execute(sql)

        after = self.counts()
        self.stdout.write(f"After  : {after[0]} keys, {after[1]} translations")
        self.stdout.write(
            f"Added  : {after[0] - before[0]} keys, "
            f"{after[1] - before[1]} translations"
        )

        if not options["no_cache_clear"]:
            try:
                from apps.base.utils.translation import clear_translation_cache
                clear_translation_cache(MODULE)
                self.stdout.write("Cache cleared")
            except Exception as error:
                self.stdout.write(self.style.WARNING(
                    f"Cache not cleared: {type(error).__name__}: {error}. "
                    f"Clear it manually before checking the page."
                ))

        if after[0] != 187 or after[1] != 374:
            self.stdout.write(self.style.WARNING(
                f"Expected 187 | 374, got {after[0]} | {after[1]}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("Seeder OK, 187 | 374"))