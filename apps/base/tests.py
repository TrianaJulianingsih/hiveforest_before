import json
import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from django.http import JsonResponse
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from apps.base.models.system_log import SystemLog, LogAction, LogStatus
from apps.base.services.system_log_service import SystemLogService, sanitize_payload
from apps.base.mixins import SystemLogMixin, SystemLogModelMixin
from apps.base.models.locations import Island
from apps.base.utils.authentication_utils import get_client_ip, parse_user_agent

User = get_user_model()

# Dynamically inject SystemLogModelMixin to Island for testing CRUD hook triggers
if SystemLogModelMixin not in Island.__bases__:
    Island.__bases__ = (SystemLogModelMixin,) + Island.__bases__


@override_settings(SYSTEM_LOG_SYNC=True)
class SystemLogTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_login(self.user)

    def test_1_login_success(self):
        SystemLog.objects.all().delete()
        self.client.logout()
        # Post to the login URL (assuming default django URL name is 'login')
        self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password123'})
        logs = SystemLog.objects.filter(action=LogAction.LOGIN, status=LogStatus.SUCCESS)
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().user.username, "testuser")

    def test_2_login_failure(self):
        SystemLog.objects.all().delete()
        # Fire the signal directly for robust test environment compatibility
        from django.contrib.auth.signals import user_login_failed
        user_login_failed.send(
            sender=self.__class__,
            credentials={'username': 'testuser'},
            request=RequestFactory().post('/login/')
        )
        logs = SystemLog.objects.filter(action=LogAction.LOGIN, status=LogStatus.ERROR)
        self.assertTrue(logs.exists())
        self.assertIn("testuser", logs.first().description)

    def test_3_create_data(self):
        SystemLog.objects.all().delete()
        island = Island.objects.create(name="Sumatra", slug="sumatra-test-crud")
        logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="Island")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().object_id, str(island.pk))
        self.assertEqual(logs.first().new_data["name"], "Sumatra")

    def test_4_update_data_diff(self):
        island = Island.objects.create(name="Java", slug="java-test-crud")
        SystemLog.objects.all().delete()
        island.name = "West Java"
        island.save()
        logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="Island")
        self.assertTrue(logs.exists())
        log = logs.first()
        changes = log.metadata.get("changes", {})
        self.assertIn("name", changes)
        self.assertEqual(changes["name"]["old"], "Java")
        self.assertEqual(changes["name"]["new"], "West Java")

    def test_5_delete_data(self):
        island = Island.objects.create(name="Bali", slug="bali-test-crud")
        SystemLog.objects.all().delete()
        island.delete()
        logs = SystemLog.objects.filter(action=LogAction.DELETE, object_type="Island")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().old_data["name"], "Bali")

    def test_6_api_success(self):
        from apps.base.middleware import SystemLogMiddleware
        factory = RequestFactory()
        request = factory.post('/api/dummy/', data=json.dumps({"name": "Valid Data"}), content_type='application/json')
        request.user = self.user
        request.resolver_match = type('Match', (), {'view_name': 'dummy_api_view'})()

        SystemLog.objects.all().delete()

        def dummy_view(req):
            return JsonResponse({"status": "created"}, status=201)

        middleware = SystemLogMiddleware(dummy_view)
        response = middleware(request)

        logs = SystemLog.objects.filter(action=LogAction.API_REQUEST)
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.response_code, 201)
        self.assertEqual(log.status, LogStatus.SUCCESS)
        self.assertIn("Valid Data", log.new_data.get("name"))

    def test_7_api_error(self):
        from apps.base.middleware import SystemLogMiddleware
        factory = RequestFactory()
        request = factory.post('/api/dummy/', data=json.dumps({"name": ""}), content_type='application/json')
        request.user = self.user
        request.resolver_match = type('Match', (), {'view_name': 'dummy_api_view'})()

        SystemLog.objects.all().delete()

        def dummy_view(req):
            return JsonResponse({"error": "Name is required"}, status=400)

        middleware = SystemLogMiddleware(dummy_view)
        response = middleware(request)

        logs = SystemLog.objects.filter(action=LogAction.API_REQUEST, status=LogStatus.ERROR)
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.response_code, 400)
        self.assertIn("Name is required", log.error_message)

    def test_8_exception_logging(self):
        from apps.base.middleware import SystemLogMiddleware
        factory = RequestFactory()
        request = factory.get('/api/critical/')
        request.user = self.user
        request.resolver_match = type('Match', (), {'view_name': 'critical_api_view'})()

        SystemLog.objects.all().delete()

        middleware = SystemLogMiddleware(lambda req: exec('raise ValueError("Unhandled DB error")'))
        try:
            middleware(request)
        except ValueError:
            pass

        middleware.process_exception(request, ValueError("Unhandled DB error"))

        logs = SystemLog.objects.filter(action=LogAction.ERROR, status=LogStatus.ERROR)
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.error_message, "Unhandled DB error")
        self.assertIsNotNone(log.stack_trace)

    def test_9_anonymous_request(self):
        from apps.base.middleware import SystemLogMiddleware
        from django.contrib.auth.models import AnonymousUser
        factory = RequestFactory()
        request = factory.get('/api/public/')
        request.user = AnonymousUser()
        request.resolver_match = type('Match', (), {'view_name': 'public_api_view'})()

        SystemLog.objects.all().delete()

        def dummy_view(req):
            return JsonResponse({"status": "guest"})

        middleware = SystemLogMiddleware(dummy_view)
        middleware(request)

        logs = SystemLog.objects.filter(action=LogAction.API_REQUEST)
        self.assertTrue(logs.exists())
        self.assertIsNone(logs.first().user)

    def test_10_ip_address_detection(self):
        factory = RequestFactory()
        request = factory.get('/api/', HTTP_X_FORWARDED_FOR='198.51.100.42, 203.0.113.195')
        self.assertEqual(get_client_ip(request), '198.51.100.42')

    def test_11_user_agent_detection(self):
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 Version/16.5 Mobile/15E148 Safari/604.1"
        browser, os = parse_user_agent(user_agent)
        self.assertEqual(browser, "Safari")
        self.assertEqual(os, "iOS")

    def test_12_sensitive_data_masking(self):
        sensitive_data = {
            "password": "plain_password",
            "password_confirmation": "plain_password",
            "token": "bearer_token_xyz",
            "nested": {
                "secret_key": "mysecret",
                "normal_field": "visible_value"
            }
        }
        sanitized = sanitize_payload(sensitive_data)
        self.assertEqual(sanitized["password"], "******")
        self.assertEqual(sanitized["password_confirmation"], "******")
        self.assertEqual(sanitized["token"], "******")
        self.assertEqual(sanitized["nested"]["secret_key"], "******")
        self.assertEqual(sanitized["nested"]["normal_field"], "visible_value")

    def test_14_bulk_operation(self):
        SystemLog.objects.all().delete()
        SystemLogService.log_bulk(
            action=LogAction.BULK_UPDATE,
            model=Island,
            affected_count=250,
            module="Locations",
            feature="Island Management"
        )
        logs = SystemLog.objects.filter(action=LogAction.BULK_UPDATE)
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.object_type, "Island")
        self.assertEqual(log.metadata.get("affected_records"), 250)

    def test_15_no_recursive_logging(self):
        # Clear logs
        SystemLog.objects.all().delete()
        
        # Perform action that creates log
        SystemLogService.log(
            action=LogAction.SYSTEM,
            module="RecursiveTest",
            description="System log check"
        )
        self.assertEqual(SystemLog.objects.count(), 1)

    def test_17_admin_changelist_view_logged(self):
        from django.contrib.admin.sites import AdminSite
        from apps.base.admin_base import BaseModelAdmin
        
        site = AdminSite()
        model_admin = BaseModelAdmin(Island, site)
        
        factory = RequestFactory()
        request = factory.get('/admin/base/island/')
        request.user = self.user
        
        SystemLog.objects.all().delete()
        
        try:
            model_admin.changelist_view(request)
        except Exception:
            pass
            
        logs = SystemLog.objects.filter(action=LogAction.READ)
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().module, "Base")
        self.assertEqual(logs.first().feature, "Islands")

    def test_18_bom_model_crud_logged(self):
        from apps.bom.models.freight_models import FreightCost
        
        # Test CREATE
        SystemLog.objects.all().delete()
        freight = FreightCost.objects.create(name="Freight A", freight_type="Air")
        logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="FreightCost")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().new_data["name"], "Freight A")
        
        # Test UPDATE
        SystemLog.objects.all().delete()
        freight.freight_type = "Sea"
        freight.save()
        logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="FreightCost")
        self.assertTrue(logs.exists())
        self.assertIn("freight_type", logs.first().metadata["changes"])

    def test_19_cms_model_crud_logged(self):
        from apps.cms.models.app_managers_models import ApplicationList
        
        # Test CREATE
        SystemLog.objects.all().delete()
        app = ApplicationList.objects.create(name="Application A", code="APP-A", initial="A")
        logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="ApplicationList")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().new_data["name"], "Application A")
        
        # Test UPDATE
        SystemLog.objects.all().delete()
        app.shortname = "App A"
        app.save()
        logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="ApplicationList")
        self.assertTrue(logs.exists())
        self.assertIn("shortname", logs.first().metadata["changes"])



class SystemLogAsyncRollbackTests(TestCase):
    def test_13_and_16_transaction_rollback_safety(self):
        # Disable sync mode so background threading is used during atomic transaction execution
        settings.SYSTEM_LOG_SYNC = False
        SystemLog.objects.all().delete()

        try:
            with transaction.atomic():
                # Perform business logging inside atomic transaction
                SystemLogService.log(
                    action=LogAction.SYSTEM,
                    module="RollbackSafetyTest",
                    description="This entry should survive the rollback of the transaction block."
                )
                # Force failure/abort transaction
                raise RuntimeError("Abort business transaction")
        except RuntimeError:
            pass

        # Give background thread pool executor a fraction of a second to complete DB write
        time.sleep(0.5)

        # The log entry should exist despite transaction aborting
        logs = SystemLog.objects.filter(module="RollbackSafetyTest")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().description, "This entry should survive the rollback of the transaction block.")
