from datetime import datetime
import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View
from .models import BrickProduction, BrickType, BrickPriceHistory, EnergyPriceHistory, EnergyType, ProductionBatch, ProductionEnergy, BrickStock, LoadingRecord
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
        
class EnergyTypeListView(LoginRequiredMixin, ListView):
    model = EnergyType
    template_name = 'production/energy_type_list.html'
    context_object_name = 'energy_types'

    def get_queryset(self):
        logger.debug("Fetching energy types")
        return EnergyType.objects.all().order_by('name')

class EnergyTypeCreateView(LoginRequiredMixin, View):
    def post(self, request):
        logger.debug("Received create energy type request")
        try:
            with transaction.atomic():
                # Create energy type
                energy_type = EnergyType.objects.create(
                    name=request.POST['name'],
                    unit=request.POST['unit'],
                    is_active=request.POST.get('is_active') == 'on',
                    notes=request.POST.get('notes', '')
                )
                
                # Create initial price
                if request.POST.get('price'):
                    EnergyPriceHistory.objects.create(
                        energy_type=energy_type,
                        price=request.POST['price'],
                        effective_date=timezone.now()
                    )

                logger.info(f"Successfully created energy type: {energy_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error creating energy type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class EnergyTypeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received update request for energy type {pk}")
        try:
            with transaction.atomic():
                energy_type = get_object_or_404(EnergyType, pk=pk)
                
                # Update basic info
                energy_type.name = request.POST['name']
                energy_type.unit = request.POST['unit']
                energy_type.is_active = request.POST.get('is_active') == 'on'
                energy_type.notes = request.POST.get('notes', '')
                energy_type.save()
                
                # Update price if provided and changed
                new_price = request.POST.get('price')
                current_price = energy_type.get_current_price()
                
                if new_price and str(new_price) != str(current_price):
                    EnergyPriceHistory.objects.create(
                        energy_type=energy_type,
                        price=new_price,
                        effective_date=timezone.now()
                    )

                logger.info(f"Successfully updated energy type: {energy_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error updating energy type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class EnergyTypeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received delete request for energy type {pk}")
        try:
            energy_type = get_object_or_404(EnergyType, pk=pk)
            
            # Check if energy type is used in production
            if ProductionEnergy.objects.filter(energy_type=energy_type).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete: This energy type has associated production records.'
                }, status=400)
                
            energy_type.delete()
            logger.info(f"Successfully deleted energy type: {energy_type.name}")
            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error deleting energy type: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
        
