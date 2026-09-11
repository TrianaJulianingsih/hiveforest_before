from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ARBalance                                           ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain MUP AR Balance for dashboard report      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\models\receivable.py                   ║
# ║  Created: Jun/19-2025 by Setiadji                          ║
# ║  Updates: Jun/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ARBalance(GenericAbstract):
     
    tipe = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Type")
    nc_np_segmentasi = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "NC_NP_Segment")
    trx_number = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Invoice No")
    party_id = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "PartyID")
    cust_account_id = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Cust. Acc. ID")
    cust_account_number = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Cust. Acc. No")
    cust_account_name = models.CharField(max_length=160, blank=True, null=True, default='', verbose_name = "Cust. Acc. Name")
    organization_name = models.CharField(max_length=160, blank=True, null=True, default='', verbose_name = "Customer Name")
    trxname = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Invoice Type") # Change from NAME to trxname to avoid conflict with abstract field
    party_site_name = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Sector")
    customer_location = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Customer Area")
    cust_class_code = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Channel")
    ownstatus = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Segment") # Chanfe from STATUS to ownstatus to avoid conflict with abstract field
    nama_salesman = models.CharField(max_length=80, blank=True, null=True, default='', verbose_name = "Salesman")
    nama_collector = models.CharField(max_length=80, blank=True, null=True, default='', verbose_name = "Collector")
    penjaminan = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Guarantee")
    trx_date = models.DateField(blank=True, null=True,verbose_name = "Invoice Date")
    payment_terms = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Payment Term")
    due_date = models.DateField(blank=True, null=True, verbose_name = "DueDate")
    umur_piutang = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "AR Aging")
    tax_document_number = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "VAT No")
    item_category = models.CharField(max_length=50, blank=True, null=True, default='', verbose_name = "ItemCategory")
    item_code = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "ItemCode")
    item_description = models.CharField(max_length=90, blank=True, null=True, default='', verbose_name = "ItemDescription")
    amount = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Amount")
    total_applied = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "TotalAppl")
    balance = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Balance")
    current_due = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "CurrentDue")
    due_0_30 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due0-30")
    due_31_60 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due31-60")
    due_61_90 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due61-90")
    due_91_120 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due91-120")
    due_121_150 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due121-150")
    due_151_180 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due151-180")
    due_181_364 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due181-360")
    due_365 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due365")
    due_above_365 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "DueAbove365")
    due_91_180 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due91-180")
    due_181_365 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due181-320")
    due_366_730 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Due366-730")
    due_above_730 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "DueAbove2")
    tanggal_hitung = models.DateField(blank=True, null=True, verbose_name = "CalculateDate")
    kc_kp_segmentasi = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "KC_KP_Segment")
    tglfaktur = models.DateField(blank=True, null=True, verbose_name = "InvoiceDate")
    ket_due = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Aging Group")
    approval_penjaminan_doc_no = models.CharField(max_length=60, blank=True, null=True, default='', verbose_name = "GuaranteeApproval")
    kodevendor = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Principal Code")
    kodevendor1 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Principal Code2")
    namavendor = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Principal Name")
    grup_produk = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "ProductGroupCode")
    group_produk = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "ProductGroup")
    branch = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Branch")
    branch_code = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "BranchCode")
    branch_name = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "BranchName")
    kelas = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Class")
    cek1 = models.CharField(max_length=10, blank=True, null=True, default='', verbose_name = "Check1")
    ket_due_2 = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Aging Group 2")                    
    ket_group_1 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Business Unit")
    ket_group_2 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Chennel")
    date_proses = models.DateField(blank=True, null=True, verbose_name = "ProcessDate")
    month_transaksi = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "TransMonth")
    time_proses = models.DateTimeField(blank=True, null=True, verbose_name = "ProcessTime")

    class Meta:
        verbose_name = "AR Balance"
        verbose_name_plural = "AR Balances"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ARCollection                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Contain MUP AR Collection for dashboard report   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\models\receivable.py                   ║
