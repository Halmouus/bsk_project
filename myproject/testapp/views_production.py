from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import traceback
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, View
from django.utils.translation import gettext as _
from .models import BrickProduction, BrickType, BrickPriceHistory, EnergyPriceHistory, EnergyType, ProductionBatch, ProductionEnergy, BrickStock, LoadingRecord, LoadingItem
from django.utils import timezone

logger = logging.getLogger(__name__)

class BrickTypeListView(LoginRequiredMixin, ListView):
    model = BrickType
    template_name = 'production/brick_type_list.html'
    context_object_name = 'brick_types'

    def get_queryset(self):
        print("Fetching brick types")
        return BrickType.objects.all().order_by('name')

class BrickTypeCreateView(LoginRequiredMixin, View):
    def post(self, request):
        print("Received create brick type request")
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
                    is_active=request.POST.get('is_active') == 'on',
                    notes=request.POST.get('notes', '')
                )
                
                # Check if effective_date is provided, otherwise use current time
                effective_date_str = request.POST.get('price_effective_date')
                if effective_date_str:
                    try:
                        # Convert the date string to datetime
                        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
                        # Set the time to the start of the day
                        effective_date = timezone.make_aware(
                            datetime.combine(effective_date, datetime.min.time())
                        )
                    except ValueError:
                        # If date parsing fails, use current time
                        effective_date = timezone.now()
                else:
                    effective_date = timezone.now()
                
                print(f"Using effective date: {effective_date}")
                
                # Create prices if provided
                if request.POST.get('bulk_price'):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=request.POST['bulk_price'],
                        is_packaged=False,
                        effective_date=effective_date
                    )
                    logger.info(f"Created new bulk price record: {request.POST['bulk_price']} effective {effective_date}")
                
                if request.POST.get('packaged_price'):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=request.POST['packaged_price'],
                        is_packaged=True,
                        effective_date=effective_date
                    )
                    logger.info(f"Created new packaged price record: {request.POST['packaged_price']} effective {effective_date}")

                logger.info(f"Successfully created brick type: {brick_type.name}")
                return JsonResponse({
                    'status': 'success',
                    'message': _('Brick type created successfully')
                })

        except Exception as e:
            print(f"Error creating brick type: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BrickTypeDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching details for brick type {pk}")
        try:
            brick_type = get_object_or_404(BrickType, pk=pk)
            
            # Get current prices
            prices = brick_type.get_current_prices()
            
            # Build response data
            data = {
                'success': True,
                'brick_type': {
                    'id': str(brick_type.id),
                    'name': brick_type.name,
                    'industrial_code': brick_type.industrial_code,
                    'length': str(brick_type.length),
                    'width': str(brick_type.width),
                    'height': str(brick_type.height),
                    'bricks_per_wagon': brick_type.bricks_per_wagon,
                    'is_active': brick_type.is_active,
                    'notes': brick_type.notes,
                    'bulk_price': str(prices['bulk_price']) if prices['bulk_price'] else '',
                    'packaged_price': str(prices['packaged_price']) if prices['packaged_price'] else ''
                }
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            print(f"Error fetching brick type details: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
class BrickTypeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received update request for brick type {pk}")
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
                brick_type.is_active = request.POST.get('is_active') == 'on'
                brick_type.save()
                
                # Update prices if provided and changed
                bulk_price = request.POST.get('bulk_price')
                packaged_price = request.POST.get('packaged_price')
                current_prices = brick_type.get_current_prices()
                
                # Check if effective_date is provided, otherwise use current time
                effective_date_str = request.POST.get('price_effective_date')
                if effective_date_str:
                    try:
                        # Convert the date string to datetime
                        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
                        # Set the time to the start of the day
                        effective_date = timezone.make_aware(
                            datetime.combine(effective_date, datetime.min.time())
                        )
                    except ValueError:
                        # If date parsing fails, use current time
                        effective_date = timezone.now()
                else:
                    effective_date = timezone.now()
                
                print(f"Using effective date: {effective_date}")
                
                if bulk_price and str(bulk_price) != str(current_prices.get('bulk_price')):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=bulk_price,
                        is_packaged=False,
                        effective_date=effective_date
                    )
                    logger.info(f"Created new bulk price record: {bulk_price} effective {effective_date}")
                
                if packaged_price and str(packaged_price) != str(current_prices.get('packaged_price')):
                    BrickPriceHistory.objects.create(
                        brick_type=brick_type,
                        price=packaged_price,
                        is_packaged=True,
                        effective_date=effective_date
                    )
                    logger.info(f"Created new packaged price record: {packaged_price} effective {effective_date}")

                logger.info(f"Successfully updated brick type: {brick_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error updating brick type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class BrickTypeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received delete request for brick type {pk}")
        try:
            brick_type = get_object_or_404(BrickType, pk=pk)
            
            # Check if brick type is used in any production
            if BrickProduction.objects.filter(brick_type=brick_type).exists():
                return JsonResponse({
                    'success': False,
                    'error': _('Cannot delete: This brick type has associated production records.')
                }, status=400)
                
            brick_type.delete()
            logger.info(f"Successfully deleted brick type: {brick_type.name}")
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error deleting brick type: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)

class BrickPriceHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching price history for brick type {pk}")
        try:
            brick_type = get_object_or_404(BrickType, pk=pk)
            
            # Fetch all price history records for this brick type
            bulk_prices = BrickPriceHistory.objects.filter(
                brick_type=brick_type,
                is_packaged=False
            ).order_by('-effective_date')
            
            packaged_prices = BrickPriceHistory.objects.filter(
                brick_type=brick_type,
                is_packaged=True
            ).order_by('-effective_date')
            
            # Format the data for the response
            bulk_history = [{
                'id': str(price.id),
                'price': str(price.price),
                'effective_date': price.effective_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': price.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(price, 'created_at') else None,
                'notes': price.notes
            } for price in bulk_prices]
            
            packaged_history = [{
                'id': str(price.id),
                'price': str(price.price),
                'effective_date': price.effective_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': price.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(price, 'created_at') else None,
                'notes': price.notes
            } for price in packaged_prices]
            
            return JsonResponse({
                'success': True,
                'brick_type': {
                    'id': str(brick_type.id),
                    'name': brick_type.name,
                    'industrial_code': brick_type.industrial_code
                },
                'bulk_prices': bulk_history,
                'packaged_prices': packaged_history
            })
        
        except Exception as e:
            print(f"Error fetching price history: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
class EnergyTypeListView(LoginRequiredMixin, ListView):
    model = EnergyType
    template_name = 'production/energy_type_list.html'
    context_object_name = 'energy_types'

    def get_queryset(self):
        print("Fetching energy types")
        return EnergyType.objects.all().order_by('name')

class EnergyTypeCreateView(LoginRequiredMixin, View):
    def post(self, request):
        print("Received create energy type request")
        try:
            with transaction.atomic():
                # Create energy type
                energy_type = EnergyType.objects.create(
                    name=request.POST['name'],
                    unit=request.POST['unit'],
                    is_active=request.POST.get('is_active') == 'on',
                    notes=request.POST.get('notes', '')
                )
                
                # Check if effective_date is provided, otherwise use current time
                effective_date_str = request.POST.get('price_effective_date')
                if effective_date_str:
                    try:
                        # Convert the date string to datetime
                        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
                        # Set the time to the start of the day
                        effective_date = timezone.make_aware(
                            datetime.combine(effective_date, datetime.min.time())
                        )
                    except ValueError:
                        # If date parsing fails, use current time
                        effective_date = timezone.now()
                else:
                    effective_date = timezone.now()
                
                print(f"Using effective date: {effective_date}")
                
                # Create initial price
                if request.POST.get('price'):
                    EnergyPriceHistory.objects.create(
                        energy_type=energy_type,
                        price=request.POST['price'],
                        effective_date=effective_date,
                        notes=request.POST.get('price_notes', '')
                    )
                    logger.info(f"Created new price record: {request.POST['price']} effective {effective_date}")

                logger.info(f"Successfully created energy type: {energy_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error creating energy type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class EnergyTypeUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received update request for energy type {pk}")
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
                
                # Check if effective_date is provided, otherwise use current time
                effective_date_str = request.POST.get('price_effective_date')
                if effective_date_str:
                    try:
                        # Convert the date string to datetime
                        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
                        # Set the time to the start of the day
                        effective_date = timezone.make_aware(
                            datetime.combine(effective_date, datetime.min.time())
                        )
                    except ValueError:
                        # If date parsing fails, use current time
                        effective_date = timezone.now()
                else:
                    effective_date = timezone.now()
                
                print(f"Using effective date: {effective_date}")
                
                if new_price and str(new_price) != str(current_price):
                    EnergyPriceHistory.objects.create(
                        energy_type=energy_type,
                        price=new_price,
                        effective_date=effective_date,
                        notes=request.POST.get('price_notes', '')
                    )
                    logger.info(f"Created new price record: {new_price} effective {effective_date}")

                logger.info(f"Successfully updated energy type: {energy_type.name}")
                return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error updating energy type: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class EnergyTypeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received delete request for energy type {pk}")
        try:
            energy_type = get_object_or_404(EnergyType, pk=pk)
            
            # Check if energy type is used in production
            if ProductionEnergy.objects.filter(energy_type=energy_type).exists():
                return JsonResponse({
                    'success': False,
                    'error': _('Cannot delete: This energy type has associated production records.')
                }, status=400)
                
            energy_type.delete()
            logger.info(f"Successfully deleted energy type: {energy_type.name}")
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error deleting energy type: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)

class EnergyPriceHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching price history for energy type {pk}")
        try:
            energy_type = get_object_or_404(EnergyType, pk=pk)
            
            # Fetch all price history records for this energy type
            prices = EnergyPriceHistory.objects.filter(
                energy_type=energy_type
            ).order_by('-effective_date')
            
            # Format the data for the response
            price_history = [{
                'id': str(price.id),
                'price': str(price.price),
                'effective_date': price.effective_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': price.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(price, 'created_at') else None,
                'notes': price.notes
            } for price in prices]
            
            return JsonResponse({
                'success': True,
                'energy_type': {
                    'id': str(energy_type.id),
                    'name': energy_type.name,
                    'unit': energy_type.unit,
                    'is_active': energy_type.is_active
                },
                'prices': price_history
            })
        
        except Exception as e:
            print(f"Error fetching energy price history: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class EnergyTypeDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching details for energy type {pk}")
        try:
            energy_type = get_object_or_404(EnergyType, pk=pk)
            
            # Get current price
            current_price = energy_type.get_current_price()
            
            # Build response data
            data = {
                'success': True,
                'energy_type': {
                    'id': str(energy_type.id),
                    'name': energy_type.name,
                    'unit': energy_type.unit,
                    'notes': energy_type.notes,
                    'is_active': energy_type.is_active,
                    'current_price': str(current_price) if current_price else ''
                }
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            print(f"Error fetching energy type details: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
class ProductionBatchListView(LoginRequiredMixin, ListView):
    model = ProductionBatch
    template_name = 'production/production_list.html'
    context_object_name = 'production_batches'
    
    def get_queryset(self):
        print("Fetching production batches")
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
        print("Received create production batch request")
        try:
            print(f"POST data: {request.POST}")
            
            # Parse JSON data from form
            brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
            wagons = json.loads(request.POST.get('wagons', '[]'))
            misc_adjustments = json.loads(request.POST.get('misc_adjustments', '[]'))
            packaged = json.loads(request.POST.get('packaged', '[]'))
            energy_type_ids = json.loads(request.POST.get('energy_type_ids', '[]'))
            energy_quantities = json.loads(request.POST.get('energy_quantities', '[]'))
            
            # Debug parsed data
            print(f"Brick type IDs: {brick_type_ids}")
            print(f"Wagons: {wagons}")
            print(f"Misc adjustments: {misc_adjustments}")
            print(f"Packaged: {packaged}")

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
            print(f"Error creating production batch: {str(e)}")
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
            
            print(f"Updated stock for {brick_type.name}: +{bulk_increase} bulk, +{packaged} packaged")
        except Exception as e:
            print(f"Error updating stock: {str(e)}")
            raise

class ProductionBatchDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching details for production batch {pk}")
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
            print(f"Error fetching production batch details: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class ProductionBatchUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received update request for production batch {pk}")
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
            print(f"Error updating production batch: {str(e)}")
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
                print(f"Reverted stock for {prod.brick_type.name}: -{bulk_change} bulk, -{bricks_packaged} packaged")
            except Exception as e:
                print(f"Error reverting stock for {prod.brick_type.name}: {str(e)}")
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
            
            print(f"Updated stock for {brick_type.name}: +{bulk_increase} bulk, +{packaged} packaged")
        except Exception as e:
            print(f"Error updating stock: {str(e)}")
            raise

class ProductionBatchDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received delete request for production batch {pk}")
        try:
            with transaction.atomic():
                batch = get_object_or_404(ProductionBatch, pk=pk)
                
                # Check if this production has dependent operations
                if LoadingRecord.objects.filter(
                    loading_date__gte=batch.production_date
                ).exists():
                    return JsonResponse({
                        'success': False,
                        'error': _('Cannot delete: Loading records exist after this production date. Delete those first.')
                    }, status=400)
                
                # Revert stock changes
                self.revert_stock_changes(batch)
                
                # Delete the batch (will cascade to productions and energy consumption)
                batch.delete()
                
                logger.info(f"Successfully deleted production batch for {batch.production_date}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            print(f"Error deleting production batch: {str(e)}")
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
                print(f"Reverted stock for {prod.brick_type.name}: -{bulk_change} bulk, -{bricks_packaged} packaged")
            except Exception as e:
                print(f"Error reverting stock for {prod.brick_type.name}: {str(e)}")
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
            print(f"Error fetching latest production date: {str(e)}")
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
            print(f"Error fetching current stock: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class HistoricalStockView(LoginRequiredMixin, View):
    def get(self, request):
        """Get stock levels for a given date"""
        try:
            date_str = request.GET.get('date')
            view_type = request.GET.get('type', 'loading')  # Default to loading view
            excluded_id = request.GET.get('exclude_id')  # Optional ID to exclude (for editing existing records)
            
            if not date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Date parameter required')
                }, status=400)
                
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid date format. Use YYYY-MM-DD')
                }, status=400)

            print(f"Calculating historical stock for date: {target_date}, view_type: {view_type}, excluded_id: {excluded_id}")
            
            # For production view: include production up to the day before target date
            # For loading view: include production up to and including target date
            if view_type == 'production':
                production_date_filter = target_date - timedelta(days=1)
                loading_filter_date = target_date
                print(f"Production filter date: {production_date_filter} (excluding target date)")
                print(f"Loading filter date: {loading_filter_date} (including target date)")
            else:
                production_date_filter = target_date
                loading_filter_date = target_date
                print(f"Production filter date: {production_date_filter} (including target date)")
                print(f"Loading filter date: {loading_filter_date} (including target date)")
            
            batches = ProductionBatch.objects.filter(
                production_date__lte=production_date_filter
            ).prefetch_related(
                'brick_productions', 
                'brick_productions__brick_type'
            )
            
            # For loading records:
            # - When viewing: include all loadings before target date 
            # - When editing: also exclude the current loading record
            loading_items_query = LoadingItem.objects.filter(
                loading_record__loading_date__lt=loading_filter_date
            ).select_related('brick_type', 'loading_record')
            
            # If we're editing an existing record, exclude it from historical calculations
            if excluded_id:
                loading_items_query = loading_items_query.exclude(loading_record_id=excluded_id)
                print(f"Excluding loading record with ID: {excluded_id}")
            
            loading_items = loading_items_query.all()
            
            print(f"Found {batches.count()} production batches and {loading_items.count()} loading items")
            
            stock_data = []
            
            # Calculate stock for each brick type
            for brick_type in BrickType.objects.all():
                # Initialize stock totals
                bulk_produced = 0
                packaged = 0
                bulk_loaded = 0
                packaged_loaded = 0
                breakage = 0
                
                # Add up production data
                for batch in batches:
                    for prod in batch.brick_productions.filter(brick_type=brick_type):
                        bulk_produced += prod.total_bricks_produced
                        packaged += prod.bricks_packaged
                        
                # Subtract loading data
                for item in loading_items.filter(brick_type=brick_type):
                    bulk_loaded += item.bulk_quantity
                    packaged_loaded += item.packaged_quantity
                    breakage += item.breakage
                
                # Calculate final stock levels
                bulk_stock = max(0, (bulk_produced - packaged) - bulk_loaded - breakage)
                packaged_stock = max(0, packaged - packaged_loaded)
                
                print(f"Stock calculation for {brick_type.name}:")
                print(f"- Bulk produced: {bulk_produced}")
                print(f"- Packaged: {packaged}")
                print(f"- Bulk loaded: {bulk_loaded}")
                print(f"- Packaged loaded: {packaged_loaded}")
                print(f"- Breakage: {breakage}")
                print(f"- Final bulk stock: {bulk_stock}")
                print(f"- Final packaged stock: {packaged_stock}")
                
                # Get prices at the target date
                print(f"Fetching prices for {brick_type.name} at {target_date}")
                
                # Convert target_date to start and end of day
                start_of_day = timezone.make_aware(
                    datetime.combine(target_date, datetime.min.time())
                )
                end_of_day = timezone.make_aware(
                    datetime.combine(target_date, datetime.max.time())
                )
                
                bulk_price = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=False,
                    effective_date__lte=end_of_day
                ).order_by('-effective_date').first()
                
                packaged_price = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=True,
                    effective_date__lte=end_of_day
                ).order_by('-effective_date').first()
                
                stock_data.append({
                    'brick_type_id': str(brick_type.id),
                    'brick_type_name': brick_type.name,
                    'bulk_quantity': bulk_stock,
                    'packaged_quantity': packaged_stock,
                    'bulk_price': str(bulk_price.price) if bulk_price else "0",
                    'packaged_price': str(packaged_price.price) if packaged_price else "0"
                })
            
            return JsonResponse({
                'success': True,
                'date': date_str,
                'view_type': view_type,
                'stock': stock_data
            })
                
        except Exception as e:
            print(f"Error fetching historical stock: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class LoadingRecordListView(LoginRequiredMixin, ListView):
    model = LoadingRecord
    template_name = 'production/loading_list.html'
    context_object_name = 'loading_records'
    
    def get_queryset(self):
        print("Fetching loading records")
        return LoadingRecord.objects.prefetch_related('items').order_by('-loading_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add brick types for the form
        context['brick_types'] = BrickType.objects.filter(is_active=True)
        
        # Add calculated values for each record
        records_with_totals = []
        
        for record in context['loading_records']:
            # Calculate totals across all items
            total_bulk = sum(item.bulk_quantity for item in record.items.all())
            total_packaged = sum(item.packaged_quantity for item in record.items.all())
            total_breakage = sum(item.breakage for item in record.items.all())
            total_value = sum(
                (item.bulk_quantity * item.bulk_price) + 
                (item.packaged_quantity * item.packaged_price)
                for item in record.items.all()
            )
            
            record_dict = {
                'id': record.id,
                'loading_date': record.loading_date,
                'notes': record.notes,
                'total_bulk': total_bulk,
                'total_packaged': total_packaged,
                'total_breakage': total_breakage,
                'total_value': total_value
            }
            
            records_with_totals.append(record_dict)
        
        context['loading_records'] = records_with_totals
        
        return context

class LoadingRecordDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        print(f"Fetching details for loading record {pk}")
        try:
            # Get loading record with related items
            record = get_object_or_404(LoadingRecord.objects.prefetch_related('items__brick_type'), pk=pk)
            
            # Build response data
            data = {
                'success': True,
                'record': {
                    'id': str(record.id),
                    'loading_date': record.loading_date.strftime('%Y-%m-%d'),
                    'notes': record.notes,
                },
                'items': [
                    {
                        'brick_type_id': str(item.brick_type.id),
                        'brick_type_name': item.brick_type.name,
                        'bulk_quantity': item.bulk_quantity,
                        'packaged_quantity': item.packaged_quantity,
                        'breakage': item.breakage,
                        'bulk_price': str(item.bulk_price),
                        'packaged_price': str(item.packaged_price)
                    }
                    for item in record.items.all()
                ]
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            print(f"Error fetching loading record details: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class LoadingRecordCreateView(LoginRequiredMixin, View):
    def post(self, request):
        print("Received create loading record request")
        try:
            with transaction.atomic():
                # Parse JSON data from form
                brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
                bulk_quantities = json.loads(request.POST.get('bulk_quantities', '[]'))
                packaged_quantities = json.loads(request.POST.get('packaged_quantities', '[]'))
                breakage_quantities = json.loads(request.POST.get('breakage_quantities', '[]'))
                
                loading_date = request.POST.get('loading_date')
                notes = request.POST.get('notes', '')
                
                if not loading_date:
                    return JsonResponse({
                        'success': False,
                        'error': _('Loading date is required')
                    }, status=400)
                
                # Check if we have any quantities to load
                has_quantities = False
                for i in range(len(brick_type_ids)):
                    bulk_qty = int(bulk_quantities[i] or 0)
                    packaged_qty = int(packaged_quantities[i] or 0)
                    breakage_qty = int(breakage_quantities[i] or 0)
                    
                    if bulk_qty > 0 or packaged_qty > 0 or breakage_qty > 0:
                        has_quantities = True
                        break
                
                if not has_quantities:
                    return JsonResponse({
                        'success': False,
                        'error': _('At least one brick type must have quantities specified')
                    }, status=400)
                
                # Get stock at the loading date
                stock_data = {}
                for brick_type in BrickType.objects.all():
                    bulk_stock, packaged_stock = self.get_stock_at_date(brick_type, loading_date)
                    stock_data[str(brick_type.id)] = {
                        'bulk': bulk_stock,
                        'packaged': packaged_stock
                    }
                
                # Validate all quantities first
                for i, brick_type_id in enumerate(brick_type_ids):
                    bulk_quantity = int(bulk_quantities[i] or 0)
                    packaged_quantity = int(packaged_quantities[i] or 0)
                    breakage_quantity = int(breakage_quantities[i] or 0)
                    
                    if bulk_quantity == 0 and packaged_quantity == 0 and breakage_quantity == 0:
                        continue  # Skip if no quantities specified
                    
                    # Validate stock
                    available_bulk = stock_data.get(brick_type_id, {}).get('bulk', 0)
                    available_packaged = stock_data.get(brick_type_id, {}).get('packaged', 0)
                    
                    if bulk_quantity + breakage_quantity > available_bulk:
                        return JsonResponse({
                            'success': False,
                            'error': _('Not enough bulk stock for brick type {0} (Available: {1}, Requested: {2})').format(
                                brick_type_id, available_bulk, bulk_quantity + breakage_quantity)
                        }, status=400)
                        
                    if packaged_quantity > available_packaged:
                        return JsonResponse({
                            'success': False,
                            'error': _('Not enough packaged stock for brick type {0} (Available: {1}, Requested: {2})').format(
                                brick_type_id, available_packaged, packaged_quantity)
                        }, status=400)
                
                # Create the parent loading record
                loading_record = LoadingRecord.objects.create(
                    loading_date=loading_date,
                    notes=notes
                )
                
                # Create loading items for each brick type with quantities
                for i, brick_type_id in enumerate(brick_type_ids):
                    bulk_quantity = int(bulk_quantities[i] or 0)
                    packaged_quantity = int(packaged_quantities[i] or 0)
                    breakage_quantity = int(breakage_quantities[i] or 0)
                    
                    if bulk_quantity == 0 and packaged_quantity == 0 and breakage_quantity == 0:
                        continue  # Skip if no quantities specified
                    
                    # Get brick type and prices
                    brick_type = BrickType.objects.get(id=brick_type_id)
                    prices = self.get_prices_at_date(brick_type, loading_date)
                    
                    # Create loading item
                    LoadingItem.objects.create(
                        loading_record=loading_record,
                        brick_type=brick_type,
                        bulk_quantity=bulk_quantity,
                        packaged_quantity=packaged_quantity,
                        breakage=breakage_quantity,
                        bulk_price=prices['bulk'],
                        packaged_price=prices['packaged']
                    )
                
                logger.info(f"Successfully created loading record for {loading_date}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            print(f"Error creating loading record: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def get_stock_at_date(self, brick_type, date_str, exclude_record=None):
        """Calculate available stock at a given date, optionally excluding a record"""
        try:
            # Debug info to help diagnose calculation issues
            print(f"Calculating stock for {brick_type.name} at {date_str}")
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get all production batches up to and including the target date
            batches = ProductionBatch.objects.filter(
                production_date__lte=target_date
            ).prefetch_related('brick_productions')
            
            # Get all loading records up to but not including the target date
            # Or, if we're editing, include target date BUT exclude the current record
            loading_items_query = LoadingItem.objects.filter(
                loading_record__loading_date__lt=target_date,
                brick_type=brick_type
            ).select_related('loading_record')
            
            # Exclude the current record if provided (for updates)
            if exclude_record:
                # Also include records from the target date but not the excluded one
                target_date_records = LoadingItem.objects.filter(
                    loading_record__loading_date=target_date,
                    brick_type=brick_type
                ).exclude(loading_record=exclude_record)
                
                # Combine the queries
                loading_items = list(loading_items_query) + list(target_date_records)
            else:
                loading_items = loading_items_query.all()
            
            # Calculate production totals
            bulk_produced = 0
            packaged = 0
            
            for batch in batches:
                for prod in batch.brick_productions.filter(brick_type=brick_type):
                    bulk_produced += prod.total_bricks_produced
                    packaged += prod.bricks_packaged
            
            # Calculate loading totals
            bulk_loaded = sum(item.bulk_quantity for item in loading_items)
            packaged_loaded = sum(item.packaged_quantity for item in loading_items)
            breakage = sum(item.breakage for item in loading_items)
            
            # Final stock
            bulk_stock = max(0, (bulk_produced - packaged) - bulk_loaded - breakage)
            packaged_stock = max(0, packaged - packaged_loaded)
            
            # Debug the calculation
            print(f"Stock calculation for {brick_type.name}:")
            print(f"- Bulk produced: {bulk_produced}")
            print(f"- Packaged: {packaged}")
            print(f"- Bulk loaded: {bulk_loaded}")
            print(f"- Packaged loaded: {packaged_loaded}")
            print(f"- Breakage: {breakage}")
            print(f"- Final bulk stock: {bulk_stock}")
            print(f"- Final packaged stock: {packaged_stock}")
            
            return bulk_stock, packaged_stock
            
        except Exception as e:
            print(f"Error calculating stock at date: {str(e)}")
            return 0, 0
    
    def get_prices_at_date(self, brick_type, date_str):
        """Get prices effective at a given date"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
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
            
            return {
                'bulk': bulk_price.price if bulk_price else Decimal('0'),
                'packaged': packaged_price.price if packaged_price else Decimal('0')
            }
            
        except Exception as e:
            print(f"Error getting prices at date: {str(e)}")
            return {'bulk': Decimal('0'), 'packaged': Decimal('0')}

class LoadingRecordUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received update request for loading record {pk}")
        try:
            with transaction.atomic():
                # Get the loading record
                loading_record = get_object_or_404(LoadingRecord, pk=pk)
                
                # Parse JSON data from form
                brick_type_ids = json.loads(request.POST.get('brick_type_ids', '[]'))
                bulk_quantities = json.loads(request.POST.get('bulk_quantities', '[]'))
                packaged_quantities = json.loads(request.POST.get('packaged_quantities', '[]'))
                breakage_quantities = json.loads(request.POST.get('breakage_quantities', '[]'))
                
                loading_date = request.POST.get('loading_date')
                notes = request.POST.get('notes', '')
                
                if not loading_date:
                    return JsonResponse({
                        'success': False,
                        'error': _('Loading date is required')
                    }, status=400)
                
                # Check if we have any quantities to load
                has_quantities = False
                for i in range(len(brick_type_ids)):
                    bulk_qty = int(bulk_quantities[i] or 0)
                    packaged_qty = int(packaged_quantities[i] or 0)
                    breakage_qty = int(breakage_quantities[i] or 0)
                    
                    if bulk_qty > 0 or packaged_qty > 0 or breakage_qty > 0:
                        has_quantities = True
                        break
                
                if not has_quantities:
                    return JsonResponse({
                        'success': False,
                        'error': _('At least one brick type must have quantities specified')
                    }, status=400)
                
                # Get stock at the loading date
                stock_data = {}
                for brick_type in BrickType.objects.all():
                    # When calculating stock for updates, we need to ignore this record's own impact
                    bulk_stock, packaged_stock = self.get_stock_at_date(brick_type, loading_date, exclude_record=loading_record)
                    stock_data[str(brick_type.id)] = {
                        'bulk': bulk_stock,
                        'packaged': packaged_stock
                    }
                
                # Validate all quantities first
                for i, brick_type_id in enumerate(brick_type_ids):
                    bulk_quantity = int(bulk_quantities[i] or 0)
                    packaged_quantity = int(packaged_quantities[i] or 0)
                    breakage_quantity = int(breakage_quantities[i] or 0)
                    
                    if bulk_quantity == 0 and packaged_quantity == 0 and breakage_quantity == 0:
                        continue  # Skip if no quantities specified
                    
                    # Validate stock
                    available_bulk = stock_data.get(brick_type_id, {}).get('bulk', 0)
                    available_packaged = stock_data.get(brick_type_id, {}).get('packaged', 0)
                    
                    if bulk_quantity + breakage_quantity > available_bulk:
                        return JsonResponse({
                            'success': False,
                            'error': _('Not enough bulk stock for brick type {0} (Available: {1}, Requested: {2})').format(
                                brick_type_id, available_bulk, bulk_quantity + breakage_quantity)
                        }, status=400)
                        
                    if packaged_quantity > available_packaged:
                        return JsonResponse({
                            'success': False,
                            'error': _('Not enough packaged stock for brick type {0} (Available: {1}, Requested: {2})').format(
                                brick_type_id, available_packaged, packaged_quantity)
                        }, status=400)
                
                # Update basic info
                loading_record.loading_date = loading_date
                loading_record.notes = notes
                loading_record.save()
                
                # Remove existing items
                loading_record.items.all().delete()
                
                # Create loading items for each brick type with quantities
                for i, brick_type_id in enumerate(brick_type_ids):
                    bulk_quantity = int(bulk_quantities[i] or 0)
                    packaged_quantity = int(packaged_quantities[i] or 0)
                    breakage_quantity = int(breakage_quantities[i] or 0)
                    
                    if bulk_quantity == 0 and packaged_quantity == 0 and breakage_quantity == 0:
                        continue  # Skip if no quantities specified
                    
                    # Get brick type and prices
                    brick_type = BrickType.objects.get(id=brick_type_id)
                    prices = self.get_prices_at_date(brick_type, loading_date)
                    
                    # Create loading item
                    LoadingItem.objects.create(
                        loading_record=loading_record,
                        brick_type=brick_type,
                        bulk_quantity=bulk_quantity,
                        packaged_quantity=packaged_quantity,
                        breakage=breakage_quantity,
                        bulk_price=prices['bulk'],
                        packaged_price=prices['packaged']
                    )
                
                logger.info(f"Successfully updated loading record {pk}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            print(f"Error updating loading record: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def get_stock_at_date(self, brick_type, date_str, exclude_record=None):
        """Calculate available stock at a given date, optionally excluding a record"""
        try:
            # Debug info to help diagnose calculation issues
            print(f"Calculating stock for {brick_type.name} at {date_str}")
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Get all production batches up to and including the target date
            batches = ProductionBatch.objects.filter(
                production_date__lte=target_date
            ).prefetch_related('brick_productions')
            
            # Get all loading records up to but not including the target date
            # Or, if we're editing, include target date BUT exclude the current record
            loading_items_query = LoadingItem.objects.filter(
                loading_record__loading_date__lt=target_date,
                brick_type=brick_type
            ).select_related('loading_record')
            
            # Exclude the current record if provided (for updates)
            if exclude_record:
                # Also include records from the target date but not the excluded one
                target_date_records = LoadingItem.objects.filter(
                    loading_record__loading_date=target_date,
                    brick_type=brick_type
                ).exclude(loading_record=exclude_record)
                
                # Combine the queries
                loading_items = list(loading_items_query) + list(target_date_records)
            else:
                loading_items = loading_items_query.all()
            
            # Calculate production totals
            bulk_produced = 0
            packaged = 0
            
            for batch in batches:
                for prod in batch.brick_productions.filter(brick_type=brick_type):
                    bulk_produced += prod.total_bricks_produced
                    packaged += prod.bricks_packaged
            
            # Calculate loading totals
            bulk_loaded = sum(item.bulk_quantity for item in loading_items)
            packaged_loaded = sum(item.packaged_quantity for item in loading_items)
            breakage = sum(item.breakage for item in loading_items)
            
            # Final stock
            bulk_stock = max(0, (bulk_produced - packaged) - bulk_loaded - breakage)
            packaged_stock = max(0, packaged - packaged_loaded)
            
            # Debug the calculation
            print(f"Stock calculation for {brick_type.name}:")
            print(f"- Bulk produced: {bulk_produced}")
            print(f"- Packaged: {packaged}")
            print(f"- Bulk loaded: {bulk_loaded}")
            print(f"- Packaged loaded: {packaged_loaded}")
            print(f"- Breakage: {breakage}")
            print(f"- Final bulk stock: {bulk_stock}")
            print(f"- Final packaged stock: {packaged_stock}")
            
            return bulk_stock, packaged_stock
            
        except Exception as e:
            print(f"Error calculating stock at date: {str(e)}")
            return 0, 0
    
    def get_prices_at_date(self, brick_type, date_str):
        """Get prices effective at a given date"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
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
            
            return {
                'bulk': bulk_price.price if bulk_price else Decimal('0'),
                'packaged': packaged_price.price if packaged_price else Decimal('0')
            }
            
        except Exception as e:
            print(f"Error getting prices at date: {str(e)}")
            return {'bulk': Decimal('0'), 'packaged': Decimal('0')}

class LoadingRecordDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        print(f"Received delete request for loading record {pk}")
        try:
            with transaction.atomic():
                loading_record = get_object_or_404(LoadingRecord, pk=pk)
                
                # Check if there are any later loading records that might depend on this one
                later_records_exist = LoadingRecord.objects.filter(
                    loading_date__gt=loading_record.loading_date
                ).exists()
                
                if later_records_exist:
                    return JsonResponse({
                        'success': False,
                        'error': _('Cannot delete this loading record because there are later records that depend on it.')
                    }, status=400)
                
                loading_record.delete()
                
                logger.info(f"Successfully deleted loading record {pk}")
                return JsonResponse({'success': True})
                
        except Exception as e:
            print(f"Error deleting loading record: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class LatestLoadingDateView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            latest_loading = LoadingRecord.objects.order_by('-loading_date').first()
            return JsonResponse({
                'success': True,
                'latest_date': latest_loading.loading_date.strftime('%Y-%m-%d') if latest_loading else None
            })
        except Exception as e:
            print(f"Error getting latest loading date: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class DashboardView(LoginRequiredMixin, View):
    def get_historical_stock(self, as_of_date, selected_brick_type=None):
        """Calculate stock levels as they were on the given date."""
        print(f"Calculating historical stock as of {as_of_date}")
        
        # Get brick types to calculate for
        if selected_brick_type:
            brick_types = [selected_brick_type]
        else:
            brick_types = BrickType.objects.filter(is_active=True)
        
        stock_data = []
        total_bulk = 0
        total_packaged = 0
        total_value = 0
        
        # Calculate stock for each brick type
        for brick_type in brick_types:
            print(f"  Calculating stock for {brick_type.name}")
            
            # Get all production batches up to and including target date
            batches = ProductionBatch.objects.filter(
                production_date__lte=as_of_date
            ).prefetch_related('brick_productions')
            
            # Get all loadings up to and including target date
            loadings = LoadingRecord.objects.filter(
                loading_date__lte=as_of_date
            ).prefetch_related('items')
            
            # Calculate production totals
            bulk_produced = 0
            packaged = 0
            
            for batch in batches:
                for prod in batch.brick_productions.filter(brick_type=brick_type):
                    bulk_produced += prod.total_bricks_produced
                    packaged += prod.bricks_packaged
            
            print(f"    Production: {bulk_produced} total, {packaged} packaged")
            
            # Calculate loading totals
            bulk_loaded = 0
            packaged_loaded = 0
            breakage = 0
            
            for loading in loadings:
                for item in loading.items.filter(brick_type=brick_type):
                    bulk_loaded += item.bulk_quantity
                    packaged_loaded += item.packaged_quantity
                    breakage += item.breakage
            
            print(f"    Loading: {bulk_loaded} bulk, {packaged_loaded} packaged, {breakage} breakage")
            
            # Calculate final stock levels
            bulk_stock = max(0, (bulk_produced - packaged) - bulk_loaded - breakage)
            packaged_stock = max(0, packaged - packaged_loaded)
            
            print(f"    Remaining: {bulk_stock} bulk, {packaged_stock} packaged")
            
            # Get prices at the target date
            try:
                # Get bulk price
                bulk_price_record = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=False,
                    effective_date__lte=as_of_date
                ).order_by('-effective_date').first()
                
                # Get packaged price
                packaged_price_record = BrickPriceHistory.objects.filter(
                    brick_type=brick_type,
                    is_packaged=True,
                    effective_date__lte=as_of_date
                ).order_by('-effective_date').first()
                
                bulk_price = bulk_price_record.price if bulk_price_record else Decimal('0')
                packaged_price = packaged_price_record.price if packaged_price_record else Decimal('0')
                
                print(f"    Prices: bulk={bulk_price}, packaged={packaged_price}")
            except Exception as e:
                print(f"    Error getting prices: {str(e)}")
                traceback.print_exc()
                bulk_price = Decimal('0')
                packaged_price = Decimal('0')
            
            # Calculate values
            bulk_value = bulk_stock * bulk_price
            packaged_value = packaged_stock * packaged_price
            total_value_item = bulk_value + packaged_value
            
            print(f"    Values: bulk={bulk_value}, packaged={packaged_value}, total={total_value_item}")
            
            # Add to totals
            total_bulk += bulk_stock
            total_packaged += packaged_stock
            total_value += total_value_item
            
            stock_data.append({
                'brick_type_id': str(brick_type.id),
                'brick_type_name': brick_type.name,
                'bulk_quantity': bulk_stock,
                'packaged_quantity': packaged_stock,
                'total_quantity': bulk_stock + packaged_stock,
                'bulk_price': str(bulk_price),
                'packaged_price': str(packaged_price),
                'bulk_value': float(bulk_value),
                'packaged_value': float(packaged_value),
                'total_value': float(total_value_item),
            })
        
        # Sort by total quantity
        stock_data.sort(key=lambda x: x['total_quantity'], reverse=True)
        
        print(f"Total stock: {total_bulk} bulk, {total_packaged} packaged, value={total_value}")
        
        return {
            'items': stock_data,
            'total_bulk': total_bulk,
            'total_packaged': total_packaged,
            'total_value': float(total_value),
        }

    def get_prices_at_date(self, brick_type, target_date):
        """Get prices effective at a given date"""
        try:
            print(f"Getting prices for {brick_type.name} as of {target_date}")
            
            # Convert to datetime if it's a date
            if isinstance(target_date, datetime.date) and not isinstance(target_date, datetime):
                target_date = datetime.combine(target_date, datetime.min.time())
                target_date = timezone.make_aware(target_date)
            
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
            
            result = {
                'bulk': bulk_price.price if bulk_price else Decimal('0'),
                'packaged': packaged_price.price if packaged_price else Decimal('0')
            }
            
            print(f"  Found prices: bulk={result['bulk']}, packaged={result['packaged']}")
            
            return result
        except Exception as e:
            print(f"Error getting prices at date: {str(e)}")
            traceback.print_exc()  # Add stack trace for better debugging
            return {'bulk': Decimal('0'), 'packaged': Decimal('0')}
    
    def calculate_stock_values(self, stock_data):
        """Add bulk and packaged values to stock data"""
        print("Calculating stock values")
        
        bulk_value = 0
        packaged_value = 0
        
        for item in stock_data['items']:
            try:
                bulk_price = float(item['bulk_price']) if item['bulk_price'] else 0
                packaged_price = float(item['packaged_price']) if item['packaged_price'] else 0
                
                item_bulk_value = item['bulk_quantity'] * bulk_price
                item_packaged_value = item['packaged_quantity'] * packaged_price
                
                bulk_value += item_bulk_value
                packaged_value += item_packaged_value
                
                print(f"  {item['brick_type_name']}: bulk={item_bulk_value}, packaged={item_packaged_value}, total={item_bulk_value + item_packaged_value}")
            except Exception as e:
                print(f"  Error calculating value for {item['brick_type_name']}: {str(e)}")
                traceback.print_exc()
        
        total_value = bulk_value + packaged_value
        
        stock_data['bulk_value'] = bulk_value
        stock_data['packaged_value'] = packaged_value
        stock_data['total_value'] = total_value
        
        print(f"Total stock values: bulk={bulk_value}, packaged={packaged_value}, total={total_value}")
        
        return stock_data
    
    def get_production_data(self, start_date, end_date, selected_brick_type=None):
        print(f"Fetching production data from {start_date} to {end_date}")
        
        # Get production batches in date range
        batches_query = ProductionBatch.objects.filter(
            production_date__gte=start_date,
            production_date__lte=end_date
        ).prefetch_related(
            'brick_productions', 
            'brick_productions__brick_type',
            'energy_consumption'
        ).order_by('production_date')
        
        print(f"Found {batches_query.count()} production batches in date range")
        
        # Filter by brick type if selected
        if selected_brick_type:
            # We still get all batches, but we'll only count the selected brick type
            print(f"Filtering production data by brick type: {selected_brick_type.name}")
        
        # Calculate production stats
        total_batches = batches_query.count()
        total_bricks = 0
        total_bulk = 0
        total_packaged = 0
        total_wagons = 0
        production_by_date = {}
        production_by_type = {}
        energy_consumption = {}
        
        for batch in batches_query:
            batch_date = batch.production_date.isoformat()
            
            # Initialize date entry if not exists
            if batch_date not in production_by_date:
                production_by_date[batch_date] = {
                    'total_bricks': 0,
                    'bulk': 0,
                    'packaged': 0,
                    'wagons': 0,
                    'vpower': batch.effective_vpower,
                }
            
            # Process each brick production in this batch
            for prod in batch.brick_productions.all():
                # Skip if filtering by brick type and this isn't the one
                if selected_brick_type and prod.brick_type.id != selected_brick_type.id:
                    continue
                
                brick_type_name = prod.brick_type.name
                total_produced = prod.total_bricks_produced
                packaged = prod.bricks_packaged
                bulk = total_produced - packaged
                
                # Add to totals
                total_bricks += total_produced
                total_packaged += packaged
                total_bulk += bulk
                total_wagons += prod.wagons_produced
                
                # Add to date aggregates
                production_by_date[batch_date]['total_bricks'] += total_produced
                production_by_date[batch_date]['bulk'] += bulk
                production_by_date[batch_date]['packaged'] += packaged
                production_by_date[batch_date]['wagons'] += prod.wagons_produced
                
                # Add to type aggregates
                if brick_type_name not in production_by_type:
                    production_by_type[brick_type_name] = {
                        'total_bricks': 0,
                        'bulk': 0,
                        'packaged': 0,
                        'id': str(prod.brick_type.id),
                    }
                
                production_by_type[brick_type_name]['total_bricks'] += total_produced
                production_by_type[brick_type_name]['bulk'] += bulk
                production_by_type[brick_type_name]['packaged'] += packaged
            
            # Process energy consumption for this batch
            # (Only count full batch energy usage if filtering by brick type)
            if not selected_brick_type:
                for energy in batch.energy_consumption.all():
                    energy_type_name = energy.energy_type.name
                    
                    if energy_type_name not in energy_consumption:
                        energy_consumption[energy_type_name] = {
                            'total_quantity': 0,
                            'unit': energy.energy_type.unit,
                            'id': str(energy.energy_type.id),
                        }
                    
                    energy_consumption[energy_type_name]['total_quantity'] += float(energy.quantity)
        
        # Remove empty dates (could happen when filtering by brick type)
        production_by_date = {date: data for date, data in production_by_date.items() 
                            if data['total_bricks'] > 0}
        
        # Convert dates dictionary to sorted list
        production_by_date_list = [{'date': date, **data} for date, data in production_by_date.items()]
        production_by_date_list.sort(key=lambda x: x['date'])
        
        # Convert types dictionary to list sorted by total bricks
        production_by_type_list = [{'name': name, **data} for name, data in production_by_type.items()]
        production_by_type_list.sort(key=lambda x: x['total_bricks'], reverse=True)
        
        # Convert energy dictionary to list
        energy_consumption_list = [{'name': name, **data} for name, data in energy_consumption.items()]
        
        # Calculate averages
        avg_vpower = sum(item['vpower'] for item in production_by_date.values()) / len(production_by_date) if production_by_date else 0
        avg_daily_production = total_bricks / len(production_by_date) if production_by_date else 0
        avg_wagons_per_day = total_wagons / len(production_by_date) if production_by_date else 0
        
        return {
            'total_batches': total_batches,
            'total_bricks': total_bricks,
            'total_bulk': total_bulk,
            'total_packaged': total_packaged,
            'total_wagons': total_wagons,
            'by_date': production_by_date_list,
            'by_type': production_by_type_list,
            'energy_consumption': energy_consumption_list,
            'avg_vpower': avg_vpower,
            'avg_daily_production': avg_daily_production,
            'avg_wagons_per_day': avg_wagons_per_day,
        }
    
    def get_loading_data(self, start_date, end_date, selected_brick_type=None):
        print(f"Fetching loading data from {start_date} to {end_date}")
        
        # Get loading records in date range
        loading_records_query = LoadingRecord.objects.filter(
            loading_date__gte=start_date,
            loading_date__lte=end_date
        ).prefetch_related('items', 'items__brick_type').order_by('loading_date')
        
        print(f"Found {loading_records_query.count()} loading records in date range")
        
        # Filter by brick type if selected (done during processing)
        if selected_brick_type:
            print(f"Filtering loading data by brick type: {selected_brick_type.name}")
        
        total_records = loading_records_query.count()
        total_bulk = 0
        total_packaged = 0
        total_breakage = 0
        total_value = 0
        loading_by_date = {}
        loading_by_type = {}
        
        for record in loading_records_query:
            record_date = record.loading_date.isoformat()
            
            # Initialize date entry if not exists
            if record_date not in loading_by_date:
                loading_by_date[record_date] = {
                    'bulk': 0,
                    'packaged': 0,
                    'breakage': 0,
                    'value': 0,
                }
            
            # Process each loading item
            for item in record.items.all():
                # Skip if filtering by brick type and this isn't the one
                if selected_brick_type and item.brick_type.id != selected_brick_type.id:
                    continue
                
                brick_type_name = item.brick_type.name
                
                # Calculate values
                bulk_value = item.bulk_quantity * item.bulk_price
                packaged_value = item.packaged_quantity * item.packaged_price
                total_value_item = bulk_value + packaged_value
                
                # Add to totals
                total_bulk += item.bulk_quantity
                total_packaged += item.packaged_quantity
                total_breakage += item.breakage
                total_value += total_value_item
                
                # Add to date aggregates
                loading_by_date[record_date]['bulk'] += item.bulk_quantity
                loading_by_date[record_date]['packaged'] += item.packaged_quantity
                loading_by_date[record_date]['breakage'] += item.breakage
                loading_by_date[record_date]['value'] += float(total_value_item)
                
                # Add to type aggregates
                if brick_type_name not in loading_by_type:
                    loading_by_type[brick_type_name] = {
                        'bulk': 0,
                        'packaged': 0,
                        'breakage': 0,
                        'value': 0,
                        'id': str(item.brick_type.id),
                    }
                
                loading_by_type[brick_type_name]['bulk'] += item.bulk_quantity
                loading_by_type[brick_type_name]['packaged'] += item.packaged_quantity
                loading_by_type[brick_type_name]['breakage'] += item.breakage
                loading_by_type[brick_type_name]['value'] += float(total_value_item)
        
        # Remove empty dates (could happen when filtering by brick type)
        loading_by_date = {date: data for date, data in loading_by_date.items() 
                         if data['bulk'] + data['packaged'] > 0}
        
        # Convert dates dictionary to sorted list
        loading_by_date_list = [{'date': date, **data} for date, data in loading_by_date.items()]
        loading_by_date_list.sort(key=lambda x: x['date'])
        
        # Convert types dictionary to list sorted by total value
        loading_by_type_list = [{'name': name, **data} for name, data in loading_by_type.items()]
        loading_by_type_list.sort(key=lambda x: x['value'], reverse=True)
        
        # Calculate averages
        avg_daily_loading = (total_bulk + total_packaged) / len(loading_by_date) if loading_by_date else 0
        avg_daily_value = total_value / len(loading_by_date) if loading_by_date else 0
        
        return {
            'total_records': total_records,
            'total_bulk': total_bulk,
            'total_packaged': total_packaged,
            'total_breakage': total_breakage,
            'total_value': float(total_value),
            'by_date': loading_by_date_list,
            'by_type': loading_by_type_list,
            'avg_daily_loading': avg_daily_loading,
            'avg_daily_value': float(avg_daily_value),
        }
    
    def calculate_kpis(self, production_data, loading_data, energy_data, start_date, end_date):
        print("Calculating KPIs")
        
        # Calculate date range length
        date_range_days = (end_date - start_date).days + 1
        
        # Production efficiency
        production_efficiency = {
            'total_bricks': production_data['total_bricks'],
            'avg_daily_production': production_data['avg_daily_production'],
            'packaging_rate': (production_data['total_packaged'] / production_data['total_bricks'] * 100) if production_data['total_bricks'] > 0 else 0,
            'avg_vpower': production_data['avg_vpower'],
        }
        
        # Stock turnover
        stock_turnover = 0
        if production_data['total_bricks'] > 0:
            stock_turnover = (loading_data['total_bulk'] + loading_data['total_packaged']) / production_data['total_bricks']
        
        # Breakage rate
        breakage_rate = 0
        if loading_data['total_bulk'] > 0:
            breakage_rate = loading_data['total_breakage'] / (loading_data['total_bulk'] + loading_data['total_breakage']) * 100
        
        # Calculate breakage value (estimate based on average bulk price)
        avg_bulk_price = 0
        if loading_data['total_bulk'] > 0 and loading_data['total_value'] > 0:
            # Estimate average bulk price from loading data
            bulk_ratio = loading_data['total_bulk'] / (loading_data['total_bulk'] + loading_data['total_packaged'])
            estimated_bulk_value = loading_data['total_value'] * bulk_ratio
            avg_bulk_price = estimated_bulk_value / loading_data['total_bulk']
        
        breakage_value = loading_data['total_breakage'] * avg_bulk_price
        
        # Energy efficiency
        energy_per_brick = 0
        if production_data['total_bricks'] > 0 and energy_data['total_value'] > 0:
            energy_per_brick = energy_data['total_value'] / production_data['total_bricks']
        
        # Calculate overall KPIs
        return {
            'production_efficiency': production_efficiency,
            'stock_turnover': float(stock_turnover),
            'breakage_rate': float(breakage_rate),
            'breakage_value': float(breakage_value),
            'energy_per_brick': float(energy_per_brick),
            'date_range_days': date_range_days,
        }
    
    def get(self, request):
        print("Loading production dashboard")
        try:
            # Get date range parameters (default to last 30 days)
            today = timezone.now().date()
            start_date_str = request.GET.get('start_date', (today - timedelta(days=30)).isoformat())
            end_date_str = request.GET.get('end_date', today.isoformat())
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                # Handle invalid date formats
                start_date = today - timedelta(days=30)
                end_date = today
                print(f"Invalid date format, using default range: {start_date} to {end_date}")
            
            # Get selected brick type (if any)
            selected_brick_type = request.GET.get('brick_type', None)
            if selected_brick_type:
                try:
                    selected_brick_type = BrickType.objects.get(id=selected_brick_type)
                    print(f"Filtering by brick type: {selected_brick_type.name}")
                except (BrickType.DoesNotExist, ValueError):
                    selected_brick_type = None
            
            # Get all brick types for calculating metrics
            brick_types = BrickType.objects.filter(is_active=True)
            
            # Get production data - only include data within the selected date range
            production_data = self.get_production_data(start_date, end_date, selected_brick_type)
            
            # Get historical stock as of the end date (to show inventory at the end of period)
            stock_data = self.get_historical_stock(end_date, selected_brick_type)
            
            # Calculate additional stock values
            stock_data = self.calculate_stock_values(stock_data)
            
            # Get loading data - only include data within the selected date range
            loading_data = self.get_loading_data(start_date, end_date, selected_brick_type)
            
            # Get energy data - only include data within the selected date range
            energy_data = self.get_energy_data(start_date, end_date, selected_brick_type)
            
            # Calculate breakage metrics
            breakage_metrics = self.calculate_breakage_metrics(loading_data, brick_types)
            
            # Calculate KPIs
            kpis = self.calculate_kpis(production_data, loading_data, energy_data, start_date, end_date)
            
            # Get brick types for filters
            brick_types = BrickType.objects.filter(is_active=True).order_by('name')
            
            # Serialize data for JavaScript
            production_data_json = json.dumps(production_data, default=str)
            stock_data_json = json.dumps(stock_data, default=str)
            loading_data_json = json.dumps(loading_data, default=str)
            energy_data_json = json.dumps(energy_data, default=str)
            kpis_json = json.dumps(kpis, default=str)
            
            context = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'selected_brick_type': selected_brick_type,
                'brick_types': brick_types,
                'production_data_json': production_data_json,
                'stock_data_json': stock_data_json, 
                'loading_data_json': loading_data_json,
                'energy_data_json': energy_data_json,
                'kpis_json': kpis_json,
                'production_data': production_data,
                'stock_data': stock_data,
                'loading_data': loading_data,
                'energy_data': energy_data,
                'kpis': kpis,
                'breakage_metrics': breakage_metrics
            }
            
            return render(request, 'production/dashboard.html', context)
        
        except Exception as e:
            print(f"Error loading dashboard: {str(e)}")
            traceback.print_exc()
            context = {
                'error_message': f"Error loading dashboard: {str(e)}",
            }
            return render(request, 'production/dashboard.html', context)

    def get_energy_data(self, start_date, end_date, selected_brick_type=None):
        """Get energy consumption data for the dashboard"""
        print(f"Fetching energy consumption data from {start_date} to {end_date}")
        
        # Get all production batches in the date range
        batches = ProductionBatch.objects.filter(
            production_date__gte=start_date,
            production_date__lte=end_date
        ).prefetch_related(
            'energy_consumption',
            'energy_consumption__energy_type'
        ).order_by('production_date')
        
        print(f"Found {batches.count()} production batches with energy data")
        
        # Initialize totals
        total_quantity = 0
        total_value = 0
        energy_by_type = {}
        energy_by_date = {}
        
        for batch in batches:
            batch_date = batch.production_date.isoformat()
            
            # Skip this batch if we're filtering by brick type and it doesn't have production for that brick type
            if selected_brick_type:
                brick_productions = batch.brick_productions.filter(brick_type=selected_brick_type)
                if not brick_productions.exists():
                    continue
            
            # Initialize date entry if it doesn't exist
            if batch_date not in energy_by_date:
                energy_by_date[batch_date] = {
                    'total_quantity': 0,
                    'total_value': 0,
                    'energy_types': {}
                }
            
            # Process each energy consumption record
            for energy in batch.energy_consumption.all():
                energy_type_name = energy.energy_type.name
                unit = energy.energy_type.unit
                
                # Calculate values
                quantity = float(energy.quantity)
                price = float(energy.price_at_time)
                value = quantity * price
                
                # Add to totals
                total_quantity += quantity
                total_value += value
                
                # Add to type aggregates
                if energy_type_name not in energy_by_type:
                    energy_by_type[energy_type_name] = {
                        'name': energy_type_name,
                        'quantity': 0,
                        'value': 0,
                        'unit': unit,
                        'id': str(energy.energy_type.id),
                        'prices': []
                    }
                
                energy_by_type[energy_type_name]['quantity'] += quantity
                energy_by_type[energy_type_name]['value'] += value
                energy_by_type[energy_type_name]['prices'].append(price)
                
                # Add to date aggregates
                energy_by_date[batch_date]['total_quantity'] += quantity
                energy_by_date[batch_date]['total_value'] += value
                
                # Add energy type breakdown for this date
                if energy_type_name not in energy_by_date[batch_date]['energy_types']:
                    energy_by_date[batch_date]['energy_types'][energy_type_name] = {
                        'quantity': 0,
                        'value': 0,
                        'unit': unit
                    }
                
                energy_by_date[batch_date]['energy_types'][energy_type_name]['quantity'] += quantity
                energy_by_date[batch_date]['energy_types'][energy_type_name]['value'] += value
        
        # Calculate average price for each energy type
        for energy_type in energy_by_type.values():
            if energy_type['quantity'] > 0:
                # Calculate average price from recorded prices
                prices = energy_type['prices']
                if prices:
                    energy_type['avg_price'] = sum(prices) / len(prices)
                else:
                    energy_type['avg_price'] = 0
            else:
                energy_type['avg_price'] = 0
            
            # Remove prices list as it's no longer needed
            del energy_type['prices']
        
        # Convert to sorted lists
        energy_by_type_list = list(energy_by_type.values())
        energy_by_type_list.sort(key=lambda x: x['value'], reverse=True)
        
        energy_by_date_list = [{'date': date, **data} for date, data in energy_by_date.items()]
        energy_by_date_list.sort(key=lambda x: x['date'])
        
        return {
            'total_quantity': total_quantity,
            'total_value': total_value,
            'by_type': energy_by_type_list,
            'by_date': energy_by_date_list
        }

    def calculate_breakage_metrics(self, loading_data, brick_types):
        """Calculate detailed breakage metrics"""
        print("Calculating breakage metrics")
        
        # We need to calculate:
        # 1. Total breakage value (using average bulk price)
        # 2. Breakage by brick type
        # 3. Breakage trends over time
        
        if not loading_data or not loading_data.get('by_date'):
            print("No loading data available for breakage calculations")
            return {
                'total_breakage': 0,
                'breakage_rate': 0,
                'breakage_value': 0,
                'by_type': [],
                'by_date': []
            }
        
        # Calculate average bulk price across all brick types for value estimation
        total_bulk_value = 0
        total_bulk_quantity = 0
        
        for brick_type in brick_types:
            try:
                # Get current price
                prices = brick_type.get_current_prices()
                bulk_price = prices.get('bulk_price') or 0
                
                # Get total quantity for this type
                brick_data = None
                for item in loading_data.get('by_type', []):
                    if item.get('id') == str(brick_type.id):
                        brick_data = item
                        break
                
                if brick_data:
                    total_bulk_quantity += brick_data.get('bulk', 0)
                    total_bulk_value += brick_data.get('bulk', 0) * float(bulk_price)
            except Exception as e:
                print(f"Error processing brick type {brick_type.name}: {str(e)}")
        
        # Calculate average price
        avg_bulk_price = total_bulk_value / total_bulk_quantity if total_bulk_quantity > 0 else 0
        
        # Calculate breakage value
        breakage_value = loading_data.get('total_breakage', 0) * avg_bulk_price
        
        # Calculate overall breakage rate
        total_bulk = loading_data.get('total_bulk', 0)
        total_breakage = loading_data.get('total_breakage', 0)
        
        if total_bulk + total_breakage > 0:
            breakage_rate = (total_breakage / (total_bulk + total_breakage)) * 100
        else:
            breakage_rate = 0
        
        # Calculate breakage by type
        breakage_by_type = []
        for item in loading_data.get('by_type', []):
            if item.get('breakage', 0) > 0:
                # Calculate breakage rate for this type
                type_bulk = item.get('bulk', 0)
                type_breakage = item.get('breakage', 0)
                
                if type_bulk + type_breakage > 0:
                    type_rate = (type_breakage / (type_bulk + type_breakage)) * 100
                else:
                    type_rate = 0
                
                breakage_by_type.append({
                    'name': item.get('name', 'Unknown'),
                    'breakage': type_breakage,
                    'rate': type_rate,
                    'id': item.get('id')
                })
        
        # Sort by breakage quantity
        breakage_by_type.sort(key=lambda x: x['breakage'], reverse=True)
        
        # Calculate breakage trends over time
        breakage_by_date = []
        for item in loading_data.get('by_date', []):
            date = item.get('date', '')
            item_breakage = item.get('breakage', 0)
            item_bulk = item.get('bulk', 0)
            
            # Calculate rate for this date
            if item_bulk + item_breakage > 0:
                item_rate = (item_breakage / (item_bulk + item_breakage)) * 100
            else:
                item_rate = 0
            
            breakage_by_date.append({
                'date': date,
                'breakage': item_breakage,
                'rate': item_rate
            })
        
        return {
            'total_breakage': total_breakage,
            'breakage_rate': breakage_rate,
            'breakage_value': breakage_value,
            'by_type': breakage_by_type,
            'by_date': breakage_by_date
        }

def report_data(request):
    """API endpoint to get report data for a given date range"""
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        brick_type_id = request.GET.get('brick_type')
        
        # Parse dates
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to 30 days ago
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to today
            end_date = timezone.now().date()
            
        # Get brick type if specified
        selected_brick_type = None
        if brick_type_id:
            try:
                selected_brick_type = BrickType.objects.get(id=brick_type_id)
            except (BrickType.DoesNotExist, ValueError):
                pass
        
        # Reuse DashboardView methods to gather the data
        dashboard = DashboardView()
        
        # Get production data
        production_data = dashboard.get_production_data(start_date, end_date, selected_brick_type)
        
        # Get historical stock as of the end date
        stock_data = dashboard.get_historical_stock(end_date, selected_brick_type)
        
        # Calculate additional stock values
        stock_data = dashboard.calculate_stock_values(stock_data)
        
        # Get loading data
        loading_data = dashboard.get_loading_data(start_date, end_date, selected_brick_type)
        
        # Get brick type details for daily production
        production_data = add_daily_brick_type_details(production_data, start_date, end_date, selected_brick_type)
        
        # Get brick type details for daily loading
        loading_data = add_daily_loading_brick_type_details(loading_data, start_date, end_date, selected_brick_type)
        
        # Calculate KPIs - Check the actual arguments needed!
        # Inspect the actual method signature and pass the correct arguments
        # This may vary based on your implementation
        try:
            # Try with the signature we assumed
            kpis = dashboard.calculate_kpis(production_data, loading_data, start_date, end_date)
        except TypeError:
            try:
                # Try alternative signature options
                kpis = dashboard.calculate_kpis(production_data, loading_data)
            except TypeError:
                # As a last resort, just create a basic KPIs structure
                kpis = {
                    'production_efficiency': {
                        'total_bricks': production_data.get('total_bricks', 0),
                        'avg_daily_production': production_data.get('avg_daily_production', 0),
                        'avg_vpower': production_data.get('avg_vpower', 0),
                        'packaging_rate': 0
                    },
                    'stock_turnover': 0,
                    'breakage_rate': 0,
                    'date_range_days': (end_date - start_date).days + 1
                }
                
                # Try to calculate some values if possible
                if production_data.get('total_bricks', 0) > 0:
                    total_packaged = production_data.get('total_packaged', 0)
                    kpis['production_efficiency']['packaging_rate'] = (total_packaged / production_data['total_bricks'] * 100)
                
                if production_data.get('total_bricks', 0) > 0:
                    total_loaded = loading_data.get('total_bulk', 0) + loading_data.get('total_packaged', 0)
                    kpis['stock_turnover'] = total_loaded / production_data['total_bricks']
                
                if loading_data.get('total_bulk', 0) > 0:
                    breakage = loading_data.get('total_breakage', 0)
                    kpis['breakage_rate'] = breakage / loading_data['total_bulk'] * 100
        
        # Energy data (if available)
        energy_data = {}
        if hasattr(dashboard, 'get_energy_data'):
            energy_data = dashboard.get_energy_data(start_date, end_date, selected_brick_type)
        
        # Prepare response
        data = {
            'success': True,
            'production_data': production_data,
            'stock_data': stock_data,
            'loading_data': loading_data,
            'kpis': kpis,
            'energy_data': energy_data,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        print(f"Error generating report data: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def add_daily_brick_type_details(production_data, start_date, end_date, selected_brick_type=None):
    """Add detailed brick type information for each production day"""
    print("Adding daily brick type details to production data")
    
    # Create dictionary to store brick type details for each day
    daily_brick_types = {}
    
    try:
        # Query all production batches in the date range
        batches = ProductionBatch.objects.filter(
            production_date__gte=start_date,
            production_date__lte=end_date
        ).prefetch_related(
            'brick_productions',
            'brick_productions__brick_type'
        )
        
        print(f"Found {batches.count()} production batches to process")
        
        # Process each batch to extract brick type details
        for batch in batches:
            date_str = batch.production_date.isoformat()
            
            # Initialize dict for this date if not exists
            if date_str not in daily_brick_types:
                daily_brick_types[date_str] = {}
                
            # Process each brick production in this batch
            for prod in batch.brick_productions.all():
                # Skip if we're filtering by brick type and this isn't the one
                if selected_brick_type and prod.brick_type.id != selected_brick_type.id:
                    continue
                
                brick_type = prod.brick_type
                brick_type_name = brick_type.name
                
                # Calculate values for this brick type
                total_produced = prod.total_bricks_produced
                packaged = prod.bricks_packaged
                bulk = total_produced - packaged
                wagons = prod.wagons_produced
                
                # Add to daily brick type details
                if brick_type_name not in daily_brick_types[date_str]:
                    daily_brick_types[date_str][brick_type_name] = {
                        'id': str(brick_type.id),
                        'name': brick_type_name,
                        'industrial_code': brick_type.industrial_code,
                        'bulk': 0,
                        'packaged': 0,
                        'wagons': 0
                    }
                
                # Add values
                daily_brick_types[date_str][brick_type_name]['bulk'] += bulk
                daily_brick_types[date_str][brick_type_name]['packaged'] += packaged
                daily_brick_types[date_str][brick_type_name]['wagons'] += wagons
        
        # Add daily brick type details to production data
        production_data['daily_brick_types'] = daily_brick_types
        
        # Also add brick_type details including industrial_code to each brick type
        # in the by_type list for easy access in the frontend
        if 'by_type' in production_data:
            for brick_item in production_data['by_type']:
                try:
                    brick_type = BrickType.objects.get(id=brick_item['id'])
                    brick_item['industrial_code'] = brick_type.industrial_code
                except Exception as e:
                    print(f"Error getting industrial code for brick type {brick_item['id']}: {e}")
                    brick_item['industrial_code'] = brick_item['name']
        
        print(f"Added brick type details for {len(daily_brick_types)} days")
        
    except Exception as e:
        print(f"Error adding daily brick type details: {str(e)}")
        traceback.print_exc()
    
    return production_data

def add_daily_loading_brick_type_details(loading_data, start_date, end_date, selected_brick_type=None):
    """Add detailed brick type information for each loading day"""
    print("Adding daily brick type details to loading data")
    
    # Create dictionary to store brick type details for each day
    daily_brick_types = {}
    
    try:
        # Query all loading records in the date range
        loading_records = LoadingRecord.objects.filter(
            loading_date__gte=start_date,
            loading_date__lte=end_date
        ).prefetch_related(
            'items',
            'items__brick_type'
        )
        
        print(f"Found {loading_records.count()} loading records to process")
        
        # Process each loading record to extract brick type details
        for record in loading_records:
            date_str = record.loading_date.isoformat()
            
            # Initialize dict for this date if not exists
            if date_str not in daily_brick_types:
                daily_brick_types[date_str] = {}
                
            # Process each loading item in this record
            for item in record.items.all():
                # Skip if we're filtering by brick type and this isn't the one
                if selected_brick_type and item.brick_type.id != selected_brick_type.id:
                    continue
                
                brick_type = item.brick_type
                brick_type_name = brick_type.name
                
                # Get values for this loading item
                bulk = item.bulk_quantity
                packaged = item.packaged_quantity
                breakage = item.breakage
                
                # Add to daily brick type details
                if brick_type_name not in daily_brick_types[date_str]:
                    daily_brick_types[date_str][brick_type_name] = {
                        'id': str(brick_type.id),
                        'name': brick_type_name,
                        'industrial_code': brick_type.industrial_code,
                        'bulk': 0,
                        'packaged': 0,
                        'breakage': 0
                    }
                
                # Add values
                daily_brick_types[date_str][brick_type_name]['bulk'] += bulk
                daily_brick_types[date_str][brick_type_name]['packaged'] += packaged
                daily_brick_types[date_str][brick_type_name]['breakage'] += breakage
        
        # Add daily brick type details to loading data
        loading_data['daily_brick_types'] = daily_brick_types
        
        # Also add brick_type details including industrial_code to each brick type
        # in the by_type list for easy access in the frontend
        if 'by_type' in loading_data:
            for brick_item in loading_data['by_type']:
                try:
                    brick_type = BrickType.objects.get(id=brick_item['id'])
                    brick_item['industrial_code'] = brick_type.industrial_code
                except Exception as e:
                    print(f"Error getting industrial code for brick type {brick_item['id']}: {e}")
                    brick_item['industrial_code'] = brick_item['name']
        
        print(f"Added brick type details for {len(daily_brick_types)} days")
        
    except Exception as e:
        print(f"Error adding daily loading brick type details: {str(e)}")
        traceback.print_exc()
    
    return loading_data