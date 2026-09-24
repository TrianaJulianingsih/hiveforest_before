from django.conf import settings
from django.db import models
from apps.humancapital.models.employee_models import Employee

class AuditModel(models.Model):
    status = models.IntegerField(
        default=1,
    )
    deleted = models.BooleanField(
        default=False,
    )
    cat = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created_at",
    )
    cby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="cby_id",
        related_name="%(class)s_created",
        verbose_name="created_by",
    )
    uat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="updated_at",
    )
    uby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="uby_id",
        related_name="%(class)s_updated",
        verbose_name="updated_by",
    )
    dat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="deleted_at",
    )
    dby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="dby_id",
        related_name="%(class)s_deleted",
        verbose_name="deleted_by",
    )
    class Meta:
        abstract = True

# Learning Category
class HumancapitalLearningCategory(AuditModel):
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    name = models.CharField(
        max_length=100,
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    class Meta:
        db_table = "humancapital_learning_category"
        verbose_name = "Learning Category"
        verbose_name_plural = "Learning Categories"
    def __str__(self):
        return self.name

# Learning Program
class HumancapitalLearningProgram(AuditModel):
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    name = models.CharField(
        max_length=100,
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    target_completion_count = models.IntegerField(
        default=4,
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.00,
    )
    category = models.ForeignKey(
        HumancapitalLearningCategory,
        on_delete=models.CASCADE,
        db_column="category_id",
        related_name="programs",
    )
    class Meta:
        db_table = "humancapital_learning_program"
        verbose_name = "Learning Program"
        verbose_name_plural = "Learning Programs"
    def __str__(self):
        return self.name

# Learning Topic
class HumancapitalLearningTopic(AuditModel):
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    name = models.CharField(
        max_length=200,
    )
    program = models.ForeignKey(
        HumancapitalLearningProgram,
        on_delete=models.CASCADE,
        db_column="program_id",
        related_name="topics",
    )
    delivery_method = models.CharField(
        max_length=20,
    )
    source_platform = models.CharField(
        max_length=50,
        default="internal",
    )
    target_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    ecourse_url = models.TextField(
        blank=True,
        null=True,
    )
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    class Meta:
        db_table = "humancapital_learning_topic"
        verbose_name = "Learning Topic"
        verbose_name_plural = "Learning Topics"
    def __str__(self):
        return self.name

# Learning Schedule
class HumancapitalLearningSchedule(AuditModel):
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    topic = models.ForeignKey(
        HumancapitalLearningTopic,
        on_delete=models.CASCADE,
        db_column="topic_id",
        related_name="schedules",
    )
    name = models.CharField(
        max_length=150,
    )
    training_type = models.CharField(
        max_length=20,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    schedule_display = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    location_or_link = models.TextField(
        blank=True,
        null=True,
    )
    trainer_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    quota = models.IntegerField(
        default=0,
    )
    schedule_status = models.CharField(
        max_length=20,
        default="scheduled",
    )
    class Meta:
        db_table = "humancapital_learning_schedule"
        verbose_name = "Learning Schedule"
        verbose_name_plural = "Learning Schedules"
    def __str__(self):
        return f"{self.name} ({self.code})"
    
# Learning Enrollment
class HumancapitalLearningEnrollment(AuditModel):
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column="employee_id",
        related_name="learning_enrollments",
    )
    training_source = models.CharField(
        max_length=20,
        default="internal",
    )
    period_year = models.IntegerField(
        default=2026,
    )
    schedule = models.ForeignKey(
        HumancapitalLearningSchedule,
        on_delete=models.SET_NULL,
        db_column="schedule_id",
        related_name="enrollments",
        blank=True,
        null=True,
    )
    invitation_status = models.CharField(
        max_length=30,
        default="not_invited",
    )
    invitation_sent_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    # External Training
    external_topic_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    provider_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    duration_text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    date_mode = models.CharField(
        max_length=10,
        default="single",
    )
    start_date = models.DateField(
        blank=True,
        null=True,
    )
    end_date = models.DateField(
        blank=True,
        null=True,
    )
    proof_type = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )

    # Approval
    approval_status = models.CharField(
        max_length=20,
        default="approved",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="approved_by_id",
        related_name="learning_enrollments_approved",
        blank=True,
        null=True,
    )
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
    )
    remark = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "humancapital_learning_enrollment"
        verbose_name = "Learning Enrollment"
        verbose_name_plural = "Learning Enrollments"

    def __str__(self):
        return self.code

# Learning Completion
class HumancapitalLearningCompletion(AuditModel):
    enrollment = models.OneToOneField(
        HumancapitalLearningEnrollment,
        on_delete=models.CASCADE,
        db_column="enrollment_id",
        related_name="completion",
    )
    attendance_status = models.CharField(
        max_length=20,
        default="present",
    )
    pre_test_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    post_test_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    grade_status = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )
    is_passed = models.BooleanField(
        default=False,
    )
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    certificate_url = models.TextField(
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    feedback_rating = models.IntegerField(
        blank=True,
        null=True,
    )
    feedback_notes = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "humancapital_learning_completion"
        verbose_name = "Learning Completion"
        verbose_name_plural = "Learning Completions"

    def __str__(self):
        return f"Completion for {self.enrollment.code}"

# Learning File
class HumancapitalLearningFile(AuditModel):
    external_training = models.ForeignKey(
        HumancapitalLearningEnrollment,
        on_delete=models.CASCADE,
        db_column="external_training_id",
        related_name="files",
    )
    file_name = models.CharField(
        max_length=255,
    )
    file_path = models.TextField()
    file_size_bytes = models.BigIntegerField(
        blank=True,
        null=True,
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    drive_url = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "humancapital_learning_file"
        verbose_name = "Learning File"
        verbose_name_plural = "Learning Files"

    def __str__(self):
        return self.file_name