"""
seed_freight_cost_menu_and_translations.py
Management command to seed:
1. TranslationModule, TranslationKey, and Translation for Freight Cost ('freight_cost')
2. CMS MenuItem for Freight Cost Dashboard (/bom/freight-cost/freightcost/dashboard/)
3. Permission assignment from existing Freight Cost menu (BO904) to Freight Cost Dashboard (BO904-DASH)

Usage:
    python manage.py seed_freight_cost_menu_and_translations
    python manage.py seed_freight_cost_menu_and_translations --force
"""

from django.core.management.base import BaseCommand
from apps.base.models.translation import TranslationModule, TranslationKey, Translation
from apps.base.models.permissions import CMSPermission
from apps.cms.models.app_managers_models import ApplicationList
from apps.cms.models.module_managers_models import ModuleList
from apps.cms.models.menu_system_models import MenuItem


TRANSLATION_MODULE_CODE = "freight_cost"
TRANSLATION_MODULE_NAME = "Freight Cost"
TRANSLATION_MODULE_DESC = "Translations for Freight Cost report and analytics dashboard"

TRANSLATION_KEYS = {
    # ── Page Titles & Headings ────────────────────────────────
    "page_title": ("Freight Cost Report", "Laporan Ongkos Angkut"),
    "dashboard_title": ("Freight Cost Dashboard", "Dashboard Ongkos Angkut"),
    "dashboard_subtitle": (
        "Interactive analytics, cost distribution, and logistics operational metrics",
        "Analitik interaktif, sebaran biaya, dan metrik operasional logistik",
    ),

    # ── Action Buttons & Navigation ───────────────────────────
    "dashboard": ("Dashboard", "Dashboard"),
    "view_table_report": ("Table Report", "Laporan Tabel"),
    "open_full_report": ("Open Detailed Report", "Buka Laporan Rinci"),
    "btn_export": ("Export", "Ekspor"),
    "btn_export_excel": ("Export Excel", "Ekspor Excel"),
    "btn_export_csv": ("Export CSV", "Ekspor CSV"),
    "filter": ("Filter", "Filter"),
    "apply": ("Apply", "Terapkan"),
    "reset": ("Reset", "Reset"),
    "search": ("Search", "Cari"),

    # ── Filter Controls ───────────────────────────────────────
    "year": ("Year", "Tahun"),
    "month": ("Month", "Bulan"),
    "burden_type": ("Burden Type", "Tipe Beban"),
    "expedition": ("Expedition", "Ekspedisi"),
    "branch": ("Branch", "Cabang"),
    "group_produk": ("Product Group", "Grup Produk"),
    "option_all_year": ("All Year", "Semua Tahun"),
    "option_all_months": ("All Months", "Semua Bulan"),
    "option_all_burden": ("All Burden Types", "Semua Tipe Beban"),
    "option_all_expeditions": ("All Expeditions", "Semua Ekspedisi"),
    "option_all_branches": ("All Branches", "Semua Cabang"),
    "option_all_groups": ("All Product Groups", "Semua Grup Produk"),

    # ── Metric / KPI Cards ────────────────────────────────────
    "total_freight_cost": ("Total Freight Cost", "Total Biaya Ongkos Angkut"),
    "total_weight_shipped": ("Total Weight", "Total Berat"),
    "total_shipments": ("Total Shipments", "Total Pengiriman"),
    "avg_cost_per_kg": ("Avg Cost / Kg", "Rata-rata Biaya / Kg"),
    "burden_distribution": ("Burden Distribution", "Distribusi Beban"),
    "oi_burden_cost": ("OI Burden Cost", "Biaya Beban OI"),
    "mup_burden_cost": ("MUP Burden Cost", "Biaya Beban MUP"),
    "cost_efficiency": ("Logistics Cost Efficiency", "Efisiensi Biaya Logistik"),
    "of_total_cost": ("of total cost", "dari total biaya"),

    # ── Chart Titles ──────────────────────────────────────────
    "monthly_cost_weight_trend": ("Monthly Cost & Weight Trend", "Tren Biaya & Berat Bulanan"),
    "burden_type_share": ("Burden Type Share (OI vs MUP)", "Porsi Tipe Beban (OI vs MUP)"),
    "top_expeditions_chart": ("Top 10 Expeditions by Total Cost", "10 Ekspedisi Teratas berdasarkan Biaya"),
    "top_branches_chart": ("Top 10 Destination Branches by Total Cost", "10 Cabang Tujuan Teratas berdasarkan Biaya"),
    "product_group_cost_chart": ("Cost by Product Group", "Biaya berdasarkan Grup Produk"),

    # ── Table Column Headers & Tables ─────────────────────────
    "top_logistics_routes": ("Top Logistics Routes", "Rute Logistik Teratas"),
    "col_route": ("Route (Origin → Destination)", "Rute (Asal → Tujuan)"),
    "col_branch": ("Branch", "Cabang"),
    "col_expedition": ("Expedition", "Ekspedisi"),
    "col_shipments": ("Shipments", "Jumlah Pengiriman"),
    "col_weight": ("Weight (Kg)", "Berat (Kg)"),
    "col_total_cost": ("Total Cost (Rp)", "Total Biaya (Rp)"),
    "col_avg_cost_kg": ("Avg Cost/Kg (Rp)", "Rata-rata Biaya/Kg (Rp)"),
    "col_freight_number": ("Freight Number", "Nomor Ongkos"),
    "col_shipping_date": ("Shipping Date", "Tanggal Kirim"),
    "col_from_location": ("From Location", "Lokasi Asal"),
    "col_to_location": ("To Location", "Lokasi Tujuan"),
    "col_expedition_name": ("Expedition Name", "Nama Ekspedisi"),
    "col_expedition_type": ("Expedition Type", "Tipe Ekspedisi"),
    "col_packaging_type": ("Packaging Type", "Tipe Kemasan"),
    "col_item_code": ("Item Code", "Kode Barang"),
    "col_item_description": ("Item Description", "Deskripsi Barang"),
    "col_qty_freight": ("Qty Freight", "Qty Muatan"),
    "col_total_weight": ("Total Weight", "Total Berat"),
    "col_nama_principal": ("Principal", "Principal"),
    "col_group_produk": ("Product Group", "Grup Produk"),
    "col_total_freight": ("Total Freight", "Total Ongkos"),
    "col_freight_type": ("Freight Type", "Tipe Muatan"),
    "col_kode_cab": ("Branch Code", "Kode Cabang"),
    "col_nama_cab": ("Branch Name", "Nama Cabang"),
    "col_item_group": ("Item Group", "Item Group"),
    "no_data": ("No freight cost data found.", "Tidak ada data ongkos angkut ditemukan."),
    "length_menu": ("Show _MENU_ entries", "Tampilkan _MENU_ data"),
    "paginate_first": ("First", "Pertama"),
    "paginate_last": ("Last", "Terakhir"),
    "paginate_next": ("Next", "Berikutnya"),
    "paginate_previous": ("Previous", "Sebelumnya"),
}


