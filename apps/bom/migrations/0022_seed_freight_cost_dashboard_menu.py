from django.db import migrations


TRANSLATION_MODULE_CODE = "freight_cost"
TRANSLATION_MODULE_NAME = "Freight Cost"
TRANSLATION_MODULE_DESC = "Translations for Freight Cost report and analytics dashboard"

TRANSLATION_KEYS = {
    "page_title": ("Freight Cost Report", "Laporan Ongkos Angkut"),
    "dashboard_title": ("Freight Cost Dashboard", "Dashboard Ongkos Angkut"),
    "dashboard_subtitle": (
        "Interactive analytics, cost distribution, and logistics operational metrics",
        "Analitik interaktif, sebaran biaya, dan metrik operasional logistik",
    ),
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
    "total_freight_cost": ("Total Freight Cost", "Total Biaya Ongkos Angkut"),
    "total_weight_shipped": ("Total Weight", "Total Berat"),
    "total_shipments": ("Total Shipments", "Total Pengiriman"),
    "avg_cost_per_kg": ("Avg Cost / Kg", "Rata-rata Biaya / Kg"),
    "burden_distribution": ("Burden Distribution", "Distribusi Beban"),
    "oi_burden_cost": ("OI Burden Cost", "Biaya Beban OI"),
    "mup_burden_cost": ("MUP Burden Cost", "Biaya Beban MUP"),
    "cost_efficiency": ("Logistics Cost Efficiency", "Efisiensi Biaya Logistik"),
    "of_total_cost": ("of total cost", "dari total biaya"),
    "monthly_cost_weight_trend": ("Monthly Cost & Weight Trend", "Tren Biaya & Berat Bulanan"),
    "burden_type_share": ("Burden Type Share (OI vs MUP)", "Porsi Tipe Beban (OI vs MUP)"),
    "top_expeditions_chart": ("Top 10 Expeditions by Total Cost", "10 Ekspedisi Teratas berdasarkan Biaya"),
    "top_branches_chart": ("Top 10 Destination Branches by Total Cost", "10 Cabang Tujuan Teratas berdasarkan Biaya"),
    "product_group_cost_chart": ("Cost by Product Group", "Biaya berdasarkan Grup Produk"),
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
            defaults={"name": key.replace("_", " ").title(), "default_value": en_val, "status": 1},
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
        or ApplicationList.objects.filter(name__icontains="Operation").first()
        or ApplicationList.objects.filter(code__icontains="BO").first()
        or ApplicationList.objects.first()
    )

    mod = (
        ModuleList.objects.filter(id=21).first()
        or ModuleList.objects.filter(name__icontains="Freight").first()
        or ModuleList.objects.filter(application=app).first()
    )

    # Menu: Freight Cost Dashboard
    menu_dash, _ = MenuItem.objects.get_or_create(
        code="BO904-DASH",
        defaults={
            "name": "Freight Cost Dashboard",
            "shortname": "Freight Dashboard",
            "initial": "FC Dash",
            "application": app,
            "module": mod,
            "icon": "nav-icon fas fa-chart-pie",
            "url": "/bom/freight-cost/freightcost/dashboard/",
            "order": 0,
            "status": 1,
            "deleted": False,
        },
    )

    # Assign to CMSPermission that has access to BO904
    existing_menu = MenuItem.objects.filter(code="BO904").first()
    if existing_menu and menu_dash:
        permissions = CMSPermission.objects.filter(menu=existing_menu)
        for perm in permissions:
            if not perm.menu.filter(id=menu_dash.id).exists():
                perm.menu.add(menu_dash)


def remove_menu_and_translations(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="BO904-DASH").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0021_seed_branch_stock_summary_dashboard_menu"),
        ("cms", "0001_initial"),
        ("base", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_menu_and_translations, remove_menu_and_translations),
    ]
