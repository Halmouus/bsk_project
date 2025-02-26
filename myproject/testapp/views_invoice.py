from django.urls import reverse_lazy
from django.db import models
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import INVOICE_STATUS, INVOICE_TYPES, CheckAllocation, ContractInvoice, DeliveryNote, DirectDebit, ForecastStatement, Invoice, InvoiceProduct, Product, ExportRecord, Check, ReceptionNote, Supplier
from .forms import InvoiceCreateForm, InvoiceUpdateForm  # Import the custom form here
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q,F, Case, When, DecimalField, Subquery, Sum, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.template.loader import render_to_string
from django.db.models.sql.where import EmptyResultSet
from django.conf import settings



@method_decorator(csrf_exempt, name='dispatch')
class AddProductToInvoiceView(View):
    def post(self, request):
        invoice_id = request.POST.get('invoice_id')
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate', 0)  # Add default value
        expense_code = request.POST.get('expense_code')

        try:
            # Fetch the invoice and product
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            product = get_object_or_404(Product, pk=product_id)

            # Create a new InvoiceProduct entry
            invoice_product = InvoiceProduct.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                vat_rate=vat_rate,
                reduction_rate=reduction_rate
            )

            # Success response
            return JsonResponse({"message": "Product added successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# List all Invoices
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        print("\n=== Getting Invoice Queryset ===")
        print("GET Parameters:", self.request.GET)

        # Start with base queryset
        queryset = Invoice.objects.select_related(
            'supplier'
        ).prefetch_related(
            'products',
            'delivery_notes',
            'reception_notes',
            'credit_notes'
        )

        filters = {}
        try:
            # Date Range Filter
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            if date_from:
                print(f"Adding date_from filter: {date_from}")
                filters['date__gte'] = date_from
            if date_to:
                print(f"Adding date_to filter: {date_to}")
                filters['date__lte'] = date_to

            # Amount Range Filter
            amount_min = self.request.GET.get('amount_min')
            amount_max = self.request.GET.get('amount_max')
            if amount_min:
                print(f"Adding min_amount filter: {amount_min}")
                filters['total_amount__gte'] = amount_min
            if amount_max:
                print(f"Adding max_amount filter: {amount_max}")
                filters['total_amount__lte'] = amount_max

            # Supplier Filter
            supplier_id = self.request.GET.get('supplier_id')
            supplier_text = self.request.GET.get('supplier')
            if supplier_id:
                queryset = queryset.filter(supplier_id=supplier_id)
            elif supplier_text:
                queryset = queryset.filter(supplier__name__icontains=supplier_text)

            # Payment Status Filter
            payment_status = self.request.GET.get('payment_status')
            if payment_status:
                print(f"Adding payment status filter: {payment_status}")
                filters['payment_status'] = payment_status

            # Invoice Type Filter
            invoice_type = self.request.GET.get('invoice_type')
            if invoice_type:
                print(f"Adding invoice type filter: {invoice_type}")
                filters['invoice_type'] = invoice_type

            # Document Status Filter
            doc_status = self.request.GET.get('doc_status')
            if doc_status:
                print(f"Adding document status filter: {doc_status}")
                filters['doc_status'] = doc_status

            # Export Status Filter
            export_status = self.request.GET.get('export_status')
            if export_status:
                print(f"Adding export status filter: {export_status}")
                if export_status == 'exported':
                    filters['exported_at__isnull'] = False
                elif export_status == 'not_exported':
                    filters['exported_at__isnull'] = True

            # Product Filter
            product_id = self.request.GET.get('product_id')
            product_text = self.request.GET.get('product')
            if product_id:
                queryset = queryset.filter(products__product_id=product_id)
            elif product_text:
                queryset = queryset.filter(products__product__name__icontains=product_text)
                
            # Credit Note Status Filter
            credit_note_status = self.request.GET.get('credit_note_status')
            if credit_note_status:
                print(f"Adding credit note status filter: {credit_note_status}")
                if credit_note_status == 'has_credit_notes':
                    filters['credit_notes__isnull'] = False
                elif credit_note_status == 'no_credit_notes':
                    filters['credit_notes__isnull'] = True
                elif credit_note_status == 'partially_credited':
                    filters.update({
                        'credit_notes__isnull': False,
                        'payment_status__in': ['not_paid', 'partially_paid']
                    })

            # Due Date Range Filter
            due_date_from = self.request.GET.get('due_date_from')
            due_date_to = self.request.GET.get('due_date_to')
            if due_date_from:
                print(f"Adding due_date_from filter: {due_date_from}")
                filters['payment_due_date__gte'] = due_date_from
            if due_date_to:
                print(f"Adding due_date_to filter: {due_date_to}")
                filters['payment_due_date__lte'] = due_date_to

            # Delivery Note Reference Filter
            delivery_note_ref = self.request.GET.get('delivery_note_ref')
            if delivery_note_ref:
                print(f"Adding delivery note filter: {delivery_note_ref}")
                filters['delivery_notes__ref__icontains'] = delivery_note_ref

            # Reception Note Reference Filter
            reception_note_ref = self.request.GET.get('reception_note_ref')
            if reception_note_ref:
                print(f"Adding reception note filter: {reception_note_ref}")
                filters['reception_notes__ref__icontains'] = reception_note_ref

            # Archive Index Range Filter
            index_min = self.request.GET.get('index_min')
            index_max = self.request.GET.get('index_max')
            if index_min:
                print(f"Adding min index filter: {index_min}")
                filters['special_index__gte'] = index_min
            if index_max:
                print(f"Adding max index filter: {index_max}")
                filters['special_index__lte'] = index_max

            # Overdue Filter
            if self.request.GET.get('is_overdue'):
                print("Adding overdue filter")
                filters.update({
                    'payment_due_date__lt': timezone.now().date(),
                    'payment_status__in': ['not_paid', 'partially_paid']
                })

            # Energy Supplier Filter
            if self.request.GET.get('is_energy'):
                print("Adding energy supplier filter")
                filters['supplier__is_energy'] = True

            # Apply all filters
            print("\nApplying filters:", filters)
            queryset = queryset.filter(**filters)

            # Handle special cases that need distinct()
            if any(key in filters for key in ['credit_notes__isnull', 'delivery_notes__ref__icontains', 'reception_notes__ref__icontains']):
                queryset = queryset.distinct()

        except Exception as e:
            print(f"Error applying filters: {str(e)}")
            import traceback
            traceback.print_exc()

        print(f"\nFinal query: {queryset.query}")
        total_count = queryset.count()
        print(f"Total results: {total_count}")

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        print("\n=== Getting Context Data ===")
        context = super().get_context_data(**kwargs)
        
        # Track active filters for display
        active_filters = {}
        
        try:
            # Supplier Filter
            supplier_id = self.request.GET.get('supplier')
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                    active_filters['Supplier'] = supplier.name
                    context['initial_supplier'] = {
                        'id': supplier_id,
                        'text': supplier.name
                    }
                    print(f"Added supplier filter: {supplier.name}")
                except Supplier.DoesNotExist:
                    print(f"Supplier not found: {supplier_id}")

            # Date Range
            if self.request.GET.get('date_from') or self.request.GET.get('date_to'):
                date_range = []
                if self.request.GET.get('date_from'):
                    date_range.append(f"From {self.request.GET.get('date_from')}")
                if self.request.GET.get('date_to'):
                    date_range.append(f"To {self.request.GET.get('date_to')}")
                active_filters['Date'] = ' - '.join(date_range)

            # Amount Range
            if self.request.GET.get('amount_min') or self.request.GET.get('amount_max'):
                amount_range = []
                if self.request.GET.get('amount_min'):
                    amount_range.append(f"Min {self.request.GET.get('amount_min')}")
                if self.request.GET.get('amount_max'):
                    amount_range.append(f"Max {self.request.GET.get('amount_max')}")
                active_filters['Amount'] = ' - '.join(amount_range)

            # Payment Status
            payment_status = self.request.GET.get('payment_status')
            if payment_status:
                status_display = dict(Invoice.PAYMENT_STATUS_CHOICES).get(payment_status)
                if status_display:
                    active_filters['Payment Status'] = status_display

            # Export Status
            export_status = self.request.GET.get('export_status')
            if export_status:
                active_filters['Export Status'] = 'Exported' if export_status == 'exported' else 'Not Exported'

            # Invoice Type
            invoice_type = self.request.GET.get('invoice_type')
            if invoice_type:
                type_display = dict(INVOICE_TYPES).get(invoice_type)
                if type_display:
                    active_filters['Type'] = type_display

            # Document Status
            doc_status = self.request.GET.get('doc_status')
            if doc_status:
                status_display = dict(INVOICE_STATUS).get(doc_status)
                if status_display:
                    active_filters['Document Status'] = status_display

            # Other boolean filters
            if self.request.GET.get('is_overdue'):
                active_filters['Status'] = 'Overdue'
            if self.request.GET.get('is_energy'):
                active_filters['Supplier Type'] = 'Energy'

            print("\nActive Filters:", active_filters)
            context['active_filters'] = active_filters
            context['total_results'] = self.get_queryset().count()

        except Exception as e:
            print(f"Error preparing context: {str(e)}")
            import traceback
            traceback.print_exc()

        return context

    def render_to_response(self, context, **response_kwargs):
        """Handle both HTML and AJAX responses"""
        print("\n=== Rendering Response ===")
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        print(f"Request is AJAX: {is_ajax}")
        
        if is_ajax:
            try:
                filtered_invoices = self.get_queryset()  # Get filtered queryset
                print(f"Filtered invoices count: {filtered_invoices.count()}")
                print("First invoice:", filtered_invoices.first())  # Debug

                rendered_html = render_to_string(
                    'invoice/partials/invoice_table.html',
                    {
                        'invoices': filtered_invoices,
                        'request': self.request,
                        'INVOICE_TYPES': INVOICE_TYPES,
                        'INVOICE_STATUS': INVOICE_STATUS,
                    },
                    request=self.request
                )
                # Add this debug line
                print("Template context:", {
                    'invoices_count': filtered_invoices.count(),
                    'first_invoice_ref': filtered_invoices.first().ref if filtered_invoices.exists() else None,
                    'has_INVOICE_TYPES': 'INVOICE_TYPES' in locals(),
                    'has_INVOICE_STATUS': 'INVOICE_STATUS' in locals()
                })



                print("Length of rendered HTML:", len(rendered_html))

                data = {
                    'html': rendered_html,
                    'total_results': filtered_invoices.count(),
                    'active_filters': context.get('active_filters', {})
                }
                return JsonResponse(data)
                
            except Exception as e:
                print(f"Error preparing AJAX response: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)

        return super().render_to_response(context, **response_kwargs)
    
# Create a new Invoice
class InvoiceCreateView(SuccessMessageMixin, CreateView):
    model = Invoice
    form_class = InvoiceUpdateForm  # Use the custom form here
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully created."

    def form_valid(self, form):
        response = super().form_valid(form)
        # We may want to pass the newly created invoice to the next page or modal
        return response

    def get_form_class(self):
        print("Using CREATE VIEW")  # Debug print
        return InvoiceCreateForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()  # Add all products to the context for dropdown population
        return data

# Update an existing Invoice
class InvoiceUpdateView(SuccessMessageMixin, UpdateView):
    model = Invoice
    form_class = InvoiceUpdateForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully updated."

    def get_initial(self):
        initial = super().get_initial()
        if self.object and self.object.date:
            # Ensure date is formatted correctly for the form
            initial['date'] = self.object.date.strftime('%Y-%m-%d')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add products formset back
        if self.request.POST:
            context['products'] = InvoiceProductInlineFormset(
                self.request.POST, 
                instance=self.object
            )
        else:
            context['products'] = InvoiceProductInlineFormset(
                instance=self.object,
                queryset=InvoiceProduct.objects.filter(invoice=self.object)
            )
        
        # Add debug info
        context['debug'] = settings.DEBUG
        return context

    def get_form_class(self):
        print("Using UPDATE VIEW")  # Debug print
        return InvoiceUpdateForm
    
    def form_valid(self, form):
        print("Entering form_valid")
        print("Form data:", form.cleaned_data)
        context = self.get_context_data()
        products = context['products']
        print("Form valid:", form.is_valid())
        print("Products valid:", products.is_valid())
        
        if not products.is_valid():
            print("Products errors:", products.errors)
            print("Non-form errors:", products.non_form_errors())
            
        if form.is_valid() and products.is_valid():
            print("Both form and products are valid")
            self.object = form.save()
            products.instance = self.object
            products.save()
            print("Save completed")
            return super().form_valid(form)
            
        print("Form validation failed")
        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.payment_status == 'paid':
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been paid and cannot be edited!', 
                         extra_tags='danger')
            return redirect('invoice-list')
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be edited!', 
                         extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)

# Delete an Invoice
class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    success_message = "Invoice successfully deleted."

    def dispatch(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.exported_at:
            messages.error(request, '<i class="fas fa-lock"></i> This invoice has been exported and cannot be deleted!', extra_tags='danger')
            return redirect('invoice-list')
        return super().dispatch(request, *args, **kwargs)


InvoiceProductInlineFormset = inlineformset_factory(
    Invoice, InvoiceProduct,
    fields=['product', 'quantity', 'unit_price', 'reduction_rate', 'vat_rate'],
    extra=1,  # Number of empty forms to display
    can_delete=True
)

# Invoice details view for AJAX request
class InvoiceDetailsView(View):
    def get(self, request):
        invoice_id = request.GET.get('invoice_id')
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            products = invoice.products.all()
            product_data = [
                {
                    'name': product.product.name,
                    'unit_price': f"{product.unit_price:,.2f}",
                    'quantity': product.quantity,
                    'vat_rate': f"{product.vat_rate}%",  # Add VAT Rate
                    'reduction_rate': product.reduction_rate,
                    'raw_price': f"{product.quantity * product.unit_price * (1 - product.reduction_rate / 100):,.2f}",
                } for product in products
            ]

            # Calculate total raw amount
            total_raw_amount = sum([
                product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                for product in products
            ])

            # Calculate subtotal per VAT rate
            vat_subtotals = {}
            for product in products:
                vat_rate = product.vat_rate
                raw_price = product.quantity * product.unit_price * (1 - product.reduction_rate / 100)
                if vat_rate not in vat_subtotals:
                    vat_subtotals[vat_rate] = 0
                vat_subtotals[vat_rate] += raw_price * (vat_rate / 100)

            response_data = {
                'products': product_data,
                'total_raw_amount': f"{total_raw_amount:,.2f}",  # Add Total Raw Amount
                'vat_subtotals': [{'vat_rate': f"{rate}%", 'subtotal': f"{subtotal:,.2f}"} for rate, subtotal in vat_subtotals.items()],  # Add VAT Subtotals
                'total_vat': f"{invoice.total_tax_amount:,.2f}",
                'total_amount': f"{invoice.total_amount:,.2f}",
            }
            return JsonResponse(response_data)
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'Invoice not found'}, status=404)

