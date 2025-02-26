from django.forms import ValidationError
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import CashExpense, Check, Contract, ContractInvoice, DirectDebit, PresentationReceipt, BankAccount, BankStatement, AccountingEntry, BankFeeType, ForecastStatement, CheckReceipt, LCN, ReceiptHistory, ContentType, VATDeclaration, get_supplier_balance, CashConfiguration, CashDeposit, CashPayment, Invoice
import json
from decimal import Decimal
from django.db.models import Q
from datetime import datetime, date
import calendar
from calendar import monthcalendar
from .services.forecast import PaymentForecastService
import traceback
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from testapp import models

class BankStatementView(View):
    """View for displaying bank statements"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters or set defaults
            today = date.today()
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not start_date and not end_date:
                # Set to first and last day of current month
                start_date = date(today.year, today.month, 1)
                end_date = date(today.year, today.month, 
                              calendar.monthrange(today.year, today.month)[1])
            else:
                # Convert string dates to date objects if provided
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get statement entries
            entries = BankStatement.get_statement(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date,
                include_forecasts=False
            )
            
             # Calculate totals excluding opening balance
            total_debit = sum(entry['debit'] or 0 for entry in entries if entry['type'] != 'BALANCE')
            total_credit = sum(entry['credit'] or 0 for entry in entries if entry['type'] != 'BALANCE')
            # Final balance comes from the first entry (they're sorted in reverse)
            final_balance = entries[0]['balance'] if entries else Decimal('0.00')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'bank/partials/statement_table.html',
                        {'entries': entries},
                        request=request
                    ),
                    'totals': {
                        'debit': total_debit,
                        'credit': total_credit,
                        'balance': final_balance
                    }
                })
            
            # Get additional data for full page render
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'bank_accounts': BankAccount.objects.filter(is_active=True).exclude(id=bank_account.id),
                'fee_types': BankFeeType.objects.all(),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'final_balance': final_balance
            }
            
            return render(request, 'bank/bank_statement.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class AccountingView(View):
    """View for displaying accounting entries"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get accounting entries
            entries = AccountingEntry.get_entries(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
            entries = [entry for entry in entries if entry['journal_code'] != '06']

            context = {
                'bank_account': bank_account,
                'entries': entries,
                'total_debit': sum(entry['debit'] or 0 for entry in entries),
                'total_credit': sum(entry['credit'] or 0 for entry in entries)
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string(
                    'bank/partials/accounting_table.html',
                    context,
                    request=request
                )
                return JsonResponse({'html': html})
            
            return render(request, 'bank/accounting.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class OtherOperationsView(View):
    """View for displaying other operations (discounted receipts)"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get accounting entries filtered for journal code '06'
            entries = AccountingEntry.get_entries(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter for other operations (journal code '06')
            entries = [e for e in entries if e['journal_code'] == '06']
            
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'total_debit': sum(entry['debit'] or 0 for entry in entries),
                'total_credit': sum(entry['credit'] or 0 for entry in entries)
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string(
                    'bank/partials/other_operations_table.html',
                    context,
                    request=request
                )
                return JsonResponse({'html': html})
            
            return render(request, 'bank/other_operations.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

class CalendarView(View):
    def get(self, request):
        # Get parameters
        print("\n=== Calendar View Request ===")
        year = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))
        selected_bank_ids = request.GET.getlist('banks', [])
        
        # Get bank accounts for calendar
        bank_accounts = BankAccount.objects.filter(is_active=True)
        calendar_banks = bank_accounts.filter(id__in=selected_bank_ids) if selected_bank_ids else bank_accounts.none()
        
        # Get ALL pending forecasts for ALL active banks
        today = date.today()
        pending_forecasts = []
        
        for bank in bank_accounts:
            pending_data = self._get_pending_forecasts(bank)
            if pending_data['count'] > 0:  # Only add if there are pending forecasts
                pending_forecasts.append({
                    'id': str(bank.id),
                    'bank': bank.get_bank_display(),
                    'account_number': bank.account_number,
                    'pending_count': pending_data['count'],
                    'pending_expected': pending_data['expected'],
                    'pending_discounted': pending_data['discounted'],
                    'pending_payments': pending_data['payments'],
                    'pending_total': pending_data['total']
                })
        
        # Build calendar data
        calendar_data = self._build_calendar_data(year, month, calendar_banks)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'calendar': calendar_data})

        context = {
            'calendar': calendar_data,
            'bank_accounts': bank_accounts,
            'selected_banks': selected_bank_ids,
            'pending_forecasts': pending_forecasts,
            'year': year,
            'month': month
        }

        return render(request, 'bank/calendar.html', context)


    def _build_calendar_data(self, year, month, bank_accounts):
        print(f"\n=== Building Calendar Data for {month}/{year} ===")
        print(f"Processing banks: {[b.account_number for b in bank_accounts]}")

        # Get calendar weeks
        cal = monthcalendar(year, month)
        calendar_data = []

        # Calculate start of month and get initial balances including all prior impacts
        start_of_month = date(year, month, 1)
        
        # Initialize tracking dictionaries with impacts from prior months
        bank_forecasts = {}
        supplier_forecasts = {}
        
        for bank in bank_accounts:
            # Get all forecasts up to start of month
            prior_receipt_forecasts = ForecastStatement.objects.filter(
                bank_account=bank,
                date__lt=start_of_month,
                date__gte=timezone.now().date(),  # Only include future forecasts
                is_processed=False,
                source_type__in=['checkreceipt', 'lcn']
            )
            
            prior_payment_forecasts = ForecastStatement.objects.filter(
                bank_account=bank,
                date__lt=start_of_month,
                date__gte=timezone.now().date(),
                is_processed=False,
                source_type__in=['supplier_check', 'contract_domiciliation', 'vat_declaration']
            )
            
            # Calculate cumulative impacts from prior months
            bank_forecasts[bank.id] = sum(
                (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                for f in prior_receipt_forecasts
            )
            
            supplier_forecasts[bank.id] = sum(
                (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                for f in prior_payment_forecasts
            )
            
            print(f"\nInitial impacts for {bank.account_number}:")
            print(f"Prior receipt impact: {bank_forecasts[bank.id]}")
            print(f"Prior payment impact: {supplier_forecasts[bank.id]}")

        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({
                        'day': '',
                        'is_weekend': False,
                        'bank_data': []
                    })
                    continue

                current_date = date(year, month, day)
                print(f"\nProcessing date: {current_date}")
                is_weekend = current_date.weekday() >= 5

                bank_data = []
                for bank in bank_accounts:
                    print(f"\nProcessing bank: {bank.account_number}")
                    
                    # Get actual balance including all real transactions
                    actual_statement = BankStatement.get_statement(
                        bank_account=bank,
                        end_date=current_date,
                        include_forecasts=False
                    )
                    actual_balance = actual_statement[0]['balance'] if actual_statement else Decimal('0.00')
                    print(f"Actual balance: {actual_balance}")

                    # Get forecasted transactions for this date
                    receipt_forecasts = ForecastStatement.objects.filter(
                        bank_account=bank,
                        date=current_date,
                        date__gte=timezone.now().date(),
                        is_processed=False,
                        source_type__in=['checkreceipt', 'lcn']
                    )

                    supplier_payment_forecasts = ForecastStatement.objects.filter(
                        bank_account=bank,
                        date=current_date,
                        date__gte=timezone.now().date(),
                        is_processed=False,
                        source_type__in=['supplier_check', 'contract_domiciliation']
                    )

                    vat_declaration_forecasts = ForecastStatement.objects.filter(
                        bank_account=bank,
                        date=current_date,
                        date__gte=timezone.now().date(),
                        is_processed=False,
                        source_type="vat_declaration"
                    )
                    print(f"\n=== VAT Forecast Query for {current_date} ===")
                    print(f"Bank: {bank.account_number}")
                    print(f"SQL Query: {vat_declaration_forecasts.query}")
                    print(f"Found forecasts: {vat_declaration_forecasts.count()}")
                    for f in vat_declaration_forecasts:
                        print(f"VAT forecast: credit={f.credit}, debit={f.debit}")

                    # Calculate receipt forecast impact for this day
                    day_receipt_impact = sum(
                        (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                        for f in receipt_forecasts
                    )

                    # Calculate supplier payment impact for this day
                    day_payment_impact = sum(
                        (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                        for f in supplier_payment_forecasts
                    )

                    # Calculate VAT declaration impact for this day
                    day_vat_impact = sum(
                        (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                        for f in vat_declaration_forecasts
                    )

                    # Update cumulative impacts
                    bank_forecasts[bank.id] += day_receipt_impact
                    supplier_forecasts[bank.id] += day_payment_impact + day_vat_impact

                    # Calculate total forecasted balance
                    forecasted_balance = actual_balance + bank_forecasts[bank.id] + supplier_forecasts[bank.id]
                    print(f"Cumulative receipt impact: {bank_forecasts[bank.id]}")
                    print(f"Cumulative payment impact: {supplier_forecasts[bank.id]}")
                    print(f"Forecasted balance: {forecasted_balance}")

                    # Prepare forecast data for display
                    expected_payments = []
                    discounted_receipts = []
                    
                    for f in receipt_forecasts:
                        amount = (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                        forecast_item = {
                            'label': f.label,
                            'credit': float(f.credit) if f.credit else None,
                            'debit': float(f.debit) if f.debit else None,
                            'reference': f.reference,
                            'amount': float(amount)
                        }
                        
                        if f.label.startswith('Expected'):
                            expected_payments.append(forecast_item)
                        else:
                            discounted_receipts.append(forecast_item)

                    bank_data.append({
                        'bank': {
                            'id': str(bank.id),
                            'name': bank.bank,
                            'account_number': bank.account_number
                        },
                        'balance': float(forecasted_balance),
                        'expected_payments': expected_payments,
                        'discounted_receipts': discounted_receipts,
                        'supplier_payments': [{
                            'amount': float(f.debit),
                            'label': f.label,
                            'source_type': f.source_type
                        } for f in supplier_payment_forecasts] if supplier_payment_forecasts else [],
                        'vat_payments': [{
                            'amount': float(f.debit),
                            'label': f.label,
                            'source_type': "vat_declaration"
                        } for f in vat_declaration_forecasts if f.debit] if vat_declaration_forecasts else [],
                        'has_forecasts': bool(expected_payments or discounted_receipts),
                        'has_payment_forecasts': supplier_payment_forecasts.exists(),
                        'has_vat_forecasts': vat_declaration_forecasts.exists(),
                        'has_contract_forecasts': bool(supplier_payment_forecasts.filter(source_type='contract_domiciliation'))
                    })

                week_data.append({
                    'day': day,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'is_weekend': is_weekend,
                    'bank_data': bank_data
                })
                
            calendar_data.append(week_data)
        
        for bank in bank_accounts:
            print(f"\n=== Balance Debug for {bank.account_number} ===")
            print("Balance from bank accounts list:", bank.get_current_balance())
            
            # Get actual balance (what we're using in calendar)
            actual_statement = BankStatement.get_statement(
                bank_account=bank,
                end_date=current_date
            )
            actual_balance = actual_statement[-1]['balance'] if actual_statement else Decimal('0.00')
            print("Calendar 'actual_balance':", actual_balance)
            
            # Get balance as shown in bank statement
            bank_statement = BankStatement.get_statement(
                bank_account=bank,
                end_date=current_date,
                include_forecasts=False
            )
            bank_statement_balance = bank_statement[-1]['balance'] if bank_statement else Decimal('0.00')
            print("Bank statement balance:", bank_statement_balance)
            
            # Print some entries details
            print("\nStatement entries:")
            for entry in actual_statement:
                print(f"Date: {entry['date']}, Type: {entry.get('type')}, " 
                    f"Debit: {entry.get('debit')}, Credit: {entry.get('credit')}, "
                    f"Balance: {entry.get('balance')}")

        return calendar_data

    def _get_pending_forecasts(self, bank_account):
        """Get forecasts that are past due but not processed"""
        today = date.today()
        
        pending_forecasts = ForecastStatement.objects.filter(
            bank_account=bank_account,
            date__lt=today,
            is_processed=False
        ).select_related('bank_account')

        # Filter out forecasts for paid receipts/checks
        filtered_forecasts = []
        for forecast in pending_forecasts:
            print(f"\nProcessing pending forecast: {forecast.label}")
            print(f"Source type: {forecast.source_type}")
            print(f"Source ID: {forecast.source_id}")
            if forecast.source_type == 'checkreceipt':
                receipt = CheckReceipt.objects.filter(id=forecast.source_id).first()
                if receipt and receipt.status not in ['PAID', 'COMPENSATED']:
                    filtered_forecasts.append(forecast)
            elif forecast.source_type == 'lcn':
                receipt = LCN.objects.filter(id=forecast.source_id).first()
                if receipt and receipt.status not in ['PAID', 'COMPENSATED']:
                    filtered_forecasts.append(forecast)
            elif forecast.source_type == 'supplier_check':
                check = Check.objects.filter(id=forecast.source_id).first()
                if check and check.status not in ['paid', 'cancelled']:
                    filtered_forecasts.append(forecast)
            elif forecast.source_type == 'contract_domiciliation':
                contract = Contract.objects.filter(id=forecast.source_id).first()
                if contract and contract.is_domiciled and not contract.domiciliation_suspended:
                    filtered_forecasts.append(forecast)
                    print(f"Added contract domiciliation forecast: {forecast.label}")
            elif forecast.source_type == 'vat_declaration':
                vat_declaration = VATDeclaration.objects.filter(id=forecast.source_id).first()
                if vat_declaration and vat_declaration.status == 'declared':
                    filtered_forecasts.append(forecast)
                    print(f"Added VAT declaration forecast: {forecast.label}")

        expected = Decimal('0.00')
        discounted = Decimal('0.00')
        payments = Decimal('0.00')
        
        for forecast in filtered_forecasts:
            print(f"\n--- Processing Forecast ---")
            print(f"Label: {forecast.label}")
            print(f"Source type: {forecast.source_type}")
            print(f"Source ID: {forecast.source_id}")
            
            if forecast.source_type == 'supplier_check' or forecast.source_type == 'contract_domiciliation' or forecast.source_type == 'vat_declaration':
                amount = forecast.debit or Decimal('0.00')
                payments += amount
                print(f"Added to payments total: {payments}")
            else:
                # Get receipt
                receipt = None
                if forecast.source_type == 'checkreceipt':
                    receipt = CheckReceipt.objects.filter(id=forecast.source_id).first()
                elif forecast.source_type == 'lcn':
                    receipt = LCN.objects.filter(id=forecast.source_id).first()
                
                if receipt:
                    # Calculate amount based on forecast type
                    if forecast.label.startswith('Expected'):
                        amount = (forecast.credit or Decimal('0.00')) - (forecast.debit or Decimal('0.00'))
                        expected += amount
                        print(f"Added to expected total: {expected}")
                    else:
                        amount = receipt.amount
                        discounted += amount
                        print(f"Added to discounted total: {discounted}")
                    
                    print(f"Processed amount: {amount}")
                    
        print(f"\n=== Summary for {bank_account.account_number} ===")
        print(f"Total expected: {expected}")
        print(f"Total discounted: {discounted}")
        print(f"Total payments: {payments}")
        print(f"Net impact: {expected + discounted - payments}")
                
        return {
            'count': len(filtered_forecasts),
            'expected': expected,
            'discounted': discounted,
            'payments': payments,
            'total': expected - payments
        }

class CalendarForecastView(View):
    """View for loading forecasts for a specific date and bank"""
    def get(self, request):
        date = request.GET.get('date')
        bank_id = request.GET.get('bank')
        
        print(f"\n=== Loading Forecasts for {date} ===")
        print(f"Bank ID: {bank_id}")
        
        try:
            forecast_date = datetime.strptime(date, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            print(f"Bank Account: {bank_account.bank} - {bank_account.account_number}")
            
            forecasts = []
            total_expected = Decimal('0.00')
            total_discounted = Decimal('0.00')
            
            # Get forecasts for this date
            payment_forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False
            )
            print(f"\nFound {payment_forecasts.count()} forecasts for this date")
            
            # Process each forecast
            for forecast in payment_forecasts:
                print(f"\n--- Processing Forecast ---")
                print(f"Label: {forecast.label}")
                print(f"Source type: {forecast.source_type}")
                print(f"Source ID: {forecast.source_id}")
                amount = forecast.amount or Decimal('0.00')
                print(f"Amount: {amount}")
                
                # Get receipt information based on source type
                receipt = None
                pres_receipt = None
                if forecast.source_type == 'checkreceipt':
                    print("\nLooking up Check receipt...")
                    receipt = CheckReceipt.objects.filter(
                        id=forecast.source_id
                    ).select_related('entity', 'client').first()
                    
                    if receipt:
                        print(f"Found Check #{receipt.check_number}")
                        print(f"Entity: {receipt.entity.name}")
                        print(f"Client: {receipt.client.name}")
                        print(f"Issuing Bank: {receipt.get_issuing_bank_display()}")
                        
                        # Get latest presentation for the receipt
                        pres_receipt = receipt.check_presentations.select_related(
                            'presentation'
                        ).order_by('-presentation__date').first()
                        
                        if pres_receipt:
                            print(f"Latest presentation ref: {pres_receipt.presentation.bank_reference}")
                            print(f"Latest presentation date: {pres_receipt.presentation.date}")
                            print(f"Total presentations: {receipt.check_presentations.count()}")
                        
                elif forecast.source_type == 'lcn':
                    print("\nLooking up LCN receipt...")
                    receipt = LCN.objects.filter(
                        id=forecast.source_id
                    ).select_related('entity', 'client').first()
                    
                    if receipt:
                        print(f"Found LCN #{receipt.lcn_number}")
                        print(f"Entity: {receipt.entity.name}")
                        print(f"Client: {receipt.client.name}")
                        print(f"Issuing Bank: {receipt.get_issuing_bank_display()}")
                        
                        # Get latest presentation for the receipt
                        pres_receipt = receipt.lcn_presentations.select_related(
                            'presentation'
                        ).order_by('-presentation__date').first()
                        
                        if pres_receipt:
                            print(f"Latest presentation ref: {pres_receipt.presentation.bank_reference}")
                            print(f"Latest presentation date: {pres_receipt.presentation.date}")
                            print(f"Total presentations: {receipt.lcn_presentations.count()}")

                if receipt and pres_receipt:
                    # Check if this is a representation
                    is_representation = False
                    if isinstance(receipt, CheckReceipt):
                        is_representation = receipt.check_presentations.count() > 1
                        print(f"Is Check representation? {is_representation}")
                    else:
                        is_representation = receipt.lcn_presentations.count() > 1
                        print(f"Is LCN representation? {is_representation}")
                    
                    # Add to appropriate total
                    if forecast.label.startswith('Expected'):
                        total_expected += amount
                        print(f"Added to expected total: {total_expected}")
                    else:
                        total_discounted += amount
                        print(f"Added to discounted total: {total_discounted}")

                    forecast_data = {
                        'type': 'Expected Payment' if forecast.label.startswith('Expected') else 'Discounted Receipt',
                        'number': receipt.get_receipt_number(),
                        'entity': receipt.entity.name,  # Use actual entity name
                        'bank': receipt.get_issuing_bank_display(),  # Use receipt's bank
                        'client': receipt.client.name,
                        'receipt_type': receipt.__class__.__name__,
                        'due_date': receipt.due_date.strftime('%Y-%m-%d') if receipt.due_date else None,
                        'amount': float(amount),
                        'presentation_ref': pres_receipt.presentation.bank_reference,
                        'presentation_date': pres_receipt.presentation.date.strftime('%Y-%m-%d'),
                        'is_representation': is_representation
                    }
                    forecasts.append(forecast_data)
                    print("\nAdded forecast data:")
                    for key, value in forecast_data.items():
                        print(f"{key}: {value}")

            print(f"\n=== Forecast Summary ===")
            print(f"Total forecasts: {len(forecasts)}")
            print(f"Total expected: {total_expected}")
            print(f"Total discounted: {total_discounted}")
            print(f"Grand total: {total_expected + total_discounted}")

            return JsonResponse({
                'status': 'success',
                'forecasts': forecasts,
                'totals': {
                    'expected_payments': float(total_expected),
                    'discounted_receipts': float(total_discounted),
                    'total': float(total_expected + total_discounted)
                }
            })
            
        except Exception as e:
            print(f"\n=== Error in CalendarForecastView ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nTraceback:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PendingForecastsView(View):
    def get(self, request, bank_id):
        try:
            bank = get_object_or_404(BankAccount, id=bank_id)
            today = date.today()
            
            pending_forecasts = ForecastStatement.objects.filter(
                bank_account=bank,
                date__lt=today,
                is_processed=False
            ).order_by('date')
            
            print(f"Found forecasts: {[f.source_type for f in pending_forecasts]}")

            forecasts_data = []
            for forecast in pending_forecasts:
                print("\n=== Processing Pending Forecast ===")
                print(f"Label: {forecast.label}")
                
                if forecast.source_type == 'supplier_check':
                    check = Check.objects.select_related(
                        'beneficiary', 'checker', 'cause'
                    ).get(id=forecast.source_id)
                    
                    supplier_balance = get_supplier_balance(check.beneficiary)
                    
                    forecast_data = {
                        'type': 'Supplier Payment',
                        'payment_type': check.checker.type,
                        'number': check.position,
                        'status': check.status,
                        'status_display': check.get_status_display(),
                        'source_id': str(check.id),
                        'supplier': {
                            'name': check.beneficiary.name,
                            'balance': float(supplier_balance['balance'])
                        },
                        'bank': check.checker.bank_account.get_bank_display(),
                        'due_date': check.payment_due.strftime('%Y-%m-%d'),
                        'amount': float(forecast.debit or 0),
                        'invoice': {
                            'ref': check.cause.ref if check.cause else None,
                            'id': str(check.cause.id) if check.cause else None,
                            'date': check.cause.date.strftime('%Y-%m-%d') if check.cause else None,
                            'amount': float(check.cause.total_amount) if check.cause else None
                        }
                    }
                    forecasts_data.append(forecast_data)
                
                elif forecast.source_type == 'contract_domiciliation':
                    print("\n=== Processing Contract Domiciliation Forecast ===")
                    # Get contract with supplier
                    contract = Contract.objects.select_related('supplier').get(
                        id=forecast.source_id,
                        is_domiciled=True,
                        domiciliation_suspended=False
                    )
                    print(f"Contract: {contract.reference}")
                    
                    # Get direct debit and associated invoice
                    direct_debit = DirectDebit.objects.filter(
                        contract=contract,
                        forecast=forecast
                    ).select_related(
                        'invoice__invoice'  # Follow the chain: DirectDebit -> ContractInvoice -> Invoice
                    ).first()
                    
                    print(f"Direct Debit found: {direct_debit.id if direct_debit else 'None'}")
                    if direct_debit:
                        print(f"Invoice ref: {direct_debit.invoice.invoice.ref}")
                        print(f"Invoice amount: {direct_debit.invoice.invoice.total_amount}")
                        print(f"Period: {direct_debit.invoice.period_start} to {direct_debit.invoice.period_end}")
                    
                    supplier_balance = get_supplier_balance(contract.supplier)
                    
                    forecast_data = {
                        'type': 'Contract Payment',
                        'payment_type': 'Domiciliation',
                        'number': forecast.reference,
                        'status': 'pending',
                        'status_display': 'Pending Payment',
                        'source_id': str(contract.id),
                        'supplier': {
                            'name': contract.supplier.name,
                            'balance': float(supplier_balance['balance'])
                        },
                        'bank': bank.get_bank_display(),
                        'due_date': forecast.date.strftime('%Y-%m-%d'),
                        'forecast_date': forecast.date.strftime('%Y-%m-%d'),
                        'amount': float(forecast.debit or 0),
                        'contract': {
                            'reference': contract.reference,
                            'id': str(contract.id)
                        }
                    }
                    
                    # Add invoice details if available
                    if direct_debit and direct_debit.invoice and direct_debit.invoice.invoice:
                        invoice = direct_debit.invoice.invoice
                        forecast_data['invoice'] = {
                            'ref': invoice.ref,
                            'id': str(invoice.id),
                            'date': invoice.date.strftime('%Y-%m-%d'),
                            'period_start': direct_debit.invoice.period_start.strftime('%Y-%m-%d'),
                            'period_end': direct_debit.invoice.period_end.strftime('%Y-%m-%d'),
                            'amount': float(invoice.total_amount),
                            'status': invoice.payment_status,
                            'status_display': invoice.get_payment_status_display()
                        }
                    
                    forecasts_data.append(forecast_data)

                elif forecast.source_type == 'vat_declaration':
                    print("\n=== Processing VAT Declaration Forecast ===")
                    try:
                        declaration = VATDeclaration.objects.get(id=forecast.source_id)
                        print(f"Declaration: {declaration.period_month}/{declaration.period_year}")
                        
                        forecast_data = {
                            'type': 'VAT Payment',
                            'payment_type': 'VAT Declaration',
                            'number': forecast.reference,
                            'status': declaration.status,
                            'status_display': declaration.get_status_display(),
                            'source_id': str(declaration.id),
                            'bank': bank.get_bank_display(),
                            'amount': float(forecast.debit or 0),
                            'due_date': forecast.date.strftime('%Y-%m-%d'),
                            'forecast_date': forecast.date.strftime('%Y-%m-%d'),
                            'declaration': {
                                'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                                'ref': forecast.reference,
                                'invoiced_vat': float(declaration.total_invoiced_vat),
                                'deducted_vat': float(declaration.total_deducted_vat)
                            }
                        }
                        forecasts_data.append(forecast_data)
                        print(f"Added VAT forecast: {forecast.debit}")
                    except VATDeclaration.DoesNotExist:
                        print(f"Declaration {forecast.source_id} not found")
                        continue
                    
                # Get receipt first
                receipt = None
                if forecast.source_type == 'checkreceipt':
                    receipt = CheckReceipt.objects.filter(
                        id=forecast.source_id
                    ).select_related('entity', 'client').first()
                    print(f"Check Receipt found: {receipt.check_number if receipt else 'None'}")
                    print(f"Check Amount: {receipt.amount if receipt else 'None'}")
                    if receipt:
                        # Get latest presentation
                        presentation = receipt.check_presentations.select_related(
                            'presentation'
                        ).order_by('-presentation__date').first()
                        print(f"Latest presentation date: {presentation.presentation.date if presentation else 'None'}")
                elif forecast.source_type == 'lcn':
                    receipt = LCN.objects.filter(
                        id=forecast.source_id
                    ).select_related('entity', 'client').first()
                    print(f"LCN found: {receipt.lcn_number if receipt else 'None'}")
                    print(f"LCN Amount: {receipt.amount if receipt else 'None'}")
                    if receipt:
                        # Get latest presentation
                        presentation = receipt.lcn_presentations.select_related(
                            'presentation'
                        ).order_by('-presentation__date').first()
                        print(f"Latest presentation date: {presentation.presentation.date if presentation else 'None'}")

                if receipt:
                    # Calculate amount based on forecast type
                    if forecast.label.startswith('Expected'):
                        amount = (forecast.credit or Decimal('0.00')) - (forecast.debit or Decimal('0.00'))
                    else:
                        # For discounted receipts, use the receipt amount directly
                        amount = receipt.amount
                    
                    print(f"Calculated amount: {amount}")

                    forecast_data = {
                        'type': 'Expected Payment' if forecast.label.startswith('Expected') else 'Discounted Receipt',
                        'number': receipt.get_receipt_number(),
                        'entity': receipt.entity.name,
                        'client': receipt.client.name,
                        'bank': receipt.get_issuing_bank_display(),
                        'due_date': receipt.due_date.strftime('%Y-%m-%d') if receipt.due_date else None,
                        'presentation_date': presentation.presentation.date.strftime('%Y-%m-%d') if presentation else None,  # Added presentation date
                        'amount': float(amount),
                        'is_representation': False,
                        'id': str(receipt.id),  
                        'receipt_type': receipt.__class__.__name__      
                    }
                    forecasts_data.append(forecast_data)
                    print("Added forecast data:", forecast_data)

            return JsonResponse({
                'status': 'success',
                'forecasts': forecasts_data
            })
            
        except Exception as e:
            print(f"Error processing forecasts: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        

class SupplierForecastView(View):
    """View for loading supplier payment forecasts for a specific date"""
    def get(self, request):
        try:
            date = request.GET.get('date')
            bank_id = request.GET.get('bank')
            
            print(f"\n=== Loading Supplier Payment Forecasts for {date} ===")
            print(f"Bank ID: {bank_id}")
            
            forecast_date = datetime.strptime(date, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            
            # Get forecasts for this date
            payment_forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False,
                source_type__in=['supplier_check', 'contract_domiciliation']  
            )
            
            print(f"Found {payment_forecasts.count()} payment forecasts")
            forecasts_data = []
            total_amount = Decimal('0.00')
            
            for forecast in payment_forecasts:
                print(f"\n--- Processing Forecast ---")
                print(f"Forecast ID: {forecast.id}")
                print(f"Amount: {forecast.debit}")
                
                if forecast.source_type == 'supplier_check':
                    # Get the check details
                    try:
                        check = Check.objects.select_related(
                            'beneficiary', 'checker', 'cause'
                        ).get(id=forecast.source_id)
                        
                        print(f"Found Check {check.position}")
                        print(f"Payment due: {check.payment_due}")
                        print(f"Checker type: {check.checker.type}")
                        
                        # Get supplier balance using existing function
                        supplier_balance = get_supplier_balance(check.beneficiary)
                        
                        forecast_data = {
                            'type': 'LCN' if check.checker.type == 'LCN' else 'Check',
                            'payment': {
                                'reference': check.position,
                                'amount': float(forecast.debit),
                                'id': str(check.id),
                                'status': check.status,
                                'status_display': check.get_status_display()
                            },
                            'supplier': {
                                'name': check.beneficiary.name,
                                'balance': float(supplier_balance['balance'])
                            },
                            'dates': {
                                'due_date': check.payment_due.strftime('%Y-%m-%d'),
                                'forecast_date': forecast.date.strftime('%Y-%m-%d'),
                                'delivered_at': check.delivered_at.strftime('%Y-%m-%d') if check.delivered_at else None,
                                'printed_at': check.printed_at.strftime('%Y-%m-%d') if check.printed_at else None
                            },
                            'invoice': {
                                'ref': check.cause.ref if check.cause else None,
                                'id': str(check.cause.id) if check.cause else None
                            },
                            'status': check.status,
                            'status_display': check.get_status_display()
                        }

                        forecasts_data.append(forecast_data)
                        total_amount += forecast.debit
                        print(f"Added to forecast data. Total now: {total_amount}")
                        
                        
                    except Check.DoesNotExist:
                        print(f"Check {forecast.source_id} not found")
                        continue
                
            
                elif forecast.source_type == 'contract_domiciliation':
                    try:
                        contract = Contract.objects.select_related('supplier').get(id=forecast.source_id)
                        print(f"Contract: {contract.reference}")
                        
                        forecast_data = {
                            'type': 'Contract Payment',
                            'payment': {
                                'reference': forecast.reference,
                                'amount': float(forecast.debit),
                                'status': 'pending',
                                'status_display': 'Pending Payment'
                            },
                            'dates': {
                                'due_date': forecast.date.strftime('%Y-%m-%d'),
                                'forecast_date': forecast.date.strftime('%Y-%m-%d')
                            },
                            'supplier': {
                                'name': contract.supplier.name,
                                'balance': float(get_supplier_balance(contract.supplier)['balance'])
                            },
                            'contract': {
                                'reference': contract.reference,
                                'id': str(contract.id),
                                'periodicity': contract.get_periodicity_display()
                            }
                        }
                        forecasts_data.append(forecast_data)
                        total_amount += forecast.debit
                        print(f"Added to forecast data. Total now: {total_amount}")
                        
                    except Contract.DoesNotExist:
                        print(f"Contract {forecast.source_id} not found")
                        continue

                print(f"Final forecasts data: {forecasts_data}")
                print(f"Total amount: {total_amount}")

            return JsonResponse({
                'status': 'success',
                'forecasts': forecasts_data,
                'total': float(total_amount)
            })
            
        except Exception as e:
            print(f"Error in SupplierForecastView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class ContractPaymentActionView(View):
    def post(self, request, contract_id):
        try:
            print("\n=== Processing Contract Payment Action ===")
            data = json.loads(request.body)
            action = data.get('action')
            payment_date = data.get('date')
            forecast_date = data.get('forecast_date')
            print(f"Action: {action}")
            print(f"Payment Date: {payment_date}")
            print(f"Forecast Date: {forecast_date}")
            
            contract = get_object_or_404(Contract, id=contract_id)
            
            # Find the corresponding direct debit
            direct_debit = DirectDebit.objects.filter(
                contract=contract,
                due_date=forecast_date,
                status=DirectDebit.PENDING
            ).select_related('forecast').first()
            
            if not direct_debit:
                print(f"No pending direct debit found for date {forecast_date}")
                raise ValidationError(f"No pending direct debit found for date {forecast_date}")

            print(f"Found direct debit {direct_debit.id}")
            
            with transaction.atomic():
                if action == 'pay':
                    print("Marking as paid...")
                    direct_debit.mark_as_processed(payment_date)
                    message = "Payment processed successfully"
                    
                elif action == 'reject':
                    print("Marking as rejected...")
                    direct_debit.mark_as_rejected(
                        payment_date,
                        data.get('rejection_reason'),
                        data.get('rejection_note', '')
                    )
                    message = "Payment rejection processed"
                    
                else:
                    raise ValidationError("Invalid action")
                    
            return JsonResponse({
                'status': 'success',
                'message': message
            })
                
        except Exception as e:
            print(f"Error processing contract payment: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        

def get_cash_statement_entries(start_date=None, end_date=None):
    """Generate statement entries for cash transactions"""
    print("\n=== Getting Cash Statement Entries ===")
    
    entries = []
    try:
        # Get configuration
        config = CashConfiguration.get_config()
        
        # Add deposits
        deposits = CashDeposit.objects.all()
        if start_date:
            deposits = deposits.filter(date__gte=start_date)
        if end_date:
            deposits = deposits.filter(date__lte=end_date)
            
        for deposit in deposits:
            entries.append({
                'date': deposit.date,
                'label': f"Cash deposit {deposit.reference}",
                'type': 'CASH_DEPOSIT',
                'debit': None,
                'credit': deposit.amount,
                'reference': deposit.reference,
                'source_type': 'cash_deposit',
                'source_id': deposit.id,
                'can_transfer': False,
                'is_transferred': False,
                'details': {
                    'notes': deposit.notes,
                    'recorded_by': deposit.recorded_by.username
                }
            })
            
        # Add payments
        payments = CashPayment.objects.all()
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)
            
        for payment in payments:
            entries.append({
                'date': payment.payment_date,
                'label': f"Cash payment for invoice {payment.invoice.ref}",
                'type': 'CASH_PAYMENT',
                'debit': payment.amount,
                'credit': None,
                'reference': payment.reference,
                'source_type': 'cash_payment',
                'source_id': payment.id,
                'can_transfer': False,
                'is_transferred': False,
                'invoice': {
                    'ref': payment.invoice.ref,
                    'id': str(payment.invoice.id),
                    'supplier': payment.invoice.supplier.name
                }
            })
        
        # Add cash expenses
        expenses = CashExpense.objects.all()
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)
            
        for expense in expenses:
            entries.append({
                'date': expense.date,
                'label': f"Cash expense ({expense.get_expense_type_display()})",
                'type': 'CASH_EXPENSE',
                'debit': expense.amount,
                'credit': None,
                'reference': expense.reference,
                'source_type': 'cash_expense',
                'source_id': expense.id,
                'can_transfer': False,
                'is_transferred': False,
                'details': {
                    'expense_type': expense.get_expense_type_display(),
                    'account': expense.expense_account,
                    'notes': expense.notes,
                    'recorded_by': expense.recorded_by.username
                }
            })
            
        # Sort entries by date
        entries.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate running balance
        balance = config.current_balance
        for entry in entries:
            balance -= (entry['debit'] or 0) - (entry['credit'] or 0)
            entry['balance'] = balance
            
        return entries
        
    except Exception as e:
        print(f"Error getting cash statement entries: {str(e)}")
        return []
