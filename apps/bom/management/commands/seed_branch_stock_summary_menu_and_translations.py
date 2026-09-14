"""
seed_branch_stock_summary_menu_and_translations.py
Management command to seed:
1. TranslationModule, TranslationKey, and Translation for Branch Stock Summary ('branch_stock_summary')
2. CMS MenuItem for Branch Stock Summary Dashboard (/bom/branchstocksummary/dashboard/) and Report List (/bom/branchstocksummary/user/)
3. Permission assignment for CMSPermission records

Usage:
    python manage.py seed_branch_stock_summary_menu_and_translations
    python manage.py seed_branch_stock_summary_menu_and_translations --force
"""

from django.core.management.base import BaseCommand
from apps.base.models.translation import TranslationModule, TranslationKey, Translation
from apps.base.models.permissions import CMSPermission
from apps.cms.models.app_managers_models import ApplicationList
from apps.cms.models.module_managers_models import ModuleList
from apps.cms.models.menu_system_models import MenuItem


TRANSLATION_MODULE_CODE = "branch_stock_summary"
TRANSLATION_MODULE_NAME = "Branch Stock Summary Module"
TRANSLATION_MODULE_DESC = "Translations for Branch Stock Summary and Capacity Dashboard"

TRANSLATION_KEYS = {
    # ── Page Titles & Headings ────────────────────────────────
    "page_title": ("Branch Stock Summary", "Ringkasan Stok Cabang"),
    "dashboard_title": ("Branch Stock Summary Dashboard", "Dashboard Ringkasan Stok Cabang"),
    "dashboard_subtitle": (
        "Monitoring realtime warehouse pallet capacity and branch stock volume",
        "Pemantauan kapasitas palet gudang dan volume stok cabang secara langsung"
    ),
    "branch_stock_breakdown": ("Branch Stock & Capacity Breakdown", "Rincian Stok & Kapasitas Cabang"),

    # ── Action Buttons & Navigation ───────────────────────────
    "view_table_report": ("Table Report", "Laporan Tabel"),
    "open_full_report": ("Open Detailed Report", "Buka Laporan Rinci"),
    "dashboard": ("Dashboard", "Dashboard"),
    "filter": ("Filter", "Filter"),
    "apply": ("Apply", "Terapkan"),
    "reset": ("Reset", "Reset"),
    "export_excel": ("Export Excel", "Ekspor Excel"),
    "search": ("Search", "Cari"),

    # ── Filter Controls ───────────────────────────────────────
    "branch_select": ("Branch", "Cabang"),
    "all_branches": ("Select Branches", "Pilih Cabang"),
    "branches_selected": ("branches selected", "cabang dipilih"),
    "all_branches_selected": ("All Branches Selected", "Semua Cabang Dipilih"),
    "select_all": ("Select All", "Pilih Semua"),
    "start_date": ("Start Date", "Tanggal Mulai"),
    "end_date": ("End Date", "Tanggal Selesai"),

    # ── Metric / KPI Cards ────────────────────────────────────
    "total_pallet_stock": ("Total Stock", "Total Stok"),
    "total_capacity": ("Warehouse Capacity", "Kapasitas Gudang"),
    "capacity_utilization": ("Capacity Utilization", "Utilisasi Kapasitas"),
    "branch_health": ("Branch Status", "Status Cabang"),

    # ── Chart Titles ──────────────────────────────────────────
    "stock_trend_chart": ("Daily Pallet Stock vs Capacity Trend", "Tren Stok Palet Harian vs Kapasitas"),
    "status_breakdown": ("Capacity Status Breakdown", "Rincian Status Kapasitas"),
    "top_stock_branches": ("Top Branches by Pallet Stock Volume", "Cabang Teratas berdasarkan Volume Stok Palet"),
    "top_util_branches": ("Highest Capacity Utilization (%)", "Utilisasi Kapasitas Tertinggi (%)"),

    # ── Table Column Headers ──────────────────────────────────
    "col_code": ("Code", "Kode"),
    "col_description": ("Description", "Deskripsi"),
    "col_pallet": ("Pallet", "Palet"),
    "warehouse_capacity": ("Warehouse Capacity", "Kapasitas Gudang"),
    "latest_stock": ("Latest Stock", "Stok Terkini"),
    "avg_stock": ("Period Avg", "Rata-rata Periode"),
    "col_status": ("Status", "Status"),
    "col_action": ("Action", "Aksi"),
    "no_data": ("No branch stock data found.", "Tidak ada data stok cabang ditemukan."),

    # ── Status Labels ─────────────────────────────────────────
    "status_over_capacity": ("Over Capacity (≥100%)", "Kelebihan Kapasitas (≥100%)"),
    "status_high_load": ("High Load (70-99%)", "Beban Tinggi (70-99%)"),
    "status_optimal": ("Optimal (30-69%)", "Optimal (30-69%)"),
    "status_low_stock": ("Low Stock (<30%)", "Stok Rendah (<30%)"),
    "status_no_capacity": ("No Capacity Set", "Kapasitas Belum Diatur"),
}


