"""
seed_sub_distributor_menu_and_translations.py
Management command to seed:
1. TranslationModule, TranslationKey, and Translation for Sub-Distributor ('sub_distributor')
2. CMS MenuItem for Sub-Distributor Dashboard and Sub-Distributor Maintenance List

Usage:
    python manage.py seed_sub_distributor_menu_and_translations
    python manage.py seed_sub_distributor_menu_and_translations --force
"""

from django.core.management.base import BaseCommand
from apps.base.models.translation import TranslationModule, TranslationKey, Translation
from apps.cms.models.app_managers_models import ApplicationList
from apps.cms.models.module_managers_models import ModuleList
from apps.cms.models.menu_system_models import MenuItem


TRANSLATION_MODULE_CODE = "sub_distributor"
TRANSLATION_MODULE_NAME = "Sub-Distributor Module"
TRANSLATION_MODULE_DESC = "Translations for Sub-Distributor maintenance and analytics dashboard"

TRANSLATION_KEYS = {
    # ── Page Titles & Headings ────────────────────────────────
    "page_title": ("Sub-Distributor Maintenance", "Pemeliharaan Sub-Distributor"),
    "dashboard_title": ("Sub-Distributor Dashboard", "Dashboard Sub-Distributor"),
    "dashboard_subtitle": (
        "Interactive overview, regional distributions, and operational maintenance for Sub-Distributors.",
        "Ikhtisar interaktif, sebaran regional, dan pemeliharaan operasional Sub-Distributor."
    ),
    "add_title": ("Add Sub-Distributor", "Tambah Sub-Distributor"),
    "table_title": ("Sub-Distributor Data List", "Daftar Data Sub-Distributor"),
    "map_title": ("Geographical Distribution Map", "Peta Distribusi Geografis"),
    "status_chart_title": ("Operational Ratio", "Rasio Operasional"),
    "station_chart_title": ("Sub-Distributors by Station (Top 8)", "Sub-Distributor per Stasiun (Top 8)"),

    # ── Action Buttons ─────────────────────────────────────────
    "btn_add": ("Add Sub-Distributor", "Tambah Sub-Distributor"),
    "btn_filter": ("Filter", "Filter"),
    "btn_reset": ("Reset", "Reset"),
    "btn_list": ("Sub-Distributor List", "Daftar Sub-Distributor"),
    "btn_back": ("Back to List", "Kembali ke Daftar"),
    "btn_save": ("Save", "Simpan"),
    "btn_cancel": ("Cancel", "Batal"),
    "btn_yes_remove": ("Yes, Remove!", "Ya, Hapus!"),
    "btn_search": ("Search", "Cari"),

    # ── Table Column Headers ──────────────────────────────────
    "col_name": ("Name", "Nama"),
    "col_code": ("Code", "Kode"),
    "col_shortname": ("Short Name", "Nama Singkat"),
    "col_address": ("Address", "Alamat"),
    "col_station": ("Station", "Stasiun"),
    "col_district": ("District", "Kecamatan"),
    "col_regency": ("Regency", "Kabupaten/Kota"),
    "col_province": ("Province", "Provinsi"),
    "col_subdist": ("Sub-Distributor", "Sub-Distributor"),
    "col_status": ("Status", "Status"),

    # ── Table Filters & Placeholders ──────────────────────────
    "search_name": ("Filter Name", "Cari Nama"),
    "search_code": ("Filter Code", "Cari Kode"),
    "search_shortname": ("Filter Short Name", "Cari Nama Singkat"),
    "search_customer_placeholder": ("Search customer by name or code...", "Cari pelanggan berdasarkan nama atau kode..."),
    "all_status": ("All Status", "Semua Status"),
    "status_active": ("Active", "Aktif"),
    "status_inactive": ("Inactive", "Nonaktif"),
    "no_data": ("No sub-distributor data found.", "Tidak ada data sub-distributor."),

    # ── Metric / KPI Cards ────────────────────────────────────
    "kpi_total": ("Total Sub-Distributor", "Total Sub-Distributor"),
    "kpi_total_desc": ("All Registered", "Semua Terdaftar"),
    "kpi_active": ("Active Operations", "Status Aktif"),
    "kpi_active_desc": ("Operational", "Operasional"),
    "kpi_inactive": ("Inactive / Pending", "Status Nonaktif"),
    "kpi_inactive_desc": ("Non-Operational", "Non-Operasional"),
    "kpi_coverage": ("Coverage", "Cakupan"),
    "kpi_stations": ("Stations", "Stasiun"),
    "kpi_provinces": ("Provinces", "Provinsi"),
    "kpi_geotagged": ("Geotagged Locations", "Lokasi Terpetakan"),
    "kpi_unmapped": ("without coordinates", "tanpa koordinat"),
    "kpi_of_total": ("of total", "dari total"),

    # ── Confirmations & Messages ──────────────────────────────
    "confirm_title": ("Confirmation", "Konfirmasi"),
    "confirm_remove_subdist": (
        "Are you sure you want to remove Sub-Distributor status?",
        "Apakah Anda yakin ingin menghapus status Sub-Distributor?"
    ),
    "yes": ("Yes", "Ya"),
    "no": ("No", "Tidak"),
    "select_customer_to_add": ("Select Customer to Add", "Pilih Pelanggan untuk Ditambahkan"),
    "customer_added_success": (
        "Customer added successfully as Sub-Distributor.",
        "Pelanggan berhasil ditambahkan sebagai Sub-Distributor."
    ),
}


