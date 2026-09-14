from django.db import migrations


TRANSLATION_MODULE_CODE = "sub_distributor"
TRANSLATION_MODULE_NAME = "Sub-Distributor Module"
TRANSLATION_MODULE_DESC = "Translations for Sub-Distributor maintenance and analytics dashboard"

TRANSLATION_KEYS = {
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
    "btn_add": ("Add Sub-Distributor", "Tambah Sub-Distributor"),
    "btn_filter": ("Filter", "Filter"),
    "btn_reset": ("Reset", "Reset"),
    "btn_list": ("Sub-Distributor List", "Daftar Sub-Distributor"),
    "btn_back": ("Back to List", "Kembali ke Daftar"),
    "btn_save": ("Save", "Simpan"),
    "btn_cancel": ("Cancel", "Batal"),
    "btn_yes_remove": ("Yes, Remove!", "Ya, Hapus!"),
    "btn_search": ("Search", "Cari"),
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
    "search_name": ("Filter Name", "Cari Nama"),
    "search_code": ("Filter Code", "Cari Kode"),
    "search_shortname": ("Filter Short Name", "Cari Nama Singkat"),
    "search_customer_placeholder": ("Search customer by name or code...", "Cari pelanggan berdasarkan nama atau kode..."),
    "all_status": ("All Status", "Semua Status"),
    "status_active": ("Active", "Aktif"),
    "status_inactive": ("Inactive", "Nonaktif"),
    "no_data": ("No sub-distributor data found.", "Tidak ada data sub-distributor."),
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


def seed_translations_and_menu(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationKey = apps.get_model("base", "TranslationKey")
    Translation = apps.get_model("base", "Translation")
    ApplicationList = apps.get_model("cms", "ApplicationList")
    ModuleList = apps.get_model("cms", "ModuleList")
    MenuItem = apps.get_model("cms", "MenuItem")

    # 1. Translation Module & Keys
    module, _ = TranslationModule.objects.get_or_create(
        code=TRANSLATION_MODULE_CODE,
        defaults={
            "name": TRANSLATION_MODULE_NAME,
            "description": TRANSLATION_MODULE_DESC,
            "status": 1,
        },
    )

    for key_code, (en_val, id_val) in TRANSLATION_KEYS.items():
        trans_key, _ = TranslationKey.objects.get_or_create(
            module=module,
            key=key_code,
            defaults={
                "name": key_code.replace("_", " ").title(),
                "default_value": en_val,
                "status": 1,
            },
        )
        Translation.objects.get_or_create(
            translation_key=trans_key,
            language="en",
            defaults={"value": en_val, "status": 1},
        )
        Translation.objects.get_or_create(
            translation_key=trans_key,
            language="id",
            defaults={"value": id_val, "status": 1},
        )

    # 2. CMS Menu Items
    app = (
        ApplicationList.objects.filter(name__icontains="BOM").first()
        or ApplicationList.objects.filter(code__icontains="BOM").first()
        or ApplicationList.objects.filter(name__icontains="Operation").first()
        or ApplicationList.objects.first()
    )

    mod = None
    if app:
        mod = (
            ModuleList.objects.filter(application=app, name__icontains="Customer").first()
            or ModuleList.objects.filter(application=app, name__icontains="Distributor").first()
            or ModuleList.objects.filter(application=app).first()
        )

    # Menu 1: Sub-Distributor Dashboard
    MenuItem.objects.get_or_create(
        code="BOM-SD-DASH",
        defaults={
            "name": "Sub-Distributor Dashboard",
            "shortname": "Sub-Dist Dashboard",
            "initial": "SDD",
            "application": app,
            "module": mod,
            "icon": "nav-icon fas fa-chart-pie",
            "url": "/bom/customer-maintenance/sub-distributor/dashboard/",
            "order": 1,
            "status": 1,
            "deleted": False,
        },
    )

    # Menu 2: Sub-Distributor Maintenance List
    MenuItem.objects.get_or_create(
        code="BOM-SD-LIST",
        defaults={
            "name": "Sub-Distributor Maintenance",
            "shortname": "Sub-Distributor",
            "initial": "SDM",
            "application": app,
            "module": mod,
            "icon": "nav-icon fas fa-truck-loading",
            "url": "/bom/customer-maintenance/sub-distributor/",
            "order": 2,
            "status": 1,
            "deleted": False,
        },
    )


def remove_translations_and_menu(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    MenuItem = apps.get_model("cms", "MenuItem")

    TranslationModule.objects.filter(code=TRANSLATION_MODULE_CODE).delete()
    MenuItem.objects.filter(code__in=["BOM-SD-DASH", "BOM-SD-LIST"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0019_add_freightcostimportjob"),
    ]

    operations = [
        migrations.RunPython(seed_translations_and_menu, remove_translations_and_menu),
    ]
