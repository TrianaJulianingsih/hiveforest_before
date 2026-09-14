from django.contrib import admin
from apps.finance.models.receivable_models import ARBalance, ARCollection
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ARBalanceAdmin                                      ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering ARBalance in Admin Site              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\admin.py                               ║
# ║  Created: Jun/19-2025 by Setiadji                          ║
# ║  Updates: Jun/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(ARBalance)
class ARBalanceAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('tipe', 'nc_np_segmentasi', 'trx_number', 'party_id', 'cust_account_id', 'cust_account_number', 'cust_account_name', 'organization_name', 'trxname', 'party_site_name') + \
        ('customer_location', 'cust_class_code', 'ownstatus', 'nama_salesman', 'nama_collector', 'penjaminan', 'trx_date', 'payment_terms', 'due_date', 'umur_piutang',) + \
        ('tax_document_number', 'item_category', 'item_code', 'item_description', 'amount', 'total_applied', 'balance', 'current_due', 'due_0_30', 'due_31_60', 'due_61_90',) + \
        ('due_91_120', 'due_121_150', 'due_151_180', 'due_181_364', 'due_365', 'due_above_365', 'due_91_180', 'due_181_365', 'due_366_730', 'due_above_730',) + \
        ('tanggal_hitung', 'kc_kp_segmentasi', 'tglfaktur', 'ket_due', 'approval_penjaminan_doc_no', 'kodevendor', 'kodevendor1', 'namavendor', 'grup_produk','group_produk', ) + \
        ('branch', 'branch_code', 'branch_name', 'kelas', 'cek1', 'ket_due_2', 'ket_group_1', 'ket_group_2', 'date_proses', 'month_transaksi', 'time_proses',) + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + \
        ('tipe', 'nc_np_segmentasi', 'trx_number', 'party_id', 'cust_account_id', 'cust_account_number', 'cust_account_name', 'organization_name', 'trxname', 'party_site_name') + \
        ('customer_location', 'cust_class_code', 'ownstatus', 'nama_salesman', 'nama_collector', 'penjaminan', 'trx_date', 'payment_terms', 'due_date', 'umur_piutang',) + \
        ('tax_document_number', 'item_category', 'item_code', 'item_description', 'amount', 'total_applied', 'balance', 'current_due', 'due_0_30', 'due_31_60', 'due_61_90',) + \
        ('due_91_120', 'due_121_150', 'due_151_180', 'due_181_364', 'due_365', 'due_above_365', 'due_91_180', 'due_181_365', 'due_366_730', 'due_above_730',) + \
        ('tanggal_hitung', 'kc_kp_segmentasi', 'tglfaktur', 'ket_due', 'approval_penjaminan_doc_no', 'kodevendor', 'kodevendor1', 'namavendor', 'grup_produk','group_produk', ) + \
        ('branch', 'branch_code', 'branch_name', 'kelas', 'cek1', 'ket_due_2', 'ket_group_1', 'ket_group_2', 'date_proses', 'month_transaksi', 'time_proses',) 
    list_per_page = 1000
    has_pandas_import = True

    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('tipe', 'nc_np_segmentasi', 'trx_number', 'party_id', 'cust_account_id', 'cust_account_number', 'cust_account_name', 'organization_name', 'trxname', 'party_site_name') + \
        ('customer_location', 'cust_class_code', 'ownstatus', 'nama_salesman', 'nama_collector', 'penjaminan', 'trx_date', 'payment_terms', 'due_date', 'umur_piutang',) + \
        ('tax_document_number', 'item_category', 'item_code', 'item_description', 'amount', 'total_applied', 'balance', 'current_due', 'due_0_30', 'due_31_60', 'due_61_90',) + \
        ('due_91_120', 'due_121_150', 'due_151_180', 'due_181_364', 'due_365', 'due_above_365', 'due_91_180', 'due_181_365', 'due_366_730', 'due_above_730',) + \
        ('tanggal_hitung', 'kc_kp_segmentasi', 'tglfaktur', 'ket_due', 'approval_penjaminan_doc_no', 'kodevendor', 'kodevendor1', 'namavendor', 'grup_produk','group_produk', ) + \
        ('branch', 'branch_code', 'branch_name', 'kelas', 'cek1', 'ket_due_2', 'ket_group_1', 'ket_group_2', 'date_proses', 'month_transaksi', 'time_proses',) 
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('name', 'description', 'remark', 'status', 'slug'),
            'description': 'System related information.',
        }),
    )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ARCollectionAdmin                                   ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering ARCollection in Admin Site           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\admin.py                               ║
