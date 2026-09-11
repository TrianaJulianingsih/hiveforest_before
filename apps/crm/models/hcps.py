import calendar
import datetime

from django.db import models
from apps.base.models.people import Person
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.utils.text import slugify

class Doctor(GenericAbstract):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Person')
    code = models.CharField(max_length=255, unique=True, blank=True, verbose_name="Code")
    prefix = models.CharField(max_length=30, null=True, blank=True, verbose_name="Prefix")
    suffix = models.CharField(max_length=30, null=True, blank=True, verbose_name="Suffix")
    license = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="License")
    start_year = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Start Year")
    start_month = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Start Month")
    private_practice = models.BooleanField(null=True, blank=True, verbose_name="Private Practice")
    source_id = models.CharField(max_length=255, unique=True, blank=True, verbose_name="Source ID")
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True, null=True, default='profile_pictures/default-user.png')

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        indexes = [
            # Matches nondeleted_objects.order_by("name") exactly (the HCP list's
            # main query) - without this, Postgres does a parallel sequential
            # scan across all ~280k rows plus a sort just to return 10 rows,
            # which measured ~0.5s of a ~0.85s full page render.
            models.Index(
                fields=["name"],
                name="crm_doctor_active_name_idx",
                condition=models.Q(dat__isnull=True),
            ),
            # Matches the analytics dashboard's active/inactive stat-card counts
            # (doctors.filter(status=1).count() / status=0) - without this,
            # Postgres full-scans all ~280k rows for each count (~130ms + 49ms).
            models.Index(
                fields=["status"],
                name="crm_doctor_active_status_idx",
                condition=models.Q(dat__isnull=True),
            ),
        ]

    def save(self, *args, **kwargs):
        parts = [self.person.name, self.license]
        self.code = "-".join(filter(None, parts))  # Join non-empty parts

        base_slug = slugify(self.code)
        counter = 1
        while self.__class__.objects.filter(slug=base_slug).exclude(pk=self.pk).exists():
            base_slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = base_slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def start_period(self):
        if self.start_year and self.start_month and 1 <= self.start_month <= 12:
            return f"{calendar.month_abbr[self.start_month]} {self.start_year}"
        return "-"

    @property
    def photo_url(self):
        name = self.profile_picture.name if self.profile_picture else ""
        if not name or name == "profile_pictures/default-user.png":
            return None
        if name.startswith("http://") or name.startswith("https://"):
            return name
        return self.profile_picture.url

    @property
    def specialities_display(self):
        names = [
            s.speciality_desc for s in self.doctorspeciality_set.all() if s.speciality_desc
        ]
        return ", ".join(names) if names else "-"

    @property
    def experience_display(self):
        if not (self.start_year and self.start_month and 1 <= self.start_month <= 12):
            return "-"
        today = datetime.date.today()
        start = datetime.date(self.start_year, self.start_month, 1)
        months = (today.year - start.year) * 12 + (today.month - start.month)
        if months < 0:
            return "-"
        years, rem_months = divmod(months, 12)
        parts = []
        if years:
            parts.append(f"{years} Year{'s' if years != 1 else ''}")
        if rem_months or not years:
            parts.append(f"{rem_months} Month{'s' if rem_months != 1 else ''}")
        return " ".join(parts)

class DoctorEducation(GenericAbstract):
    doctor = models.ForeignKey('crm.Doctor', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Doctor")
    institution = models.CharField(max_length=100, null=True, blank=True, verbose_name="Institution")
    completed_year = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Completed Year")
    completed_month = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Completed Month")
    source_id = models.CharField(max_length=255, blank=True, verbose_name="Source ID")

    @property
    def completed_period(self):
        if self.completed_year and self.completed_month and 1 <= self.completed_month <= 12:
            return f"{calendar.month_name[self.completed_month]} {self.completed_year}"
        return "-"

    class Meta:
        verbose_name = "Education"
        verbose_name_plural = "Educations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    
    def __str__(self):
        return self.institution

class DoctorPlace(GenericAbstract):
    doctor = models.ForeignKey('crm.Doctor', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Doctor")
    province_desc = models.CharField(max_length=100, null=True, blank=True, verbose_name="Province Desc")
    city_desc = models.CharField(max_length=100, null=True, blank=True, verbose_name="City Desc")
    place_desc = models.CharField(max_length=100, null=True, blank=True, verbose_name="Place Desc")
    province = models.ForeignKey('base.Province', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Province")
    city = models.ForeignKey('base.Regency', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="City")
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Customer")
    source_id = models.CharField(max_length=255, blank=True, verbose_name="Source ID")

    class Meta:
        verbose_name = "Place of Practice"
        verbose_name_plural = "Places of Practice"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    
    def __str__(self):
        return self.place_desc

class DoctorSpeciality(GenericAbstract):
    doctor = models.ForeignKey('crm.Doctor', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Doctor")
    speciality_desc = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Speciality Desc")
    speciality = models.ForeignKey('crm.Specialization', on_delete=models.SET_NULL, null=True, blank=True, verbose_name= 'Speciality')
    source_id = models.CharField(max_length=255, blank=True, verbose_name="Source ID")

    class Meta:
        verbose_name = "Doctor Speciality"
        verbose_name_plural = "Doctor Specialities"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.speciality_desc
    
class Specialization(GenericAbstract):
    code = models.CharField(max_length=20, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    title = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name="Title")

    class Meta:
        verbose_name = "Specialization"
        verbose_name_plural = "Specializations"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]