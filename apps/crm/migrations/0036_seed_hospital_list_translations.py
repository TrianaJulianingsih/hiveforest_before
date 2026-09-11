from django.db import migrations

# Translations for the Hospital List page (html_dashboard/hospital_list.html and its
# table partial html_dashboard/hospital_table.html). Mirrors the pattern used for
# hcp_list/hcp_analytics in 0032_seed_hcp_translations_and_menu_labels.py - most keys
# only need an Indonesian row since English already falls back to default_value.
HOSPITAL_LIST_KEYS = {
    "page_title": ("Hospitals", None, "Rumah Sakit"),
    "search_placeholder": ("Search Hospital", None, "Cari Rumah Sakit"),
    "btn_filter": ("Filter", None, "Filter"),
    "btn_export": ("Export", None, "Ekspor"),
    "col_no": ("NO", None, "NO"),
    "col_name": ("NAME", None, "NAMA"),
    "col_type": ("TYPE", None, "JENIS"),
    "col_class": ("CLASS", None, "KELAS"),
    "col_province": ("PROVINCE", "PROVINCE", "PROVINSI"),
    "col_regency": ("REGENCY", None, "KABUPATEN/KOTA"),
    "empty_state": ("No hospitals found.", None, "Tidak ada rumah sakit yang ditemukan."),
    "label_show": ("Show", None, "Menampilkan"),
    "label_entries": ("entries", "entries", "entri"),
    "label_all": ("All", None, "Semua"),
    "label_in_total": ("in total", None, "total"),
    "label_to": ("to", None, "sampai"),
    "label_of": ("of", None, "dari"),
    "label_results": ("results", None, "hasil"),
}

MODULES = {
    "hospital_list": ("Hospital - List", HOSPITAL_LIST_KEYS),
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


def remove_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationModule.objects.filter(code__in=MODULES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0035_remove_doctor_dashboard_menu_item"),
        ("base", "0104_merge_20260806_0911"),
    ]

    operations = [
        migrations.RunPython(seed_translations, remove_translations),
    ]
