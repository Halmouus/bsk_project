import calendar
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import traceback

from .models import (
    AccountingEntry, PayConfiguration, PayItem, PayDeclaration, PayDeclarationItem,
    BankAccount, DirectDebit, ForecastStatement
)

class PayConfigurationView(View):
    """View for managing global pay configuration"""
    def get(self, request):
        print("\n=== Pay Configuration View ===")
        try:
            config = PayConfiguration.objects.first()
            bank_accounts = BankAccount.objects.filter(is_active=True)

            context = {
                'config': config,
                'bank_accounts': bank_accounts
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/config_form.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/configuration.html', context)

        except Exception as e:
            print(f"Error in pay config view: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request):
        print("\n=== Saving Pay Configuration ===")
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")

            with transaction.atomic():
                config = PayConfiguration.objects.first()
                if not config:
                    print("Creating new configuration")
                    config = PayConfiguration()
                
                # Update fields
                config.generation_day = data['generation_day']
                config.account_code = data['account_code']
                config.journal_code = data.get('journal_code', '07')
                config.domiciliation_bank = BankAccount.objects.get(
                    id=data['domiciliation_bank']
                )
                
                config.save()
                print(f"Configuration saved successfully")

                return JsonResponse({
                    'status': 'success',
                    'message': _('Configuration saved successfully')
                })

        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayListView(View):
    """Main pay dashboard view"""
    def get(self, request):
        print("\n=== Pay Dashboard View ===")
        try:
            config = PayConfiguration.objects.first()
            declarations = PayDeclaration.objects.all().order_by('-created_at')
            pending = PayDeclaration.objects.filter(status=PayDeclaration.STATUS_DECLARED)
            declarations_list = declarations[:10]
            items = PayItem.objects.filter(is_active=True)

            # Calculate total estimated monthly amount
            estimated_total = sum(
                item.default_amount if item.is_debit else -item.default_amount 
                for item in items
            )

            context = {
                'config': config,
                'declarations': declarations,
                'pending_count': pending.count(),
                'items_count': items.count(),
                'estimated_total': estimated_total
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/dashboard.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/dashboard.html', context)

        except Exception as e:
            print(f"Error in pay dashboard: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

class PayItemListView(View):
    """View for listing pay items"""
    def get(self, request):
        print("\n=== Pay Items List View ===")
        try:
            items = PayItem.objects.all()
            
            total_debit = sum(item.default_amount for item in items if item.is_debit)
            total_credit = sum(item.default_amount for item in items if not item.is_debit)
            net_total = total_debit - total_credit

            context = {
                'items': items,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'net_total': net_total
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/items_table.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/items.html', context)

        except Exception as e:
            print(f"Error in pay items list: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class PayItemCreateView(View):
    """View for creating pay items"""
    def post(self, request):
        print("\n=== Creating Pay Item ===")
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")

            with transaction.atomic():
                item = PayItem.objects.create(
                    description=data['description'],
                    account_code=data['account_code'],
                    default_amount=data['default_amount'],
                    is_debit=data['is_debit']
                )
                print(f"Created item: {item}")

                return JsonResponse({
                    'status': 'success',
                    'message': _('Item created successfully'),
                    'id': str(item.id)
                })

        except Exception as e:
            print(f"Error creating pay item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class PayItemUpdateView(View):
    """View for updating pay items"""
    def post(self, request, pk):
        print(f"\n=== Updating Pay Item {pk} ===")
        try:
            item = get_object_or_404(PayItem, pk=pk)
            data = json.loads(request.body)
            print(f"Received data: {data}")

            with transaction.atomic():
                item.description = data['description']
                item.account_code = data['account_code']
                item.default_amount = data['default_amount']
                item.is_debit = data['is_debit']
                item.is_active = data.get('is_active', True)
                
                item.save()
                print(f"Updated item: {item}")

                return JsonResponse({
                    'status': 'success',
                    'message': _('Item updated successfully')
                })

        except Exception as e:
            print(f"Error updating pay item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayItemDeleteView(View):
    """View for deleting pay items"""
    def post(self, request, pk):
        print(f"\n=== Deleting Pay Item {pk} ===")
        try:
            item = get_object_or_404(PayItem, pk=pk)
            item.is_active = False
            item.save()
            return JsonResponse({'status': 'success', 'message': _('Item deleted successfully')})
        except Exception as e:
            print(f"Error deleting pay item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class PayDeclarationListView(View):
    """View for listing pay declarations"""
    def get(self, request):
        print("\n=== Pay Declarations List View ===")
        try:
            declarations = PayDeclaration.objects.all()
            
            # Filter by period if specified
            year = request.GET.get('year')
            month = request.GET.get('month')
            if year and month:
                declarations = declarations.filter(
                    period_year=year,
                    period_month=month
                )

            context = {
                'declarations': declarations,
                'total_paid': sum(d.total_amount for d in declarations if d.status == PayDeclaration.STATUS_PAID),
                'total_pending': sum(d.total_amount for d in declarations if d.status == PayDeclaration.STATUS_DECLARED)
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/declarations_table.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/declarations.html', context)

        except Exception as e:
            print(f"Error in declarations list: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

class PayDeclarationCreateView(View):
    """View for creating pay declarations"""
    def post(self, request):
        print("\n=== Creating Pay Declaration ===")
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")

            with transaction.atomic():
                # Check if declaration already exists
                if PayDeclaration.objects.filter(
                    period_year=data['year'],
                    period_month=data['month']
                ).exists():
                    raise ValidationError(_("Declaration already exists for this period"))

                # Get configuration
                config = PayConfiguration.get_config()
                
                # Calculate due date (generation day of the period)
                month = int(data['month'])
                year = int(data['year'])
                # Get last day of month
                last_day = calendar.monthrange(year, month)[1]
                # Use generation day or last day of month if generation day is higher
                generation_day = min(config.generation_day, last_day)
                due_date = date(year, month, generation_day)
                
                # Adjust for weekends
                while due_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                    due_date += timedelta(days=1)
                
                print(f"Calculated due date: {due_date}")

                # Create declaration
                declaration = PayDeclaration.objects.create(
                    period_year=data['year'],
                    period_month=data['month'],
                    status=PayDeclaration.STATUS_DRAFT,
                    total_amount=Decimal('0.00'),
                    due_date=due_date  # Set the calculated due date
                )

                # Create items from templates
                total_amount = Decimal('0.00')
                for template in PayItem.objects.filter(is_active=True):
                    item = PayDeclarationItem.objects.create(
                        declaration=declaration,
                        description=template.description,
                        account_code=template.account_code,
                        amount=template.default_amount,
                        is_debit=template.is_debit,
                        template_item=template
                    )
                    amount = item.amount if item.is_debit else -item.amount
                    total_amount += amount

                # Update total and create forecast
                declaration.total_amount = total_amount
                declaration.save()

                # Create forecast
                forecast = ForecastStatement.objects.create(
                    bank_account=config.domiciliation_bank,
                    date=declaration.due_date,
                    label=_("Pay Declaration {month:02d}/{year}").format(
                        month=int(declaration.period_month),
                        year=declaration.period_year
                    ),
                    debit=total_amount,
                    reference=f"PAY-{int(declaration.period_month):02d}-{declaration.period_year}",
                    source_type='pay_declaration',
                    source_id=declaration.id
                )
                declaration.forecast = forecast
                declaration.save()

                print(f"Created declaration: {declaration}")
                return JsonResponse({
                    'status': 'success',
                    'message': _('Declaration created successfully'),
                    'id': str(declaration.id)
                })

        except Exception as e:
            print(f"Error creating declaration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayDeclarationDetailView(View):
    """View for declaration details"""
    def get(self, request, pk):
        print(f"\n=== Pay Declaration Detail View {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            items = declaration.items.all()

            context = {
                'declaration': declaration,
                'items': items,
                'total_debit': sum(i.amount for i in items if i.is_debit),
                'total_credit': sum(i.amount for i in items if not i.is_debit)
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/declaration_detail.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/declaration_detail.html', context)

        except Exception as e:
            print(f"Error in declaration detail: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

class PayDeclarationItemUpdateView(View):
    """View for updating declaration items"""
    def post(self, request, pk, item_pk):
        print(f"\n=== Updating Pay Declaration Item {item_pk} ===")
        try:
            item = get_object_or_404(PayDeclarationItem, pk=item_pk, declaration_id=pk)
            data = json.loads(request.body)
            print(f"Received data: {data}")

            with transaction.atomic():
                # Convert old amount to Decimal for calculation
                old_amount = Decimal(str(item.amount)) if item.is_debit else -Decimal(str(item.amount))
                
                item.description = data['description']
                item.account_code = data['account_code']
                # Convert new amount to Decimal
                item.amount = Decimal(str(data['amount']))
                item.is_debit = data['is_debit']
                item.save()

                # Calculate new amount using Decimal
                new_amount = item.amount if item.is_debit else -item.amount
                difference = new_amount - old_amount
                declaration = item.declaration
                declaration.total_amount += difference
                declaration.save()

                # Update forecast
                if declaration.forecast:
                    declaration.forecast.debit = declaration.total_amount
                    declaration.forecast.save()

                print(f"Updated item: {item}")
                return JsonResponse({
                    'status': 'success',
                    'message': _('Item updated successfully')
                })

        except Exception as e:
            print(f"Error updating declaration item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayAccountingView(View):
    """View for pay accounting entries"""
    def get(self, request):
        print("\n=== Pay Accounting View ===")
        try:
            # Get filter parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get entries
            entries = AccountingEntry.get_entries_for_journal('07', start_date, end_date)
            
            context = {
                'entries': entries,
                'total_debit': sum(e['debit'] or 0 for e in entries),
                'total_credit': sum(e['credit'] or 0 for e in entries)
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': render_to_string(
                        'pay/partials/accounting_table.html',
                        context,
                        request=request
                    )
                })

            return render(request, 'pay/accounting.html', context)

        except Exception as e:
            print(f"Error in pay accounting: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

class PayDeclarationActionView(View):
    """View for declaration actions (pay/reject)"""
    def post(self, request, pk):
        print(f"\n=== Pay Declaration Action {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            data = json.loads(request.body)
            action = data.get('action')
            print(f"Action: {action}")

            with transaction.atomic():
                if action == 'pay':
                    payment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    declaration.mark_as_paid(payment_date)
                    message = _('Declaration marked as paid')
                elif action == 'reject':
                    rejection_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    declaration.mark_as_rejected(rejection_date, data.get('reason'))
                    message = _('Declaration marked as rejected')
                else:
                    raise ValidationError(_("Invalid action"))

                return JsonResponse({
                    'status': 'success',
                    'message': message
                })

        except Exception as e:
            print(f"Error in declaration action: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayDeclarationUpdateView(View):
    """View for updating pay declarations"""
    def post(self, request, pk):
        print(f"\n=== Updating Pay Declaration {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            data = json.loads(request.body)
            print(f"Received data: {data}")

            if declaration.status != PayDeclaration.STATUS_DRAFT:
                raise ValidationError(_("Only draft declarations can be updated"))

            with transaction.atomic():
                if 'status' in data and data['status'] == 'declared':
                    declaration.status = PayDeclaration.STATUS_DECLARED
                    message = _('Declaration declared successfully')
                else:
                    message = _('Declaration updated successfully')
                
                declaration.save()

                return JsonResponse({
                    'status': 'success',
                    'message': message
                })

        except Exception as e:
            print(f"Error updating declaration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayDeclarationDeleteView(View):
    """View for deleting pay declarations"""
    def post(self, request, pk):
        print(f"\n=== Deleting Pay Declaration {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            
            if declaration.status != PayDeclaration.STATUS_DRAFT:
                raise ValidationError(_("Only draft declarations can be deleted"))

            with transaction.atomic():
                declaration.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': _('Declaration deleted successfully')
                })

        except Exception as e:
            print(f"Error deleting declaration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayDeclarationItemCreateView(View):
    """View for creating declaration items"""
    def post(self, request, pk):
        print(f"\n=== Creating Declaration Item for Declaration {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            data = json.loads(request.body)
            print(f"Received data: {data}")

            if declaration.status != PayDeclaration.STATUS_DRAFT:
                raise ValidationError(_("Can't add items to non-draft declarations"))

            with transaction.atomic():
                # Convert amount to Decimal
                amount = Decimal(str(data['amount']))
                
                item = PayDeclarationItem.objects.create(
                    declaration=declaration,
                    description=data['description'],
                    account_code=data['account_code'],
                    amount=amount,  # Use converted amount
                    is_debit=data['is_debit']
                )

                # Update declaration total using Decimal
                amount_to_add = amount if item.is_debit else -amount
                declaration.total_amount += amount_to_add
                declaration.save()

                # Update forecast if exists
                if declaration.forecast:
                    declaration.forecast.debit = declaration.total_amount
                    declaration.forecast.save()

                print(f"Created item: {item}")
                return JsonResponse({
                    'status': 'success',
                    'message': _('Item created successfully')
                })

        except Exception as e:
            print(f"Error creating declaration item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class PayDeclarationItemDeleteView(View):
    """View for deleting declaration items"""
    def post(self, request, pk, item_pk):
        print(f"\n=== Deleting Declaration Item {item_pk} ===")
        try:
            item = get_object_or_404(PayDeclarationItem, pk=item_pk, declaration_id=pk)
            
            if item.declaration.status != PayDeclaration.STATUS_DRAFT:
                raise ValidationError(_("Can't delete items from non-draft declarations"))

            with transaction.atomic():
                # Update declaration total
                amount = item.amount if item.is_debit else -item.amount
                declaration = item.declaration
                declaration.total_amount -= amount
                declaration.save()

                # Update forecast if exists
                if declaration.forecast:
                    declaration.forecast.debit = declaration.total_amount
                    declaration.forecast.save()

                item.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': _('Item deleted successfully')
                })

        except Exception as e:
            print(f"Error deleting declaration item: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        
class PayPendingDeclarationsView(View):
    """View for pending declarations"""
    def get(self, request):
        try:
            declarations = PayDeclaration.objects.filter(
                status=PayDeclaration.STATUS_DECLARED
            ).order_by('due_date')
            
            context = {
                'declarations': declarations,
                'total_amount': sum(d.total_amount for d in declarations)
            }
            
            return render(request, 'pay/pending.html', context)
            
        except Exception as e:
            print(f"Error in pending declarations: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        
class PayDeclarationDeclareView(View):
    """View for declaring a pay declaration"""
    def post(self, request, pk):
        print(f"\n=== Declaring Pay Declaration {pk} ===")
        try:
            declaration = get_object_or_404(PayDeclaration, pk=pk)
            
            if declaration.status != PayDeclaration.STATUS_DRAFT:
                raise ValidationError(_("Only draft declarations can be declared"))
                
            if declaration.items.count() == 0:
                raise ValidationError(_("Cannot declare empty declaration"))

            with transaction.atomic():
                declaration.status = PayDeclaration.STATUS_DECLARED
                declaration.save()
                
                # Make sure forecast exists
                if not declaration.forecast:
                    config = PayConfiguration.get_config()
                    declaration.forecast = ForecastStatement.objects.create(
                        bank_account=config.domiciliation_bank,
                        date=declaration.due_date,
                        label=_("Pay Declaration {month:02d}/{year}").format(
                            month=declaration.period_month,
                            year=declaration.period_year
                        ),
                        debit=declaration.total_amount,
                        reference=f"PAY-{declaration.period_month:02d}-{declaration.period_year}",
                        source_type='pay_declaration',
                        source_id=declaration.id
                    )
                    declaration.save()

                print(f"Declaration declared successfully")
                return JsonResponse({
                    'status': 'success',
                    'message': _('Declaration declared successfully')
                })

        except Exception as e:
            print(f"Error declaring declaration: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)