# ║  Created: Jun/20-2025 by Setiadji                          ║
# ║  Updates: Jun/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(ARCollection)
class ARCollectionAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + BaseModelAdmin.list_display_name + \
        ('date_from', 'date_to', 'cabang', 'username', 'tanggal', 'kode_salesman', 'kode_collector', 'kode_pelanggan', 'nama_pelanggan', 'alamat_pelanggan', 'npwp',) + \
        ('nomor_faktur', 'trx_date', 'tax_document_number', 'nilai_faktur', 'dpp_number', 'dpp_date', 'collect_amount', 'ssp_ppn', 'ssp_pph', 'receiptnumber', 'receipt_date',) + \
        ('receipt_type', 'reference_number', 'reference_date', 'receipt_method', 'apply_amount', 'customer_trx_id', 'saldo_ar', 'time_proses', 'customer_trx_id1', ) + \
        ('trx_number', 'batch_source_name', 'line_number', 'line_type', 'item_code', 'quantity_invoiced', 'unit_selling_price', 'tax_rate', 'amount', 'amount_tax',) + \
        ('amount_total', 'item_description', 'primary_uom_code', 'primary_unit_of_measure', 'imhrmn', 'imhrmn_description', 'harmonisasi', 'grup_produk', 'group_produk',) + \
        ('principal', 'kodevendor', 'kodevendor1', 'namavendor', 'cust_class_code', 'jumlah_bayar', 'tgltransaksi', 'ket_grup_1', 'ket_grup_2', 'month_transaksi', 'date_proses',) + \
        BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + \
        ('date_from', 'date_to', 'cabang', 'username', 'tanggal', 'kode_salesman', 'kode_collector', 'kode_pelanggan', 'nama_pelanggan', 'alamat_pelanggan', 'npwp',) + \
        ('nomor_faktur', 'trx_date', 'tax_document_number', 'nilai_faktur', 'dpp_number', 'dpp_date', 'collect_amount', 'ssp_ppn', 'ssp_pph', 'receiptnumber', 'receipt_date',) + \
        ('receipt_type', 'reference_number', 'reference_date', 'receipt_method', 'apply_amount', 'customer_trx_id', 'saldo_ar', 'time_proses', 'customer_trx_id1', ) + \
        ('trx_number', 'batch_source_name', 'line_number', 'line_type', 'item_code', 'quantity_invoiced', 'unit_selling_price', 'tax_rate', 'amount', 'amount_tax',) + \
        ('amount_total', 'item_description', 'primary_uom_code', 'primary_unit_of_measure', 'imhrmn', 'imhrmn_description', 'harmonisasi', 'grup_produk', 'group_produk',) + \
        ('principal', 'kodevendor', 'kodevendor1', 'namavendor', 'cust_class_code', 'jumlah_bayar', 'tgltransaksi', 'ket_grup_1', 'ket_grup_2', 'month_transaksi', 'date_proses',)
    list_per_page = 1000
    has_pandas_import = True

    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('date_from', 'date_to', 'cabang', 'username', 'tanggal', 'kode_salesman', 'kode_collector', 'kode_pelanggan', 'nama_pelanggan', 'alamat_pelanggan',) + \
                ('npwp', 'nomor_faktur', 'trx_date', 'tax_document_number', 'nilai_faktur', 'dpp_number', 'dpp_date', 'collect_amount', 'ssp_ppn', 'ssp_pph', 'receiptnumber',) + \
                ('receipt_date', 'receipt_type', 'reference_number', 'reference_date', 'receipt_method', 'apply_amount', 'customer_trx_id', 'saldo_ar', 'time_proses',) + \
                ('customer_trx_id1', 'trx_number', 'batch_source_name', 'line_number', 'line_type', 'item_code', 'quantity_invoiced', 'unit_selling_price', 'tax_rate',) + \
                ('amount', 'amount_tax', 'amount_total', 'item_description', 'primary_uom_code', 'primary_unit_of_measure', 'imhrmn', 'imhrmn_description', 'harmonisasi',) + \
                ('grup_produk', 'group_produk', 'principal', 'kodevendor', 'kodevendor1', 'namavendor', 'cust_class_code', 'jumlah_bayar', 'tgltransaksi', 'ket_grup_1',) + \
                ('ket_grup_2', 'month_transaksi', 'date_proses',),
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('name', 'description', 'remark', 'status', 'slug'),
            'description': 'System related information.',
        }),
    )
