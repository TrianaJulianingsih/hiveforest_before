from django.db import models
from apps.base.models.entities import Company
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from django.utils.text import slugify
from django.db import IntegrityError
from apps.supplychain.models.distributions import Branch, Distributor, DistributorItem
from apps.sales.models.customer import Outlet
from apps.humancapital.models.structure import Position
from apps.base.models.items import UoM
from apps.finance.models.products import ItemPrice

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawMUSO                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of MUP              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/8-2025 by Noval                              ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawMUSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    whse = models.CharField(max_length=6, null=True, blank=True, default="", verbose_name="WHSE")
    no_order = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="No_Order")
    nodokjdi = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="NoDokJDI")
    hrdok = models.CharField(max_length=8, null=True, blank=True, default="", verbose_name="HRDok")
    area = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Area")
    kodepos = models.CharField(max_length=9, null=True, blank=True, default="", verbose_name="KodePos")
    gruplang = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="GrupLang")
    kodelang = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="KodeLang")
    kdcust = models.CharField(max_length=25, null=True, blank=True, default="", verbose_name="KdCust")
    nmlang = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="NmLang")
    almtlang = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="AlmtLang")
    kodesalur = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="KodeSalur")
    kodeprod = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="KodeProd")
    nmprod = models.CharField(max_length=40, null=True, blank=True, default="", verbose_name="NmProd")
    klasprod = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="KlasProd")
    nmklas1 = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="NmKlas1")
    nmklas2 = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="NmKlas2")
    banyak = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True, default=None, verbose_name='Banyak')
    hna = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name='HNA')
    harga = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name='Harga')
    tharga = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None, verbose_name='THarga')
    thna = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None, verbose_name='THNA')
    banys = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True, default=None, verbose_name='BanyS')
    ehna = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name='EHNA')
    prsnpot = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, default=None, verbose_name='PrsnPot')
    pharga = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True, default=None, verbose_name='PHarga')
    prsnbp = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, default=None, verbose_name='PrsnBP')
    prsnbmp = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, default=None, verbose_name='PrsnBMP')
    mom = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="MoM")
    nobat = models.CharField(max_length=40, null=True, blank=True, default="", verbose_name="NoBat")
    dun = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="DUN")
    idpkt = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="IDPKT")
    principle = models.ForeignKey('base.Company', on_delete=models.PROTECT, null=True, blank=True, verbose_name="Principle")

    class Meta:
        verbose_name = "Raw MU-SO"
        verbose_name_plural = "Raw MU-SO"
        ordering = ("-name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def save(self, *args, **kwargs):
        try:
            if not self.code:  # Generate only if not set
                whse_str = str(self.whse).strip() if self.whse else ""
                if whse_str.isdigit():
                    whse_str = f"{int(whse_str):03d}"  # Zero-pad if numeric

                nodokjdi_str = str(self.nodokjdi).strip() if self.nodokjdi else ""
                if nodokjdi_str.isdigit():
                    nodokjdi_str = f"{int(nodokjdi_str):07d}"
                mom_str = str(self.mom).strip() if self.mom else "NA"
                if mom_str.isdigit():
                    mom_str = f"{int(mom_str):03d}"

                self.banys_value = str(self.banys) if self.banys not in [None, "", "NULL"] else "0"  # ✅ Ensure banys is always a string
                self.code = f"{self.hrdok}-{whse_str}-{nodokjdi_str[-7:]}-{self.kodeprod}-{self.nobat}-{self.hna}-{self.harga}-{self.banyak}-{self.banys_value}-{mom_str}"
                self.name = f"{self.hrdok}{whse_str}{nodokjdi_str[-7:]}.{self.kodeprod}"
                
            if not self.slug or self.code:
                base_slug = slugify(self.code)
                slug = base_slug
                counter = 1
                while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug

            # Assign principle based on klasprod prefix
            if self.klasprod:
                if self.klasprod.startswith("001"):
                    self.principle = 1
                elif self.klasprod.startswith("002"):
                    self.principle = 2

            super().save(*args, **kwargs)
            
        except IntegrityError as e:
            print(f"❌ ERROR: Database Integrity Error - {e}")

        except Exception as e:
            print(f"❌ ERROR: Unexpected error in save method - {e}")

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawRNSO                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of RN               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/17-2025 by Noval                             ║
# ║  Updates: Jun/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
class RawRNSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default='', verbose_name='Code')
    branch_id = models.CharField(max_length=255, null=False, blank=True, default='', verbose_name='BranchID')
    branch_name = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='BranchName')
    class_name = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='ClassName')
    catalog_no = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='CatalogNo')
    prod_id = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='ProdID')
    prod_name = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='ProdName')
    uom = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='UOM')
    kwt = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, default=None, verbose_name='KWT')
    price_list = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None, verbose_name='Price List')
    neto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Neto')
    disc_amt = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='DiscAmt')
    bruto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Bruto')
    invoice_date = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='InvoiceDate')
    invoice_no = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='InvoiceNo')
    no_pesan = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='NoPesan')
    ref_invoice = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='RefInvoice')
    cust_id = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='CustID')
    cust_id_old = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='CustIDOld')
    nama_pelanggan = models.CharField(max_length=255, null=True, default='', verbose_name='NamaPelanggan')
    kategori_pelanggan = models.CharField(max_length=100, null=True, default='', verbose_name='KategoriPelanggan')
    kota = models.CharField(max_length=100, null=True, default='', verbose_name='Kota')
    alamat = models.CharField(max_length=255, null=True, default='', verbose_name='Alamat')
    periode = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Periode')

    class Meta:
        verbose_name = 'Raw RN-SO'
        verbose_name_plural = 'Raw RN-SO'
        ordering = ('-name',)
        permissions = [
            ('soft_delete', 'Can delete items'),
            ('soft_restore', 'Can restore deleted items'),
        ]

    def save(self, *args, **kwargs):
        try:
            if not self.code:  # Generate only if not set
                invoice_no_str = str(self.invoice_no).replace("/","") if self.invoice_no else ""
                invoice_date_str = str(self.invoice_date).split(" ")[0].replace("-","") if self.invoice_date else ""
                prod_id_str = str(self.prod_id).strip() if self.prod_id else ""

                self.code = f"{prod_id_str}-{invoice_date_str}-{invoice_no_str}-{self.kwt}-{self.cust_id}-{self.no_pesan}" # need adjustmnet
                self.name = f"{prod_id_str}-{invoice_date_str}-{invoice_no_str}"

            if not self.slug or self.code:
                base_slug = slugify(self.code)
                slug = base_slug
                counter = 1
                while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug

            super().save(*args, **kwargs)

        except IntegrityError as e:
            print(f"❌ ERROR: Database Integrity Error - {e}")

        except Exception as e:
            print(f"❌ ERROR: Unexpected error in save method - {e}")

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawLMSSO                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of LMS              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/17-2025 by Noval                             ║
# ║  Updates: Jun/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawLMSSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default='', verbose_name='Code')
    tanggal = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='Tanggal')
    nomor_bukti = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Nomor Bukti')
    kode_customer = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Kode Customer')
    nama_customer = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Nama Customer')
    alamat = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Alamat')
    kota = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Kota')
    kode_cabang = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Kode Cabang')
    kode_sales = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Kode Sales')
    nama_sales = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Nama Sales')
    kode_barang = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Kode Barang')
    nama_barang = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Nama Barang')
    satuan = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Satuan')
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name='Qty')
    hna = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='HNA')
    disc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Disc')
    nilai = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Nilai')
    disc_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Disc Value')
    nilai_netto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Nilai Netto')
    total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Total')

    class Meta:
        verbose_name = 'Raw LMS-SO'
        verbose_name_plural = 'Raw LMS-SO'
        ordering = ('-name',)
        permissions = [
            ('soft_delete', 'Can delete items'),
            ('soft_restore', 'Can restore deleted items'),
        ]

    def save(self, *args, **kwargs):
        try:
            if not self.code:  # Generate only if not set
                invoice_no_str = str(self.invoice_no).replace("/","") if self.invoice_no else ""
                invoice_date_str = str(self.invoice_date).split(" ")[0].replace("-","") if self.invoice_date else ""
                prod_id_str = str(self.prod_id).strip() if self.prod_id else ""

                self.code = f"{prod_id_str}-{invoice_date_str}-{invoice_no_str}-{self.kwt}-{self.cust_id}-{self.no_pesan}" # need adjustmnet
                self.name = f"{prod_id_str}-{invoice_date_str}-{invoice_no_str}"

            if not self.slug or self.code:
                base_slug = slugify(self.code)
                slug = base_slug
                counter = 1
                while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug

            super().save(*args, **kwargs)

        except IntegrityError as e:
            print(f"❌ ERROR: Database Integrity Error - {e}")

        except Exception as e:
            print(f"❌ ERROR: Unexpected error in save method - {e}")

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawKFSO                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of KFTD             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawKFSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default='', verbose_name='Code')
    sales_office = models.CharField(max_length=50, null=False, default='', verbose_name='Sales Office')
    desc_s_office = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. S.Office')
    so_type = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='SO Type')
    desc_sales_order = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. Sales Order')
    billing_type = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Billing Type')
    posting_date = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Posting Date')
    billing_no = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Billing No')
    posting_status = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Posting Status')
    bill_cancel = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Bill.Cancel')
    bill_to_party = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Bill to party')
    sold_to_party = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Sold to Party')
    name_bill_to = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Name Bill to')
    address = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Address')
    city = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='City')
    region = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Region')
    postal_code = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='Postal Code')
    ship_to_party = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Ship to Party')
    name_ship_to = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Name Ship to')
    address_ship_to = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Address Ship to')
    city_ship_to = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='City Ship to')
    postal_code_ship_to = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='Postal Code Ship to')
    material = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Material')
    text_material = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Text Material')
    quantity = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, default=None, verbose_name='Quantity')
    sales_unit = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Sales Unit')
    bill_qty_in_sku = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name='Bill Qty in SKU')
    uom_sku = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='UoM SKU')
    unit_price_penjualan = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=None, verbose_name='Unit Price Penjualan')
    dis_zd01 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD01)')
    dis_amt_zd01 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD01)')
    dis_zd02 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD02)')
    dis_amt_zd02 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD02)')
    dis_zd03 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD03)')
    dis_amt_zd03 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD03)')
    dis_zd04 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD04)')
    dis_amt_zd04 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD04)')
    dis_zd05 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD05)')
    dis_amt_zd05 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD05)')
    dis_zd06 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name='Dis% (ZD06)')
    dis_amt_zd06 = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='DisAmt (ZD06)')
    total_discount = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='Total Discount')
    surcharge = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name='Surcharge')
    total_penjualan = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='Total Penjualan')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name='Tax Amount')
    curr = models.CharField(max_length=10, null=True, blank=True, default='', verbose_name='Curr')
    code_pelayanan = models.CharField(max_length=5, null=True, blank=True, default='', verbose_name='Code Pelayanan')
    desc_pelayanan = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Desc. Pelayanan')
    prodh_material = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Prodh. Material')
    prod_hierarchy1 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Prod. Hierarchy1')
    prod_hierarchy2 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Prod. Hierarchy2')
    prod_hierarchy3 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Prod. Hierarchy3')
    prod_hierarchy4 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Prod. Hierarchy4')
    manufactur = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Manufactur')
    name_manufactur = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Name Manufactur')
    principle = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Principle')
    name_principle = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Name Principle')
    cust_grp1 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Cust. Grp1')
    desc_cust_grp1 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. Cust. Grp1')
    cust_grp2 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Cust. Grp2')
    desc_cust_grp2 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. Cust. Grp2')
    cust_grp3 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Cust. Grp3')
    desc_cust_grp3 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. Cust. Grp3')
    cust_grp4 = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Cust. Grp4')
    desc_cust_grp4 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Desc. Cust. Grp4')
    salesman = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Salesman')
    name_salesman = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Name Salesman')
    cancelled_bill_doc = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Cancelled Bill.Doc.')
    bill_doc_creation_date = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Bill.Doc.Creation Date')
    user_login_tpd_line_disc4 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='User Login TPD (Line Disc4)')
    remark_ptd_4 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Remark PTD 4')
    user_login_tpd_line_disc2 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='User Login TPD (Line Disc2)')
    remark_ptd_2 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Remark PTD 2')
    user_login_tpd_line_disc3 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='User Login TPD (Line Disc3)')
    remark_ptd_3 = models.CharField(max_length=255, null=True, blank=True, default='', verbose_name='Remark PTD 3') 

    class Meta:
        verbose_name = 'Raw KFTD-SO'
        verbose_name_plural = 'Raw KFTD-SO'
        ordering = ('-name',)
        permissions = [
            ('soft_delete', 'Can delete items'),
            ('soft_restore', 'Can restore deleted items'),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawIGSO                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of IGM              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jul/16-2025 by Noval                             ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawIGSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    tanggal_trans = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Tanggal Trans")
    cabang = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Cabang")
    kode_cust = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Cust")
    cust_desc = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Cust Desc")
    cust_city = models.CharField(max_length=100, null=True, blank=True, default="", verbose_name="Cust City")
    cust_addr = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Cust Addr")
    cust_group = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Cust Group")
    invoice_number = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Invoice Number")
    type_sales = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Type Sales")
    item = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Item")
    item_desc = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Item Desc")
    principal = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Principal")
    qty = models.DecimalField(max_digits=50, decimal_places=0, null=True, blank=True, default=None, verbose_name="QTY")
    hpp = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=None, verbose_name="HPP")
    disc_igm = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Disc IGM")
    percent_igm = models.DecimalField(max_digits=15, decimal_places= 2, null=True, blank=True, default=None, verbose_name="Percent IGM")
    disc_princip = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Disc PRINC")
    percent_princip = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Percent PRINC")
    disc_marketing = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Disc Marketing")
    percent_marketing = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Percent Marketing")
    gross = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Gross")
    sales_nett = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Sales Nett")
    do_number = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="DO Number")
    id_paket = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="ID Paket")
    invoice_referensi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Invoice Referensi")
    salesman = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Salesman")
    group_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Group Produk")
    group_principal = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Group Principal")
    tax_amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=None, verbose_name="Tax Amount")
    tax_code = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Tax Code")
    seri_pajak = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Seri Pajak")
    pengantar_barang = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Pengantar Barang")
    cash_disc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Cash Disc")
    cash_percent = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Cash Percent")
    tgl_do_posting = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Tanggal DO Posting")
    remarks_so = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Remarks SO")
    no_kontrak = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="No Kontrak")
    no_epdo = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="No EPDO")
    referensi_epdo = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Referensi EPDO")
    kurs = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=None, verbose_name="Kurs")
    currency = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Currency")
    top = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="TOP")
    mr_inaf = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="MR INAF")
    outsourcing_salesman = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Outsourcing Salesman")
    so_number = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="SO Number")

    class Meta:
        verbose_name = "Raw IGM-SO"
        verbose_name_plural = "Raw IGM-SO"
        ordering = ("-name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawPPSO                                             ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of PPI              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/30-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawPPSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    cabang = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Cabang")
    nama_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Nama Outlet")
    kode_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Kode Outlet")
    kode_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Produk")
    nama_produk = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Nama Produk")
    qty_botol = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name="Qty (Botol)")
    value_rp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Value (Rp.)")
    tanggal_invoice = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Tanggal Invoice")

    class Meta:
        verbose_name = "Raw PPI-SO"
        verbose_name_plural = "Raw PPI-SO"
        ordering = ("-name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawAPLSO                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of APL              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawAPLSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    kode_distributor = models.CharField(max_length=50, null=False, default="", verbose_name="Kode Distributor")
    type = models.CharField(max_length=50, null=False, default="", verbose_name="Type")
    facno = models.CharField(max_length=50, null=False, default="", verbose_name="Facno")
    tanggal = models.CharField(max_length=50, null=False, default="", verbose_name="Tanggal")
    kode_produk = models.CharField(max_length=50, null=False, default="", verbose_name="Kode Produk")
    produk = models.CharField(max_length=255, null=False, default="", verbose_name="Produk")
    kode_produk_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Produk OI")
    produk_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Produk OI")
    kode_group_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Group Produk")
    group_produk = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Group Produk")
    kode_subgroup_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Subgroup Produk")
    subgroup_produk = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Subgroup Produk")
    kode_branch = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Branch")
    branch = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Branch")
    id_branch_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="ID Branch OI")
    kode_branch_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Branch OI")
    branch_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Branch OI")
    kode_outlet = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Outlet")
    cust_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Cust ID")
    outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Outlet")
    alamat_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Alamat Outlet")
    kode_outlet_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Outlet OI")
    outlet_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Outlet OI")
    alamat_outlet_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Alamat Outlet OI")
    kode_group_outlet = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Group Outlet")
    group_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Group Outlet")
    kode_salur = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Salur")
    kode_sector = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Sector")
    sector = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Sector")
    kode_channel = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Channel")
    channel = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Channel")
    kode_sub_channel = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Sub Channel")
    sub_channel = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Sub Channel")
    kode_region = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Region")
    region = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Region")
    qty = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name="Qty")
    faktor_kali = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name="Faktor Kali")
    hjp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="HJP")
    hna = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="HNA")
    harga = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Harga")
    whse = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Whse")
    tanggal_expired = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Tanggal Expired")
    batch = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Batch")
    prsnd = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsND")
    prsnpot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnPot")
    prsnt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsNT")
    prsnbp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBP")
    prsnbmp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBMP")
    bonus = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Bonus")
    facAcu = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="FacAcu")
    kode_team = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Team")
    team = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Team")
    dun = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="DUN")
    distribute_apks = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Distribute APKs")
    distributed_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Distributed ID")
    distributed_name = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Distributed Name")
    parent_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Parent ID")
    missing_facno = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Missing Facno")
    no_order = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="No Order")
    periode = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Periode")

    class Meta:
            verbose_name = "Raw APL -SO"
            verbose_name_plural = "Raw APL-SO"
            ordering = ("-name",)
            permissions = [
                ("soft_delete", "Can delete items"),
                ("soft_restore", "Can restore deleted items"),
            ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawAPPSO                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain raw selling out data of APP              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class RawAPPSO(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    kode_distributor = models.CharField(max_length=50, null=False, default="", verbose_name="Kode Distributor")
    type = models.CharField(max_length=50, null=False, default="", verbose_name="Type")
    facno = models.CharField(max_length=50, null=False, default="", verbose_name="Facno")
    tanggal = models.CharField(max_length=50, null=False, default="", verbose_name="Tanggal")
    kode_produk = models.CharField(max_length=50, null=False, default="", verbose_name="Kode Produk")
    produk = models.CharField(max_length=255, null=False, default="", verbose_name="Produk")
    kode_produk_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Produk OI")
    produk_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Produk OI")
    kode_group_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Group Produk")
    group_produk = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Group Produk")
    kode_subgroup_produk = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Subgroup Produk")
    subgroup_produk = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Subgroup Produk")
    kode_branch = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Branch")
    branch = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Branch")
    id_branch_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="ID Branch OI")
    kode_branch_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Branch OI")
    branch_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Branch OI")
    kode_outlet = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Outlet")
    cust_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Cust ID")
    outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Outlet")
    alamat_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Alamat Outlet")
    kode_outlet_oi = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Outlet OI")
    outlet_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Outlet OI")
    alamat_outlet_oi = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Alamat Outlet OI")
    kode_group_outlet = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Group Outlet")
    group_outlet = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Group Outlet")
    kode_salur = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Salur")
    kode_sector = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Sector")
    sector = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Sector")
    kode_channel = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Channel")
    channel = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Channel")
    kode_sub_channel = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Sub Channel")
    sub_channel = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Sub Channel")
    kode_region = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Region")
    region = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Region")
    qty = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, default=None, verbose_name="Qty")
    faktor_kali = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, verbose_name="Faktor Kali")
    hjp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="HJP")
    hna = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="HNA")
    harga = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Harga")
    whse = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Whse")
    tanggal_expired = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Tanggal Expired")
    batch = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Batch")
    prsnd = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsND")
    prsnpot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnPot")
    prsnt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsNT")
    prsnbp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBP")
    prsnbmp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBMP")
    bonus = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None, verbose_name="Bonus")
    facAcu = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="FacAcu")
    kode_team = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Kode Team")
    team = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Team")
    dun = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="DUN")
    distribute_apks = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Distribute APKs")
    distributed_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Distributed ID")
    distributed_name = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Distributed Name")
    parent_id = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Parent ID")
    missing_facno = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Missing Facno")
    no_order = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="No Order")
    periode = models.CharField(max_length=50, null=True, blank=True, default="", verbose_name="Periode")

    class Meta:
            verbose_name = "Raw APP-SO"
            verbose_name_plural = "Raw APP-SO"
            ordering = ("-name",)
            permissions = [
                ("soft_delete", "Can delete items"),
                ("soft_restore", "Can restore deleted items"),
            ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SellingOut                                          ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain selling out data from all distributors   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates: Aug/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
class SellingOut(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    raw_id = models.IntegerField(null=True, blank=True, verbose_name="Raw ID")
    invoice_date = models.DateField(verbose_name= "Invoice Date")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, verbose_name="Company", null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Branch")
    distributor = models.ForeignKey(Distributor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Distributor")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Outlet")
    item = models.ForeignKey(DistributorItem, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Item")
    invoice_number = models.CharField(max_length=255, null=True, blank=True, default="", verbose_name="Invoice Number")
    qty = models.IntegerField(null=True, blank=True,  verbose_name="Quantity")
    bonusqty = models.IntegerField(null=True, blank=True,  verbose_name="Bonus Qty")
    bonusvalue = models.IntegerField(null=True, blank=True,  verbose_name="Bonus Value")
    grossvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Gross Value")
    discvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Disc Value")
    netvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Net Value")
    isbonus = models.IntegerField(null=True, blank=True, verbose_name="Is Bonus")
    pricecode = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Price Code")
    hjpprice = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="HJP Price")
    hjpvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="HJP Value")
    so = models.IntegerField(null=True, blank=True, verbose_name="SO")
    soo = models.IntegerField(null=True, blank=True, verbose_name="SOO")
    uom = models.ForeignKey(UoM, on_delete=models.SET_NULL, verbose_name="UoM", null=True, blank=True)
    prsnbp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBP")
    prsnbmp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None, verbose_name="PrsnBMP")
    closed = models.BooleanField(verbose_name="Closed", null=True, blank=True, default=False)

    class Meta:
            verbose_name = "Selling Out"
            verbose_name_plural = "Selling Out"
            ordering = ("-name",)
            permissions = [
                ("soft_delete", "Can delete items"),
                ("soft_restore", "Can restore deleted items"),
            ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AnnualTarget                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain annual target for each subgroup items    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jul/1-2025 by Noval                              ║
# ║  Updates: Aug/7-2025 by Noval                              ║
# ╚════════════════════════════════════════════════════════════╝ 
class AnnualTarget(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    version = models.IntegerField(null=True, blank=True, default=1, verbose_name="Version")
    date = models.DateField(default=None, verbose_name= "Date")
    product = models.ForeignKey('sales.Product', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Product")
    type = models.ForeignKey('sales.SalesType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type")
    qty = models.IntegerField(verbose_name="Qty")
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Price")
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Value")
    targetgroup = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Target Group')

    class Meta:
            verbose_name = "Annual Target"
            verbose_name_plural = "Annual Target"
            ordering = ("-name",)
            permissions = [
                ("soft_delete", "Can delete items"),
                ("soft_restore", "Can restore deleted items"),
            ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CycleTarget                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain cycle target for each items per group    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Jul/1-2025 by Noval                              ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class CycleTarget(GenericAbstract):
    code = models.CharField(max_length=255, null=False, default="", verbose_name="Code")
    group = models.ForeignKey('sales.ProductGroup', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Group")
    subgroup = models.ForeignKey('sales.ProductSubgroup', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sub Group")
    item = models.ForeignKey('sales.Product', on_delete=models.SET_NULL, null=True, blank=True,  verbose_name="Item")
    mr = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,  verbose_name="MR", related_name="mr_cycletargets")
    am = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,  verbose_name="AM", related_name="am_cycletargets")
    rm = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,  verbose_name="RM", related_name="rm_cycletargets")
    month = models.IntegerField(verbose_name="Month")
    year = models.IntegerField(verbose_name="Year")
    type = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Type")
    qty = models.IntegerField(verbose_name="Qty")
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Value")
    version = models.DecimalField(max_digits=15, decimal_places=1, null=True, blank=True, verbose_name="Version")

    class Meta:
            verbose_name = "Cycle Target"
            verbose_name_plural = "Cycle Target"
            ordering = ("-name",)
            permissions = [
                ("soft_delete", "Can delete items"),
                ("soft_restore", "Can restore deleted items"),
            ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RepOffice                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain representative offices                   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝              
class RepOffice(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")
    type = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")

    class Meta:
        verbose_name = "Representative Office"
        verbose_name_plural = "Representative Offices"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesType                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain sales type                               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
class SalesType(GenericAbstract):
    code = models.CharField(max_length=10, null=False, default="", verbose_name="Code")
    initial = models.CharField(max_length=7, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Shortname")
    parent = models.ForeignKey('SalesType', on_delete=models.CASCADE, verbose_name="Parent",null=True, blank=True)

    class Meta:
        verbose_name = "Sales Type"
        verbose_name_plural = "Sales Types"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: eCatalog                                            ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain ecatalog sales                           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\models\sales.py                          ║
# ║  Created: Aug/19-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝ 
class ECatalog(GenericAbstract):
    code = models.CharField(max_length=225, null=False, default="", verbose_name="Code")
    nomor_paket = models.CharField(max_length=25, null=True, blank=True, verbose_name='Nomor Paket')
    rup = models.CharField(max_length=10, null=True, blank=True, verbose_name='RUP')
    sumber_dana = models.CharField(max_length=20, null=True, blank=True, verbose_name='Sumber Dana')
    tahun_anggaran = models.IntegerField(verbose_name='Tahun Anggaran')
    etalase = models.CharField(max_length=80, null=True, blank=True, verbose_name='Etalase')
    jenis_katalog = models.CharField(max_length=10, null=True, blank=True, verbose_name='Jenis Katalog')
    instansi_pengelola_etalase = models.CharField(max_length=225, null=True, blank=True, verbose_name='Instansi Pengelola Etalase')
    nama_paket = models.CharField(max_length=1000, null=True, blank=True, verbose_name='Nama Paket')
    jenis_instansi = models.CharField(max_length=225, null=True, blank=True, verbose_name='Jenis Instansi')
    instansi = models.CharField(max_length=225, null=True, blank=True, verbose_name='Instansi')
    satuan_kerja = models.CharField(max_length=1000, null=True, blank=True, verbose_name = 'Satuan Kerja')
    alamat_satuan_kerja = models.CharField(max_length=1000,null=True, blank=True, verbose_name='Alamat Satuan Kerja')
    nama_ppk = models.CharField(max_length=225, null=True, blank=True, verbose_name='Nama PPK')
    nama_kategori = models.CharField(max_length=225, null=True, blank=True, verbose_name='Nama Kategori')
    merek_manufaktur = models.CharField(max_length=225, null=True, blank=True, verbose_name='Merek/Manufaktur')
    nomor_produk = models.CharField(max_length=225, null=True, blank=True, verbose_name='Nomor Produk')
    nomor_produk_penyedia = models.CharField(max_length=225, null=True, blank=True, verbose_name='Nomor Produk Penyedia')
    nama_produk = models.CharField(max_length=225, null=True, blank=True, verbose_name='Nama Produk')
    jenis_produk = models.CharField(max_length=20, null=True, blank=True, verbose_name='Jenis Produk')
    tkdn = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='TKDN (%)')
    kuantitas_pembelian = models.IntegerField(null=True, blank=True, verbose_name='Kuantitas Pembelian')
    harga_satuan_pembelian = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Harga Satuan Pembelian')
    ongkos_kirim = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Ongkos Kirim')
    total_harga = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, verbose_name='Total Harga')
    tanggal_pembuatan_paket = models.DateField(null=True, blank=True, verbose_name='Tanggal Pembuatan Paket')
    penyedia = models.CharField(max_length=225, null=True, blank=True, verbose_name='Penyedia')
    distributor = models.CharField(max_length=225, null=True, blank=True, verbose_name='Distributor')
    status_paket = models.CharField(max_length=225, null=True, blank=True, verbose_name='Status Paket')
    deskripsi_paket = models.CharField(max_length=225, null=True, blank=True, verbose_name='Deskripsi Paket')
    status_ukm = models.CharField(max_length=225, null=True, blank=True, verbose_name='Status UKM')
    product = models.ForeignKey('sales.Product',on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Product')
    satker = models.ForeignKey('sales.Satker', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Satker')
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Customer')
    business = models.ForeignKey('humancapital.Organization', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Business')

    class Meta:
        verbose_name = "E-Catalog"
        verbose_name_plural = "E-Catalogs"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        
    def __str__(self):
        return self.name