from django.contrib import admin
from apps.base.models.translation import TranslationModule, TranslationKey, Translation


# ═══════════════════════════════════════════════════════════
# FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════
class TranslationInline(admin.TabularInline):
    model = Translation
    extra = 3
    fields = ["language", "value"]


@admin.register(TranslationModule)
class TranslationModuleAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "description", "status", "cat", "cby"]
    list_filter = ["status"]
    search_fields = ["code", "name", "description"]
    ordering = ["code"]


@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    list_display = ["module", "key", "default_value", "name", "status"]
    list_filter = ["module", "status"]
    search_fields = ["key", "name", "default_value"]
    ordering = ["module", "key"]
    inlines = [TranslationInline]

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("module", "key", "name", "default_value", "status")},
        ),
        ("Description", {"fields": ("description",), "classes": ("collapse",)}),
    )


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ["translation_key", "language", "value_preview", "status"]
    list_filter = ["language", "translation_key__module", "status"]
    search_fields = ["translation_key__key", "value"]
    ordering = ["translation_key", "language"]

    def value_preview(self, obj):
        return obj.value[:100] + "..." if len(obj.value) > 100 else obj.value

    value_preview.short_description = "Value"
