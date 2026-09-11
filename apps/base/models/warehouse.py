from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models.abstracts import GenericAbstract
from apps.base.models.entities import Company
from apps.supplychain.models.distributions import Branch


class WarehousePalette(GenericAbstract):
    code = models.CharField(max_length=30, null=False, default="", verbose_name="Code")
    deleted = models.BooleanField(
        default=False, verbose_name="Deleted", help_text="Soft delete flag."
    )
    initial = models.CharField(
        max_length=15, null=True, blank=True, default="", verbose_name="Initial"
    )
    shortname = models.CharField(
        max_length=30, null=True, blank=True, default="", verbose_name="Shortname"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warehouse_palettes",
        verbose_name="Company",
    )
    ambient_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Ambient Capacity",
        help_text="Kapasitas palete ruangan ambient.",
    )
    ac_room_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="AC Room Capacity",
        help_text="Kapasitas palete ruangan ber-AC.",
    )
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Palette Capacity",
        help_text="Total kapasitas palete yang tersedia di gudang.",
    )
    utilized = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Palette Used",
        help_text="Jumlah palete yang saat ini terpakai.",
    )
    # branch = models.ForeignKey(
    #     "supplychain.Branch",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="warehouse_palettes",
    #     verbose_name="Branch",
    #     help_text="Relasi ke cabang (branch) yang menggunakan palete ini.",
    # )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="warehouse_palettes",
        verbose_name="Branch",
        help_text="Relasi ke cabang (branch) yang menggunakan palete ini.",
    )
    remaining = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Palette Remaining",
        help_text="Sisa palete yang dapat digunakan.",
    )
    warehouse_code = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        default="",
        verbose_name="Warehouse Code",
        help_text="Kode referensi gudang sesuai sistem sumber.",
    )

    class Meta:
        verbose_name = "Warehouse Palette"
        verbose_name_plural = "Warehouse Palettes"
        ordering = ("name", "code")
        unique_together = ("company", "code")
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def clean(self):
        super().clean()
        if self.ambient_capacity is None or self.ambient_capacity < 0:
            raise ValidationError(
                {"ambient_capacity": _("Nilai kapasitas ambient harus >= 0.")}
            )
        if self.ac_room_capacity is None or self.ac_room_capacity < 0:
            raise ValidationError(
                {"ac_room_capacity": _("Nilai kapasitas AC room harus >= 0.")}
            )

    def save(self, *args, **kwargs):
        user = getattr(self, "_request_user", None)
        if not self.name and self.warehouse_code:
            self.name = self.warehouse_code
        # Capacity selalu hasil penjumlahan dua field
        self.capacity = (self.ambient_capacity or 0) + (self.ac_room_capacity or 0)
        self.remaining = max(self.capacity - (self.utilized or 0), 0)
        import datetime

        now = datetime.datetime.now()
        if not self.pk:
            self.cat = now
            if user:
                self.cby_id = user.id
        else:
            self.uat = now
            if user:
                self.uby_id = user.id
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard=False):
        user = getattr(self, "_request_user", None)
        import datetime

        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted = True
        self.dat = datetime.datetime.now()
        if user:
            self.dby_id = user.id

        self.save(update_fields=["deleted", "dat", "dby_id"])


# class CalculationFormula(GenericAbstract):
#     class TargetSystem(models.TextChoices):
#         HIVEFOREST = "hiveforest", "HiveForest"
#         POWER_BI = "power_bi", "Power BI"
#         EXCEL = "excel", "Excel"
#         OTHERS = "others", "Other"

#     code = models.CharField(max_length=64, null=False, default="", verbose_name="Code")
#     category = models.CharField(max_length=64, null=True, blank=True, default="", verbose_name="Category")
#     version = models.CharField(max_length=32, null=True, blank=True, default="", verbose_name="Version")
#     expression = models.TextField(verbose_name="Expression", help_text="Rumus utama yang menjadi acuan perhitungan.")
#     target_systems = models.JSONField(
#         default=list,
#         blank=True,
#         verbose_name="Target Systems",
#         help_text="Daftar sistem yang menggunakan rumus ini (mis. HiveForest, Power BI, Excel).",
#     )
#     metadata = models.JSONField(
#         default=dict,
#         blank=True,
#         verbose_name="Metadata",
#         help_text="Informasi tambahan seperti asumsi, referensi sheet, atau catatan migrasi.",
#     )

#     class Meta:
#         verbose_name = "Calculation Formula"
#         verbose_name_plural = "Calculation Formulas"
#         ordering = ("code",)
#         unique_together = ("code", "version")
#         permissions = [
#             ("soft_delete", "Can delete items"),
#             ("soft_restore", "Can restore deleted items"),
#         ]

#     def clean(self):
#         super().clean()
#         if not self.expression:
#             raise ValidationError({"expression": _("Expression wajib diisi.")})
#         if self.target_systems and not isinstance(self.target_systems, list):
#             raise ValidationError({"target_systems": _("Format target systems harus berupa list.")})

#     def save(self, *args, **kwargs):
#         if not self.name and self.code:
#             self.name = self.code
#         if self.target_systems is None:
#             self.target_systems = []
#         super().save(*args, **kwargs)


# class CalculationVariable(GenericAbstract):
#     class DataType(models.TextChoices):
#         STRING = "string", "String"
#         INTEGER = "integer", "Integer"
#         DECIMAL = "decimal", "Decimal"
#         PERCENTAGE = "percentage", "Percentage"
#         BOOLEAN = "boolean", "Boolean"

#     formula = models.ForeignKey(
#         CalculationFormula,
#         on_delete=models.CASCADE,
#         related_name="variables",
#         verbose_name="Formula",
#     )
#     symbol = models.CharField(max_length=50, verbose_name="Symbol")
#     label = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Label")
#     data_type = models.CharField(
#         max_length=20,
#         choices=DataType.choices,
#         default=DataType.DECIMAL,
#         verbose_name="Data Type",
#     )
#     default_value = models.CharField(
#         max_length=255,
#         null=True,
#         blank=True,
#         default="",
#         verbose_name="Default Value",
#         help_text="Nilai bawaan atau contoh nilai yang digunakan di Excel.",
#     )
#     unit = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Unit")
#     source_reference = models.CharField(
#         max_length=255,
#         null=True,
#         blank=True,
#         default="",
#         verbose_name="Source Reference",
#         help_text="Referensi kolom atau sheet asal data.",
#     )

#     class Meta:
#         verbose_name = "Calculation Variable"
#         verbose_name_plural = "Calculation Variables"
#         ordering = ("formula", "symbol")
#         unique_together = ("formula", "symbol")
#         permissions = [
#             ("soft_delete", "Can delete items"),
#             ("soft_restore", "Can restore deleted items"),
#         ]

#     def clean(self):
#         super().clean()
#         if not self.symbol:
#             raise ValidationError({"symbol": _("Symbol wajib diisi.")})

#     def save(self, *args, **kwargs):
#         if not self.name:
#             self.name = self.label or self.symbol
#         super().save(*args, **kwargs)
