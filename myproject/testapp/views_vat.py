from datetime import datetime
import traceback
from django.forms import ValidationError
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .models import ForecastStatement, VATConfiguration, VATDeclaration, BankAccount
from django.db import transaction
from django.db.models import Q

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
            
            if not (1 <= declaration_day <= 31):
                raise ValueError("Invalid declaration day")
                
            bank = get_object_or_404(BankAccount, id=bank_id)
            
            config = VATConfiguration.initialize(
                declaration_day=declaration_day,
                domiciliation_bank=bank
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
        
        # Calculate totals
        total_receipts = Decimal('0.00')
        total_invoices = Decimal('0.00')
        
        # Sum up receipt totals
        for rate_summary in receipt_summary.values():
            total_receipts += rate_summary['total_vat']
        
        # Sum up invoice totals
        for rate_summary in invoice_summary.values():
            total_invoices += rate_summary['total_vat']
        
        print("\nTotals Calculation:")
        print(f"Receipt VAT Total: {total_receipts}")
        print(f"Invoice VAT Total: {total_invoices}")
        
        context = {
            'declaration': declaration,
            'receipt_details': receipt_details,
            'invoice_details': invoice_details,
            'receipt_summary': receipt_summary,
            'invoice_summary': invoice_summary,
            'total_receipts': total_receipts,
            'total_invoices': total_invoices
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