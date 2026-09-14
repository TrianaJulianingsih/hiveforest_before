import uuid

from django.db import models

from apps.base.models.abstracts import GenericAbstract

# Commit result state
STATE_SUCCESS = "success"
STATE_PARTIAL = "partial"
STATE_FAILED = "failed"

STATE_CHOICES = [
    (STATE_SUCCESS, "Success"),
    (STATE_PARTIAL, "Partial"),
    (STATE_FAILED, "Failed"),
]

# Upload lifecycle for one staged file
STAGE_WAITING = "waiting"
STAGE_READY = "ready"
STAGE_DONE = "done"

STAGE_CHOICES = [
    (STAGE_WAITING, "Waiting"),
    (STAGE_READY, "Ready"),
    (STAGE_DONE, "Done"),
]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: DataImportStaging                                   ║
# ║  Type: Concrete model                                      ║
# ║  Purpose: Hold uploaded files until the batch is complete  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\models\iqvia_import.py               ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
class DataImportStaging(GenericAbstract):
    batch = models.UUIDField(default=uuid.uuid4, db_index=True, verbose_name="Batch")
    dimension = models.CharField(max_length=30, db_index=True, verbose_name="Dimension")
    file = models.FileField(upload_to="iqvia_import/%Y/%m/", verbose_name="File")
    file_name = models.CharField(max_length=255, default="", verbose_name="File Name")
    # Sha256 of raw bytes, blocks the same file twice
    file_hash = models.CharField(max_length=64, default="", verbose_name="File Hash")
    file_type = models.CharField(max_length=10, default="", verbose_name="File Type")
    rows_read = models.IntegerField(default=0, verbose_name="Rows Read")
    columns = models.JSONField(null=True, blank=True, verbose_name="Columns")
    # Parse result cached here so a batch never reads the same file twice
    summary = models.JSONField(null=True, blank=True, verbose_name="Summary")
    stage = models.CharField(
        max_length=10, choices=STAGE_CHOICES, default=STAGE_WAITING,
        db_index=True, verbose_name="Stage",
    )

    class Meta:
        verbose_name = "Data Import Staging"
        verbose_name_plural = "Data Import Stagings"
        ordering = ["batch", "id"]
        # One physical file can enter a batch once only
        unique_together = [["batch", "file_hash"]]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    # GenericAbstract keeps slug unique, empty string would clash
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file_name or str(self.batch)
        if not self.slug:
            self.slug = f"stg-{uuid.uuid4().hex[:16]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension} | {self.file_name}"


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: DataCommitHistory                                   ║
# ║  Type: Concrete model                                      ║
# ║  Purpose: Audit trail of every IQVIA master import         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\models\iqvia_import.py               ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
class DataCommitHistory(GenericAbstract):
    batch = models.UUIDField(default=uuid.uuid4, db_index=True, verbose_name="Batch")
    dimension = models.CharField(max_length=30, db_index=True, verbose_name="Dimension")
    dimension_label = models.CharField(max_length=60, default="", verbose_name="Dimension Label")
    table_name = models.CharField(max_length=60, default="", verbose_name="Table Name")

    # One row per dimension, the batch column ties a multi level file together
    file_name = models.CharField(max_length=255, default="", verbose_name="File Name")

    rows_read = models.IntegerField(default=0, verbose_name="Rows Read")
    rows_clean = models.IntegerField(default=0, verbose_name="Rows Clean")
    rows_insert = models.IntegerField(default=0, verbose_name="Rows Inserted")
    rows_update = models.IntegerField(default=0, verbose_name="Rows Updated")
    rows_same = models.IntegerField(default=0, verbose_name="Rows Unchanged")
    # Subtotal, PivotTable, blank and repeated header rows
    rows_noise = models.IntegerField(default=0, verbose_name="Rows Noise")
    rows_duplicate = models.IntegerField(default=0, verbose_name="Rows Duplicate")

    # Parent value written in the file but missing in the parent table
    orphan_rows = models.IntegerField(default=0, verbose_name="Orphan Rows")
    orphan_field = models.CharField(max_length=60, null=True, blank=True, default="", verbose_name="Orphan Field")
    orphan_parent = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="Orphan Parent")

    state = models.CharField(
        max_length=10, choices=STATE_CHOICES, default=STATE_SUCCESS,
        db_index=True, verbose_name="State",
    )
    message = models.TextField(null=True, blank=True, verbose_name="Message")
    # Sample orphan keys, per file counters, anything the UI needs to expand
    detail = models.JSONField(null=True, blank=True, verbose_name="Detail")
    duration_ms = models.IntegerField(default=0, verbose_name="Duration")

    class Meta:
        verbose_name = "Data Commit History"
        verbose_name_plural = "Data Commit Histories"
        ordering = ["-cat", "-id"]
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    # GenericAbstract keeps slug unique, empty string would clash
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Import {self.dimension_label or self.dimension}"
        if not self.slug:
            self.slug = f"commit-{uuid.uuid4().hex[:16]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dimension_label} +{self.rows_insert} ~{self.rows_update}"