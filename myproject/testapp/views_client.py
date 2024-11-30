from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from .models import Client, Entity
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

def client_management(request):
    """Main view for client management interface"""
    logger.info("Accessing client management page")
    return render(request, 'client/client_management.html')

@require_http_methods(["GET"])
def list_clients(request):
    """API endpoint to list all clients"""
    logger.debug("Fetching client list")
    try:
        clients = Client.objects.all()
        data = [{
            'id': str(c.id),
            'name': c.name,
            'client_code': c.client_code
        } for c in clients]
        logger.info(f"Successfully fetched {len(data)} clients")
        return JsonResponse({'clients': data})
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_client(request):
    """API endpoint to create a new client"""
    logger.debug("Creating new client")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Validate client code format
        client_code = data.get('client_code', '').strip()
        if not client_code.isdigit() or len(client_code) < 5 or len(client_code) > 10:
            raise ValidationError("Invalid client code format")
        
        # Check for duplicate client code
        if Client.objects.filter(client_code=client_code).exists():
            raise ValidationError("Client code already exists")
        
        client = Client.objects.create(
            name=data['name'],
            client_code=client_code
        )
        logger.info(f"Successfully created client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        }, status=201)
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_client(request, client_id):
    """API endpoint to update a client"""
    logger.debug(f"Updating client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Update fields
        client.name = data['name']
        if 'client_code' in data:
            new_code = data['client_code'].strip()
            if not new_code.isdigit() or len(new_code) < 5 or len(new_code) > 10:
                raise ValidationError("Invalid client code format")
            if Client.objects.filter(client_code=new_code).exclude(id=client_id).exists():
                raise ValidationError("Client code already exists")
            client.client_code = new_code
            
        client.save()
        logger.info(f"Successfully updated client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_client(request, client_id):
    """API endpoint to delete a client"""
    logger.debug(f"Deleting client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        logger.info(f"Successfully deleted client: {client.name}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def validate_field(request, field, value):
    """API endpoint to validate unique fields"""
    logger.debug(f"Validating {field}: {value}")
    
    # Handle empty values
    if not value or value.strip() == '':
        return JsonResponse({'error': 'Value cannot be empty'}, status=400)
    
    try:
        if field == 'clientCode':
            if not (5 <= len(value) <= 10):
                return JsonResponse({'error': 'Client code must be between 5 and 10 digits'}, status=400)
            exists = Client.objects.filter(client_code=value).exists()
        elif field == 'accountingCode':
            if not (5 <= len(value) <= 7):
                return JsonResponse({'error': 'Accounting code must be between 5 and 7 digits'}, status=400)
            if not value.startswith('3'):
                return JsonResponse({'error': 'Accounting code must start with 3'}, status=400)
            exists = Entity.objects.filter(accounting_code=value).exists()
        elif field == 'iceCode':
            if len(value) != 15:
                return JsonResponse({'error': 'ICE code must be exactly 15 digits'}, status=400)
            exists = Entity.objects.filter(ice_code=value).exists()
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        return JsonResponse({'available': not exists})
    except Exception as e:
        logger.error(f"Error validating {field}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

