from django.views.generic import ListView, View
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import BankAccount, BankFeeTransaction, BankStatement, CashConfiguration, CashDeposit, CashExpense, CashPayment, InterBankTransfer, Invoice, Presentation, TransferredRecord
from django.contrib import messages
import json
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum
from datetime import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _


class BankAccountListView(ListView):
    model = BankAccount
    template_name = 'bank/bank_list.html'
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = BankAccount.BANK_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        print("\n=== Getting Bank Account List ===")
        
        # Apply filters if any
        bank = self.request.GET.get('bank')
        if bank:
            queryset = queryset.filter(bank=bank)
            
        account_type = self.request.GET.get('type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(is_active=status == 'active')
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(account_number__icontains=search)

        for account in queryset:
            entries = BankStatement.get_statement(account)
            account.current_balance = entries[0]['balance'] if entries else Decimal('0.00')
            
        return queryset

class BankAccountCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    data[field] = Decimal(str(data[field]))
                else:
                    data[field] = None
            
            # Create bank account
            account = BankAccount.objects.create(
                bank=data['bank'],
                account_number=data['account_number'],
                accounting_number=data['accounting_number'],
                journal_number=data['journal_number'],
                city=data['city'],
                if_code=data['if_code'],
                ice_code=data['ice_code'],
                account_type=data['account_type'],
                is_active=data.get('is_active', True),
                is_current=data.get('is_current', False),
                bank_overdraft=data['bank_overdraft'],
                overdraft_fee=data['overdraft_fee'],
                has_check_discount_line=data.get('has_check_discount_line', False),
                check_discount_line_amount=data['check_discount_line_amount'],
                has_lcn_discount_line=data.get('has_lcn_discount_line', False),
                lcn_discount_line_amount=data['lcn_discount_line_amount'],
                stamp_fee_per_receipt=data['stamp_fee_per_receipt']
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account created successfully',
                'id': str(account.id)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountUpdateView(View):
    def get(self, request, pk):
        account = get_object_or_404(BankAccount, pk=pk)
        return JsonResponse({
            'id': str(account.id),
            'bank': account.bank,
            'account_number': account.account_number,
            'accounting_number': account.accounting_number,
            'journal_number': account.journal_number,
            'city': account.city,
            'if_code': account.if_code,
            'ice_code': account.ice_code,
            'account_type': account.account_type,
            'is_active': account.is_active,
            'is_current': account.is_current,
            'bank_overdraft': str(account.bank_overdraft) if account.bank_overdraft else None,
            'overdraft_fee': str(account.overdraft_fee) if account.overdraft_fee else None,
            'has_check_discount_line': account.has_check_discount_line,
            'check_discount_line_amount': str(account.check_discount_line_amount) if account.check_discount_line_amount else None,
            'has_lcn_discount_line': account.has_lcn_discount_line,
            'lcn_discount_line_amount': str(account.lcn_discount_line_amount) if account.lcn_discount_line_amount else None,
            'stamp_fee_per_receipt': str(account.stamp_fee_per_receipt) if account.stamp_fee_per_receipt else None
        })

    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    setattr(account, field, Decimal(str(data[field])))
                else:
                    setattr(account, field, None)
            
            # Update other fields
            account.bank = data['bank']
            account.account_number = data['account_number']
            account.accounting_number = data['accounting_number']
            account.journal_number = data['journal_number']
            account.city = data['city']
            account.if_code = data['if_code']
            account.ice_code = data['ice_code']
            account.account_type = data['account_type']
            account.is_active = data.get('is_active', True)
            account.is_current = data.get('is_current', False)
            account.has_check_discount_line = data.get('has_check_discount_line', False)
            account.has_lcn_discount_line = data.get('has_lcn_discount_line', False)
            
            account.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountDeleteView(View):
    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            account.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountDeactivateView(View):
    def post(self, request, pk):
        try:
            account = BankAccount.objects.get(pk=pk)
            
            # Check for active checkers
            if account.checker_set.filter(is_active=True).exists():
                return JsonResponse(
                    {'error': 'Cannot deactivate account with active checkers'}, 
                    status=400
                )
            
            account.is_active = False
            account.save()
            
            return JsonResponse({'message': _('Account deactivated successfully')})
            
        except BankAccount.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class BankAccountFilterView(View):
    def get(self, request):
        try:
            # Start with all accounts
            queryset = BankAccount.objects.all()
            print("Initial QuerySet Count:", queryset.count())  # Debug log
            
            # Apply bank filter
            bank = request.GET.get('bank')
            if bank:
                print("Filter by bank:", bank)  # Debug log
                queryset = queryset.filter(bank=bank)

            # Apply account type filter
            account_type = request.GET.get('type')
            if account_type:
                print("Filter by account type:", account_type)  # Debug log
                queryset = queryset.filter(account_type=account_type)

            # Apply status filter
            status = request.GET.get('status')
            if status:
                print("Filter by status:", status)  # Debug log
                queryset = queryset.filter(is_active=status == 'active')

            # Apply search filter
            search = request.GET.get('search')
            if search:
                print("Filter by search term:", search)  # Debug log
                queryset = queryset.filter(account_number__icontains=search)

            # Final count before rendering
            print("Filtered QuerySet Count:", queryset.count())  # Debug log

            # Render rows
            html = render_to_string(
                'bank/partials/accounts_table.html',
                {'accounts': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            print("Error in filter view:", str(e))  # Debug log
            return JsonResponse({'error': str(e)}, status=500)



def bank_account_autocomplete(request):
    try:
        search = request.GET.get('search', '')
        print(f"[BankAutocomplete] Search term: {search}")  # Debug log
        
        accounts = BankAccount.objects.filter(
            Q(account_number__icontains=search) |
            Q(bank__icontains=search),
            is_active=True,
            account_type='national'
        )[:10]
        
        print(f"[BankAutocomplete] Found {accounts.count()} matches")  # Debug log
        
        results = [{
            'id': str(account.id),
            'bank': account.bank,
            'account_number': account.account_number
        } for account in accounts]
        
        print(f"[BankAutocomplete] Returning results: {results}")  # Debug log
        return JsonResponse(results, safe=False)
        
    except Exception as e:
        print(f"[BankAutocomplete] Error: {str(e)}")  # Debug log
        return JsonResponse({
            'error': 'Failed to fetch bank accounts',
            'details': str(e)
        }, status=500)

class BankFeeCreateView(View):
    """Handle creation of bank fee transactions"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create fee transaction
                fee = BankFeeTransaction.objects.create(
                    bank_account_id=data['bank_account'],
                    fee_type_id=data['fee_type'],
                    date=data['date'],
                    related_presentation_id=data.get('related_presentation'),
                    raw_amount=Decimal(str(data['raw_amount'])),
                    vat_rate=Decimal(str(data['vat_rate'])) if data['vat_rate'] else None,
                    vat_included=data['vat_included'],
                    vat_amount=Decimal(str(data.get('vat_amount', '0.00'))),
                    total_amount=Decimal(str(data.get('total_amount', '0.00')))
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Bank fee recorded successfully',
                    'id': str(fee.id)
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankFeeDeleteView(View):
    """Handle deletion of bank fee transactions"""
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                fee = get_object_or_404(BankFeeTransaction, pk=pk)
                fee.delete()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Bank fee deleted successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PresentationAutocompleteView(View):
    """Autocomplete for presentation references"""
    
    def get(self, request):
        try:
            term = request.GET.get('term', '')
            presentations = Presentation.objects.filter(
                Q(bank_reference__icontains=term) |
                Q(id__icontains=term)
            ).order_by('-date')[:10]
            
            results = [{
                'id': str(pres.id),
                'text': f"{pres.bank_reference or f'Pres. #{pres.id}'} ({pres.date})"
            } for pres in presentations]
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

class CashConfigurationView(View):
    """View for managing cash configuration"""
    def get(self, request):
        print("\n=== Cash Configuration View ===")
        try:
            config = CashConfiguration.objects.first()
            print(f"Current config: {config}")

            bank_accounts = BankAccount.objects.filter(is_active=True)
            
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            reference = request.GET.get('reference')
            supplier = request.GET.get('supplier')
            types = request.GET.get('types')
            min_amount = request.GET.get('min_amount')
            max_amount = request.GET.get('max_amount')
            
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            print(f"Filter params - start: {start_date}, end: {end_date}, reference: {reference}, supplier: {supplier}")
            print(f"Types: {types}, min: {min_amount}, max: {max_amount}, ajax: {is_ajax}")
            
            # Get all transactions
            deposits = CashDeposit.objects.all()
            payments = CashPayment.objects.select_related('invoice', 'invoice__supplier')
            expenses = CashExpense.objects.all()
            
            # Apply date filters if provided
            if start_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                deposits = deposits.filter(date__gte=start_date_obj)
                payments = payments.filter(payment_date__gte=start_date_obj)
                expenses = expenses.filter(date__gte=start_date_obj)
                
            if end_date:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                deposits = deposits.filter(date__lte=end_date_obj)
                payments = payments.filter(payment_date__lte=end_date_obj)
                expenses = expenses.filter(date__lte=end_date_obj)
            
            # Apply reference filter
            if reference:
                deposits = deposits.filter(reference__icontains=reference)
                payments = payments.filter(reference__icontains=reference)
                expenses = expenses.filter(reference__icontains=reference)
                
            
            # Sort by date for processing
            deposits = deposits.order_by('date')
            payments = payments.order_by('payment_date')
            expenses = expenses.order_by('date')
            
            # Create a list of all transactions in chronological order
            all_transactions = []
            
            # Apply transaction type filter - only add transactions of selected types
            selected_types = types.split(',') if types else ['deposit', 'payment', 'expense']
            
            if 'deposit' in selected_types:
                for deposit in deposits:
                    all_transactions.append({
                        'id': deposit.id,
                        'source_id': deposit.id,
                        'date': deposit.date,
                        'reference': deposit.reference,
                        'type': 'deposit',
                        'notes': deposit.notes,
                        'description': deposit.notes if deposit.notes else f"Cash deposit {deposit.reference}",
                        'credit': deposit.amount,
                        'debit': None,
                        'source_bank': deposit.source_bank_account,
                        'raw_date': deposit.date,
                        'amount': deposit.amount  # For amount filtering
                    })
                    
            if 'payment' in selected_types:
                # Apply supplier filter only to payments, before adding them to all_transactions
                filtered_payments = payments
                if supplier:
                    filtered_payments = payments.filter(invoice__supplier__name__icontains=supplier)
                    
                for payment in filtered_payments:
                    all_transactions.append({
                        'id': payment.id,
                        'source_id': payment.id,
                        'date': payment.payment_date,
                        'reference': payment.reference,
                        'type': 'payment',
                        'invoice': payment.invoice,
                        'supplier': payment.invoice.supplier.name,  # Include supplier name
                        'description': f"Invoice {payment.invoice.ref}",
                        'credit': None,
                        'debit': payment.amount,
                        'raw_date': payment.payment_date,
                        'amount': payment.amount  # For amount filtering
                    })
                    
            if 'expense' in selected_types:
                for expense in expenses:
                    all_transactions.append({
                        'id': expense.id,
                        'source_id': expense.id,
                        'date': expense.date,
                        'reference': expense.reference,
                        'type': 'expense',
                        'notes': expense.notes,
                        'description': expense.notes if expense.notes else f"{expense.get_expense_type_display()}",
                        'credit': None,
                        'debit': expense.amount,
                        'expense_account': expense.expense_account,
                        'raw_date': expense.date,
                        'amount': expense.amount  # For amount filtering
                    })
                    
            # Apply amount range filter
            if min_amount or max_amount:
                filtered_transactions = []
                for t in all_transactions:
                    amount = t.get('amount', 0)
                    if min_amount and float(amount) < float(min_amount):
                        continue
                    if max_amount and float(amount) > float(max_amount):
                        continue
                    filtered_transactions.append(t)
                all_transactions = filtered_transactions
                
            # Sort all transactions by date (oldest first for balance calculation)
            all_transactions.sort(key=lambda x: x['raw_date'])
            
            # Calculate proper running balance
            # Make absolutely sure we're only calculating balance from actual transactions
            
            # Starting balance calculation (properly considering transaction effects)
            starting_balance = config.current_balance
            for t in all_transactions:
                if t['type'] == 'deposit':
                    starting_balance -= t['credit']  # Subtract deposits
                else:
                    starting_balance += t['debit']   # Add payments/expenses

            # Now calculate the running balance for each transaction
            running_balance = starting_balance
            statement_entries = []

            print(f"Starting balance before transactions: {starting_balance}")
            for transaction in all_transactions:
                # Create a new dictionary for the display entry to avoid modifying original
                entry = transaction.copy()
                
                # Update running balance
                if transaction['type'] == 'deposit':
                    running_balance += transaction['credit']  # Deposits increase cash
                else:
                    running_balance -= transaction['debit']   # Payments/expenses decrease cash
                
                entry['balance'] = running_balance
                print(f"Transaction: {transaction['type']} - {transaction['raw_date']} - "+
                    f"Credit: {transaction['credit']} - Debit: {transaction['debit']} - "+
                    f"New Balance: {running_balance}")
                
                statement_entries.append(entry)
            
            # Reverse for display (newest first)
            statement_entries.reverse()
            
            # Generate accounting entries
            accounting_entries = []
            
            # Add entries for deposits
            for deposit in deposits:
                bank_account = deposit.source_bank_account
                print(f"Bank account for accounting: {bank_account}")
                accounting_entries.extend([
                    {
                        'date': deposit.date,
                        'journal': config.journal_code if config else '08',
                        'account_code': config.accounting_code if config else '5300',
                        'description': f"Cash deposit {deposit.reference}",
                        'debit': deposit.amount,
                        'credit': None,
                        'reference': deposit.reference
                    },
                    {
                        'date': deposit.date,
                        'journal': config.journal_code if config else '08',
                        'account_code': bank_account.accounting_number if bank_account else '5169',
                        'description': f"Cash deposit {deposit.reference}",
                        'debit': None,
                        'credit': deposit.amount,
                        'reference': deposit.reference
                    }
                ])
                
            # Add entries for payments
            for payment in payments:
                accounting_entries.extend([
                    {
                        'date': payment.payment_date,
                        'journal': config.journal_code if config else '08',
                        'account_code': payment.invoice.supplier.accounting_code,
                        'description': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': payment.amount,
                        'credit': None,
                        'reference': payment.reference
                    },
                    {
                        'date': payment.payment_date,
                        'journal': config.journal_code if config else '08',
                        'account_code': config.accounting_code if config else '5300',
                        'description': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': None,
                        'credit': payment.amount,
                        'reference': payment.reference
                    }
                ])

            # Add expense entries
            for expense in expenses:
                accounting_entries.extend([
                    {
                        'date': expense.date,
                        'journal': config.journal_code if config else '08',
                        'account_code': expense.expense_account,
                        'description': f"Expense {expense.reference}",
                        'debit': expense.amount,
                        'credit': None,
                        'reference': expense.reference
                    },
                    {
                        'date': expense.date,
                        'journal': config.journal_code if config else '08',
                        'account_code': config.accounting_code if config else '5300',
                        'description': f"Expense {expense.reference}",
                        'debit': None,
                        'credit': expense.amount,
                        'reference': expense.reference
                    }
                ])
            
            # Sort accounting entries by date (newest first)
            accounting_entries.sort(key=lambda x: x['date'], reverse=True)
            
            # Calculate totals
            total_credit = sum(entry['credit'] or 0 for entry in statement_entries)
            total_debit = sum(entry['debit'] or 0 for entry in statement_entries)
            
            total_deposits_amount = deposits.aggregate(total=Sum('amount'))['total'] or 0
            total_payments_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
            total_expenses_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
            
            # Handle AJAX request for filtered data
            if is_ajax:
                filter_type = request.GET.get('filter_type', 'statement')
                
                if filter_type == 'statement':
                    # Calculate totals from the filtered and displayed transactions only
                    filtered_total_credit = sum(entry['credit'] or 0 for entry in statement_entries)
                    filtered_total_debit = sum(entry['debit'] or 0 for entry in statement_entries)
                    
                    html = render_to_string(
                        'bank/partials/cash_statement_table.html',
                        {
                            'entries': statement_entries,
                            'filtered_total_credit': filtered_total_credit,
                            'filtered_total_debit': filtered_total_debit
                        },
                        request=request
                    )
                    return JsonResponse({
                        'html': html,
                        'totals': {
                            'filtered_credit': float(filtered_total_credit),
                            'filtered_debit': float(filtered_total_debit),
                            'total_count': len(statement_entries)
                        }
                    })
                elif filter_type == 'accounting':
                    total_debit = sum(entry['debit'] or 0 for entry in accounting_entries)
                    total_credit = sum(entry['credit'] or 0 for entry in accounting_entries)
                    html = render_to_string(
                        'bank/partials/cash_accounting_table.html',
                        {'entries': accounting_entries, 'total_debit': total_debit, 'total_credit': total_credit},
                        request=request
                    )
                    return JsonResponse({'html': html})
            
            # Normal page load
            context = {
                'config': config,
                'current_balance': float(config.current_balance) if config else 0,
                'max_threshold_value': config.max_payment_threshold if config else 5000.00,
                'total_deposits': float(total_deposits_amount),
                'total_payments': float(total_payments_amount),
                'total_expenses': float(total_expenses_amount),
                'expense_types': dict(CashExpense.EXPENSE_TYPE_CHOICES),
                'statement_entries': statement_entries,
                'accounting_entries': accounting_entries,
                'total_credit': float(total_credit),
                'total_debit': float(total_debit),
                'bank_accounts': bank_accounts
            }
            
            print(f"\nDebug Config object: {config}")
            print(f"Config max_payment_threshold: {config.max_payment_threshold if config else 'None'}")
            
            return render(request, 'bank/cash_management.html', context)
            
        except Exception as e:
            print(f"Error in cash configuration view: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, str(e))
            return redirect('home')

    def get_accounting_entries(self, transactions):
        """Generate accounting entries from transactions"""
        entries = []
        config = CashConfiguration.objects.first()
        print(f"Current config: {config}")
        print(f"Max payment threshold: {config.max_payment_threshold if config else 'None'}")
        
        
        for t in transactions:
            if t.get('credit'):  # Deposit
                entries.extend([
                    {
                        'date': t['date'],
                        'journal': config.journal_code,
                        'account_code': config.accounting_code,
                        'description': f"Cash deposit {t['reference']}",
                        'debit': t['credit'],
                        'credit': None,
                        'reference': t['reference']
                    },
                    {
                        'date': t['date'],
                        'journal': config.journal_code,
                        'account_code': '5161',  # Transit account
                        'description': f"Cash deposit {t['reference']}",
                        'debit': None,
                        'credit': t['credit'],
                        'reference': t['reference']
                    }
                ])
            else:  # Payment
                entries.extend([
                    {
                        'date': t['date'],
                        'journal': config.journal_code,
                        'account_code': t['invoice'].supplier.accounting_code,
                        'description': f"Cash payment for invoice {t['invoice'].ref}",
                        'debit': t['debit'],
                        'credit': None,
                        'reference': t['reference']
                    },
                    {
                        'date': t['date'],
                        'journal': config.journal_code,
                        'account_code': config.accounting_code,
                        'description': f"Cash payment for invoice {t['invoice'].ref}",
                        'debit': None,
                        'credit': t['debit'],
                        'reference': t['reference']
                    }
                ])
        
        return entries

    def post(self, request):
        print("\n=== Saving Cash Configuration ===")
        try:
            data = request.POST
            config = CashConfiguration.objects.first() or CashConfiguration()
            
            config.accounting_code = data.get('accounting_code')
            config.journal_code = data.get('journal_code')
            config.max_payment_threshold = Decimal(data.get('max_payment_threshold', '5000.00'))
            
            config.full_clean()
            config.save()
            
            messages.success(request, "Cash configuration saved successfully")
            return redirect('cash-configuration')
            
        except Exception as e:
            print(f"Error saving cash configuration: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')

class CashDepositView(View):
    """View for managing cash deposits"""
    def get(self, request):
        print("\n=== Cash Deposit View ===")
        try:
            config = CashConfiguration.get_config()
            deposits = CashDeposit.objects.all().select_related('recorded_by')
            
            # Get date range filters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if start_date:
                deposits = deposits.filter(date__gte=start_date)
            if end_date:
                deposits = deposits.filter(date__lte=end_date)
            
            context = {
                'deposits': deposits,
                'current_balance': float(config.current_balance),
                'total_deposits': deposits.aggregate(
                    total=Sum('amount')
                )['total'] or 0
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'bank/partials/cash_deposits_table.html',
                        context,
                        request=request
                    )
                })
            
            return render(request, 'bank/cash_deposits.html', context)
            
        except Exception as e:
            print(f"Error in cash deposit view: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')

    def post(self, request):
        print("\n=== Recording Cash Deposit ===")
        try:
            data = json.loads(request.body)
            source_type = data.get('source_type')
            
            # Create deposit instance
            deposit = CashDeposit(
                amount=Decimal(data.get('amount')),
                date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
                reference=data.get('reference'),
                notes=data.get('notes', ''),
                recorded_by=request.user
            )
            
            # Handle source type
            if source_type == 'bank':
                bank_account_id = data.get('bank_account_id')
                if not bank_account_id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Bank account is required'
                    }, status=400)
                    
                bank_account = get_object_or_404(BankAccount, id=bank_account_id)
                deposit.source_type = 'bank'
                deposit.source_bank_account = bank_account
                deposit.source_account_code = bank_account.accounting_number
                
                # Check if bank has enough balance
                if bank_account.get_current_balance() < deposit.amount:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Insufficient funds in bank account'
                    }, status=400)
                
            elif source_type == 'other':
                account_code = data.get('account_code')
                if not account_code:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Account code is required'
                    }, status=400)
                    
                deposit.source_type = 'other'
                deposit.source_account_code = account_code
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid source type'
                }, status=400)
                
            deposit.full_clean()
            deposit.save()
            
            if source_type == 'bank' and deposit.source_bank_account:
                print(f"Cash withdrawal from bank account {deposit.source_bank_account.account_number}: {deposit.amount}")
            
            messages.success(request, "Cash deposit recorded successfully")
            return JsonResponse({'status': 'success', 'message': _('Deposit recorded successfully')})
            
        except Exception as e:
            print(f"Error recording cash deposit: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CashPaymentView(View):
    """View for managing cash payments"""
    def get(self, request):
        print("\n=== Cash Payment View ===")
        try:
            config = CashConfiguration.get_config()
            
            # Get unpaid cash-allowed invoices
            invoices = Invoice.objects.filter(
                cash_payment_allowed=True,
                payment_status__in=['not_paid', 'partially_paid']
            ).select_related('supplier')
            
            # Filter out invoices over threshold
            invoices = [inv for inv in invoices if inv.get_cash_payment_status()['remaining'] <= config.max_payment_threshold]
            
            context = {
                'invoices': invoices,
                'current_balance': float(config.current_balance),
                'max_threshold': float(config.max_payment_threshold),
                'payments': CashPayment.objects.all().select_related(
                    'invoice', 'recorded_by'
                ).order_by('-payment_date')
            }
            
            return render(request, 'bank/cash_payments.html', context)
            
        except Exception as e:
            print(f"Error in cash payment view: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')

    def post(self, request):
        print("\n=== Recording Cash Payment ===")
        try:
            data = json.loads(request.body)
            invoice = get_object_or_404(Invoice, id=data.get('invoice_id'))
            
            payment = CashPayment(
                invoice=invoice,
                amount=Decimal(data.get('amount')),
                payment_date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
                reference=data.get('reference'),
                notes=data.get('notes', ''),
                recorded_by=request.user
            )
            
            payment.full_clean()
            payment.save()
            invoice.update_payment_status()
            # Return updated invoice details
            payment_status = invoice.get_cash_payment_status()
            return JsonResponse({
                'status': 'success',
                'message': 'Payment recorded successfully',
                'payment': {
                    'id': str(payment.id),
                    'amount': float(payment.amount),
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'reference': payment.reference
                },
                'invoice': {
                    'total_paid': float(payment_status['total_paid']),
                    'remaining': float(payment_status['remaining']),
                    'status': invoice.payment_status,
                    'status_display': invoice.get_payment_status_display()
                }
            })
            
        except Exception as e:
            print(f"Error recording cash payment: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    

class CashExpenseView(View):
    """View for managing direct cash expenses"""
    def get(self, request):
        print("\n=== Cash Expense View ===")
        try:
            config = CashConfiguration.get_config()
            
            # Get expenses with filters
            expenses = CashExpense.objects.all().select_related('recorded_by')
            
            # Date range filters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if start_date:
                expenses = expenses.filter(date__gte=start_date)
            if end_date:
                expenses = expenses.filter(date__lte=end_date)
            
            context = {
                'expenses': expenses,
                'current_balance': float(config.current_balance),
                'total_expenses': expenses.aggregate(
                    total=Sum('amount')
                )['total'] or 0,
                'expense_types': dict(CashExpense.EXPENSE_TYPE_CHOICES)
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'bank/partials/cash_expenses_table.html',
                        context,
                        request=request
                    )
                })
            
            return render(request, 'bank/cash_expenses.html', context)
            
        except Exception as e:
            print(f"Error in cash expense view: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')

    def post(self, request):
        print("\n=== Recording Cash Expense ===")
        try:
            data = json.loads(request.body)
            
            expense = CashExpense(
                amount=Decimal(data.get('amount')),
                date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
                reference=data.get('reference'),
                expense_account=data.get('expense_account'),
                expense_type=data.get('expense_type'),
                notes=data.get('notes', ''),
                recorded_by=request.user
            )
            
            expense.full_clean()
            expense.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Expense recorded successfully',
                'expense': {
                    'id': str(expense.id),
                    'amount': float(expense.amount),
                    'date': expense.date.strftime('%Y-%m-%d'),
                    'reference': expense.reference,
                    'type': expense.get_expense_type_display()
                }
            })
            
        except Exception as e:
            print(f"Error recording cash expense: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
            
class CashPaymentDetailsView(View):
    def get(self, request, invoice_id):
        print(f"\n=== Getting Cash Payment Details for Invoice {invoice_id} ===")
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            config = CashConfiguration.get_config()
            
            payment_status = invoice.get_cash_payment_status()
            
            return JsonResponse({
                'status': 'success',
                'invoice': {
                    'id': str(invoice.id),
                    'ref': invoice.ref,
                    'supplier': invoice.supplier.name,
                    'total_amount': float(invoice.total_amount),
                    'paid_amount': float(payment_status['total_paid']),
                    'remaining': float(payment_status['remaining'])
                },
                'cash_config': {
                    'current_balance': float(config.current_balance),
                    'max_threshold': float(config.max_payment_threshold)
                }
            })
            
        except Exception as e:
            print(f"Error getting invoice details: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
class GetExpenseTypesView(View):
    """View for getting expense types"""
    def get(self, request):
        print("\n=== Getting Expense Types ===")
        expense_types = [
            {'code': code, 'name': name} 
            for code, name in CashExpense.EXPENSE_TYPE_CHOICES
        ]
        return JsonResponse(expense_types, safe=False)

class CashStatementView(View):
    """View for displaying cash statement"""
    def get(self, request):
        try:
            config = CashConfiguration.get_config()

            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            print(f"\n=== Cash Statement Filter ===")
            print(f"Start Date: {start_date}")
            print(f"End Date: {end_date}")
            
            # Get all transactions chronologically
            transactions = []
            running_balance = config.current_balance

            # Get deposits and payments
            deposits = CashDeposit.objects.all().order_by('-date')
            payments = CashPayment.objects.select_related('invoice', 'invoice__supplier').order_by('-payment_date')
            expenses = CashExpense.objects.all().order_by('-date')

            # Build transactions list with running balance
            for deposit in deposits:
                transactions.append({
                    'date': deposit.date,
                    'type': 'deposit',
                    'reference': deposit.reference,
                    'description': f"Cash deposit {deposit.reference}",
                    'credit': deposit.amount,
                    'debit': None,
                    'balance': running_balance
                })
                running_balance -= deposit.amount

            for payment in payments:
                transactions.append({
                    'date': payment.payment_date,
                    'type': 'payment',
                    'reference': payment.reference,
                    'description': f"Payment for invoice {payment.invoice.ref}",
                    'credit': None,
                    'debit': payment.amount,
                    'balance': running_balance
                })
                running_balance += payment.amount

            for expense in expenses:
                transactions.append({
                    'date': expense.date,
                    'type': 'expense',
                    'reference': expense.reference,
                    'description': f"Expense {expense.reference}",
                    'credit': None,
                    'debit': expense.amount,
                    'balance': running_balance
                })
                running_balance -= expense.amount

            # Sort by date, newest first
            transactions.sort(key=lambda x: x['date'], reverse=True)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('bank/partials/cash_statement_table.html',
                    {'transactions': transactions}, request=request)
                return JsonResponse({'html': html})

            return render(request, 'bank/cash_statement.html', {
                'transactions': transactions,
                'total_credit': sum(t['credit'] or 0 for t in transactions),
                'total_debit': sum(t['debit'] or 0 for t in transactions),
                'current_balance': float(config.current_balance)
            })

        except Exception as e:
            print(f"Error in cash statement view: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')

class CashAccountingView(View):
    """View for displaying cash accounting entries"""
    def get(self, request):
        try:
            config = CashConfiguration.get_config()
            entries = []

            deposits = CashDeposit.objects.all().order_by('-date')
            payments = CashPayment.objects.select_related('invoice', 'invoice__supplier').order_by('-payment_date')

            # Generate accounting entries
            for deposit in deposits:
                bank_account = deposit.source_bank_account
                entries.extend([
                    {
                        'date': deposit.date,
                        'journal': config.journal_code,
                        'account_code': config.accounting_code,
                        'description': f"Cash deposit {deposit.reference}",
                        'debit': deposit.amount,
                        'credit': None,
                        'reference': deposit.reference
                    },
                    {
                        'date': deposit.date,
                        'journal': config.journal_code,
                        'account_code': bank_account.accounting_number,
                        'description': f"Cash deposit {deposit.reference}",
                        'debit': None,
                        'credit': deposit.amount,
                        'reference': deposit.reference
                    }
                ])

            for payment in payments:
                entries.extend([
                    {
                        'date': payment.payment_date,
                        'journal': config.journal_code,
                        'account_code': payment.invoice.supplier.accounting_code,
                        'description': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': payment.amount,
                        'credit': None,
                        'reference': payment.reference
                    },
                    {
                        'date': payment.payment_date,
                        'journal': config.journal_code,
                        'account_code': config.accounting_code,
                        'description': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': None,
                        'credit': payment.amount,
                        'reference': payment.reference
                    }
                ])

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('bank/partials/cash_accounting_table.html',
                    {'entries': entries}, request=request)
                return JsonResponse({'html': html})

            return render(request, 'bank/cash_accounting.html', {
                'entries': entries
            })

        except Exception as e:
            print(f"Error in cash accounting view: {str(e)}")
            messages.error(request, str(e))
            return redirect('cash-configuration')


class CashPaymentDetailView(View):
    """View for displaying cash payment details"""
    def get(self, request):
        try:
            payment_id = request.GET.get('id')
            payment = get_object_or_404(CashPayment, id=payment_id)
            
            return JsonResponse({
                'payment': {
                    'id': str(payment.id),
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'reference': payment.reference,
                    'amount': float(payment.amount),
                    'invoice': {
                        'id': str(payment.invoice.id),
                        'ref': payment.invoice.ref,
                        'supplier': payment.invoice.supplier.name
                    },
                    'notes': payment.notes or '-'
                }
            })
            
        except Exception as e:
            print(f"Error fetching payment details: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)