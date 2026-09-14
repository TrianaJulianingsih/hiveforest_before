from django.db import models, transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.base.models.people import Person, Gender
from apps.base.mixins import SystemLogModelMixin


class Employee(SystemLogModelMixin, GenericAbstract):
    EMPLOYMENT_REGULAR = 'regular'
    EMPLOYMENT_PROBATION = 'probation'
    EMPLOYMENT_STATUS_CHOICES = (
        (EMPLOYMENT_REGULAR, _('Regular')),
        (EMPLOYMENT_PROBATION, _('Probation')),
    )

    person = models.OneToOneField(Person, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Person')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee',
        verbose_name='User',
        db_column='user_id'
    )
    # Email field: prefer explicit email on Employee to drive automatic User creation.
    # Kept nullable for migration safety; application enforces presence on create.
    email = models.EmailField(max_length=254, null=True, blank=True, verbose_name='Email')
    code = models.CharField(max_length=10, null=False, default="", verbose_name='Code')
    hired = models.DateField(null=True, blank=True, verbose_name= 'Hired')
    terminated = models.DateField(null=True, blank=True, verbose_name= 'Terminated')
    employment_status = models.CharField(
        max_length=12,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default=EMPLOYMENT_REGULAR,
        verbose_name=_('Employment status'),
    )

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ('name',)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure name derived from person if not provided
        if not self.name and self.person:
            self.name = f"{self.person.name}"

        # If creating new Employee, enforce email and auto-create User+Profile inside a transaction
        is_create = self.pk is None
        if is_create:
            if not getattr(self, 'email', None):
                raise ValueError('Email is required when creating Employee')
            with transaction.atomic():
                super().save(*args, **kwargs)
                # create_user_account will set the user field without triggering recursive save
                self.create_user_account(send_email=True)
        else:
            super().save(*args, **kwargs)

    def create_user_account(self, email=None, password="h!v3f0r35t", send_email=True):
        """Create linked User and rely on existing UserProfile signal.

        This method will:
        - validate email
        - create User with username=email
        - set password via set_password
        - link `user` to created user
        - update user.userprofile.person to this.employee.person
        - schedule notification email to be sent after commit

        Raises exceptions on failure to allow caller to rollback transaction.
        """
        # Prefer explicit email provided or Employee.email, fallback to EmailContact
        if not email:
            email = getattr(self, 'email', None)
        if not email and self.person:
            from apps.base.models.contacts import EmailContact
            emails = EmailContact.objects.filter(person=self.person)
            email = emails.first().email if emails.exists() else None

        if not email:
            raise ValueError("Employee must have an email to create user account")

        User = get_user_model()
        if User.objects.filter(username=email).exists():
            raise ValueError("User with this username/email already exists")

        with transaction.atomic():
            user = User.objects.create(username=email, email=email)
            user.set_password(password)
            user.save()

            # link without invoking Employee.save() to avoid recursion
            if self.pk:
                type(self).objects.filter(pk=self.pk).update(user=user)
            else:
                # if not saved yet, assign and let caller persist
                self.user = user

            # ensure UserProfile.person is set (post_save signal creates profile)
            from apps.base.models.userprofiles import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user, defaults={"person": self.person or None})
            if not created and self.person:
                profile.person = self.person
                profile.save()

            # send email notification after successful commit
            if send_email:
                def _send():
                    # Build absolute login URL using configured site/domain settings
                    site_domain = getattr(settings, 'SITE_DOMAIN', None)
                    if not site_domain:
                        try:
                            site_domain = settings.ALLOWED_HOSTS[0]
                        except Exception:
                            site_domain = 'localhost:8000'
                    scheme = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
                    login_path = getattr(settings, 'LOGIN_URL', '/login/')
                    login_url = f"{scheme}://{site_domain}{login_path}"
                    subject = 'Account Created'
                    message = f"Hello {self.name or ''}\n\nUsername : {email}\nPassword : {password}\nLogin : {login_url}\n"
                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                    except Exception:
                        import logging
                        logging.exception('Failed to send account creation email to %s', email)

                transaction.on_commit(_send)

            return user


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeeTitle                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain title of employee like Staff, Manager    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\models\employee_models.py         ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: May/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝                
class EmployeeTitle(SystemLogModelMixin, GenericAbstract):
    code = models.CharField(max_length=10, null=False, default='', verbose_name='Code')
    initial = models.CharField(max_length=15, null=True, blank=True, default="", verbose_name='Initial')
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name='Shortname')

    class Meta:
        verbose_name = 'Employee Title'
        verbose_name_plural = 'Employee Titles'
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    # May/23-2025
    def __str__(self):
        return self.name
