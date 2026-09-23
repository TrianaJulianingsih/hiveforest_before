from django.db import models
from django.conf import settings

# LEARNING CATEGORY
class LearningCategory(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_categories_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_categories_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_categories_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_category"

    def __str__(self):
        return f"{self.code} - {self.name}"

# LEARNING PROGRAM
class LearningProgram(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    target_completion_count = models.IntegerField(
        default=4
    )

    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.00
    )

    category_id = models.ForeignKey(
        LearningCategory,
        on_delete=models.PROTECT,
        related_name="programs"
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_programs_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_programs_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_programs_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_program"

    def __str__(self):
        return f"{self.code} - {self.name}"

# LEARNING TOPIC
class LearningTopic(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=200
    )

    program_id = models.ForeignKey(
        LearningProgram,
        on_delete=models.PROTECT,
        related_name="topics"
    )

    delivery_method = models.CharField(
        max_length=20,
        # default="internal"
    )

    source_platform = models.CharField(
        max_length=50,
        default="internal"
    )

    target_level = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    course_url = models.TextField(
        blank=True,
        null=True
    )

    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_topics_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_topics_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_topics_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_topic"

    def __str__(self):
        return f"{self.code} - {self.name}"

# LEARNING SCHEDULE
class LearningSchedule(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    topic_id = models.ForeignKey(
        LearningTopic,
        on_delete=models.PROTECT,
        related_name="scheduled"
    )

    name = models.CharField(
        max_length=150
    )

    training_type = models.CharField(
        max_length=20
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    schedule_display = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    location_or_link = models.TextField(
        blank=True,
        null=True
    )

    training_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    quota = models.IntegerField(
        default=0
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_schedules_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_schedules_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_schedules_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_schedule"

    def __str__(self):
        return f"{self.code} - {self.name}"

# LEARNING ENROLLMENT
class LearningEnrollment(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    # Sesuaikan "Employee" dengan model Employee
    # yang sudah ada di aplikasi humancapital.
    employee_id = models.ForeignKey(
        "humancapital.Employee",
        on_delete=models.PAROTECT,
        related_name="learning_enrollments"
    )

    training_source = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default="internal"
    )

    priority_year = models.IntegerField(
        default=2026
    )

    schedule_id = models.ForeignKey(
        LearningSchedule,
        on_delete=models.PROTECT,
        related_name="enrollments",
        blank=True,
        null=True
    )

    invitation_status = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        default="not_invited"
    )

    invitation_sent_at = models.DateTimeField(
        blank=True,
        null=True
    )

    external_topic_title = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    provider_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    duration_text = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    date_mode = models.CharField(
        max_length=10,
        default="single"
    )

    start_date = models.DateField(
        blank=True,
        null=True
    )

    end_date = models.DateField(
        blank=True,
        null=True
    )

    proof_type = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    approval_status = models.CharField(
        max_length=20,
        default="approved"
    )

    approved_by_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_enrollments_approved",
        blank=True,
        null=True
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    remark = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_enrollments_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_enrollments_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_enrollments_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_enrollment"

    def __str__(self):
        return self.code

# LEARNING COMPLETION
class LearningCompletion(models.Model):

    enrollment_id = models.ForeignKey(
        LearningEnrollment,
        on_delete=models.CASCADE,
        related_name="completions"
    )

    attendance_status = models.CharField(
        max_length=20,
        default="present"
    )

    pre_test_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    post_test_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    grade_status = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    is_passed = models.BooleanField(
        default=False
    )

    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    certificate_url = models.TextField(
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    feedback_rating = models.IntegerField(
        blank=True,
        null=True
    )

    feedback_notes = models.TextField(
        blank=True,
        null=True
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_completions_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_completions_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_completions_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_completion"

    def __str__(self):
        return f"Completion #{self.pk} - {self.enrollment}"

# LEARNING FILE
class LearningFile(models.Model):

    external_training_id = models.ForeignKey(
        LearningEnrollment,
        on_delete=models.CASCADE,
        related_name="files"
    )

    file_name = models.CharField(
        max_length=255
    )

    file_path = models.TextField(
        blank=True,
        null=True
    )

    file_size_bytes = models.BigIntegerField(
        blank=True,
        null=True
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    drive_url = models.TextField(
        blank=True,
        null=True
    )

    status = models.IntegerField(
        default=1
    )

    deleted = models.BooleanField(
        default=False
    )

    cat_timestamp = models.DateTimeField(
        auto_now_add=True
    )

    cby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_files_created"
    )

    uat_timestamp = models.DateTimeField(
        auto_now=True
    )

    uby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_files_updated"
    )

    dat_timestamp = models.DateTimeField(
        blank=True,
        null=True
    )

    dby_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learning_files_deleted",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "humancapital_learning_file"

    def __str__(self):
        return self.file_name