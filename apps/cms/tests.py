from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cms.models.menu_system_models import MenuItem
from apps.base.models.system_log import SystemLog, LogAction

User = get_user_model()

@override_settings(SYSTEM_LOG_SYNC=True)
class CMSViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="cmsuser", password="cmspassword")
        from apps.base.user_models import ForcePasswordStatus
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

        # Create dummy menu item
        self.menu_item = MenuItem.objects.create(
            name="Test Dashboard Menu",
            code="test_menu",
            iframe_url="https://example.com/iframe",
            slug="test-dashboard-menu"
        )

    def test_dashboard_view_redirect_when_not_logged_in(self):
        response = self.client.get(reverse("cms:dashboard_views"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_view_without_menu_param(self):
        self.client.force_login(self.user)
        SystemLog.objects.all().delete()
        response = self.client.get(reverse("cms:dashboard_views"))
        self.assertEqual(response.status_code, 200)

        # Verify log capture
        logs = SystemLog.objects.filter(action=LogAction.READ, module="CMS")
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.feature, "CMS Dashboard")
        self.assertEqual(log.status, "SUCCESS")

    def test_dashboard_view_with_menu_param(self):
        self.client.force_login(self.user)
        SystemLog.objects.all().delete()
        response = self.client.get(reverse("cms:dashboard_views") + "?menu=test_menu")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["iframe_url"], "https://example.com/iframe")

        # Verify log capture
        logs = SystemLog.objects.filter(action=LogAction.READ, module="CMS")
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.feature, "Dashboard: Test Dashboard Menu")
        self.assertEqual(log.status, "SUCCESS")
