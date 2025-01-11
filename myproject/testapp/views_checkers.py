from datetime import datetime
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CheckAllocation, Checker, Check, Invoice, Supplier, BankAccount, get_supplier_balance, get_supplier_unpaid_invoices
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
import traceback




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
            
            # Get all used positions
            used_positions = set(
                checker.checks.values_list('position', flat=True)
            )
            
            # Calculate available positions
            available_positions = [
                pos for pos in range(checker.starting_page, checker.final_page + 1)
                if str(pos) not in used_positions
            ]
            
            # Find first available position
            next_available = min(available_positions) if available_positions else None
            
            return JsonResponse({
                'id': str(checker.id),
                'starting_page': checker.starting_page,
                'final_page': checker.final_page,
                'current_position': checker.current_position,
                'remaining_pages': checker.remaining_pages,
                'used_positions': list(used_positions),
                'available_positions': available_positions,
                'next_available': next_available,
                'status': checker.status
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
        
        # Calculate total from direct checks - including draft
        direct_checks_amount = float(sum(
            check.amount 
            for check in Check.objects.filter(
                cause=invoice
            ).exclude(
                status='cancelled'  # Only exclude cancelled checks
            )
        ) or 0)
        
        # Calculate total from allocated checks - including draft
        allocated_amount = float(sum(
            allocation.amount 
            for allocation in CheckAllocation.objects.filter(
                invoice=invoice
            ).exclude(
                payment__status='cancelled'  # Only exclude cancelled allocations
            )
        ) or 0)
        
        # Calculate total payments
        total_payments = direct_checks_amount + allocated_amount
        
        # Calculate available amount
        available_amount = max(0, net_amount - total_payments)
        
        # Skip invoices that are fully allocated
        if available_amount <= 0:
            continue

        # Only consider paid checks for payment status
        paid_amount = float(sum(
            check.amount for check in Check.objects.filter(
                cause=invoice,
                status='paid'
            )
        ) or 0)

        # Determine status icon based only on paid amounts
        status_icon = '📄 Not Paid'
        if paid_amount >= net_amount:
            status_icon = '🔒 Paid'
        elif paid_amount > 0:
            status_icon = '⏳ Partially Paid'

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
                'total_amount': net_amount,
                'issued_amount': float(total_payments),
                'paid_amount': float(paid_amount),
                'available_amount': available_amount
            },
            'label': (
                f"{invoice.ref} ({invoice.date.strftime('%Y-%m-%d')}) - "
                f"{status_icon} - Available: {available_amount:,.2f} MAD{credit_note_info}"
            )
        })
    
    return JsonResponse(invoice_list, safe=False)

class CheckerSignatureView(View):
    def get(self, request, pk):
        checker = get_object_or_404(Checker, pk=pk)
        print(f"Getting signatures for checker {pk}")
        
        used_positions = {
            str(check.position): {
                'ref': check.position,
                'beneficiary': check.beneficiary.name if check.beneficiary else None,
                'amount': float(check.amount) if check.amount else None
            }
            for check in checker.checks.exclude(status='available')
        }
        print(f"Used positions: {used_positions}")
        
        return JsonResponse({
            'positions': checker.position_signatures,
            'used_positions': used_positions
        })

    def post(self, request, pk):
        checker = get_object_or_404(Checker, pk=pk)
        position = request.POST.get('position')
        signature = request.POST.get('signature')
        
        print(f"Adding signature {signature} to position {position}")
        checker.add_signature(position, signature)
        
        return JsonResponse({'status': 'success'})
    
