import calendar
import math
import os
import uuid
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, MinLengthValidator, MaxLengthValidator, FileExtensionValidator
from .base import BaseModel
from datetime import timedelta
import datetime
import random
import string
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q
import logging
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from itertools import groupby
from operator import itemgetter
import traceback
from dateutil.relativedelta import relativedelta
from django.db.models.functions import Coalesce
from django.db.models import Sum, Manager, Max
from django.utils.translation import gettext_lazy as _
import re

logger = logging.getLogger(__name__)
    
class Checker(BaseModel):
    TYPE_CHOICES = [
        ('CHQ', 'Cheque'),
        ('LCN', 'LCN')
    ]
    
    PAGE_CHOICES = [
        (25, '25'),
        (50, '50'),
        (100, '100')
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_use', 'In Use'), 
        ('completed', 'Completed')
    ]

    code = models.CharField(max_length=10, unique=True, blank=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)  # New field
    num_pages = models.IntegerField(choices=PAGE_CHOICES)
    index = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Z]{1,3}$', _('Must be 1 to 3 uppercase letters.'))]
    )
    starting_page = models.IntegerField(validators=[MinValueValidator(1)])
    final_page = models.IntegerField(blank=True)
    current_position = models.IntegerField(blank=True)
    is_active = models.BooleanField(default=True)
    owner = models.CharField(max_length=100, default="Briqueterie Sidi Kacem")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')

    def update_status(self):
        """Update checker status based on remaining pages"""
        print("\n=== Updating Checker Status ===")
        print(f"Checker {self.id} - Current status: {self.status}")
        print(f"Remaining pages: {self.remaining_pages}")
        print(f"Total pages: {self.num_pages}")
        
        if self.remaining_pages == self.num_pages:
            self.status = 'new'
        elif self.remaining_pages > 0:
            self.status = 'in_use'
        else:
            self.status = 'completed'
        
        print(f"New status: {self.status}")
        self.save()

    def get_status(self):
        STATUS_STYLES = {
            'new': {'label': 'New', 'color': 'primary'},
            'in_use': {'label': 'In Use', 'color': 'warning'},
            'completed': {'label': 'Completed', 'color': 'success'},
        }
        return STATUS_STYLES.get(self.status, {'label': 'Unknown', 'color': 'secondary'})

    @property
    def remaining_pages(self):
        print(f"Calculating remaining pages for {self.bank_account.bank}")
        
        # Get all used positions (excluding cancelled checks)
        used_positions = set(
            self.checks.values_list('position', flat=True)
        )
        used_positions_count = self.checks.count()
        # Count available positions
        available_count = self.final_page - self.starting_page + 1 - used_positions_count
        print(f"Used positions: {used_positions}")
        print(f"Available positions count: {available_count}")
        
        return available_count
    
    def clean(self):
        if self.bank_account:
            if not self.bank_account.is_active:
                raise ValidationError(_("Cannot create checker for inactive bank account"))
            if self.bank_account.account_type != 'national':
                raise ValidationError(_("Can only create checkers for national accounts"))
        super().clean()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.final_page:
            self.final_page = self.starting_page + self.num_pages - 1
        if not self.current_position:
            self.current_position = self.starting_page
        super().save(*args, **kwargs)

    def generate_code(self):
        # Generate random alphanumeric code
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    #signature part#
    position_signatures = models.JSONField(default=dict)

    def get_position_signature_status(self, position):
        print(f"Getting signature status for position {position}")
        print(f"Current signatures: {self.position_signatures}")
        return self.position_signatures.get(str(position), {
            'signatures': [],
            'timestamps': []
        })

    def add_signature(self, position, signature):
        print(f"Adding signature {signature} to position {position}")
        position = str(position)
        if position not in self.position_signatures:
            print(f"Position {position} not found, initializing")
            self.position_signatures[position] = {
                'signatures': [],
                'timestamps': []
            }
        
        if signature not in self.position_signatures[position]['signatures']:
            print(f"Adding new signature {signature}")
            self.position_signatures[position]['signatures'].append(signature)
            self.position_signatures[position]['timestamps'].append(
                timezone.now().isoformat()
            )
            print(f"Updated signatures: {self.position_signatures}")
            self.save()
        else:
            print(f"Signature {signature} already exists for position {position}")
        
    
    def get_last_issued_check(self):
        """Get the last issued check."""
        return self.checks.exclude(status="available").order_by('-position').first()

    def get_next_available_position(self):
        """Calculate the next available position."""
        last_check = self.get_last_issued_check()
        if last_check:
            last_position = int(last_check.position[len(self.index):])
            next_position = last_position + 1
            if next_position <= self.final_page:
                return next_position
        return self.starting_page

    def __str__(self):
        return f'Checker {self.index}'

    class Meta:
        ordering = ['-created_at']

