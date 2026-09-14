from django.db import migrations


MODULE_CODE = "territory_assignment"
MODULE_NAME = "Territory Assignment"
MODULE_DESCRIPTION = "Translations for the territory assignment page"

TRANSLATIONS = {
    "page_title": {
        "default": "Territory Assignment",
        "en": "Territory Assignment",
        "id": "Penugasan Territory",
    },
    "card_title": {
        "default": "Sales Territory Assignment",
        "en": "Sales Territory Assignment",
        "id": "Penugasan Sales Territory",
    },
    "col_user": {
        "default": "User",
        "en": "User",
        "id": "Pengguna",
    },
    "col_medrep": {
        "default": "Medical Representative (MedRep)",
        "en": "Medical Representative (MedRep)",
        "id": "Medical Representative (MedRep)",
    },
    "col_assignment": {
        "default": "Assignment",
        "en": "Assignment",
        "id": "Penugasan",
    },
    "col_position": {
        "default": "Position",
        "en": "Position",
        "id": "Posisi",
    },
    "col_customer": {
        "default": "Customer",
        "en": "Customer",
        "id": "Customer",
    },
    "col_province": {
        "default": "Province",
        "en": "Province",
        "id": "Provinsi",
    },
    "col_regency": {
        "default": "Regency",
        "en": "Regency",
        "id": "Kabupaten/Kota",
    },
    "col_district": {
        "default": "District",
        "en": "District",
        "id": "Kecamatan",
    },
    "col_effective": {
        "default": "Effective",
        "en": "Effective",
        "id": "Efektif",
    },
    "col_terminated": {
        "default": "Terminated",
        "en": "Terminated",
        "id": "Terminasi",
    },
    "empty_message": {
        "default": "No territory assignments found.",
        "en": "No territory assignments found.",
        "id": "Data penugasan territory tidak ditemukan.",
    },
}


def seed_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationKey = apps.get_model("base", "TranslationKey")
    Translation = apps.get_model("base", "Translation")

    module, _ = TranslationModule.objects.get_or_create(
        code=MODULE_CODE,
        defaults={
            "name": MODULE_NAME,
            "description": MODULE_DESCRIPTION,
            "status": 1,
            "deleted": False,
        },
    )

    if module.name != MODULE_NAME or module.description != MODULE_DESCRIPTION:
        module.name = MODULE_NAME
        module.description = MODULE_DESCRIPTION
        module.status = 1
        module.deleted = False
        module.save()

    for key, values in TRANSLATIONS.items():
        translation_key, _ = TranslationKey.objects.get_or_create(
            module=module,
            key=key,
            defaults={
                "name": key.replace("_", " ").title(),
                "default_value": values["default"],
                "status": 1,
                "deleted": False,
            },
        )

        if translation_key.default_value != values["default"]:
            translation_key.default_value = values["default"]
            translation_key.status = 1
            translation_key.deleted = False
            translation_key.save()

        for language in ("en", "id"):
            translation, _ = Translation.objects.get_or_create(
                translation_key=translation_key,
                language=language,
                defaults={
                    "name": f"{translation_key.key} {language}",
                    "value": values[language],
                    "status": 1,
                    "deleted": False,
                },
            )
            if translation.value != values[language]:
                translation.value = values[language]
                translation.status = 1
                translation.deleted = False
                translation.save()


def remove_translations(apps, schema_editor):
    TranslationModule = apps.get_model("base", "TranslationModule")
    TranslationModule.objects.filter(code=MODULE_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0101_sites"),
    ]

    operations = [
        migrations.RunPython(seed_translations, remove_translations),
    ]