# ║  Created: Jun/19-2025 by Setiadji                          ║
# ║  Updates: Jun/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
class ARCollection(GenericAbstract):
    date_from = models.DateField(blank=True, null=True,verbose_name = "DateFrom")
    date_to = models.DateField(blank=True, null=True,verbose_name = "DateTo")
    cabang = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Branch")
    username = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Username")
    tanggal = models.DateTimeField(blank=True, null=True, verbose_name = "Calculate Date")
    kode_salesman = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "SalesCode")
    kode_collector = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "CollectorCode")
    kode_pelanggan = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "CustAcc")
    nama_pelanggan = models.CharField(max_length=255, blank=True, null=True, default='', verbose_name = "Customer Name")
    alamat_pelanggan = models.CharField(max_length=255, blank=True, null=True, default='', verbose_name = "Customer Address")
    npwp = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "TaxID")
    nomor_faktur = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Invoice No")
    trx_date = models.DateField(blank=True, null=True,verbose_name = "Invoice Date")
    tax_document_number = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "VAT No")
    nilai_faktur = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "InvoiceAmount")
    dpp_number = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "DPPNumber")
    dpp_date = models.DateField(blank=True, null=True,verbose_name = "DPPDate")
    collect_amount = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "CollectionAmount")
    ssp_ppn = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "SSP_PPN")
    ssp_pph = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "SSP_PPH")
    receiptnumber = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "ReceiptNo")
    receipt_date = models.DateField(blank=True, null=True,verbose_name = "ReceiptDate")
    receipt_type = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Receipt Type")
    reference_number = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Reference")
    reference_date = models.DateField(blank=True, null=True,verbose_name = "ReferenceDate")
    receipt_method = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Receipt Memo")
    apply_amount = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Payment Amount by Type")
    customer_trx_id = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Customer Code")
    saldo_ar = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "ARBalance")
    time_proses = models.DateTimeField(blank=True, null=True, verbose_name = "ProcessTime")
    customer_trx_id1 = models.DecimalField(max_digits=15, blank=True, null=True, decimal_places=2, verbose_name = "Customer Code 2")
    trx_number = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "Invoice No 2")
    batch_source_name = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Branch")
    line_number = models.IntegerField(blank=True, null=True, default='', verbose_name = "LineNumber")
    line_type = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "LineType")
    item_code = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "ItemCode")
    quantity_invoiced = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "Quantity")
    unit_selling_price = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "UnitSellingPrice")
    tax_rate = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "TaxRate")
    amount = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "Amount")
    amount_tax = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "VAT")
    amount_total = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "Total")
    item_description = models.CharField(max_length=70, blank=True, null=True, default='', verbose_name = "ItemDescription")
    primary_uom_code = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "UoM")
    primary_unit_of_measure = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "UoM Description")
    imhrmn = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "IMHRMN")
    imhrmn_description = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "IMHRMNDescription")
    harmonisasi = models.CharField(max_length=50, blank=True, null=True, default='', verbose_name = "Harmonisasi")
    grup_produk = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "ProductGroupCode")
    group_produk = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "ProductGroup")
    principal = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Principal Name 2")
    kodevendor = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Principal Code")
    kodevendor1 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Principal Code2")
    namavendor = models.CharField(max_length=40, blank=True, null=True, default='', verbose_name = "Principal Name")
    cust_class_code = models.CharField(max_length=30, blank=True, null=True, default='', verbose_name = "CustomerClass")
    jumlah_bayar = models.DecimalField(max_digits=20, blank=True, null=True, decimal_places=2, verbose_name = "Payment Amount by Type 2")
    tgltransaksi = models.DateField(blank=True, null=True,verbose_name = "TransactionDate")
    ket_grup_1 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Business Unit")
    ket_grup_2 = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "Channel")
    month_transaksi = models.CharField(max_length=20, blank=True, null=True, default='', verbose_name = "TrxMonth")
    date_proses = models.DateTimeField(blank=True, null=True, verbose_name = "ProcessTime")

    class Meta:
        verbose_name = "AR Collection"
        verbose_name_plural = "AR Collections"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]