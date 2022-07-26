from decimal import Decimal
from unicodedata import decimal
from accounts.models import Account
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save, post_save
from products.models import Product
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# User = get_user_model()

# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id



ORDER_STATUS_CHOICES = (
    ("created", "Created"),
    ("stale", "Stale"),
    ("paid", "Paid"),
    ("shipped", "Shipped"),
    ("refunded", "Refunded"),

)


class Order(models.Model):
    user = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='created')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True) # automatically datetime object
    inventory_updated = models.BooleanField(default=False)



    def get_absolute_url(self):
        return f"/orders/{self.pk}/download/"

    
    # def get_download_url(self):
    #     return f"/orders/{self.pk}/download/"

    def get_download_url(self):
            view_name = "order:download"
            return reverse(view_name, kwargs={"order_id": self.pk})

    @property
    def is_downloadable(self):
        if not self.product:
            return False
        if self.product.is_digital:
            return True
        return False



    def mark_paid(self, custom_amount=None, save=False):
        paid_amount = self.total
        if custom_amount != None:
            paid_amount = custom_amount
        self.paid = paid_amount
        self.status = "paid"
        # if not self.inventory_updated and self.product:
        #     self.product.remove_item(save=True, count=1)
        #     self.inventory_updated = True
        if save == True:
            self.save()
        return self.paid


    def calculate(self,save=False):
        if not self.product:
            return {}
        subtotal = self.product.price
        tax_rate = Decimal(0.12)
        tax_total = (subtotal * tax_rate)
        tax_total = Decimal("%.2f" %(tax_total))
        total = subtotal + tax_total
        total = Decimal("%.2f" %(total))

        totals = {
            "subtotal": subtotal,
            "tax": tax_total,
            "total": total
        }
        for k,v in totals.items():
            setattr(self, k, v)
            if save == True:
                self.save()
        return self.total

def order_pre_save(sender, instance, *args, **kwargs):
    instance.calculate(save=False)
pre_save.connect(order_pre_save, sender=Order)



