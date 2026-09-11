from django.shortcuts import render
from django.apps import apps
from importlib import import_module
from apps.base.translation_registry import TRANSLATABLE_MODELS

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: translation_console                                 ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Shared translation admin class across apps.      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\views\console.py                          ║
# ║  Created: May/30-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
def translation_console(request):
    rows = []

    for entry in TRANSLATABLE_MODELS:
        module_path, class_name = ".".join(entry["model_class"].split(".")[:-1]), entry["model_class"].split(".")[-1]
        model_class = getattr(import_module(module_path), class_name)
        objects = model_class.objects.all()

        for obj in objects:
            for field in entry["fields"]:
                rows.append({
                    "application": entry["app"],
                    "model": entry["model"],
                    "field": field,
                    "value": getattr(obj, field, ""),  # ✅ original
                    "value_en": getattr(obj, f"{field}_en", "") or getattr(obj, field, ""),
                    "value_id": getattr(obj, f"{field}_ind", ""),
                    "value_ja": getattr(obj, f"{field}_ja", ""),
                })
    context = {
        'page_title': 'Translation Console',
        'card_title': 'Model Field Translations',
        'table_id': 'translation-table',
        'tbody_id': 'translation-body',
        'columns': ['Application', 'Model', 'Field', 'Original', 'EN', 'ID', 'JA'],
        'data': rows,
        'custom_js': 'custom/js/translation_console.js',
    }
    return render(request, 'base/translation_console.html', context)