import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cms.models.appmanagers import ApplicationList
from apps.cms.models.modmanagers import ModuleList
from apps.cms.models.menusystem import MenuItem

DATA_DIR = Path(__file__).resolve().parent / "seed_data"


def _blank_to_none(value):
    value = (value or "").strip()
    return value if value else None


def _read_rows(filename):
    with open(DATA_DIR / filename, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = (
        "Seed the CMS navigation hierarchy: ApplicationList (menu), "
        "ModuleList (sub menu) and MenuItem (sub-sub menu, including nested "
        "children via parent_id). Reads from seed_data/*.csv and upserts by "
        "id, so it is safe to re-run."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            app_count = self._seed_applications()
            mod_count = self._seed_modules()
            menu_count = self._seed_menu_items()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {app_count} application(s), {mod_count} module(s), "
                f"{menu_count} menu item(s)."
            )
        )

    def _seed_applications(self):
        rows = _read_rows("cms_applicationlist.csv")
        for row in rows:
            ApplicationList.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "name": row["name"],
                    "description": _blank_to_none(row["description"]),
                    "remark": _blank_to_none(row["remark"]),
                    "status": int(row["status"]),
                    "code": _blank_to_none(row["code"]),
                    "initial": _blank_to_none(row["initial"]),
                    "shortname": _blank_to_none(row["shortname"]),
                    "icon": _blank_to_none(row["icon"]),
                    "order": int(row["order"]),
                },
            )
        return len(rows)

    def _seed_modules(self):
        rows = _read_rows("cms_modulelist.csv")
        for row in rows:
            ModuleList.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "name": row["name"],
                    "description": _blank_to_none(row["description"]),
                    "remark": _blank_to_none(row["remark"]),
                    "status": int(row["status"]),
                    "code": _blank_to_none(row["code"]),
                    "initial": _blank_to_none(row["initial"]),
                    "shortname": _blank_to_none(row["shortname"]),
                    "icon": _blank_to_none(row["icon"]),
                    "order": int(row["order"]),
                    "application_id": int(row["application_id"]),
                },
            )
        return len(rows)

    def _seed_menu_items(self):
        rows = _read_rows("cms_menuitem.csv")
        for row in rows:
            module_id = _blank_to_none(row["module_id"])
            application_id = _blank_to_none(row["application_id"])
            parent_id = _blank_to_none(row["parent_id"])
            MenuItem.objects.update_or_create(
                id=int(row["id"]),
                defaults={
                    "name": row["name"],
                    "description": _blank_to_none(row["description"]),
                    "remark": _blank_to_none(row["remark"]),
                    "status": int(row["status"]),
                    "code": _blank_to_none(row["code"]),
                    "initial": _blank_to_none(row["initial"]),
                    "shortname": _blank_to_none(row["shortname"]),
                    "icon": _blank_to_none(row["icon"]),
                    "url": _blank_to_none(row["url"]),
                    "order": int(row["order"]),
                    "module_id": int(module_id) if module_id else None,
                    "application_id": int(application_id) if application_id else None,
                    "parent_id": int(parent_id) if parent_id else None,
                    "iframe_url": _blank_to_none(row["iframe_url"]),
                },
            )
        return len(rows)
