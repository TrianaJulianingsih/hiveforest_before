from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.base.models.people import Person
from apps.crm.models.hcps_models import Doctor
from apps.crm.models.hospital_models import Hospital
from apps.sales.models.customer_models import Customer

User = get_user_model()

@override_settings(SYSTEM_LOG_SYNC=True)
class CRMModelTests(TestCase):
    def setUp(self):
        super().setUp()
        self.person = Person.objects.create(
            first_name="Jane",
            last_name="Doe",
            slug="jane-doe"
        )

    def test_doctor_creation(self):
        doctor = Doctor.objects.create(
            person=self.person,
            name="Dr. Jane Doe",
            license="LIC123",
            slug="dr-jane-doe"
        )
        self.assertEqual(doctor.name, "Dr. Jane Doe")
        self.assertEqual(doctor.license, "LIC123")
        self.assertTrue(doctor.code.startswith("Jane Doe-LIC123"))

    def test_hospital_creation_without_customer(self):
        hospital = Hospital.objects.create(
            name="Central Hospital",
            code="HOSP01",
            slug="central-hospital"
        )
        self.assertEqual(hospital.code, "HOSP01-Central Hospital")

    def test_hospital_creation_with_customer(self):
        customer = Customer.objects.create(
            name="Cust01",
            code="C01",
            slug="cust-01"
        )
        hospital = Hospital.objects.create(
            name="North Hospital",
            code="HOSP02",
            customer=customer,
            slug="north-hospital"
        )
        self.assertEqual(hospital.code, f"HOSP02-North Hospital-{customer.id}")

    def test_model_crud_logging(self):
        from apps.base.models.system_log import SystemLog, LogAction
        
        SystemLog.objects.all().delete()
        
        # Test Create
        hospital = Hospital.objects.create(
            name="Log Test Hospital",
            code="LHOSP01",
            slug="log-test-hospital"
        )
        self.assertTrue(SystemLog.objects.filter(action=LogAction.CREATE, object_type="Hospital").exists())
        
        # Test Update
        SystemLog.objects.all().delete()
        hospital.name = "Updated Log Test Hospital"
        hospital.save()
        self.assertTrue(SystemLog.objects.filter(action=LogAction.UPDATE, object_type="Hospital").exists())
        
        # Test Delete
        SystemLog.objects.all().delete()
        hospital.delete()
        self.assertTrue(SystemLog.objects.filter(action=LogAction.DELETE, object_type="Hospital").exists())


@override_settings(SYSTEM_LOG_SYNC=True)
class CRMViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="crmuser", password="crmpassword")
        from apps.base.user_models import ForcePasswordStatus
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

    def test_dashboard_views_redirect_when_not_logged_in(self):
        views = ['crm:dash_hospital', 'crm:dash_doctor', 'crm:dash_kamactivity']
        for view in views:
            response = self.client.get(reverse(view))
            self.assertEqual(response.status_code, 302) # Redirect to login page

    def test_dashboard_views_accessible_when_logged_in(self):
        from apps.base.models.system_log import SystemLog, LogAction
        self.client.force_login(self.user)
        views = ['crm:dash_hospital', 'crm:dash_doctor', 'crm:dash_kamactivity']
        for view in views:
            SystemLog.objects.all().delete()
            response = self.client.get(reverse(view))
            if response.status_code == 302:
                raise AssertionError(f"Redirected to {response.url}")
            self.assertEqual(response.status_code, 200)
            
            # Verify system log entry was created
            logs = SystemLog.objects.filter(action=LogAction.READ, module="CRM")
            self.assertEqual(logs.count(), 1)
            log = logs.first()
            self.assertEqual(log.status, "SUCCESS")


