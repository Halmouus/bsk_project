import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View
from .models import BrickProduction, BrickType, BrickPriceHistory, ProductionBatch
from django.utils import timezone

logger = logging.getLogger(__name__)

class BrickTypeListView(LoginRequiredMixin, ListView):
    model = BrickType
    template_name = 'production/brick_type_list.html'
    context_object_name = 'brick_types'

    def get_queryset(self):
        logger.debug("Fetching brick types")
        return BrickType.objects.all().order_by('name')

class BrickTypeCreateView(LoginRequiredMixin, View):
    def post(self, request):
        logger.debug("Received create brick type request")
        try:
            with transaction.atomic():
                # Create brick type
                brick_type = BrickType.objects.create(
                    name=request.POST['name'],
                    industrial_code=request.POST['industrial_code'],
                    length=request.POST['length'],
                    width=request.POST['width'],
                    height=request.POST['height'],
                    bricks_per_wagon=request.POST['bricks_per_wagon'],
                    notes=request.POST.get('notes', '')
                )
                
                # Create prices if provided
                if request.POST.get('bulk_price'):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=request.POST['bulk_price'],
                        is_packaged=False,
                        effective_date=timezone.now()
                    )
                
                if request.POST.get('packaged_price'):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=request.POST['packaged_price'],
                        is_packaged=True,
                        effective_date=timezone.now()
                    )

                logger.info(f"Successfully created brick type: {brick_type.name}")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Brick type created successfully'
                })

        except Exception as e:
            logger.error(f"Error creating brick type: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BrickTypeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received update request for brick type {pk}")
        try:
            with transaction.atomic():
                brick_type = get_object_or_404(BrickType, pk=pk)
                
                # Update basic info
                brick_type.name = request.POST['name']
                brick_type.industrial_code = request.POST['industrial_code']
                brick_type.length = request.POST['length']
                brick_type.width = request.POST['width']
                brick_type.height = request.POST['height']
                brick_type.bricks_per_wagon = request.POST['bricks_per_wagon']
                brick_type.notes = request.POST.get('notes', '')
                brick_type.save()
                
                # Update prices if provided and changed
                bulk_price = request.POST.get('bulk_price')
                packaged_price = request.POST.get('packaged_price')
                current_prices = brick_type.get_current_prices()
                
                if bulk_price and str(bulk_price) != str(current_prices.get('bulk_price')):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=bulk_price,
                        is_packaged=False,
                        effective_date=timezone.now()
                    )
                
                if packaged_price and str(packaged_price) != str(current_prices.get('packaged_price')):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=packaged_price,
                        is_packaged=True,
                        effective_date=timezone.now()
                    )

                logger.info(f"Successfully updated brick type: {brick_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error updating brick type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class BrickTypeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received delete request for brick type {pk}")
        try:
            brick_type = get_object_or_404(BrickType, pk=pk)
            
            # Check if brick type is used in any production
            if BrickProduction.objects.filter(brick_type=brick_type).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete: This brick type has associated production records.'
                }, status=400)
                
            brick_type.delete()
            logger.info(f"Successfully deleted brick type: {brick_type.name}")
            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error deleting brick type: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)