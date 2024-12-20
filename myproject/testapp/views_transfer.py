# views_transfer.py

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import InterBankTransfer, TransferredRecord, BankAccount, BankStatement
import json
from decimal import Decimal
from django.db import transaction
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils import timezone

class CreateTransferView(View):
    """Handle creation of interbank transfers"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Validate basic data
                from_bank = get_object_or_404(BankAccount, id=data['from_bank'])
                to_bank = get_object_or_404(BankAccount, id=data['to_bank'])
                
                if from_bank == to_bank:
                    raise ValidationError("Cannot transfer to the same bank account")
                    
                # Create the transfer
                total_amount = Decimal('0.00')
                records_to_transfer = data['records']
                
                # Validate records are available for transfer
                for record in records_to_transfer:
                    if TransferredRecord.objects.filter(
                        source_type=record['source_type'],
                        source_id=record['source_id']
                    ).exists():
                        raise ValidationError(f"Record {record['source_id']} has already been transferred")
                    
                    total_amount += Decimal(str(record['amount']))

                # Check available balance
                current_balance = BankStatement.calculate_balance_until(from_bank, timezone.now().date())
                if current_balance < total_amount:
                    raise ValidationError(f"Insufficient balance. Available: {current_balance}, Required: {total_amount}")
                
                # Create transfer
                transfer = InterBankTransfer.objects.create(
                    from_bank=from_bank,
                    to_bank=to_bank,
                    date=data['date'],
                    label=data.get('label', 'Interbank Transfer'),
                    total_amount=total_amount
                )
                
                # Create transferred records
                for record in records_to_transfer:
                    TransferredRecord.objects.create(
                        transfer=transfer,
                        source_type=record['source_type'],
                        source_id=record['source_id'],
                        amount=Decimal(str(record['amount'])),
                        original_date=record['date'],
                        original_label=record['label'],
                        original_reference=record['reference']
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Transfer created successfully',
                    'transfer_id': str(transfer.id)
                })
                
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to create transfer: {str(e)}'
            }, status=500)

class DeleteTransferView(View):
    """Handle deletion of interbank transfers"""
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                transfer = get_object_or_404(InterBankTransfer, pk=pk)
                
                # Get all transferred records before deletion
                transferred_records = transfer.transferred_records.all()
                
                # Delete the transferred records to remove the "transferred" status
                transferred_records.delete()
                
                # Soft delete the transfer
                transfer.is_deleted = True
                transfer.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Transfer deleted successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to delete transfer: {str(e)}'
            }, status=500)