from datetime import datetime
from decimal import Decimal
import traceback
from django.forms import ValidationError
from django.views import View
from django.views.generic import ListView
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json

from .models import INVOICE_TYPES, BankAccount, Contract, ContractProduct, DirectDebit, ForecastStatement, Supplier, Product, ContractInvoice

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_types'] = INVOICE_TYPES
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True)
        return context

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
            print("\n=== Creating Contract ===")
            print("Contract data:", data)   
            
            with transaction.atomic():
                domiciliation_bank = None
                # For loan contracts, get bank's supplier
                if data.get('is_loan'):
                    print("Creating loan contract")
                    bank = BankAccount.objects.get(id=data['bank_id'])
                    supplier = bank.create_supplier()
                    if not supplier:
                        raise ValidationError(_("Bank account must have IF/ICE codes set"))
                    data['supplier_id'] = supplier.id
                    
                    # Force domiciliation to loaning bank
                    data['generation_day'] = data['payment_day']
                    data['is_domiciled'] = True
                    data['domiciliation_bank'] = data['bank_id']
                    data['domiciliation_day'] = data['payment_day']
                
                if not data.get('generation_day') and not data.get('is_loan'):
                    raise ValidationError("Generation day is required for regular contracts")
            
                if data.get('is_domiciled'):
                    domiciliation_bank = BankAccount.objects.get(id=data['domiciliation_bank'])
                    print(f"Found domiciliation bank: {domiciliation_bank}")
                    
                contract = Contract.objects.create(
                    reference=data['reference'],
                    supplier_id=data['supplier_id'],
                    start_date=data['start_date'],
                    end_date=data.get('end_date'),
                    is_indefinite=data.get('is_indefinite', False),
                    periodicity=data['periodicity'],
                    generation_day=data['generation_day'],
                    is_domiciled=data.get('is_domiciled', False),       
                    domiciliation_bank_id=data.get('domiciliation_bank'),
                    domiciliation_day=data.get('domiciliation_day'),
                    invoice_type='LOAN' if data.get('is_loan') else data.get('invoice_type', 'OTHER')
                )
                
                # Track total contract amount (WITH VAT)
                total_amount = Decimal('0')

                # Add products
                for product_data in data['products']:
                    # Get product for VAT rate
                    product = Product.objects.get(id=product_data['product_id'])
                    quantity = Decimal(str(product_data['quantity']))
                    
                    # Handle unit price that could be string or number
                    unit_price_raw = product_data['unit_price']
                    if isinstance(unit_price_raw, str):
                        unit_price = Decimal(unit_price_raw.replace(',', '.'))
                    else:
                        unit_price = Decimal(str(unit_price_raw))
                        
                    reduction_rate = Decimal(str(product_data.get('reduction_rate', '0')))

                    # Calculate amount with VAT included
                    amount = quantity * unit_price
                    if reduction_rate > 0:
                        reduction_amount = amount * (reduction_rate / Decimal('100'))
                        amount -= reduction_amount
                    
                    # Add VAT
                    amount += amount * (product.vat_rate / Decimal('100'))
                    total_amount += amount

                    print(f"Product: {product.name}")
                    print(f"Amount (with VAT): {amount}")

                    ContractProduct.objects.create(
                        contract=contract,
                        product_id=product_data['product_id'],
                        quantity=product_data['quantity'],
                        unit_price=unit_price,
                        reduction_rate=product_data.get('reduction_rate', 0)
                    )

                # Store the total (with VAT)
                contract.amount = total_amount
                contract.save()

                # Generate forecasts if newly domiciled
                if contract.is_domiciled and not contract.domiciliation_suspended:
                    print("Generating domiciliation forecasts...")
                    contract.refresh_from_db()
                    print(f"Refreshed contract. Bank: {contract.domiciliation_bank}")
                    contract.generate_domiciliation_forecasts()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contract created successfully',
                    'id': str(contract.id),
                    'amount': float(total_amount)
                })
                
        except Exception as e:
            print(f"Error creating contract: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ContractUpdateView(View):
    def get(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            
            print(f"\n=== Loading Contract {contract.id} ===")
            print(f"Invoice type: {contract.invoice_type}")
            print(f"Is domiciled: {contract.is_domiciled}")
            print(f"Has forecasts: {ForecastStatement.objects.filter(source_type='contract_domiciliation', source_id=contract.id).exists()}")
            
            # Check if contract has any forecasts - if yes, domiciliation is locked
            has_forecasts = ForecastStatement.objects.filter(
                source_type='contract_domiciliation',
                source_id=contract.id
            ).exists()

            response_data = {
                'id': str(contract.id),
                'reference': contract.reference,
                'supplier_id': str(contract.supplier_id),
                'supplier_name': contract.supplier.name,
                'start_date': contract.start_date.isoformat(),
                'end_date': contract.end_date.isoformat() if contract.end_date else None,
                'is_indefinite': contract.is_indefinite,
                'periodicity': contract.periodicity,
                'generation_day': contract.generation_day,
                'invoice_type': contract.invoice_type,
                'status': contract.status,
                'products': [{
                    'id': str(p.id),
                    'product_id': str(p.product_id),
                    'product_name': p.product.name,
                    'quantity': str(p.quantity),
                    'unit_price': str(p.unit_price),
                    'reduction_rate': str(p.reduction_rate)
                } for p in contract.products.all()],
                # Domiciliation details with locking info
                'is_domiciled': contract.is_domiciled,
                'domiciliation_locked': has_forecasts or contract.status != 'draft',  # Lock if has forecasts or not draft
                'domiciliation_bank': str(contract.domiciliation_bank_id) if contract.domiciliation_bank else None,
                'domiciliation_bank_name': contract.domiciliation_bank.get_bank_display() if contract.domiciliation_bank else None,
                'domiciliation_day': contract.domiciliation_day,
                'domiciliation_suspended': contract.domiciliation_suspended,
                'domiciliation_suspension_date': contract.domiciliation_suspension_date.isoformat() if contract.domiciliation_suspension_date else None,
                'domiciliation_suspension_reason': contract.domiciliation_suspension_reason,
                'is_loan': contract.invoice_type == 'LOAN'
            }

            print("Response data:", response_data)
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error loading contract: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)

    def post(self, request, pk):
        try:
            contract = get_object_or_404(Contract, pk=pk)
            data = json.loads(request.body)
            
            print(f"\n=== Updating Contract {contract.id} ===")
            print(f"Current status: {contract.status}")
            print(f"Has forecasts: {ForecastStatement.objects.filter(source_type='contract_domiciliation', source_id=contract.id).exists()}")
            
            with transaction.atomic():
                # If contract has forecasts, don't allow domiciliation changes
                has_forecasts = ForecastStatement.objects.filter(
                    source_type='contract_domiciliation',
                    source_id=contract.id
                ).exists()
                
                if has_forecasts or contract.status != 'draft':
                    print("Contract has forecasts or is not draft - preserving domiciliation settings")
                    data['is_domiciled'] = contract.is_domiciled
                    data['domiciliation_bank'] = contract.domiciliation_bank_id
                    data['domiciliation_day'] = contract.domiciliation_day
                
                # Rest of the update code remains same
                contract.reference = data['reference']
                contract.supplier_id = data['supplier_id']
                contract.start_date = data['start_date']
                contract.end_date = data.get('end_date')
                contract.is_indefinite = data.get('is_indefinite', False)
                contract.periodicity = data['periodicity']
                contract.generation_day = data['generation_day']
                contract.invoice_type = data.get('invoice_type', 'OTHER')
                
                # Handle domiciliation only if not locked
                if not has_forecasts and contract.status == 'draft':
                    contract.is_domiciled = data.get('is_domiciled', False)
                    if contract.is_domiciled:
                        contract.domiciliation_bank_id = data.get('domiciliation_bank')
                        contract.domiciliation_day = data.get('domiciliation_day')
                
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
            print(f"Error updating contract: {str(e)}")
            print(traceback.format_exc())
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
            
            print("\n=== Getting Contract History ===")
            invoice_data = []
            
            for inv in invoices:
                print(f"\nProcessing invoice: {inv.invoice.ref}")
                
                # Get direct debit details
                direct_debit = DirectDebit.objects.filter(
                    invoice=inv
                ).first()
                
                processed_date = None
                if direct_debit and direct_debit.status == DirectDebit.PROCESSED:
                    processed_date = direct_debit.processed_date
                    print(f"Found processed date: {processed_date}")
                
                invoice_data.append({
                    'ref': inv.invoice.ref,
                    'period_start': inv.period_start.strftime('%Y-%m-%d'),
                    'period_end': inv.period_end.strftime('%Y-%m-%d'),
                    'amount': str(inv.invoice.total_amount),
                    'status': inv.invoice.payment_status,
                    'export_status': 'Exported' if inv.invoice.exported_at else 'Not Exported',
                    'generated_at': inv.created_at.strftime('%Y-%m-%d %H:%M'),
                    'paid_at': processed_date.strftime('%Y-%m-%d') if processed_date else None
                })
            
            return JsonResponse({
                'status': 'success',
                'history': invoice_data
            })
            
        except Exception as e:
            print(f"Error getting contract history: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ContractSuspendDomiciliationView(View):
    def post(self, request, pk):
        print("\n=== Processing Contract Domiciliation Suspension ===")
        try:
            data = json.loads(request.body)
            contract = get_object_or_404(Contract, pk=pk)
            
            print(f"Contract: {contract.reference}")
            print(f"Suspension date: {data['date']}")
            print(f"Reason: {data.get('reason', '')}")
            
            if not contract.is_domiciled:
                raise ValidationError("Contract is not domiciled")
                
            with transaction.atomic():
                # Delete future forecasts
                future_forecasts = ForecastStatement.objects.filter(
                    source_type='contract_domiciliation',
                    source_id=contract.id,
                    date__gte=data['date']
                )
                
                deleted_count = future_forecasts.count()
                print(f"Deleting {deleted_count} future forecasts")
                future_forecasts.delete()
                
                # Update contract
                contract.domiciliation_suspended = True
                contract.domiciliation_suspension_date = data['date']
                contract.domiciliation_suspension_reason = data.get('reason', '')
                contract.save()
                
                print("Domiciliation suspended successfully")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Domiciliation suspended. {deleted_count} forecasts removed.'
                })
                
        except ValidationError as e:
            print(f"Validation error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to suspend domiciliation'
            }, status=500)