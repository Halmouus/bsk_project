from datetime import timezone
from decimal import Decimal
import traceback
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .forms import SupplierCreateForm
from .models import Invoice, Supplier, get_supplier_balance
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import ProtectedError
from django.views.generic.edit import DeleteView
from django.contrib import messages
import mimetypes
import os
from django.http import FileResponse
from django.core.files.base import ContentFile
# List all Suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = 'supplier/supplier_list.html'
    context_object_name = 'suppliers'

# Create a new Supplier
class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierCreateForm
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully created."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create_mode'] = True
        return context
        
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle document uploads
        if 'regulation_file' in self.request.FILES:
            try:
                uploaded_file = self.request.FILES['regulation_file']
                self.object.regulation_file.save(
                    uploaded_file.name,
                    uploaded_file,
                    save=True
                )
                print(f"Regulation file saved successfully: {self.object.regulation_file.name}")
            except Exception as e:
                print(f"Error saving regulation file: {str(e)}")
        
        if 'payment_delay_file' in self.request.FILES:
            try:
                uploaded_file = self.request.FILES['payment_delay_file']
                self.object.payment_delay_file.save(
                    uploaded_file.name,
                    uploaded_file,
                    save=True
                )
                print(f"Payment delay file saved successfully: {self.object.payment_delay_file.name}")
            except Exception as e:
                print(f"Error saving payment delay file: {str(e)}")
        
        return response

# Update an existing Supplier
class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierCreateForm  # Use the custom form
    template_name = 'supplier/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier successfully updated."
    
    def form_valid(self, form):
        print("\n=== SupplierUpdateView.form_valid ===")
        print(f"Form data: {form.cleaned_data}")
        print(f"Files: {self.request.FILES}")
        print(f"POST data: {self.request.POST}")
        response = super().form_valid(form)
        
        # Handle document uploads and deletions
        if 'delete_regulation_file' in self.request.POST and self.request.POST.get('delete_regulation_file') == 'true':
            try:
                if self.object.regulation_file:
                    self.object.regulation_file.delete()
                    self.object.regulation_file = None
                    print(f"Regulation file deleted successfully")
            except Exception as e:
                print(f"Error deleting regulation file: {str(e)}")
        
        if 'delete_payment_delay_file' in self.request.POST and self.request.POST.get('delete_payment_delay_file') == 'true':
            try:
                if self.object.payment_delay_file:
                    self.object.payment_delay_file.delete()
                    self.object.payment_delay_file = None
                    print(f"Payment delay file deleted successfully")
            except Exception as e:
                print(f"Error deleting payment delay file: {str(e)}")
        
        # Handle new document uploads
        if 'regulation_file' in self.request.FILES:
            try:
                # Delete old file if exists and not already deleted
                if self.object.regulation_file:
                    self.object.regulation_file.delete(save=False)
                
                uploaded_file = self.request.FILES['regulation_file']
                self.object.regulation_file.save(
                    uploaded_file.name,
                    uploaded_file,
                    save=True
                )
                print(f"Regulation file saved successfully: {self.object.regulation_file.name}")
            except Exception as e:
                print(f"Error saving regulation file: {str(e)}")
        
        if 'payment_delay_file' in self.request.FILES:
            try:
                # Delete old file if exists and not already deleted
                if self.object.payment_delay_file:
                    self.object.payment_delay_file.delete(save=False)
                
                uploaded_file = self.request.FILES['payment_delay_file']
                self.object.payment_delay_file.save(
                    uploaded_file.name,
                    uploaded_file,
                    save=True
                )
                print(f"Payment delay file saved successfully: {self.object.payment_delay_file.name}")
            except Exception as e:
                print(f"Error saving payment delay file: {str(e)}")
        
        # Save changes
        self.object.save()
        return response

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


class SupplierDocumentView(View):
    def get(self, request, pk, document_type):
        print(f"\n=== SupplierDocumentView.get ===")
        print(f"pk: {pk}, document_type: {document_type}")
        
        supplier = get_object_or_404(Supplier, pk=pk)
        print(f"Found supplier: {supplier.name}")
        
        # Determine which document to serve
        if document_type == 'regulation':
            document = supplier.regulation_file
            document_name = "Regulation File"
            print(f"Regulation file: {document}")
        elif document_type == 'payment_delay':
            document = supplier.payment_delay_file
            document_name = "Payment Delay File"
            print(f"Payment delay file: {document}")
        else:
            print(f"Invalid document type: {document_type}")
            return JsonResponse({"error": "Invalid document type"}, status=400)
        
        if not document:
            print(f"No {document_name} found for this supplier")
            return JsonResponse({"error": f"No {document_name} found for this supplier"}, status=404)
        
        # Open the file and return it
        try:
            file_path = document.path
            print(f"Document path: {file_path}")
            
            # Check if file exists
            import os
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return JsonResponse({"error": "File not found on disk"}, status=404)
            
            content_type, _ = mimetypes.guess_type(file_path)
            print(f"Content type: {content_type}")
            
            if not content_type:
                content_type = 'application/octet-stream'
                
            # Get filename from document path
            filename = os.path.basename(document.name)
            print(f"Filename: {filename}")
                
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            # Add cache control headers
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        except FileNotFoundError:
            print(f"Document file not found: {file_path}")
            return JsonResponse({"error": "Document file not found"}, status=404)
        except Exception as e:
            print(f"Error serving document: {str(e)}")
            return JsonResponse({"error": f"Error: {str(e)}"}, status=500)