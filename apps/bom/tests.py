from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.base.models.system_log import SystemLog, LogAction

User = get_user_model()

@override_settings(SYSTEM_LOG_SYNC=True)
class BOMViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="bomuser", password="bompassword")
        from apps.base.user_models import ForcePasswordStatus
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

    def test_dashboard_views_redirect_when_not_logged_in(self):
        views = [
            'bom:dash_distribution',
            'bom:dash_stock',
            'bom:branchstock_summary_dashboard',
            'bom:branchstock_summary_user',
        ]
        for view in views:
            response = self.client.get(reverse(view))
            self.assertEqual(response.status_code, 302)

    def test_dashboard_views_accessible_when_logged_in(self):
        self.client.force_login(self.user)
        views = [
            ('bom:dash_distribution', 'Distribution Dashboard'),
            ('bom:dash_stock', 'Stock Dashboard'),
            ('bom:branchstock_summary_dashboard', 'Branch Stock Summary Dashboard'),
            ('bom:branchstock_summary_user', 'Branch Stock Summary User Report'),
            ('bom:freight_cost_dashboard', 'Freight Cost Dashboard'),
            ('bom:dash_freight_cost', 'Freight Cost Dashboard'),
        ]
        for view, feature_name in views:
            SystemLog.objects.all().delete()
            response = self.client.get(reverse(view))
            if response.status_code == 302:
                raise AssertionError(f"Redirected to {response.url}")
            self.assertEqual(response.status_code, 200)

            # Verify log capture
            logs = SystemLog.objects.filter(action=LogAction.READ, module="BOM")
            self.assertEqual(logs.count(), 1)
            log = logs.first()
            self.assertEqual(log.feature, feature_name)
            self.assertEqual(log.status, "SUCCESS")

    def test_freight_cost_dashboard_filters_and_aggregations(self):
        from decimal import Decimal
        from django.utils import timezone
        from apps.bom.models import FreightCost, FreightCostDetail

        self.client.force_login(self.user)

        freight_2025 = FreightCost.objects.create(
            name="FRG-2025-01",
            shipping_date=timezone.datetime(2025, 5, 10).date(),
            burden_type=FreightCost.BURDEN_TYPE_OI,
        )
        FreightCostDetail.objects.create(
            freight=freight_2025,
            item_code="ITM01",
            item_description="Test Item 1",
            from_location="JAKARTA",
            to_location="BANDUNG",
            nama_cab="BANDUNG",
            expedition_name="JNE",
            group_produk="PHARMA",
            qty_freight=Decimal("10.00"),
            total_weight=Decimal("50.00"),
            total_freight=Decimal("100000.00"),
            total_cost=Decimal("120000.00"),
        )

        freight_mup = FreightCost.objects.create(
            name="FRG-2025-02",
            shipping_date=timezone.datetime(2025, 6, 15).date(),
            burden_type=FreightCost.BURDEN_TYPE_MUP,
        )
        FreightCostDetail.objects.create(
            freight=freight_mup,
            item_code="ITM02",
            item_description="Test Item 2",
            from_location="SURABAYA",
            to_location="BALI",
            nama_cab="DENPASAR",
            expedition_name="TIKI",
            group_produk="CONSUMER",
            qty_freight=Decimal("20.00"),
            total_weight=Decimal("100.00"),
            total_freight=Decimal("200000.00"),
            total_cost=Decimal("250000.00"),
        )

        # GET dashboard with 2025 filter
        response = self.client.get(reverse('bom:freight_cost_dashboard'), {"year": "2025"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("metrics", response.context)
        self.assertEqual(response.context["metrics"]["total_cost"], Decimal("370000.00"))
        self.assertEqual(response.context["metrics"]["total_weight"], Decimal("150.00"))
        self.assertEqual(response.context["metrics"]["oi_cost"], Decimal("120000.00"))
        self.assertEqual(response.context["metrics"]["mup_cost"], Decimal("250000.00"))

        # GET dashboard with Burden filter
        response_oi = self.client.get(
            reverse('bom:freight_cost_dashboard'),
            {"year": "2025", "burden_type": FreightCost.BURDEN_TYPE_OI}
        )
        self.assertEqual(response_oi.status_code, 200)
        self.assertEqual(response_oi.context["metrics"]["total_cost"], Decimal("120000.00"))
        self.assertEqual(response_oi.context["metrics"]["total_items"], 1)

    def test_seed_freight_cost_menu_and_translations_command(self):
        from django.core.management import call_command
        from apps.cms.models.menu_system_models import MenuItem
        from apps.base.models.translation import TranslationModule, TranslationKey

        call_command("seed_freight_cost_menu_and_translations", force=True)

        # Verify menu item
        menu = MenuItem.objects.filter(code="BO904-DASH").first()
        self.assertIsNotNone(menu)
        self.assertEqual(menu.url, "/bom/freight-cost/freightcost/dashboard/")

        # Verify translations
        module = TranslationModule.objects.filter(code="freight_cost").first()
        self.assertIsNotNone(module)
        key = TranslationKey.objects.filter(module=module, key="dashboard_title").first()
        self.assertIsNotNone(key)

