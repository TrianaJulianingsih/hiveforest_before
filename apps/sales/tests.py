from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.sales.models.customer_models import Customer, CustomerType, CustomerGroup, Outlet, OutletGroup, Satker
from apps.sales.models.product_models import Product, ProductCategory, ProductGroup, ProductPackage, ProductSubgroup
from apps.sales.models.sales_models import RepOffice, SalesType, SellingOut, AnnualTarget, CycleTarget, ECatalog
from apps.sales.models.territory_models import SalesTeam, SalesRegion, RegionProvince, SalesArea, AreaRegency, KAMArea
from apps.sales.forms.products_forms import ProductsForm
from apps.base.models.system_log import SystemLog, LogAction

User = get_user_model()


@override_settings(SYSTEM_LOG_SYNC=True)
class SalesModelTests(TestCase):
    def setUp(self):
        super().setUp()
        self.cust_type = CustomerType.objects.create(
            name="Hospital",
            code="01",
            slug="hosp-type",
        )

    def test_customer_creation_and_logging(self):
        SystemLog.objects.all().delete()
        customer = Customer.objects.create(
            name="General Hospital",
            custtype=self.cust_type,
            slug="gen-hospital",
        )
        self.assertEqual(customer.name, "General Hospital")
        self.assertTrue(customer.code.startswith("01"))

        # Verify CREATE log was captured by SystemLogModelMixin
        create_log = SystemLog.objects.filter(action=LogAction.CREATE, object_type="Customer").first()
        self.assertIsNotNone(create_log)
        self.assertEqual(create_log.status, "SUCCESS")

        # Test UPDATE logging
        SystemLog.objects.all().delete()
        customer.name = "General Hospital Updated"
        customer.save()
        update_log = SystemLog.objects.filter(action=LogAction.UPDATE, object_type="Customer").first()
        self.assertIsNotNone(update_log)

        # Test DELETE logging
        SystemLog.objects.all().delete()
        customer.delete()
        delete_log = SystemLog.objects.filter(action=LogAction.DELETE, object_type="Customer").first()
        self.assertIsNotNone(delete_log)

    def test_product_creation_and_logging(self):
        SystemLog.objects.all().delete()
        category = ProductCategory.objects.create(
            name="Ethical",
            code="ETH",
            slug="ethical-cat",
        )
        product = Product.objects.create(
            name="Paracetamol 500mg",
            code="PRD001",
            category=category,
            slug="paracetamol-500",
        )
        self.assertEqual(product.name, "Paracetamol 500mg")
        self.assertEqual(product.code, "PRD001")

        # Verify CREATE log
        log_entry = SystemLog.objects.filter(action=LogAction.CREATE, object_type="Product").first()
        self.assertIsNotNone(log_entry)

    def test_territory_models_creation(self):
        SystemLog.objects.all().delete()
        team = SalesTeam.objects.create(
            name="Team Alpha",
            code="TM-A",
            slug="team-alpha",
        )
        self.assertEqual(team.name, "Team Alpha")

        region = SalesRegion.objects.create(
            name="Region West",
            code="REG-W",
            shortname="West Region",
            slug="reg-west",
        )
        self.assertEqual(region.name, "Region West")

        log_count = SystemLog.objects.filter(action=LogAction.CREATE).count()
        self.assertGreaterEqual(log_count, 2)


@override_settings(SYSTEM_LOG_SYNC=True)
class SalesViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="salesuser",
            password="salespassword",
            is_staff=True,
            is_superuser=True,
        )
        from apps.base.user_models import ForcePasswordStatus
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

    def test_dashboard_views_redirect_anonymous(self):
        views = [
            "sales:sales_dashboard",
            "sales:ecatalog_dashboard",
            "sales:iqvia_itma_dashboard",
        ]
        for view_name in views:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 302)

    def test_dashboard_views_authenticated_and_logged(self):
        self.client.force_login(self.user)
        views = [
            ("sales:sales_dashboard", "Sales Dashboard"),
            ("sales:ecatalog_dashboard", "E-Catalog Dashboard"),
            ("sales:iqvia_itma_dashboard", "IQVIA ITMA Dashboard"),
        ]
        for view_name, feature_name in views:
            SystemLog.objects.all().delete()
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)

            # Check SystemLog entry
            log = SystemLog.objects.filter(
                action=LogAction.READ,
                module="Sales",
                feature=feature_name,
            ).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.status, "SUCCESS")

    def test_data_views_logging(self):
        self.client.force_login(self.user)
        SystemLog.objects.all().delete()
        response = self.client.get(reverse("sales:outlet_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.READ,
                module="Sales",
                feature="Outlet List",
            ).exists()
        )

        SystemLog.objects.all().delete()
        response = self.client.get(reverse("sales:distributor_data"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.READ,
                module="Sales",
                feature="Distributor Data API",
            ).exists()
        )

    def test_territory_matrix_view_logging(self):
        self.client.force_login(self.user)
        SystemLog.objects.all().delete()
        response = self.client.get(reverse("sales:region_matrix"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.READ,
                module="Sales",
                feature="Region Province Matrix",
            ).exists()
        )


@override_settings(SYSTEM_LOG_SYNC=True)
class SalesFormTests(TestCase):
    def test_products_form_valid(self):
        data = {
            "name": "Amoxicillin 500mg",
            "code": "AMX500",
            "initial": "AMX",
            "shortname": "Amox",
            "slug": "amoxicillin-500",
        }
        form = ProductsForm(data=data)
        self.assertTrue(form.is_valid())