class Check(BaseModel):
    checker = models.ForeignKey(Checker, on_delete=models.PROTECT, related_name='checks')
    position = models.CharField(max_length=10, unique=True)
    creation_date = models.DateField(default=timezone.now)
    beneficiary = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    cause = models.ForeignKey(
        Invoice, 
        on_delete=models.PROTECT, 
        null=True,
        blank=True
    )
    payment_due = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_supplier_payment = models.BooleanField(default=False)
    is_tax_payment = models.BooleanField(default=False)
    tax_declaration_type = models.CharField(max_length=50, null=True, blank=True)
    tax_declaration_id = models.UUIDField(null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name="tax_checks"
    )
    object_id = models.UUIDField(null=True, blank=True)
    tax_declaration = GenericForeignKey('content_type', 'object_id')

    observation = models.TextField(blank=True)
    delivered = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=25,
        choices=[
            ('draft', 'Draft'),
            ('printed', 'Printed'),
            ('ready_to_sign', 'Ready to Sign'),
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
            ('paid', 'Paid'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )

    REJECTION_REASONS = [
        ('insufficient_funds', 'Insufficient Funds'),
        ('signature_mismatch', 'Signature Mismatch'),
        ('amount_error', 'Amount Error'),
        ('date_error', 'Date Error'),
        ('other', 'Other')
    ]

    SIGNATURE_CHOICES = [
        ('OUK', 'OUK'),
        ('KEZ', 'KEZ')
    ]
    

    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS, null=True, blank=True)
    rejection_note = models.TextField(blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)

    replaces = models.ForeignKey('self', null=True, blank=True, related_name='replaced_by', on_delete=models.PROTECT)

    received_at = models.DateTimeField(null=True, blank=True)
    received_notes = models.TextField(blank=True)

    signatures = models.JSONField(default=list)

    vat_declared = models.BooleanField(default=False)
    vat_declaration_period = models.CharField(
        max_length=7,  
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                r'^\d{2}-\d{4}$',
                _('Period must be in MM-YYYY format')
            )
        ]
    )

    def get_allocated_amount(self):
        """Get total allocated amount"""
        return sum(
            allocation.amount 
            for allocation in self.allocations.all()
        )
    
    def get_available_amount(self):
        """Get remaining amount available for allocation"""
        return self.amount - self.get_allocated_amount()
    
    def can_be_paid(self):
        """Check if payment can be marked as paid"""
        if self.is_supplier_payment:
            # Must be fully allocated for supplier payments
            return self.get_available_amount() == 0
        return True  # Direct invoice payments can always be paid
    
    def save(self, *args, **kwargs):
        print("\n=== Check Save Method Started ===")
        print(f"Check ID: {self.pk}")
        print(f"Is new check: {not self.pk}")
        print(f"Current position: {getattr(self, 'position', None)}")
        
        if not self.pk:  # New check
            print("Processing new check creation")
            print(f"Checker ID: {self.checker.id}")
            print(f"Checker position_signatures: {self.checker.position_signatures}")
            
            if hasattr(self, 'position') and self.position:
                position_str = str(self.position)
                print(f"Looking for signatures at position: {position_str}")
                
                position_sigs = self.checker.position_signatures.get(position_str, {})
                print(f"Found position signatures: {position_sigs}")
                
                if position_sigs and 'signatures' in position_sigs:
                    print(f"Setting signatures from position_sigs: {position_sigs['signatures']}")
                    self.signatures = position_sigs['signatures']
                else:
                    print("No signatures found for this position")
                    self.signatures = []
            
            if not hasattr(self, 'position') or not self.position:
                print(f"Setting position to current_position: {self.checker.current_position}")
                self.position = self.checker.current_position
                
            if not self.amount_due:
                print(f"Setting amount_due from cause: {self.cause.total_amount if self.cause else 0}")
                if self.cause:
                    try:
                        self.amount_due = float(self.cause.total_amount)
                        print(f"Amount due set to: {self.amount_due}")
                    except (ValueError, TypeError) as e:
                        print(f"Error converting amount_due: {e}")
                        self.amount_due = 0
                else:
                    self.amount_due = 0
                    
            # If this is a tax payment check, delete any existing tax forecast
            if self.is_tax_payment and self.tax_declaration_id and self.tax_declaration_type:
                print(f"Tax payment check detected, type: {self.tax_declaration_type}")
                print(f"Deleting any existing tax forecasts for declaration: {self.tax_declaration_id}")
                
                # Map tax declaration types to forecast source types
                forecast_type_mapping = {
                    'other_tax': {
                        'professional': 'professional_tax',
                        'communal': 'communal_tax',
                        # Add other subtypes
                        'default': 'other_tax'
                    },
                    'ir': 'ir_declaration',
                    'stamp_right': 'stamp_right_declaration',
                    'vat': 'vat_declaration'
                }
                
                source_type = None
                if self.tax_declaration_type == 'other_tax':
                    # For OtherTaxDeclaration, we need the subtype
                    try:
                        tax = OtherTaxDeclaration.objects.get(id=self.tax_declaration_id)
                        source_type = forecast_type_mapping['other_tax'].get(
                            tax.tax_type,
                            forecast_type_mapping['other_tax']['default']
                        )
                    except Exception as e:
                        print(f"Error getting tax subtype: {str(e)}")
                        source_type = forecast_type_mapping['other_tax']['default']
                else:
                    source_type = forecast_type_mapping.get(self.tax_declaration_type)

                if source_type:
                    try:
                        deleted_count = ForecastStatement.objects.filter(
                            source_type=source_type,
                            source_id=self.id,
                            is_processed=False
                        ).delete()[0]
                        print(f"Deleted {deleted_count} forecasts for tax declaration")
                    except Exception as e:
                        print(f"Error deleting tax forecasts: {str(e)}")
        
        # If this is a tax payment, sync the generic fields
        if self.is_tax_payment and self.tax_declaration_type and self.tax_declaration_id:
            if self.tax_declaration_type == 'other_tax':
                model_class = OtherTaxDeclaration
            elif self.tax_declaration_type == 'ir':
                model_class = IRDeclaration
            elif self.tax_declaration_type == 'stamp_right':
                model_class = StampRightDeclaration
            elif self.tax_declaration_type == 'vat':
                model_class = VATDeclaration
            
            # Set content_type and object_id
            self.content_type = ContentType.objects.get_for_model(model_class)
            self.object_id = self.tax_declaration_id
        
        print(f"Final signatures before save: {getattr(self, 'signatures', [])}")
        super().save(*args, **kwargs)
        print(f"Check saved with signatures: {self.signatures}")
        
        # Update status if printed and has all signatures
        if self.status == 'printed' and len(self.signatures) == 2:
            self.status = 'pending'
            super().save(update_fields=['status'])
            
        # Update checker current_position if new check
        if not self.pk and int(self.position) == self.checker.current_position:
            print("Updating checker current_position")
            self.checker.current_position = int(self.position) + 1
            self.checker.save()


        # Regular payment forecast handling
        if self.payment_due and not self.is_tax_payment:  # Added condition to skip tax payments
            print(f"[Check Save] Initial payment_due: {self.payment_due} (type: {type(self.payment_due)})")
            
            # Ensure payment_due is a date object
            if isinstance(self.payment_due, str):
                try:
                    self.payment_due = datetime.datetime.strptime(self.payment_due, '%Y-%m-%d').date()
                    print(f"[Check Save] Converted payment_due to date: {self.payment_due}")
                except ValueError as e:
                    print(f"[Check Save] Error converting payment_due date: {e}")
                    return

            # Delete existing forecast if any
            ForecastStatement.objects.filter(
                source_type='supplier_check',
                source_id=self.id,
                is_processed=False
            ).delete()

            # Create new forecast if status allows
            if self.status not in ['cancelled', 'paid', 'unpaid']:
                # Calculate forecast date
                forecast_date = self.payment_due
                
                # Add supplier delay based on checker type
                delay = self.beneficiary.delay_lcn if self.checker.type == 'LCN' else self.beneficiary.delay_check
                print(f"[Check Save] Using delay of {delay} days based on checker type {self.checker.type}")
                
                current_date = forecast_date
                print(f"[Check Save] Starting date calculation from: {current_date} (type: {type(current_date)})")
                
                try:
                    while delay > 0 or current_date.weekday() >= 5:
                        current_date += timedelta(days=1)
                        print(f"[Check Save] Checking date: {current_date} (weekday: {current_date.weekday()})")
                        if current_date.weekday() < 5:  # Only count business days
                            delay -= 1
                            print(f"[Check Save] Business day found, remaining delay: {delay}")
                            
                    print(f"[Check Save] Final forecast date: {current_date}")
                    
                    # Create forecast
                    ForecastStatement.objects.create(
                        bank_account=self.checker.bank_account,
                        date=current_date,
                        label=f"Expected payment to {self.beneficiary.name}",
                        debit=self.amount,
                        amount=self.amount,
                        reference=f"Payment #{self.position}",
                        source_type='supplier_check',
                        source_id=self.id
                    )
                    print(f"[Check Save] Forecast created successfully")
                    
                except Exception as e:
                    print(f"[Check Save] Error during forecast creation: {str(e)}")
                    pass
            
        if self.payment_due and self.is_tax_payment and self.tax_declaration_id and self.tax_declaration_type and self.status != 'cancelled':
            print(f"\n[Check Save] Tax payment forecast handling START")
            print(f"[Check Save] Check ID: {self.pk}")
            print(f"[Check Save] Status: {self.status}")
            print(f"[Check Save] Payment due: {self.payment_due}")
            print(f"[Check Save] Is tax payment: {self.is_tax_payment}")
            print(f"[Check Save] Tax declaration ID: {self.tax_declaration_id}")
            print(f"[Check Save] Tax declaration type: {self.tax_declaration_type}")
            
            # Get the tax declaration
            tax_declaration = None
            source_type = None
            
            # Map tax declaration types to forecast source types
            forecast_type_mapping = {
                'other_tax': {
                    'professional': 'professional_tax',
                    'communal': 'communal_tax',
                    'default': 'other_tax'
                },
                'ir': 'ir_declaration',
                'stamp_right': 'stamp_right_declaration',
                'vat': 'vat_declaration'
            }
            
            # Get the declaration and its source type
            if self.tax_declaration_type == 'other_tax':
                try:
                    tax_declaration = OtherTaxDeclaration.objects.get(id=self.tax_declaration_id)
                    tax_type = tax_declaration.tax_type
                    print(f"[Check Save] Found tax record, type: {tax_type}")
                    
                    source_type = forecast_type_mapping['other_tax'].get(
                        tax_type,
                        forecast_type_mapping['other_tax']['default']
                    )
                    print(f"[Check Save] Mapped to source_type: {source_type}")
                except Exception as e:
                    print(f"[Check Save] Error getting tax declaration: {str(e)}")
                    return
            else:
                source_type = forecast_type_mapping.get(self.tax_declaration_type)
            
            # Process check based on status
            if self.status == 'paid':
                # For paid checks, add payment to declaration but don't delete forecast
                # (just update its amount to reflect remaining)
                print(f"[Check Save] Processing paid check for tax declaration")
                
                if self.tax_declaration_type == 'other_tax' and tax_declaration:
                    # Get previous paid amount before processing payment
                    old_paid_amount = tax_declaration.paid_amount
                    
                    # Process payment
                    tax_declaration.calculate_payment_status()
                    
                    # If declaration is now fully paid, mark forecasts as processed
                    if tax_declaration.status == 'paid':
                        print(f"[Check Save] Declaration fully paid, marking forecasts as processed")
                        processed_count = ForecastStatement.objects.filter(
                            source_type=source_type,
                            source_id=self.tax_declaration_id,
                            is_processed=False
                        ).update(is_processed=True)
                        print(f"[Check Save] Marked {processed_count} forecasts as processed")
                    else:
                        # Otherwise, update forecasts to show remaining amount
                        remaining_amount = tax_declaration.amount - tax_declaration.paid_amount
                        print(f"[Check Save] Declaration partially paid, updating forecast to {remaining_amount}")
                        
                        # Update instead of recreate
                        updated = ForecastStatement.objects.filter(
                            source_type=source_type,
                            source_id=self.tax_declaration_id,
                            is_processed=False
                        ).update(
                            debit=remaining_amount,
                            amount=remaining_amount
                        )
                        print(f"[Check Save] Updated {updated} forecasts with remaining amount")
                
                print(f"[Check Save] Tax payment forecast handling END\n")
                return
                
        print("=== Check Save Method Completed ===\n")

    def clean(self):
                
        # Ensure no duplicate positions
        if self.objects.filter(checker=self.checker, position=self.position).exists():
            raise ValidationError("This position is already used.")
        
        # Ensure the position is within the valid range
        if int(self.position[len(self.checker.index):]) < self.checker.starting_page or \
           int(self.position[len(self.checker.index):]) > self.checker.final_page:
            raise ValidationError(
                f"Position must be between {self.checker.starting_page} and {self.checker.final_page}."
            )

        # Check payment type validation
        payment_types = sum([
            not self.is_supplier_payment and not self.is_tax_payment and bool(self.cause),
            bool(self.is_supplier_payment),
            bool(self.is_tax_payment)
        ])
        
        if payment_types > 1:
            raise ValidationError(_("Check can only be one payment type: invoice, supplier, or tax"))
        
        if payment_types == 0:
            raise ValidationError(_("Check must be either an invoice, supplier, or tax payment"))
        
        # Tax payment validation
        if self.is_tax_payment:
            if not self.tax_declaration_type or not self.tax_declaration_id:
                raise ValidationError(_("Tax declaration type and ID are required for tax payments"))
            if self.cause:
                raise ValidationError(_("Tax payments cannot specify a direct cause"))
        
        # Invoice payment validation
        if not self.is_supplier_payment and not self.is_tax_payment and not self.cause:
            raise ValidationError(_("Invoice is required for direct invoice payments"))
            
        if self.is_supplier_payment and self.cause:
            raise ValidationError(_("Supplier payments cannot specify a direct cause"))
            
        if self.cause and self.cause.supplier != self.beneficiary:
            raise ValidationError(_("Invoice supplier must match check beneficiary"))
            
        # Validate amount for invoice payments
        if not self.is_supplier_payment and not self.is_tax_payment and self.cause:
            if self.amount > self.cause.amount_available_for_payment:
                raise ValidationError(_("Amount exceeds invoice's available amount"))
            
        if self.paid_at and not self.delivered_at:
            raise ValidationError(_("Check cannot be marked as paid before delivery"))

        # Validate supplier payment allocation before printing
        if self.status == 'printed' and self.is_supplier_payment:
            if self.get_available_amount() > 0:
                raise ValidationError(_("Supplier payment must be fully allocated before printing"))
            
        # Only allow edits to specific fields after draft status
        if self.pk and self.status not in ['draft', 'pending']:
            original = Check.objects.get(pk=self.pk)
            changed_fields = []
            for field in ['beneficiary', 'cause', 'amount', 'position', 'checker']:
                if getattr(self, field) != getattr(original, field):
                    changed_fields.append(field)
            
            if changed_fields:
                raise ValidationError(_(f"Cannot modify {', '.join(changed_fields)} after check is printed"))        
        super().clean()

    class Meta:
        ordering = ['-creation_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    is_supplier_payment=True
                ) | models.Q(
                    amount__lte=models.F('amount_due')
                ),
                name='check_amount_cannot_exceed_due'
            )
        ]
    
    @property
    def has_replacement(self):
        return hasattr(self, 'replaced_by') and self.replaced_by.exists()

    def reject(self, reason, note=''):
        self.status = 'rejected'
        self.rejection_reason = reason
        self.rejection_note = note
        self.rejection_date = timezone.now()
        self.save()

    def replace_with(self, new_check):
        new_check.replaces = self
        new_check.save()

    @property
    def is_received(self):
        """Check if we have physical possession of the check"""
        return bool(self.received_at)

    @property
    def can_be_replaced(self):
        """Can only replace rejected checks that we physically have"""
        return (
            self.status == 'rejected' and 
            self.is_received and 
            not self.has_replacement
        )

    def receive(self, notes=''):
        """Mark check as physically received"""
        if self.status not in ['delivered', 'rejected']:
            raise ValidationError(_("Only delivered or rejected checks can be received"))
        
        self.received_at = timezone.now()
        self.received_notes = notes
        self.save()

    def create_replacement(self, checker, **kwargs):
        """
        Create a replacement check after validating state
        
        Args:
            checker (Checker): The checker to use for the new check
        """
        if not self.can_be_replaced:
            raise ValidationError(
                _("Cannot replace: Check must be rejected and received, with no existing replacement")
            )

        if not checker.is_active or checker.status == 'completed':
            raise ValidationError(_("Selected checker is not available for new checks"))

        # Create new check with same base properties but new checker and details
        replacement = Check.objects.create(
            checker=checker,  # Use the provided checker
            beneficiary=self.beneficiary,
            cause=self.cause,
            amount_due=self.amount_due,
            replaces=self,
        )
        return replacement

    @property
    def signature_status(self):
        sig_count = len(self.signatures)
        if sig_count == 0:
            return 'unsigned'
        elif sig_count == 1:
            return 'mono-signed'
        return 'double-signed'

    def can_be_signed(self, signature):
        return (
            signature in dict(self.SIGNATURE_CHOICES) and
            signature not in self.signatures and
            len(self.signatures) < 2
        )

    def add_signature(self, signature):
        if self.can_be_signed(signature):
            self.signatures.append(signature)
            if len(self.signatures) == 2:
                self.status = 'pending'
            elif self.status == 'printed':
                self.status = 'ready_to_sign'
            self.save()