# Product Autocomplete View
def product_autocomplete(request):
    query = request.GET.get('term', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(fiscal_label__icontains=query)
    )[:10]
    
    product_list = [{
        "label": f"{product.name} ({product.fiscal_label})",
        "value": product.id
    } for product in products]
    
    if not products:
        product_list.append({
            "label": f"Create new product: {query}",
            "value": "new"
        })
        
    return JsonResponse(product_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class EditProductInInvoiceView(View):
    def get(self, request, pk):
        """
        Handles loading the product data for editing.
        """
        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)
            # Prepare product data to return
            product_data = {
                'product': invoice_product.product.name,
                'product_name': invoice_product.product.name,
                'quantity': invoice_product.quantity,
                'unit_price': float(invoice_product.unit_price),
                'vat_rate': float(invoice_product.vat_rate),
                'reduction_rate': float(invoice_product.reduction_rate),
                'expense_code': invoice_product.product.expense_code,
                'fiscal_label': invoice_product.product.fiscal_label 
            }
            return JsonResponse(product_data, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        """
        Handles updating the product information.
        """
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        vat_rate = request.POST.get('vat_rate')
        reduction_rate = request.POST.get('reduction_rate')

        try:
            # Fetch the existing InvoiceProduct
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Update the fields with the provided data
            invoice_product.quantity = quantity
            invoice_product.unit_price = unit_price
            invoice_product.vat_rate = vat_rate
            invoice_product.reduction_rate = reduction_rate
            invoice_product.save()

            # Success response
            return JsonResponse({"message": "Product updated successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        """
        Handles deleting the product from the invoice.
        """
        try:
            # Fetch the InvoiceProduct instance
            invoice_product = get_object_or_404(InvoiceProduct, pk=pk)

            # Delete the instance
            invoice_product.delete()

            # Success response
            return JsonResponse({"message": "Product deleted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportInvoicesView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_export_invoice')

    def generate_excel(self, invoices):
        wb = Workbook()
        ws = wb.active
        ws.title = "Accounting Entries"

        # Define styles
        header_style = {
            'font': Font(bold=True, color='FFFFFF'),
            'fill': PatternFill(start_color='344960', end_color='344960', fill_type='solid'),
            'alignment': Alignment(horizontal='center', vertical='center'),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }

        # Set headers
        headers = ['Date', 'Label', 'Debit', 'Credit', 'Account Code', 'Reference', 'Journal', 'Counterpart']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_style['font']
            cell.fill = header_style['fill']
            cell.alignment = header_style['alignment']
            cell.border = header_style['border']

        # Set column widths
        ws.column_dimensions['A'].width = 12  # Date
        ws.column_dimensions['B'].width = 40  # Label
        ws.column_dimensions['C'].width = 15  # Debit
        ws.column_dimensions['D'].width = 15  # Credit
        ws.column_dimensions['E'].width = 15  # Account Code
        ws.column_dimensions['F'].width = 15  # Reference
        ws.column_dimensions['G'].width = 10  # Journal
        ws.column_dimensions['H'].width = 15  # Counterpart

        current_row = 2
        for invoice in invoices:
            entries = invoice.get_accounting_entries()
            for entry in entries:
                ws.cell(row=current_row, column=1, value=entry['date'].strftime('%d/%m/%Y'))
                ws.cell(row=current_row, column=2, value=entry['label'])
                ws.cell(row=current_row, column=3, value=entry['debit'])
                ws.cell(row=current_row, column=4, value=entry['credit'])
                ws.cell(row=current_row, column=5, value=entry['account_code'])
                ws.cell(row=current_row, column=6, value=entry['reference'])
                ws.cell(row=current_row, column=7, value=entry['journal'])
                ws.cell(row=current_row, column=8, value=entry['counterpart'])

                # Style number cells
                for col in [3, 4]:  # Debit and Credit columns
                    cell = ws.cell(row=current_row, column=col)
                    cell.number_format = '# ##0.00'
                    cell.alignment = Alignment(horizontal='right')

                current_row += 1

        return wb

    def post(self, request):
        try:
            data = json.loads(request.body)
            invoice_ids = data.get('invoice_ids', [])
            invoices = Invoice.objects.filter(id__in=invoice_ids, exported_at__isnull=True)

            if not invoices:
                return JsonResponse({'error': 'No valid invoices to export'}, status=400)

            # Generate Excel file
            wb = self.generate_excel(invoices)

            # Create export record
            export_record = ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'accounting_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )

            # Mark invoices as exported
            for invoice in invoices:
                invoice.exported_at = timezone.now()
                invoice.export_history.add(export_record)
                invoice.save()

            # Prepare response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{export_record.filename}"'
            wb.save(response)

            return response

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UnexportInvoiceView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('testapp.can_unexport_invoice')

    def post(self, request, invoice_id):
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            if not invoice.exported_at:
                return JsonResponse({'error': 'Invoice is not exported'}, status=400)

            # Create export record for the unexport action
            ExportRecord.objects.create(
                exported_by=request.user,
                filename=f'unexport_{invoice.ref}_{timezone.now().strftime("%Y%m%d_%H%M%S")}',
                note=f'Unexported by {request.user.username}'
            )

            # Clear export date
            invoice.exported_at = None
            invoice.save()

            return JsonResponse({'message': 'Invoice successfully unexported'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class InvoicePaymentDetailsView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        payment_details = invoice.get_payment_details()
        
        # Get direct checks
        direct_checks = Check.objects.filter(
            cause=invoice
        ).select_related('checker__bank_account')
        
        # Get allocated checks
        allocations = CheckAllocation.objects.filter(
            invoice_id=invoice.id
        ).select_related('payment__checker__bank_account')
        

        # Combine both types of checks
        check_details = []
        
        # Add direct checks
        for check in direct_checks:
            check_details.append({
                'id': str(check.id),
                'type': 'direct',
                'payment_type': 'LCN' if check.checker.type == 'LCN' else 'Check',
                'reference': f"{check.checker.bank_account.bank}-{check.position}",
                'amount': float(check.amount),
                'status': check.status,
                'created_at': check.creation_date.strftime('%Y-%m-%d'),
                'delivered_at': check.delivered_at.strftime('%Y-%m-%d') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%d') if check.paid_at else None,
            })

        # Add allocated checks
        for allocation in allocations:
            check_details.append({
                'id': str(allocation.payment.id),
                'type': 'allocation',
                'payment_type': 'LCN' if allocation.payment.checker.type == 'LCN' else 'Check',
                'reference': f"{allocation.payment.checker.bank_account.bank}-{allocation.payment.position}",
                'total_amount': float(allocation.payment.amount),
                'allocated_amount': float(allocation.amount),
                'status': allocation.payment.status,
                'created_at': allocation.payment.creation_date.strftime('%Y-%m-%d'),
                'delivered_at': allocation.payment.delivered_at.strftime('%Y-%m-%d') if allocation.payment.delivered_at else None,
                'paid_at': allocation.payment.paid_at.strftime('%Y-%m-%d') if allocation.payment.paid_at else None,
            })

        cash_payments = invoice.cash_payments.all()
        print(f"\nFound {cash_payments.count()} cash payments")
        for payment in cash_payments:
            check_details.append({
                'id': str(payment.id),
                'type': 'cash',
                'payment_type': 'Cash',
                'reference': payment.reference,
                'amount': float(payment.amount),
                'status': 'paid',
                'created_at': payment.payment_date.strftime('%Y-%m-%d'),
                'delivered_at': payment.payment_date.strftime('%Y-%m-%d'),
                'paid_at': payment.payment_date.strftime('%Y-%m-%d'),
            })
        
        # Get direct debit records if this is a contract invoice
        contract_invoice = ContractInvoice.objects.filter(invoice=invoice).first()
        if contract_invoice:
            print("\n=== Processing Contract Invoice Payment Details ===")
            print(f"Contract Invoice ID: {contract_invoice.id}")
            
            direct_debits = DirectDebit.objects.filter(
                invoice=contract_invoice
            ).select_related('bank_account')
            
            print(f"Found {direct_debits.count()} direct debits")
            
            # Convert both numbers to Decimal
            payment_details['total_amount'] = Decimal(str(payment_details['total_amount']))
            payment_details['paid_amount'] = Decimal(str(payment_details['paid_amount']))
            
            for debit in direct_debits:
                if debit.status == DirectDebit.PROCESSED:
                    payment_details['paid_amount'] += debit.amount
                    print(f"Added paid amount: {debit.amount}")
                    print(f"New total paid amount: {payment_details['paid_amount']}")
            
            # Recalculate remaining_to_pay after updating paid_amount
            payment_details['remaining_to_pay'] = payment_details['total_amount'] - payment_details['paid_amount']
            
            payment_details['direct_debits'] = [{
                'date': debit.due_date,
                'bank': f"{debit.bank_account.bank} - {debit.bank_account.account_number}",
                'amount': float(debit.amount),
                'status': debit.get_status_display(),
                'processed_date': debit.processed_date,
                'rejection_cause': debit.get_rejection_cause_display() if debit.rejection_cause else None,
                'rejection_date': debit.rejection_date,
                'rejection_note': debit.rejection_note
            } for debit in direct_debits]
            
            # Calculate percentage with Decimals, then convert to float for JSON
            payment_details['payment_percentage'] = float(
                (payment_details['paid_amount'] / payment_details['total_amount']) * 100
                if payment_details['total_amount'] else 0
            )
            
            print(f"Updated payment details: {payment_details}")
                
            # Add direct debits to check_details
            for debit in direct_debits:
                check_details.append({
                    'id': str(debit.id),
                    'type': 'direct_debit',
                    'payment_type': 'Direct Debit',
                    'reference': f"DOM/{debit.contract.reference}/{debit.due_date.strftime('%Y%m')}",
                    'amount': float(debit.amount),
                    'status': debit.status,
                    'created_at': debit.due_date.strftime('%Y-%m-%d'),
                    'paid_at': debit.processed_date.strftime('%Y-%m-%d') if debit.processed_date else None,
                    'bank': debit.bank_account.bank,
                    'account': debit.bank_account.account_number
                })

        return JsonResponse({
            'payment_details': payment_details,
            'checks': check_details
        })

class InvoiceAccountingSummaryView(View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Get original entries
        original_entries = invoice.get_accounting_entries()
        
        # Get credit note entries
        credit_note_entries = []
        credit_notes_total = 0
        for credit_note in invoice.credit_notes.all():
            entries = credit_note.get_accounting_entries()
            credit_note_entries.extend(entries)
            credit_notes_total += credit_note.total_amount
            
        return JsonResponse({
            'original_entries': original_entries,
            'credit_note_entries': credit_note_entries,
            'totals': {
                'original': float(invoice.total_amount),
                'credit_notes': float(-credit_notes_total),
                'net': float(invoice.net_amount)
            }
        })

@method_decorator(csrf_exempt, name='dispatch')
class LinkDeliveryNoteView(View):
    def post(self, request):
        print("\n=== Linking Delivery Note ===")
        try:
            data = json.loads(request.body)
            invoice = get_object_or_404(Invoice, id=data.get('invoice_id'))
            note = get_object_or_404(DeliveryNote, id=data.get('note_id'))
            
            print(f"Invoice: {invoice.ref}")
            print(f"Note: {note.ref}")

            # Check if note is already linked to another invoice
            if note.invoices.exists():
                print("Note already linked to an invoice")
                return JsonResponse({
                    'success': False, 
                    'error': 'This delivery note is already linked to another invoice'
                })

            invoice.delivery_notes.add(note)
            print("Successfully linked note to invoice")
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"Error linking note: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class UnlinkDeliveryNoteView(View):
    def post(self, request):
        print("\n=== Unlinking Delivery Note ===")
        try:
            data = json.loads(request.body)
            invoice = get_object_or_404(Invoice, id=data.get('invoice_id'))
            note = get_object_or_404(DeliveryNote, id=data.get('note_id'))
            
            print(f"Invoice: {invoice.ref}")
            print(f"Note: {note.ref}")

            invoice.delivery_notes.remove(note)
            print("Successfully unlinked note from invoice")
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"Error unlinking note: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class LinkReceptionNoteView(View):
    def post(self, request):
        print("\n=== Linking Reception Note ===")
        try:
            data = json.loads(request.body)
            invoice = get_object_or_404(Invoice, id=data.get('invoice_id'))
            note = get_object_or_404(ReceptionNote, id=data.get('note_id'))
            
            print(f"Invoice: {invoice.ref}")
            print(f"Note: {note.ref}")

            # Check if note is already linked to another invoice
            if note.invoices.exists():
                print("Note already linked to an invoice")
                return JsonResponse({
                    'success': False, 
                    'error': 'This reception note is already linked to another invoice'
                })

            invoice.reception_notes.add(note)
            print("Successfully linked note to invoice")
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"Error linking note: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class UnlinkReceptionNoteView(View):
    def post(self, request):
        print("\n=== Unlinking Reception Note ===")
        try:
            data = json.loads(request.body)
            invoice = get_object_or_404(Invoice, id=data.get('invoice_id'))
            note = get_object_or_404(ReceptionNote, id=data.get('note_id'))
            
            print(f"Invoice: {invoice.ref}")
            print(f"Note: {note.ref}")

            invoice.reception_notes.remove(note)
            print("Successfully unlinked note from invoice")
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"Error unlinking note: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })