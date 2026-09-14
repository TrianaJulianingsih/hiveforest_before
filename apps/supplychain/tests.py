from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from decimal import Decimal

from apps.supplychain.models.distributions_models import (
    Distributor,
    BranchType,
    Branch,
    DistributorItemGroup,
    DistributorItem,
    StDistDaily,
    BranchStock,
    OrderStatus,
    OrderType,
)
from apps.supplychain.models.manufacturing_models import (
    StockStatus,
    ManufacturingItemGroup,
    ManufacturingItemSubgroup,
    ManufacturingItem,
    StMfgOts,
)
from apps.supplychain.models.distrib_orders_models import (
    OrderHeader,
    OrderDetail,
    POHeader,
    PODetail,
    DOHeader,
    DODetail,
)
from apps.supplychain.forms.branch_forms import BranchForm
from apps.base.models.system_log import SystemLog, LogAction
from apps.base.models.items import UoM
from apps.base.models.entities import Company
from apps.sales.models.product_models import Product, ProductGroup, ProductSubgroup
from apps.base.user_models import ForcePasswordStatus
from apps.base.models.userprofiles import UserProfile

User = get_user_model()


@override_settings(SYSTEM_LOG_SYNC=True)
class SupplyChainModelSystemLogTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            username="sc_admin",
            email="sc_admin@example.com",
            password="adminpassword123",
        )
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

        self.company = Company.objects.create(name="PT Test Company", code="TC01")
        self.uom = UoM.objects.create(name="Box", code="BOX")
        self.product_group = ProductGroup.objects.create(name="Ethical", code="ETH")
        self.product_subgroup = ProductSubgroup.objects.create(name="Team A", code="TMA", group=self.product_group)
        self.product = Product.objects.create(name="Amoxicillin 500mg", code="AMX500", subgroup=self.product_subgroup)

    def test_distributor_crud_and_system_log(self):
        SystemLog.objects.all().delete()
        # CREATE
        dist = Distributor.objects.create(
            name="Distributor Utama",
            code="DIST01",
            initial="DU",
            company=self.company,
        )
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type="Distributor",
            ).exists()
        )

        # UPDATE
        SystemLog.objects.all().delete()
        dist.name = "Distributor Utama Updated"
        dist.save()
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.UPDATE,
                object_type="Distributor",
            ).exists()
        )

        # DELETE
        SystemLog.objects.all().delete()
        dist.delete()
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.DELETE,
                object_type="Distributor",
            ).exists()
        )

    def test_branch_and_branch_type_crud(self):
        SystemLog.objects.all().delete()
        btype = BranchType.objects.create(name="Main Branch", code="MB01", initial="MB")
        dist = Distributor.objects.create(name="Dist A", code="DA", initial="DA")
        branch = Branch.objects.create(
            name="Branch Jakarta",
            code="JKT01",
            initial="JKT",
            distributor=dist,
            type=btype,
        )
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type="Branch",
            ).exists()
        )

    def test_manufacturing_models_system_log(self):
        SystemLog.objects.all().delete()
        mfg_group = ManufacturingItemGroup.objects.create(name="Tablet", code="TAB", initial="TAB")
        mfg_subgroup = ManufacturingItemSubgroup.objects.create(name="Coated", code="COAT", initial="COAT", group=mfg_group)
        mfg_item = ManufacturingItem.objects.create(
            name="Mfg Paracetamol",
            code="MPAR",
            subgroup=mfg_subgroup,
            owner=self.company,
            product=self.product,
            deliveryuom=self.uom,
            stockuom=self.uom,
        )
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type="Manufacturingitem",
            ).exists() or SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type="ManufacturingItem",
            ).exists()
        )

    def test_order_header_and_detail_crud(self):
        SystemLog.objects.all().delete()
        status_draft = OrderStatus.objects.create(id=1, name="Draft", code="DRAFT", initial="DR")
        dist = Distributor.objects.create(name="Dist B", code="DB", initial="DB")
        ordertype = OrderType.objects.create(name="Regular", code="REG", distributor=dist)
        branch = Branch.objects.create(name="Branch Bandung", code="BDG01", distributor=dist)

        order = OrderHeader.objects.create(
            distributor=dist,
            branch=branch,
            ordertype=ordertype,
            orderno="ORD-2026-001",
            orderdate=date.today(),
            orderdue=date.today(),
            progress=status_draft,
        )
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type__iexact="OrderHeader",
            ).exists()
        )

        itemgroup = DistributorItemGroup.objects.create(name="Group A", code="GA", distributor=dist)
        dist_item = DistributorItem.objects.create(
            name="Dist Paracetamol",
            code="DPAR",
            distributor=dist,
            product=self.product,
            group=itemgroup,
            salesuom=self.uom,
            stockuom=self.uom,
            orderuom=self.uom,
        )

        SystemLog.objects.all().delete()
        detail = OrderDetail.objects.create(
            order=order,
            orderline="001",
            itemgroup=itemgroup,
            item=dist_item,
            qty=10,
            uom=self.uom,
            price=Decimal("15000.00"),
            amount=Decimal("150000.00"),
            progress=status_draft,
        )
        self.assertTrue(
            SystemLog.objects.filter(
                action=LogAction.CREATE,
                object_type__iexact="OrderDetail",
            ).exists()
        )


