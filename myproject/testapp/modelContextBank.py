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

class Supplier(BaseModel):

    numeric_validator = RegexValidator(r'^[0-9]*$', _('Only numeric characters are allowed.'))
    alphanumeric_validator = RegexValidator(r'^[a-zA-Z0-9 ]*$', _('Only alphanumeric characters are allowed.'))
    phone_validator = RegexValidator(r'^\+?[0-9]{8,15}$', _('Enter a valid phone number.'))
    email_validator = RegexValidator(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', _('Enter a valid email address.'))

    name = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    if_code = models.CharField(max_length=25, unique=True, validators=[numeric_validator])
    ice_code = models.CharField(max_length=15, unique=True, validators=[numeric_validator])  # Exactly 15 characters
    rc_code = models.CharField(max_length=25, validators=[numeric_validator])
    rc_center = models.CharField(max_length=100, validators=[alphanumeric_validator])
    accounting_code = models.CharField(max_length=25, unique=True, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    
    # Contact information
    email_primary = models.EmailField(max_length=100, blank=True, null=True, validators=[email_validator])
    email_secondary = models.EmailField(max_length=100, blank=True, null=True, validators=[email_validator])
    phone_primary = models.CharField(max_length=20, blank=True, null=True, validators=[phone_validator])
    phone_secondary = models.CharField(max_length=20, blank=True, null=True, validators=[phone_validator])
    
    is_energy = models.BooleanField(default=False)
    service = models.CharField(max_length=255, blank=True, validators=[alphanumeric_validator])  # Description of merch/service sold
    delay_convention = models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)
    is_regulated = models.BooleanField(default=False)
    
    # Document fields
    regulation_file = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True, 
        blank=True,
        help_text=_("Upload supplier regulation file")
    )
    payment_delay_file = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True, 
        blank=True,
        help_text=_("Upload payment delay agreement file")
    )
    
    delay_check = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Number of days to delay check payment forecasts after due date")
    )
    delay_lcn = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Number of days to delay LCN payment forecasts after due date")
    )

    def clean(self):
        super().clean()
        # Ensure IF code is numeric
        if not self.if_code.isdigit():
            raise ValidationError(_("IF code must be numeric."))
        # Ensure ICE code has exactly 15 characters
        if len(self.ice_code) != 15:
            raise ValidationError(_("ICE code must contain exactly 15 characters."))
    
    class Meta:
        constraints = [
        ]

    def __str__(self):
        return self.name

# models.py
def get_supplier_balance(supplier):
    """Calculate supplier balance including only PAID payments"""
    invoices = Invoice.objects.filter(
        supplier=supplier,
        type='invoice'
    )
    
    invoice_total = sum(invoice.net_amount for invoice in invoices)
    
    # Get all PAID check payments (both direct and allocated)
    check_total = Decimal('0.00')
    
    # Direct invoice payments - only PAID checks
    direct_payments = Check.objects.filter(
        beneficiary=supplier,
        is_supplier_payment=False,
        status='paid'  # Only count paid checks
    ).exclude(status='cancelled')
    check_total += sum(check.amount for check in direct_payments)
    
    # Allocated payments - only from PAID checks
    allocated_payments = CheckAllocation.objects.filter(
        payment__beneficiary=supplier,
        payment__is_supplier_payment=True,
        payment__status='paid'  # Only count allocations from paid checks
    )
    check_total += sum(alloc.amount for alloc in allocated_payments)
    
    return {
        'payable': invoice_total,  # What we owe supplier
        'paid': check_total,       # What we've actually paid
        'balance': invoice_total - check_total,  # Remaining to pay
        'invoices_count': Invoice.objects.filter(
            supplier=supplier,
            type='invoice',
            payment_status__in=['not_paid', 'partially_paid']
        ).count()
    }

def get_supplier_unpaid_invoices(supplier):
    """Get all invoices that still have amount available for payment"""
    invoices = Invoice.objects.filter(
        supplier=supplier,
        type='invoice'
    ).exclude(
        status='cancelled'
    )
    
    # Filter out invoices with no available amount
    return [inv for inv in invoices if inv.amount_available_for_payment > 0]

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
    document = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True,
        blank=True,
        help_text="Upload check document"
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

