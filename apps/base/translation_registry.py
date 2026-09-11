# ╔════════════════════════════════════════════════════════════╗
# ║  Name: translation_registry                                ║
# ║  Type: Function Base View                                  ║
# ║  Purpose: Registrer translatable models                    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\views\translation_registry.py             ║
# ║  Created: May/30-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝

TRANSLATABLE_MODELS = [
    {
        "app": "CMS",
        "model": "ApplicationList",
        "model_class": "apps.cms.models.appmanagers.ApplicationList",
        "fields": ["shortname"],
    },
    # You can later register more models here
]