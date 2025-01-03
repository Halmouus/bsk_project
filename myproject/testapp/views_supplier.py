from datetime import timezone
from decimal import Decimal
import traceback
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Invoice, Supplier, get_supplier_balance
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
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


# Get supplier balance
class SupplierBalanceView(View):
    def get(self, request, pk):
        try:
            supplier = get_object_or_404(Supplier, pk=pk)
            balance = get_supplier_balance(supplier)
            
            return JsonResponse({
                'payable': float(balance['payable']),
                'paid': float(balance['paid']),
                'balance': float(balance['balance']),
                'unpaid_invoices_count': balance['invoices_count']
            })
            
        except Exception as e:
            print(f"Error in SupplierBalanceView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': str(e)}, status=400)
        
# Get supplier details
class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'supplier/supplier_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        
        # Get supplier balance info
        balance = get_supplier_balance(supplier)
        context['balance'] = balance
        
        # Get supplier's invoices using same logic as invoice list
        invoices = Invoice.objects.filter(
            supplier=supplier,
            type='invoice'  
        )
        
        # Add all invoice list filters
        filters = {}
        
        # Date Range Filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            invoices = invoices.filter(date__gte=date_from)
        if date_to:
            invoices = invoices.filter(date__lte=date_to)

        # Amount Range Filter  
        amount_min = self.request.GET.get('amount_min')
        amount_max = self.request.GET.get('amount_max')
        if amount_min or amount_max:
            amount_min = Decimal(amount_min if amount_min else '0')
            amount_max = Decimal(amount_max if amount_max else '999999999')
            invoices = invoices.filter(total_amount__gte=amount_min, total_amount__lte=amount_max)

        # Payment Status Filter
        payment_status = self.request.GET.get('payment_status')
        if payment_status:
            invoices = invoices.filter(payment_status=payment_status)

        # Export Status Filter
        export_status = self.request.GET.get('export_status')
        if export_status == 'exported':
            invoices = invoices.filter(exported_at__isnull=False)
        elif export_status == 'not_exported':
            invoices = invoices.filter(exported_at__isnull=True)

        # Status Filters
        has_pending_checks = self.request.GET.get('has_pending_checks')
        if has_pending_checks:
            invoices = invoices.filter(check__status='pending').distinct()

        has_delivered_unpaid = self.request.GET.get('has_delivered_unpaid')
        if has_delivered_unpaid:
            invoices = invoices.filter(check__status='delivered').exclude(check__status='paid').distinct()

        # Credit Note Status
        credit_note_status = self.request.GET.get('credit_note_status')
        if credit_note_status == 'has_credit_notes':
            invoices = invoices.filter(credit_notes__isnull=False).distinct()
        elif credit_note_status == 'no_credit_notes':
            invoices = invoices.filter(credit_notes__isnull=True)
        elif credit_note_status == 'partially_credited':
            invoices = invoices.filter(
                credit_notes__isnull=False,
                payment_status__in=['not_paid', 'partially_paid']
            ).distinct()

        # Overdue Filter
        is_overdue = self.request.GET.get('is_overdue')
        if is_overdue:
            today = timezone.now().date()
            invoices = invoices.filter(
                payment_due_date__lt=today,
                payment_status__in=['not_paid', 'partially_paid']
            )

        context['invoices'] = invoices.order_by('-date').select_related('supplier')
        context['active_filters'] = filters
        return context