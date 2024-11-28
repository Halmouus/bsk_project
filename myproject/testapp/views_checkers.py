from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Checker, Check, Invoice, Supplier, BankAccount
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from dateutil.parser import parse
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal




class CheckerListView(ListView):
    model = Checker
    template_name = 'checker/checker_list.html'
    context_object_name = 'checkers'

    def get_queryset(self):
        return Checker.objects.select_related('bank_account').filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banks'] = BankAccount.objects.filter(
            is_active=True,
            account_type='national'
        )

        # Precompute additional fields for checkers
        for checker in context['checkers']:
            checker.remaining_ratio = f"{checker.remaining_pages}/{checker.num_pages}"
            checker.remaining_percentage = (
                (checker.remaining_pages / checker.num_pages) * 100 if checker.num_pages > 0 else 0
            )

        print("Banks available:", context['banks'])
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CheckerCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate bank account
            bank_account = get_object_or_404(
                BankAccount, 
                id=data['bank_account_id'],
                is_active=True,
                account_type='national'
            )

            # Create checker
            checker = Checker.objects.create(
                type=data['type'],
                bank_account=bank_account,
                num_pages=int(data['num_pages']),
                index=data['index'].upper(),
                starting_page=int(data['starting_page'])
            )
            
            return JsonResponse({
                'message': 'Checker created successfully',
                'checker': {
                    'id': str(checker.id),
                    'code': checker.code,
                    'current_position': checker.current_position,
                    'final_page': checker.final_page
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckerDetailsView(View):
        def get(self, request, pk):
            try:
                checker = get_object_or_404(Checker, pk=pk)
                return JsonResponse({
                    'code': checker.code,
                    'type': checker.type,
                    'bank': checker.get_bank_display(),
                    'account_number': checker.account_number,
                    'city': checker.city,
                    'num_pages': checker.num_pages,
                    'index': checker.index,
                    'starting_page': checker.starting_page,
                    'final_page': checker.final_page,
                    'current_position': checker.current_position,
                    'remaining_pages': checker.final_page - checker.current_position + 1
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

class CheckerDeleteView(View):
    def post(self, request, pk):
        try:
            checker = get_object_or_404(Checker, pk=pk)
            if checker.checks.exists():
                return JsonResponse({'error': 'Cannot delete checker with existing checks'}, status=400)
            checker.delete()
            return JsonResponse({'message': 'Checker deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class AvailableCheckersView(View):
    def get(self, request):
        try:
            # Add debug print
            print("Starting AvailableCheckersView get request")
            
            checkers = Checker.objects.filter(
                is_active=True
            ).exclude(
                status='completed'
            ).select_related('bank_account')
            
            # Debug print the queryset
            print(f"Found {checkers.count()} checkers")
            
            checker_data = [{
                'id': str(checker.id),
                'bank': checker.bank_account.get_bank_display(),
                'account': checker.bank_account.account_number,
                'remaining_pages': checker.remaining_pages,
                'label': f"{checker.bank_account.get_bank_display()} - {checker.bank_account.account_number} ({checker.remaining_pages} pages)"
            } for checker in checkers]
            
            print(f"Processed {len(checker_data)} checkers into data")

            return JsonResponse({
                'checkers': checker_data
            })

        except Exception as e:
            # Enhanced error reporting
            print(f"Exception type: {type(e)}")
            print(f"Exception args: {e.args}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({'error': str(e)}, status=400)


def invoice_autocomplete(request):
    query = request.GET.get('term', '')
    supplier_id = request.GET.get('supplier')
    
    invoices = Invoice.objects.filter(
        supplier_id=supplier_id,
        ref__icontains=query,
        type='invoice'
    )
    
    invoice_list = []
    for invoice in invoices:
        net_amount = float(invoice.net_amount)
        checks_amount = float(sum(
            check.amount
        for check in Check.objects.filter(
                        cause=invoice
                    ).exclude(
                        status='cancelled'
                    )
        ) or 0)
        
        # Calculate available amount
        available_amount = max(0, net_amount - checks_amount)
        
        # Skip invoices that are fully paid or have no remaining amount
        if available_amount <= 0:
            continue

        status_icon = {
            'paid': '🔒 Paid',
            'partially_paid': '⏳ Partially Paid',
            'not_paid': '📄 Not Paid'
        }.get(invoice.payment_status, '')

        credit_note_info = ""
        if invoice.has_credit_notes:
            credit_note_info = f" (Credited: {float(invoice.total_amount - invoice.net_amount):,.2f})"
        
        invoice_list.append({
            'id': str(invoice.id),
            'ref': invoice.ref,
            'date': invoice.date.strftime('%Y-%m-%d'),
            'status': status_icon,
            'amount': net_amount,
            'payment_info': {
                'total_amount': net_amount,  # Use net amount instead of total
                'issued_amount': float(checks_amount),
                'paid_amount': float(sum(
                    check.amount for check in Check.objects.filter(
                        cause=invoice,
                        status='paid'
                    )
                )),
                'available_amount': available_amount
            },
            'label': (
                f"{invoice.ref} ({invoice.date.strftime('%Y-%m-%d')}) - "
                f"{status_icon} - {net_amount:,.2f} MAD{credit_note_info}"
            )
        })
    
    return JsonResponse(invoice_list, safe=False)

class SignChecksView(View):
    def post(self, request):
        data = json.loads(request.body)
        checks = Check.objects.filter(id__in=data['checks'])
        signature = data['signature']
        
        for check in checks:
            if check.can_be_signed(signature):
                check.add_signature(signature)
        
        return JsonResponse({'status': 'success'})

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            invoice = get_object_or_404(Invoice, pk=data['invoice_id'])

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            
            check = Check.objects.create(
                checker=checker,
                creation_date=data.get('creation_date', timezone.now().date()),
                beneficiary=invoice.supplier,
                cause=invoice,
                payment_due=payment_due,
                amount_due=invoice.total_amount,
                amount=data['amount'],
                observation=data.get('observation', '')
            )
            
            return JsonResponse({
                'message': 'Check created successfully',
                'check_id': str(check.id)
            })
            
        except Exception as e:
            print("Error creating check:", str(e))  # Debug print
            return JsonResponse({'error': str(e)}, status=400)
    
class CheckListView(ListView):
    model = Check
    template_name = 'checker/check_list.html'
    context_object_name = 'checks'

    def get_queryset(self):
        return Check.objects.select_related(
            'checker__bank_account', 
            'beneficiary', 
            'cause'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get distinct banks that have checks
        context['banks'] = BankAccount.objects.filter(
            checker__checks__isnull=False
        ).distinct()
        context['rejection_reasons'] = Check.REJECTION_REASONS
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CheckStatusView(View):
    def post(self, request, pk, action):
        try:
            check = get_object_or_404(Check, pk=pk)
            
            if action == 'delivered':
                if check.delivered:
                    return JsonResponse({'error': 'Check already delivered'}, status=400)
                check.delivered = True
            elif action == 'paid':
                if not check.delivered:
                    return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                if check.paid:
                    return JsonResponse({'error': 'Check already paid'}, status=400)
                check.paid = True
            
            check.save()
            return JsonResponse({'message': f'Check marked as {action}'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def supplier_autocomplete(request):
    query = request.GET.get('term', '')
    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) | 
        Q(accounting_code__icontains=query)
    )[:10]
    
    supplier_list = [{
        "label": f"{supplier.name} ({supplier.accounting_code})",
        "value": str(supplier.id)
    } for supplier in suppliers]
    
    return JsonResponse(supplier_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckUpdateView(View):
    def get(self, request, pk):
        try:
            check = get_object_or_404(Check, pk=pk)
            return JsonResponse({
                'id': str(check.id),
                'status': check.status,
                'delivered_at': check.delivered_at.strftime('%Y-%m-%dT%H:%M') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%dT%H:%M') if check.paid_at else None,
                'cancelled_at': check.cancelled_at.strftime('%Y-%m-%dT%H:%M') if check.cancelled_at else None,
                'cancellation_reason': check.cancellation_reason
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if 'delivered_at' in data:
                check.delivered_at = parse(data['delivered_at']) if data['delivered_at'] else None
                check.delivered = bool(check.delivered_at)
                if check.delivered_at:
                    check.status = 'delivered'
            
            if 'paid_at' in data:
                if data['paid_at'] and not check.delivered_at:
                    return JsonResponse({'error': 'Check must be delivered before being marked as paid'}, status=400)
                check.paid_at = parse(data['paid_at']) if data['paid_at'] else None
                check.paid = bool(check.paid_at)
                if check.paid_at:
                    check.status = 'paid'
            
            check.save()
            return JsonResponse({'message': 'Check updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class CheckCancelView(View):
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if check.paid_at:
                return JsonResponse({'error': 'Cannot cancel a paid check'}, status=400)
                
            check.cancelled_at = timezone.now()
            check.cancellation_reason = data.get('reason')
            check.status = 'cancelled'
            check.save()
            
            return JsonResponse({'message': 'Check cancelled successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class CheckActionView(View):
    def post(self, request, pk):
            try:
                check = get_object_or_404(Check, pk=pk)
                data = json.loads(request.body)
                action = data.get('action')
                print(f"Action received: {action}")  # Debug
                print(f"Request data: {data}")  # Debug

                if action == 'print':
                    if check.status == 'draft':
                        check.status = 'printed'
                        check.save()
                elif action == 'sign':
                    signature = data.get('signature')
                    if check.can_be_signed(signature):
                        check.add_signature(signature)                
                elif action == 'reject':
                    reason = data.get('rejection_reason')
                    notes = data.get('rejection_note')
                    print(f"Rejection reason: {reason}")  # Debug
                    print(f"Rejection notes: {notes}")  # Debug
                    check.rejected_at = timezone.now()
                    check.rejection_reason = reason
                    check.rejection_note = notes
                    check.status = 'rejected'
                    print(f"Check status after update: {check.status}")  # Debug

                elif action == 'receive':
                    check.receive(notes=data.get('notes', ''))

                elif action == 'replace':
                    if not check.can_be_replaced:
                        raise ValidationError("Cannot replace this check")
                    
                    # Get the new checker
                    checker = get_object_or_404(Checker, pk=data.get('checker_id'))
                    
                    # Pass checker as a named argument
                    replacement = check.create_replacement(
                    checker=checker,  # Fix is here - pass checker as named arg
                    amount=Decimal(data.get('amount')),
                    payment_due=data.get('payment_due') or None,  # Handle empty string
                    observation=data.get('observation', '')
                            )

                elif action == 'cancel':
                    reason = data.get('reason')
                    if not reason:
                        return JsonResponse({'error': 'Reason is required'}, status=400)
                    check.cancelled_at = timezone.now()
                    check.cancellation_reason = reason
                    check.status = 'cancelled'

                elif action == 'deliver':
                    check.delivered_at = timezone.now()
                    check.status = 'delivered'

                elif action == 'pay':
                    if not check.delivered_at:
                        return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                    check.paid_at = timezone.now()
                    check.status = 'paid'

                check.save()
                return JsonResponse({'status': 'success'})

            except Check.DoesNotExist:
                return JsonResponse({'error': 'Check not found'}, status=404)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            except Exception as e:
                print(f"Error handling check action: {str(e)}")  # Debug
                return JsonResponse({'error': str(e)}, status=500)

class CheckerFilterView(View):
    def get(self, request):
        queryset = Checker.objects.all()
        
        bank_account = request.GET.get('bank_account')
        if bank_account:
            queryset = queryset.filter(bank_account_id=bank_account)
            
        checker_type = request.GET.get('type')
        if checker_type:
            queryset = queryset.filter(type=checker_type)
            
        status = request.GET.get('status')
        if status:
            if status == 'New':
                queryset = queryset.filter(current_position__lt=F('final_page'))
            elif status == 'Completed':
                queryset = queryset.filter(current_position=F('final_page'))

        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(index__icontains=search)
            )

        html = render_to_string(
            'checker/partials/checkers_table.html',
            {'checkers': queryset},
            request=request
        )
        
        return JsonResponse({'html': html})

class CheckFilterView(View):
    def get(self, request):
        try:
            queryset = Check.objects.select_related(
                'checker__bank_account',
                'beneficiary',
                'cause'
            )

            # Apply bank filter
            if bank := request.GET.get('bank'):
                queryset = queryset.filter(checker__bank_account__bank=bank)
                
            # Apply status filter
            if status := request.GET.get('status'):
                queryset = queryset.filter(status=status)
                
            # Apply beneficiary filter
            if beneficiary := request.GET.get('beneficiary'):
                queryset = queryset.filter(beneficiary_id=beneficiary)
                
            # Apply search
            if search := request.GET.get('search'):
                queryset = queryset.filter(
                    Q(position__icontains=search) |
                    Q(beneficiary__name__icontains=search) |
                    Q(cause__ref__icontains=search)
                )

            # Render partial template
            html = render_to_string(
                'checker/partials/checks_table.html',
                {'checks': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class CheckDetailView(View):
    def get(self, request, check_id):
        try:
            check = Check.objects.get(id=check_id)
            data = {
                "creation_date": check.creation_date.strftime("%Y-%m-%d") if check.creation_date else None,
                "delivered_at": check.delivered_at.strftime("%Y-%m-%d") if check.delivered_at else None,
                "paid_at": check.paid_at.strftime("%Y-%m-%d") if check.paid_at else None,
                "rejected_at": check.rejected_at.strftime("%Y-%m-%d") if check.rejected_at else None,
                "rejection_reason": check.rejection_reason,
                "rejection_note": check.rejection_note,
                "cancelled_at": check.cancelled_at.strftime("%Y-%m-%d") if check.cancelled_at else None,
                "cancellation_reason": check.cancellation_reason,
                "received_at": check.received_at.strftime("%Y-%m-d") if check.received_at else None,
                "received_notes": check.received_notes,
                "reference": f"{check.checker.bank_account.bank}-{check.position}",
                "amount": float(check.amount),
                "replacement_info": {
                "replaces": {
                    "id": str(check.replaces.id),
                    "reference": f"{check.replaces.checker.bank_account.bank}-{check.replaces.position}",
                    "amount": float(check.replaces.amount),
                    "rejection_reason": check.replaces.rejection_reason,
                    "rejection_date": check.replaces.rejected_at.strftime("%Y-%m-%d") if check.replaces.rejected_at else None
                } if check.replaces else None,
                "replaced_by": {
                    "id": str(check.replaced_by.first().id),
                    "reference": f"{check.replaced_by.first().checker.bank_account.bank}-{check.replaced_by.first().position}",
                    "amount": float(check.replaced_by.first().amount),
                    "date": check.replaced_by.first().created_at.strftime("%Y-%m-%d")
                } if check.replaced_by.exists() else None
            }
                
            }
            return JsonResponse(data)
        except Check.DoesNotExist:
            return JsonResponse({"error": "Check not found"}, status=404)