from django.db import migrations

# Translations for the Doctor List / Doctor Analytics pages (html_dashboard/hcp_list.html,
# html_dashboard/analytics_dashboard.html and their partials). Each value is
# (default_value, english_override_or_None, indonesian_value) - most keys only need an
# Indonesian row since English already falls back to default_value.
HCP_LIST_KEYS = {
    "btn_dashboard": ("Dashboard", None, "Dasbor"),
    "btn_export": ("Export", None, "Ekspor"),
    "btn_filter": ("Filter", None, "Filter"),
    "col_education": ("EDUCATION", None, "PENDIDIKAN"),
    "col_license": ("LICENSE", None, "LISENSI"),
    "col_name": ("NAME", None, "NAMA"),
    "col_no": ("NO", None, "NO"),
    "col_place_of_practice": ("PLACE OF PRACTICE", None, "TEMPAT PRAKTIK"),
    "col_province": ("PROVINCE", "PROVINCE", "PROVINSI"),
    "col_specialities": ("SPECIALITIES", "SPECIALITIES", "SPESIALISASI"),
    "col_start_date": ("START DATE", "START DATE", "TANGGAL MULAI"),
    "col_status": ("STATUS", None, "STATUS"),
    "empty_state": ("No healthcare professionals found.", None, "Tidak ada tenaga kesehatan yang ditemukan."),
    "label_entries": ("entries", "entries", "entri"),
    "label_in_total": ("in total", None, "total"),
    "label_of": ("of", None, "dari"),
    "label_results": ("results", None, "hasil"),
    "label_show": ("Show", None, "Menampilkan"),
    "label_to": ("to", None, "sampai"),
    "page_title": ("Healthcare Professionals", None, "Tenaga Kesehatan"),
    "search_placeholder": ("Search", None, "Cari"),
    "status_active": ("Active", None, "Aktif"),
    "status_inactive": ("Inactive", None, "Tidak Aktif"),
}

HCP_ANALYTICS_KEYS = {
    "btn_back": ("Back", None, "Kembali"),
    "btn_export": ("Export", None, "Ekspor"),
    "btn_filter": ("Filter", None, "Filter"),
    "chart_education_empty": ("No education data available yet.", None, "Data pendidikan belum tersedia."),
    "chart_education_title": ("Healthcare Education", None, "Pendidikan Tenaga Kesehatan"),
    "chart_places_empty": ("No place-of-practice data available yet.", None, "Data tempat praktik belum tersedia."),
    "chart_places_title": ("Top Hospitals / Places of Practice", None, "Rumah Sakit / Tempat Praktik Teratas"),
    "chart_province_empty": ("No province data available yet.", None, "Data provinsi belum tersedia."),
    "chart_province_subtitle": (
        "Click or hover a province to see how many doctors practice there.",
        None,
        "Klik atau arahkan kursor ke provinsi untuk melihat jumlah dokter yang berpraktik di sana.",
    ),
    "chart_province_title": (
        "Top Provinces by Healthcare Count", None, "Provinsi Teratas berdasarkan Jumlah Tenaga Kesehatan"
    ),
    "chart_specialities_empty": ("No speciality data available yet.", None, "Data spesialisasi belum tersedia."),
    "chart_specialities_title": ("Healthcare Specialities", None, "Spesialisasi Kesehatan"),
    "col_education": ("EDUCATION", None, "PENDIDIKAN"),
    "col_license": ("LICENSE", None, "LISENSI"),
    "col_name": ("NAME", None, "NAMA"),
    "col_no": ("NO", None, "NO"),
    "col_place_of_practice": ("PLACE OF PRACTICE", None, "TEMPAT PRAKTIK"),
    "col_province": ("PROVINCE", "PROVINCE", "PROVINSI"),
    "col_specialities": ("SPECIALITIES", "SPECIALITIES", "SPESIALISASI"),
    "col_start_date": ("START DATE", "START DATE", "TANGGAL MULAI"),
    "col_status": ("STATUS", None, "STATUS"),
    "empty_state": ("No healthcare professionals found.", None, "Tidak ada tenaga kesehatan yang ditemukan."),
    "filter_label_education": ("Education", None, "Pendidikan"),
    "filter_label_places": ("Hospital / Place", None, "Rumah Sakit / Tempat"),
    "filter_label_province": ("Province", None, "Provinsi"),
    "filter_label_specialities": ("Speciality", None, "Spesialisasi"),
    "label_entries": ("entries", "entries", "entri"),
    "label_in_total": ("in total", None, "total"),
    "label_of": ("of", None, "dari"),
    "label_results": ("results", None, "hasil"),
    "label_show": ("Show", None, "Menampilkan"),
    "label_to": ("to", None, "sampai"),
    "page_title": ("Healthcare Professionals Analytics", None, "Analitik Tenaga Kesehatan"),
    "search_placeholder": (
        "Search healthcare professionals in this table",
        None,
        "Cari tenaga kesehatan profesional di tabel ini",
    ),
    "stat_across": ("Across", None, "Di"),
    "stat_active": ("Active Licenses", None, "Lisensi Aktif"),
    "stat_facilities": ("Practice Facilities", None, "Fasilitas Praktik"),
    "stat_inactive": ("Inactive", None, "Tidak Aktif"),
    "stat_regions": ("Regions", None, "Wilayah"),
    "stat_total": ("Total Health Care", None, "Total Tenaga Kesehatan"),
    "status_active": ("Active", None, "Aktif"),
    "status_inactive": ("Inactive", None, "Tidak Aktif"),
}

MODULES = {
    "hcp_list": ("Healthcare Professionals - List", HCP_LIST_KEYS),
    "hcp_analytics": ("Healthcare Professionals - Analytics", HCP_ANALYTICS_KEYS),
}

# cms_menuitem rows for these two pages already existed with shortname "HCP List" /
# "HCP Analytics" - rename them to match the Doctor List / Doctor Analytics naming used
# everywhere else in the feature.
MENU_LABELS = {
    "CR201": "Doctor List",
    "CR202": "Doctor Analytics",
}


def seed_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationKey = apps.get_model("base", "TranslationKey")
    Translation = apps.get_model("base", "Translation")

    for module_code, (module_name, keys) in MODULES.items():
        module, _ = TranslationModule.objects.get_or_create(
            code=module_code, defaults={"name": module_name}
        )
        for key, (default_value, en_value, id_value) in keys.items():
            translation_key, _ = TranslationKey.objects.get_or_create(
                module=module, key=key,
                defaults={"name": key, "default_value": default_value},
            )
            if en_value is not None:
                Translation.objects.get_or_create(
                    translation_key=translation_key, language="en",
                    defaults={"value": en_value, "name": f"{key}_en"},
                )
            Translation.objects.get_or_create(
                translation_key=translation_key, language="id",
                defaults={"value": id_value, "name": f"{key}_id"},
            )


def rename_menu_items(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    for code, shortname in MENU_LABELS.items():
        MenuItem.objects.filter(code=code).update(shortname=shortname)


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0031_doctor_active_status_index"),
        ("base", "0104_merge_20260806_0911"),
        ("cms", "0023_alter_menuitem_iframe_url"),
    ]

    operations = [
        migrations.RunPython(seed_translations, migrations.RunPython.noop),
        migrations.RunPython(rename_menu_items, migrations.RunPython.noop),
    ]
