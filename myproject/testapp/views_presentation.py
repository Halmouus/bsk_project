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
import traceback

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
    def get(self, request, pk):
        print("\n=== Starting PresentationDetailView.get ===")
        try:
            print(f"Looking for presentation with pk: {pk}")
            presentation = get_object_or_404(Presentation, pk=pk)
            print(f"Found presentation: {presentation}")
            
            print("Fetching related receipts...")
            receipts = presentation.presentation_receipts.all().select_related(
                'checkreceipt__client',
                'lcn__client',
                'checkreceipt__bank_account',
                'lcn__bank_account'
            )
            print(f"Found {receipts.count()} receipts")

            # Debug template loading
            print("\nChecking template tags:")
            from django.template import engines
            django_engine = engines['django']
            try:
                print("Available template tag libraries:", django_engine.template_libraries)
            except Exception as e:
                print(f"Error accessing template libraries: {e}")

            context = {
                'presentation': presentation,
                'receipts': receipts,
                'rejection_causes': CheckReceipt.REJECTION_CAUSES,
                'total_amount': sum(receipt.amount for receipt in receipts)
            }
            print("\nContext prepared:", context)
            
            try:
                print("\nAttempting to render template...")
                rendered = render(
                    request, 
                    'presentation/presentation_detail_modal.html',
                    context
                )
                print("Template rendered successfully")
                return rendered
            except Exception as template_error:
                import traceback
                print("\nTemplate rendering error:")
                print(traceback.format_exc())
                raise template_error

        except Exception as e:
            import traceback
            print("\n=== Error in PresentationDetailView ===")
            print(traceback.format_exc())
            print("=======================================")
            return JsonResponse({
                'status': 'error',
                'message': f"Detail view error: {str(e)}",
                'traceback': traceback.format_exc()
            }, status=400)

def handle_receipt_status(receipt, new_status):
        if new_status == 'paid':
            receipt.status = 'PAID'
        elif new_status == 'unpaid':
            receipt.status = 'UNPAID'
        receipt.save()

@method_decorator(csrf_exempt, name='dispatch')
class PresentationUpdateView(View):
    def post(self, request, pk):
        print("\n=== Starting presentation edit ===")
        try:
            data = json.loads(request.body)
            print(f"Parsed data: {data}")
            print(f"Request headers: {dict(request.headers)}")
            
            with transaction.atomic():
                presentation = get_object_or_404(Presentation, pk=pk)
                print(f"Found presentation: {presentation.__dict__}")

                if presentation.status == 'pending':
                    # Handle initial status change
                    if not data.get('bank_reference'):
                        print("Error: Missing bank reference")
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Bank reference is required'
                        }, status=400)
                    
                    print(f"Updating presentation status from pending to {data['status']}")
                    presentation.bank_reference = data['bank_reference']
                    presentation.status = data['status']
                    presentation.save()
                    print("Presentation updated successfully")

                elif (presentation.status == 'presented' or presentation.status == 'discounted'):
                    if 'receipt_statuses' in data:
                        receipt_statuses = data['receipt_statuses']
                        print(f"Processing {len(receipt_statuses)} receipt status updates: {receipt_statuses}")
                        
                        for receipt_id, new_status in receipt_statuses.items():
                            print(f"\nProcessing receipt {receipt_id}:")
                            print(f"New status data: {new_status}")
                            
                            if not new_status:
                                print("Skipping empty status update")
                                continue
                                
                            try:
                                presentation_receipt = PresentationReceipt.objects.get(
                                    id=receipt_id,
                                    presentation=presentation
                                )
                                print(f"Found presentation receipt: {presentation_receipt.__dict__}")
                                
                                receipt = presentation_receipt.checkreceipt or presentation_receipt.lcn
                                print(f"Associated receipt: {receipt.__dict__ if receipt else None}")
                                
                                if receipt and receipt.status not in ['PAID', 'UNPAID', 'COMPENSATED']:
                                    status_value = new_status['status'] if isinstance(new_status, dict) else new_status
                                    print(f"Processing status update to {status_value}")
                                    
                                    if status_value == 'unpaid':
                                        cause = new_status.get('cause') if isinstance(new_status, dict) else None
                                        print(f"Processing unpaid status with cause: {cause}")
                                        if not cause:
                                            raise ValidationError("Rejection cause required for unpaid status")
                                        receipt.mark_as_unpaid(cause)
                                    else:
                                        print(f"Updating status to: {status_value.upper()}")
                                        receipt.status = status_value.upper()
                                        receipt.save()
                                        
                                        if status_value.upper() == 'PAID':
                                            print("Receipt marked as paid, updating compensated receipts")
                                            receipt.update_compensated_receipts()
                                    
                                    print("Status update completed successfully")
                                else:
                                    print(f"Skipping receipt with status: {receipt.status if receipt else 'None'}")

                            except PresentationReceipt.DoesNotExist:
                                print(f"Error: Receipt {receipt_id} not found in presentation {pk}")
                                continue
                            except Exception as e:
                                print(f"Error processing receipt {receipt_id}: {str(e)}")
                                print(traceback.format_exc())
                                raise
                
                print("Presentation update completed successfully")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Presentation updated successfully'
                })

        except Exception as e:
            print("=== Error in presentation edit ===")
            print(traceback.format_exc())
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
            print(f"Delete request received for presentation {pk}")
            try:
                with transaction.atomic():
                    presentation = get_object_or_404(Presentation, pk=pk)
                    
                    # Only allow deletion of pending presentations
                    if presentation.status != 'pending':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Only pending presentations can be deleted'
                        }, status=400)

                    # Reset status of all receipts back to portfolio
                    for pr in presentation.presentation_receipts.all():
                        print(f"Processing receipt in presentation: {pr}")
                        receipt = pr.checkreceipt or pr.lcn
                        if receipt:
                            print(f"Resetting status for receipt: {receipt}")
                            receipt.status = 'PORTFOLIO'
                            receipt.save()
                            print(f"Receipt status reset to PORTFOLIO")
                    
                    # Delete the presentation
                    presentation.delete()
                    print(f"Presentation {pk} deleted successfully")

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Presentation deleted successfully'
                    })

            except Presentation.DoesNotExist:
                print(f"Presentation {pk} not found")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Presentation not found'
                }, status=404)
            except Exception as e:
                print(f"Error deleting presentation {pk}: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to delete presentation: {str(e)}'
                }, status=500)

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