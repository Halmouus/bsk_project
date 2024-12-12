from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import BankAccount, BankStatement, AccountingEntry
import json
from decimal import Decimal
from django.db.models import Q

class BankStatementView(View):
    """View for displaying bank statements"""
    def get(self, request, pk):
        try:
            bank_account = get_object_or_404(BankAccount, pk=pk)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get statement entries
            entries = BankStatement.get_statement(
                bank_account=bank_account,
                start_date=start_date,
                end_date=end_date
            )
            
            context = {
                'bank_account': bank_account,
                'entries': entries,
                'total_debit': sum(entry['debit'] or 0 for entry in entries),
                'total_credit': sum(entry['credit'] or 0 for entry in entries),
                'final_balance': entries[-1]['balance'] if entries else Decimal('0.00')
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string(
                    'bank/partials/statement_table.html',
                    context,
                    request=request
                )
                return JsonResponse({'html': html})
            
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