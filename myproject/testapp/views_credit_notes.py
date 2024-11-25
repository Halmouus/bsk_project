from django.views import View
from django.http import JsonResponse
from .models import Invoice, InvoiceProduct, Product
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CreditNoteDetailsView(View):
    def get(self, request, invoice_id):
        print("Credit note details requested for invoice:", invoice_id) 
        invoice = get_object_or_404(Invoice, id=invoice_id)
        credited_quantities = invoice.get_credited_quantities()
        available_quantities = invoice.get_available_quantities()
        
        products = []
        for item in invoice.products.all():
            products.append({
                'id': str(item.product.id),
                'name': item.product.name,
                'original_quantity': item.quantity,
                'credited_quantity': credited_quantities.get(item.product.id, 0),
                'available_quantity': available_quantities.get(item.product.id, 0),
                'unit_price': float(item.unit_price)
            })

        return JsonResponse({
            'invoice': {
                'ref': invoice.ref,
                'date': invoice.date.strftime('%Y-%m-d'),
                'total_amount': float(invoice.total_amount),
                'credited_amount': float(invoice.total_amount - invoice.net_amount)
            },
            'products': products
        })
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateCreditNoteView(View):
    def post(self, request):
        try:
            print("Received POST request for creating credit note")
            data = json.loads(request.body)
            print("Received data:", data)
            original_invoice = get_object_or_404(Invoice, id=data['original_invoice_id'])
            print("Original Invoice:", original_invoice)

            # Check for duplicate reference
            if Invoice.objects.filter(ref=data['ref']).exists():
                return JsonResponse(
                    {'error': 'Credit note reference already exists'}, 
                    status=400
                )
            
            # Create credit note
            credit_note = Invoice.objects.create(
                type='credit_note',
                original_invoice=original_invoice,
                supplier=original_invoice.supplier,
                ref=data['ref'],
                date=data['date'],
                status='draft'
            )

            # Add products
            for product_data in data['products']:
                product = get_object_or_404(Product, id=product_data['product_id'])
                original_item = original_invoice.products.get(product=product)
                
                InvoiceProduct.objects.create(
                    invoice=credit_note,
                    product=product,
                    quantity=product_data['quantity'],
                    unit_price=original_item.unit_price,
                    reduction_rate=original_item.reduction_rate,
                    vat_rate=original_item.vat_rate
                )

            return JsonResponse({
                'message': 'Credit note created successfully',
                'credit_note_id': str(credit_note.id)
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)