class Command(BaseCommand):
    help = "Seed translations and CMS Menu items for Branch Stock Summary and Dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing translation and menu values",
        )

    def handle(self, *args, **options):
        force = options["force"]
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=== Seeding Branch Stock Summary Translations & Menus ==="
            )
        )

        # ── 1. Seed Translations ───────────────────────────────────────
        self.stdout.write(
            self.style.HTTP_INFO("\n[1/3] Seeding Translation Module & Keys...")
        )
        module, mod_created = TranslationModule.objects.get_or_create(
            code=TRANSLATION_MODULE_CODE,
            defaults={
                "name": TRANSLATION_MODULE_NAME,
                "description": TRANSLATION_MODULE_DESC,
                "status": 1,
            },
        )
        if mod_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [+] Translation Module created: {TRANSLATION_MODULE_CODE}"
                )
            )
        else:
            self.stdout.write(
                f"  [=] Translation Module exists: {TRANSLATION_MODULE_CODE}"
            )

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
                trans_key.name = key_code.replace("_", " ").title()
                trans_key.save(update_fields=["default_value", "name"])
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
        self.stdout.write(self.style.HTTP_INFO("\n[2/3] Seeding CMS Menu Items..."))

        # Find Application (BOM / Business Operations Management)
        app = (
            ApplicationList.objects.filter(id=5).first()
            or ApplicationList.objects.filter(code__icontains="BO").first()
            or ApplicationList.objects.filter(name__icontains="BOM").first()
            or ApplicationList.objects.first()
        )

        # Find ModuleList (Branch Stock Summary / Module 17)
        mod = (
            ModuleList.objects.filter(id=17).first()
            or ModuleList.objects.filter(name__icontains="Stock").first()
            or ModuleList.objects.filter(application=app).first()
        )

        # Menu 1: Branch Stock Summary Dashboard
        dash_code = "BO905-DASH"
        dash_url = "/bom/branchstocksummary/dashboard/"
        menu_dash, dash_created = MenuItem.objects.get_or_create(
            code=dash_code,
            defaults={
                "name": "Branch Stock Summary Dashboard",
                "shortname": "Stock Dashboard",
                "initial": "BSS Dash",
                "application": app,
                "module": mod,
                "icon": "nav-icon fas fa-chart-pie",
                "url": dash_url,
                "order": 0,
                "status": 1,
                "deleted": False,
            },
        )
        if dash_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [+] Menu Item created : {menu_dash.name} ({dash_url})"
                )
            )
        else:
            if force:
                menu_dash.name = "Branch Stock Summary Dashboard"
                menu_dash.shortname = "Stock Dashboard"
                menu_dash.initial = "BSS Dash"
                menu_dash.url = dash_url
                menu_dash.icon = "nav-icon fas fa-chart-pie"
                menu_dash.application = app
                menu_dash.module = mod
                menu_dash.order = 0
                menu_dash.status = 1
                menu_dash.deleted = False
                menu_dash.save()
                self.stdout.write(
                    self.style.SUCCESS(f"  [^] Menu Item updated : {menu_dash.name}")
                )
            else:
                self.stdout.write(
                    f"  [=] Menu Item exists  : {menu_dash.name} ({menu_dash.code})"
                )

        # Menu 2: Branch Stock Summary Report (Ensure existing menu is properly linked)
        report_code = "BO905"
        report_url = "/bom/branchstocksummary/user"
        menu_report, report_created = MenuItem.objects.get_or_create(
            code=report_code,
            defaults={
                "name": "Branch Stock Summary",
                "shortname": "Branch Stock Summary",
                "initial": "BS Summary",
                "application": app,
                "module": mod,
                "icon": "fas fa-chart-line menu-icon",
                "url": report_url,
                "order": 1,
                "status": 1,
                "deleted": False,
            },
        )
        if report_created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [+] Menu Item created : {menu_report.name} ({report_url})"
                )
            )
        else:
            self.stdout.write(
                f"  [=] Menu Item exists  : {menu_report.name} ({menu_report.code})"
            )

        # ── 3. Assign Permissions ──────────────────────────────────────
        self.stdout.write(
            self.style.HTTP_INFO("\n[3/3] Synchronizing Menu Permissions...")
        )
        assigned_perms = 0
        if menu_report and menu_dash:
            permissions = CMSPermission.objects.filter(menu=menu_report)
            for perm in permissions:
                if not perm.menu.filter(id=menu_dash.id).exists():
                    perm.menu.add(menu_dash)
                    assigned_perms += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Permission mapped to {assigned_perms} CMSPermission role profile(s)."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\nAll Branch Stock Summary translations and CMS menu items seeded successfully!"
            )
        )
