import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from .models import StampRightDeclaration, StampRightConfiguration, ForecastStatement, BankAccount
from decimal import Decimal
from datetime import date, datetime
import calendar
import json

class StampRightConfigFormView(View):
    """View for managing Stamp Rights configuration"""
    def get(self, request):
        config = StampRightConfiguration.objects.first()
        bank_accounts = BankAccount.objects.filter(is_active=True)
        
        return JsonResponse({
            'html': render_to_string(
                'tax/stamp_rights/config_form.html',
                {
                    'config': config,
                    'bank_accounts': bank_accounts
                },
                request=request
            )
        })
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            accounting_code = data.get('accounting_code')
            journal_code = data.get('journal_code')
            bank_id = data.get('domiciliation_bank')
            default_amount = data.get('default_amount')
            declaration_day = data.get('declaration_day')
            frequency = data.get('frequency')
            tax_rate = data.get('tax_rate')
            
            if not bank_id:
                return JsonResponse({'status': 'error', 'message': 'Bank account is required'})
            
            bank = BankAccount.objects.get(id=bank_id)
            
            config = StampRightConfiguration.objects.first()
            if not config:
                config = StampRightConfiguration()
            
            config.accounting_code = accounting_code
            config.journal_code = journal_code
            config.domiciliation_bank = bank
            config.default_amount = Decimal(default_amount)
            config.declaration_day = int(declaration_day)
            config.frequency = frequency
            config.tax_rate = Decimal(tax_rate)
            
            config.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Stamp Rights configuration updated successfully'
            })
            
        except Exception as e:
            print(f"Error saving Stamp Rights configuration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StampRightListView(View):
    """View for displaying Stamp Rights declarations"""
    def get(self, request):
        declarations = StampRightDeclaration.objects.all().order_by('-period_year', '-period_month')
        
        try:
            config = StampRightConfiguration.objects.first()
            configured = bool(config)
        except:
            config = None
            configured = False
        
        # Get next available period
        next_period = self._get_next_available_period()
        
        context = {
            'declarations': declarations,
            'config': config,
            'configured': configured,
            'next_period': next_period
        }
        
        return render(request, 'tax/stamp_rights/list.html', context)
    
    def _get_next_available_period(self):
        """Get the next available period for a new declaration"""
        last_declaration = StampRightDeclaration.objects.order_by('-period_year', '-period_month').first()
        
        if not last_declaration:
            # If no declarations yet, start with current month
            today = date.today()
            return {
                'month': today.month,
                'year': today.year
            }
        
        try:
            config = StampRightConfiguration.get_config()
            
            # Calculate next period based on frequency
            next_month = last_declaration.period_month
            next_year = last_declaration.period_year
            
            if config.frequency == 'monthly':
                next_month += 1
            elif config.frequency == 'quarterly':
                next_month += 3
            elif config.frequency == 'biannual':
                next_month += 6
            elif config.frequency == 'annual':
                next_month += 12
            
            # Adjust year if needed
            while next_month > 12:
                next_month -= 12
                next_year += 1
            
            # Don't allow future periods
            today = date.today()
            current_month_year = today.year * 12 + today.month
            next_month_year = next_year * 12 + next_month
            
            if next_month_year > current_month_year:
                next_month = today.month
                next_year = today.year
            
            return {
                'month': next_month,
                'year': next_year
            }
            
        except Exception as e:
            # Default to current month if error
            today = date.today()
            return {
                'month': today.month,
                'year': today.year
            }

class StampRightDeclarationFormView(View):
    """View for creating/editing Stamp Rights declarations"""
    def get(self, request, declaration_id=None):
        if declaration_id:
            declaration = get_object_or_404(StampRightDeclaration, id=declaration_id)
            title = f"Edit Stamp Rights Declaration {declaration.period_month:02d}/{declaration.period_year}"
            is_first = False
        else:
            declaration = None
            title = "New Stamp Rights Declaration"
            is_first = StampRightDeclaration.objects.count() == 0
        
        # Get next available period if creating new declaration
        next_period = None
        if not declaration_id:
            next_period = StampRightListView()._get_next_available_period()
        
        # Check if configuration exists
        try:
            config = StampRightConfiguration.get_config()
        except:
            return JsonResponse({
                'status': 'error',
                'message': 'Stamp Rights configuration must be set up first'
            }, status=400)
        
        return JsonResponse({
            'html': render_to_string(
                'tax/stamp_rights/declaration_form.html',
                {
                    'declaration': declaration,
                    'title': title,
                    'is_first': is_first,
                    'next_period': next_period,
                    'config': config
                },
                request=request
            )
        })
    
    def post(self, request, declaration_id=None):
        try:
            data = json.loads(request.body)
            
            period_month = int(data.get('period_month'))
            period_year = int(data.get('period_year'))
            invoices_amount = Decimal(data.get('invoices_amount'))
            tax_amount = Decimal(data.get('tax_amount', 0))
            notes = data.get('notes', '')
            
            # Validate period
            if not (1 <= period_month <= 12):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid month'
                }, status=400)
            
            # Check for existing declaration in this period
            if declaration_id:
                existing = StampRightDeclaration.objects.filter(
                    period_month=period_month,
                    period_year=period_year
                ).exclude(id=declaration_id).exists()
            else:
                existing = StampRightDeclaration.objects.filter(
                    period_month=period_month,
                    period_year=period_year
                ).exists()
            
            if existing:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Declaration already exists for {period_month:02d}/{period_year}'
                }, status=400)
            
            # Check if only first declaration or following correct sequence
            if not declaration_id and StampRightDeclaration.objects.exists():
                next_period = StampRightListView()._get_next_available_period()
                if period_month != next_period['month'] or period_year != next_period['year']:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Please create declaration for {next_period["month"]:02d}/{next_period["year"]} first'
                    }, status=400)
            
            # Get config to calculate tax amount
            config = StampRightConfiguration.get_config()
            
            # If tax_amount is not provided, calculate it
            if not tax_amount or tax_amount == 0:
                tax_amount = (invoices_amount * config.tax_rate) / Decimal('100.0')
            
            # Create or update declaration
            with transaction.atomic():
                if declaration_id:
                    declaration = get_object_or_404(StampRightDeclaration, id=declaration_id)
                    # If status is paid or rejected, don't allow edits
                    if declaration.status in ['paid', 'rejected']:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Cannot edit {declaration.status} declaration'
                        }, status=400)
                else:
                    declaration = StampRightDeclaration()
                
                declaration.period_month = period_month
                declaration.period_year = period_year
                declaration.invoices_amount = invoices_amount
                declaration.tax_amount = tax_amount
                declaration.notes = notes
                
                # Save will handle forecast creation
                declaration.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Declaration saved successfully'
            })
            
        except Exception as e:
            print(f"Error saving Stamp Rights declaration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StampRightDeclarationStatusView(View):
    """View for updating Stamp Rights declaration status (paid/rejected)"""
    def post(self, request, declaration_id):
        try:
            declaration = get_object_or_404(StampRightDeclaration, id=declaration_id)
            data = json.loads(request.body)
            
            status = data.get('status')
            date_value = data.get('date')
            
            if not status or status not in ['paid', 'rejected']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status'
                }, status=400)
            
            try:
                status_date = datetime.strptime(date_value, '%Y-%m-%d').date()
            except:
                status_date = timezone.now().date()
            
            if status == 'paid':
                declaration.mark_as_paid(status_date)
                message = f"Declaration {declaration.period_month:02d}/{declaration.period_year} marked as paid"
            else:
                declaration.mark_as_rejected(status_date)
                message = f"Declaration {declaration.period_month:02d}/{declaration.period_year} marked as rejected"
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
        except Exception as e:
            print(f"Error updating status: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StampRightDeclarationDeleteView(View):
    """View for deleting Stamp Rights declarations"""
    def post(self, request, declaration_id):
        try:
            declaration = get_object_or_404(StampRightDeclaration, id=declaration_id)
            
            # Only allow deletion of declarations that are not paid
            if declaration.status == 'paid':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot delete paid declaration'
                }, status=400)
            
            # Delete forecast if exists
            if declaration.forecast:
                declaration.forecast.delete()
            
            # Delete declaration
            declaration.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f"Declaration {declaration.period_month:02d}/{declaration.period_year} deleted successfully"
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StampRightCalendarStatusView(View):
    """View for updating Stamp Rights declaration status from calendar"""
    def post(self, request, declaration_id):
        try:
            print(f"\n=== Processing Stamp Rights Calendar Status Update ===")
            print(f"Declaration ID: {declaration_id}")
            
            declaration = get_object_or_404(StampRightDeclaration, id=declaration_id)
            data = json.loads(request.body)
            
            status = data.get('status')
            date_str = data.get('date')
            
            print(f"Status: {status}")
            print(f"Date: {date_str}")
            
            if not status or status not in ['paid', 'rejected']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status'
                }, status=400)
                
            # Convert date string to date object
            try:
                status_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                status_date = timezone.now().date()
                
            print(f"Status date: {status_date}")
                
            # Update declaration status
            if status == 'paid':
                declaration.mark_as_paid(status_date)
                message = f"Stamp Rights Declaration {declaration.period_month:02d}/{declaration.period_year} marked as paid"
            else:
                declaration.mark_as_rejected(status_date)
                message = f"Stamp Rights Declaration {declaration.period_month:02d}/{declaration.period_year} marked as rejected"
                
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
        except Exception as e:
            print(f"Error updating Stamp Rights status: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StampRightForecastView(View):
    """View for loading Stamp Rights forecasts for a specific date"""
    def get(self, request):
        try:
            date = request.GET.get('date')
            bank_id = request.GET.get('bank')

            forecast_date = datetime.strptime(date, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            
            print(f"\n=== Loading Stamp Rights Forecasts for date {forecast_date} ===")
            print(f"Bank Account: {bank_account.account_number}")

            # ONLY fetch forecasts - no updates or creation
            forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False, 
                source_type='stamp_right_declaration'
            )

            print(f"Found {forecasts.count()} Stamp Rights forecasts")
            forecasts_data = []
            total_amount = Decimal('0.00')
            
            for forecast in forecasts:
                # Try to get declaration info
                declaration = None
                is_declared = False
                
                if forecast.source_id:
                    try:
                        declaration = StampRightDeclaration.objects.get(id=forecast.source_id)
                        is_declared = True
                        period = f"{declaration.period_month:02d}/{declaration.period_year}"
                    except:
                        period = forecast.label.split()[-1] if ' ' in forecast.label else ''
                else:
                    period = forecast.label.split()[-1] if ' ' in forecast.label else ''
                
                amount = forecast.debit or Decimal('0.00')
                total_amount += amount
                
                forecasts_data.append({
                    'amount': float(amount),
                    'due_date': forecast_date.strftime('%Y-%m-%d'),
                    'period': period,
                    'label': forecast.label,
                    'is_declared': is_declared,
                    'declaration_id': str(declaration.id) if declaration else None
                })

            return JsonResponse({
                'status': 'success',
                'forecasts': forecasts_data,
                'total': float(total_amount)
            })

        except Exception as e:
            print(f"Error in StampRightForecastView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)