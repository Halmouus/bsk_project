import calendar
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
from django.contrib.contenttypes.fields import GenericForeignKey
from itertools import groupby
from operator import itemgetter
import traceback
from dateutil.relativedelta import relativedelta
from django.db.models.functions import Coalesce
from django.db.models import Sum, Manager, Max
from django.utils.translation import gettext_lazy as _
import re

logger = logging.getLogger(__name__)

MOROCCAN_BANKS = [
    ('ATW', 'Attijariwafa Bank'),
    ('BCP', 'Banque Populaire'),
    ('BOA', 'Bank of Africa'),
    ('CAM', 'Crédit Agricole du Maroc'),
    ('CIH', 'CIH Bank'),
    ('BMCI', 'BMCI'),
    ('SGM', 'Société Générale Maroc'),
    ('CDM', 'Crédit du Maroc'),
    ('ABB', 'Al Barid Bank'),
    ('CFG', 'CFG Bank'),
    ('ABM', 'Arab Bank Maroc'),
    ('CTB', 'Citibank Maghreb')
]

INVOICE_TYPES = [
    ('ENERGY', 'Energy'),
    ('INSURANCE', 'Insurance'),
    ('LEASING', 'Leasing'),
    ('UTILITIES', 'Water/Electricity'),
    ('TELECOM', 'Phone/Internet'),
    ('RENT', 'Rent'),
    ('SERVICE', 'Services'),
    ('LOAN', 'Bank Loan'),
    ('SOCIAL', 'Social Security'),
    ('RETIREMENT', 'Retirement'),
    ('OTHER', 'Other')
]

INVOICE_STATUS = [
    ('ORIGINAL', 'Original'),
    ('COPY', 'Copy')
]

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

