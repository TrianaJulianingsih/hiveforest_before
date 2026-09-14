from django.contrib import admin
from apps.analytics.models.sellingout_models import SellingOutCY

@admin.register(SellingOutCY)
class SellingOutCYAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'invoice_date', 'so', 'soo', 'isbonus', 'pricecode', 'price', 'qty',
        'grossvalue', 'discvalue', 'netvalue', 'hjp', 'company', 'distributor',
        'branch', 'outlet', 'customer', 'item', 'uom'
    )
    list_display_links = ("invoice_date",)
    search_fields = ('pricecode', 'so', 'soo')
    list_filter = ('company', 'distributor', 'branch')
    list_per_page = 1000
