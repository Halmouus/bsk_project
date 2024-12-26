from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import PresentationReceipt, BankAccount, BankStatement, AccountingEntry, BankFeeType, ForecastStatement, CheckReceipt, LCN, ReceiptHistory, ContentType
import json
from decimal import Decimal
from django.db.models import Q
from datetime import datetime, date
import calendar
from calendar import monthcalendar
from .services.forecast import PaymentForecastService


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
        selected_banks = request.GET.getlist('banks', [])
        print(f"Selected banks: {selected_banks}")
        
        # Get bank accounts
        if selected_banks:
            bank_accounts = BankAccount.objects.filter(id__in=selected_banks)
        else:
            bank_accounts = BankAccount.objects.none()

        print(f"Filtered bank accounts: {[b.account_number for b in bank_accounts]}")

        # Build calendar data
        calendar_data = self._build_calendar_data(year, month, bank_accounts)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'calendar': calendar_data})

        return render(request, 'bank/calendar.html', {
            'calendar': calendar_data,
            'bank_accounts': BankAccount.objects.filter(is_active=True),
            'selected_banks': selected_banks,
            'year': year,
            'month': month
        })

    def _build_calendar_data(self, year, month, bank_accounts):
        print(f"\n=== Building Calendar Data for {month}/{year} ===")
        print(f"Processing banks: {[b.account_number for b in bank_accounts]}")

        # Get calendar weeks
        cal = monthcalendar(year, month)
        calendar_data = []

        # Keep track of cumulative forecasts for each bank
        bank_forecasts = {bank.id: Decimal('0.00') for bank in bank_accounts}

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
                    
                    # Get actual balance
                    actual_statement = BankStatement.get_statement(
                        bank_account=bank,
                        end_date=current_date,
                        include_forecasts=False
                    )
                    actual_balance = actual_statement[0]['balance'] if actual_statement else Decimal('0.00')
                    print(f"Actual balance: {actual_balance}")

                    # Get forecasted transactions for this date
                    forecasts = ForecastStatement.objects.filter(
                        bank_account=bank,
                        date=current_date,
                        is_processed=False
                    )
                    print(f"Found {forecasts.count()} forecasts")

                    # Calculate forecast impact for this day
                    day_forecast_impact = Decimal('0.00')
                    forecast_data = []
                    for f in forecasts:
                        print(f"Processing forecast: {f.label}")
                        amount = (f.credit or Decimal('0.00')) - (f.debit or Decimal('0.00'))
                        day_forecast_impact += amount
                        forecast_data.append({
                            'label': f.label,
                            'credit': float(f.credit) if f.credit else None,
                            'debit': float(f.debit) if f.debit else None,
                            'reference': f.reference
                        })

                    # Update cumulative forecast for this bank
                    bank_forecasts[bank.id] += day_forecast_impact

                    # Calculate forecasted balance
                    forecasted_balance = actual_balance + bank_forecasts[bank.id]
                    print(f"Actual balance: {actual_balance}")
                    print(f"Cumulative forecast impact: {bank_forecasts[bank.id]}")
                    print(f"Forecasted balance: {forecasted_balance}")

                    bank_data.append({
                        'bank': {
                            'id': str(bank.id),
                            'name': bank.bank,
                            'account_number': bank.account_number
                        },
                        'balance': float(forecasted_balance),  # Use forecasted balance here
                        'forecasts': forecast_data,
                        'has_forecasts': forecasts.exists()
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

class CalendarForecastView(View):
    """View for loading forecasts for a specific date and bank"""
    def get(self, request):
        date = request.GET.get('date')
        bank_id = request.GET.get('bank')
        
        print(f"\n=== Loading Forecasts for {date} ===")
        
        try:
            forecast_date = datetime.strptime(date, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            
            forecasts = []
            total_expected = Decimal('0.00')    # Initialize here!
            total_discounted = Decimal('0.00')  # Initialize here!
            
            # Get regular payment forecasts
            payment_forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False
            )
            
            # Add payment forecasts to the list
            for forecast in payment_forecasts:
                amount = forecast.amount or Decimal('0.00')
                if forecast.label.startswith('Expected'):
                    total_expected += amount
                else:
                    total_discounted += amount
                
                # Get receipt data if available
                receipt_data = {}
                if forecast.source_id:
                    if forecast.source_type == 'checkreceipt':
                        receipt = CheckReceipt.objects.filter(id=forecast.source_id).select_related('client', 'entity').first()
                        if receipt:
                            presentation = PresentationReceipt.objects.filter(checkreceipt=receipt).select_related('presentation').first()
                            receipt_data = self._get_receipt_data(receipt, presentation)
                    elif forecast.source_type == 'lcn':
                        receipt = LCN.objects.filter(id=forecast.source_id).select_related('client', 'entity').first()
                        if receipt:
                            presentation = PresentationReceipt.objects.filter(lcn=receipt).select_related('presentation').first()
                            receipt_data = self._get_receipt_data(receipt, presentation)
                    
                forecasts.append({
                    'type': 'Expected Payment' if forecast.label.startswith('Expected') else 'Discounted Receipt',
                    'number': forecast.reference,
                    'entity': forecast.label,
                    'bank': bank_account.bank,
                    'amount': float(amount),
                    **receipt_data
                })
            
            # Rest of your existing code for discounted receipts...
            discounted_receipts = PresentationReceipt.objects.filter(
                presentation__bank_account=bank_account,
                presentation__date=forecast_date,
                presentation__presentation_type='DISCOUNT'
            ).select_related(
                'presentation',
                'checkreceipt',
                'lcn',
                'checkreceipt__entity',
                'checkreceipt__client',
                'lcn__entity',
                'lcn__client'
            )
            
            # Your existing code for processing discounted_receipts...
            
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
            print(f"Error loading forecasts: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    def _get_receipt_data(self, receipt, presentation):
        """Helper method to get receipt data"""
        return {
            'client': receipt.client.name if receipt.client else None,
            'receipt_type': 'Check' if isinstance(receipt, CheckReceipt) else 'LCN',
            'due_date': receipt.due_date.strftime('%Y-%m-%d') if receipt.due_date else None,
            'issuing_bank': receipt.issuing_bank,
            'receipt_number': receipt.get_receipt_number(),
            'presentation_ref': presentation.presentation.bank_reference if presentation and presentation.presentation else None,
            'presentation_date': presentation.presentation.date.strftime('%Y-%m-%d') if presentation and presentation.presentation and presentation.presentation.date else None
        }
