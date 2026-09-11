from django.db import migrations

# Translations for the Doctor Profile and Hospital Profile pages
# (html_dashboard/hcp_profile.html, html_dashboard/hospital_profile.html and the
# client_table_entries.html partial the latter reuses). Mirrors the pattern used for
# hcp_list/hcp_analytics in 0032_seed_hcp_translations_and_menu_labels.py - most keys
# only need an Indonesian row since English already falls back to default_value.
HCP_PROFILE_KEYS = {
    "page_title": ("Healthcare Professionals", None, "Tenaga Kesehatan"),
    "btn_back": ("Back", None, "Kembali"),
    "search_placeholder": ("Search", None, "Cari"),
    "profile_link_label": ("Profile link", None, "Tautan profil"),
    "about_prefix": ("About", None, "Tentang"),
    "label_experience": ("Experience", None, "Pengalaman"),
    "label_license_str": ("License (STR)", None, "Lisensi (STR)"),
    "section_place_of_practice": ("Place of Practice", None, "Tempat Praktik"),
    "col_no": ("NO", None, "NO"),
    "col_place_of_practice": ("PLACE OF PRACTICE", None, "TEMPAT PRAKTIK"),
    "col_city": ("CITY", None, "KOTA"),
    "col_province": ("PROVINCE", "PROVINCE", "PROVINSI"),
    "empty_place_of_practice": ("No place of practice on file.", None, "Tidak ada tempat praktik yang tercatat."),
    "section_education": ("Education", None, "Pendidikan"),
    "col_education": ("EDUCATION", None, "PENDIDIKAN"),
    "col_completed_date": ("COMPLETED DATE", None, "TANGGAL SELESAI"),
    "empty_education": ("No education on file.", None, "Tidak ada riwayat pendidikan yang tercatat."),
    "section_speciality": ("Speciality", None, "Spesialisasi"),
    "col_speciality": ("SPECIALITY", None, "SPESIALISASI"),
    "empty_speciality": ("No speciality on file.", None, "Tidak ada spesialisasi yang tercatat."),
}

HOSPITAL_PROFILE_KEYS = {
    "page_title": ("Hospitals", None, "Rumah Sakit"),
    "btn_back": ("Back", None, "Kembali"),
    "search_placeholder": ("Search Hospital", None, "Cari Rumah Sakit"),
    "label_director": ("Director", None, "Direktur"),
    "label_phone": ("Phone", None, "Telepon"),
    "about_prefix": ("About", None, "Tentang"),
    "label_is_customer": ("Is Customer?", None, "Apakah Pelanggan?"),
    "label_yes": ("Yes", None, "Ya"),
    "label_no": ("No", None, "Tidak"),
    "label_ownership": ("Ownership", None, "Kepemilikan"),
    "label_blu_status": ("BLU Status", None, "Status BLU"),
    "label_province": ("Province", None, "Provinsi"),
    "label_regency": ("Regency", None, "Kabupaten/Kota"),
    "label_district": ("District", None, "Kecamatan"),
    "label_village": ("Village", None, "Kelurahan/Desa"),
    "label_building": ("Building", None, "Gedung"),
    "label_complex": ("Complex", None, "Kompleks"),
    "section_hospital_location": ("Hospital Location", None, "Lokasi Rumah Sakit"),
    "section_doctors": ("Doctors", None, "Dokter"),
    "section_bed_count": ("Bed Count", None, "Jumlah Tempat Tidur"),
    "section_services": ("Services", None, "Layanan"),
    "section_professional_group": ("Professional Group", None, "Kelompok Profesi"),
    "col_no": ("NO", None, "NO"),
    "col_name": ("NAME", None, "NAMA"),
    "col_license": ("LICENSE", None, "LISENSI"),
    "col_specialties": ("SPECIALTIES", None, "SPESIALISASI"),
    "col_start_date": ("START DATE", "START DATE", "TANGGAL MULAI"),
    "col_class": ("CLASS", None, "KELAS"),
    "col_count": ("COUNT", None, "JUMLAH"),
    "col_service": ("SERVICE", None, "LAYANAN"),
    "col_professional": ("PROFESSIONAL", None, "PROFESI"),
    "empty_doctors": ("No doctors linked to this hospital.", None, "Tidak ada dokter yang terhubung dengan rumah sakit ini."),
    "empty_beds": ("No bed data on file.", None, "Tidak ada data tempat tidur yang tercatat."),
    "empty_services": ("No service data on file.", None, "Tidak ada data layanan yang tercatat."),
    "empty_professionals": ("No professional group data on file.", None, "Tidak ada data kelompok profesi yang tercatat."),
    "filter_label_specialties": ("Specialties", None, "Spesialisasi"),
    "filter_label_class": ("Class", None, "Kelas"),
    "filter_label_service": ("Service", None, "Layanan"),
    "filter_label_professional": ("Professional", None, "Profesi"),
    "btn_filter": ("Filter", None, "Filter"),
    "btn_reset": ("Reset", None, "Atur Ulang"),
    "btn_confirm": ("Confirm", None, "Konfirmasi"),
    "filter_search_placeholder": ("Search", None, "Cari"),
    "label_show": ("Show", None, "Menampilkan"),
    "label_entries": ("entries", "entries", "entri"),
    "label_all": ("All", None, "Semua"),
    "label_showing": ("Showing", None, "Menampilkan"),
    "label_to": ("to", None, "sampai"),
    "label_of": ("of", None, "dari"),
    "empty_no_matching": ("No matching entries found", None, "Tidak ada entri yang cocok ditemukan"),
}

MODULES = {
    "hcp_profile": ("Healthcare Professionals - Profile", HCP_PROFILE_KEYS),
    "hospital_profile": ("Hospital - Profile", HOSPITAL_PROFILE_KEYS),
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
        ("crm", "0036_seed_hospital_list_translations"),
        ("base", "0104_merge_20260806_0911"),
    ]

    operations = [
        migrations.RunPython(seed_translations, remove_translations),
    ]
