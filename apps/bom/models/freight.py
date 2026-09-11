from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.text import slugify

from apps.base.models.abstracts import GenericAbstract


def _build_unique_slug(instance, *parts):
    slug_source = "-".join(
        (part or "").strip() for part in parts if (part or "").strip()
    )
    base_slug = slugify(slug_source) or slugify(instance.name or "") or "item"
    base_slug = base_slug[:255]
    slug = base_slug
    counter = 1

    while instance.__class__.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[: 255 - len(suffix)]}{suffix}"
        counter += 1

    return slug


class FreightCost(GenericAbstract):
    BURDEN_TYPE_OI = "OI BURDEN"
    BURDEN_TYPE_OU_LEGACY = "OU BURDEN"
    BURDEN_TYPE_MUP = "MUP BURDEN"
    BURDEN_TYPE_CHOICES = (
        (BURDEN_TYPE_OI, "OI BURDEN"),
        (BURDEN_TYPE_MUP, "MUP BURDEN"),
    )

    shipping_date = models.DateField(
        null=True, blank=True, verbose_name="Shipping Date"
    )
    freight_type = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Freight Type"
    )
    burden_type = models.CharField(
        max_length=20,
        choices=BURDEN_TYPE_CHOICES,
        default=BURDEN_TYPE_OI,
        verbose_name="Burden Type",
    )

    class Meta:
        verbose_name = "Freight Cost"
        verbose_name_plural = "Freight Costs"
        ordering = ["-shipping_date", "name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                condition=~Q(name=""),
                name="uniq_bom_freightcost_name_ci",
            ),
        ]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
            ("export_report", "Can export freight cost report"),
        ]

    def __str__(self):
        return f"{self.name} – {self.shipping_date}"

    def _get_existing_by_name(self):
        freight_name = (self.name or "").strip()
        if not freight_name:
            return None

        return (
            self.__class__.objects.annotate(name_ci=Lower("name"))
            .filter(name_ci=freight_name.lower())
            .exclude(pk=self.pk)
            .order_by("id")
            .first()
        )

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        self.freight_type = (self.freight_type or "").strip()
        if self.burden_type == self.BURDEN_TYPE_OU_LEGACY:
            self.burden_type = self.BURDEN_TYPE_OI
        if self.burden_type not in dict(self.BURDEN_TYPE_CHOICES):
            self.burden_type = self.BURDEN_TYPE_OI
        self.slug = _build_unique_slug(self, self.name)

        existing = None
        if not self.pk:
            existing = self._get_existing_by_name()
            if existing:
                self.pk = existing.pk
                self.slug = existing.slug
                if not self.shipping_date:
                    self.shipping_date = existing.shipping_date
                if not self.freight_type:
                    self.freight_type = existing.freight_type
                if self.burden_type == self.BURDEN_TYPE_OI and existing.burden_type:
                    self.burden_type = existing.burden_type
                if not (self.description or "").strip():
                    self.description = existing.description
                if not (self.remark or "").strip():
                    self.remark = existing.remark
                self.status = existing.status
                self.deleted = existing.deleted

        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
            if self.pk:
                raise

            existing = self._get_existing_by_name()
            if existing is None:
                raise

            self.pk = existing.pk
            self.slug = existing.slug
            super().save(*args, **kwargs)


