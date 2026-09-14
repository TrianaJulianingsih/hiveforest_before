import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cms.models.appmanagers import ApplicationList

DATA_DIR = Path(__file__).resolve().parent / "seed_data"


def _blank_to_none(value):
    value = (value or "").strip()
    return value if value else None


class Command(BaseCommand):
    help = (
        "Seed English/Indonesian shortname translations (shortname_en, "
        "shortname_ind) for ApplicationList rows. Run seed_menu first so "
        "the ApplicationList rows exist."
    )

    def handle(self, *args, **options):
        with open(
            DATA_DIR / "cms_applicationlist.csv", encoding="utf-8-sig", newline=""
        ) as f:
            rows = list(csv.DictReader(f))

        updated = 0
        missing = []
        with transaction.atomic():
            for row in rows:
                app_id = int(row["id"])
                changed = ApplicationList.objects.filter(id=app_id).update(
                    shortname_en=_blank_to_none(row["shortname_en"]),
                    shortname_ind=_blank_to_none(row["shortname_ind"]),
                )
                if changed:
                    updated += 1
                else:
                    missing.append(app_id)

        if missing:
            raise CommandError(
                f"ApplicationList id(s) not found, run seed_menu first: {missing}"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Updated translations for {updated} application(s).")
        )
