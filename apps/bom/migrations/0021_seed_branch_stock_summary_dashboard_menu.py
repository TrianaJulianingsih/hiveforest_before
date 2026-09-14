from django.db import migrations


TRANSLATION_MODULE_CODE = "branch_stock_summary"
TRANSLATION_MODULE_NAME = "Branch Stock Summary Module"
TRANSLATION_MODULE_DESC = "Translations for Branch Stock Summary and Capacity Dashboard"

TRANSLATION_KEYS = {
    "dashboard_title": ("Branch Stock Summary Dashboard", "Dashboard Ringkasan Stok Cabang"),
    "dashboard_subtitle": (
        "Monitoring realtime warehouse pallet capacity and branch stock volume",
        "Pemantauan kapasitas palet gudang dan volume stok cabang secara langsung"
    ),
    "view_table_report": ("Table Report", "Laporan Tabel"),
    "dashboard": ("Dashboard", "Dashboard"),
    "filter": ("Filter", "Filter"),
    "branch_select": ("Branch", "Cabang"),
    "start_date": ("Start Date", "Tanggal Mulai"),
    "end_date": ("End Date", "Tanggal Selesai"),
    "apply": ("Apply", "Terapkan"),
    "export_excel": ("Export Excel", "Ekspor Excel"),
    "total_pallet_stock": ("Total Stock", "Total Stok"),
    "total_capacity": ("Warehouse Capacity", "Kapasitas Gudang"),
    "capacity_utilization": ("Capacity Utilization", "Utilisasi Kapasitas"),
    "branch_health": ("Branch Status", "Status Cabang"),
    "stock_trend_chart": ("Daily Pallet Stock vs Capacity Trend", "Tren Stok Palet Harian vs Kapasitas"),
    "status_breakdown": ("Capacity Status Breakdown", "Rincian Status Kapasitas"),
    "top_stock_branches": ("Top Branches by Pallet Stock Volume", "Cabang Teratas berdasarkan Volume Stok Palet"),
    "top_util_branches": ("Highest Capacity Utilization (%)", "Utilisasi Kapasitas Tertinggi (%)"),
    "branch_stock_breakdown": ("Branch Stock & Capacity Breakdown", "Rincian Stok & Kapasitas Cabang"),
    "open_full_report": ("Open Detailed Report", "Buka Laporan Rinci"),
    "col_code": ("Code", "Kode"),
    "col_description": ("Description", "Deskripsi"),
    "col_pallet": ("Pallet", "Palet"),
    "col_status": ("Status", "Status"),
    "col_action": ("Action", "Aksi"),
    "latest_stock": ("Latest Stock", "Stok Terkini"),
    "avg_stock": ("Period Avg", "Rata-rata Periode"),
    "no_data": ("No branch stock data found.", "Tidak ada data stok cabang ditemukan."),
}


def seed_menu_and_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationKey = apps.get_model("base", "TranslationKey")
    Translation = apps.get_model("base", "Translation")
    MenuItem = apps.get_model("cms", "MenuItem")
    ApplicationList = apps.get_model("cms", "ApplicationList")
    ModuleList = apps.get_model("cms", "ModuleList")
    CMSPermission = apps.get_model("base", "CMSPermission")

    # 1. Seed Translations
    module, _ = TranslationModule.objects.get_or_create(
        code=TRANSLATION_MODULE_CODE,
        defaults={
            "name": TRANSLATION_MODULE_NAME,
            "description": TRANSLATION_MODULE_DESC,
            "status": 1,
        },
    )

    for key, (en_val, id_val) in TRANSLATION_KEYS.items():
        t_key, _ = TranslationKey.objects.get_or_create(
            module=module,
            key=key,
            defaults={"default_value": en_val, "status": 1},
        )
        Translation.objects.update_or_create(
            translation_key=t_key,
            language="en",
            defaults={"value": en_val, "status": 1},
        )
        Translation.objects.update_or_create(
            translation_key=t_key,
            language="id",
            defaults={"value": id_val, "status": 1},
        )

    # 2. CMS Menu Item for Dashboard
    app = (
        ApplicationList.objects.filter(id=5).first()
        or ApplicationList.objects.filter(code__icontains="BO").first()
        or ApplicationList.objects.first()
    )

    mod = (
        ModuleList.objects.filter(id=17).first()
        or ModuleList.objects.filter(name__icontains="Stock").first()
        or ModuleList.objects.filter(application=app).first()
    )

    # Menu: Branch Stock Summary Dashboard
    menu_dash, _ = MenuItem.objects.get_or_create(
        code="BO905-DASH",
        defaults={
            "name": "Branch Stock Summary Dashboard",
            "shortname": "Stock Dashboard",
            "initial": "BSS Dash",
            "application": app,
            "module": mod,
            "icon": "nav-icon fas fa-chart-pie",
            "url": "/bom/branchstocksummary/dashboard/",
            "order": 0,
            "status": 1,
            "deleted": False,
        },
    )

    # Assign to CMSPermission that has access to BO905 (id=25)
    existing_menu = MenuItem.objects.filter(code="BO905").first()
    if existing_menu and menu_dash:
        permissions = CMSPermission.objects.filter(menu=existing_menu)
        for perm in permissions:
            perm.menu.add(menu_dash)


def remove_menu_and_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    MenuItem = apps.get_model("cms", "MenuItem")

    TranslationModule.objects.filter(code=TRANSLATION_MODULE_CODE).delete()
    MenuItem.objects.filter(code="BO905-DASH").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0020_seed_sub_distributor_translations_and_menu"),
        ("cms", "0001_initial"),
        ("base", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_menu_and_translations, remove_menu_and_translations),
    ]
