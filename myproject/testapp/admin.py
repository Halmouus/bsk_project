from django.contrib import admin
from .models import item, Supplier, Product, Invoice, InvoiceProduct

# Register your models here.
admin.site.register(item)  # Test model
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(InvoiceProduct)