class Command(BaseCommand):
    help = "Seed translations and CMS Menu items for Freight Cost Dashboard"

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
                "=== Seeding Freight Cost Translations & Menus ==="
            )
        )

        # ── 1. Translation Module, Keys & Values ───────────────────────
        self.stdout.write(self.style.HTTP_INFO("\n[1/3] Seeding Translations..."))

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
                self.style.SUCCESS(f"  [+] Created TranslationModule: {module.code}")
            )
        else:
            self.stdout.write(
                f"  [=] Using existing TranslationModule: {module.code}"
            )

        keys_created = 0
        translations_updated = 0

        for key_code, (en_val, id_val) in TRANSLATION_KEYS.items():
            trans_key, key_created = TranslationKey.objects.get_or_create(
                module=module,
                key=key_code,
                defaults={
                    "name": key_code.replace("_", " ").title(),
                    "default_value": en_val,
                    "status": 1,
                },
            )
            if key_created:
                keys_created += 1

            for lang_code, text_val in [("en", en_val), ("id", id_val)]:
                trans, created = Translation.objects.get_or_create(
                    translation_key=trans_key,
                    language=lang_code,
                    defaults={"value": text_val, "status": 1},
                )
                if not created and force:
                    trans.value = text_val
                    trans.save()
                    translations_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Translations done: {keys_created} new keys created, {len(TRANSLATION_KEYS)} keys verified."
            )
        )

        # ── 2. CMS Menu Items ──────────────────────────────────────────
        self.stdout.write(self.style.HTTP_INFO("\n[2/3] Seeding CMS Menu Items..."))

        # Find ApplicationList (Business Operation Management / ID 5)
        app = (
            ApplicationList.objects.filter(id=5).first()
            or ApplicationList.objects.filter(name__icontains="Operation").first()
            or ApplicationList.objects.filter(code__icontains="BO").first()
            or ApplicationList.objects.first()
        )

        # Find ModuleList (Freight Cost / ID 21)
        mod = (
            ModuleList.objects.filter(id=21).first()
            or ModuleList.objects.filter(name__icontains="Freight").first()
            or ModuleList.objects.filter(application=app).first()
        )

        # Menu 1: Freight Cost Dashboard
        dash_code = "BO904-DASH"
        dash_url = "/bom/freight-cost/freightcost/dashboard/"
        menu_dash, dash_created = MenuItem.objects.get_or_create(
            code=dash_code,
            defaults={
                "name": "Freight Cost Dashboard",
                "shortname": "Freight Dashboard",
                "initial": "FC Dash",
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
                menu_dash.name = "Freight Cost Dashboard"
                menu_dash.shortname = "Freight Dashboard"
                menu_dash.initial = "FC Dash"
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

        # Menu 2: Freight Cost List Report (Ensure existing menu is properly linked)
        report_code = "BO904"
        report_url = "/bom/freight-cost/freightcost/"
        menu_report = MenuItem.objects.filter(code=report_code).first()
        if menu_report:
            if force:
                menu_report.url = report_url
                menu_report.order = 1
                menu_report.save()
            self.stdout.write(
                f"  [=] Existing Report Menu : {menu_report.name} ({menu_report.code})"
            )
        else:
            menu_report = MenuItem.objects.create(
                code=report_code,
                name="Freight Cost",
                shortname="Freight Cost",
                initial="Freight Cost",
                application=app,
                module=mod,
                icon="fas fa-truck menu-icon",
                url=report_url,
                order=1,
                status=1,
                deleted=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [+] Report Menu Item created : {menu_report.name} ({report_url})"
                )
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
                "\nAll Freight Cost translations and CMS menu items seeded successfully!"
            )
        )
