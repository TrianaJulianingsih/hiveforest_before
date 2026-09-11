import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0090_forcepasswordstatus"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TranslationModule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Name"
                    ),
                ),
                (
                    "remark",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Remark"
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Active"), (0, "Inactive")],
                        default=1,
                        verbose_name="Status",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        blank=True,
                        default=None,
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "cat",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "uat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Updated at"
                    ),
                ),
                (
                    "dat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                ("deleted", models.BooleanField(default=False)),
                (
                    "code",
                    models.CharField(
                        help_text="Contoh: sub_distributor, employee, product",
                        max_length=50,
                        unique=True,
                        verbose_name="Module Code",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "cby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "dby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted by",
                    ),
                ),
                (
                    "uby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated by",
                    ),
                ),
            ],
            options={
                "verbose_name": "Translation Module",
                "verbose_name_plural": "Translation Modules",
                "db_table": "base_translation_module",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="TranslationKey",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Name"
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "remark",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Remark"
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Active"), (0, "Inactive")],
                        default=1,
                        verbose_name="Status",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        blank=True,
                        default=None,
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "cat",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "uat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Updated at"
                    ),
                ),
                (
                    "dat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                ("deleted", models.BooleanField(default=False)),
                (
                    "key",
                    models.CharField(
                        help_text="Contoh: page_title, btn_add, col_name",
                        max_length=100,
                        verbose_name="Translation Key",
                    ),
                ),
                (
                    "default_value",
                    models.TextField(
                        blank=True,
                        help_text="Nilai default dalam bahasa Inggris",
                        null=True,
                        verbose_name="Default Value (English)",
                    ),
                ),
                (
                    "cby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "dby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted by",
                    ),
                ),
                (
                    "uby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated by",
                    ),
                ),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translation_keys",
                        to="base.translationmodule",
                        verbose_name="Module",
                    ),
                ),
            ],
            options={
                "verbose_name": "Translation Key",
                "verbose_name_plural": "Translation Keys",
                "db_table": "base_translation_key",
                "ordering": ["module", "key"],
                "unique_together": {("module", "key")},
            },
        ),
        migrations.CreateModel(
            name="Translation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Name"
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "remark",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Remark"
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Active"), (0, "Inactive")],
                        default=1,
                        verbose_name="Status",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        blank=True,
                        default=None,
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "cat",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "uat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Updated at"
                    ),
                ),
                (
                    "dat",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                ("deleted", models.BooleanField(default=False)),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("en", "English"),
                            ("id", "Indonesia"),
                            ("ja", "Japanese"),
                        ],
                        max_length=5,
                        verbose_name="Language",
                    ),
                ),
                ("value", models.TextField(verbose_name="Translated Value")),
                (
                    "cby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "dby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted by",
                    ),
                ),
                (
                    "uby",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated by",
                    ),
                ),
                (
                    "translation_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="base.translationkey",
                        verbose_name="Translation Key",
                    ),
                ),
            ],
            options={
                "verbose_name": "Translation",
                "verbose_name_plural": "Translations",
                "db_table": "base_translation",
                "ordering": ["translation_key", "language"],
                "unique_together": {("translation_key", "language")},
            },
        ),
    ]