class BankStatement(models.Model):
    """
    Virtual model that dynamically generates bank statement entries.
    Does not store records directly - serves as a view model.
    """
    class Meta:
        managed = False

    def calculate_previous_balance(bank_account, start_date):
        # Start with Jan 1st of current year if start_date is in current year
        # Or Jan 1st of previous year if start_date is in previous year
        year_start = datetime.date(start_date.year, 1, 1)
        
        # Get all entries from year start until start_date
        # (using same logic we use for normal entries but with date range)
        entries = []  # get all entries between year_start and start_date
        
        # Calculate running balance
        balance = Decimal('0.00')  # Assume previous year ended at 0
        for entry in entries:
            balance += (entry.get('credit') or 0) - (entry.get('debit') or 0)
            
        return balance
    
    @classmethod
    def categorize_transaction(cls, entry_type, data=None):
        """
        Determine the main_type and sub_type for a transaction based on its properties.
        
        Args:
            entry_type (str): The original entry type
            data (dict): Additional data about the transaction to help with categorization
        
        Returns:
            tuple: (main_type, sub_type)
        """
        # Default values
        main_type = "OPERATIONAL"
        sub_type = "OTHER"
        
        # Check/Supplier payments
        if entry_type == 'SUPPLIER_PAYMENT':
            check = data.get('payment')
            
            # Tax payments take precedence
            if check and check.is_tax_payment:
                main_type = "TAX"
                if check.tax_declaration_type == 'vat':
                    sub_type = "VAT"
                elif check.tax_declaration_type == 'ir':
                    sub_type = "IR"
                elif check.tax_declaration_type == 'stamp_right':
                    sub_type = "STAMP"
                elif check.tax_declaration_type == 'other_tax':
                    sub_type = "OTHER_TAX"
                else:
                    sub_type = "GENERAL"
            
            # Direct invoice payments or allocated payments
            elif check:
                invoice = check.cause
                if invoice:
                    # Use invoice type if available
                    main_type = "EXPENSE" 
                    sub_type = invoice.type if hasattr(invoice, 'type') else "GENERAL"
                    
                    # Special handling for specific invoice types
                    if hasattr(invoice, 'type'):
                        if invoice.type in ["ENERGY", "UTILITIES"]:
                            main_type = "UTILITY"
                        elif invoice.type == "INSURANCE":
                            main_type = "INSURANCE"
                        elif invoice.type == "LEASING":
                            main_type = "LEASING"
                        elif invoice.type == "TELECOM":
                            main_type = "TELECOM"
                        elif invoice.type == "RENT":
                            main_type = "PROPERTY"
                        elif invoice.type == "SERVICE":
                            main_type = "SERVICE"
                        elif invoice.type == "LOAN":
                            main_type = "FINANCIAL"
                        elif invoice.type in ["SOCIAL", "RETIREMENT"]:
                            main_type = "SOCIAL_SECURITY"
                
                # Check supplier properties if no invoice or couldn't categorize by invoice
                if (not invoice or main_type == "EXPENSE") and check.beneficiary:
                    supplier = check.beneficiary
                    if supplier.is_energy:
                        main_type = "UTILITY"
                        sub_type = "ENERGY"
        
        # Direct Debit payments
        elif entry_type == 'DIRECT_DEBIT':
            direct_debit = data.get('direct_debit')
            if direct_debit and direct_debit.invoice and direct_debit.invoice.invoice:
                invoice = direct_debit.invoice.invoice
                # Similar logic as above, based on invoice type
                if hasattr(invoice, 'type'):
                    if invoice.type in ["ENERGY", "UTILITIES"]:
                        main_type = "UTILITY"
                        sub_type = invoice.type
                    elif invoice.type == "INSURANCE":
                        main_type = "INSURANCE"
                        sub_type = "GENERAL"
                    elif invoice.type == "LEASING":
                        main_type = "LEASING"
                        sub_type = "GENERAL"
                    elif invoice.type == "TELECOM":
                        main_type = "TELECOM"
                        sub_type = "GENERAL"
                    elif invoice.type == "RENT":
                        main_type = "PROPERTY"
                        sub_type = "RENT"
                    elif invoice.type == "SERVICE":
                        main_type = "SERVICE"
                        sub_type = "GENERAL"
                    elif invoice.type == "LOAN":
                        main_type = "FINANCIAL"
                        sub_type = "LOAN"
                    elif invoice.type in ["SOCIAL", "RETIREMENT"]:
                        main_type = "SOCIAL_SECURITY"
                        sub_type = invoice.type
                    else:
                        main_type = "EXPENSE"
                        sub_type = invoice.type
        
        # Tax payments
        elif entry_type in ['VAT_PAYMENT', 'IR_PAYMENT', 'STAMP_PAYMENT']:
            main_type = "TAX"
            if entry_type == 'VAT_PAYMENT':
                sub_type = "VAT"
            elif entry_type == 'IR_PAYMENT':
                sub_type = "IR"
            else:
                sub_type = "STAMP"
        
        # Client receipts/income
        elif entry_type in ['CASH', 'TRANSFER']:
            main_type = "CLIENT"
            sub_type = "PAYMENT"
        elif entry_type in ['CHECK_COLLECTION', 'LCN_COLLECTION']:
            main_type = "CLIENT"
            sub_type = entry_type.split('_')[0]  # CHECK or LCN
        elif entry_type in ['CHECK_DISCOUNT', 'LCN_DISCOUNT']:
            main_type = "FINANCIAL"
            sub_type = "DISCOUNT"
        elif entry_type in ['CHECK_REVERSAL', 'LCN_REVERSAL']:
            main_type = "FINANCIAL"
            sub_type = "REVERSAL"
        
        # Bank fees
        elif entry_type == 'BANK_FEE':
            main_type = "FEE"
            sub_type = "BANK"
        
        # Interbank transfers
        elif entry_type in ['INTERBANK_TRANSFER_IN', 'INTERBANK_TRANSFER_OUT']:
            main_type = "INTERNAL"
            sub_type = "TRANSFER"
        
        # Balance entries
        elif entry_type == 'BALANCE':
            main_type = "BALANCE"
            sub_type = "OPENING"
        
        # Payroll
        elif entry_type == 'PAY_DECLARATION':
            main_type = "PAYROLL"
            sub_type = "SALARY"
            
        # Cash operations
        elif entry_type == 'CASH_WITHDRAWAL':
            main_type = "CASH"
            sub_type = "WITHDRAWAL"
        elif entry_type == 'CASH_DEPOSIT':
            main_type = "CASH"
            sub_type = "DEPOSIT"
        elif entry_type == 'CASH_EXPENSE':
            main_type = "EXPENSE"
            sub_type = "CASH"
        elif entry_type == 'CASH_PAYMENT':
            main_type = "EXPENSE"
            sub_type = "CASH"
            
        # Custom records
        elif entry_type == 'MANUAL':
            # Could potentially enhance with analysis of label or account_code
            main_type = "MANUAL"
            sub_type = "CUSTOM"
            
        # Other tax types
        elif entry_type in ['PROFESSIONAL_TAX', 'COMMUNAL_TAX', 'OTHER_TAX']:
            main_type = "TAX"
            sub_type = entry_type
        
        print(f"Categorized {entry_type} as {main_type}/{sub_type}")
        return main_type, sub_type
    
    @classmethod
    def get_statement(cls, bank_account, start_date=None, end_date=None, include_forecasts=False):
        """
        Dynamically generates statement entries for a bank account.
        """
        entries = []

        # Convert string dates to datetime.date objects
        if start_date and isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date and isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        cash_withdrawals = CashDeposit.objects.filter(
            source_type='bank',
            source_bank_account=bank_account
        )

        for deposit in cash_withdrawals:
            entries.append({
                'date': deposit.date,
                'label': f"Cash withdrawal - {deposit.reference}",
                'type': 'CASH_WITHDRAWAL',
                'debit': deposit.amount,
                'credit': None,
                'reference': deposit.reference,
                'source_type': 'cash_deposit',
                'source_id': deposit.id,
                'can_transfer': False,
                'is_transferred': False,
            })
            print(f"Added cash withdrawal to bank statement: {deposit.amount}")
        
        # Get cash receipts
        cash_receipts = CashReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        for receipt in cash_receipts:
            # For rejected receipts
            if hasattr(receipt, 'rejection_cause'):
                rejection_info = {
                    'rejection_cause': receipt.rejection_cause,
                    'rejection_cause_display': receipt.get_rejection_cause_display()
                }
            else:
                rejection_info = {
                    'rejection_cause': None,
                    'rejection_cause_display': None
                }
            
            entries.append({
                'date': receipt.operation_date,
                'label': f"Cash payment from {receipt.entity.name}",
                'type': 'CASH',
                'debit': None,
                'credit': receipt.amount,
                'reference': receipt.reference_number or 'N/A',
                'source_type': 'cash_receipt',
                'source_id': receipt.id,
                'can_transfer': True,
                'is_transferred': False,
                'entity': {
                    'name': receipt.entity.name,
                    'ice_code': receipt.entity.ice_code
                },
                'client': {
                    'name': receipt.client.name,
                    'client_code': receipt.client.client_code
                },
                'operation_date': receipt.operation_date,
                **rejection_info  # Spread rejection info safely
            })
        
        # Get transfer receipts
        transfer_receipts = TransferReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        for receipt in transfer_receipts:
            entries.append({
                'date': receipt.operation_date,
                'label': f"Bank transfer from {receipt.entity.name}",
                'type': 'TRANSFER',
                'debit': None,
                'credit': receipt.amount,
                'reference': receipt.transfer_reference,
                'source_type': 'transfer_receipt',
                'source_id': receipt.id,
                'can_transfer': True,
                'is_transferred': False,
                'entity': {
                    'name': receipt.entity.name,
                    'ice_code': receipt.entity.ice_code
                },
                'client': {
                    'name': receipt.client.name,
                    'client_code': receipt.client.client_code
                },
                'operation_date': receipt.operation_date,
                'transfer_date': receipt.transfer_date
            })

        # Get presentations
        presentations = Presentation.objects.filter(
            bank_account=bank_account
        ).prefetch_related(
            'presentation_receipts__checkreceipt',
            'presentation_receipts__lcn'
        )

        for pres in presentations:
            for pr in pres.presentation_receipts.all():
                receipt = pr.checkreceipt or pr.lcn
                receipt_type = 'check' if pr.checkreceipt else 'lcn'
                
                # For collection presentations - only record if marked as PAID
                if pres.presentation_type == 'COLLECTION':
                    if pr.recorded_status == 'PAID':
                        print(f"\n=== Processing paid collection receipt {receipt.get_receipt_number()} ===")
                        print(f"Presentation date: {pres.date}")
                        
                        # Get payment date from history
                        payment_history = ReceiptHistory.objects.filter(
                            content_type=ContentType.objects.get_for_model(receipt.__class__),
                            object_id=receipt.id,
                            action='status_changed',
                            new_value__status='PAID'
                        ).order_by('-business_date').first()
                        
                        print(f"Found history record: {payment_history is not None}")
                        if payment_history:
                            print(f"History timestamp: {payment_history.timestamp}")
                            print(f"History business_date: {payment_history.business_date}")
                        
                        # First try to get date from history, fall back to presentation date if not found
                        entry_date = (payment_history.business_date.date() 
                            if payment_history and payment_history.business_date 
                            else pres.date)
                        
                        print(f"Final entry_date being used: {entry_date}")
                        print("=== End processing paid collection receipt ===\n")
                        
                        entries.append({
                            'date': entry_date,
                            'label': f"Payment of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}",
                            'type': f'{receipt_type.upper()}_COLLECTION',
                            'debit': None,
                            'credit': receipt.amount,
                            'reference': pres.bank_reference or f"Pres. #{pres.id}",
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'can_transfer': True,
                            'is_transferred': False,
                            'entity': {
                                'name': receipt.entity.name,
                                'ice_code': receipt.entity.ice_code
                            },
                            'client': {
                                'name': receipt.client.name,
                                'client_code': receipt.client.client_code
                            },
                            'due_date': receipt.due_date,
                            'issuing_bank_display': receipt.get_issuing_bank_display(),
                            'presentation_reference': pres.bank_reference,
                            'status': receipt.status if hasattr(receipt, 'status') else None,
                            'rejection_cause': getattr(receipt, 'rejection_cause', None),
                            'rejection_cause_display': receipt.get_rejection_cause_display() if hasattr(receipt, 'get_rejection_cause_display') else None
                        })
                
                # For discount presentations
                elif pres.presentation_type == 'DISCOUNT':
                    # Record initial discount
                    discount_entry = {
                        'date': pres.date,
                        'label': f"Discount of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}",
                        'type': f'{receipt_type.upper()}_DISCOUNT',
                        'debit': None,
                        'credit': receipt.amount,
                        'reference': pres.bank_reference or f"Pres. #{pres.id}",
                        'source_type': 'presentation_receipt',
                        'source_id': pr.id,
                        'can_transfer': True,
                        'is_transferred': False,
                        'entity': {
                            'name': receipt.entity.name,
                            'ice_code': receipt.entity.ice_code
                        },
                        'client': {
                            'name': receipt.client.name,
                            'client_code': receipt.client.client_code
                        },
                        'due_date': receipt.due_date,
                        'issuing_bank_display': receipt.get_issuing_bank_display(),
                        'presentation_reference': pres.bank_reference,
                        'status': receipt.status if hasattr(receipt, 'status') else None,
                        'rejection_cause': getattr(receipt, 'rejection_cause', None),
                        'rejection_cause_display': receipt.get_rejection_cause_display() if hasattr(receipt, 'get_rejection_cause_display') else None
                    }
                    entries.append(discount_entry)

                    # If marked as UNPAID in this presentation
                    if pr.recorded_status == 'UNPAID':
                        # Get unpaid date from history
                        unpaid_history = ReceiptHistory.objects.filter(
                            content_type=ContentType.objects.get_for_model(receipt.__class__),
                            object_id=receipt.id,
                            action='status_changed',
                            new_value__status='UNPAID'
                        ).order_by('timestamp').first()
                        print("Unpaid history:", unpaid_history)
                        print("pres date:", pres.date)
                        unpaid_date = None
                        if unpaid_history:
                            # Convert both to date, ensuring they are always pure dates
                            unpaid_date = (unpaid_history.business_date.date() if unpaid_history.business_date 
                                        else unpaid_history.timestamp.date())
                        else:
                            unpaid_date = pres.date
                        print("Unpaid date:", unpaid_date)
                        print("Type of pres.date:", type(pres.date))
                        print("Type of unpaid_date:", type(unpaid_date))
                    
                        reversal_entry = {
                            'date': unpaid_date,  # Use unpaid date if available
                            'label': (f"Reversal of {receipt_type} "
                                    f"#{receipt.get_receipt_number()} - {receipt.entity.name}"),
                            'type': f'{receipt_type.upper()}_REVERSAL',
                            'debit': receipt.amount,
                            'credit': None,
                            'reference': pres.bank_reference or f"Pres. #{pres.id}",
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,  # Keep original ID
                            'display_id': f"{pr.id}-reversal",  # Add new field for frontend 
                            'can_transfer': False,
                            'is_transferred': False,
                            'discount_reference': discount_entry['reference'],  # Link to original discount
                            'entity': {
                                'name': receipt.entity.name,
                                'ice_code': receipt.entity.ice_code
                            },
                            'client': {
                                'name': receipt.client.name,
                                'client_code': receipt.client.client_code
                            },
                            'issuing_bank_display': receipt.get_issuing_bank_display(),
                            'due_date': receipt.due_date,
                            'status': receipt.status,
                            'rejection_cause': receipt.rejection_cause,
                            'rejection_cause_display': receipt.get_rejection_cause_display() if hasattr(receipt, 'get_rejection_cause_display') else None
                        }
                        entries.append(reversal_entry)

        # Add outgoing transfers
        outgoing_transfers = InterBankTransfer.objects.filter(
            from_bank=bank_account,
            is_deleted=False
        )
        
        for transfer in outgoing_transfers:
            entries.append({
                'date': transfer.date,
                'label': transfer.label,
                'type': 'INTERBANK_TRANSFER_OUT',
                'debit': transfer.total_amount,
                'credit': None,
                'reference': f'Transfer #{transfer.id}',
                'source_type': 'interbank_transfer',
                'source_id': transfer.id,
                'can_delete': True,
                'can_transfer': False,
                'is_transferred': False,
                'from_bank': transfer.from_bank,
                'to_bank': transfer.to_bank
            })
            
        # Add incoming transfer records
        incoming_transfers = InterBankTransfer.objects.filter(
            to_bank=bank_account,
            is_deleted=False
        ).prefetch_related('transferred_records')
        
        for transfer in incoming_transfers:
            for record in transfer.transferred_records.all():
                entries.append({
                    'date': transfer.date,
                    'label': f"{transfer.label} - {record.original_label}",
                    'type': 'INTERBANK_TRANSFER_IN',
                    'debit': None,
                    'credit': record.amount,
                    'reference': record.original_reference,
                    'source_type': 'transferred_record',
                    'source_id': record.id,
                    'can_delete': False,
                    'can_transfer': True,
                    'is_transferred': False,
                    'from_bank': transfer.from_bank,
                    'to_bank': transfer.to_bank
                })

        # Check for transferred status
        transferred_records = TransferredRecord.objects.filter(
            source_type__in=[entry['source_type'] for entry in entries],
            source_id__in=[entry['source_id'] for entry in entries]
        ).values_list('source_type', 'source_id')
        
        transferred_set = {(t, i) for t, i in transferred_records}
        
        # Mark transferred entries
        for entry in entries:
            if (entry['source_type'], entry['source_id']) in transferred_set:
                entry['is_transferred'] = True
                entry['can_transfer'] = False

         # Add bank fee transactions
        fee_transactions = BankFeeTransaction.objects.filter(
            bank_account=bank_account
        ).select_related('fee_type', 'related_presentation')

        for fee in fee_transactions:
            entries.append({
                'date': fee.date,
                'label': (f"{fee.fee_type.name}"
                        f"{' - Pres. ' + fee.related_presentation.bank_reference if fee.related_presentation else ''}"),
                'type': 'BANK_FEE',
                'debit': fee.total_amount,
                'credit': None,
                'reference': fee.fee_type.code,
                'source_type': 'bank_fee',
                'source_id': fee.id,
                'can_delete': True,
                'can_transfer': False,
                'is_transferred': False,
                'is_expandable': True,
                'details': {
                    'fee_type': fee.fee_type.name,
                    'raw_amount': fee.raw_amount,
                    'vat_rate': fee.vat_rate,
                    'vat_included': fee.vat_included,
                    'vat_amount': fee.vat_amount,
                    'total_amount': fee.total_amount,
                    'related_presentation': fee.related_presentation.bank_reference if fee.related_presentation else None
                }
        })

        custom_records = CustomBankRecord.objects.filter(
            bank_account=bank_account
        )
        
        if start_date:
            custom_records = custom_records.filter(date__gte=start_date)
        if end_date:
            custom_records = custom_records.filter(date__lte=end_date)
            
        for record in custom_records:
            entries.append({
                'date': record.date,
                'label': record.bank_label,
                'type': 'MANUAL',
                'debit': record.debit,
                'credit': record.credit,
                'reference': record.reference,
                'source_type': 'custom_record',
                'source_id': record.id,
                'can_delete': True,
                'can_transfer': False,
                'is_transferred': False,
                'notes': record.notes
            })

        print("\n=== Getting Supplier Payments ===")
        supplier_payments = Check.objects.filter(
            checker__bank_account=bank_account,
            status='paid'
        ).select_related('checker', 'beneficiary')
        
        print(f"Found {supplier_payments.count()} supplier payments")
        #print("Query:", supplier_payments.query)  # Print the actual SQL query
        
        for payment in supplier_payments:
            print(f"\nPayment details:")
            print(f"ID: {payment.id}")
            print(f"Position: {payment.position}")
            print(f"Status: {payment.status}")
            print(f"Amount: {payment.amount}")
            print(f"Paid at: {payment.paid_at}")
            print(f"Is supplier payment: {payment.is_supplier_payment}")
            print(f"Bank Account: {payment.checker.bank_account.id} (Expected: {bank_account.id})")
            
            entries.append({
                'date': payment.paid_at.date(),
                'label': f"Payment to {payment.beneficiary.name}",
                'type': 'SUPPLIER_PAYMENT',
                'debit': payment.amount,
                'credit': None,
                'reference': f"{payment.checker.type} {payment.checker.index}{payment.position}",
                'source_type': 'supplier_payment',
                'source_id': payment.id,
                'can_transfer': False,
                'is_transferred': False,
                # Details for collapsible
                'beneficiary': {
                    'name': payment.beneficiary.name,
                    'accounting_code': payment.beneficiary.accounting_code,
                    'ice_code': payment.beneficiary.ice_code
                },
                'payment_due': payment.payment_due,
                'status': payment.status,
                'checker_type': payment.checker.type,
                'invoice': {
                    'ref': payment.cause.ref,
                    'id': str(payment.cause.id),
                    'date': payment.cause.date,
                    'fiscal_label': payment.cause.fiscal_label,
                    'net_amount': payment.cause.net_amount
                } if payment.cause else None,
                'operation_details': {
                    'payment_date': payment.paid_at.date(),
                    'creation_date': payment.creation_date,
                    'bank_account': f"{payment.checker.bank_account.bank} - {payment.checker.bank_account.account_number}"
                },
                'is_expandable': True
            })

        print("\n=== Processing Direct Debits ===")
        direct_debits = DirectDebit.objects.filter(
            bank_account=bank_account,
            status=DirectDebit.PROCESSED
        ).select_related('contract', 'invoice__invoice', 'bank_account')
        
        print(f"\nFound {direct_debits.count()} processed direct debits")
        
        for debit in direct_debits:
            try:
                print(f"\nProcessing direct debit: {debit.id}")
                print(f"Contract: {debit.contract.reference}")
                print(f"Invoice: {debit.invoice.invoice.ref}")
                print(f"Amount: {debit.amount}")
                print(f"Processed date: {debit.processed_date}")
                
                entries.append({
                    'date': debit.processed_date,
                    'label': f"Domiciled payment for contract {debit.contract.reference}",
                    'type': 'DIRECT_DEBIT',
                    'debit': debit.amount,
                    'credit': None,
                    'reference': f"DOM/{debit.contract.reference}/{debit.processed_date.strftime('%Y%m')}",
                    'source_type': 'direct_debit',
                    'source_id': debit.id,
                    'display_id': str(debit.id), 
                    'can_delete': False,
                    'can_transfer': False,
                    'is_transferred': False,
                    'is_expandable': True,
                    'contract': {
                        'reference': debit.contract.reference,
                        'id': str(debit.contract.id),
                        'supplier': {
                            'name': debit.contract.supplier.name,
                            'ice_code': debit.contract.supplier.ice_code
                        }
                    },
                    'invoice': {
                        'id': str(debit.invoice.invoice.id),
                        'ref': debit.invoice.invoice.ref,
                        'period_start': debit.invoice.period_start.strftime('%Y-%m-%d'),
                        'period_end': debit.invoice.period_end.strftime('%Y-%m-%d')
                    },
                    'due_date': debit.due_date.strftime('%Y-%m-%d'),
                    'bank': debit.bank_account.get_bank_display(),
                    'account': debit.bank_account.account_number
                })
                print("Entry added successfully")
                
            except Exception as e:
                print(f"Error processing direct debit {debit.id}: {str(e)}")
                print(traceback.format_exc())
        
        print("\n=== Processing VAT Declarations ===")
        vat_config = VATConfiguration.objects.first()
        if vat_config and vat_config.domiciliation_bank_id == bank_account.id:
            declarations = VATDeclaration.objects.filter(
                status=VATDeclaration.PAID,
                payment_date__isnull=False
            )
            
            if start_date:
                declarations = declarations.filter(payment_date__gte=start_date)
            if end_date:
                declarations = declarations.filter(payment_date__lte=end_date)
                
            print(f"Found {declarations.count()} paid VAT declarations")
            for declaration in declarations:
                print(f"\nProcessing VAT declaration: {declaration.period_month}/{declaration.period_year}")
                print(f"Payment date: {declaration.payment_date}")
                print(f"Total invoiced VAT: {declaration.total_invoiced_vat}")
                print(f"Total deducted VAT: {declaration.total_deducted_vat}")
                net_vat = declaration.total_invoiced_vat - declaration.total_deducted_vat
                print(f"Net VAT to pay: {net_vat}")
                
                entries.append({
                    'date': declaration.payment_date,
                    'label': f"VAT Payment {declaration.period_month:02d}/{declaration.period_year}",
                    'type': 'VAT_PAYMENT',
                    'debit': net_vat if net_vat > 0 else None,
                    'credit': abs(net_vat) if net_vat < 0 else None,
                    'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                    'source_type': 'vat_declaration',
                    'source_id': declaration.id,
                    'can_delete': False,
                    'can_transfer': False,
                    'is_transferred': False,
                    'declaration': {
                        'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                        'invoiced_vat': float(declaration.total_invoiced_vat),
                        'deducted_vat': float(declaration.total_deducted_vat),
                        'payment_date': declaration.payment_date.strftime('%Y-%m-%d'),
                        'due_date': declaration.due_date.strftime('%Y-%m-%d')
                    }
                })
        else:
            print("No VAT configuration found or bank account mismatch")

        print("\n=== Processing IR Declarations ===")
        try:
            # Look for IR declarations with matching bank account
            ir_declarations = IRDeclaration.objects.filter(
                status='paid',
                payment_date__isnull=False
            )
            
            if start_date:
                ir_declarations = ir_declarations.filter(payment_date__gte=start_date)
            if end_date:
                ir_declarations = ir_declarations.filter(payment_date__lte=end_date)
            
            # Get IR configuration to check the bank
            ir_config = IRConfiguration.objects.first()
            
            # Only process if the bank matches
            if ir_config and ir_config.domiciliation_bank_id == bank_account.id:
                print(f"Found matching IR configuration for bank {bank_account.account_number}")
                
                print(f"Found {ir_declarations.count()} paid IR declarations")
                for declaration in ir_declarations:
                    print(f"\nProcessing IR declaration: {declaration.period_month}/{declaration.period_year}")
                    print(f"Payment date: {declaration.payment_date}")
                    print(f"Tax amount: {declaration.tax_amount}")
                    
                    entries.append({
                        'date': declaration.payment_date,
                        'label': f"IR Payment {declaration.period_month:02d}/{declaration.period_year}",
                        'type': 'IR_PAYMENT',
                        'debit': declaration.tax_amount,
                        'credit': None,
                        'reference': f"IR-{declaration.period_month:02d}-{declaration.period_year}",
                        'source_type': 'ir_declaration',
                        'source_id': declaration.id,
                        'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                        'salary_amount': float(declaration.salary_amount),
                        'tax_amount': float(declaration.tax_amount),
                        'due_date': declaration.due_date.strftime('%Y-%m-%d'),
                        'can_delete': False,
                        'can_transfer': False,
                        'is_transferred': False,
                    })
            else:
                # Check for IR forecasts directly for this bank account
                ir_forecasts = ForecastStatement.objects.filter(
                    bank_account=bank_account,
                    source_type='ir_declaration'
                )
                
                if ir_forecasts.exists():
                    print(f"Found {ir_forecasts.count()} IR forecasts for bank {bank_account.account_number}")
                    # But no configuration matches
                    print("IR configuration exists but doesn't match this bank account")
                else:
                    print("No IR forecasts found for this bank account")
        except Exception as e:
            print(f"Error processing IR declarations: {str(e)}")

        print("\n=== Processing Stamp Rights Declarations ===")
        stamp_rights = StampRightDeclaration.objects.filter(
            payment_date__isnull=False,
            status='paid'
        )   
        
        config = StampRightConfiguration.get_config()

        if config and config.domiciliation_bank_id == bank_account.id:
            print(f"Found matching stamp right configuration for bank {bank_account.account_number}")
            
            print(f"Found {stamp_rights.count()} paid stamp rights declarations")
            for declaration in stamp_rights:
                print(f"\nProcessing stamp rights declaration: {declaration.period_month}/{declaration.period_year}")
                print(f"Payment date: {declaration.payment_date}")
                print(f"Tax amount: {declaration.tax_amount}")
                
                entries.append({
                    'date': declaration.payment_date,
                    'label': f"Stamp Rights Payment {declaration.period_month:02d}/{declaration.period_year}",
                    'type': 'STAMP_PAYMENT',
                    'debit': declaration.tax_amount,
                    'credit': None,
                    'reference': f"SR-{declaration.period_month:02d}-{declaration.period_year}",
                    'source_type': 'stamp_right_declaration',
                    'source_id': declaration.id,
                    'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                    'invoices_amount': float(declaration.invoices_amount),
                    'tax_amount': float(declaration.tax_amount),
                    'due_date': declaration.due_date.strftime('%Y-%m-%d'),
                    'can_delete': False,
                    'can_transfer': False,
                    'is_transferred': False,
                })
        else:
            print("No stamp right configuration found or bank account mismatch")

        # pay declarations
        pay_declarations = PayDeclaration.objects.filter(
            status=PayDeclaration.STATUS_PAID,
            direct_debit__isnull=False,
            direct_debit__bank_account=bank_account
        )

        if start_date:
            pay_declarations = pay_declarations.filter(payment_date__gte=start_date)
        if end_date:
            pay_declarations = pay_declarations.filter(payment_date__lte=end_date)

        print(f"\nProcessing pay declarations: {pay_declarations.count()}")

        for declaration in pay_declarations:
            entries.append({
                'date': declaration.payment_date,
                'label': f"Pay Declaration {declaration.period_month:02d}/{declaration.period_year}",
                'type': 'PAY_DECLARATION',
                'debit': declaration.total_amount,
                'credit': None,
                'reference': f"PAY-{declaration.period_month:02d}-{declaration.period_year}",
                'source_type': 'pay_declaration',
                'source_id': declaration.id,
                'can_delete': False,
                'can_transfer': False,
                'is_transferred': False,
                'details': {
                    'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                    'items_count': declaration.items.count(),
                    'payment_date': declaration.payment_date.strftime('%Y-%m-%d'),
                    'due_date': declaration.due_date.strftime('%Y-%m-%d')
                }
            })
            
        initial_balance = Decimal('0.00')
        if start_date:
            # First sort all entries by date
            entries.sort(key=lambda x: x['date'])
            
            # Calculate sum of all operations before start_date
            for entry in entries:
                if entry['date'] < start_date:
                    initial_balance += (entry['credit'] or Decimal('0.00')) - (entry['debit'] or Decimal('0.00'))

            # Add opening balance entry
            entries.append({
                'date': start_date,
                'label': 'Opening Balance',
                'type': 'BALANCE',
                'debit': initial_balance if initial_balance < 0 else None,
                'credit': initial_balance if initial_balance > 0 else None,
                'reference': 'Opening balance',
                'source_type': 'balance',
                'source_id': None,
                'can_transfer': False,
                'is_transferred': False,
                'balance': initial_balance
            })

        # Then your existing date filtering code:
        if start_date or end_date:
            filtered_entries = []
            for entry in entries:
                entry_date = entry['date']
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                filtered_entries.append(entry)
            entries = filtered_entries

        # Add forecast entries
        if include_forecasts:  # Only add forecasts if the parameter is True
            forecast_entries = ForecastStatement.objects.filter(
                bank_account=bank_account,
                is_processed=False
            )
            if start_date:
                forecast_entries = forecast_entries.filter(date__gte=start_date)
            if end_date:
                forecast_entries = forecast_entries.filter(date__lte=end_date)

            for forecast in forecast_entries:
                entries.append({
                    'date': forecast.date,
                    'label': forecast.label,
                    'debit': forecast.debit,
                    'credit': forecast.credit,
                    'reference': forecast.reference,
                    'source_type': forecast.source_type,
                    'source_id': forecast.source_id,
                    'type': 'FORECAST',
                    'is_forecast': True
                })

        # Sort entries by date in reverse order
        entries.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate balance
        balance = initial_balance if start_date else Decimal('0.00')
        for entry in reversed(entries):
            if entry.get('type') != 'BALANCE':  # Skip balance entry when calculating
                balance += (entry['credit'] or Decimal('0.00')) - (entry['debit'] or Decimal('0.00'))
            entry['balance'] = balance

        return entries
    
    @classmethod
    def calculate_balance_until(cls, bank_account, date):
        """Calculate total balance up to a specific date"""
        print(f"\n=== Calculating Balance Until {date} ===")
        print(f"Bank Account: {bank_account.bank} - {bank_account.account_number}")
        
        entries = cls.get_statement(bank_account, end_date=date, include_forecasts=False)
        
        print(f"Found {len(entries)} entries")
        
        if entries:
            balance = entries[0]['balance']  # First entry has final balance since they're sorted in reverse
            print(f"Final balance: {balance}")
            return balance
            
        print("No entries found, returning 0")
        return Decimal('0.00')