class Command(BaseCommand):
    help = "Seed translations and CMS Menu items for Sub-Distributor module"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing translation and menu values",
        )

    def handle(self, *args, **options):
        force = options["force"]
        self.stdout.write(self.style.MIGRATE_HEADING("=== Seeding Sub-Distributor Translations & Menus ==="))

        # ── 1. Seed Translations ───────────────────────────────────────
        self.stdout.write(self.style.HTTP_INFO("\n[1/2] Seeding Translation Module & Keys..."))
        module, mod_created = TranslationModule.objects.get_or_create(
            code=TRANSLATION_MODULE_CODE,
            defaults={
                "name": TRANSLATION_MODULE_NAME,
                "description": TRANSLATION_MODULE_DESC,
                "status": 1,
            },
        )
        if mod_created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Translation Module created: {TRANSLATION_MODULE_CODE}"))
        else:
            self.stdout.write(f"  [=] Translation Module exists: {TRANSLATION_MODULE_CODE}")

        created_keys = 0
        updated_keys = 0
        created_trans = 0
        updated_trans = 0

        for key_code, (en_val, id_val) in TRANSLATION_KEYS.items():
            trans_key, k_created = TranslationKey.objects.get_or_create(
                module=module,
                key=key_code,
                defaults={
                    "name": key_code.replace("_", " ").title(),
                    "default_value": en_val,
                    "status": 1,
                },
            )
            if k_created:
                created_keys += 1
            elif force:
                trans_key.default_value = en_val
                trans_key.save(update_fields=["default_value"])
                updated_keys += 1

            # EN Translation
            t_en, ten_created = Translation.objects.get_or_create(
                translation_key=trans_key,
                language="en",
                defaults={"value": en_val, "status": 1},
            )
            if ten_created:
                created_trans += 1
            elif force:
                t_en.value = en_val
                t_en.save(update_fields=["value"])
                updated_trans += 1

            # ID Translation
            t_id, tid_created = Translation.objects.get_or_create(
                translation_key=trans_key,
                language="id",
                defaults={"value": id_val, "status": 1},
            )
            if tid_created:
                created_trans += 1
            elif force:
                t_id.value = id_val
                t_id.save(update_fields=["value"])
                updated_trans += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Translations seeded: Keys (created={created_keys}, updated={updated_keys}) | "
                f"Values (created={created_trans}, updated={updated_trans})"
            )
        )

        # ── 2. Seed CMS Menu Items ─────────────────────────────────────
        self.stdout.write(self.style.HTTP_INFO("\n[2/2] Seeding CMS Menu Items..."))

        # Find or create Application (BOM / Business Operations Management)
        app = (
            ApplicationList.objects.filter(name__icontains="BOM").first()
            or ApplicationList.objects.filter(code__icontains="BOM").first()
            or ApplicationList.objects.filter(name__icontains="Operation").first()
            or ApplicationList.objects.first()
        )

        # Find or create ModuleList
        mod = None
        if app:
            mod = (
                ModuleList.objects.filter(application=app, name__icontains="Customer").first()
                or ModuleList.objects.filter(application=app, name__icontains="Distributor").first()
                or ModuleList.objects.filter(application=app).first()
            )

        # Menu 1: Sub-Distributor Dashboard
        menu_dash_code = "BOM-SD-DASH"
        menu_dash_url = "/bom/customer-maintenance/sub-distributor/dashboard/"
        menu_dash, dash_created = MenuItem.objects.get_or_create(
            code=menu_dash_code,
            defaults={
                "name": "Sub-Distributor Dashboard",
                "shortname": "Sub-Dist Dashboard",
                "initial": "SDD",
                "application": app,
                "module": mod,
                "icon": "nav-icon fas fa-chart-pie",
                "url": menu_dash_url,
                "order": 1,
                "status": 1,
                "deleted": False,
            },
        )
        if dash_created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Menu Item created : {menu_dash.name} ({menu_dash_url})"))
        else:
            if force:
                menu_dash.name = "Sub-Distributor Dashboard"
                menu_dash.shortname = "Sub-Dist Dashboard"
                menu_dash.url = menu_dash_url
                menu_dash.icon = "nav-icon fas fa-chart-pie"
                menu_dash.application = app
                menu_dash.module = mod
                menu_dash.status = 1
                menu_dash.deleted = False
                menu_dash.save()
                self.stdout.write(self.style.SUCCESS(f"  [^] Menu Item updated : {menu_dash.name}"))
            else:
                self.stdout.write(f"  [=] Menu Item exists  : {menu_dash.name} ({menu_dash.code})")

        # Menu 2: Sub-Distributor Maintenance List
        menu_list_code = "BOM-SD-LIST"
        menu_list_url = "/bom/customer-maintenance/sub-distributor/"
        menu_list, list_created = MenuItem.objects.get_or_create(
            code=menu_list_code,
            defaults={
                "name": "Sub-Distributor Maintenance",
                "shortname": "Sub-Distributor",
                "initial": "SDM",
                "application": app,
                "module": mod,
                "icon": "nav-icon fas fa-truck-loading",
                "url": menu_list_url,
                "order": 2,
                "status": 1,
                "deleted": False,
            },
        )
        if list_created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Menu Item created : {menu_list.name} ({menu_list_url})"))
        else:
            if force:
                menu_list.name = "Sub-Distributor Maintenance"
                menu_list.shortname = "Sub-Distributor"
                menu_list.url = menu_list_url
                menu_list.icon = "nav-icon fas fa-truck-loading"
                menu_list.application = app
                menu_list.module = mod
                menu_list.status = 1
                menu_list.deleted = False
                menu_list.save()
                self.stdout.write(self.style.SUCCESS(f"  [^] Menu Item updated : {menu_list.name}"))
            else:
                self.stdout.write(f"  [=] Menu Item exists  : {menu_list.name} ({menu_list.code})")

        self.stdout.write(self.style.SUCCESS("\nAll Sub-Distributor translations and CMS menu items seeded successfully!"))
