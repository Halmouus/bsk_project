from django.forms import ValidationError
from django.views import View
from django.views.generic import ListView
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import json

from .models import Contract, ContractProduct, Supplier, Product, ContractInvoice

class ContractListView(ListView):
    model = Contract
    template_name = 'contract/contract_list.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters if any
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        supplier = self.request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(reference__icontains=search)

        return queryset.select_related('supplier')

class ContractFilterView(View):
    def get(self, request):
        queryset = Contract.objects.all()
        
        # Apply filters
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        supplier = request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
            
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(reference__icontains=search)

        html = render_to_string(
            'contract/partials/contracts_table.html',
            {'contracts': queryset},
            request=request
        )
        
        return JsonResponse({'html': html})

class ContractCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create contract
                contract = Contract.objects.create(
                    reference=data['reference'],
                    supplier_id=data['supplier_id'],
                    start_date=data['start_date'],
                    end_date=data.get('end_date'),
                    is_indefinite=data.get('is_indefinite', False),
                    periodicity=data['periodicity'],
                    generation_day=data['generation_day']
                )
                
                # Add products
                for product_data in data['products']:
                    ContractProduct.objects.create(
                        contract=contract,
                        product_id=product_data['product_id'],
                        quantity=product_data['quantity'],
                        unit_price=product_data['unit_price'],
                        reduction_rate=product_data.get('reduction_rate', 0)
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contract created successfully',
                    'id': str(contract.id)
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ContractUpdateView(View):
    def get(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        products = [{
            'id': str(p.id),
            'product_id': str(p.product_id),
            'product_name': p.product.name,
            'quantity': str(p.quantity),
            'unit_price': str(p.unit_price),
            'reduction_rate': str(p.reduction_rate)
        } for p in contract.products.all()]
        
        return JsonResponse({
            'id': str(contract.id),
            'reference': contract.reference,
            'supplier_id': str(contract.supplier_id),
            'supplier_name': contract.supplier.name,
            'start_date': contract.start_date.isoformat(),
            'end_date': contract.end_date.isoformat() if contract.end_date else None,
            'is_indefinite': contract.is_indefinite,
            'periodicity': contract.periodicity,
            'generation_day': contract.generation_day,
            'status': contract.status,
            'products': products
        })

    def post(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Update contract fields
                contract.reference = data['reference']
                contract.supplier_id = data['supplier_id']
                contract.start_date = data['start_date']
                contract.end_date = data.get('end_date')
                contract.is_indefinite = data.get('is_indefinite', False)
                contract.periodicity = data['periodicity']
                contract.generation_day = data['generation_day']
                contract.save()
                
                # Update products
                contract.products.all().delete()
                for product_data in data['products']:
                    ContractProduct.objects.create(
                        contract=contract,
                        product_id=product_data['product_id'],
                        quantity=product_data['quantity'],
                        unit_price=product_data['unit_price'],
                        reduction_rate=product_data.get('reduction_rate', 0)
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contract updated successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ContractDeleteView(View):
    def post(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            
            # Only allow deletion of draft contracts or those without invoices
            if contract.status != 'draft' and contract.contractinvoice_set.exists():
                raise ValidationError("Cannot delete contract with existing invoices")
                
            contract.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Contract deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ContractGenerateInvoicesView(View):
    def post(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            up_to_date = request.POST.get('up_to_date')
            
            if up_to_date:
                up_to_date = timezone.datetime.strptime(up_to_date, '%Y-%m-%d').date()
            else:
                up_to_date = timezone.now().date()
                
            invoices = contract.generate_missing_invoices(up_to_date)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Generated {len(invoices)} invoices',
                'invoices': [{
                    'id': str(inv.id),
                    'ref': inv.ref,
                    'date': inv.date.isoformat(),
                    'amount': str(inv.total_amount)
                } for inv in invoices]
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ContractTerminateView(View):
    def post(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            data = json.loads(request.body)
            
            contract.status = Contract.STATUS_TERMINATED
            contract.cancellation_date = data['cancellation_date']
            contract.cancellation_reason = data.get('cancellation_reason', '')
            contract.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Contract terminated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        
class ContractActivateView(View):
    def post(self, request, pk):
        print("\n=== Contract Activation Started ===")
        print(f"Activating contract {pk}")
        try:
            contract = get_object_or_404(Contract, pk=pk)
            print(f"Contract found: {contract.reference}")
            
            # Validate contract can be activated
            print("Validating contract status...")
            if contract.status != Contract.STATUS_DRAFT:
                raise ValidationError("Only draft contracts can be activated")
            
            print("Checking for products...")
            if not contract.products.exists():
                raise ValidationError("Cannot activate contract with no products")
            
            print("Starting atomic transaction...")
            with transaction.atomic():
                print("Changing status to active...")
                # Change status to active
                contract.status = Contract.STATUS_ACTIVE
                contract.save()
                print("Status changed successfully")

                # Generate any past due invoices up to current date if needed
                if contract.start_date < timezone.now().date():
                    print("Contract start date is in the past, generating missing invoices...")
                    invoices = contract.generate_missing_invoices()
                    print(f"Generated {len(invoices)} invoices")
                else:
                    print("No past invoices to generate")
                
            print("Transaction completed successfully")
            return JsonResponse({
                'status': 'success',
                'message': 'Contract activated successfully'
            })
            
        except ValidationError as e:
            print(f"Validation error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

class ContractHistoryView(View):
    def get(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            invoices = ContractInvoice.objects.filter(
                contract=contract
            ).select_related('invoice').order_by('-period_start')
            
            invoice_data = [{
                'ref': inv.invoice.ref,
                'period_start': inv.period_start.strftime('%Y-%m-%d'),
                'period_end': inv.period_end.strftime('%Y-%m-%d'),
                'amount': str(inv.invoice.total_amount),
                'status': inv.invoice.payment_status,
                'export_status': 'Exported' if inv.invoice.exported_at else 'Not Exported',
                'generated_at': inv.created_at.strftime('%Y-%m-%d %H:%M'),
            } for inv in invoices]
            
            return JsonResponse({
                'status': 'success',
                'history': invoice_data
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)