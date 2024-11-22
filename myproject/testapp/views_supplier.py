from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Supplier
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = 'supplier/supplier_list.html'
    context_object_name = 'suppliers'

# Create a new Supplier
class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully created."

# Update an existing Supplier
class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    fields = ['name', 'if_code', 'ice_code', 'rc_code', 'rc_center', 'accounting_code', 'is_energy', 'service', 'delay_convention', 'is_regulated', 'regulation_file_path']
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully updated."


# Delete a Supplier
class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'supplier/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoice_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoice_set.count()} invoice(s).')
            return redirect('supplier-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete supplier. It is referenced by one or more invoices.')
            return redirect('supplier-list')
