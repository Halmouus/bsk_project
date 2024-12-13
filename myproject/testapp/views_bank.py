from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import BankAccount, BankFeeTransaction, Presentation
from django.contrib import messages
import json
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.db.models import Q

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
            
            return JsonResponse({'message': 'Account deactivated successfully'})
            
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
    search_term = request.GET.get('search', '')
    accounts = BankAccount.objects.filter(account_number__icontains=search_term)[:10]
    results = [
        {
            "label": f"{account.bank} [{account.account_number}]",
            "value": account.id,
            "bank": account.bank
        }
        for account in accounts
    ]
    return JsonResponse(results, safe=False)

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