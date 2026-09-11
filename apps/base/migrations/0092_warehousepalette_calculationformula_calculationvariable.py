import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0091_translationmodule_translationkey_translation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WarehousePalette",
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
                    "code",
                    models.CharField(
                        default="", max_length=30, verbose_name="Code"
                    ),
                ),
                (
                    "initial",
                    models.CharField(
                        blank=True, default="", max_length=15, null=True, verbose_name="Initial"
                    ),
                ),
                (
                    "shortname",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=30,
                        null=True,
                        verbose_name="Shortname",
                    ),
                ),
                (
                    "capacity",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Total kapasitas palete yang tersedia di gudang.",
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Palette Capacity",
                    ),
                ),
                (
                    "utilized",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Jumlah palete yang saat ini terpakai.",
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Palette Used",
                    ),
                ),
                (
                    "remaining",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Sisa palete yang dapat digunakan.",
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Palette Remaining",
                    ),
                ),
                (
                    "warehouse_code",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Kode referensi gudang sesuai sistem sumber.",
                        max_length=30,
                        null=True,
                        verbose_name="Warehouse Code",
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
                    "company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="warehouse_palettes",
                        to="base.company",
                        verbose_name="Company",
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
                "ordering": ("name", "code"),
                "permissions": [
                    ("soft_delete", "Can delete items"),
                    ("soft_restore", "Can restore deleted items"),
                ],
                "unique_together": {("company", "code")},
                "verbose_name": "Warehouse Palette",
                "verbose_name_plural": "Warehouse Palettes",
            },
        ),
        # migrations.CreateModel(
        #     name="CalculationFormula",
        #     fields=[
        #         (
        #             "id",
        #             models.BigAutoField(
        #                 auto_created=True,
        #                 primary_key=True,
        #                 serialize=False,
        #                 verbose_name="ID",
        #             ),
        #         ),
        #         (
        #             "name",
        #             models.CharField(
        #                 blank=True, default="", max_length=100, verbose_name="Name"
        #             ),
        #         ),
        #         (
        #             "description",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=255,
        #                 null=True,
        #                 verbose_name="Description",
        #             ),
        #         ),
        #         (
        #             "remark",
        #             models.CharField(
        #                 blank=True, max_length=255, null=True, verbose_name="Remark"
        #             ),
        #         ),
        #         (
        #             "status",
        #             models.IntegerField(
        #                 choices=[(1, "Active"), (0, "Inactive")],
        #                 default=1,
        #                 verbose_name="Status",
        #             ),
        #         ),
        #         (
        #             "slug",
        #             models.SlugField(
        #                 blank=True,
        #                 default=None,
        #                 max_length=255,
        #                 null=True,
        #                 unique=True,
        #                 verbose_name="Slug",
        #             ),
        #         ),
        #         (
        #             "cat",
        #             models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
        #         ),
        #         (
        #             "uat",
        #             models.DateTimeField(
        #                 blank=True, null=True, verbose_name="Updated at"
        #             ),
        #         ),
        #         (
        #             "dat",
        #             models.DateTimeField(
        #                 blank=True, null=True, verbose_name="Deleted at"
        #             ),
        #         ),
        #         ("deleted", models.BooleanField(default=False)),
        #         (
        #             "code",
        #             models.CharField(
        #                 default="", max_length=64, verbose_name="Code"
        #             ),
        #         ),
        #         (
        #             "category",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=64,
        #                 null=True,
        #                 verbose_name="Category",
        #             ),
        #         ),
        #         (
        #             "version",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=32,
        #                 null=True,
        #                 verbose_name="Version",
        #             ),
        #         ),
        #         (
        #             "expression",
        #             models.TextField(
        #                 help_text="Rumus utama yang menjadi acuan perhitungan.",
        #                 verbose_name="Expression",
        #             ),
        #         ),
        #         (
        #             "target_systems",
        #             models.JSONField(
        #                 blank=True,
        #                 default=list,
        #                 help_text="Daftar sistem yang menggunakan rumus ini (mis. HiveForest, Power BI, Excel).",
        #                 verbose_name="Target Systems",
        #             ),
        #         ),
        #         (
        #             "metadata",
        #             models.JSONField(
        #                 blank=True,
        #                 default=dict,
        #                 help_text="Informasi tambahan seperti asumsi, referensi sheet, atau catatan migrasi.",
        #                 verbose_name="Metadata",
        #             ),
        #         ),
        #         (
        #             "cby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="+",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Created by",
        #             ),
        #         ),
        #         (
        #             "dby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="%(class)s_deleted",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Deleted by",
        #             ),
        #         ),
        #         (
        #             "uby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="%(class)s_updated",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Updated by",
        #             ),
        #         ),
        #     ],
        #     options={
        #         "ordering": ("code",),
        #         "permissions": [
        #             ("soft_delete", "Can delete items"),
        #             ("soft_restore", "Can restore deleted items"),
        #         ],
        #         "unique_together": {("code", "version")},
        #         "verbose_name": "Calculation Formula",
        #         "verbose_name_plural": "Calculation Formulas",
        #     },
        # ),
        # migrations.CreateModel(
        #     name="CalculationVariable",
        #     fields=[
        #         (
        #             "id",
        #             models.BigAutoField(
        #                 auto_created=True,
        #                 primary_key=True,
        #                 serialize=False,
        #                 verbose_name="ID",
        #             ),
        #         ),
        #         (
        #             "name",
        #             models.CharField(
        #                 blank=True, default="", max_length=100, verbose_name="Name"
        #             ),
        #         ),
        #         (
        #             "description",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=255,
        #                 null=True,
        #                 verbose_name="Description",
        #             ),
        #         ),
        #         (
        #             "remark",
        #             models.CharField(
        #                 blank=True, max_length=255, null=True, verbose_name="Remark"
        #             ),
        #         ),
        #         (
        #             "status",
        #             models.IntegerField(
        #                 choices=[(1, "Active"), (0, "Inactive")],
        #                 default=1,
        #                 verbose_name="Status",
        #             ),
        #         ),
        #         (
        #             "slug",
        #             models.SlugField(
        #                 blank=True,
        #                 default=None,
        #                 max_length=255,
        #                 null=True,
        #                 unique=True,
        #                 verbose_name="Slug",
        #             ),
        #         ),
        #         (
        #             "cat",
        #             models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
        #         ),
        #         (
        #             "uat",
        #             models.DateTimeField(
        #                 blank=True, null=True, verbose_name="Updated at"
        #             ),
        #         ),
        #         (
        #             "dat",
        #             models.DateTimeField(
        #                 blank=True, null=True, verbose_name="Deleted at"
        #             ),
        #         ),
        #         ("deleted", models.BooleanField(default=False)),
        #         (
        #             "symbol",
        #             models.CharField(max_length=50, verbose_name="Symbol"),
        #         ),
        #         (
        #             "label",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=100,
        #                 null=True,
        #                 verbose_name="Label",
        #             ),
        #         ),
        #         (
        #             "data_type",
        #             models.CharField(
        #                 choices=[
        #                     ("string", "String"),
        #                     ("integer", "Integer"),
        #                     ("decimal", "Decimal"),
        #                     ("percentage", "Percentage"),
        #                     ("boolean", "Boolean"),
        #                 ],
        #                 default="decimal",
        #                 max_length=20,
        #                 verbose_name="Data Type",
        #             ),
        #         ),
        #         (
        #             "default_value",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=255,
        #                 null=True,
        #                 verbose_name="Default Value",
        #             ),
        #         ),
        #         (
        #             "unit",
        #             models.CharField(
        #                 blank=True, default="", max_length=30, null=True, verbose_name="Unit"
        #             ),
        #         ),
        #         (
        #             "source_reference",
        #             models.CharField(
        #                 blank=True,
        #                 default="",
        #                 max_length=255,
        #                 null=True,
        #                 verbose_name="Source Reference",
        #             ),
        #         ),
        #         (
        #             "cby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="+",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Created by",
        #             ),
        #         ),
        #         (
        #             "dby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="%(class)s_deleted",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Deleted by",
        #             ),
        #         ),
        #         (
        #             "formula",
        #             models.ForeignKey(
        #                 on_delete=django.db.models.deletion.CASCADE,
        #                 related_name="variables",
        #                 to="base.calculationformula",
        #                 verbose_name="Formula",
        #             ),
        #         ),
        #         (
        #             "uby",
        #             models.ForeignKey(
        #                 blank=True,
        #                 editable=False,
        #                 null=True,
        #                 on_delete=django.db.models.deletion.SET_NULL,
        #                 related_name="%(class)s_updated",
        #                 to=settings.AUTH_USER_MODEL,
        #                 verbose_name="Updated by",
        #             ),
        #         ),
        #     ],
        #     options={
        #         "ordering": ("formula", "symbol"),
        #         "permissions": [
        #             ("soft_delete", "Can delete items"),
        #             ("soft_restore", "Can restore deleted items"),
        #         ],
        #         "unique_together": {("formula", "symbol")},
        #         "verbose_name": "Calculation Variable",
        #         "verbose_name_plural": "Calculation Variables",
        #     },
        # ),
    ]
