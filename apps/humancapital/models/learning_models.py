from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.base.models.abstracts import GenericAbstract
from apps.humancapital.models.employee_models import Employee

class HumancapitalLearningCategory(GenericAbstract):
    code = models.CharField(
        max_length=30,
        unique=True,
    )

    class Meta:
        db_table = "humancapital_learning_category"
        verbose_name = "Learning Category"
        verbose_name_plural = "Learning Categories"

class HumancapitalLearningProgram(GenericAbstract):
    code = models.CharField(
        max_length=30,
        unique=True,
    )

    target_completion_count = models.IntegerField(
        default=4,
    )

    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("80.00"),
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

class HumancapitalLearningTopic(GenericAbstract):
    code = models.CharField(
        max_length=30,
        unique=True,
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

    class Meta:
        db_table = "humancapital_learning_topic"
        verbose_name = "Learning Topic"
        verbose_name_plural = "Learning Topics"

class HumancapitalLearningSchedule(GenericAbstract):
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

class HumancapitalLearningEnrollment(GenericAbstract):
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

    class Meta:
        db_table = "humancapital_learning_enrollment"
        verbose_name = "Learning Enrollment"
        verbose_name_plural = "Learning Enrollments"

    def __str__(self):
        return self.code

class HumancapitalLearningCompletion(GenericAbstract):
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

class HumancapitalLearningFile(GenericAbstract):
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