class CheckerPositionStatusView(View):
    def get(self, request, checker_id, position):
        print(f"Checking status for position {position} in checker {checker_id}")
        checker = get_object_or_404(Checker, pk=checker_id)
        
        # Format full position with index
        full_position = position
        print(f"Checking full position: {full_position}")
        
        is_used = checker.checks.filter(
            position=full_position
        ).exists()
        
        print(f"Position {full_position} used status: {is_used}")
        return JsonResponse({
            'is_used': is_used,
            'full_position': full_position
        })

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            print("\n=== Check Creation Process Started ===")
            print("Raw request body:", request.body)
            data = json.loads(request.body)
            print("Parsed JSON data:", data)
            
            position = data.get('position')
            print("Position value:", position, "Type:", type(position))
            
            # Get checker and its signatures
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            print(f"Found checker: {checker.id}")
            print(f"Checker position_signatures: {checker.position_signatures}")

            # Check for pre-signed signatures
            position_sigs = checker.position_signatures.get(str(position), {})
            print(f"Pre-signed signatures for position {position}: {position_sigs}")
            
            initial_signatures = position_sigs.get('signatures', [])
            print(f"Found pre-signed signatures for position {position}: {initial_signatures}")
            
            # Get supplier
            supplier = get_object_or_404(Supplier, pk=data['supplier_id'])
            
            # Handle supplier payment vs invoice payment
            is_supplier_payment = data.get('is_supplier_payment', False)
            cause = None
            if not is_supplier_payment:
                cause = get_object_or_404(Invoice, pk=data['invoice_id'])
                if cause.supplier != supplier:
                    raise ValidationError("Invoice supplier must match selected supplier")

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            print(f"Payment due date: {payment_due}")
            
            # Create check with initial data
            check = Check(
                position=position,
                checker=checker,
                creation_date=data.get('creation_date', timezone.now().date()),
                beneficiary=supplier,
                is_supplier_payment=is_supplier_payment,
                cause=cause,
                amount_due=cause.total_amount if cause else 0,
                payment_due=data.get('payment_due'),
                amount=data['amount'],
                observation=data.get('observation', ''),
                signatures=initial_signatures
            )
            
             # For supplier payments, validate that amount doesn't exceed total unpaid
            if is_supplier_payment:
                supplier_balance = get_supplier_balance(supplier)
                if Decimal(str(data['amount'])) > supplier_balance['balance']:
                    raise ValidationError(
                        f"Amount {data['amount']} exceeds supplier's unpaid balance "
                        f"{supplier_balance['balance']}"
                    )
            
            check.save()

            # Handle immediate allocation if provided
            if is_supplier_payment and data.get('allocations'):
                for allocation in data['allocations']:
                    CheckAllocation.objects.create(
                        check=check,
                        invoice_id=allocation['invoice_id'],
                        amount=Decimal(str(allocation['amount']))
                    )

            return JsonResponse({
                'message': 'Check created successfully',
                'check_id': str(check.id),
                'is_supplier_payment': is_supplier_payment,
                'available_amount': float(check.get_available_amount())
            })
            
        except ValidationError as e:
            print("Validation error:", str(e))
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print("Error in check creation:", str(e))
            return JsonResponse({'error': str(e)}, status=400)


