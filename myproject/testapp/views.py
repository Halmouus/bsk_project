from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import Entity, Client, CheckReceipt, LCN
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def home(request):
    print("[HomeView] Accessing home page")
    return render(request, 'home.html')

@require_http_methods(["POST"])
@login_required
def check_receipt_duplicate(request):
    print("[CheckReceiptDuplicate] Checking for duplicate receipt")
    data = json.loads(request.body)
    number = data.get('number')
    entity = data.get('entity')
    bank = data.get('bank')
    receipt_type = data.get('receipt_type')
    
    if receipt_type == 'check':
        exists = CheckReceipt.objects.filter(
            check_number=number,
            entity_id=entity,
            issuing_bank=bank
        ).exists()
    else:
        exists = LCN.objects.filter(
            lcn_number=number,
            entity_id=entity,
            issuing_bank=bank
        ).exists()
    
    print(f"[CheckReceiptDuplicate] Result: {exists}")
    return JsonResponse({'exists': exists})

@require_http_methods(["GET"])
@login_required
def validate_entity(request, entity_id):
    print(f"[ValidateEntity] Validating entity: {entity_id}")
    valid = Entity.objects.filter(id=entity_id).exists()
    return JsonResponse({'valid': valid})

@require_http_methods(["GET"])
@login_required
def validate_client(request, client_id):
    print(f"[ValidateClient] Validating client: {client_id}")
    valid = Client.objects.filter(id=client_id).exists()
    return JsonResponse({'valid': valid})

@require_http_methods(["GET"])
@login_required
def validate_receipt(request, receipt_id):
    print(f"[ValidateReceipt] Validating receipt: {receipt_id}")
    valid = (
        CheckReceipt.objects.filter(id=receipt_id).exists() or
        LCN.objects.filter(id=receipt_id).exists()
    )
    return JsonResponse({'valid': valid})

def custom_403(request, exception=None):
    return render(request, 'unauthorized.html', {
        'reason': 'You do not have permission to access this resource.',
    }, status=403)