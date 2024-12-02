from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Presentation, PresentationReceipt, CheckReceipt, LCN, BankAccount
import json

class PresentationListView(ListView):
    """
    Display a list of all presentations with filtering capabilities.
    """
    model = Presentation
    template_name = 'presentation/presentation_list.html'
    context_object_name = 'presentations'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add bank accounts for the filter dropdown
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True)
        return context

@method_decorator(csrf_exempt, name='dispatch')
class PresentationCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            print("Parsed JSON data:", data)

            with transaction.atomic():
                # Create the presentation
                presentation = Presentation.objects.create(
                    presentation_type=data['presentation_type'],
                    date=data['date'],
                    bank_account_id=data['bank_account'],
                    notes=data.get('notes', '')
                )
                print("Created presentation:", presentation)

                # Add receipts to the presentation
                receipt_type = data['receipt_type']
                receipt_ids = data['receipt_ids']
                print(f"Adding {receipt_type} receipts:", receipt_ids)

                for receipt_id in receipt_ids:
                    try:
                        # Get the correct receipt model
                        ReceiptModel = CheckReceipt if receipt_type == 'check' else LCN
                        receipt = ReceiptModel.objects.get(id=receipt_id)
                        
                        print(f"Processing receipt: {receipt}, Status: {receipt.status}")

                        # Verify receipt is in portfolio status
                        if receipt.status != 'PORTFOLIO':
                            raise ValidationError(f"Receipt {receipt} is not in portfolio status")

                        # Create presentation receipt with proper field name
                        field_name = 'checkreceipt' if receipt_type == 'check' else 'lcn'
                        kwargs = {
                            'presentation': presentation,
                            'checkreceipt' if receipt_type == 'check' else 'lcn': receipt,
                            'amount': receipt.amount
                        }
                        
                        print(f"Creating presentation receipt with kwargs:", kwargs)
                        presentation_receipt = PresentationReceipt.objects.create(**kwargs)
                        print(f"Created presentation receipt: {presentation_receipt}")

                    except Exception as e:
                        import traceback
                        traceback.print_exc()

                        print(f"Error processing receipt {receipt_id}: {str(e)}")
                        raise

            return JsonResponse({
                'status': 'success',
                'message': 'Presentation created successfully',
                'id': str(presentation.id)
            })

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Error in presentation creation: {type(e).__name__} - {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Failed to create presentation: {str(e)}"
            }, status=400)

class PresentationDetailView(View):
    """
    Display detailed information about a presentation, including all its receipts.
    """
    def get(self, request, pk):
        presentation = get_object_or_404(Presentation, pk=pk)
        context = {
            'presentation': presentation,
            'receipts': presentation.presentation_receipts.all()
        }
        return render(request, 'presentation/presentation_detail_modal.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class PresentationUpdateView(View):
    """
    Handle updates to presentation status and bank reference.
    """
    def post(self, request, pk):
        try:
            presentation = get_object_or_404(Presentation, pk=pk)
            data = json.loads(request.body)

            with transaction.atomic():
                if 'status' in data:
                    presentation.status = data['status']
                    # Update status of all receipts in the presentation
                    for pr in presentation.presentation_receipts.all():
                        receipt = pr.checkreceipt or pr.lcn
                        if receipt:
                            if data['status'] == 'paid':
                                receipt.status = receipt.STATUS_PAID
                            elif data['status'] == 'rejected':
                                receipt.status = receipt.STATUS_REJECTED
                            receipt.save()

                if 'bank_reference' in data:
                    presentation.bank_reference = data['bank_reference']
                
                presentation.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Presentation updated successfully'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class PresentationDeleteView(View):
    """
    Handle deletion of presentations, resetting the status of associated receipts.
    """
    def post(self, request, pk):
        try:
            presentation = get_object_or_404(Presentation, pk=pk)
            
            with transaction.atomic():
                # Reset status of all receipts back to portfolio
                for pr in presentation.presentation_receipts.all():
                    receipt = pr.checkreceipt or pr.lcn
                    if receipt:
                        receipt.status = receipt.STATUS_PORTFOLIO
                        receipt.save()
                
                presentation.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Presentation deleted successfully'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class AvailableReceiptsView(View):
    """
    Return a list of receipts available for presentation (in portfolio status).
    """
    def get(self, request):
        receipt_type = request.GET.get('type')
        
        if receipt_type == 'check':
            receipts = CheckReceipt.objects.filter(
                status=CheckReceipt.STATUS_PORTFOLIO
            ).select_related('client')
        else:  # lcn
            receipts = LCN.objects.filter(
                status=LCN.STATUS_PORTFOLIO
            ).select_related('client')
        
        html = render_to_string('presentation/available_receipts.html', {
            'receipts': receipts
        }, request=request)
        
        return JsonResponse({'html': html})