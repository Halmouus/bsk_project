from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import calendar
from .models import CheckReceipt, LCN, CashReceipt, TransferReceipt, BankAccount, Client, Entity,MOROCCAN_BANKS
from django.db.models import Q

class ReceiptListView(ListView):
    template_name = 'receipt/receipt_list.html'
    context_object_name = 'receipts'

    def get_queryset(self):
        print("\n=== Getting Receipt Queryset ===")
        checks = CheckReceipt.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'check_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {checks.count()} checks")
        
        lcns = LCN.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'lcn_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {lcns.count()} LCNs")

        # Debug presentation info
        for check in checks:
            pres = check.check_presentations.first()
            if pres:
                print(f"Check {check.id} presentation: {pres.presentation.id}")
                print(f"Bank: {pres.presentation.bank_account}")

        return {
            'checks': checks,
            'lcns': lcns,
            'cash': CashReceipt.objects.select_related('client', 'entity', 'credited_account').all(),
            'transfers': TransferReceipt.objects.select_related('client', 'entity', 'credited_account').all()
        }

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptCreateView(View):
    def get(self, request, receipt_type):
        if receipt_type not in ['check', 'lcn', 'cash', 'transfer']:
            return JsonResponse({'error': 'Invalid receipt type'}, status=400)

        # Get current date info
        today = timezone.now()
        current_year = today.year
        current_month = today.month

        # Generate year choices (current year and 2 years back)
        year_choices = range(current_year - 2, current_year + 1)

        # Generate month choices
        month_choices = [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]

        # Get active bank accounts
        bank_accounts = BankAccount.objects.filter(is_active=True)

        context = {
            'receipt_type': receipt_type,
            'title': f'New {receipt_type.title()} Receipt',
            'year_choices': year_choices,
            'month_choices': month_choices,
            'current_year': current_year,
            'current_month': current_month,
            'bank_accounts': bank_accounts,
            'bank_choices': MOROCCAN_BANKS, 
        }

        return render(request, 'receipt/receipt_form_modal.html', context)
    
    def post(self, request, receipt_type):
        print("POST request received:")
        print("Receipt type:", receipt_type)
        print("POST data:", request.POST)
        try:
            data = request.POST.dict()
            
            # Common fields for all receipt types
            common_fields = {
                'client_id': data['client'],
                'entity_id': data['entity'],
                'operation_date': data['operation_date'],
                'amount': data['amount'],
                'client_year': data['client_year'],
                'client_month': data['client_month'],
                'notes': data.get('notes', '')
            }

            if receipt_type == 'check':
                receipt = CheckReceipt.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    check_number=data['check_number'],
                    branch=data.get('branch', '')
                )
            
            elif receipt_type == 'lcn':
                receipt = LCN.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    lcn_number=data['lcn_number'],
                )
            
            elif receipt_type == 'cash':
                receipt = CashReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    reference_number=data.get('reference_number', '')
                )
            
            elif receipt_type == 'transfer':
                receipt = TransferReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    transfer_reference=data['transfer_reference'],
                    transfer_date=data['transfer_date']
                )
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid receipt type'
                }, status=400)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} created successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptUpdateView(View):
    def get(self, request, receipt_type, pk):
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        try:
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            
            # Get current date info for form
            today = timezone.now()
            year_choices = range(today.year - 2, today.year + 1)
            month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
            bank_accounts = BankAccount.objects.filter(is_active=True)

            context = {
                'receipt_type': receipt_type,
                'receipt': receipt,
                'title': f'Edit {receipt_type.title()}',
                'year_choices': year_choices,
                'month_choices': month_choices,
                'bank_accounts': bank_accounts,
                'client': {
                    'id': str(receipt.client.id),
                    'text': f"{receipt.client.name} ({receipt.client.client_code})"
                },
                'entity': {
                    'id': str(receipt.entity.id),
                    'text': f"{receipt.entity.name} ({receipt.entity.ice_code})"
                }
            }

            return render(request, 'receipt/receipt_form_modal.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, receipt_type, pk):
        import traceback
        try:
            data = request.POST.dict()
            print(f"Received data for {receipt_type} update:", data)
            
            model_map = {
                'check': CheckReceipt,
                'lcn': LCN,
                'cash': CashReceipt,
                'transfer': TransferReceipt
            }
            
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Update common fields
            receipt.client_id = data['client']
            receipt.entity_id = data['entity']
            receipt.operation_date = data['operation_date']
            receipt.amount = data['amount']
            receipt.client_year = data['client_year']
            receipt.client_month = data['client_month']
            receipt.notes = data.get('notes', '')

            # Update type-specific fields
            if receipt_type in ['check', 'lcn']:
                receipt.issuing_bank = data['issuing_bank']  # Set issuing bank
                receipt.due_date = data['due_date']
                if receipt_type == 'check':
                    receipt.check_number = data['check_number']
                    receipt.branch = data.get('branch', '')
                else:
                    receipt.lcn_number = data['lcn_number']
            else:  # cash or transfer
                receipt.bank_account_id = data['bank_account']
                if receipt_type == 'transfer':
                    receipt.transfer_reference = data['transfer_reference'] 
                    receipt.transfer_date = data['transfer_date']

            receipt.save()
            print(f"{receipt_type} updated successfully:", receipt)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} updated successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            print("Error in receipt update:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDeleteView(View):
    def post(self, request, receipt_type, pk):
        try:
            model_map = {
                'check': CheckReceipt,
                'lcn': LCN,
                'cash': CashReceipt,
                'transfer': TransferReceipt
            }
            
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Check if receipt can be deleted
            if not receipt.can_delete():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot delete receipt that is part of a presentation'
                }, status=400)

            receipt.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} deleted successfully'
            })
        except Exception as e:
            print("Error in receipt deletion:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ReceiptDetailView(View):
    def get(self, request, receipt_type, pk):
        # Map receipt types to their corresponding models
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        # Get the appropriate model
        model = model_map.get(receipt_type)
        if not model:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid receipt type'
            }, status=400)
        
        # Get the receipt instance
        try:
            receipt = model.objects.select_related(
                'client',
                'entity',
                'bank_account'
            ).get(pk=pk)
            
            # Build context based on receipt type
            context = {
                'receipt': receipt,
                'receipt_type': receipt_type,
                'client': receipt.client,
                'entity': receipt.entity,
                'bank_account': receipt.bank_account,
                'common_fields': {
                    'Operation Date': receipt.operation_date,
                    'Amount': receipt.amount,
                    'Client Year': receipt.client_year,
                    'Client Month': calendar.month_name[receipt.client_month],
                    'Notes': receipt.notes or 'No notes'
                }
            }
            
            # Add type-specific fields
            if receipt_type in ['check', 'lcn']:
                context['specific_fields'] = {
                    'Due Date': receipt.due_date,
                    'Status': receipt.get_status_display() if hasattr(receipt, 'get_status_display') else receipt.status
                }
                if receipt_type == 'check':
                    context['specific_fields'].update({
                        'Check Number': receipt.check_number,
                        'Bank Name': receipt.bank_name,
                        'Branch': receipt.branch or 'N/A'
                    })
                else:  # LCN
                    context['specific_fields'].update({
                        'LCN Number': receipt.lcn_number,
                        'Issuing Bank': receipt.issuing_bank
                    })
            else:  # cash or transfer
                context['specific_fields'] = {
                    'Credited Account': receipt.credited_account.account_number
                }
                if receipt_type == 'cash':
                    context['specific_fields']['Reference Number'] = receipt.reference_number or 'N/A'
                else:  # transfer
                    context['specific_fields'].update({
                        'Transfer Reference': receipt.transfer_reference,
                        'Transfer Date': receipt.transfer_date
                    })
            
            # Render the template
            html = render_to_string('receipt/receipt_detail_modal.html', context)
            return JsonResponse({
                'status': 'success',
                'html': html
            })
            
        except model.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Receipt not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

def client_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    clients = Client.objects.filter(
        Q(name__icontains=search) | 
        Q(client_code__icontains=search)
    )[:10]

    results = [{
        'id': str(client.id),
        'text': f"{client.name} ({client.client_code})"
    } for client in clients]
    print(f"results({len(results)}): {results}")

    return JsonResponse({'results': results})


def entity_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    entities = Entity.objects.filter(
        Q(name__icontains=search) | 
        Q(ice_code__icontains=search)
    )[:10]

    results = [{
        'id': str(entity.id),
        'text': f"{entity.name} ({entity.ice_code})"
    } for entity in entities]
    print(f"results({len(results)}): {results}")
    return JsonResponse({'results': results})