class CheckAllocationView(View):
    def get(self, request, pk):
        """Get allocation details for a check"""
        try:
            check = get_object_or_404(Check, pk=pk)
            if not check.is_supplier_payment:
                return JsonResponse(
                    {'error': 'Only supplier payments can be allocated'}, 
                    status=400
                )
                
            # Get all unpaid invoices for supplier
            unpaid_invoices = get_supplier_unpaid_invoices(check.beneficiary)
            
            # Get existing allocations
            allocations = check.allocations.select_related('invoice').all()
            
            return JsonResponse({
                'check': {
                    'id': str(check.id),
                    'amount': float(check.amount),
                    'available_amount': float(check.get_available_amount()),
                    'allocated_amount': float(check.get_allocated_amount())
                },
                'allocations': [{
                    'id': str(alloc.id),
                    'invoice_id': str(alloc.invoice.id),
                    'invoice_ref': alloc.invoice.ref,
                    'amount': float(alloc.amount)
                } for alloc in allocations],
                'available_invoices': [{
                    'id': str(inv.id),
                    'ref': inv.ref,
                    'date': inv.date.strftime('%Y-%m-%d'),
                    'total_amount': float(inv.total_amount),
                    'available_amount': float(inv.amount_available_for_payment)
                } for inv in unpaid_invoices]
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def post(self, request, pk):
        """Create a new allocation"""
        try:
            check = get_object_or_404(Check, pk=pk)
            data = json.loads(request.body)
            
            allocation = CheckAllocation.objects.create(
                payment=check,
                invoice_id=data['invoice_id'],
                amount=Decimal(str(data['amount']))
            )
            
            return JsonResponse({
                'message': 'Allocation created successfully',
                'allocation_id': str(allocation.id),
                'available_amount': float(check.get_available_amount())
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def delete(self, request, pk, allocation_id):
        """Delete an allocation"""
        try:
            allocation = get_object_or_404(CheckAllocation, pk=allocation_id, check_id=pk)
            check = allocation.check
            allocation.delete()
            
            return JsonResponse({
                'message': 'Allocation deleted successfully',
                'available_amount': float(check.get_available_amount())
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class CheckListView(ListView):
    model = Check
    template_name = 'checker/check_list.html'
    context_object_name = 'checks'

    def get_queryset(self):
        queryset = Check.objects.select_related(
            'checker__bank_account', 
            'beneficiary', 
            'cause'
        )
        
        for check in queryset:
            print(f"Check {check.id} signatures: {check.signatures}")
            
        return queryset

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

            # Only allow editing of undelivered checks
            if check.status not in ['draft', 'pending']:
                return JsonResponse({
                    'error': 'This check cannot be edited'
                }, status=403)

            # Add editable fields to the response if check is draft
            response_data = {
                'id': str(check.id),
                'status': check.status,
                'delivered_at': check.delivered_at.strftime('%Y-%m-%dT%H:%M') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%dT%H:%M') if check.paid_at else None,
                'cancelled_at': check.cancelled_at.strftime('%Y-%m-%dT%H:%M') if check.cancelled_at else None,
                'cancellation_reason': check.cancellation_reason,
                'payment_due': check.payment_due.strftime('%Y-%m-%d') if check.payment_due else None,
                'observation': check.observation
            }
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)

            # Validate check can be edited
            if check.status not in ['draft', 'pending']:
                return JsonResponse({
                    'error': 'This check cannot be edited'
                }, status=403)
            
            # Handle status updates
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
            
            # Update editable fields
            if 'payment_due' in data:
                check.payment_due = parse(data['payment_due']).date() if data['payment_due'] else None
            if 'observation' in data:
                check.observation = data['observation']

            check.save()
            
            return JsonResponse({
                'message': 'Check updated successfully',
                'check': {
                    'id': str(check.id),
                    'payment_due': check.payment_due.strftime('%Y-%m-%d') if check.payment_due else None,
                    'observation': check.observation
                }
            })

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

@method_decorator(csrf_exempt, name='dispatch')
class CheckActionView(View):
    def get(self, request, pk):
        """Get check details for editing"""
        try:
            check = get_object_or_404(Check.objects.select_related(
                'checker__bank_account',
                'beneficiary',
                'cause'
            ).prefetch_related('allocations'), pk=pk)
            
            print(f"[CheckActionView] Loading check details for ID: {pk}")
            print(f"[CheckActionView] Has allocations: {check.allocations.exists()}")
            
            # Only allow editing of undelivered checks
            if check.status not in ['draft', 'pending', 'printed']:
                return JsonResponse({
                    'error': 'This check cannot be edited'
                }, status=403)
            
            response_data = {
                'id': str(check.id),
                'bank': check.checker.bank_account.bank,
                'position': check.position,
                'reference': f"{check.checker.bank_account.bank}-{check.position}",
                'amount': float(check.amount),
                'amount_due': float(check.amount_due) if check.amount_due else None,
                'beneficiary': check.beneficiary.name,
                'status': check.status,
                'status_display': check.get_status_display(),
                'payment_due': check.payment_due.strftime('%Y-%m-%d') if check.payment_due else None,
                'observation': check.observation or '',
                'creation_date': check.creation_date.strftime('%Y-%m-%d'),
                'signatures': check.signatures or [],
                'is_supplier_payment': check.is_supplier_payment,
                'invoice_ref': check.cause.ref if check.cause else None,
                'has_allocations': check.allocations.exists(),
                'allocations': [{
                    'invoice_ref': alloc.invoice.ref,
                    'amount': float(alloc.amount)
                } for alloc in check.allocations.all()]
            }
            
            print("[CheckActionView] Returning check data:", response_data)
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"[CheckActionView] Error loading check: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=400)
        
    def post(self, request, pk):
            try:
                check = get_object_or_404(Check, pk=pk)
                data = json.loads(request.body)
                action = data.get('action')
                print(f"Action received: {action}")  # Debug
                print(f"Request data: {data}")  # Debug

                if action == 'print':
                    if check.status == 'draft':
                        print_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
                        check.status = 'printed'
                        check.printed_at = print_date
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
                    cancel_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
                    if not reason:
                        return JsonResponse({'error': 'Reason is required'}, status=400)
                    check.cancelled_at = cancel_date
                    check.cancellation_reason = reason
                    check.status = 'cancelled'

                elif action == 'deliver':
                    if not check.printed_at:
                        return JsonResponse({'error': 'Check must be printed first'}, status=400)
                    deliver_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
                    check.delivered_at = deliver_date
                    check.status = 'delivered'
                    check.save()

                elif action == 'pay':
                    if not check.delivered_at:
                        return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                    pay_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
                    check.paid_at = pay_date
                    check.status = 'paid'
                    check.save()
                
                elif action == 'edit':
                    # Validate check can be edited
                    if check.status not in ['draft', 'pending', 'printed']:
                        return JsonResponse({
                            'error': 'This check cannot be edited'
                        }, status=403)
                    
                    # Update editable fields
                    if 'payment_due' in data:
                        try:
                            check.payment_due = parse(data['payment_due']).date() if data['payment_due'] else None
                        except ValueError as e:
                            return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)
                            
                    if 'observation' in data:
                        check.observation = data['observation']

                    check.save()
                    print(f"[CheckActionView] Check updated successfully: payment_due={check.payment_due}, observation={check.observation}")
                    
                    return JsonResponse({
                        'message': 'Check updated successfully',
                        'check': {
                            'id': str(check.id),
                            'payment_due': check.payment_due.strftime('%Y-%m-%d') if check.payment_due else None,
                            'observation': check.observation
                        }
                    })

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

        for checker in queryset:
            print(f"[CheckerFilterView] Processing checker {checker.id}")
            checker.remaining_ratio = f"{checker.remaining_pages}/{checker.num_pages}"
            checker.remaining_percentage = (
                (checker.remaining_pages / checker.num_pages) * 100 
                if checker.num_pages > 0 else 0
            )
            print(f"[CheckerFilterView] Checker stats: {checker.remaining_ratio}, {checker.remaining_percentage}%")


        html = render_to_string(
            'checker/partials/checkers_table.html',
            {'checkers': queryset},
            request=request
        )
        
        return JsonResponse({'html': html})

class CheckFilterView(View):
    def get(self, request):
        try:
            print("[CheckFilterView] Processing filter request")
            queryset = Check.objects.select_related(
                'checker__bank_account',
                'beneficiary',
                'cause'
            )

            # Basic filters
            if bank := request.GET.get('bank'):
                print(f"[CheckFilterView] Filtering by bank: {bank}")
                queryset = queryset.filter(checker__bank_account__bank=bank)
            
            if type := request.GET.get('type'):
                print(f"[CheckFilterView] Filtering by type: {type}")
                queryset = queryset.filter(checker__type=type)
            
            if status := request.GET.get('status'):
                print(f"[CheckFilterView] Filtering by status: {status}")
                queryset = queryset.filter(status=status)
                
            if beneficiary := request.GET.get('beneficiary'):
                print(f"[CheckFilterView] Filtering by beneficiary: {beneficiary}")
                queryset = queryset.filter(beneficiary_id=beneficiary)

            # Date range filter
            if due_date_from := request.GET.get('due_date_from'):
                print(f"[CheckFilterView] Filtering by due date from: {due_date_from}")
                queryset = queryset.filter(payment_due__gte=due_date_from)
                
            if due_date_to := request.GET.get('due_date_to'):
                print(f"[CheckFilterView] Filtering by due date to: {due_date_to}")
                queryset = queryset.filter(payment_due__lte=due_date_to)

            # Amount range filter
            if amount_from := request.GET.get('amount_from'):
                print(f"[CheckFilterView] Filtering by amount from: {amount_from}")
                queryset = queryset.filter(amount__gte=amount_from)
                
            if amount_to := request.GET.get('amount_to'):
                print(f"[CheckFilterView] Filtering by amount to: {amount_to}")
                queryset = queryset.filter(amount__lte=amount_to)

            # Search filter
            if search := request.GET.get('search'):
                print(f"[CheckFilterView] Searching for: {search}")
                queryset = queryset.filter(
                    Q(position__icontains=search) |
                    Q(beneficiary__name__icontains=search) |
                    Q(cause__ref__icontains=search)
                )

            # Render filtered results
            html = render_to_string(
                'checker/partials/checks_table.html',
                {'checks': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            print(f"[CheckFilterView] Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
        

class CheckDetailView(View):
    def get(self, request, check_id):
        try:
            check = Check.objects.get(id=check_id)
            data = {
                "creation_date": check.creation_date.strftime("%Y-%m-%d") if check.creation_date else None,
                "printed_at": check.printed_at.strftime("%Y-%m-%d") if check.printed_at else None,
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