from django.db import models

class SellingOutCY(models.Model):
    # Fact data
    invoice_date = models.DateField(verbose_name= 'Invoice Date')
    so = models.IntegerField(null=True, blank=True, verbose_name="SO")
    soo = models.IntegerField(null=True, blank=True, verbose_name="SOO")
    isbonus = models.IntegerField(null=True, blank=True, verbose_name="Is Bonus")
    pricecode = models.CharField(max_length=10, null=True, blank=True, default="", verbose_name="Price Code")
    price = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Price")
    # Measures
    qty = models.IntegerField(null=True, blank=True,  verbose_name="Quantity")
    grossvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Gross Value")
    discvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Disc Value")
    netvalue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="Net Value")
    hjp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, default=None, verbose_name="HJP")
    # Dimension foreign key
    company = models.ForeignKey('base.Company', on_delete=models.SET_NULL, verbose_name='Company', null=True, blank=True)
    distributor = models.ForeignKey('supplychain.Distributor', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Distributor")
    branch = models.ForeignKey('supplychain.Branch', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Branch")
    outlet = models.ForeignKey('sales.Outlet', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Outlet")
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, verbose_name="Customer", null=True, blank=True)
    item = models.ForeignKey('supplychain.DistributorItem', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Item")
    uom = models.ForeignKey('base.UoM', on_delete=models.SET_NULL, verbose_name="UoM", null=True, blank=True)


    class Meta:
        db_table = 'analytics"."current_sellingout'  # Points to analytics schema
        verbose_name = "Current Selling Out"
        verbose_name_plural = "Current Selling Out"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]