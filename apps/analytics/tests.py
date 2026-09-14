from django.test import TestCase, override_settings
from apps.analytics.models.iqvia_models import IQV_Company, IQV_Product
from apps.analytics.models.sellingout_models import SellingOutCY
from apps.base.models.system_log import SystemLog, LogAction
from django.utils import timezone

@override_settings(SYSTEM_LOG_SYNC=True)
class AnalyticsModelLoggingTests(TestCase):
    def setUp(self):
        super().setUp()
        SystemLog.objects.all().delete()

    def test_company_and_product_crud_logging(self):
        # 1. Test Create logging
        company = IQV_Company.objects.create(
            name="IQVIA Test Company",
            code="COMP01",
            slug="iqvia-test-company"
        )
        product = IQV_Product.objects.create(
            name="IQVIA Test Product",
            code="PROD01",
            company=company,
            slug="iqvia-test-product"
        )

        create_logs = SystemLog.objects.filter(action=LogAction.CREATE)
        # Verify both objects created logs
        self.assertTrue(create_logs.filter(object_type="IQV_Company").exists())
        self.assertTrue(create_logs.filter(object_type="IQV_Product").exists())

        # 2. Test Update logging
        SystemLog.objects.all().delete()
        product.name = "Updated IQVIA Test Product"
        product.save()

        update_logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="IQV_Product")
        self.assertTrue(update_logs.exists())
        log = update_logs.first()
        changes = log.metadata.get("changes", {})
        self.assertIn("name", changes)
        self.assertEqual(changes["name"]["old"], "IQVIA Test Product")
        self.assertEqual(changes["name"]["new"], "Updated IQVIA Test Product")

        # 3. Test Delete logging
        SystemLog.objects.all().delete()
        product.delete()

        delete_logs = SystemLog.objects.filter(action=LogAction.DELETE, object_type="IQV_Product")
        self.assertTrue(delete_logs.exists())

    def test_sellingout_crud_logging(self):
        # Test Create
        so_record = SellingOutCY.objects.create(
            invoice_date=timezone.now().date(),
            so=123,
            price=1500.00,
            qty=10,
            netvalue=15000.00
        )
        create_logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="SellingOutCY")
        self.assertTrue(create_logs.exists())

        # Test Update
        SystemLog.objects.all().delete()
        so_record.so = 456
        so_record.save()
        update_logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="SellingOutCY")
        self.assertTrue(update_logs.exists())

        # Test Delete
        SystemLog.objects.all().delete()
        so_record.delete()
        delete_logs = SystemLog.objects.filter(action=LogAction.DELETE, object_type="SellingOutCY")
        self.assertTrue(delete_logs.exists())