class FreightCostDetail(GenericAbstract):
    freight = models.ForeignKey(
        "bom.FreightCost",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="details",
        verbose_name="Freight Cost",
    )
    item_code = models.CharField(
        max_length=50, null=True, blank=True, default="", verbose_name="Item Code"
    )
    item_description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="",
        verbose_name="Item Description",
    )
    from_location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="",
        verbose_name="From Location",
    )
    to_location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="",
        verbose_name="To Location",
    )
    expedition_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="",
        verbose_name="Expedition Name",
    )
    expedition_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default="",
        verbose_name="Expedition Type",
    )
    kode_cab = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        default="",
        verbose_name="Kode Cabang",
    )
    nama_cab = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="",
        verbose_name="Nama Cabang",
    )
    product = models.ForeignKey(
        "sales.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="freight_cost_details",
        verbose_name="Product",
    )
    product_distributor = models.ForeignKey(
        "supplychain.DistributorItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="freight_cost_details",
        verbose_name="Product Distributor",
        db_column="product_id_distributor",
    )
    packaging_type = models.ForeignKey(
        "sales.ProductPackage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="freight_cost_details",
        verbose_name="Packaging Type",
    )
    principal = models.ForeignKey(
        "base.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="freight_cost_details",
        verbose_name="Nama Principal",
    )
    qty_freight = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Qty Freight",
    )
    total_weight = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Total Weight",
    )
    group_produk = models.CharField(
        max_length=100, null=True, blank=True, default="", verbose_name="Group Produk"
    )
    item_group = models.CharField(
        max_length=100, null=True, blank=True, default="", verbose_name="Item Group"
    )
    total_freight = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total Freight",
    )
    total_cost = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total Cost",
    )

    class Meta:
        db_table = "bom_freightcost_detail"
        verbose_name = "Freight Cost Detail"
        verbose_name_plural = "Freight Cost Details"
        ordering = ["freight", "item_code", "id"]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        freight_no = self.freight.name if self.freight else "-"
        return f"{freight_no} | {self.item_code} – {self.item_description}"

    @property
    def resolved_product(self):
        if self.product:
            return self.product

        if self.product_distributor and self.product_distributor.product:
            return self.product_distributor.product

        return None

    @property
    def resolved_distributor_item(self):
        if self.product_distributor:
            return self.product_distributor

        product = self.product
        if not product:
            return None

        prefetched_items = getattr(product, "_prefetched_objects_cache", {}).get(
            "distributoritem_set"
        )
        distributor_items = (
            prefetched_items
            if prefetched_items is not None
            else product.distributoritem_set.select_related("group", "product").all()
        )

        fallback_item = None
        for distributor_item in distributor_items:
            if fallback_item is None:
                fallback_item = distributor_item

            group = getattr(distributor_item, "group", None)
            if group and not getattr(group, "deleted", False):
                return distributor_item

        return fallback_item

    @property
    def resolved_packaging(self):
        packaging_type_id = self.packaging_type_id
        if not packaging_type_id:
            return None

        packaging_model = self._meta.get_field("packaging_type").remote_field.model
        try:
            return self.packaging_type
        except packaging_model.DoesNotExist:
            return None

    @property
    def packaging_type_value(self):
        packaging = self.resolved_packaging
        if packaging:
            return packaging.name

        return str(self.packaging_type_id or "")

    def get_product_group_produk(self):
        distributor_item = self.resolved_distributor_item
        if distributor_item:
            group = getattr(distributor_item, "group", None)
            if group and not getattr(group, "deleted", False):
                return group.name

        return ""

    @property
    def nama_principal(self):
        return self.principal.name if self.principal else ""

    @property
    def item_group_name(self):
        if (self.item_group or "").strip():
            return self.item_group

        product = self.resolved_product
        if product and product.subgroup:
            return product.subgroup.name

        return ""

    def save(self, *args, **kwargs):
        if self.product_distributor and not self.product and self.product_distributor.product:
            self.product = self.product_distributor.product

        product = self.resolved_product
        if product:
            if not (self.group_produk or "").strip():
                self.group_produk = self.get_product_group_produk()
            if not (self.item_group or "").strip() and product.subgroup:
                self.item_group = product.subgroup.name
            if not (self.item_code or "").strip():
                self.item_code = product.code
            if not (self.item_description or "").strip():
                self.item_description = product.name

        if self.product_distributor:
            if not (self.item_code or "").strip():
                self.item_code = self.product_distributor.code
            if not (self.item_description or "").strip():
                self.item_description = self.product_distributor.name

        if not (self.name or "").strip():
            self.name = (self.item_code or self.item_description or "").strip()

        if not (self.description or "").strip() and (self.item_description or "").strip():
            self.description = self.item_description

        self.slug = _build_unique_slug(self, self.name, self.description)

        super().save(*args, **kwargs)


class FreightCostImportJob(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    )

    upload_file = models.FileField(upload_to="freight_imports/")
    original_filename = models.CharField(max_length=255)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="freight_cost_import_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED,
    )
    background_pid = models.IntegerField(null=True, blank=True)
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    created_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    message = models.CharField(max_length=255, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Freight Cost Import Job"
        verbose_name_plural = "Freight Cost Import Jobs"

    def __str__(self):
        return f"Freight Import #{self.pk} - {self.original_filename}"
