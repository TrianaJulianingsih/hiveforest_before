from django.core.cache import cache
from apps.base.models.translation import TranslationModule, TranslationKey, Translation


# ═══════════════════════════════════════════════════════════
# FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════
class SafeTranslationDict(dict):
    def __getattr__(self, key):
        return self.get(key, key)

    def __getitem__(self, key):
        return self.get(key, key)


def get_translation(module_code, key, language="en", default=None):
    cache_key = f"trans_{module_code}_{key}_{language}"

    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    try:
        translation_key = TranslationKey.objects.select_related("module").get(
            module__code=module_code, key=key
        )

        translation = Translation.objects.filter(
            translation_key=translation_key, language=language
        ).first()

        if translation:
            value = translation.value
        else:
            value = translation_key.default_value or default or key

        cache.set(cache_key, value, 3600)
        return value

    except (TranslationModule.DoesNotExist, TranslationKey.DoesNotExist):
        return default or key


def get_module_translations(module_code, language="en"):
    cache_key = f"trans_module_{module_code}_{language}"

    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return SafeTranslationDict(cached_value)

    try:
        module = TranslationModule.objects.get(code=module_code)

        result = {}
        for trans_key in module.translation_keys.all():
            translation = trans_key.translations.filter(language=language).first()
            if translation:
                result[trans_key.key] = translation.value
            else:
                result[trans_key.key] = trans_key.default_value or trans_key.key

        cache.set(cache_key, result, 3600)
        return SafeTranslationDict(result)

    except TranslationModule.DoesNotExist:
        return SafeTranslationDict()


def clear_translation_cache(module_code=None):
    if module_code:
        for lang in ["en", "id"]:
            cache.delete(f"trans_module_{module_code}_{lang}")
    else:
        cache.delete_pattern("trans_*")
