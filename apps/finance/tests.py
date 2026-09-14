from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from apps.finance.models.products_models import ItemPrice
from apps.finance.models.receivable_models import ARBalance, ARCollection
from apps.base.models.system_log import SystemLog, LogAction, LogStatus
from unittest.mock import patch

@override_settings(SYSTEM_LOG_SYNC=True)
class FinanceSystemLogTests(TestCase):
    def setUp(self):
        super().setUp()
        SystemLog.objects.all().delete()
        
        # Setup users
        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            email="admin@test.com",
            password="adminpassword"
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@test.com",
            password="staffpassword",
            is_staff=True
        )

        # Bypass forced password change middleware
        for user in [self.admin_user, self.staff_user]:
            status = user.forcepasswordstatus
            status.must_change_password = False
            status.last_reset_at = timezone.now()
            status.save()

    def test_item_price_crud_logging(self):
        # 1. Test Create
        item_price = ItemPrice.objects.create(
            code="TESTCODE",
            name="Test Price Item",
            hna=100.00,
            hjp=120.00,
            effective=timezone.now().date(),
            status=1,
            slug="test-price-item"
        )
        create_logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="ItemPrice")
        self.assertTrue(create_logs.exists())

        # 2. Test Update
        SystemLog.objects.all().delete()
        item_price.hna = 110.00
        item_price.save()
        update_logs = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="ItemPrice")
        self.assertTrue(update_logs.exists())

        # 3. Test Delete
        SystemLog.objects.all().delete()
        item_price.delete()
        delete_logs = SystemLog.objects.filter(action=LogAction.DELETE, object_type="ItemPrice")
        self.assertTrue(delete_logs.exists())

    def test_ar_balance_crud_logging(self):
        balance = ARBalance.objects.create(
            name="Test Balance",
            trx_number="INV-001",
            amount=500.00,
            balance=500.00,
            status=1
        )
        create_logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="ARBalance")
        self.assertTrue(create_logs.exists())

    def test_ar_collection_crud_logging(self):
        collection = ARCollection.objects.create(
            name="Test Collection",
            cabang="Jakarta",
            nomor_faktur="INV-001",
            collect_amount=500.00,
            line_number=1,
            status=1
        )
        create_logs = SystemLog.objects.filter(action=LogAction.CREATE, object_type="ARCollection")
        self.assertTrue(create_logs.exists())

    @patch('apps.finance.views.sync_views.call_command')
    def test_sync_views_logging(self, mock_call_command):
        # Log in as staff using force_login
        self.client.force_login(self.staff_user)

        # 1. Test sync_arbalance success logging
        response = self.client.post(reverse('finance:sync_arbalance'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.SYSTEM, 
            module="Finance", 
            feature="AR Balance Sync",
            status=LogStatus.SUCCESS
        ).exists())

        # 2. Test sync_arcollection success logging
        SystemLog.objects.all().delete()
        response = self.client.post(reverse('finance:sync_arcollection'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.SYSTEM, 
            module="Finance", 
            feature="AR Collection Sync",
            status=LogStatus.SUCCESS
        ).exists())

        # 3. Test sync_arbalance failure logging
        SystemLog.objects.all().delete()
        mock_call_command.side_effect = Exception("Mocked execution failure")
        response = self.client.post(reverse('finance:sync_arbalance'))
        self.assertEqual(response.status_code, 500)
        self.assertTrue(SystemLog.objects.filter(
            action=LogAction.ERROR, 
            module="Finance", 
            feature="AR Balance Sync",
            status=LogStatus.ERROR
        ).exists())
