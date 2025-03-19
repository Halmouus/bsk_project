import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import OtherTaxConfiguration, OtherTaxDeclaration, TaxFine, ForecastStatement, BankAccount, Check
from datetime import date, datetime
import calendar
from decimal import Decimal
import json

class OtherTaxConfigFormView(View):
    """View for managing other tax configuration"""
    def get(self, request, tax_type):
        config = OtherTaxConfiguration.objects.filter(tax_type=tax_type).first()
        bank_accounts = BankAccount.objects.filter(is_active=True)
        
        tax_type_display = dict(OtherTaxConfiguration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title())
        
        return JsonResponse({
            'html': render_to_string(
                'tax/other/config_form.html',
                {
                    'config': config,
                    'bank_accounts': bank_accounts,
                    'tax_type': tax_type,
                    'tax_type_display': tax_type_display
                },
                request=request
            )
        })
    
    def post(self, request, tax_type):
        try:
            data = json.loads(request.body)
            
            accounting_code = data.get('accounting_code')
            journal_code = data.get('journal_code')
            bank_id = data.get('domiciliation_bank')
            default_amount = data.get('default_amount', '0.00')
            due_month = data.get('due_month')
            due_day = data.get('due_day')
            fines_accounting_code = data.get('fines_accounting_code')
            
            # Bank can be null since it's only needed for direct debit
            bank = None
            if bank_id:
                bank = BankAccount.objects.get(id=bank_id)

            forecast_bank_id = data.get('forecast_bank')
            forecast_bank = None
            if forecast_bank_id:
                forecast_bank = BankAccount.objects.get(id=forecast_bank_id)
            
            # Convert comma-separated amount to decimal
            default_amount = default_amount.replace(',', '.')
            
            config, created = OtherTaxConfiguration.objects.update_or_create(
                tax_type=tax_type,
                defaults={
                    'accounting_code': accounting_code,
                    'journal_code': journal_code,
                    'domiciliation_bank': bank,
                    'forecast_bank': forecast_bank,
                    'default_amount': Decimal(default_amount),
                    'due_month': int(due_month),
                    'due_day': int(due_day),
                    'fines_accounting_code': fines_accounting_code
                }
            )
            
            tax_type_display = dict(OtherTaxConfiguration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title())
            
            return JsonResponse({
                'status': 'success',
                'message': f'{tax_type_display} configuration {"created" if created else "updated"} successfully'
            })
            
        except Exception as e:
            print(f"Error saving tax config: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxListView(View):
    """View for displaying other tax declarations"""
    def get(self, request, tax_type):
        declarations = OtherTaxDeclaration.objects.filter(tax_type=tax_type).order_by('-year')
        
        try:
            config = OtherTaxConfiguration.objects.filter(tax_type=tax_type).first()
            configured = bool(config)
        except:
            config = None
            configured = False
        
        # Get current year for new declaration
        current_year = timezone.now().year
        
        tax_type_display = dict(OtherTaxDeclaration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title())
        
        context = {
            'declarations': declarations,
            'config': config,
            'configured': configured,
            'current_year': current_year,
            'tax_type': tax_type,
            'tax_type_display': tax_type_display
        }
        
        return render(request, 'tax/other/list.html', context)


class OtherTaxDeclarationFormView(View):
    """View for creating/editing other tax declarations"""
    def get(self, request, tax_type, declaration_id=None):
        if declaration_id:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id)
            title = f"Edit {declaration.get_tax_type_display()} Declaration {declaration.year}"
        else:
            declaration = None
            tax_type_display = dict(OtherTaxDeclaration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title())
            title = f"New {tax_type_display} Declaration"
        
        # Check if configuration exists
        try:
            config = OtherTaxConfiguration.get_config(tax_type)
        except ValidationError:
            return JsonResponse({
                'status': 'error',
                'message': f'{tax_type.title()} Tax configuration must be set up first'
            }, status=400)
        
        # Get current year if creating new
        current_year = timezone.now().year if not declaration else None
        
        # Get all fines if this is an existing declaration
        fines = []
        linked_checks = []
        if declaration:
            fines = declaration.fines.all().order_by('-fine_date')
            # Get linked checks using the GenericRelation
            linked_checks = declaration.checks.all().select_related(
                'checker', 'checker__bank_account'
            )
        
        return JsonResponse({
            'html': render_to_string(
                'tax/other/declaration_form.html',
                {
                    'declaration': declaration,
                    'title': title,
                    'current_year': current_year,
                    'config': config,
                    'tax_type': tax_type,
                    'tax_type_display': dict(OtherTaxDeclaration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title()),
                    'fines': fines,
                    'linked_checks': linked_checks,  # Add this line
                    'payment_methods': OtherTaxDeclaration.PAYMENT_METHOD_CHOICES
                },
                request=request
            )
        })
    
    def post(self, request, tax_type, declaration_id=None):
        try:
            data = json.loads(request.body)
            
            year = int(data.get('year'))
            amount = data.get('amount').replace(',', '.')
            payment_method = data.get('payment_method')
            notes = data.get('notes', '')
            
            # Validate year
            current_year = timezone.now().year
            if year < 2000 or year > current_year + 1:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid year: must be between 2000 and {current_year + 1}'
                }, status=400)
            
            # Check for existing declaration in this year
            if declaration_id:
                existing = OtherTaxDeclaration.objects.filter(
                    tax_type=tax_type,
                    year=year
                ).exclude(id=declaration_id).exists()
            else:
                existing = OtherTaxDeclaration.objects.filter(
                    tax_type=tax_type,
                    year=year
                ).exists()

            # We don't return an error, we'll just warn the user in the response
            existing_warning = existing
            
            # Create or update declaration
            with transaction.atomic():
                if declaration_id:
                    declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id)
                    # If status is paid or rejected, don't allow edits
                    if declaration.status == 'paid':
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Cannot edit paid declaration'
                        }, status=400)
                else:
                    declaration = OtherTaxDeclaration(tax_type=tax_type)
                
                declaration.year = year
                declaration.amount = Decimal(amount)
                declaration.payment_method = payment_method
                declaration.notes = notes
                
                # Calculate due date based on config
                config = OtherTaxConfiguration.get_config(tax_type)
                day = config.due_day
                month = config.due_month
                
                # Create date with specified day, or last day of month if out of range
                last_day = calendar.monthrange(year, month)[1]
                if day > last_day:
                    declaration.due_date = datetime(year, month, last_day).date()
                else:
                    declaration.due_date = datetime(year, month, day).date()
                
                # Save will handle forecast creation if direct debit
                declaration.save()
            
            # Return response with declaration ID for new declarations
            if not declaration_id:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Declaration saved successfully',
                    'declaration_id': str(declaration.id),
                    'existing_warning': existing_warning
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Declaration updated successfully',
                    'existing_warning': existing_warning
                })
            
        except Exception as e:
            print(f"Error in OtherTaxDeclarationFormView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxDeclarationStatusView(View):
    """View for updating other tax declaration status (paid/rejected)"""
    def post(self, request, tax_type, declaration_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            data = json.loads(request.body)
            
            status = data.get('status')
            date_value = data.get('date')
            amount = data.get('amount', '0.00').replace(',', '.')
            payment_method = data.get('payment_method')
            
            if not status or status not in ['paid', 'partially_paid', 'rejected']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status'
                }, status=400)
            
            try:
                status_date = datetime.strptime(date_value, '%Y-%m-%d').date()
            except:
                status_date = timezone.now().date()
            
            if status in ['paid', 'partially_paid']:
                # Make sure amount is provided for payment
                if not amount or Decimal(amount) <= 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment amount is required'
                    }, status=400)
                
                # Make sure payment method is provided
                if not payment_method:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment method is required'
                    }, status=400)
                
                # Add payment to declaration
                declaration.add_payment(Decimal(amount), payment_method, status_date)
                message = f"Payment of {amount} added to declaration {declaration.year}"
            else:
                # Extract rejection cause and notes
                rejection_cause = data.get('rejection_cause')
                rejection_notes = data.get('rejection_notes', '')
                
                declaration.mark_as_rejected(status_date, rejection_cause, rejection_notes)
                message = f"Declaration {declaration.year} marked as rejected"
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
        except Exception as e:
            print(f"Error in OtherTaxDeclarationStatusView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxDeclarationDeleteView(View):
    """View for deleting other tax declarations"""
    def post(self, request, tax_type, declaration_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            
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
                'message': f"Declaration {declaration.year} deleted successfully"
            })
            
        except Exception as e:
            print(f"Error in OtherTaxDeclarationDeleteView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class TaxFineFormView(View):
    """View for adding/editing tax fines"""
    def get(self, request, tax_type, declaration_id, fine_id=None):
        declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
        
        if fine_id:
            fine = get_object_or_404(TaxFine, id=fine_id, declaration=declaration)
            title = "Edit Fine"
        else:
            fine = None
            title = "Add Fine"
        
        tax_type_display = dict(OtherTaxDeclaration.TAX_TYPE_CHOICES).get(tax_type, tax_type.title())
        
        return JsonResponse({
            'html': render_to_string(
                'tax/other/fine_form.html',
                {
                    'fine': fine,
                    'declaration': declaration,
                    'title': title,
                    'tax_type': tax_type,
                    'tax_type_display': tax_type_display
                },
                request=request
            )
        })
    
    def post(self, request, tax_type, declaration_id, fine_id=None):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            data = json.loads(request.body)
            
            amount = data.get('amount').replace(',', '.')
            fine_date = data.get('fine_date')
            reference = data.get('reference', '')
            description = data.get('description', '')
            paid = data.get('paid', False)
            payment_date = data.get('payment_date') if paid else None
            
            # Validate amount
            if not amount or Decimal(amount) <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Fine amount is required and must be positive'
                }, status=400)
            
            # Validate fine date
            try:
                fine_date = datetime.strptime(fine_date, '%Y-%m-%d').date()
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid fine date'
                }, status=400)
            
            # Validate payment date if paid
            if paid and payment_date:
                try:
                    payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
                except:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid payment date'
                    }, status=400)
            
            # Create or update fine
            if fine_id:
                fine = get_object_or_404(TaxFine, id=fine_id, declaration=declaration)
            else:
                fine = TaxFine(declaration=declaration)
            
            fine.amount = Decimal(amount)
            fine.fine_date = fine_date
            fine.reference = reference
            fine.description = description
            fine.paid = paid
            fine.payment_date = payment_date
            
            fine.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f"Fine {'updated' if fine_id else 'added'} successfully"
            })
            
        except Exception as e:
            print(f"Error in TaxFineFormView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class TaxFineDeleteView(View):
    """View for deleting tax fines"""
    def post(self, request, tax_type, declaration_id, fine_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            fine = get_object_or_404(TaxFine, id=fine_id, declaration=declaration)
            
            fine.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': "Fine deleted successfully"
            })
            
        except Exception as e:
            print(f"Error in TaxFineDeleteView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxDocumentUploadView(View):
    """View for uploading tax documents"""
    def post(self, request, tax_type, declaration_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            
            document_type = request.POST.get('document_type')
            if document_type not in ['tax_notice', 'payment_receipt']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid document type'
                }, status=400)
                
            file = request.FILES.get('document')
            if not file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No file uploaded'
                }, status=400)
            
            # Check file size (limit to 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB in bytes
                return JsonResponse({
                    'status': 'error',
                    'message': 'File size exceeds 10MB limit'
                }, status=400)
                
            # Check file type (optional)
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
                }, status=400)
            
            # Delete existing document if present
            if document_type == 'tax_notice' and declaration.tax_notice_document:
                declaration.tax_notice_document.delete()
            elif document_type == 'payment_receipt' and declaration.payment_receipt_document:
                declaration.payment_receipt_document.delete()
            
            # Set the appropriate document field
            if document_type == 'tax_notice':
                declaration.tax_notice_document = file
            else:  # payment_receipt
                declaration.payment_receipt_document = file
                
            declaration.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Document uploaded successfully',
                'document_url': declaration.tax_notice_document.url if document_type == 'tax_notice' else declaration.payment_receipt_document.url
            })
            
        except Exception as e:
            print(f"Error uploading document: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxDocumentDeleteView(View):
    """View for deleting tax documents"""
    def post(self, request, tax_type, declaration_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id, tax_type=tax_type)
            
            data = json.loads(request.body)
            document_type = data.get('document_type')
            
            if document_type not in ['tax_notice', 'payment_receipt']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid document type'
                }, status=400)
                
            # Delete the appropriate document
            if document_type == 'tax_notice':
                if declaration.tax_notice_document:
                    declaration.tax_notice_document.delete()
                    declaration.tax_notice_document = None
            else:  # payment_receipt
                if declaration.payment_receipt_document:
                    declaration.payment_receipt_document.delete()
                    declaration.payment_receipt_document = None
                    
            declaration.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'{"Tax notice" if document_type == "tax_notice" else "Payment receipt"} document deleted successfully'
            })
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class OtherTaxForecastView(View):
    """View for loading tax forecasts for a specific date"""
    def get(self, request, tax_type):
        try:
            date_str = request.GET.get('date')
            bank_id = request.GET.get('bank')

            forecast_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            bank_account = BankAccount.objects.get(id=bank_id)
            
            print(f"\n=== Loading {tax_type.title()} Tax Forecasts for date {forecast_date} ===")
            print(f"Bank Account: {bank_account.account_number}")

            # Fetch forecasts for this date and bank
            forecasts = ForecastStatement.objects.filter(
                bank_account=bank_account,
                date=forecast_date,
                is_processed=False, 
                source_type=f"{tax_type}_tax"
            )

            print(f"Found {forecasts.count()} tax forecasts")
            forecasts_data = []
            total_amount = Decimal('0.00')
            
            for forecast in forecasts:
                # Try to get declaration info
                declaration = None
                is_declared = False
                
                if forecast.source_id:
                    try:
                        declaration = OtherTaxDeclaration.objects.get(id=forecast.source_id, tax_type=tax_type)
                        is_declared = True
                        year = declaration.year
                    except:
                        year = forecast.label.split()[-1] if ' ' in forecast.label else ''
                else:
                    year = forecast.label.split()[-1] if ' ' in forecast.label else ''
                
                amount = forecast.debit or Decimal('0.00')
                total_amount += amount
                
                forecasts_data.append({
                    'amount': float(amount),
                    'due_date': forecast_date.strftime('%Y-%m-%d'),
                    'year': year,
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
            print(f"Error in OtherTaxForecastView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        
@method_decorator(csrf_exempt, name='dispatch')
class DeclarationPaymentsView(View):
    """View for displaying payment details for a tax declaration"""
    def get(self, request, tax_type, declaration_id):
        try:
            declaration = get_object_or_404(OtherTaxDeclaration, id=declaration_id)
            
            # Get linked checks
            linked_checks = declaration.checks.all().select_related(
                'checker', 'checker__bank_account'
            )
            
            # Calculate payment values
            payment_percentage = 0
            remaining_amount = declaration.amount
            
            if declaration.status == 'partially_paid' and hasattr(declaration, 'paid_amount') and declaration.paid_amount and declaration.amount > 0:
                payment_percentage = round((declaration.paid_amount / declaration.amount) * 100)
                remaining_amount = declaration.amount - declaration.paid_amount
            
            # Calculate total fines amount
            fines = declaration.fines.all()
            total_fines = sum(fine.amount for fine in fines)
            
            # Calculate total checks amount
            total_checks_amount = sum(check.amount for check in linked_checks)
            
            # Calculate grand total (declaration + fines)
            grand_total = declaration.amount + total_fines
            
            return JsonResponse({
                'html': render_to_string(
                    'tax/other/payment_details.html',
                    {
                        'declaration': declaration,
                        'linked_checks': linked_checks,
                        'tax_type': tax_type,
                        'payment_percentage': payment_percentage,
                        'remaining_amount': remaining_amount,
                        'total_fines': total_fines,
                        'total_checks_amount': total_checks_amount,
                        'grand_total': grand_total
                    },
                    request=request
                )
            })
        except Exception as e:
            print(f"Error in DeclarationPaymentsView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)