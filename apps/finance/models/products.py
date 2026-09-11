from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models.abstracts import GenericAbstract
from apps.supplychain.models.distributions import Distributor, DistributorItem
from django.utils.text import slugify

class ItemPrice(GenericAbstract):
    code = models.CharField(max_length=50, blank=True, unique=True, verbose_name="Code")
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Distributor")
    distitem = models.ForeignKey(DistributorItem, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Distributor Item")
    salestype = models.ForeignKey('sales.SalesType', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Type")
    hna = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="HNA", null=True, blank=True)
    hjp = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="HJP", null=True, blank=True)
    pct_pm = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="PM %", null=True, blank=True)
    pct_advdisc = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Adv. Disc. %", null=True, blank=True)
    effective = models.DateField(null=True, blank=True, verbose_name= "Effective")
    priceuom = models.ForeignKey('base.UoM', on_delete=models.SET_NULL, default="", null=True, blank=True, verbose_name = "Price UOM",)
    conversionsize = models.IntegerField(null=True, blank=True, verbose_name = "Conversion Size")

    class Meta:
        verbose_name = "Item Price"
        verbose_name_plural = "Item Prices"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def clean(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        qs = ItemPrice.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        while qs.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug  # ✅ Set before validation happens

    def save(self, *args, **kwargs):
        # Generate the code if it is not manually set
        if not self.code:
            self.code = f"{self.distributor.code} {self.salestype.code} {self.distitem.code} {self.effective.year}{self.effective.month:02d}{self.effective.day:02d}"
        self.full_clean()  # ✅ call clean() before saving
        super().save(*args, **kwargs)