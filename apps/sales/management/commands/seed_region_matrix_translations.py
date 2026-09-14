"""
seed_region_matrix_translations.py
Management command to seed TranslationModule, TranslationKey, and Translation
records for the Region Matrix page (module code: 'region_matrix').

Usage:
    python manage.py seed_region_matrix_translations
    python manage.py seed_region_matrix_translations --force   # overwrite existing values
"""

from django.core.management.base import BaseCommand
from apps.base.models.translation import TranslationModule, TranslationKey, Translation


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: seed_region_matrix_translations                     ║
# ║  Type: Management Command                                  ║
# ║  Purpose: Seed DB translations for Region Matrix page      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps/sales/management/commands/                     ║
# ║        seed_region_matrix_translations.py                  ║
# ║  Created: Jun/11-2026 by FaisalS                           ║
# ╚════════════════════════════════════════════════════════════╝

# Translation keys definition:
# Structure: { key: (default_value_en, id_value) }
TRANSLATION_KEYS = {
    # ── Page ─────────────────────────────────────────────────
    "page_title":           ("Region Matrix",               "Matriks Region"),
    # ── Buttons ──────────────────────────────────────────────
    "btn_expand_all":       ("Expand All",                  "Buka Semua"),
    "btn_collapse_all":     ("Collapse All",                "Tutup Semua"),
    "btn_inactive":         ("Inactive",                    "Nonaktif"),
    "btn_cancel":           ("Cancel",                      "Batal"),
    "btn_save":             ("Save",                        "Simpan"),
    # ── Column headers ────────────────────────────────────────
    "col_island":           ("Island",                      "Pulau"),
    "col_province":         ("Province",                    "Provinsi"),
    # ── Modal tabs ───────────────────────────────────────────
    "tab_edit":             ("Edit",                        "Edit"),
    "tab_history":          ("History",                     "Riwayat"),
    # ── Modal labels ─────────────────────────────────────────
    "modal_title":          ("Edit Region Mapping",         "Edit Pemetaan Region"),
    "lbl_province":         ("Province",                    "Provinsi"),
    "lbl_region":           ("Region",                      "Region"),
    "lbl_status":           ("Status",                      "Status"),
    "lbl_effective_date":   ("Effective Date",              "Tanggal Efektif"),
    "lbl_terminated_date":  ("Terminated Date",             "Tanggal Berakhir"),
    # ── Status values ─────────────────────────────────────────
    "lbl_no_mapping":       ("No Mapping",                  "Tidak Ada Pemetaan"),
    "status_active":        ("Active",                      "Aktif"),
    "status_inactive":      ("Inactive",                    "Tidak Aktif"),
    # ── Messages ─────────────────────────────────────────────
    "msg_updated_title":    ("Updated",                     "Diperbarui"),
    "msg_updated_text":     ("Region mapping has been updated.", "Pemetaan region telah diperbarui."),
    # ── History ───────────────────────────────────────────────
    "col_hist_date":        ("Date",                        "Tanggal"),
    "col_hist_by":          ("By",                          "Oleh"),
    "col_hist_action":      ("Action",                      "Aksi"),
    "col_hist_changes":     ("Changes",                     "Perubahan"),
    "lbl_no_history":       ("No history available.",       "Belum ada riwayat perubahan."),
    "action_created":       ("Created",                     "Dibuat"),
    "action_updated":       ("Updated",                     "Diperbarui"),
    "action_inactive":      ("Set Inactive",                "Dinonaktifkan"),
}

MODULE_CODE        = "region_matrix"
MODULE_NAME        = "Region Matrix"
MODULE_DESCRIPTION = "Labels for Region Matrix territory management page"


class Command(BaseCommand):
    help = "Seed translation keys and values for the Region Matrix page"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing translation values",
        )

    def handle(self, *args, **options):
        force = options["force"]

        # 1 ── Ensure TranslationModule exists ──────────────────────────
        module, module_created = TranslationModule.objects.get_or_create(
            code=MODULE_CODE,
            defaults={
                "name":        MODULE_NAME,
                "description": MODULE_DESCRIPTION,
                "status":      1,
            },
        )
        if module_created:
            self.stdout.write(self.style.SUCCESS(f"  [+] Module created : {MODULE_CODE}"))
        else:
            self.stdout.write(f"  [=] Module exists  : {MODULE_CODE}")

        # 2 ── Seed TranslationKey + Translation rows ───────────────────
        created_keys = 0
        updated_keys = 0
        created_trans = 0
        updated_trans = 0

        for key_code, (default_en, value_id) in TRANSLATION_KEYS.items():
            # TranslationKey
            trans_key, key_created = TranslationKey.objects.get_or_create(
                module=module,
                key=key_code,
                defaults={
                    "name":          key_code,
                    "default_value": default_en,
                    "status":        1,
                },
            )
            if key_created:
                created_keys += 1
            elif force:
                trans_key.default_value = default_en
                trans_key.save(update_fields=["default_value"])
                updated_keys += 1

            # Translation rows per language
            lang_values = {
                "en": default_en,
                "id": value_id,
            }
            for lang, value in lang_values.items():
                trans, trans_created = Translation.objects.get_or_create(
                    translation_key=trans_key,
                    language=lang,
                    defaults={"value": value, "name": f"{key_code} ({lang})", "status": 1},
                )
                if trans_created:
                    created_trans += 1
                elif force:
                    trans.value = value
                    trans.save(update_fields=["value"])
                    updated_trans += 1

        # 3 ── Summary ──────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  Translation seed complete:"))
        self.stdout.write(f"    Keys    — created: {created_keys}, updated: {updated_keys}")
        self.stdout.write(f"    Strings — created: {created_trans}, updated: {updated_trans}")
        if not force and (updated_keys + updated_trans) == 0 and (created_keys + created_trans) == 0:
            self.stdout.write(
                self.style.WARNING(
                    "  All entries already exist. Use --force to overwrite."
                )
            )