@override_settings(SYSTEM_LOG_SYNC=True)
class SupplyChainViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = User.objects.create_user(
            username="sc_staff",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

        UserProfile.objects.get_or_create(user=self.user, defaults={"language": "en"})
        self.client.force_login(self.user)

        self.status_draft = OrderStatus.objects.create(id=1, name="Draft", code="DRAFT")
        self.dist = Distributor.objects.create(name="Dist View", code="DV", initial="DV")
        self.branch = Branch.objects.create(name="Branch Surabaya", code="SUB01", distributor=self.dist)
        self.ordertype = OrderType.objects.create(name="Regular", code="REG", distributor=self.dist)
        self.order = OrderHeader.objects.create(
            distributor=self.dist,
            branch=self.branch,
            ordertype=self.ordertype,
            orderno="ORD-VIEW-001",
            orderdate=date.today(),
            orderdue=date.today(),
            progress=self.status_draft,
        )

    def test_order_list_view(self):
        response = self.client.get(reverse("supplychain:order_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                module="SupplyChain",
                feature="Order List",
                action=LogAction.READ,
            ).exists()
        )

    def test_order_view_detail(self):
        response = self.client.get(reverse("supplychain:order_view", kwargs={"pk": self.order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                module="SupplyChain",
                feature="Order View Detail",
                action=LogAction.READ,
            ).exists()
        )

    def test_branch_list_view(self):
        response = self.client.get(reverse("supplychain:branch_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SystemLog.objects.filter(
                module="SupplyChain",
                feature="Branch List",
                action=LogAction.READ,
            ).exists()
        )

    def test_get_branches_ajax(self):
        response = self.client.get(
            reverse("supplychain:get_branches"),
            {"distributor_id": self.dist.id},
        )
        self.assertEqual(response.status_code, 200)

    def test_get_ordertypes_ajax(self):
        response = self.client.get(
            reverse("supplychain:get_ordertypes"),
            {"distributor_id": self.dist.id},
        )
        self.assertEqual(response.status_code, 200)


@override_settings(SYSTEM_LOG_SYNC=True)
class SupplyChainFormTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            username="form_user",
            email="form_user@example.com",
            password="password123",
        )
        status = ForcePasswordStatus.objects.filter(user=self.user).first()
        if status:
            status.must_change_password = False
            status.save()

        self.dist = Distributor.objects.create(name="Dist Form", code="DF")
        self.branch_type = BranchType.objects.create(name="HQ", code="HQ")

    def test_branch_form_validation(self):
        form_data = {
            "name": "Branch Test Form",
            "code": "BTF01",
            "initial": "BTF",
            "distributor": self.dist.id,
            "type": self.branch_type.id,
            "has_sales": True,
            "has_stock": True,
            "has_order": True,
        }
        form = BranchForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