def get_upload_path(instance, filename):
    # Get current year
    year = timezone.now().year
    # Get model type (delivery/reception)
    model_type = instance.__class__.__name__.lower()
    # Clean filename
    ext = filename.split('.')[-1]
    new_name = f"{model_type}_{uuid.uuid4().hex[:8]}.{ext}"
    # Important: Files must be saved under media directory
    return f"documents/{model_type}/{year}/{new_name}"

def get_receipt_upload_path(instance, filename):
    """Get upload path for receipt documents"""
    print(f"\n=== Getting upload path for {instance.__class__.__name__} document ===")
    # Get current year 
    year = timezone.now().year
    receipt_type = instance.__class__.__name__.lower()

    # Clean filename
    ext = filename.split('.')[-1]
    new_name = f"{receipt_type}_{uuid.uuid4().hex[:8]}.{ext}"
    
    path = f"receipts/{receipt_type}/{year}/{new_name}"
    print(f"Generated path: {path}")
    return path

def validate_file_size(value):
    """
    Validate file size (5MB limit)
    """
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError(_("The maximum file size that can be uploaded is 5MB"))



class Receipt(BaseModel):
    """Base class for all receipt types."""
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    entity = models.ForeignKey('Entity', on_delete=models.PROTECT)
    operation_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    client_year = models.IntegerField()
    client_month = models.IntegerField()
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    vat_declared = models.BooleanField(default=False)
    vat_declaration_period = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                r'^\d{2}-\d{4}$',
                'Period must be in MM-YYYY format'
            )
        ]
    )
    document = models.FileField(
        upload_to=get_receipt_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        print(f"\n=== Saving {self.__class__.__name__} ===")
        if self.document:
            print(f"Document: {self.document.name}")
        if not self.client_year:
            self.client_year = timezone.now().year
        if not self.client_month:
            self.client_month = timezone.now().month
        super().save(*args, **kwargs)


class CashReceipt(Receipt):
    """Cash receipt implementation."""
    reference_number = models.CharField(max_length=50, blank=True)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='cash_receipts'
    )

    def get_compensated_receipt(self):
        """Returns receipts this cash is compensating"""
        return CompensationRecord.objects.filter(
            compensator_content_type=ContentType.objects.get_for_model(self),
            compensator_id=self.id,
            is_active=True
        )

    def get_compensation_description(self):
        """Returns description if this receipt compensates another"""
        compensated = self.get_compensated_receipt()
        if compensated:
            return f"Compensating unpaid {compensated.__class__.__name__.replace('Receipt', '')} #{compensated.get_receipt_number()}"
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def can_delete(self):
        """Check if receipt can be deleted"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def __str__(self):
        return f"Cash Receipt {self.reference_number or 'N/A'}"

    class Meta:
        verbose_name = "Cash Receipt"
        verbose_name_plural = "Cash Receipts"

    def get_receipt_number(self):
        """Returns reference number for consistency with other receipts"""
        return self.reference_number or 'N/A'

class TransferReceipt(Receipt):
    """Bank transfer implementation."""
    transfer_reference = models.CharField(max_length=100)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='transfer_receipts'
    )
    transfer_date = models.DateField(default=timezone.now)

    def get_compensated_receipt(self):
        """Returns receipts this transfer is compensating"""
        return CompensationRecord.objects.filter(
            compensator_content_type=ContentType.objects.get_for_model(self),
            compensator_id=self.id,
            is_active=True
        )

    def get_compensation_description(self):
        """Returns description if this receipt compensates another"""
        compensated = self.get_compensated_receipt()
        if compensated:
            return f"Compensating unpaid {compensated.__class__.__name__.replace('Receipt', '')} #{compensated.get_receipt_number()}"
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def can_delete(self):
        """Check if receipt can be deleted"""
        compensated_receipt = self.get_compensated_receipt()
        return compensated_receipt is None

    def __str__(self):
        return f"Transfer {self.transfer_reference}"

    class Meta:
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"

    def get_receipt_number(self):
        """Returns transfer reference for consistency with other receipts"""
        return self.transfer_reference