class ProductionBatchListView(LoginRequiredMixin, ListView):
    model = ProductionBatch
    template_name = 'production/production_list.html'
    context_object_name = 'production_batches'
    
    def get_queryset(self):
        logger.debug("Fetching production batches")
        return ProductionBatch.objects.prefetch_related(
            'brick_productions',
            'brick_productions__brick_type',
            'energy_consumption',
            'energy_consumption__energy_type'
        ).order_by('-production_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add brick types and energy types for the form
        context['brick_types'] = BrickType.objects.filter(is_active=True)
        context['energy_types'] = EnergyType.objects.filter(is_active=True)
        
        # Add computed values for each batch
        for batch in context['production_batches']:
            batch.total_wagons = sum(prod.wagons_produced for prod in batch.brick_productions.all())
            batch.total_bricks = sum(prod.total_bricks_produced for prod in batch.brick_productions.all())
            batch.total_packaged = sum(prod.bricks_packaged for prod in batch.brick_productions.all())
            batch.total_bulk = batch.total_bricks - batch.total_packaged
        
        return context

class ProductionBatchCreateView(LoginRequiredMixin, View):
    def post(self, request):
        logger.debug("Received create production batch request")
        try:
            logger.debug(f"POST data: {request.POST}")
            
            # Parse JSON data from form
            brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
            wagons = json.loads(request.POST.get('wagons', '[]'))
            misc_adjustments = json.loads(request.POST.get('misc_adjustments', '[]'))
            packaged = json.loads(request.POST.get('packaged', '[]'))
            energy_type_ids = json.loads(request.POST.get('energy_type_ids', '[]'))
            energy_quantities = json.loads(request.POST.get('energy_quantities', '[]'))
            
            # Debug parsed data
            logger.debug(f"Brick type IDs: {brick_type_ids}")
            logger.debug(f"Wagons: {wagons}")
            logger.debug(f"Misc adjustments: {misc_adjustments}")
            logger.debug(f"Packaged: {packaged}")

            with transaction.atomic():
                # Parse JSON data from form
                brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
                wagons = json.loads(request.POST.get('wagons', '[]'))
                misc_adjustments = json.loads(request.POST.get('misc_adjustments', '[]'))
                packaged = json.loads(request.POST.get('packaged', '[]'))
                energy_type_ids = json.loads(request.POST.get('energy_type_ids', '[]'))
                energy_quantities = json.loads(request.POST.get('energy_quantities', '[]'))
                
                # Create the production batch
                batch = ProductionBatch.objects.create(
                    production_date=request.POST.get('production_date'),
                    vpower=request.POST.get('vpower_manual') == '1' and request.POST.get('vpower') or None,
                    notes=request.POST.get('notes', '')
                )
                
                # Create brick productions
                for i, brick_type_id in enumerate(brick_type_ids):
                    if int(wagons[i]) > 0 or int(misc_adjustments[i]) != 0:
                        brick_type = BrickType.objects.get(id=brick_type_id)
                        prod = BrickProduction.objects.create(
                            production_batch=batch,
                            brick_type=brick_type,
                            wagons_produced=wagons[i],
                            miscellaneous_adjustment=misc_adjustments[i],
                            bricks_packaged=packaged[i],
                            bulk_price_at_time=brick_type.get_current_prices().get('bulk_price', 0) or 0,
                            packaged_price_at_time=brick_type.get_current_prices().get('packaged_price', 0) or 0
                        )
                        
                        # Update stock
                        self.update_stock(
                            brick_type,
                            prod.total_bricks_produced,
                            int(packaged[i])
                        )
                
                # Create energy consumption records
                for i, energy_type_id in enumerate(energy_type_ids):
                    quantity = float(energy_quantities[i] or 0)
                    if quantity > 0:
                        energy_type = EnergyType.objects.get(id=energy_type_id)
                        ProductionEnergy.objects.create(
                            production_batch=batch,
                            energy_type=energy_type,
                            quantity=quantity,
                            price_at_time=energy_type.get_current_price() or 0
                        )
                
                batch.calculated_vpower = batch.calculate_vpower()
                batch.save()
                
                logger.info(f"Successfully created production batch for {batch.production_date}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error creating production batch: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def update_stock(self, brick_type, total_produced, packaged):
        """Update stock levels based on production"""
        try:
            # Get or create stock record
            stock, created = BrickStock.objects.get_or_create(
                brick_type=brick_type,
                defaults={'bulk_quantity': 0, 'packaged_quantity': 0}
            )
            
            # Convert values to integers to ensure proper calculation
            total_produced = int(total_produced)
            packaged = int(packaged)
            
            # Update quantities
            bulk_increase = total_produced - packaged
            stock.bulk_quantity += bulk_increase
            stock.packaged_quantity += packaged
            stock.save()
            
            logger.debug(f"Updated stock for {brick_type.name}: +{bulk_increase} bulk, +{packaged} packaged")
        except Exception as e:
            logger.error(f"Error updating stock: {str(e)}")
            raise

class ProductionBatchDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        logger.debug(f"Fetching details for production batch {pk}")
        try:
            # Get production batch with related data
            batch = get_object_or_404(ProductionBatch.objects.prefetch_related(
                'brick_productions',
                'brick_productions__brick_type',
                'energy_consumption',
                'energy_consumption__energy_type'
            ), pk=pk)
            
            # Build response data
            data = {
                'success': True,
                'batch': {
                    'id': str(batch.id),
                    'production_date': batch.production_date.strftime('%Y-%m-%d'),
                    'vpower': batch.vpower,
                    'calculated_vpower': batch.calculated_vpower,
                    'notes': batch.notes
                },
                'brick_productions': [
                    {
                        'brick_type_id': str(prod.brick_type.id),
                        'brick_type_name': prod.brick_type.name,
                        'wagons_produced': prod.wagons_produced,
                        'miscellaneous_adjustment': prod.miscellaneous_adjustment,
                        'bricks_packaged': prod.bricks_packaged,
                        'total_bricks': prod.total_bricks_produced,
                        'bulk_price': str(prod.bulk_price_at_time),
                        'packaged_price': str(prod.packaged_price_at_time)
                    }
                    for prod in batch.brick_productions.all()
                ],
                'energy_consumption': [
                    {
                        'energy_type_id': str(energy.energy_type.id),
                        'energy_type_name': energy.energy_type.name,
                        'quantity': float(energy.quantity),
                        'price': str(energy.price_at_time),
                        'unit': energy.energy_type.unit
                    }
                    for energy in batch.energy_consumption.all()
                ]
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Error fetching production batch details: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class ProductionBatchUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received update request for production batch {pk}")
        try:
            with transaction.atomic():
                # Get the production batch
                batch = get_object_or_404(ProductionBatch, pk=pk)
                
                # Parse JSON data from form
                brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
                wagons = json.loads(request.POST.get('wagons', '[]'))
                misc_adjustments = json.loads(request.POST.get('misc_adjustments', '[]'))
                packaged = json.loads(request.POST.get('packaged', '[]'))
                energy_type_ids = json.loads(request.POST.get('energy_type_ids', '[]'))
                energy_quantities = json.loads(request.POST.get('energy_quantities', '[]'))
                
                # Revert stock changes from previous data
                self.revert_stock_changes(batch)
                
                # Update basic batch info
                batch.production_date = request.POST.get('production_date')
                batch.vpower = request.POST.get('vpower_manual') == '1' and request.POST.get('vpower') or None
                batch.notes = request.POST.get('notes', '')
                
                # Delete old production data
                batch.brick_productions.all().delete()
                batch.energy_consumption.all().delete()
                
                # Create brick productions
                for i, brick_type_id in enumerate(brick_type_ids):
                    if int(wagons[i]) > 0 or int(misc_adjustments[i]) != 0:
                        brick_type = BrickType.objects.get(id=brick_type_id)
                        prod = BrickProduction.objects.create(
                            production_batch=batch,
                            brick_type=brick_type,
                            wagons_produced=wagons[i],
                            miscellaneous_adjustment=misc_adjustments[i],
                            bricks_packaged=packaged[i],
                            bulk_price_at_time=brick_type.get_current_prices().get('bulk_price', 0) or 0,
                            packaged_price_at_time=brick_type.get_current_prices().get('packaged_price', 0) or 0
                        )
                        
                        # Update stock
                        self.update_stock(
                            brick_type,
                            prod.total_bricks_produced,
                            int(packaged[i])
                        )
                
                # Create energy consumption records
                for i, energy_type_id in enumerate(energy_type_ids):
                    quantity = float(energy_quantities[i] or 0)
                    if quantity > 0:
                        energy_type = EnergyType.objects.get(id=energy_type_id)
                        ProductionEnergy.objects.create(
                            production_batch=batch,
                            energy_type=energy_type,
                            quantity=quantity,
                            price_at_time=energy_type.get_current_price() or 0
                        )
                
                batch.calculated_vpower = batch.calculate_vpower()
                batch.save()
                
                logger.info(f"Successfully updated production batch for {batch.production_date}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error updating production batch: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def revert_stock_changes(self, batch):
        """Revert stock changes from previous production data"""
        for prod in batch.brick_productions.all():
            try:
                stock = BrickStock.objects.get(brick_type=prod.brick_type)
                
                # Get values as integers
                total_bricks = int(prod.total_bricks_produced)
                bricks_packaged = int(prod.bricks_packaged)
                
                # Subtract the previously added quantities
                bulk_change = total_bricks - bricks_packaged
                stock.bulk_quantity -= bulk_change
                stock.packaged_quantity -= bricks_packaged
                
                # Ensure we don't go negative
                stock.bulk_quantity = max(0, stock.bulk_quantity)
                stock.packaged_quantity = max(0, stock.packaged_quantity)
                
                stock.save()
                logger.debug(f"Reverted stock for {prod.brick_type.name}: -{bulk_change} bulk, -{bricks_packaged} packaged")
            except Exception as e:
                logger.error(f"Error reverting stock for {prod.brick_type.name}: {str(e)}")
                raise
    
    def update_stock(self, brick_type, total_produced, packaged):
        """Update stock levels based on production"""
        try:
            # Get or create stock record
            stock, created = BrickStock.objects.get_or_create(
                brick_type=brick_type,
                defaults={'bulk_quantity': 0, 'packaged_quantity': 0}
            )
            
            # Convert values to integers to ensure proper calculation
            total_produced = int(total_produced)
            packaged = int(packaged)
            
            # Update quantities
            bulk_increase = total_produced - packaged
            stock.bulk_quantity += bulk_increase
            stock.packaged_quantity += packaged
            stock.save()
            
            logger.debug(f"Updated stock for {brick_type.name}: +{bulk_increase} bulk, +{packaged} packaged")
        except Exception as e:
            logger.error(f"Error updating stock: {str(e)}")
            raise

class ProductionBatchDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        logger.debug(f"Received delete request for production batch {pk}")
        try:
            with transaction.atomic():
                batch = get_object_or_404(ProductionBatch, pk=pk)
                
                # Check if this production has dependent operations
                if LoadingRecord.objects.filter(
                    loading_date__gte=batch.production_date
                ).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot delete: Loading records exist after this production date. Delete those first.'
                    }, status=400)
                
                # Revert stock changes
                self.revert_stock_changes(batch)
                
                # Delete the batch (will cascade to productions and energy consumption)
                batch.delete()
                
                logger.info(f"Successfully deleted production batch for {batch.production_date}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error deleting production batch: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def revert_stock_changes(self, batch):
        """Revert stock changes from previous production data"""
        for prod in batch.brick_productions.all():
            try:
                stock = BrickStock.objects.get(brick_type=prod.brick_type)
                
                # Get values as integers
                total_bricks = int(prod.total_bricks_produced)
                bricks_packaged = int(prod.bricks_packaged)
                
                # Subtract the previously added quantities
                bulk_change = total_bricks - bricks_packaged
                stock.bulk_quantity -= bulk_change
                stock.packaged_quantity -= bricks_packaged
                
                # Ensure we don't go negative
                stock.bulk_quantity = max(0, stock.bulk_quantity)
                stock.packaged_quantity = max(0, stock.packaged_quantity)
                
                stock.save()
                logger.debug(f"Reverted stock for {prod.brick_type.name}: -{bulk_change} bulk, -{bricks_packaged} packaged")
            except Exception as e:
                logger.error(f"Error reverting stock for {prod.brick_type.name}: {str(e)}")
                raise

class LatestProductionDateView(LoginRequiredMixin, View):
    def get(self, request):
        """Get the latest production date"""
        try:
            latest_batch = ProductionBatch.objects.order_by('-production_date').first()
            latest_date = latest_batch.production_date if latest_batch else None
            
            return JsonResponse({
                'success': True,
                'latest_date': latest_date.isoformat() if latest_date else None
            })
        except Exception as e:
            logger.error(f"Error fetching latest production date: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class CurrentStockView(LoginRequiredMixin, View):
    def get(self, request):
        """Get current stock levels for all brick types"""
        try:
            # Get reference date for pricing (if provided)
            reference_date_str = request.GET.get('date')
            reference_date = None
            
            if reference_date_str:
                try:
                    reference_date = datetime.strptime(reference_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            stock_items = BrickStock.objects.select_related('brick_type').all()
            
            stock_data = []
            for item in stock_items:
                # Get prices for the brick type
                brick_type = item.brick_type
                
                # Get prices at reference date or current prices
                if reference_date:
                    bulk_price = BrickPriceHistory.objects.filter(
                        brick_type=brick_type,
                        is_packaged=False,
                        effective_date__lte=reference_date
                    ).order_by('-effective_date').first()
                    
                    packaged_price = BrickPriceHistory.objects.filter(
                        brick_type=brick_type,
                        is_packaged=True,
                        effective_date__lte=reference_date
                    ).order_by('-effective_date').first()
                else:
                    # Use current prices
                    prices = brick_type.get_current_prices()
                    bulk_price = prices.get('bulk_price')
                    packaged_price = prices.get('packaged_price')
                
                stock_data.append({
                    'brick_type_id': str(item.brick_type.id),
                    'brick_type_name': item.brick_type.name,
                    'bulk_quantity': item.bulk_quantity,
                    'packaged_quantity': item.packaged_quantity,
                    'total_quantity': item.bulk_quantity + item.packaged_quantity,
                    'bulk_price': str(bulk_price or 0),
                    'packaged_price': str(packaged_price or 0)
                })
            
            return JsonResponse({
                'success': True,
                'stock': stock_data
            })
        except Exception as e:
            logger.error(f"Error fetching current stock: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class HistoricalStockView(LoginRequiredMixin, View):
    def get(self, request):
        """Get stock levels for a given date"""
        try:
            # Get reference date from query param
            date_str = request.GET.get('date')
            if not date_str:
                return JsonResponse({
                    'success': False,
                    'error': 'Date parameter required'
                }, status=400)
                
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=400)
            
            # Get all production batches up to and including the target date
            batches = ProductionBatch.objects.filter(
                production_date__lte=target_date
            ).prefetch_related(
                'brick_productions', 
                'brick_productions__brick_type'
            ).order_by('production_date')
            
            # Get all loading records up to and including the target date
            loadings = LoadingRecord.objects.filter(
                loading_date__lte=target_date
            ).select_related('brick_type').order_by('loading_date')
            
            # Calculate stock for each brick type as of the target date
            brick_types = BrickType.objects.all()
            stock_data = []
            
            for brick_type in brick_types:
                # Initialize stock totals
                bulk_produced = 0
                packaged = 0
                bulk_loaded = 0
                packaged_loaded = 0
                
                # Add up production data
                for batch in batches:
                    for prod in batch.brick_productions.filter(brick_type=brick_type):
                        bulk_produced += prod.total_bricks_produced
                        packaged += prod.bricks_packaged
                        
                # Subtract loading data
                for loading in loadings.filter(brick_type=brick_type):
                    bulk_loaded += loading.bulk_quantity
                    packaged_loaded += loading.packaged_quantity
                
                # Calculate final stock levels
                bulk_stock = max(0, (bulk_produced - packaged) - bulk_loaded)
                packaged_stock = max(0, packaged - packaged_loaded)
                
                # Get prices at the target date
                bulk_price = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=False,
                    effective_date__lte=target_date
                ).order_by('-effective_date').first()
                
                packaged_price = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=True,
                    effective_date__lte=target_date
                ).order_by('-effective_date').first()
                
                stock_data.append({
                    'brick_type_id': str(brick_type.id),
                    'brick_type_name': brick_type.name,
                    'bulk_quantity': bulk_stock,
                    'packaged_quantity': packaged_stock,
                    'bulk_price': str(bulk_price.price if bulk_price else 0),
                    'packaged_price': str(packaged_price.price if packaged_price else 0)
                })
            
            return JsonResponse({
                'success': True,
                'date': date_str,
                'stock': stock_data
            })
                
        except Exception as e:
            logger.error(f"Error fetching historical stock: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)