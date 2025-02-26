from datetime import datetime, timedelta
import traceback
from django.forms import ValidationError
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .models import BankFeeTransaction, Check, DirectDebit, ForecastStatement, VATConfiguration, VATDeclaration, BankAccount
from django.db import transaction
from django.db.models import Q, Sum

class VATListView(View):
    def get(self, request):
        """Display VAT declarations list and configuration"""
        print("\n=== VAT List View ===")
        
        try:
            config = VATConfiguration.objects.first()
        except VATConfiguration.DoesNotExist:
            config = None
            
        declarations = VATDeclaration.objects.all().order_by(
            '-period_year', 
            '-period_month'
        )
        
        pending = VATDeclaration.objects.get_pending_declarations()
        
        context = {
            'config': config,
            'declarations': declarations,
            'pending_count': pending.count(),
            'bank_accounts': BankAccount.objects.filter(is_active=True)
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'html': render_to_string(
                    'vat/partials/declaration_list.html',
                    context,
                    request=request
                )
            })
            
        return render(request, 'vat/vat_list.html', context)

class VATConfigurationView(View):
    def post(self, request):
        """Create or update VAT configuration"""
        print("\n=== Updating VAT Configuration ===")
        
        try:
            declaration_day = int(request.POST.get('declaration_day'))
            bank_id = request.POST.get('bank_id')
            invoiced_vat_account = request.POST.get('invoiced_vat_account')
            deducted_vat_account = request.POST.get('deducted_vat_account')
            journal = request.POST.get('journal')
            default_forecast_amount = request.POST.get('default_forecast_amount')
            
            if not (1 <= declaration_day <= 31):
                raise ValueError("Invalid declaration day")
                    
            bank = get_object_or_404(BankAccount, id=bank_id)
            
            config = VATConfiguration.initialize(
                declaration_day=declaration_day,
                domiciliation_bank=bank,
                invoiced_vat_account=invoiced_vat_account,
                deducted_vat_account=deducted_vat_account,
                journal=journal,
                default_forecast_amount=default_forecast_amount
            )
            
            messages.success(request, "VAT Configuration updated successfully")
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class VATDeclarationCreateView(View):
    def post(self, request):
        """Create new VAT declaration"""
        print("\n=== Creating VAT Declaration ===")
        
        try:
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            
            if not (1 <= month <= 12):
                raise ValueError("Invalid month")
            
            latest = VATDeclaration.objects.order_by('-period_year', '-period_month').first()
            
            if latest:
                # Calculate next valid period
                next_month = latest.period_month + 1
                next_year = latest.period_year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                    
                # Validate requested period
                if year < next_year or (year == next_year and month < next_month):
                    raise ValidationError(f"Can only create declaration for period {next_month}/{next_year} or later")
            
                
            declaration = VATDeclaration.objects.create(
                period_month=month,
                period_year=year
            )
            
            print(f"Created declaration for {month}/{year}")
            messages.success(request, f"VAT Declaration for {month}/{year} created")
            
            return JsonResponse({
                'status': 'success',
                'declaration_id': declaration.id
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        
class VATDeclarationDetailView(View):
    def get(self, request, declaration_id):
        """Display VAT declaration details with rate breakdowns"""
        print(f"\n=== VAT Declaration Detail View {declaration_id} ===")
        
        declaration = get_object_or_404(VATDeclaration, id=declaration_id)
        details = declaration.details.all()
        
        # Group receipt details by VAT rate
        receipt_details = details.filter(source_type='receipt').order_by('vat_rate')
        receipt_summary = {}
        for detail in receipt_details:
            rate = detail.vat_rate
            if rate not in receipt_summary:
                receipt_summary[rate] = {
                    'count': 0,
                    'total_amount': Decimal('0.00'),
                    'total_vat': Decimal('0.00')
                }
            receipt_summary[rate]['count'] += 1
            receipt_summary[rate]['total_amount'] += detail.original_amount
            receipt_summary[rate]['total_vat'] += detail.vat_amount
        
        # Group invoice details by VAT rate
        invoice_details = details.exclude(source_type='receipt').order_by('vat_rate')
        invoice_summary = {}
        for detail in invoice_details:
            rate = detail.vat_rate
            if rate not in invoice_summary:
                invoice_summary[rate] = {
                    'count': 0,
                    'total_original': Decimal('0.00'),
                    'total_credits': Decimal('0.00'),
                    'total_vat': Decimal('0.00')
                }
            invoice_summary[rate]['count'] += 1
            invoice_summary[rate]['total_original'] += detail.original_amount
            invoice_summary[rate]['total_credits'] += detail.credit_amount
            invoice_summary[rate]['total_vat'] += detail.vat_amount

        bank_fee_details = details.filter(source_type='bank_fee').order_by('vat_rate')
        bank_fee_summary = {}
        for detail in bank_fee_details:
            rate = detail.vat_rate
            if rate not in bank_fee_summary:
                bank_fee_summary[rate] = {
                    'count': 0,
                    'total_amount': Decimal('0.00'),
                    'total_vat': Decimal('0.00')
                }
            bank_fee_summary[rate]['count'] += 1
            bank_fee_summary[rate]['total_amount'] += detail.original_amount
            bank_fee_summary[rate]['total_vat'] += detail.vat_amount
        
        # Calculate totals
        total_receipts = Decimal('0.00')
        total_invoices = Decimal('0.00')
        total_bank_fees = Decimal('0.00')
        # Sum up receipt totals
        for rate_summary in receipt_summary.values():
            total_receipts += rate_summary['total_vat']
        
        # Sum up invoice totals
        for rate_summary in invoice_summary.values():
            total_invoices += rate_summary['total_vat']
        
        # Sum up bank fee totals
        for rate_summary in bank_fee_summary.values():
            total_bank_fees += rate_summary['total_vat']
        
        print("\nTotals Calculation:")
        print(f"Receipt VAT Total: {total_receipts}")
        print(f"Invoice VAT Total: {total_invoices}")
        
        context = {
            'declaration': declaration,
            'receipt_details': receipt_details,
            'invoice_details': invoice_details,
            'bank_fee_details': bank_fee_details,
            'receipt_summary': receipt_summary,
            'invoice_summary': invoice_summary,
            'bank_fee_summary': bank_fee_summary,
            'total_receipts': total_receipts,
            'total_invoices': total_invoices,
            'total_bank_fees': total_bank_fees
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'html': render_to_string(
                    'vat/partials/declaration_details.html',
                    context,
                    request=request
                )
            })
            
        return render(request, 'vat/declaration_detail.html', context)

class VATDeclarationProcessView(View):
    def post(self, request, declaration_id):
        """Process VAT declaration calculations"""
        print(f"\n=== Processing VAT Declaration {declaration_id} ===")
        
        try:
            declaration = get_object_or_404(VATDeclaration, id=declaration_id)
            
            if declaration.status != VATDeclaration.DRAFT:
                raise ValidationError("Only draft declarations can be processed")
            
            # Start transaction to ensure atomicity
            with transaction.atomic():
                # Calculate and store VATs
                declaration.process_declaration()
                
                # Group results by rate for response
                details = declaration.details.all()
                
                invoiced_by_rate = {}
                deducted_by_rate = {}
                
                for detail in details:
                    rate = detail.vat_rate
                    if detail.source_type == 'receipt':
                        if rate not in invoiced_by_rate:
                            invoiced_by_rate[rate] = Decimal('0.00')
                        invoiced_by_rate[rate] += detail.vat_amount
                    else:
                        if rate not in deducted_by_rate:
                            deducted_by_rate[rate] = Decimal('0.00')
                        deducted_by_rate[rate] += detail.vat_amount
                
                messages.success(request, "Declaration processed successfully")
                return JsonResponse({
                    'status': 'success',
                    'invoiced_vat': {
                        str(rate): float(amount) 
                        for rate, amount in invoiced_by_rate.items()
                    },
                    'deducted_vat': {
                        str(rate): float(amount) 
                        for rate, amount in deducted_by_rate.items()
                    },
                    'total_invoiced': float(declaration.total_invoiced_vat),
                    'total_deducted': float(declaration.total_deducted_vat),
                    'net_vat': float(declaration.total_invoiced_vat - declaration.total_deducted_vat)
                })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class VATDeclarationDeclareView(View):
    def post(self, request, declaration_id):
        """Mark VAT declaration as declared"""
        print(f"\n=== Declaring VAT Declaration {declaration_id} ===")
        
        try:
            declaration = get_object_or_404(VATDeclaration, id=declaration_id)
            
            if not declaration.is_processed:
                raise ValidationError("Declaration must be processed first")
                
            declaration.declare()
            
            messages.success(request, "Declaration marked as declared")
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class VATDeclarationPayView(View):
    def post(self, request, declaration_id):
        """Mark VAT declaration as paid"""
        print(f"\n=== Marking VAT Declaration {declaration_id} as Paid ===")
        print("Request POST data:", request.POST)  # Debug line only post data
        
        try:
            declaration = get_object_or_404(VATDeclaration, id=declaration_id)
            payment_date = request.POST.get('payment_date')
            
            if not payment_date:
                print("No payment date found in request")  # Debug line
                raise ValidationError("Payment date is required")
                
            print(f"Payment date received: {payment_date}")  # Debug line
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            
            declaration.mark_as_paid(payment_date)
            
            messages.success(request, "VAT payment recorded")
            return JsonResponse({
                'status': 'success',
                'message': 'VAT payment recorded successfully'
            })
                
        except ValidationError as e:
            print(f"Validation Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while processing the payment'
            }, status=500)

