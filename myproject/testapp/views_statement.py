from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import BankAccount, BankStatement, AccountingEntry, BankFeeType
import json
from decimal import Decimal
from django.db.models import Q
from datetime import datetime, date
import calendar

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
                end_date=end_date
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