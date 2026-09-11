from modeltranslation.translator import register, TranslationOptions
from apps.cms.models.appmanagers import ApplicationList

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ApplicationListTranslation                          ║
# ║  Purpose: Mantain application translation                  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\cms\translations.py                            ║
# ║  Created: May/30-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@register(ApplicationList)
class ApplicationListTranslationOptions(TranslationOptions):
    fields = ('shortname',)