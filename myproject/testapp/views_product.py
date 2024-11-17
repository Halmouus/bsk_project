from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product
from django.contrib.messages.views import SuccessMessageMixin

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."