from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime
from apps.base.models.system_log import SystemLog, LogAction, LogStatus
from apps.base.models.people import Person, Gender
from apps.humancapital.models import (
    Business, Employee, EmployeeTitle, Organization, OrganizationType, Position, Assignment
)

@override_settings(SYSTEM_LOG_SYNC=True)
class HumanCapitalSystemLogTests(TestCase):
    def setUp(self):
        super().setUp()
        SystemLog.objects.all().delete()
        
        # Setup users
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@test.com",
            password="staffpassword",
            is_staff=True
        )

        # Bypass forced password change middleware
        status = self.staff_user.forcepasswordstatus
        status.must_change_password = False
        status.last_reset_at = timezone.now()
        status.save()

        # Create basic pre-requisites
        self.gender = Gender.objects.create(name="Male", code="M")
        self.title = EmployeeTitle.objects.create(name="Staff", code="STF")
        self.org_type = OrganizationType.objects.create(name="Division", code="DIV")
        self.org = Organization.objects.create(name="IT Division", code="IT", type=self.org_type)
        self.position = Position.objects.create(name="Developer", code="DEV", title=self.title, organization=self.org)
        self.person = Person.objects.create(first_name="John", last_name="Doe", name="John Doe", gender=self.gender)
        self.employee = Employee.objects.create(person=self.person, code="EMP001", name="John Doe")

    def test_model_crud_logging(self):
        # Clear logs from setup objects creation
        SystemLog.objects.all().delete()

        # 1. Test creation logs
        biz = Business.objects.create(
            code="BIZ01",
            name="Otsuka Business",
            effective=timezone.now().date()
        )
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.CREATE,
            module="Humancapital",
            feature="Business"
        ).exists())

        # 2. Test update logs
        SystemLog.objects.all().delete()
        biz.name = "Otsuka Business Group"
        biz.save()
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.UPDATE,
            module="Humancapital",
            feature="Business"
        ).exists())

        # 3. Test delete logs
        SystemLog.objects.all().delete()
        biz.delete()
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.DELETE,
            module="Humancapital",
            feature="Business"
        ).exists())

    def test_view_access_logging(self):
        self.client.force_login(self.staff_user)

        # 1. Test landing page
        SystemLog.objects.all().delete()
        response = self.client.get(reverse('humancapital:hcd-landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.READ,
            module="Human Capital",
            feature="Human Capital Landing Page"
        ).exists())

        # 2. Test organogram page
        SystemLog.objects.all().delete()
        response = self.client.get(reverse('humancapital:organogram'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.READ,
            module="Human Capital",
            feature="Organogram View"
        ).exists())

        # 3. Test list view
        SystemLog.objects.all().delete()
        response = self.client.get(reverse('humancapital:employee-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.READ,
            module="Human Capital",
            feature="Employee List"
        ).exists())

    def test_custom_actions_logging(self):
        self.client.force_login(self.staff_user)

        # 1. Test change_status toggle logging
        SystemLog.objects.all().delete()
        response = self.client.post(reverse('humancapital:employee-change-status', kwargs={'pk': self.employee.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.UPDATE,
            module="Human Capital",
            feature="Employee Status Toggle"
        ).exists())

        # 2. Test quick_add organization logging
        SystemLog.objects.all().delete()
        payload = {
            'name': 'New Org',
            'code': 'NORG',
            'type': self.org_type.id,
            'status': 1
        }
        response = self.client.post(reverse('humancapital:organization-quick-add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.CREATE,
            module="Human Capital",
            feature="Organization Quick Add"
        ).exists())
