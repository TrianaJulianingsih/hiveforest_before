from django.db import models
from apps.base.models.abstracts import GenericAbstract


# ═══════════════════════════════════════════════════════════
# FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════
class TranslationModule(GenericAbstract):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Module Code",
        help_text="Contoh: sub_distributor, employee, product",
    )
    description = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Description"
    )

    class Meta:
        db_table = "base_translation_module"
        verbose_name = "Translation Module"
        verbose_name_plural = "Translation Modules"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TranslationKey(GenericAbstract):
    module = models.ForeignKey(
        TranslationModule,
        on_delete=models.CASCADE,
        related_name="translation_keys",
        verbose_name="Module",
    )
    key = models.CharField(
        max_length=100,
        verbose_name="Translation Key",
        help_text="Contoh: page_title, btn_add, col_name",
    )
    default_value = models.TextField(
        null=True,
        blank=True,
        verbose_name="Default Value (English)",
        help_text="Nilai default dalam bahasa Inggris",
    )

    class Meta:
        db_table = "base_translation_key"
        verbose_name = "Translation Key"
        verbose_name_plural = "Translation Keys"
        unique_together = [["module", "key"]]
        ordering = ["module", "key"]

    def __str__(self):
        return f"{self.module.code}.{self.key}"


class Translation(GenericAbstract):
    LANGUAGE_CHOICES = (
        ("en", "English"),
        ("id", "Indonesia"),
    )

    translation_key = models.ForeignKey(
        TranslationKey,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name="Translation Key",
    )
    language = models.CharField(
        max_length=5, choices=LANGUAGE_CHOICES, verbose_name="Language"
    )
    value = models.TextField(verbose_name="Translated Value")

    class Meta:
        db_table = "base_translation"
        verbose_name = "Translation"
        verbose_name_plural = "Translations"
        unique_together = [["translation_key", "language"]]
        ordering = ["translation_key", "language"]

    def __str__(self):
        return f"{self.translation_key} ({self.language}): {self.value[:50]}"