class Supplier(BaseModel):

    numeric_validator = RegexValidator(r'^[0-9]*$', _('Only numeric characters are allowed.'))
    alphanumeric_validator = RegexValidator(r'^[a-zA-Z0-9 ]*$', _('Only alphanumeric characters are allowed.'))

    name = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    if_code = models.CharField(max_length=25, unique=True, validators=[numeric_validator])
    ice_code = models.CharField(max_length=15, unique=True, validators=[numeric_validator])  # Exactly 15 characters
    rc_code = models.CharField(max_length=25, validators=[numeric_validator])
    rc_center = models.CharField(max_length=100, validators=[alphanumeric_validator])
    accounting_code = models.CharField(max_length=25, unique=True, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    service = models.CharField(max_length=255, blank=True, validators=[alphanumeric_validator])  # Description of merch/service sold
    delay_convention = models.IntegerField(choices=[(0, '0'), (30, '30'), (60, '60'), (90, '90'), (120, '120')], default=60)
    is_regulated = models.BooleanField(default=False)
    regulation_file_path = models.FileField(upload_to='supplier_regulations/', null=True, blank=True)
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


class BankAccount(BaseModel):
    BANK_CHOICES = [
        ('ATW', 'Attijariwafa Bank'),
        ('BCP', 'Banque Populaire'),
        ('BOA', 'Bank of Africa'),
        ('CAM', 'Crédit Agricole du Maroc'),
        ('CIH', 'CIH Bank'),
        ('BMCI', 'BMCI'),
        ('SGM', 'Société Générale Maroc'),
        ('CDM', 'Crédit du Maroc'),
        ('ABB', 'Al Barid Bank'),
        ('CFG', 'CFG Bank'),
        ('ABM', 'Arab Bank Maroc'),
        ('CTB', 'Citibank Maghreb')
    ]

    ACCOUNT_TYPE = [
        ('national', 'National'),
        ('international', 'International')
    ]

    bank = models.CharField(max_length=4, choices=BANK_CHOICES)
    account_number = models.CharField(
        max_length=30,
        validators=[
            MinLengthValidator(10, _('Account number must be at least 10 characters')),
            RegexValidator(r'^\d+$', _('Only numeric characters allowed'))
        ]
    )
    accounting_number = models.CharField(
        max_length=10,
        validators=[
            MinLengthValidator(5, _('Accounting number must be at least 5 characters')),
            RegexValidator(r'^\d+$', _('Only numeric characters allowed'))
        ]
    )
    journal_number = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(r'^\d{2}$', _('Must be exactly 2 digits'))
        ]
    )
    city = models.CharField(max_length=100)
    if_code = models.CharField(
        max_length=25, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^[0-9]*$', _('Only numeric characters are allowed.'))]
    )
    ice_code = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(r'^[0-9]{15}$', _('ICE code must be exactly 15 digits'))
        ]
    )
    account_type = models.CharField(max_length=15, choices=ACCOUNT_TYPE)
    is_active = models.BooleanField(default=True)

    is_current = models.BooleanField(
        default=False,
        help_text=_("Determines if accounting operations are recorded on this account")
    )
    bank_overdraft = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Maximum allowed overdraft amount")
    )
    overdraft_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Fee applied for overdraft usage")
    )
    has_check_discount_line = models.BooleanField(
        default=False,
        help_text=_("Indicates if this account can discount checks")
    )
    check_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Maximum amount available for check discounting")
    )
    has_lcn_discount_line = models.BooleanField(
        default=False,
        help_text=_("Indicates if this account can discount LCNs")
    )
    lcn_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Maximum amount available for LCN discounting")
    )
    stamp_fee_per_receipt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Stamp fee charged per presented receipt")
    )

    def get_available_check_discount_line(self):
        """Calculate remaining check discount line amount"""
        if not self.has_check_discount_line or not self.check_discount_line_amount:
            return Decimal('0.00')
            
        # Get all discounted checks for this account
        total_discounted = PresentationReceipt.objects.filter(
            presentation__bank_account=self,
            presentation__presentation_type='DISCOUNT',
            checkreceipt__isnull=False  # Ensure it's a check
        ).exclude(
            recorded_status__in=['UNPAID', 'PAID'] # Only count currently discounted
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return self.check_discount_line_amount - total_discounted

    def get_available_lcn_discount_line(self):
        """Calculate remaining LCN discount line amount"""
        if not self.has_lcn_discount_line or not self.lcn_discount_line_amount:
            return Decimal('0.00')
            
        discounted_amount = PresentationReceipt.objects.filter(
            presentation__bank_account=self,
            presentation__presentation_type='DISCOUNT',
            lcn__isnull=False,  # Ensure it's an LCN
            lcn__status='DISCOUNTED'  # Only count currently discounted
        ).exclude(
            lcn__status__in=['UNPAID', 'PAID', 'COMPENSATED']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return self.lcn_discount_line_amount - discounted_amount
    
    def get_current_balance(self):
        """Get current balance for the account"""
        from .models import BankStatement  # Import here to avoid circular import
        return BankStatement.calculate_balance_until(self, timezone.now().date())

    def create_supplier(self):
        """Create or update supplier for bank account"""
        print(f"\n=== Creating/Updating Bank Supplier ===")
        print(f"Bank: {self.bank} - {self.account_number}")
        
        # Only create supplier if IF/ICE codes are provided
        if not (self.if_code and self.ice_code):
            print("Missing IF/ICE codes, skipping supplier creation")
            return None
            
        supplier, created = Supplier.objects.update_or_create(
            ice_code=self.ice_code,
            defaults={
                'name': f"{self.get_bank_display()}",
                'if_code': self.if_code,
                'rc_code': self.if_code,  # Use IF code as RC
                'rc_center': self.city,
                'accounting_code': self.accounting_number,
                'service': 'Banking',
                'delay_convention': 0,  # No delay for bank payments
                'is_regulated': True
            }
        )
        
        print(f"Supplier {'created' if created else 'updated'}: {supplier.name}")
        return supplier

    def clean(self):
        super().clean()

        # Only validate if either code is provided
        if self.if_code or self.ice_code:
            if not (self.if_code and self.ice_code):
                raise ValidationError(_("Both IF and ICE codes must be provided for bank suppliers"))
                
            # Validate IF code is numeric
            if not self.if_code.isdigit():
                raise ValidationError({
                    'if_code': _("IF code must be numeric")
                })
            
            # Validate ICE code has exactly 15 digits
            if len(self.ice_code) != 15 or not self.ice_code.isdigit():
                raise ValidationError({
                    'ice_code': _("ICE code must contain exactly 15 digits")
                })
            
        if self.has_check_discount_line and not self.check_discount_line_amount:
            raise ValidationError({
                'check_discount_line_amount': _('Amount required when check discount line is enabled')
            })
        if self.has_lcn_discount_line and not self.lcn_discount_line_amount:
            raise ValidationError({
                'lcn_discount_line_amount': _('Amount required when LCN discount line is enabled')
            })
    
    def save(self, *args, **kwargs):
        """Override save to create supplier"""
        super().save(*args, **kwargs)
        if self.if_code and self.ice_code:
            self.create_supplier()

    class Meta:
        ordering = ['bank', 'account_number']


    def __str__(self):
        type_indicator = 'NAT' if self.account_type == 'national' else 'INT'
        return f"{self.bank} [{self.account_number}] - {type_indicator}"
    
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

        if self.payment_due:
            print(f"[Check Save] Initial payment_due: {self.payment_due} (type: {type(self.payment_due)})")
            
            # Ensure payment_due is a date object
            if isinstance(self.payment_due, str):
                try:
                    self.payment_due = datetime.datetime.strptime(self.payment_due, '%Y-%m-%d').date()
                    print(f"[Check Save] Converted payment_due to date: {self.payment_due}")
                except ValueError as e:
                    print(f"[Check Save] Error converting payment_due date: {e}")
                    return super().save(*args, **kwargs)

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
                        reference=f"Payment #{self.position}",
                        source_type='supplier_check',
                        source_id=self.id
                    )
                    print(f"[Check Save] Forecast created successfully")
                    
                except Exception as e:
                    print(f"[Check Save] Error during forecast creation: {str(e)}")
                    # Don't let forecast errors prevent check creation
                    pass
        
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
        

        if not self.is_supplier_payment and not self.cause:
            raise ValidationError(_("Invoice is required for direct invoice payments"))
            
        if self.is_supplier_payment and self.cause:
            raise ValidationError(_("Supplier payments cannot specify a direct cause"))
            
        if self.cause and self.cause.supplier != self.beneficiary:
            raise ValidationError(_("Invoice supplier must match check beneficiary"))
            
        # Validate amount for invoice payments
        if not self.is_supplier_payment and self.cause:
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
        

class AccountingEntry(models.Model):
    """
    Virtual model that dynamically generates accounting entries.
    Does not store records directly - serves as a view model.
    """
    class Meta:
        managed = False

    @classmethod
    def get_entries(cls, bank_account, start_date=None, end_date=None):
        """
        Dynamically generates double-entry accounting records.
        Returns chronologically ordered list of debit/credit pairs.
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
            # Journal entry for the bank side
            entries.extend([
                {
                    'date': deposit.date,
                    'label': f"Cash withdrawal - {deposit.reference}",
                    'debit': None,
                    'credit': deposit.amount,
                    'account_code': bank_account.accounting_number,
                    'reference': deposit.reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_deposit',
                    'source_id': deposit.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': deposit.date,
                    'label': f"Cash withdrawal - {deposit.reference}",
                    'debit': deposit.amount,
                    'credit': None,
                    'account_code': CashConfiguration.get_config().accounting_code,
                    'reference': deposit.reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_deposit',
                    'source_id': deposit.id,
                    'pair_index': len(entries) // 2
                }
            ])
            print(f"Added cash withdrawal accounting entries: {deposit.amount}")
        
        # Get all relevant receipts and presentations
        cash_receipts = CashReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        transfer_receipts = TransferReceipt.objects.filter(
            credited_account=bank_account
        ).select_related('entity', 'client')
        
        presentations = Presentation.objects.filter(
            bank_account=bank_account
        ).prefetch_related(
            'presentation_receipts__checkreceipt',
            'presentation_receipts__lcn'
        )
        
        # Process cash receipts
        for receipt in cash_receipts:
            label = f"Cash payment from {receipt.entity.name}"
            reference = receipt.reference_number or 'N/A'
            
            # Add debit and credit pair
            entries.extend([
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': receipt.amount,
                    'credit': None,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': None,
                    'credit': receipt.amount,
                    'account_code': receipt.entity.accounting_code,  # Entity account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'cash_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                }
            ])
            
        # Process transfer receipts
        for receipt in transfer_receipts:
            label = f"Bank transfer from {receipt.entity.name}"
            reference = receipt.transfer_reference
            
            # Add debit and credit pair
            entries.extend([
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': receipt.amount,
                    'credit': None,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'transfer_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': receipt.operation_date,
                    'label': label,
                    'debit': None,
                    'credit': receipt.amount,
                    'account_code': receipt.entity.accounting_code,  # Entity account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'transfer_receipt',
                    'source_id': receipt.id,
                    'pair_index': len(entries) // 2
                }
            ])

        # Process presentations
        for pres in presentations:
            for pr in pres.presentation_receipts.all():
                receipt = pr.checkreceipt or pr.lcn
                receipt_type = 'check' if pr.checkreceipt else 'lcn'
                reference = pres.bank_reference or f"Pres. #{pres.id}"
                
                # For collection presentations - only record if marked as PAID
                if pres.presentation_type == 'COLLECTION' and pr.recorded_status == 'PAID':
                    label = f"Payment of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                    
                    # Get payment date from history
                    payment_history = ReceiptHistory.objects.filter(
                        content_type=ContentType.objects.get_for_model(receipt.__class__),
                        object_id=receipt.id,
                        action='status_changed',
                        new_value__status='PAID'
                    ).order_by('-business_date').first()
                    
                    # Use history date if available, otherwise use presentation date
                    entry_date = (payment_history.business_date.date() 
                        if payment_history and payment_history.business_date 
                        else pres.date)
                    
                    # Add debit and credit pair with correct date
                    entries.extend([
                        {
                            'date': entry_date,  # Use correct payment date
                            'label': label,
                            'debit': receipt.amount,
                            'credit': None,
                            'account_code': bank_account.accounting_number,  # Bank account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': entry_date,  # Use correct payment date
                            'label': label,
                            'debit': None,
                            'credit': receipt.amount,
                            'account_code': receipt.entity.accounting_code,  # Entity account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        }
                    ])
                
                # For discount presentations
                elif pres.presentation_type == 'DISCOUNT':
                    
                    # Initial discount entry
                    label = f"Discount of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                    
                    # Add debit and credit pair
                    entries.extend([
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': receipt.amount,
                            'credit': None,
                            'account_code': bank_account.accounting_number,  # Bank account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': pres.date,
                            'label': label,
                            'debit': None,
                            'credit': receipt.amount,
                            'account_code': '5000',  # On-hold account
                            'reference': reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'presentation_receipt',
                            'source_id': pr.id,
                            'pair_index': len(entries) // 2
                        }
                    ])

                    # If marked as unpaid in this presentation, add reversal
                    if pr.recorded_status == 'UNPAID':
                        label = f"Reversal of {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"

                        payment_history = ReceiptHistory.objects.filter(
                            content_type=ContentType.objects.get_for_model(receipt.__class__),
                            object_id=receipt.id,
                            action='status_changed',
                            new_value__status='UNPAID'
                        ).order_by('business_date', '-timestamp').first()
                        
                        entry_date = payment_history.business_date.date() if payment_history and payment_history.business_date else pres.date
                        print(f"Using payment date for discounted receipt: {entry_date}")

                        # Add debit and credit pair for reversal
                        entries.extend([
                            {
                                'date': entry_date,
                                'label': label,
                                'debit': None,
                                'credit': receipt.amount,
                                'account_code': bank_account.accounting_number,  # Bank account
                                'reference': reference,
                                'journal_code': bank_account.journal_number,
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            },
                            {
                                'date': entry_date,
                                'label': label,
                                'debit': receipt.amount,
                                'credit': None,
                                'account_code': '5000',  # On-hold account
                                'reference': reference,
                                'journal_code': bank_account.journal_number,
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            }
                        ])
                        
                    # If paid, record other operations entry
                    elif pr.recorded_status == 'PAID':
                        label = f"Payment of discounted {receipt_type} #{receipt.get_receipt_number()} - {receipt.entity.name}"
                        
                        payment_history = ReceiptHistory.objects.filter(
                            content_type=ContentType.objects.get_for_model(receipt.__class__),
                            object_id=receipt.id,
                            action='status_changed',
                            new_value__status='PAID'
                        ).order_by('business_date', '-timestamp').first()
                        
                        entry_date = payment_history.business_date.date() if payment_history and payment_history.business_date else pres.date
                        print(f"Using payment date for discounted receipt: {entry_date}")

                        # Add debit and credit pair for other operations
                        entries.extend([
                            {
                                'date': entry_date,
                                'label': label,
                                'debit': receipt.amount,
                                'credit': None,
                                'account_code': '5000',  # On-hold account
                                'reference': reference,
                                'journal_code': '06',  # Other operations
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            },
                            {
                                'date': entry_date,
                                'label': label,
                                'debit': None,
                                'credit': receipt.amount,
                                'account_code': receipt.entity.accounting_code,  # Entity account
                                'reference': reference,
                                'journal_code': '06',  # Other operations
                                'source_type': 'presentation_receipt',
                                'source_id': pr.id,
                                'pair_index': len(entries) // 2
                            }
                        ])

        incoming_transfers = InterBankTransfer.objects.filter(
            to_bank=bank_account,
            is_deleted=False
        ).prefetch_related('transferred_records')
        
        for transfer in incoming_transfers:
            for transferred_record in transfer.transferred_records.all():
                # Need to get the original record's entity
                if transferred_record.source_type == 'cash_receipt':
                    original_record = CashReceipt.objects.get(id=transferred_record.source_id)
                elif transferred_record.source_type == 'transfer_receipt':
                    original_record = TransferReceipt.objects.get(id=transferred_record.source_id)
                else:  # presentation_receipt
                    pres_receipt = PresentationReceipt.objects.get(id=transferred_record.source_id)
                    original_record = pres_receipt.checkreceipt or pres_receipt.lcn

                # Now we can access the entity
                entries.extend([
                    {
                        'date': transfer.date,
                        'label': f"{transfer.label} - {transferred_record.original_label}",
                        'debit': transferred_record.amount,
                        'credit': None,
                        'account_code': bank_account.accounting_number,  # Bank account
                        'reference': transferred_record.original_reference,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'transferred_record',
                        'source_id': transferred_record.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': transfer.date,
                        'label': f"{transfer.label} - {transferred_record.original_label}",
                        'debit': None,
                        'credit': transferred_record.amount,
                        'account_code': original_record.entity.accounting_code,  # Entity account
                        'reference': transferred_record.original_reference,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'transferred_record',
                        'source_id': transferred_record.id,
                        'pair_index': len(entries) // 2
                    }
                ])
        
        custom_records = CustomBankRecord.objects.filter(
            bank_account=bank_account
        )
        
        print(f"Found {custom_records.count()} custom records")
        
        if start_date:
            custom_records = custom_records.filter(date__gte=start_date)
        if end_date:
            custom_records = custom_records.filter(date__lte=end_date)
        
        print(f"After date filtering: {custom_records.count()} custom records")
        
        # Debug log custom records
        for record in custom_records:
            print(f"\nCustom record: {record.id}")
            print(f"Date: {record.date}")
            print(f"Bank Label: {record.bank_label}")
            print(f"Accounting Label: {record.accounting_label}")
            print(f"Debit: {record.debit}")
            print(f"Credit: {record.credit}")
            print(f"Account Code: {record.account_code}")
            
            # Add the main account entry
            entries.append({
                'date': record.date,
                'label': record.accounting_label,
                'debit': record.debit,
                'credit': record.credit,
                'account_code': record.account_code,
                'reference': record.reference,
                'journal_code': bank_account.journal_number,
                'source_type': 'custom_record',
                'source_id': record.id,
                'pair_index': len(entries) // 2
            })
            
            # Add the counterpart entry (bank account)
            entries.append({
                'date': record.date,
                'label': record.accounting_label,
                'debit': record.credit,  # Swap debit/credit for counterpart
                'credit': record.debit,  # Swap debit/credit for counterpart
                'account_code': bank_account.accounting_number,
                'reference': record.reference,
                'journal_code': bank_account.journal_number,
                'source_type': 'custom_record',
                'source_id': record.id,
                'pair_index': len(entries) // 2
            })
        
        # Bank fee entries
        fee_transactions = BankFeeTransaction.objects.filter(
            bank_account=bank_account
        ).select_related('fee_type')

        for fee in fee_transactions:
            # Raw amount entry
            entries.extend([
                {
                    'date': fee.date,
                    'label': f"{fee.fee_type.name} - Raw Amount",
                    'debit': fee.raw_amount,
                    'credit': None,
                    'account_code': fee.fee_type.accounting_code,  # Fee account
                    'reference': fee.fee_type.code,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'bank_fee',
                    'source_id': fee.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': fee.date,
                    'label': f"{fee.fee_type.name} - Raw Amount",
                    'debit': None,
                    'credit': fee.raw_amount,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': fee.fee_type.code,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'bank_fee',
                    'source_id': fee.id,
                    'pair_index': len(entries) // 2
                }
            ])

            
            # VAT entry if applicable
            if fee.vat_amount > 0:
                entries.extend([
                    {
                        'date': fee.date,
                        'label': f"{fee.fee_type.name} - VAT",
                        'debit': fee.vat_amount,
                        'credit': None,
                        'account_code': fee.fee_type.vat_code,  # VAT account
                        'reference': fee.fee_type.code,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'bank_fee',
                        'source_id': fee.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': fee.date,
                        'label': f"{fee.fee_type.name} - VAT",
                        'debit': None,
                        'credit': fee.vat_amount,
                        'account_code': bank_account.accounting_number,  # Bank account
                        'reference': fee.fee_type.code,
                        'journal_code': bank_account.journal_number,
                        'source_type': 'bank_fee',
                        'source_id': fee.id,
                        'pair_index': len(entries) // 2
                    }
                ])

        # Supplier payments accounting entries
        supplier_payments = Check.objects.filter(
            checker__bank_account=bank_account,
            status='paid'
        ).select_related('checker', 'beneficiary')

        for payment in supplier_payments:
            label = f"Payment to {payment.beneficiary.name}"
            reference = f"{payment.checker.type} {payment.checker.index}{payment.position}"

            # Add debit and credit pair
            entries.extend([
                {
                    'date': payment.paid_at.date(),
                    'label': label,
                    'debit': None,
                    'credit': payment.amount,
                    'account_code': bank_account.accounting_number,  # Bank account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'supplier_payment',
                    'source_id': payment.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': payment.paid_at.date(),
                    'label': label,
                    'debit': payment.amount,
                    'credit': None,
                    'account_code': payment.beneficiary.accounting_code,  # Supplier account
                    'reference': reference,
                    'journal_code': bank_account.journal_number,
                    'source_type': 'supplier_payment',
                    'source_id': payment.id,
                    'pair_index': len(entries) // 2
                }
            ])

        contract_payments = ForecastStatement.objects.filter(
            bank_account=bank_account,
            source_type='contract_domiciliation',
            is_processed=True
        ).select_related('bank_account')

        print(f"Found {contract_payments.count()} contract payments to account for")

        for payment in contract_payments:
            try:
                contract = Contract.objects.get(id=payment.source_id)
                print(f"\n=== Processing Contract Payment Accounting ===")
                print(f"Contract: {contract.reference}")
                print(f"Payment date: {payment.date}")
                print(f"Amount: {payment.debit}")

                # Get invoice for this payment period
                contract_invoice = ContractInvoice.objects.filter(
                    contract=contract,
                    period_start__year=payment.date.year,
                    period_start__month=payment.date.month
                ).select_related('invoice').first()

                if contract_invoice and contract_invoice.invoice:
                    print(f"Found invoice: {contract_invoice.invoice.ref}")
                    # Mirror invoice accounting entries with bank journal
                    invoice_entries = contract_invoice.invoice.get_accounting_entries()
                    print(f"Found {len(invoice_entries)} invoice entries to mirror")
                    
                    for entry in invoice_entries:
                        print(f"Mirroring entry: {entry['label']}")
                        print(f"Account: {entry['account_code']}")
                        print(f"Debit: {entry['debit']}, Credit: {entry['credit']}")
                        
                        entries.append({
                            'date': payment.date,
                            'label': entry['label'],
                            'debit': entry['debit'],
                            'credit': entry['credit'],
                            'account_code': entry['account_code'],
                            'reference': payment.reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'contract_domiciliation',
                            'source_id': payment.source_id,
                            'pair_index': len(entries) // 2
                        })
                else:
                    print("No invoice found, using default supplier accounting")
                    # Fallback to default supplier payment accounting
                    entries.extend([
                        {
                            'date': payment.date,
                            'label': f"Domiciled payment for contract {contract.reference}",
                            'debit': payment.debit,
                            'credit': None,
                            'account_code': contract.supplier.accounting_code,
                            'reference': payment.reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'contract_domiciliation',
                            'source_id': payment.source_id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': payment.date,
                            'label': f"Domiciled payment for contract {contract.reference}",
                            'debit': None,
                            'credit': payment.debit,
                            'account_code': bank_account.accounting_number,
                            'reference': payment.reference,
                            'journal_code': bank_account.journal_number,
                            'source_type': 'contract_domiciliation',
                            'source_id': payment.source_id,
                            'pair_index': len(entries) // 2
                        }
                    ])

            except Contract.DoesNotExist:
                print(f"Contract {payment.source_id} not found")
                continue
            except Exception as e:
                print(f"Error creating accounting entries: {str(e)}")
                print(traceback.format_exc())
                continue
        
        # Pay declarations
        pay_declarations = PayDeclaration.objects.filter(
            status=PayDeclaration.STATUS_PAID
        )

        if start_date:
            pay_declarations = pay_declarations.filter(payment_date__gte=start_date)
        if end_date:
            pay_declarations = pay_declarations.filter(payment_date__lte=end_date)

        print(f"\nProcessing pay declarations: {pay_declarations.count()}")

        for declaration in pay_declarations:
            # Group by account code
            account_groups = {}
            for item in declaration.items.all():
                if item.account_code not in account_groups:
                    account_groups[item.account_code] = []
                account_groups[item.account_code].append(item)

            # Create entries for each account
            for account_code, items in account_groups.items():
                total = sum(
                    item.amount if item.is_debit else -item.amount 
                    for item in items
                )
                if total != 0:
                    entries.append({
                        'date': declaration.payment_date,
                        'label': f"Pay {declaration.period_month:02d}/{declaration.period_year}",
                        'debit': abs(total) if total > 0 else None,
                        'credit': abs(total) if total < 0 else None,
                        'account_code': account_code,
                        'reference': f"PAY-{declaration.period_month:02d}-{declaration.period_year}",
                        'journal_code': '07',
                        'source_type': 'pay_declaration',
                        'source_id': declaration.id
                    })

        print("\n=== Getting VAT Accounting Entries ===")
        declarations = VATDeclaration.objects.filter(
            status=VATDeclaration.PAID,
        ).select_related('forecast')

        print(f"Found {declarations.count()} paid declarations")
        print(f"Query: {declarations.query}")  # Print the query

        for declaration in declarations:
            print(f"\nProcessing declaration: {declaration.period_month}/{declaration.period_year}")
            config = VATConfiguration.objects.first()
            print(f"Config found: {bool(config)}")
            if not config:
                continue

            # Print payment details    
            print(f"Payment date: {declaration.payment_date}")
            print(f"Total invoiced VAT: {declaration.total_invoiced_vat}")
            print(f"Total deducted VAT: {declaration.total_deducted_vat}")
            print(f"Net VAT: {declaration.total_invoiced_vat - declaration.total_deducted_vat}")
                
            # Get period end date for accounting entries
            period_end = datetime.date(
                declaration.period_year + (declaration.period_month == 12),
                (declaration.period_month % 12) + 1,
                1
            ) - timedelta(days=1)
            
            # Payment entry in bank journal
            entries.extend([
                {
                    'date': declaration.payment_date,
                    'label': f"VAT Payment {declaration.period_month:02d}/{declaration.period_year}",
                    'debit': declaration.total_invoiced_vat - declaration.total_deducted_vat,
                    'credit': None,
                    'account_code': config.deducted_vat_account,
                    'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                    'journal_code': bank_account.journal_number,
                    'source_type': 'vat_declaration',
                    'source_id': declaration.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': declaration.payment_date,
                    'label': f"VAT Payment {declaration.period_month:02d}/{declaration.period_year}",
                    'debit': None,
                    'credit': declaration.total_invoiced_vat - declaration.total_deducted_vat,
                    'account_code': bank_account.accounting_number,
                    'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                    'journal_code': bank_account.journal_number,
                    'source_type': 'vat_declaration',
                    'source_id': declaration.id,
                    'pair_index': len(entries) // 2
                }
            ])
            
            # VAT declaration entries in VAT journal
            # First entry: Total invoiced VAT
            entries.extend([
                {
                    'date': period_end,
                    'label': f"VAT Declaration {declaration.period_month:02d}/{declaration.period_year} - Invoiced VAT",
                    'debit': declaration.total_invoiced_vat,
                    'credit': None,
                    'account_code': config.invoiced_vat_account,
                    'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                    'journal_code': config.journal,
                    'source_type': 'vat_declaration',
                    'source_id': declaration.id,
                    'pair_index': len(entries) // 2
                },
                {
                    'date': period_end,
                    'label': f"VAT Declaration {declaration.period_month:02d}/{declaration.period_year} - Invoiced VAT",
                    'debit': None,
                    'credit': declaration.total_invoiced_vat,
                    'account_code': config.deducted_vat_account,
                    'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                    'journal_code': config.journal,
                    'source_type': 'vat_declaration',
                    'source_id': declaration.id,
                    'pair_index': len(entries) // 2
                }
            ])
            
            # Process deducted VAT by rate
            details = declaration.details.exclude(source_type='receipt')
            by_rate = {}
            for detail in details:
                by_rate[detail.vat_rate] = by_rate.get(detail.vat_rate, Decimal('0')) + detail.vat_amount
            
            # Create entries for each VAT rate
            for rate, amount in by_rate.items():
                if rate > 0:
                    entries.extend([
                        {
                            'date': period_end,
                            'label': f"VAT Declaration {declaration.period_month:02d}/{declaration.period_year} - {rate}% VAT",
                            'debit': amount,
                            'credit': None,
                            'account_code': config.deducted_vat_account,
                            'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                            'journal_code': config.journal,
                            'source_type': 'vat_declaration',
                            'source_id': declaration.id,
                            'pair_index': len(entries) // 2
                        },
                        {
                            'date': period_end,
                            'label': f"VAT Declaration {declaration.period_month:02d}/{declaration.period_year} - {rate}% VAT",
                            'debit': None,
                            'credit': amount,
                            'account_code': f"345{int(rate):02d}",  # VAT rate specific account
                            'reference': f"VAT-{declaration.period_month:02d}-{declaration.period_year}",
                            'journal_code': config.journal,
                            'source_type': 'vat_declaration',
                            'source_id': declaration.id,
                            'pair_index': len(entries) // 2
                        }
                    ])

        # Filter entries
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
            print(f"Filtered entries: {entries}")

        # Sort entries keeping pairs together
        entries.sort(key=lambda x: (x['date'], x['pair_index']), reverse=True)
        
        return entries
    
    def get_cash_entries(cls, start_date=None, end_date=None):
        """Generate accounting entries for cash transactions"""
        print("\n=== Getting Cash Accounting Entries ===")
        
        entries = []
        try:
            config = CashConfiguration.get_config()
            
            # Process deposits
            deposits = CashDeposit.objects.all()
            if start_date:
                deposits = deposits.filter(date__gte=start_date)
            if end_date:
                deposits = deposits.filter(date__lte=end_date)
                
            for deposit in deposits:
                entries.extend([
                    {
                        'date': deposit.date,
                        'label': f"Cash deposit {deposit.reference}",
                        'debit': deposit.amount,
                        'credit': None,
                        'account_code': config.accounting_code,
                        'reference': deposit.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_deposit',
                        'source_id': deposit.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': deposit.date,
                        'label': f"Cash deposit {deposit.reference}",
                        'debit': None,
                        'credit': deposit.amount,
                        'account_code': '5161',  # Cash in transit
                        'reference': deposit.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_deposit',
                        'source_id': deposit.id,
                        'pair_index': len(entries) // 2
                    }
                ])
                
            # Process payments
            payments = CashPayment.objects.all()
            if start_date:
                payments = payments.filter(payment_date__gte=start_date)
            if end_date:
                payments = payments.filter(payment_date__lte=end_date)
                
            for payment in payments:
                entries.extend([
                    {
                        'date': payment.payment_date,
                        'label': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': payment.amount,
                        'credit': None,
                        'account_code': payment.invoice.supplier.accounting_code,
                        'reference': payment.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_payment',
                        'source_id': payment.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': payment.payment_date,
                        'label': f"Cash payment for invoice {payment.invoice.ref}",
                        'debit': None,
                        'credit': payment.amount,
                        'account_code': config.accounting_code,
                        'reference': payment.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_payment',
                        'source_id': payment.id,
                        'pair_index': len(entries) // 2
                    }
                ])
            
            # Process expenses
            expenses = CashExpense.objects.all()
            if start_date:
                expenses = expenses.filter(date__gte=start_date)
            if end_date:
                expenses = expenses.filter(date__lte=end_date)
                
            for expense in expenses:
                entries.extend([
                    {
                        'date': expense.date,
                        'label': f"Cash expense ({expense.get_expense_type_display()})",
                        'debit': expense.amount,
                        'credit': None,
                        'account_code': expense.expense_account,
                        'reference': expense.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_expense',
                        'source_id': expense.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': expense.date,
                        'label': f"Cash expense ({expense.get_expense_type_display()})",
                        'debit': None,
                        'credit': expense.amount,
                        'account_code': config.accounting_code,
                        'reference': expense.reference,
                        'journal_code': config.journal_code,
                        'source_type': 'cash_expense',
                        'source_id': expense.id,
                        'pair_index': len(entries) // 2
                    }
                ])

            return entries
            
        except Exception as e:
            print(f"Error getting cash accounting entries: {str(e)}")
            return []


    @classmethod
    def get_entries_for_journal(cls, journal_code, start_date=None, end_date=None):
        print(f"\n=== Getting entries for journal {journal_code} ===")
        print(f"Date range: {start_date} - {end_date}")
        
        entries = []
        declarations = PayDeclaration.objects.filter(
            status=PayDeclaration.STATUS_PAID,
            items__isnull=False
        ).distinct()

        if start_date:
            declarations = declarations.filter(payment_date__gte=start_date)
        if end_date:
            declarations = declarations.filter(payment_date__lte=end_date)

        print(f"Found {declarations.count()} paid declarations")

        for declaration in declarations:
            # Group by account code
            account_groups = {}
            for item in declaration.items.all():
                key = (item.account_code, item.is_debit)
                if key not in account_groups:
                    account_groups[key] = Decimal('0.00')
                account_groups[key] += item.amount

            # Create entries for each account group
            for (account_code, is_debit), amount in account_groups.items():
                entries.append({
                    'date': declaration.payment_date,
                    'label': f"Pay Declaration {declaration.period_month:02d}/{declaration.period_year}",
                    'debit': amount if is_debit else None,
                    'credit': amount if not is_debit else None,
                    'account_code': account_code,
                    'journal_code': journal_code,
                    'reference': f"PAY-{declaration.period_month:02d}-{declaration.period_year}",
                    'source_type': 'pay_declaration',
                    'source_id': declaration.id,
                    'details': {
                        'period': f"{declaration.period_month:02d}/{declaration.period_year}",
                        'items_count': declaration.items.count(),
                        'payment_date': declaration.payment_date.strftime('%Y-%m-% d'),
                        'due_date': declaration.due_date.strftime('%Y-%m-% d')
                    }
                })

        print(f"Generated {len(entries)} accounting entries")
        return entries



class ForecastStatement(BaseModel):
    """Stores forecasted bank statement entries"""
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    date = models.DateField()
    label = models.CharField(max_length=255)
    debit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    credit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    reference = models.CharField(max_length=100)
    source_type = models.CharField(max_length=50)  # 'check_receipt', 'lcn', etc.
    source_id = models.UUIDField()  # ID of the related receipt
    is_processed = models.BooleanField(default=False)  # Turns true when actual statement is created
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Forecast {self.label} on {self.date}"
    
class Contract(BaseModel):
    """Contract for a supplier"""
    PERIOD_MONTHLY = 'monthly'
    PERIOD_QUARTERLY = 'quarterly'
    PERIOD_BIANNUAL = 'biannual'
    PERIOD_ANNUAL = 'annual'
    
    PERIOD_CHOICES = [
        (PERIOD_MONTHLY, 'Monthly'),
        (PERIOD_QUARTERLY, 'Quarterly'),
        (PERIOD_BIANNUAL, 'Biannual'),
        (PERIOD_ANNUAL, 'Annual')
    ]

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_TERMINATED = 'terminated'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_TERMINATED, 'Terminated'),
        (STATUS_EXPIRED, 'Expired')
    ]

    reference = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey('Supplier', on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_indefinite = models.BooleanField(default=False)
    periodicity = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    generation_day = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month to generate invoice (1-28)"
    )
    cancellation_date = models.DateField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    is_domiciled = models.BooleanField(default=False)
    domiciliation_bank = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='domiciled_contracts'
    )
    domiciliation_day = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month for domiciliation payment (1-28)"
    )
    domiciliation_suspended = models.BooleanField(default=False)
    domiciliation_suspension_date = models.DateField(null=True, blank=True)
    domiciliation_suspension_reason = models.TextField(blank=True)
    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPES,
        default='OTHER'
    )
    
    def clean(self):
        if not self.is_indefinite and not self.end_date:
            raise ValidationError("End date is required for fixed-term contracts")
        
        if self.is_indefinite and self.end_date:
            raise ValidationError("Indefinite contracts cannot have an end date")
        
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")

    def get_next_generation_date(self, from_date=None):
        """Calculate the next invoice generation date based on periodicity"""
        if not from_date:
            from_date = timezone.now().date()

        # Start with the generation day in the current month
        next_date = from_date.replace(day=min(self.generation_day, 28))
        
        # If we've passed this month's generation day, move to next period
        if from_date.day > self.generation_day:
            if self.periodicity == self.PERIOD_MONTHLY:
                next_date += relativedelta(months=1)
            elif self.periodicity == self.PERIOD_QUARTERLY:
                next_date += relativedelta(months=3)
            elif self.periodicity == self.PERIOD_BIANNUAL:
                next_date += relativedelta(months=6)
            else:  # annual
                next_date += relativedelta(years=1)
                
        return next_date

    def get_period_end_date(self, start_date):
        """Calculate period end date based on periodicity"""
        if self.periodicity == self.PERIOD_MONTHLY:
            return start_date + relativedelta(months=1, days=-1)
        elif self.periodicity == self.PERIOD_QUARTERLY:
            return start_date + relativedelta(months=3, days=-1)
        elif self.periodicity == self.PERIOD_BIANNUAL:
            return start_date + relativedelta(months=6, days=-1)
        else:  # annual
            return start_date + relativedelta(years=1, days=-1)

    def can_generate_invoice(self, for_date):
        """Check if an invoice can be generated for the given date"""
        if self.status not in [self.STATUS_ACTIVE, self.STATUS_TERMINATED]:
            return False

        # Check if date is within contract period
        if for_date < self.start_date:
            return False
            
        if self.end_date and for_date > self.end_date:
            return False
            
        if self.cancellation_date and for_date > self.cancellation_date:
            return False

        # Check if invoice already exists for this period
        period_start = self.get_period_start_date(for_date)
        period_end = self.get_period_end_date(period_start)
        
        return not ContractInvoice.objects.filter(
            contract=self,
            period_start=period_start,
            period_end=period_end
        ).exists()

    def get_period_start_date(self, for_date):
        """Get the start date of the period containing the given date"""
        if self.periodicity == self.PERIOD_MONTHLY:
            return for_date.replace(day=1)
        elif self.periodicity == self.PERIOD_QUARTERLY:
            month = ((for_date.month - 1) // 3) * 3 + 1
            return for_date.replace(month=month, day=1)
        elif self.periodicity == self.PERIOD_BIANNUAL:
            month = ((for_date.month - 1) // 6) * 6 + 1
            return for_date.replace(month=month, day=1)
        else:  # annual
            return for_date.replace(month=1, day=1)

    def generate_invoice(self, for_date):
        """Generate an invoice for the given date"""
        print(f"\n=== Generating Invoice for Contract {self.reference} ===")
        print(f"Date: {for_date}")
        
        if not self.can_generate_invoice(for_date):
            raise ValidationError("Cannot generate invoice for this date")

        period_start = self.get_period_start_date(for_date)
        period_end = self.get_period_end_date(period_start)
        print(f"Period: {period_start} to {period_end}")

        # Create invoice
        invoice = Invoice.objects.create(
            ref=f"{self.reference}-{period_start.strftime('%Y%m')}",
            date=for_date,
            supplier=self.supplier,
            type='invoice',
            invoice_type=self.invoice_type
        )
        print(f"Created invoice: {invoice.ref}")

        # Add products from contract
        total_amount = Decimal('0')
        for contract_product in self.products.all():
            print(f"\nProcessing product: {contract_product.product.name}")
            # Calculate product amount with VAT
            amount = contract_product.quantity * contract_product.unit_price
            if contract_product.reduction_rate:
                reduction = amount * (contract_product.reduction_rate / Decimal('100'))
                amount -= reduction
            vat_amount = amount * (contract_product.product.vat_rate / Decimal('100'))
            amount += vat_amount
            total_amount += amount
            
            InvoiceProduct.objects.create(
                invoice=invoice,
                product=contract_product.product,
                quantity=contract_product.quantity,
                unit_price=contract_product.unit_price,
                reduction_rate=contract_product.reduction_rate,
                vat_rate=contract_product.product.vat_rate
            )

        # Create contract invoice record
        contract_invoice = ContractInvoice.objects.create(
            contract=self,
            invoice=invoice,
            period_start=period_start,
            period_end=period_end
        )
        print(f"Created contract invoice record: {contract_invoice.id}")

        # If contract is domiciled, create DirectDebit
        if self.is_domiciled and not self.domiciliation_suspended:
            print("\nCreating DirectDebit record")
            valid_day = self.get_valid_day(period_start.year, period_start.month, self.domiciliation_day)
            payment_date = period_start.replace(day=valid_day)
            while payment_date.weekday() >= 5:  # Skip weekends
                payment_date += timedelta(days=1)
            
            # Find associated forecast
            forecast = ForecastStatement.objects.filter(
                bank_account=self.domiciliation_bank,
                date=payment_date,
                source_type='contract_domiciliation',
                source_id=self.id,
                is_processed=False
            ).first()
            print(f"Found forecast: {forecast.id if forecast else None}")

            direct_debit = DirectDebit.objects.create(
                invoice=contract_invoice,
                contract=self,
                bank_account=self.domiciliation_bank,
                due_date=payment_date,
                amount=total_amount,
                forecast=forecast
            )
            print(f"Created DirectDebit: {direct_debit.id}")

        return invoice

    def generate_missing_invoices(self, up_to_date=None):
        """Generate any missing invoices up to given date"""
        print("\n=== Starting invoice generation ===")
        if not up_to_date:
            up_to_date = timezone.now().date()
        print(f"Generating invoices up to: {up_to_date}")
        
        # Start from contract start date
        current_date = self.start_date
        print(f"Starting from date: {current_date}")
        
        invoices = []
        while current_date <= up_to_date:
            print(f"\nChecking date: {current_date}")
            
            if self.can_generate_invoice(current_date):
                print(f"\nChecking if invoice can be generated for {current_date}")
                # Check if invoice exists for this period
                period_start = self.get_period_start_date(current_date)
                period_end = self.get_period_end_date(period_start)
                
                invoice_exists = ContractInvoice.objects.filter(
                    contract=self,
                    period_start=period_start,
                    period_end=period_end
                ).exists()
                
                print(f"Invoice exists for period: {invoice_exists}")
                
                if not invoice_exists:
                    print(f"Generating invoice for: {current_date}")
                    invoice = self.generate_invoice(current_date)
                    invoices.append(invoice)
            
            # Move to next period
            current_date = self._get_next_period_date(current_date)
        
        return invoices

    def can_generate_invoice(self, for_date):
        """Check if an invoice can be generated for the given date"""
        print(f"\nChecking if invoice can be generated for {for_date}")
        
        if self.status not in [self.STATUS_ACTIVE, self.STATUS_TERMINATED]:
            print("Invalid status")
            return False

        # Check if date is within contract period
        if for_date < self.start_date:
            print("Date before contract start")
            return False
            
        if self.end_date and for_date > self.end_date:
            print("Date after contract end")
            return False
            
        if self.cancellation_date and for_date > self.cancellation_date:
            print("Date after cancellation")
            return False

        # Check if invoice already exists for this period
        period_start = self.get_period_start_date(for_date)
        period_end = self.get_period_end_date(period_start)
        
        exists = ContractInvoice.objects.filter(
            contract=self,
            period_start=period_start,
            period_end=period_end
        ).exists()
        
        print(f"Invoice exists for period: {exists}")
        return not exists

    def get_next_generation_date(self, from_date=None):
        """Calculate the next invoice generation date based on periodicity"""
        print(f"\nCalculating next generation date from {from_date}")
        if not from_date:
            from_date = timezone.now().date()

        # Always advance to next period
        if self.periodicity == self.PERIOD_MONTHLY:
            next_date = from_date + relativedelta(months=1)
        elif self.periodicity == self.PERIOD_QUARTERLY:
            next_date = from_date + relativedelta(months=3)
        elif self.periodicity == self.PERIOD_BIANNUAL:
            next_date = from_date + relativedelta(months=6)
        else:  # annual
            next_date = from_date + relativedelta(years=1)

        # Set to generation day
        next_date = next_date.replace(day=min(self.generation_day, 
            (next_date + relativedelta(months=1) - relativedelta(days=1)).day))
        
        print(f"Next generation date: {next_date}")
        return next_date
    
    def suspend_domiciliation(self, date, reason):
        """Suspend domiciliation and remove future forecasts"""
        if not self.is_domiciled:
            raise ValidationError("Contract is not domiciled")
            
        print(f"\n=== Suspending Domiciliation for Contract {self.id} ===")
        print(f"Suspension date: {date}")
        print(f"Reason: {reason}")
        
        self.domiciliation_suspended = True
        self.domiciliation_suspension_date = date
        self.domiciliation_suspension_reason = reason
        
        # Delete future forecasts
        ForecastStatement.objects.filter(
            source_type='contract_domiciliation',
            source_id=self.id,
            date__gte=date
        ).delete()
        
        self.save()

    def _next_business_day(self, date):
        """Get next business day, skipping weekends"""
        print(f"\n=== Getting next business day from {date} ===")
        next_date = date
        while next_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            next_date += timedelta(days=1)
            print(f"Skipped to: {next_date}")
        return next_date

    def _calculate_total_amount_with_vat(self):
        """Calculate total contract amount including VAT"""
        total_amount = Decimal('0')
        for contract_product in self.products.all():
            product_amount = contract_product.quantity * contract_product.unit_price
            
            if contract_product.reduction_rate:
                reduction = product_amount * (contract_product.reduction_rate / Decimal('100'))
                product_amount -= reduction
            
            vat_amount = product_amount * (contract_product.product.vat_rate / Decimal('100'))
            product_amount += vat_amount
            
            total_amount += product_amount
            
        return total_amount

    def _get_or_create_invoice_for_date(self, date):
        """Get or create invoice for the given date"""
        period_start = self.get_period_start_date(date)
        period_end = self.get_period_end_date(period_start)
        
        # Check if invoice exists
        invoice = ContractInvoice.objects.filter(
            contract=self,
            period_start=period_start,
            period_end=period_end
        ).first()
        
        if not invoice and self.can_generate_invoice(date):
            print(f"Generating new invoice for period {period_start} to {period_end}")
            invoice = self.generate_invoice(date)
        
        return invoice

    def _create_forecast_and_direct_debit(self, payment_date, amount, invoice, current_date):
        """Create forecast and direct debit records"""
        # Check if forecast already exists
        existing_forecast = ForecastStatement.objects.filter(
            bank_account=self.domiciliation_bank,
            date=payment_date,
            source_type='contract_domiciliation',
            source_id=self.id
        ).first()
        
        if not existing_forecast:
            print(f"Creating new forecast for {payment_date}")
            forecast = ForecastStatement.objects.create(
                bank_account=self.domiciliation_bank,
                date=payment_date,
                label=f"Domiciled payment for contract {self.reference}",
                debit=amount,
                amount=amount,
                reference=f"DOM/{self.reference}/{current_date.strftime('%Y%m')}",
                source_type='contract_domiciliation',
                source_id=self.id,
                is_processed=False
            )
        else:
            forecast = existing_forecast
            print(f"Using existing forecast {forecast.id}")
        
        # Create DirectDebit if it doesn't exist
        direct_debit = DirectDebit.objects.filter(
            invoice=invoice,
            contract=self,
            forecast=forecast
        ).first()
        
        if not direct_debit:
            print(f"Creating DirectDebit for invoice {invoice.invoice.ref}")
            DirectDebit.objects.create(
                invoice=invoice,
                contract=self,
                bank_account=self.domiciliation_bank,
                due_date=payment_date,
                amount=amount,
                forecast=forecast
            )
        else:
            print(f"DirectDebit already exists: {direct_debit.id}")


    def generate_domiciliation_forecasts(self):
        """Generate a year of forecasts for domiciled contract"""
        if not self.is_domiciled or self.domiciliation_suspended:
            return
                    
        print(f"\n=== Generating Domiciliation Forecasts for Contract {self.id} ===")
        print(f"Contract start date: {self.start_date}")
        print(f"Domiciliation day: {self.domiciliation_day}")
        
        today = timezone.now().date()
        year_end = today + timedelta(days=365)
        
        valid_day = self.get_valid_day(self.start_date.year, self.start_date.month, self.domiciliation_day)
        current_date = self.start_date.replace(day=valid_day)
        if current_date < self.start_date:
            current_date += relativedelta(months=1)
                
        print(f"First payment date: {current_date}")
        
        total_amount = Decimal('0')
        for contract_product in self.products.all():
            product_amount = contract_product.quantity * contract_product.unit_price
            
            if contract_product.reduction_rate:
                reduction = product_amount * (contract_product.reduction_rate / Decimal('100'))
                product_amount -= reduction
            
            vat_amount = product_amount * (contract_product.product.vat_rate / Decimal('100'))
            product_amount += vat_amount
            
            total_amount += product_amount
            
        print(f"Total amount (with VAT): {total_amount}")
        
        while current_date < today:
            payment_date = current_date
            while payment_date.weekday() >= 5:
                payment_date += timedelta(days=1)
                    
            print(f"\nCreating past due forecast for: {payment_date} (Original: {current_date})")
            
            forecast = ForecastStatement.objects.create(
                bank_account=self.domiciliation_bank,
                date=payment_date,
                label=f"Domiciled payment for contract {self.reference}",
                debit=total_amount,
                amount=total_amount,
                reference=f"DOM/{self.reference}/{current_date.strftime('%Y%m')}",
                source_type='contract_domiciliation',
                source_id=self.id,
                is_processed=False
            )

            # ONLY NEW CODE: Create DirectDebit for this forecast
            invoice = ContractInvoice.objects.filter(
                contract=self,
                period_start__year=current_date.year,
                period_start__month=current_date.month
            ).first()

            if invoice:
                DirectDebit.objects.create(
                    invoice=invoice,
                    contract=self,
                    bank_account=self.domiciliation_bank,
                    due_date=payment_date,
                    amount=total_amount,
                    forecast=forecast
                )
            
            if self.periodicity == self.PERIOD_MONTHLY:
                current_date += relativedelta(months=1)
            elif self.periodicity == self.PERIOD_QUARTERLY:
                current_date += relativedelta(months=3)
            elif self.periodicity == self.PERIOD_BIANNUAL:
                current_date += relativedelta(months=6)
            else:
                current_date += relativedelta(years=1)
            
            # Validate day for new month
            valid_day = self.get_valid_day(current_date.year, current_date.month, self.domiciliation_day)
            current_date = current_date.replace(day=valid_day)
        
        while current_date <= year_end:
            payment_date = current_date
            while payment_date.weekday() >= 5:
                payment_date += timedelta(days=1)
                    
            print(f"\nCreating future forecast for: {payment_date} (Original: {current_date})")
                
            forecast = ForecastStatement.objects.create(
                bank_account=self.domiciliation_bank,
                date=payment_date,
                label=f"Domiciled payment for contract {self.reference}",
                debit=total_amount,
                amount=total_amount,
                reference=f"DOM/{self.reference}/{current_date.strftime('%Y%m')}",
                source_type='contract_domiciliation',
                source_id=self.id,
                is_processed=False
            )

            # ONLY NEW CODE: Create DirectDebit for this forecast
            invoice = ContractInvoice.objects.filter(
                contract=self,
                period_start__year=current_date.year,
                period_start__month=current_date.month
            ).first()

            if invoice:
                DirectDebit.objects.create(
                    invoice=invoice,
                    contract=self,
                    bank_account=self.domiciliation_bank,
                    due_date=payment_date,
                    amount=total_amount,
                    forecast=forecast
                )

            if self.periodicity == self.PERIOD_MONTHLY:
                current_date += relativedelta(months=1)
            elif self.periodicity == self.PERIOD_QUARTERLY:
                current_date += relativedelta(months=3)
            elif self.periodicity == self.PERIOD_BIANNUAL:
                current_date += relativedelta(months=6)
            else:
                current_date += relativedelta(years=1)
                
            print(f"Next payment date: {current_date}")
            
    def _get_next_period_date(self, current_date):
        """Get next period date based on contract periodicity"""
        if self.periodicity == self.PERIOD_MONTHLY:
            return current_date + relativedelta(months=1)
        elif self.periodicity == self.PERIOD_QUARTERLY:
            return current_date + relativedelta(months=3)
        elif self.periodicity == self.PERIOD_BIANNUAL:
            return current_date + relativedelta(months=6)
        else:  # annual
            return current_date + relativedelta(years=1)

    def get_valid_day(self, year, month, target_day):
        """Get valid day for the given month, adjusting for month end if necessary"""
        last_day = calendar.monthrange(year, month)[1]
        return min(target_day, last_day)

            
class DirectDebit(BaseModel):
    """Direct debit for a contract invoice"""

    PENDING = 'pending'
    PROCESSED = 'processed'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSED, 'Processed'),
        (REJECTED, 'Rejected')
    ]
    
    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('TECHNICAL_ERROR', 'Technical Error'),
        ('STOP_PAYMENT', 'Stop Payment Order'),
        ('BANK_ERROR', 'Bank Processing Error')
    ]
    
    invoice = models.ForeignKey('ContractInvoice', on_delete=models.PROTECT, null=True, blank=True)
    contract = models.ForeignKey('Contract', on_delete=models.PROTECT, null=True, blank=True)
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    
    due_date = models.DateField()
    processed_date = models.DateField(null=True, blank=True)
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    rejection_cause = models.CharField(
        max_length=50, 
        choices=REJECTION_CAUSES,
        null=True, 
        blank=True
    )
    rejection_date = models.DateField(null=True, blank=True)
    rejection_note = models.TextField(blank=True)
    
    forecast = models.OneToOneField(
        'ForecastStatement', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='direct_debit'
    )
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
    
    class Meta:
        ordering = ['due_date']
        verbose_name = "Direct Debit"
        verbose_name_plural = "Direct Debits"
    
    def __str__(self):
        return f"DirectDebit {self.id} for {self.invoice.invoice.ref}"
        
    def mark_as_processed(self, processed_date):
        print(f"\n=== Processing DirectDebit {self.id} ===")
        print(f"Invoice: {self.invoice.invoice.ref}")
        print(f"Amount: {self.amount}")
        print(f"Process date: {processed_date}")
        
        self.status = self.PROCESSED
        self.processed_date = processed_date
        self.save()
        
        # Update invoice payment status
        self.invoice.invoice.update_payment_status()
        
        # Mark forecast as processed if exists
        if self.forecast:
            print(f"Marking forecast {self.forecast.id} as processed")
            self.forecast.is_processed = True
            self.forecast.save()
        
        print(f"DirectDebit processed successfully")
        
    def mark_as_rejected(self, rejection_date, cause, note=''):
        print(f"\n=== Rejecting DirectDebit {self.id} ===")
        print(f"Invoice: {self.invoice.invoice.ref}")
        print(f"Cause: {cause}")
        print(f"Date: {rejection_date}")
        
        self.status = self.REJECTED
        self.rejection_date = rejection_date
        self.rejection_cause = cause
        self.rejection_note = note
        self.save()
        
        # Update invoice payment status
        self.invoice.invoice.update_payment_status()
        
        # Mark forecast as processed if exists
        if self.forecast:
            print(f"Marking forecast {self.forecast.id} as processed")
            self.forecast.is_processed = True
            self.forecast.save()
            
        print(f"DirectDebit rejected successfully")

    @property
    def presentation_info(self):
        """Get formatted presentation information"""
        return {
            'date': self.due_date,
            'type': 'Direct Debit',
            'bank': self.bank_account,
            'status': self.get_status_display(),
            'rejection_cause': self.get_rejection_cause_display() if self.rejection_cause else None
        }

class IRConfiguration(BaseModel):
    """Configuration for Income Tax (IR) management"""
    accounting_code = models.CharField(
        max_length=10,
        default='44525',
        validators=[
            RegexValidator(r'^\d{4,10}$', 'Account code must be 4-10 digits')
        ],
        help_text="Accounting code for IR operations"
    )
    journal_code = models.CharField(
        max_length=2,
        default='05',
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ]
    )
    domiciliation_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='ir_declarations',
        help_text="Bank account used for IR payments"
    )
    default_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Default IR amount for forecasts"
    )
    declaration_day = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month when IR declarations are due"
    )
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual')
    ]
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='monthly',
        help_text="Frequency of IR declarations"
    )

    @classmethod
    def get_config(cls):
        """Get or create IR configuration"""
        config = IRConfiguration.objects.first()
        if not config:
            raise ValidationError("IR Configuration must be set up")
        return config

    def __str__(self):
        return f"IR Configuration (Bank: {self.domiciliation_bank.bank})"

    class Meta:
        verbose_name = "IR Configuration"
        verbose_name_plural = "IR Configuration"


class IRDeclaration(BaseModel):
    """Income Tax (IR) declaration"""
    STATUS_CHOICES = [
        ('declared', 'Declared'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected')
    ]
    
    period_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    period_year = models.PositiveSmallIntegerField()
    salary_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total salary amount"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total IR tax amount"
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='declared'
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the declaration was paid"
    )
    rejection_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the declaration was rejected"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    forecast = models.ForeignKey(
        'ForecastStatement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ir_declaration'
    )

    def save(self, *args, **kwargs):
        print("\n=== Saving IRDeclaration ===")
        print(f"Period: {self.period_month}/{self.period_year}")
        print(f"Tax amount: {self.tax_amount}")
        
        if not self.due_date:
            config = IRConfiguration.get_config()
            day = config.declaration_day
            
            # Create date with specified day, or last day of month if out of range
            last_day = calendar.monthrange(self.period_year, self.period_month)[1]
            if day > last_day:
                self.due_date = datetime.date(self.period_year, self.period_month, last_day)
            else:
                self.due_date = datetime.date(self.period_year, self.period_month, day)
            
            print(f"Set due date to {self.due_date}")
        
        # Update or create forecast
        self._update_forecast()
        
        super().save(*args, **kwargs)

    def _update_forecast(self):
        """Update or create forecast for this declaration"""
        print("\n=== Updating IR Forecast ===")
        
        # Delete old forecast if exists
        if self.forecast:
            print(f"Deleting old forecast: {self.forecast.id}")
            self.forecast.delete()
            self.forecast = None
        
        # Don't create forecast for paid or rejected declarations
        if self.status in ['paid', 'rejected']:
            print(f"Not creating forecast for {self.status} declaration")
            return
        
        # Delete any existing forecasts for this period (important new step)
        existing_forecasts = ForecastStatement.objects.filter(
            bank_account=IRConfiguration.get_config().domiciliation_bank,
            label__icontains=f"{self.period_month:02d}/{self.period_year}",
            source_type="ir_declaration",
            is_processed=False
        )
        
        if existing_forecasts.exists():
            print(f"Deleting {existing_forecasts.count()} existing forecasts for period {self.period_month:02d}/{self.period_year}")
            existing_forecasts.delete()

        # Create new forecast
        config = IRConfiguration.get_config()
        
        forecast = ForecastStatement.objects.create(
            bank_account=config.domiciliation_bank,
            date=self.due_date,
            label=f"IR Payment {self.period_month:02d}/{self.period_year}",
            debit=self.tax_amount,
            reference=f"IR-{self.period_month:02d}-{self.period_year}",
            source_type="ir_declaration",
            source_id=self.id,
            amount=self.tax_amount
        )
        
        self.forecast = forecast
        print(f"Created new forecast: {forecast.id}")
        
        # Generate next year's forecasts
        self._generate_future_forecasts()

    def _generate_future_forecasts(self):
        """Generate forecasts for the next periods"""
        print("\n=== Generating Future IR Forecasts ===")
        
        config = IRConfiguration.get_config()
        
        # Calculate next periods based on frequency
        next_periods = []
        if config.frequency == 'monthly':
            step_months = 1
        elif config.frequency == 'quarterly':
            step_months = 3
        elif config.frequency == 'biannual':
            step_months = 6
        elif config.frequency == 'annual':
            step_months = 12
        
        # Generate periods for one year ahead
        current_month = self.period_month
        current_year = self.period_year
        
        for _ in range(12 // step_months):
            # Calculate next period
            current_month += step_months
            while current_month > 12:
                current_month -= 12
                current_year += 1
            
            # Check if declaration already exists for this period
            if IRDeclaration.objects.filter(
                period_month=current_month, 
                period_year=current_year
            ).exists():
                print(f"Declaration already exists for {current_month}/{current_year}, skipping")
                continue
            
            # Check if forecast already exists for this period
            try:
                due_date = datetime.date(
                    current_year, 
                    current_month, 
                    min(config.declaration_day, calendar.monthrange(current_year, current_month)[1])
                )
                
                # Check for existing forecast
                existing_forecast = ForecastStatement.objects.filter(
                    source_type="ir_declaration",
                    bank_account=config.domiciliation_bank,
                    date=due_date
                ).first()
                
                if existing_forecast:
                    print(f"Forecast already exists for {current_month}/{current_year}, skipping")
                    continue
                
                # Create forecast with default amount
                ForecastStatement.objects.create(
                    bank_account=config.domiciliation_bank,
                    date=due_date,
                    label=f"IR Forecast {current_month:02d}/{current_year}",
                    debit=config.default_amount,
                    reference=f"IR-{current_month:02d}-{current_year}",
                    source_type="ir_declaration",
                    source_id=uuid.uuid4(),
                    amount=config.default_amount
                )
                print(f"Created forecast for {current_month}/{current_year}")
                
            except Exception as e:
                print(f"Error creating forecast for {current_month}/{current_year}: {str(e)}")

    def mark_as_paid(self, payment_date=None):
        """Mark declaration as paid"""
        print(f"\n=== Marking IR declaration {self.period_month}/{self.period_year} as paid ===")
        
        self.status = 'paid'
        self.payment_date = payment_date or timezone.now().date()
        self.rejection_date = None
        
        # Update forecast (will be deleted)
        self._update_forecast()
        self.save()
        
        # Create bank statement and accounting entries
        config = IRConfiguration.get_config()
        
        # Add to bank statement
        statement_entry = {
            'date': self.payment_date,
            'label': f"IR Payment {self.period_month:02d}/{self.period_year}",
            'type': 'IR_PAYMENT',
            'debit': self.tax_amount,
            'credit': None,
            'reference': f"IR-{self.period_month:02d}-{self.period_year}",
            'source_type': 'ir_declaration',
            'source_id': self.id
        }
        
        # Add to accounting entries
        accounting_entries = [
            {
                'date': self.payment_date,
                'label': f"IR Payment {self.period_month:02d}/{self.period_year}",
                'debit': self.tax_amount,
                'credit': None,
                'account_code': config.accounting_code,
                'reference': f"IR-{self.period_month:02d}-{self.period_year}",
                'journal_code': config.journal_code
            },
            {
                'date': self.payment_date,
                'label': f"IR Payment {self.period_month:02d}/{self.period_year}",
                'debit': None,
                'credit': self.tax_amount,
                'account_code': config.domiciliation_bank.accounting_number,
                'reference': f"IR-{self.period_month:02d}-{self.period_year}",
                'journal_code': config.journal_code
            }
        ]
        
        print("IR declaration marked as paid")

    def mark_as_rejected(self, rejection_date=None):
        """Mark declaration as rejected"""
        print(f"\n=== Marking IR declaration {self.period_month}/{self.period_year} as rejected ===")
        
        self.status = 'rejected'
        self.rejection_date = rejection_date or timezone.now().date()
        self.payment_date = None
        
        # Update forecast (will be deleted)
        self._update_forecast()
        self.save()
        
        print("IR declaration marked as rejected")

    def __str__(self):
        return f"IR Declaration {self.period_month:02d}/{self.period_year}"

    class Meta:
        ordering = ['-period_year', '-period_month']
        unique_together = ['period_month', 'period_year']
        verbose_name = "IR Declaration"
        verbose_name_plural = "IR Declarations"