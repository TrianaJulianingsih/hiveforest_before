from django import template
from django.utils.translation import get_language
from apps.base.utils.translation import get_translation, get_module_translations, SafeTranslationDict

# ═══════════════════════════════════════════════════════════
# FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════
register = template.Library()


@register.simple_tag(takes_context=True)
def trans(context, module_code, key, default=None):
    request = context.get("request")
    language = get_language()

    if request and hasattr(request, "LANGUAGE_CODE"):
        language = request.LANGUAGE_CODE

    return get_translation(module_code, key, language, default)


@register.simple_tag(takes_context=True)
def get_translations(context, module_code):
    language = get_language()
    request = context.get("request")

    if request and hasattr(request, "LANGUAGE_CODE"):
        language = request.LANGUAGE_CODE

    result = get_module_translations(module_code, language)
    if result is None:
        result = SafeTranslationDict()
    return result


@register.inclusion_tag("base/language_selector.html", takes_context=True)
def language_selector(context):
    return {
        "request": context.get("request"),
        "current_language": get_language(),
    }