class VATPendingDeclarationsView(View):
    def get(self, request):
        """Get list of pending declarations"""
        print("\n=== Getting Pending VAT Declarations ===")
        
        pending = VATDeclaration.objects.get_pending_declarations()
        
        declarations = []
        for declaration in pending:
            declarations.append({
                'id': str(declaration.id),
                'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                'due_date': declaration.due_date.strftime('%Y-%m-%d'),
                'days_overdue': (timezone.now().date() - declaration.due_date).days
            })
            
        return JsonResponse({
            'status': 'success',
            'declarations': declarations
        })

class VATForecastView(View):
    """View for loading VAT forecasts for a specific date"""
    def get(self, request):
        try:
            date = request.GET.get('date')
            bank_id = request.GET.get('bank')
            
            forecast_date = datetime.strptime(date, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            
            print(f"\n=== Loading VAT Forecasts for date {forecast_date} ===")
            print(f"Bank Account: {bank_account.account_number}")
            
            # ONLY fetch forecasts - no updates or creation
            forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False,
                source_type='vat_declaration'
            )
            
            print(f"Found {forecasts.count()} forecasts")
            forecasts_data = []
            total_amount = Decimal('0.00')
            
            for forecast in forecasts:
                print(f"Processing forecast: amount={forecast.debit or forecast.credit}")
                amount = forecast.debit or forecast.credit
                if amount:
                    forecasts_data.append({
                        'amount': float(amount),
                        'label': forecast.label,
                        'due_date': forecast_date.strftime('%Y-%m-%d'),
                        'status': 'pending',
                        'status_display': 'Pending Payment'
                    })
                    total_amount += amount
            
            print(f"Total amount: {total_amount}")
            
            return JsonResponse({
                'status': 'success',
                'forecasts': forecasts_data,
                'total': float(total_amount)
            })
            
        except Exception as e:
            print(f"Error in VATForecastView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        
class VATDeductionDetailsView(View):
    def get(self, request, declaration_id):
        """Display detailed list of VAT deductions"""
        print(f"\n=== VAT Deduction Details View {declaration_id} ===")
        
        declaration = get_object_or_404(VATDeclaration, id=declaration_id)
        consolidated_details = {}  # Key will be (supplier_id, invoice_id, vat_rate)
        
        deduction_details = declaration.details.exclude(
            source_type='receipt'
        ).select_related(
            'declaration'
        ).order_by('source_type', '-vat_amount')
        
        print(f"Found {deduction_details.count()} deduction details")
        
        total_raw = Decimal('0.00')
        total_vat = Decimal('0.00')
        total_net = Decimal('0.00')

        bank_fees = deduction_details.filter(source_type='bank_fee')
        print(f"\nProcessing {bank_fees.count()} bank fees")

        for detail in bank_fees:
            print(f"\nProcessing bank fee detail: {detail.id}")
            print(f"VAT amount: {detail.vat_amount}")
            print(f"Original amount: {detail.original_amount}")
            
            try:
                fee = BankFeeTransaction.objects.select_related(
                    'fee_type', 
                    'bank_account'
                ).get(id=detail.source_id)

                consolidated_details[(None, fee.id, detail.vat_rate, 'bank_fee')] = {
                    'payment_date': fee.date,
                    'payment_code': '3',  # Direct debit code
                    'supplier_name': fee.bank_account.get_bank_display(),  # Bank name
                    'if_code': fee.bank_account.if_code,  # Bank IF code
                    'ice_code': fee.bank_account.ice_code,  # Bank ICE code
                    'invoice_date': fee.date,
                    'invoice_ref': fee.fee_type.name,  # Fee type name as reference
                    'invoice_id': None,
                    'vat_rate': detail.vat_rate,
                    'fiscal_labels': 'Bank Fee',
                    'raw_amount': detail.original_amount,
                    'vat_amount': detail.vat_amount,
                    'net_amount': detail.original_amount + detail.vat_amount,
                    'is_credit_note': False,
                    'order': 1,
                    'is_bank_fee': True
                }
                
                print(f"Bank: {fee.bank_account.get_bank_display()}")
                print(f"IF Code: {fee.bank_account.if_code}")
                print(f"ICE Code: {fee.bank_account.ice_code}")
                
                total_raw += detail.original_amount
                total_vat += detail.vat_amount
                total_net += detail.original_amount + detail.vat_amount
                
            except BankFeeTransaction.DoesNotExist:
                print(f"Bank fee {detail.source_id} not found")
                continue
        
        for detail in deduction_details:
            print(f"\nProcessing detail: {detail.source_type} - {detail.source_id}")
            print(f"VAT amount from detail: {detail.vat_amount}")
            print(f"Original amount from detail: {detail.original_amount}")
            
            payment = None
            if detail.source_type == 'invoice_check':
                payment = Check.objects.select_related(
                    'cause', 'beneficiary'
                ).get(id=detail.source_id)
                payment_code = '2'
                payment_date = payment.paid_at
                invoice = payment.cause
                supplier = payment.beneficiary
                payment_amount = payment.amount
                
            elif detail.source_type == 'invoice_direct_debit':
                payment = DirectDebit.objects.select_related(
                    'invoice__invoice', 'contract__supplier'
                ).get(id=detail.source_id)
                payment_code = '3'
                payment_date = payment.processed_date
                invoice = payment.invoice.invoice
                supplier = payment.contract.supplier
                payment_amount = payment.amount
            
            if payment:
                print(f"Payment found: {payment.__class__.__name__} {payment.id}")
                print(f"Payment amount: {payment_amount}")
                
                # Get all VAT details for this payment
                vat_details = invoice.calculate_payment_vat(payment_amount)
                print(f"VAT details: {vat_details}")
                
                # Process each VAT rate
                for rate, amounts in vat_details.items():
                    if rate == detail.vat_rate:  # Only process matching VAT rate
                        key = (supplier.id, invoice.id, rate)
                        
                        if key not in consolidated_details:
                            # Check if invoice is fully paid in this period
                            period_start = declaration.due_date - timedelta(days=30)
                            period_end = declaration.due_date
                            
                            print(f"\nChecking payments in period {period_start} to {period_end}")
                            
                            # Sum all types of payments
                            checks_total = invoice.check_allocations.filter(
                                payment__paid_at__range=(period_start, period_end)
                            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                            
                            direct_debits_total = DirectDebit.objects.filter(
                                invoice__invoice=invoice,
                                processed_date__range=(period_start, period_end)
                            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                            
                            total_paid = checks_total + direct_debits_total
                            print(f"Total paid in period: {total_paid}")
                            print(f"Amount available: {invoice.amount_available_for_payment}")
                            
                            is_fully_paid = total_paid >= invoice.amount_available_for_payment
                            
                            # Get fiscal labels for this VAT rate
                            fiscal_labels = set(
                                product.product.fiscal_label 
                                for product in invoice.products.filter(
                                    vat_rate=rate
                                ).select_related('product')
                            )
                            
                            consolidated_details[key] = {
                                'payment_date': payment_date,
                                'payment_code': payment_code,
                                'supplier_name': supplier.name,
                                'if_code': supplier.if_code,
                                'ice_code': supplier.ice_code,
                                'invoice_date': invoice.date,
                                'invoice_ref': invoice.ref,
                                'invoice_id': invoice.id,
                                'vat_rate': rate,
                                'fiscal_labels': ' - '.join(sorted(fiscal_labels)) if fiscal_labels else '',
                                'raw_amount': amounts['amount'],
                                'vat_amount': amounts['vat'],
                                'net_amount': amounts['amount'] + amounts['vat'],
                                'is_credit_note': False,
                                'order': 1 if is_fully_paid else 2
                            }
                            print(f"Created new consolidated entry:")
                            print(f"Key: {key}")
                            print(f"Consolidated details: {consolidated_details[key]}")
                            print(f"Raw amount: {amounts['amount']}")
                            print(f"VAT amount: {amounts['vat']}")
                        else:
                            # Update amounts for existing entry
                            consolidated_details[key]['raw_amount'] += amounts['amount']
                            consolidated_details[key]['vat_amount'] += amounts['vat']
                            consolidated_details[key]['net_amount'] += amounts['amount'] + amounts['vat']
                            
                            # Update payment date if this one is more recent
                            if payment_date > consolidated_details[key]['payment_date']:
                                consolidated_details[key]['payment_date'] = payment_date
                                
                            print(f"Updated existing entry:")
                            print(f"New raw amount: {consolidated_details[key]['raw_amount']}")
                            print(f"New VAT amount: {consolidated_details[key]['vat_amount']}")
                
                # Handle credit notes
                if detail.credit_amount > 0:
                    key = (supplier.id, invoice.id, detail.vat_rate)
                    credit_key = (key[0], key[1], key[2], 'credit')
                    
                    if key in consolidated_details:
                        consolidated_details[credit_key] = consolidated_details[key].copy()
                        credit_vat = detail.credit_amount * (detail.vat_rate / Decimal('100.00'))
                        
                        consolidated_details[credit_key].update({
                            'raw_amount': -detail.credit_amount,
                            'vat_amount': -credit_vat,
                            'net_amount': -(detail.credit_amount + credit_vat),
                            'is_credit_note': True
                        })
                        print(f"Added credit note entry:")
                        print(f"Raw amount: {-detail.credit_amount}")
                        print(f"VAT amount: {-credit_vat}")
        
        # Convert consolidated details to list and calculate totals
        details = []
        for detail in consolidated_details.values():
            if 'fiscal_label' in detail and isinstance(detail['fiscal_label'], set):
                detail['fiscal_label'] = ' - '.join(sorted(detail['fiscal_label']))
            details.append(detail)
            total_raw += detail['raw_amount']
            total_vat += detail['vat_amount']
            total_net += detail['net_amount']

        # Sort by order first, then by supplier name and invoice ref
        details.sort(key=lambda x: (x['order'], x['supplier_name'], x['invoice_ref']))
        
        print(f"\nFinal totals:")
        print(f"Raw: {total_raw}")
        print(f"VAT: {total_vat}")
        print(f"Net: {total_net}")
        
        context = {
            'declaration': declaration,
            'details': details,
            'total_raw': total_raw,
            'total_vat': total_vat,
            'total_net': total_net
        }
        
        return render(request, 'vat/vat_deduction_details.html', context)
    

class VATDeclarationDeleteView(View):
    def post(self, request, declaration_id):
        """Delete VAT declaration"""
        print(f"\n=== Deleting VAT Declaration {declaration_id} ===")
        
        try:
            declaration = get_object_or_404(VATDeclaration, id=declaration_id)
            
            if not declaration.can_be_deleted():
                raise ValidationError("This declaration cannot be deleted")
                
            declaration.delete()
            messages.success(request, "VAT Declaration deleted successfully")
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)