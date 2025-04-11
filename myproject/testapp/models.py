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

class item(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()    
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class UserRole(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Permissions for different sections
    can_manage_users = models.BooleanField(default=False)
    can_view_bank = models.BooleanField(default=False)
    can_manage_bank = models.BooleanField(default=False)
    can_view_checks = models.BooleanField(default=False)
    can_manage_checks = models.BooleanField(default=False)
    can_view_clients = models.BooleanField(default=False)
    can_manage_clients = models.BooleanField(default=False)
    can_view_suppliers = models.BooleanField(default=False)
    can_manage_suppliers = models.BooleanField(default=False)
    can_view_products = models.BooleanField(default=False)
    can_manage_products = models.BooleanField(default=False)
    can_view_invoices = models.BooleanField(default=False)
    can_manage_invoices = models.BooleanField(default=False)
    can_view_receipts = models.BooleanField(default=False)
    can_manage_receipts = models.BooleanField(default=False)
    can_view_contracts = models.BooleanField(default=False)
    can_manage_contracts = models.BooleanField(default=False)
    can_view_bank_accounts = models.BooleanField(default=False)
    can_manage_bank_accounts = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.role.name})"

class UserActivity(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    target_model = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50, null=True, blank=True)
    details = models.JSONField(null=True)
    ip_address = models.GenericIPAddressField(null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"
    
class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

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

class Product(BaseModel):
    name = models.CharField(max_length=100)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, choices=[
        (Decimal('0.00'), '0%'),
        (Decimal('7.00'), '7%'), 
        (Decimal('10.00'), '10%'),
        (Decimal('11.00'), '11%'),
        (Decimal('14.00'), '14%'),
        (Decimal('16.00'), '16%'),
        (Decimal('20.00'), '20%')
    ])
    # Remove the validator from the model field
    expense_code = models.CharField(max_length=25)
    is_energy = models.BooleanField(default=False)
    fiscal_label = models.CharField(max_length=255, blank=False)
    is_asset = models.BooleanField(
        default=False,
        help_text=_("If true, this product is treated as an asset")
    )
    asset_account = models.ForeignKey(
        'AssetAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_("Required if product is an asset")
    )
    non_deductible_vat = models.BooleanField(
        default=False,
        help_text=_("If true, VAT from this product cannot be deducted")
    )

    def clean(self):
        super().clean()
        if self.is_asset:
            if not self.asset_account:
                raise ValidationError(_("Asset account is required for assets"))
            # For assets, validate 4-digit minimum
            if not re.match(r'^[0-9]{4,}$', str(self.expense_code)):
                raise ValidationError({
                    'expense_code': _("Asset account code must be numeric and at least 4 characters long.")
                })
        else:
            if self.asset_account:
                raise ValidationError(_("Asset account can only be set for assets"))
            if not self.expense_code:
                raise ValidationError(_("Expense code is required for non-asset products"))
            # For non-assets, validate 5-digit minimum
            if not re.match(r'^[0-9]{5,}$', str(self.expense_code)):
                raise ValidationError({
                    'expense_code': _("Expense code must be numeric and at least 5 characters long.")
                })

    class Meta:
        # Allow products with same name but different types
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'is_asset'],
                name='unique_product_name_per_type'
            )
        ]

class AssetAccount(BaseModel):
    account_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^2\d{3,4}$', _('Asset account must start with 2 and have 4-5 digits'))
        ],
        unique=True
    )
    depreciation_account = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^2\d{3,4}$', _('Depreciation account must start with 2 and have 4-5 digits'))
        ],
        unique=True
    )
    allowance_account = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^6\d{3,4}$', _('Allowance account must start with 6 and have 4-5 digits'))
        ],
        unique=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    depreciation_period = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(20)
        ],
        help_text=_("Depreciation period in years")
    )

    class Meta:
        ordering = ['name']
        verbose_name = _("Asset Account")
        verbose_name_plural = _("Asset Accounts")

    def __str__(self):
        return f"{self.name} ({self.account_code})"

    def clean(self):
        super().clean()
        # Ensure accounts are different
        if len({self.account_code, self.depreciation_account, self.allowance_account}) != 3:
            raise ValidationError(_("Asset, depreciation and allowance accounts must be different"))
        
class DocumentBase(BaseModel):
    """
    Base model for documents with common fields and functionality
    """
    ref = models.CharField(max_length=50)
    date = models.DateField()
    supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.PROTECT,
        related_name='%(class)s_notes',
        null=True  # TEMPORARY
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    document = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.get_document_type()} {self.ref} ({self.date})"

    def get_document_type(self):
        return self.__class__.__name__

    @property
    def document_url(self):
        return self.document.url if self.document else None

    @property
    def filename(self):
        return os.path.basename(self.document.name) if self.document else None

    def clean(self):
        super().clean()
        if self.document and not self.document.name.lower().endswith('.pdf'):
            raise ValidationError(_("Only PDF files are allowed."))

class DeliveryNote(DocumentBase):
    """Bon de livraison"""
    class Meta:
        ordering = ['-date', 'ref']
        constraints = [
            models.UniqueConstraint(
                fields=['ref'],
                name='unique_delivery_note_ref'
            )
        ]

    def get_document_type(self):
        return "BL"

class ReceptionNote(DocumentBase):
    """Bon de réception"""
    class Meta:
        ordering = ['-date', 'ref']
        constraints = [
            models.UniqueConstraint(
                fields=['ref'],
                name='unique_reception_note_ref'
            )
        ]

    def get_document_type(self):
        return "BR"

class Invoice(BaseModel):
    INVOICE_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('credit_note', 'Credit Note'),
    ]
    ref = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=25, choices=[('draft', 'Draft'), ('final', 'Finalized'), ('paid', 'Paid')], default='draft'
    )
    payment_due_date = models.DateField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    export_history = models.ManyToManyField('ExportRecord', blank=True, related_name='invoices')
    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPES,
        default='OTHER'
    )
    doc_status = models.CharField(
        max_length=10,
        choices=INVOICE_STATUS,
        default='ORIGINAL'
    )
    special_index = models.IntegerField(null=True, blank=True)
    document = models.FileField(
        upload_to=get_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    delivery_notes = models.ManyToManyField(
        DeliveryNote,
        blank=True,
        related_name='invoices'
    )
    reception_notes = models.ManyToManyField(
        ReceptionNote,
        blank=True,
        related_name='invoices'
    )


    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid')
    ]

    payment_status = models.CharField(
        max_length=25,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_paid'
    )
    
    type = models.CharField(
        max_length=25,
        choices=INVOICE_TYPE_CHOICES,
        default='invoice'
    )

    
    vat_deduction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text=_("Percentage of VAT that can be deducted")
    )

    non_deductible_vat = models.BooleanField(
        default=False,
        help_text=_("If true, VAT from this invoice cannot be deducted")
    )

    original_invoice = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='credit_notes'
    )
    cash_payment_allowed = models.BooleanField(
        default=False,
        help_text="If True, this invoice can be paid by cash"
    )

    def save(self, *args, **kwargs):
        print(f"\n=== Saving Invoice {self.ref} ===")
        print(f"Cash payment allowed: {self.cash_payment_allowed}")
        if not self.special_index:
            # Get the last index for this type this year
            year = self.date.year
            last_index = Invoice.objects.filter(
                invoice_type=self.invoice_type,
                date__year=year
            ).aggregate(Max('special_index'))['special_index__max'] or 0
            self.special_index = last_index + 1

        if self.type == 'invoice':  # Only calculate payment_due_date for regular invoices
            if not self.payment_due_date:
                self.payment_due_date = self.date + timedelta(days=self.supplier.delay_convention)
        else:  # For credit notes
            self.payment_due_date = None

        super().save(*args, **kwargs)
    
    @property
    def archive_index(self):
        """Returns the formatted archive index"""
        return f"{self.special_index}-{self.date.strftime('%y')}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(
                    Q(type='invoice', original_invoice__isnull=True) |
                    Q(type='credit_note', original_invoice__isnull=False)
                ),
                name='credit_note_must_have_original_invoice'
            )
        ]
        permissions = [
        ("can_export_invoice", "Can export invoice"),
        ("can_unexport_invoice", "Can unexport invoice"),
        ]

    @property
    def fiscal_label(self):
        """Generate a combined fiscal label from all related products."""
        products = [(item.product.fiscal_label, item.quantity * item.unit_price) 
                    for item in self.products.all()]
        unique_labels = []
        seen = set()
        
        # Sort by value and get unique labels
        for label, _ in sorted(products, key=lambda x: x[1], reverse=True):
            if label not in seen:
                unique_labels.append(label)
                seen.add(label)
        
        top_labels = unique_labels[:3]
        if len(unique_labels) > 3:
            top_labels.append('...')
        
        return " - ".join(top_labels)
    
    @property
    def raw_amount(self):
        """Calculate the total amount before tax, considering reduction rate for each product."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100))
                for item in self.products.all()
            ]
        )

    @property
    def total_tax_amount(self):
        """Calculate the total tax amount for the invoice considering different VAT rates."""
        return sum(
            [
                (item.quantity * item.unit_price * (1 - item.reduction_rate / 100) * item.vat_rate / 100)
                for item in self.products.all()
            ]
        )

    @property
    def total_amount(self):
        """Calculate the total amount of the invoice including tax."""
        from decimal import Decimal
        try:
            raw = sum(
                [
                    (item.quantity * item.unit_price * (1 - item.reduction_rate / 100))
                    for item in self.products.all()
                ]
            )
            tax = sum(
                [
                    (item.quantity * item.unit_price * (1 - item.reduction_rate / 100) * item.vat_rate / 100)
                    for item in self.products.all()
                ]
            )
            return Decimal(str(raw + tax))
        except Exception as e:
            print(f"Error calculating total_amount: {e}")
            return Decimal('0')
    
    @property
    def net_amount(self):
        """Calculate net amount after credit notes"""
        credit_notes_total = sum(
            cn.total_amount for cn in self.credit_notes.all()
        )
        return self.total_amount - credit_notes_total

    @property
    def has_credit_notes(self):
        """Check if invoice has any credit notes"""
        return self.credit_notes.exists()
    
    @property
    def can_be_credited(self):
        """Check if invoice can have more credit notes"""
        if self.type == 'credit_note':
            return False
        if self.payment_status == 'paid':
            return False
        credit_notes_total = sum(cn.total_amount for cn in self.credit_notes.all())
        return credit_notes_total < self.total_amount
    
    def get_cash_payment_status(self):
        """Get cash payment details"""
        total_cash_paid = sum(
            payment.amount for payment in self.cash_payments.all()
        )
        return {
            'total_paid': total_cash_paid,
            'remaining': max(Decimal('0.00'), self.total_amount - total_cash_paid)
        }

    def clean(self):
        """Custom clean method to validate credit notes"""
        super().clean()
        if self.pk:  # Only check if invoice exists
            delivery_refs = self.delivery_notes.values_list('ref', flat=True)
            if len(delivery_refs) != len(set(delivery_refs)):
                raise ValidationError(_("Duplicate delivery notes are not allowed"))
            
            reception_refs = self.reception_notes.values_list('ref', flat=True)
            if len(reception_refs) != len(set(reception_refs)):
                raise ValidationError("Duplicate reception notes are not allowed")
            
        if self.type == 'credit_note':
            if not self.original_invoice:
                raise ValidationError(_("Credit note must reference an original invoice"))
            if self.original_invoice.type != 'invoice':
                raise ValidationError(_("Cannot create credit note for another credit note"))
            if self.supplier != self.original_invoice.supplier:
                raise ValidationError(_("Credit note must have same supplier as original invoice"))
        
        if self.cash_payment_allowed and self.total_amount > Decimal('5000.00'):
            raise ValidationError("Invoices over 5000 cannot be paid by cash")
    
    @property
    def has_documents(self):
        """Check if invoice has any documents attached"""
        return bool(
            self.document or 
            self.delivery_notes.filter(document__isnull=False).exists() or
            self.reception_notes.filter(document__isnull=False).exists()
        )

    def get_all_documents(self):
        """Get all related documents"""
        documents = []
        if self.document:
            documents.append({
                'type': 'Invoice',
                'ref': self.ref,
                'date': self.date,
                'url': self.document.url,
                'filename': os.path.basename(self.document.name)
            })
        
        for note in self.delivery_notes.all():
            if note.document:
                documents.append({
                    'type': 'BL',
                    'ref': note.ref,
                    'date': note.date,
                    'url': note.document.url,
                    'filename': note.filename
                })
        
        for note in self.reception_notes.all():
            if note.document:
                documents.append({
                    'type': 'BR',
                    'ref': note.ref,
                    'date': note.date,
                    'url': note.document.url,
                    'filename': note.filename
                })
        
        return sorted(documents, key=lambda x: x['date'], reverse=True)

    def get_credited_quantities(self):
        """Get total credited quantities per product"""
        credited_quantities = {}
        for credit_note in self.credit_notes.all():
            for item in credit_note.products.all():
                if item.product_id in credited_quantities:
                    credited_quantities[item.product_id] += item.quantity
                else:
                    credited_quantities[item.product_id] = item.quantity
        return credited_quantities

    def get_available_quantities(self):
        """Get available quantities that can still be credited"""
        original_quantities = {
            item.product_id: item.quantity 
            for item in self.products.all()
        }
        credited_quantities = self.get_credited_quantities()
        
        return {
            product_id: original_quantities[product_id] - credited_quantities.get(product_id, 0)
            for product_id in original_quantities
        }

    def get_accounting_entries(self):
        entries = []
        sign = -1 if self.type == 'credit_note' else 1
        expense_groups = {}
        asset_groups = {}
        tax_groups = {}

        print("\n=== Generating Accounting Entries ===")
        print(f"Invoice: {self.ref}")
        
        for invoice_product in self.products.all():
            if self.is_loan_invoice() and self.payment_status != 'paid':
                print("Loan invoice not paid yet, skipping accounting entries")
                return entries

            print(f"\nProcessing product: {invoice_product.product.name}")
            print(f"Is asset: {invoice_product.product.is_asset}")
            
            # Calculate product value
            product_value = (
                invoice_product.quantity * 
                invoice_product.unit_price * 
                (1 - invoice_product.reduction_rate / 100) * 
                sign
            )
            print(f"Product value: {product_value}")

            if invoice_product.product.is_asset:
                # Group by asset account
                asset_account = invoice_product.product.asset_account
                key = asset_account.account_code
                if key not in asset_groups:
                    asset_groups[key] = {
                        'products': {},
                        'amount': 0,
                        'asset_account': asset_account,
                        'is_energy': invoice_product.product.is_energy
                    }
                asset_groups[key]['products'][invoice_product.product.name] = product_value
                asset_groups[key]['amount'] += product_value
                print(f"Added to asset group: {key}")
            else:
                # Group by expense code
                key = invoice_product.product.expense_code
                if key not in expense_groups:
                    expense_groups[key] = {
                        'products': {},
                        'amount': 0,
                        'is_energy': invoice_product.product.is_energy
                    }
                expense_groups[key]['products'][invoice_product.product.name] = product_value
                expense_groups[key]['amount'] += product_value
                print(f"Added to expense group: {key}")

            # Group taxes
            tax_key = invoice_product.vat_rate
            if tax_key not in tax_groups:
                tax_groups[tax_key] = 0
            tax_groups[tax_key] += (product_value * invoice_product.vat_rate / 100)
            print(f"Added VAT: {tax_key}% - {product_value * invoice_product.vat_rate / 100}")

        # Add expense entries
        prefix = "CN -" if self.type == 'credit_note' else ""
        print("\nProcessing expense groups:")
        for expense_code, data in expense_groups.items():
            sorted_products = sorted(data['products'].items(), key=lambda x: x[1], reverse=True)
            unique_products = []
            seen = set()
            for name, _ in sorted_products:
                if name not in seen:
                    unique_products.append(name)
                    seen.add(name)
            
            product_names = unique_products[:3]
            if len(sorted_products) > 3:
                product_names.append('...')

            entries.append({
                'date': self.date,
                'label': f"{prefix} {', '.join(product_names)}",
                'debit': data['amount'] if sign > 0 else None,
                'credit': abs(data['amount']) if sign < 0 else None,
                'account_code': expense_code,
                'reference': self.ref,
                'journal': '10' if data['is_energy'] else '01',
                'counterpart': ''
            })
            print(f"Added expense entry: {expense_code} - {data['amount']}")

        # Add asset entries
        print("\nProcessing asset groups:")
        for asset_code, data in asset_groups.items():
            sorted_products = sorted(data['products'].items(), key=lambda x: x[1], reverse=True)
            unique_products = []
            seen = set()
            for name, _ in sorted_products:
                if name not in seen:
                    unique_products.append(name)
                    seen.add(name)
            
            product_names = unique_products[:3]
            if len(sorted_products) > 3:
                product_names.append('...')

            # Asset entry
            entries.append({
                'date': self.date,
                'label': f"{prefix} {', '.join(product_names)} (Asset)",
                'debit': data['amount'] if sign > 0 else None,
                'credit': abs(data['amount']) if sign < 0 else None,
                'account_code': asset_code,
                'reference': self.ref,
                'journal': '20',  # Asset journal
                'counterpart': ''
            })
            print(f"Added asset entry: {asset_code} - {data['amount']}")

        # Add VAT entries
        print("\nProcessing VAT entries:")
        for rate, amount in tax_groups.items():
            if rate > 0:
                entries.append({
                    'date': self.date,
                    'label': f'VAT {int(rate)}%',
                    'debit': amount if sign > 0 else None,
                    'credit': abs(amount) if sign < 0 else None,
                    'account_code': f'345{int(rate):02d}',
                    'reference': self.ref,
                    'journal': '10' if self.supplier.is_energy else '01',
                    'counterpart': ''
                })
                print(f"Added VAT entry: {rate}% - {amount}")

        # Add supplier entry
        entries.append({
            'date': self.date,
            'label': self.supplier.name,
            'debit': abs(self.total_amount) if sign < 0 else None,
            'credit': self.total_amount if sign > 0 else None,
            'account_code': self.supplier.accounting_code,
            'reference': self.ref,
            'journal': '10' if self.supplier.is_energy else '01',
            'counterpart': ''
        })
        print(f"Added supplier entry: {self.total_amount}")

        print(f"\nTotal entries generated: {len(entries)}")
        return entries
    
    @property
    def amount_available_for_payment(self):
        """Calculate amount still available for payment"""
        net_amount = self.net_amount
        
        # Calculate total from direct checks - including draft
        direct_checks_amount = sum(
            check.amount 
            for check in Check.objects.filter(
                cause=self
            ).exclude(
                status='cancelled'  # Only exclude cancelled checks
            )
        ) or Decimal('0')
        
        # Calculate total from allocated checks - including draft
        allocated_amount = sum(
            allocation.amount 
            for allocation in CheckAllocation.objects.filter(
                invoice=self
            ).exclude(
                payment__status='cancelled'  # Only exclude cancelled allocations
            )
        ) or Decimal('0')
        
        # Calculate total payments and available amount
        total_payments = direct_checks_amount + allocated_amount
        return max(Decimal('0'), net_amount - total_payments)
    
    def get_payment_details(self):
        """Calculate comprehensive payment details"""
        print("\n=== Getting Payment Details ===")
        print(f"Invoice: {self.ref}")
        
        # Get all non-cancelled checks for this invoice
        valid_checks = Check.objects.filter(
            cause=self
        ).exclude(
            status='cancelled'
        )
        print(f"Direct checks found: {valid_checks.count()}")

        # Calculate direct payment amounts
        pending_amount = sum(c.amount for c in valid_checks.filter(status='pending'))
        delivered_amount = sum(c.amount for c in valid_checks.filter(status='delivered'))
        paid_amount = sum(c.amount for c in valid_checks.filter(status='paid'))
        total_issued = sum(c.amount for c in valid_checks)

        print(f"Direct payments - Pending: {pending_amount}, Delivered: {delivered_amount}, Paid: {paid_amount}")

        # Get allocations
        print(f"Looking for allocations with invoice_id: {self.id}")
        allocations = CheckAllocation.objects.filter(invoice_id=self.id)
        print(f"Raw allocations found: {allocations.count()}")
        print("Allocation details:")
        for alloc in allocations:
            print(f"Allocation ID: {alloc.id}")
            print(f"Check ID: {alloc.payment.id if hasattr(alloc, 'payment') else 'No payment'}")
            print(f"Check status: {alloc.payment.status if hasattr(alloc, 'payment') else 'No status'}")

        # Get valid allocations
        valid_allocations = CheckAllocation.objects.filter(
            invoice_id=self.id,
            payment__status__in=['pending', 'delivered', 'paid', 'draft']
        ).select_related('payment')
        print(f"Allocations found: {valid_allocations.count()}")

        # Add allocated amounts
        alloc_pending = sum(a.amount for a in valid_allocations.filter(payment__status='pending'))
        alloc_delivered = sum(a.amount for a in valid_allocations.filter(payment__status='delivered'))
        alloc_paid = sum(a.amount for a in valid_allocations.filter(payment__status='paid'))
        total_allocated = sum(a.amount for a in valid_allocations)

        print(f"Allocated payments - Pending: {alloc_pending}, Delivered: {alloc_delivered}, Paid: {alloc_paid}")

        cash_payments = self.cash_payments.all()
        cash_paid_amount = sum(payment.amount for payment in cash_payments)
        print(f"Cash payments found: {cash_payments.count()}, Total: {cash_paid_amount}")

        # Get contract payments if this is a contract invoice
        direct_debit_amount = Decimal('0')
        direct_debit_details = None
        contract_invoice = ContractInvoice.objects.filter(invoice=self).select_related('contract', 'contract__domiciliation_bank').first()

        if contract_invoice and contract_invoice.contract.is_domiciled:
            print(f"Found contract invoice for contract: {contract_invoice.contract.reference}")
            
            # Get all non-rejected direct debits to subtract from amount_to_issue
            non_rejected_debits = DirectDebit.objects.filter(
                invoice=contract_invoice
            ).exclude(status=DirectDebit.REJECTED)
            
            # Subtract from total_issued (both pending and processed)
            total_issued += sum(dd.amount for dd in non_rejected_debits)
            
            direct_debit_details = {
                'contract_ref': contract_invoice.contract.reference,
                'bank': contract_invoice.contract.domiciliation_bank.bank,
                'account': contract_invoice.contract.domiciliation_bank.account_number,
            }
        
        

        # Update totals with allocations only (direct debits handled in view)
        pending_amount += alloc_pending
        delivered_amount += alloc_delivered
        paid_amount += alloc_paid + cash_paid_amount
        total_issued += total_allocated + cash_paid_amount

        net_amount = self.net_amount
        amount_to_issue = net_amount - total_issued  # Now total_issued includes non-rejected direct debits
        remaining_to_pay = net_amount - paid_amount
        payment_percentage = (paid_amount / net_amount * 100) if net_amount else 0

        print(f"Final totals:")
        print(f"Net amount: {net_amount}")
        print(f"Total issued: {total_issued}")
        print(f"Amount to issue: {amount_to_issue}")
        print(f"Remaining to pay: {remaining_to_pay}")
        print(f"Payment percentage: {payment_percentage}%")

        # Prepare check details
        checks = []
        
        # Add direct checks
        for check in valid_checks:
            checks.append({
                'id': str(check.id),
                'type': 'direct',
                'reference': f"{check.checker.bank_account.bank}-{check.position}",
                'amount': float(check.amount),
                'status': check.status,
                'created_at': check.creation_date.strftime('%Y-%m-%d'),
                'delivered_at': check.delivered_at.strftime('%Y-%m-%d') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%d') if check.paid_at else None,
            })
        
        # Add allocated checks
        for allocation in valid_allocations:
            checks.append({
                'id': str(allocation.payment.id),
                'type': 'allocation',
                'reference': f"{allocation.payment.checker.bank_account.bank}-{allocation.payment.position}",
                'total_amount': float(allocation.payment.amount),
                'allocated_amount': float(allocation.amount),
                'status': allocation.payment.status,
                'created_at': allocation.payment.creation_date.strftime('%Y-%m-%d'),
                'delivered_at': allocation.payment.delivered_at.strftime('%Y-%m-%d') if allocation.payment.delivered_at else None,
                'paid_at': allocation.payment.paid_at.strftime('%Y-%m-%d') if allocation.payment.paid_at else None,
            })
        
        for payment in cash_payments:
            checks.append({
                'id': str(payment.id),
                'type': 'cash',
                'reference': payment.reference,
                'amount': float(payment.amount),
                'status': 'paid',
                'created_at': payment.payment_date.strftime('%Y-%m-%d'),
                'delivered_at': payment.payment_date.strftime('%Y-%m-%d'),
                'paid_at': payment.payment_date.strftime('%Y-%m-%d'),
            })

        print(f"Total checks to display: {len(checks)}")
        print("=== End Payment Details ===\n")

        return {
            'total_amount': float(net_amount),
            'pending_amount': float(pending_amount),
            'delivered_amount': float(delivered_amount),
            'paid_amount': float(paid_amount),
            'amount_to_issue': float(amount_to_issue),
            'remaining_to_pay': float(remaining_to_pay),
            'payment_percentage': float(payment_percentage),
            'payment_status': self.get_payment_status(paid_amount),
            'checks': checks,
            'direct_debit': direct_debit_details,
            'direct_debit_amount': float(direct_debit_amount)
        }
    def get_payment_status(self, paid_amount=None):
        """Determine payment status based on paid amount"""
        if paid_amount is None:
            paid_amount = sum(c.amount for c in Check.objects.filter(
                cause=self, 
                status='paid'
            ).exclude(status='cancelled'))    

        if paid_amount >= self.total_amount:
            return 'paid'
        elif paid_amount > 0:
            return 'partially_paid'
        return 'not_paid'


    @property
    def payments_summary(self):
        payments = Check.objects.filter(cause=self).exclude(status='cancelled')
        return {
            'pending_amount': sum(p.amount for p in payments.filter(status='pending')),
            'delivered_amount': sum(p.amount for p in payments.filter(status='delivered')),
            'paid_amount': sum(p.amount for p in payments.filter(status='paid')),
            'percentage_paid': (sum(p.amount for p in payments.filter(status='paid')) / self.total_amount * 100) if self.total_amount else 0,
            'remaining_amount': self.total_amount - sum(p.amount for p in payments.filter(status='paid')),
            'amount_to_issue': self.total_amount - sum(p.amount for p in payments.exclude(status='cancelled'))
        }

    def update_payment_status(self):
        """Update payment status based on all payment types"""
        print(f"\n=== Updating Payment Status for Invoice {self.ref} ===")
        total_payments = Decimal('0')
        
        # Direct check payments - only count PAID checks
        direct_checks = Check.objects.filter(
            cause=self,
            status='paid'  # Only count paid checks
        ).exclude(
            status='cancelled'
        )
        total_payments += sum(check.amount for check in direct_checks)
        
        # Allocated payments - only count from PAID checks
        allocations = CheckAllocation.objects.filter(
            invoice=self,
            payment__status='paid'  # Only count allocations from paid checks
        )
        total_payments += sum(allocation.amount for allocation in allocations)

        # Cash payments
        cash_payments = CashPayment.objects.filter(invoice=self)
        total_payments += sum(payment.amount for payment in cash_payments)

        contract_invoice = hasattr(self, 'contract_invoice') and self.contract_invoice
        if contract_invoice:
            direct_debit_paid = DirectDebit.objects.filter(
                invoice=contract_invoice,
                status=DirectDebit.PROCESSED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            print(f"Direct debit payments: {direct_debit_paid}")
            total_payments += direct_debit_paid
        
        # Determine status
        if total_payments >= self.net_amount:
            self.payment_status = 'paid'
        elif total_payments > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'not_paid'
            
        self.save()

    def calculate_vat_details(self):
        """Calculate VAT amounts by rate, considering credit notes"""
        print("\n=== Calculating VAT Details ===")
        print(f"Invoice: {self.ref}")
        
        vat_details = {}
        
        # Group by VAT rate
        for product in self.products.all():
            if product.product.non_deductible_vat:
                print(f"Skipping non-deductible product: {product.product.name}")
                continue
                
            rate = product.vat_rate
            if rate not in vat_details:
                vat_details[rate] = {
                    'original_amount': Decimal('0.00'),
                    'original_vat': Decimal('0.00'),
                    'credit_amount': Decimal('0.00'),
                    'credit_vat': Decimal('0.00')
                }
            
            # Calculate original amounts
            subtotal = round(product.quantity * product.unit_price * 
                    (1 - product.reduction_rate / 100), 2)
            vat_amount = round(subtotal * (rate / Decimal('100.00')), 2)
            
            print(f"\nProduct: {product.product.name}")
            print(f"VAT Rate: {rate}%")
            print(f"Original Amount: {subtotal}")
            print(f"VAT Amount: {vat_amount}")
            
            vat_details[rate]['original_amount'] += subtotal
            vat_details[rate]['original_vat'] += vat_amount
            
            # Process credit notes
            for credit_note in self.credit_notes.all():
                for credited_product in credit_note.products.filter(product=product.product):
                    credit_subtotal = (credited_product.quantity * 
                                    credited_product.unit_price *
                                    (1 - credited_product.reduction_rate / 100))
                    credit_vat = round(credit_subtotal * (rate / Decimal('100.00')), 2)
                    
                    print(f"\nCredit Note: {credit_note.ref}")
                    print(f"Credited Amount: {credit_subtotal}")
                    print(f"Credited VAT: {credit_vat}")
                    
                    vat_details[rate]['credit_amount'] += credit_subtotal
                    vat_details[rate]['credit_vat'] += credit_vat
        
        # Calculate net amounts
        for rate_details in vat_details.values():
            rate_details['net_amount'] = (
                rate_details['original_amount'] - rate_details['credit_amount']
            )
            rate_details['net_vat'] = (
                rate_details['original_vat'] - rate_details['credit_vat']
            )
        
        print("\nFinal VAT Details:")
        for rate, details in vat_details.items():
            print(f"\nRate {rate}%:")
            print(f"Net Amount: {details['net_amount']}")
            print(f"Net VAT: {details['net_vat']}")
        
        return vat_details

    def calculate_payment_vat(self, payment_amount):
        """Calculate VAT for a specific payment amount"""
        print(f"\n=== Calculating VAT for Payment {payment_amount} ===")
        
        #setting deduction rate to 100%
        self.vat_deduction_rate = Decimal('100.00')

        payment_percentage = round(payment_amount / self.total_amount, 4)
        print(f"Payment Amount: {payment_amount}")
        print(f"Total Amount: {self.total_amount}")
        print(f"Payment Percentage: {payment_percentage}")
        
        vat_details = self.calculate_vat_details()
        payment_vat = {}
        
        for rate, details in vat_details.items():
            deductible_vat = (
                details['net_vat'] * 
                payment_percentage * 
                (self.vat_deduction_rate / Decimal('100.00'))
            )
            
            print(f"\nRate {rate}%:")
            print(f"Net VAT: {round(details['net_vat'], 2)}")
            print(f"payment_percentage: {round(payment_percentage, 2)}")
            print(f"deduction_rate: {round(self.vat_deduction_rate, 2)}")
            print(f"Deductible VAT: {round(deductible_vat, 2)}")
            
            payment_vat[rate] = {
                'amount': details['net_amount'] * payment_percentage,
                'vat': deductible_vat
            }
        
        return payment_vat

    def is_loan_invoice(self):
        """Check if this is a loan invoice"""
        return self.invoice_type == 'LOAN'

    def get_remaining_amount(self):
        """Get remaining amount to be paid"""
        # Get total from cash payments
        cash_payments_total = Decimal('0')
        for payment in self.cash_payments.all():
            cash_payments_total += payment.amount
        
        # Get total from other payment types (checks, etc.)
        other_payments = self.get_payment_details()['paid_amount']
        
        # Return remaining amount
        return max(Decimal('0'), self.total_amount - cash_payments_total - other_payments)

    def __str__(self):
        return f'Invoice {self.ref} from {self.supplier.name}'

class InvoiceProduct(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    reduction_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=[
        (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
    ], default=20.00)
    treated_as_asset = models.BooleanField(
        default=False,
        help_text=_("Indicates if this product was treated as an asset in this invoice")
    )
    @property
    def subtotal(self):
        discount = (self.unit_price * self.quantity) * (self.reduction_rate / 100)
        return (self.unit_price * self.quantity) - discount

    @property
    def total_amount(self):
        return self.subtotal + (self.subtotal * (self.vat_rate / 100))

    def save(self, *args, **kwargs):
        if self.vat_rate == 0.00:
            self.vat_rate = self.product.vat_rate
        if not self.pk:
            self.treated_as_asset = self.product.is_asset
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.product.name} on Invoice {self.invoice.ref}'
    
class ExportRecord(BaseModel):
    exported_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Export {self.filename} at {self.exported_at}"

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

    
class CheckAllocation(BaseModel):
    """Tracks how supplier payments are allocated to invoices"""
    payment = models.ForeignKey(
        Check, 
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.PROTECT,
        related_name='check_allocations'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name='check_allocation_positive'
            )
        ]
    
    def clean(self):
        # Ensure allocation is for a supplier payment
        if not self.payment.is_supplier_payment:  
            raise ValidationError(_("Can only allocate supplier payments"))
            
        # Ensure invoice matches check's beneficiary
        if self.invoice.supplier != self.payment.beneficiary:  
            raise ValidationError(_("Invoice must belong to check's beneficiary"))
            
        # Ensure we don't exceed available amount
        available = self.payment.get_available_amount()  
        if self.amount > available:
            raise ValidationError(
                _(f"Amount {self.amount} exceeds available amount {available}")
            )
            
        # Ensure we don't exceed invoice's available amount
        if self.amount > self.invoice.amount_available_for_payment:
            raise ValidationError(_("Amount exceeds invoice's available amount"))

class BankCheckTemplate(BaseModel):
    bank = models.CharField(max_length=4, choices=MOROCCAN_BANKS)
    check_type = models.CharField(max_length=3, choices=[('CHQ', 'Cheque'), ('LCN', 'LCN')])
    template_data = models.JSONField(default=dict)  # Stores positions for each field

    class Meta:
        unique_together = ['bank', 'check_type']


class CashConfiguration(BaseModel):
    """Configuration for cash management"""
    accounting_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ],
        help_text="Main account code for cash operations"
    )
    journal_code = models.CharField(
        max_length=2,
        default='08',  # Using 08 for cash journal
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ]
    )
    current_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    max_payment_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('5000.00')
    )

    def clean(self):
        super().clean()
        if self.pk and CashConfiguration.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one cash configuration can exist")

    def save(self, *args, **kwargs):
        print("\n=== Saving CashConfiguration ===")
        print(f"Current balance: {self.current_balance}")
        print(f"Max threshold: {self.max_payment_threshold}")
        
        if not self.pk and CashConfiguration.objects.exists():
            raise ValidationError("Only one cash configuration can exist")
            
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create cash configuration"""
        config = CashConfiguration.objects.first()
        if not config:
            raise ValidationError("Cash Configuration must be set up")
        return config

    def __str__(self):
        return f"Cash Configuration (Balance: {self.current_balance})"

class CashDeposit(BaseModel):
    """Records cash deposits to increase cash reserve"""
    SOURCE_TYPE_CHOICES = [
        ('bank', 'Bank Account'),
        ('other', 'Other Source')
    ]
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique reference number for this deposit"
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='cash_deposits'
    )
    
    # New fields for source tracking
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_TYPE_CHOICES,
        default='other'
    )
    source_bank_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cash_withdrawals'
    )
    source_account_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Accounting code for the source account"
    )

    def save(self, *args, **kwargs):
        print("\n=== Saving CashDeposit ===")
        print(f"Amount: {self.amount}")
        print(f"Date: {self.date}")
        print(f"Reference: {self.reference}")
        print(f"Source Type: {self.source_type}")
        
        # Update cash balance
        config = CashConfiguration.get_config()
        config.current_balance += self.amount
        config.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        print("\n=== Deleting CashDeposit ===")
        print(f"Amount: {self.amount}")
        
        # Revert cash balance
        config = CashConfiguration.get_config()
        config.current_balance -= self.amount
        config.save()
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Cash Deposit {self.reference} - {self.amount}"

    class Meta:
        ordering = ['-date', '-created_at']

class CashPayment(BaseModel):
    """Records cash payments for invoices"""
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.PROTECT,
        related_name='cash_payments'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField()
    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique reference number for this payment"
    )
    recorded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='cash_payments'
    )
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

    def clean(self):
        super().clean()
        if not self.invoice.cash_payment_allowed:
            raise ValidationError("This invoice cannot be paid by cash")
            
        # Check if payment would exceed cash balance
        config = CashConfiguration.get_config()
        if self.amount > config.current_balance:
            raise ValidationError("Insufficient cash balance for this payment")
            
        # Check if payment would exceed invoice remaining amount
        payment_status = self.invoice.get_cash_payment_status()
        if self.amount > payment_status['remaining']:
            raise ValidationError("Payment amount exceeds invoice remaining amount")

    def save(self, *args, **kwargs):
        print("\n=== Saving CashPayment ===")
        print(f"Invoice: {self.invoice.ref}")
        print(f"Amount: {self.amount}")
        print(f"Date: {self.payment_date}")
        
        # Update cash balance
        config = CashConfiguration.get_config()
        config.current_balance -= self.amount
        config.save()
        
        # Update invoice payment status
        self.invoice.update_payment_status()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        print("\n=== Deleting CashPayment ===")
        print(f"Amount: {self.amount}")
        
        # Revert cash balance
        config = CashConfiguration.get_config()
        config.current_balance += self.amount
        config.save()
        
        # Update invoice payment status
        self.invoice.update_payment_status()
        
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Cash Payment {self.reference} for Invoice {self.invoice.ref}"

    class Meta:
        ordering = ['-payment_date', '-created_at']


class CashExpense(BaseModel):
    """Records direct cash expenses without invoices"""
    EXPENSE_TYPE_CHOICES = [
        ('FINE', 'Fines'),
        ('FOOD', 'Food'),
        ('TAXI', 'Transportation'),
        ('OTHER', 'Other Expenses')
    ]
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    reference = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique reference number for this expense"
    )
    expense_account = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ],
        help_text="Expense account code"
    )
    expense_type = models.CharField(
        max_length=20,
        choices=[
            ('FINE', 'Fines'),
            ('FOOD', 'Food'),
            ('TAXI', 'Transportation'),
            ('OTHER', 'Other Expenses')
        ]
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='cash_expenses'
    )

    def save(self, *args, **kwargs):
        print("\n=== Saving CashExpense ===")
        print(f"Amount: {self.amount}")
        print(f"Date: {self.date}")
        print(f"Account: {self.expense_account}")
        
        # Update cash balance
        config = CashConfiguration.get_config()
        config.current_balance -= self.amount
        config.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        print("\n=== Deleting CashExpense ===")
        print(f"Amount: {self.amount}")
        
        # Revert cash balance
        config = CashConfiguration.get_config()
        config.current_balance += self.amount
        config.save()
        
        super().delete(*args, **kwargs)

class Client(BaseModel):
    """
    Client model with manually entered client code.
    Inherits UUID from BaseModel but maintains a separate client_code field.
    """
    name = models.CharField(
        max_length=255, 
        null=False, 
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message=_('Name can only contain letters and spaces')
            )
        ]
    )
    
    client_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            MinLengthValidator(5, _('Client code must be at least 5 digits')),
            MaxLengthValidator(10, _('Client code cannot exceed 10 digits')),
            RegexValidator(
                regex=r'^\d+$',
                message=_('Client code must contain only digits')
            )
        ],
        help_text='Enter a unique 5-10 digit code'
    )

    def clean(self):
        """Additional model validation"""
        logger.debug(f"Validating Client: name={self.name}, code={self.client_code}")
        
        if self.client_code:
            try:
                code_length = len(self.client_code)
                if code_length < 5 or code_length > 10:
                    raise ValidationError({
                        'client_code': _('Client code must be between 5 and 10 digits')
                    })
            except Exception as e:
                logger.error(f"Validation error for client_code: {e}")
                raise
    
    def get_transactions(self, year=None, month=None):
        """
        Get all transactions for the client with optional year/month filter.
        For sales: Uses the actual date
        """
        print("\n=== Starting get_transactions ===")
        transactions = []
        
        # Get sales for the specified period (using actual date)
        sales_query = self.clientsale_set.all()
        if year:
            sales_query = sales_query.filter(date__year=year)
            if month:
                sales_query = sales_query.filter(date__month=month)
                    
        for sale in sales_query:
            transactions.append({
                'date': sale.date,
                'type': 'SALE',
                'description': f'Sales of {sale.date.strftime("%m-%Y")}',
                'debit': sale.amount,
                'credit': None,
                'actual_date': sale.date
            })

        # Calculate previous balance
        if year and month:
            current_date = datetime.date(int(year), int(month), 1)
            previous_balance = 0
            
            print("\n=== Calculating Previous Balance ===")
            
            # Previous Sales (by actual date)
            prev_sales = self.clientsale_set.filter(date__lt=current_date)
            previous_balance = sum(sale.amount for sale in prev_sales)
            print(f"Previous sales balance: {previous_balance}")

            # Previous Checks and LCNs - using the SAME logic as current month
            for receipt_class, type_name in [(CheckReceipt, 'CHECK'), (LCN, 'LCN')]:
                receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('entity')

                print(f"\nProcessing previous {type_name} receipts:")
                for receipt in receipts:
                    print(f"\nReceipt: {type_name} #{receipt.get_receipt_number()}")
                    print(f"Current Status: {receipt.status}")

                    # Get all presentations for this receipt
                    if isinstance(receipt, CheckReceipt):
                        presentations = receipt.check_presentations.select_related('presentation').all()
                    else:
                        presentations = receipt.lcn_presentations.select_related('presentation').all()

                    print(f"Found {presentations.count()} presentations")

                    # Process presentations before current date
                    for pres in presentations:
                            print(f"\nPresentation date: {pres.presentation.date}")
                            number = receipt.check_number if type_name == 'CHECK' else receipt.lcn_number

                            # Add presentation transaction
                            presentation_entry = {
                                'date': pres.presentation.date,
                                'type': type_name,
                                'description': _(f'{type_name} {number} {receipt.entity.name} presented for '
                                            f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                            f'on {pres.presentation.date.strftime("%Y-%m-%d")}'),
                                'debit': None,
                                'credit': receipt.amount,
                                'actual_date': pres.presentation.date
                            }
                            previous_balance -= receipt.amount
                            print(f"Added presentation credit: -{receipt.amount}")

                    # Handle ALL unpaid statuses (history)
                    unpaid_history = ReceiptHistory.objects.filter(
                        content_type=ContentType.objects.get_for_model(receipt_class),
                        object_id=receipt.id,
                        action='status_changed',
                        new_value__status='UNPAID',
                    ).order_by('timestamp')

                    print(f"Found {unpaid_history.count()} unpaid history records")
                    for history in unpaid_history:
                        unpaid_amount = history.new_value.get("amount", receipt.amount)
                        previous_balance += unpaid_amount
                        print(f"Added unpaid debit: +{unpaid_amount}")
                        print(f"From history record: {history.timestamp}")

            # Previous Cash/Transfers (these can't be unpaid)
            for receipt_class, type_name in [(CashReceipt, 'CASH'), (TransferReceipt, 'TRANSFER')]:
                prev_receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('entity')
                total_amount = sum(receipt.amount for receipt in prev_receipts)
                previous_balance -= total_amount
                print(f"\nTotal {type_name} amount: -{total_amount}")

            print(f"\nFinal previous balance: {previous_balance}")

            # Add balance entry even if no transactions in current month
            transactions.insert(0, {
                'date': current_date,
                'type': 'BALANCE',
                'description': _('Previous Balance'),
                'debit': max(previous_balance, 0),
                'credit': abs(min(previous_balance, 0)),
                'actual_date': current_date,
                'balance': previous_balance
            })

            # Get current period receipts
            # Handle Checks and LCNs with presentations
            for receipt_class, type_name in [(CheckReceipt, 'CHECK'), (LCN, 'LCN')]:
                receipts = receipt_class.objects.filter(
                    client=self,
                    client_year=year,
                    client_month=month
                ).select_related('entity')

                print(f"\nProcessing {type_name} receipts:")
                for receipt in receipts:
                    print(f"\nReceipt: {type_name} #{receipt.get_receipt_number()}")
                    print(f"Current Status: {receipt.status}")
                    

                    # Get all presentations for this receipt
                    if isinstance(receipt, CheckReceipt):
                        presentations = receipt.check_presentations.select_related('presentation').all()
                    else:
                        presentations = receipt.lcn_presentations.select_related('presentation').all()

                    print(f"Found {presentations.count()} presentations")

                    # Process presentations
                    for pres in presentations:
                        print(f"\nPresentation date: {pres.presentation.date}")
                        number = receipt.check_number if type_name == 'CHECK' else receipt.lcn_number

                        # Determine if this is a representation
                        is_representation = False
                        earlier_presentations = presentations.filter(
                            presentation__date__lt=pres.presentation.date
                        ).exists()
                        if earlier_presentations:
                            is_representation = True

                        # Add presentation transaction
                        presentation_entry = {
                            'date': pres.presentation.date,
                            'type': type_name,
                            'description': _(f'{type_name} {number} {receipt.entity.name} '
                                        f'({("re" if is_representation else "")}presented for '
                                        f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                        f'on {pres.presentation.date.strftime("%Y-%m-%d")})'),
                            'debit': None,
                            'credit': receipt.amount,
                            'actual_date': pres.presentation.date
                        }
                        transactions.append(presentation_entry)
                        print("Added presentation entry:", presentation_entry)

                    # Handle ALL unpaid statuses (history)
                    unpaid_history = ReceiptHistory.objects.filter(
                        content_type=ContentType.objects.get_for_model(receipt_class),
                        object_id=receipt.id,
                        action='status_changed',
                        new_value__status='UNPAID'
                    ).order_by('timestamp')

                    for history in unpaid_history:
                        unpaid_entry = {
                            'date': history.business_date or history.timestamp.date(),  # Use business_date if available
                            'type': f'{type_name}_REVERSAL',
                            'description': _(f'Reversal of {type_name} {receipt.get_receipt_number()} - '
                                        f'{history.notes if history.notes else "Unpaid"}'),
                            'debit': history.new_value.get("amount", receipt.amount),
                            'credit': None,
                            'actual_date': history.business_date or history.timestamp.date()  # Also update actual_date
                        }
                        transactions.append(unpaid_entry)
                        print("Added historical unpaid entry:", unpaid_entry)
                # Process current period cash and transfer receipts
        for receipt_class, type_name in [(CashReceipt, 'CASH'), (TransferReceipt, 'TRANSFER')]:
            receipts = receipt_class.objects.filter(
                client=self,
                client_year=year,
                client_month=month
            ).select_related('entity')

            for receipt in receipts:
                transactions.append({
                    'date': receipt.operation_date,
                    'type': type_name,
                    'description': _(f'{type_name} {receipt.reference_number if hasattr(receipt, "reference_number") else receipt.transfer_reference} {receipt.entity.name}'),
                    'debit': None,
                    'credit': receipt.amount,
                    'actual_date': receipt.operation_date
                })

        
        print("\n=== Finished processing transactions ===\n")
        # Sort transactions
        transactions.sort(key=lambda x: (
            x['type'] != 'BALANCE',  # Balance entries first
            x['actual_date'].date() if isinstance(x['actual_date'], datetime.datetime) else x['actual_date']  # Convert datetime to date if needed

        ))

        # Calculate running balance
        balance = previous_balance if year and month else 0
        for t in transactions:
            if t['type'] != 'BALANCE':  # Skip balance entries
                balance += (t['debit'] or 0) - (t['credit'] or 0)
            t['balance'] = balance

        return transactions

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs"""
        logger.info(f"Saving Client: {self.name}")
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Successfully saved Client: {self.name} with code {self.client_code}")

    def __str__(self):
        return f"{self.name} ({self.client_code})"

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Entity(BaseModel):
    """
    Entity model with strict validation for ICE and accounting codes.
    """
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]*$',
                message='Name can only contain letters and spaces'
            )
        ]
    )
    
    ice_code = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{15}$',
                message='ICE code must be exactly 15 digits'
            )
        ],
        help_text='Enter exactly 15 digits'
    )
    
    accounting_code = models.CharField(
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^3\d{4,6}$',
                message='Accounting code must start with 3 and be 5-7 digits long'
            )
        ],
        help_text='Enter 5-7 digits starting with 3'
    )
    
    city = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        """Additional model validation"""
        logger.debug(f"Validating Entity: name={self.name}, ice={self.ice_code}, accounting={self.accounting_code}")
        
        # Validate ICE code
        if self.ice_code and not self.ice_code.isdigit():
            raise ValidationError({
                'ice_code': 'ICE code must contain only digits'
            })
            
        # Validate accounting code
        if self.accounting_code:
            if not self.accounting_code.startswith('3'):
                raise ValidationError({
                    'accounting_code': 'Accounting code must start with 3'
                })
            if not self.accounting_code.isdigit():
                raise ValidationError({
                    'accounting_code': 'Accounting code must contain only digits'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs"""
        logger.info(f"Saving Entity: {self.name}")
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Successfully saved Entity: {self.name}")

    def __str__(self):
        return f"{self.name} ({self.ice_code})"

    class Meta:
        ordering = ['name']
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'



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

class NegotiableReceipt(Receipt):
    """Base class for checks and LCNs."""

    STATUS_PORTFOLIO = 'PORTFOLIO'
    STATUS_PRESENTED_COLLECTION = 'PRESENTED_COLLECTION'
    STATUS_PRESENTED_DISCOUNT = 'PRESENTED_DISCOUNT'
    STATUS_DISCOUNTED = 'DISCOUNTED'
    STATUS_PAID = 'PAID'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPENSATED = 'COMPENSATED'
    STATUS_UNPAID = 'UNPAID'
    STATUS_PARTIALLY_COMPENSATED = 'PARTIALLY_COMPENSATED'

    RECEIPT_STATUS = [
        (STATUS_PORTFOLIO, 'In Portfolio'),
        (STATUS_PRESENTED_COLLECTION, 'Presented for Collection'),
        (STATUS_PRESENTED_DISCOUNT, 'Presented for Discount'),
        (STATUS_DISCOUNTED, 'Discounted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPENSATED, 'Compensated'),
        (STATUS_UNPAID, 'Unpaid'),
        (STATUS_PARTIALLY_COMPENSATED, 'Partially Compensated') 
    ]
    
    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('SIGNATURE_MISMATCH', 'Signature Mismatch'),
        ('INVALID_DATE', 'Date Invalid/Post-dated'),
        ('AMOUNT_DISCREPANCY', 'Amount Discrepancy'),
        ('TECHNICAL_ERROR', 'Technical Error (MICR)'),
        ('STOP_PAYMENT', 'Stop Payment Order'),
        ('ACCOUNT_ERROR', 'Account Number Error'),
        ('FORMAL_DEFECT', 'Formal Defect'),
        ('BANK_ERROR', 'Bank Processing Error')
    ]

    bank_account = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    issuing_bank = models.CharField(
        max_length=4,
        choices=MOROCCAN_BANKS
    )

    due_date = models.DateField()
    status = models.CharField(
        max_length=25, 
        choices=RECEIPT_STATUS,
        default=STATUS_PORTFOLIO
    )
    unpaid_date = models.DateTimeField(null=True, blank=True)
    rejection_cause = models.CharField(
        max_length=50,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True
    )
    def can_be_presented(self):
        return self.status == self.STATUS_PORTFOLIO

    def present_for_collection(self):
        if not self.can_be_presented():
            raise ValidationError("Receipt cannot be presented")
        self.status = self.STATUS_PRESENTED_COLLECTION
        self.save()

    def present_for_discount(self):
        if not self.can_be_presented():
            raise ValidationError("Receipt cannot be presented")
        self.status = self.STATUS_PRESENTED_DISCOUNT
        self.save()

    def get_receipt_number(self):
        """
        Returns the appropriate receipt number based on the receipt type.
        """
        if hasattr(self, 'check_number'):
            return self.check_number
        elif hasattr(self, 'lcn_number'):
            return self.lcn_number
        return ''
    
    def get_presentation_info(self):
        """Returns formatted presentation information if receipt is presented"""
        if self.status in ['PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT','DISCOUNTED', 'PAID', 'REJECTED']:
            presentation_receipt = (
                self.check_presentations.first() if hasattr(self, 'check_presentations') 
                else self.lcn_presentations.first()
            )
            if presentation_receipt and presentation_receipt.presentation:
                pres = presentation_receipt.presentation
                return {
                    'date': pres.date,
                    'ref': f"Presentation #{pres.id}",
                    'bank': pres.bank_account,
                    'type': pres.get_presentation_type_display(),
                    'status': pres.status
                }
        return None

    def can_edit(self):
        """Check if receipt can be edited"""
        compensating_records = CompensationRecord.objects.filter(
            compensator_content_type=ContentType.objects.get_for_model(self),
            compensator_id=self.id,
            is_active=True
        ).exists()
        
        return not compensating_records

    def can_delete(self):
        """Check if receipt can be deleted"""
        return self.can_edit()

    def get_status_display_with_details(self):
        """Enhanced status display with presentation details"""
        status_display = self.get_status_display()
        pres_info = self.get_presentation_info()
        
        if pres_info:
            details = (
                f"{pres_info['type']} on {pres_info['date']}\n"
                f"Ref: {pres_info['ref']}\n"
                f"Bank: {pres_info['bank']}"
            )
            return status_display, details
        return status_display, None
    
    @property
    def compensation_info(self):
        """Returns formatted compensation information"""
        print("\n=== Getting Compensation Info ===")
        
        # Check if this receipt is compensating others
        compensating_records = CompensationRecord.objects.filter(
            compensator_content_type=ContentType.objects.get_for_model(self),
            compensator_id=self.id,
            is_active=True
        )
        if compensating_records.exists():
            total = sum(r.amount for r in compensating_records)
            return f"Compensating {len(compensating_records)} receipt(s) for total {total}"
        
        # Check if this receipt is being compensated
        compensated_records = CompensationRecord.objects.filter(
            compensated_content_type=ContentType.objects.get_for_model(self),
            compensated_id=self.id,
            is_active=True
        )
        if compensated_records.exists():
            compensators = []
            for record in compensated_records:
                compensator = record.compensator_receipt
                if isinstance(compensator, CashReceipt):
                    compensators.append(f"Cash payment (Ref: {compensator.reference_number})")
                elif isinstance(compensator, TransferReceipt):
                    compensators.append(f"Transfer (Ref: {compensator.transfer_reference})")
                else:
                    compensators.append(f"{compensator.__class__.__name__.replace('Receipt', '')} #{compensator.get_receipt_number()}")
            return "Compensated by " + ", ".join(compensators)
        
        return None

    def mark_as_unpaid(self, cause, unpaid_date=None):
        """Mark receipt as unpaid with a cause"""
        print(f"\n=== Marking receipt {self.get_receipt_number()} as unpaid ===")
        if self.status not in ['REJECTED', 'PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT', 'DISCOUNTED']:
            msg = "Only rejected or presented receipts can be marked as unpaid"
            print(f"Error: {msg}")
            raise ValidationError(msg)
        
        business_date = unpaid_date or timezone.now()
        print(f"Using business date: {business_date}")
        print(f"Rejection cause: {cause}")
        
        old_status = self.status
        self.status = self.STATUS_UNPAID
        self.rejection_cause = cause
        self.unpaid_date = business_date
        
        # Record status change with business date
        print("Recording unpaid status in history")
        self.record_history(
            action='status_changed',
            old_value={'status': old_status},
            new_value={
                'status': self.STATUS_UNPAID,
                'cause': cause
            },
            notes=f'Marked as unpaid: {self.get_rejection_cause_display()}',
            business_date=business_date
        )
        
        # Skip duplicate history in save()
        self._skip_status_history = True
        try:
            self.save()
        finally:
            # Re-enable status change recording
            self._skip_status_history = False

    def record_history(self, action, old_value=None, new_value=None, notes=None, user=None, business_date=None):
        """
        Record a history event for the negotiable receipt, optionally with a business date
        """
        content_type = ContentType.objects.get_for_model(self)
        
        ReceiptHistory.objects.create(
            content_type=content_type,
            object_id=self.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            user=user,
            business_date=business_date
        )

    def delete(self, *args, **kwargs):
        # If this receipt is compensating any unpaid receipts and is still in PORTFOLIO
        if self.status == self.STATUS_PORTFOLIO:
            # Find any receipts this is compensating through CompensationRecord
            compensation_records = CompensationRecord.objects.filter(
                compensator_content_type=ContentType.objects.get_for_model(self),
                compensator_id=self.id
            )

            # Clean up the compensated receipts
            for record in compensation_records:
                compensated_receipt = record.compensated_receipt
                compensated_receipt.record_history(
                    action='compensation_cancelled',
                    notes=f'Compensating receipt {self.__class__.__name__} #{self.get_receipt_number()} was deleted'
                )
                # Update the compensated receipt's status
                compensated_receipt.update_compensation_status()
                # Delete the compensation record
                record.delete()

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """NegotiableReceipt save"""
        print("\n=== NegotiableReceipt save method start ===")
        print(f"Receipt ID: {self.pk}")
        print(f"Is new: {not self.pk}")

        if not self.pk:
            super().save(*args, **kwargs)
            print("Creating new receipt history record")
            self.record_history(
                action='created',
                notes=f'Receipt created with status {self.get_status_display()}'
            )
        else:
            try:
                old_instance = type(self).objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    print(f"Status change detected: {old_instance.status} -> {self.status}")
                    # Only record if we haven't explicitly asked to skip it
                    if not getattr(self, '_skip_status_history', False):
                        print("Recording status change in history")
                        
                        # Get appropriate business date based on status
                        business_date = None
                        
                        # Get the presentation receipt for the current receipt
                        presentation_receipt = None
                        if hasattr(self, 'check_presentations'):
                            presentation_receipt = self.check_presentations.last()
                        elif hasattr(self, 'lcn_presentations'):
                            presentation_receipt = self.lcn_presentations.last()
                            
                        if presentation_receipt:
                            print(f"Found presentation receipt: {presentation_receipt.id}")
                            print(f"Presentation date: {presentation_receipt.presentation.date}")
                        
                        if self.status in ['PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT', 'DISCOUNTED']:
                            # For any presentation-related status, use the presentation date
                            if presentation_receipt:
                                business_date = presentation_receipt.presentation.date
                                print(f"Using presentation date as business date: {business_date}")
                        elif self.status == 'UNPAID':
                            business_date = self.unpaid_date
                            print(f"Using unpaid date as business date: {business_date}")
                        elif self.status in ['COMPENSATED', 'PARTIALLY_COMPENSATED']:
                            business_date = getattr(self, '_force_status_date', None)
                            print(f"Using forced status date as business date: {business_date}")
                        
                        print(f"Final business date for history: {business_date}")
                        
                        self.record_history(
                            action='status_changed',
                            old_value={'status': old_instance.status},
                            new_value={'status': self.status},
                            business_date=business_date,
                            notes=f'Status changed from {old_instance.status} to {self.status}'
                        )
                    else:
                        print("Skipping status history record due to _skip_status_history flag")
                else:
                    print("No status change detected")
            except type(self).DoesNotExist:
                print("No previous instance found")
                pass
                    
            super().save(*args, **kwargs)
        print("=== NegotiableReceipt save method end ===\n")

    def update_compensation_status(self, business_date=None):
        """Update receipt status based on CompensationRecords"""
        comp_status = self.get_compensation_status()
        old_status = self.status
        
        # Determine new status
        if comp_status['total_compensated'] == 0:
            new_status = self.STATUS_UNPAID
        elif comp_status['total_compensated'] >= self.amount:
            new_status = self.STATUS_COMPENSATED
        else:
            new_status = self.STATUS_PARTIALLY_COMPENSATED
        
        if old_status != new_status:
            self.status = new_status
            self._force_status_date = business_date  # Store the date before saving
            try:
                self.record_history(
                    action='status_changed',
                    old_value={'status': old_status},
                    new_value={'status': new_status},
                    business_date=business_date,
                    notes=f'Status updated due to compensation changes. Total: {comp_status["total_compensated"]}'
                )
                self.save()
            finally:
                self._force_status_date = None  # Clean up

    def handle_payment(self):
        """Called when a negotiable receipt is paid"""
        print("\n=== Handling Payment for Compensator ===")
        print(f"Receipt: {self.__class__.__name__} #{self.get_receipt_number()}")
        
        # Activate any compensation records where this receipt is the compensator
        records = CompensationRecord.objects.filter(
            compensator_content_type=ContentType.objects.get_for_model(self),
            compensator_id=self.id,
            is_active=False
        )
        
        print(f"Found {records.count()} pending compensation records")
        
        # Activate records and update compensated receipts
        for record in records:
            record.is_active = True
            record.save()
            record.compensated_receipt.update_compensation_status()
            
            # Record history
            self.record_history(
                action='compensation_activated',
                notes=f'Activated compensation for {record.compensated_receipt.__class__.__name__} #{record.compensated_receipt.get_receipt_number()}'
            )

    def mark_as_paid(self, paid_date=None):
        """Mark receipt as paid and handle compensations"""
        if self.status == self.STATUS_PAID:
            return  # Already paid, don't do anything
            
        print(f"\n=== Marking receipt {self.get_receipt_number()} as paid ===")
        old_status = self.status
        business_date = paid_date or timezone.now()
        print(f"Using business date: {business_date}")
        
        self.status = self.STATUS_PAID
        self.paid_date = business_date
        
        # Record status change with business date
        print("Recording paid status in history")
        self.record_history(
            action='status_changed',
            old_value={'status': old_status},
            new_value={'status': self.STATUS_PAID},
            notes='Receipt marked as paid',
            business_date=business_date
        )
        
        # Skip duplicate history in save()
        self._skip_status_history = True
        try:
            self.save()
            
            # Activate any pending compensations where this receipt is the compensator
            records = CompensationRecord.objects.filter(
                compensator_content_type=ContentType.objects.get_for_model(self),
                compensator_id=self.id,
                is_active=False
            )
            
            # Activate records and update compensated receipts
            for record in records:
                record.is_active = True
                record.save()
                # Update the compensated receipt's status with the same business date
                record.compensated_receipt.update_compensation_status(business_date=business_date)
                
        finally:
            self._skip_status_history = False

    class Meta:
        abstract = True

    def get_compensation_status(self):
        """Get total compensated amount and remaining"""
        print(f"\n=== Getting Compensation Status for {self.__class__.__name__} #{self.get_receipt_number()} ===")
        
        records = CompensationRecord.objects.filter(
            compensated_content_type=ContentType.objects.get_for_model(self),
            compensated_id=self.id,
            is_active=True
        )
        
        total = sum(r.amount for r in records)
        remaining = self.amount - total
        
        print(f"Total compensated: {total}")
        print(f"Remaining: {remaining}")
        
        return {
            'total_compensated': total,
            'remaining': remaining
        }

    def add_compensation(self, compensating_receipt, amount):
        """Add a compensation record"""
        print(f"\n=== Adding Compensation for {self.__class__.__name__} #{self.get_receipt_number()} ===")
        print(f"Compensator: {compensating_receipt.__class__.__name__} #{compensating_receipt.get_receipt_number()}")
        print(f"Amount: {amount}")
        
        # Get the business date from the compensating receipt's creation/operation date
        business_date = compensating_receipt.operation_date
        
        print(f"Using business date from compensator creation: {business_date}")

        compensation = CompensationRecord(
            compensated_content_type=ContentType.objects.get_for_model(self),
            compensated_id=self.id,
            compensator_content_type=ContentType.objects.get_for_model(compensating_receipt),
            compensator_id=compensating_receipt.id,
            amount=amount,
            is_active=isinstance(compensating_receipt, (CashReceipt, TransferReceipt))
        )
        compensation.clean()
        compensation.save()
        
        self.record_history(
            action='compensated',
            new_value={
                'amount': str(amount),
                'compensator_type': compensating_receipt.__class__.__name__,
                'compensator_number': compensating_receipt.get_receipt_number(),
                'compensator_entity': compensating_receipt.entity.name if hasattr(compensating_receipt, 'entity') else None
            },
            notes=f'Compensated with {amount} by {compensating_receipt.__class__.__name__} #{compensating_receipt.get_receipt_number()}',
            business_date=business_date
        )
        
        # For cash/transfer receipts, update status immediately since they're already paid
        if isinstance(compensating_receipt, (CashReceipt, TransferReceipt)):
            # Pass the same business_date to ensure consistency
            self._force_status_date = business_date  # Add this flag
            try:
                self.update_compensation_status(business_date)
            finally:
                self._force_status_date = None
        
        return compensation

class CheckReceipt(NegotiableReceipt):
    """Check-specific implementation."""
    check_number = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                r'^\d+$',
                'Check number must contain only digits.'
            )
        ]
    )
    branch = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Check {self.check_number} - {self.amount}"

    class Meta:
        verbose_name = "Check"
        verbose_name_plural = "Checks"
        constraints = [
            models.UniqueConstraint(
                fields=['check_number', 'issuing_bank', 'entity'],
                name='unique_check_number_per_bank_entity'
            )
        ]

    def clean(self):
        super().clean()
        
        # Validate amount
        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive'})

        # Validate entity exists
        if self.entity_id and not Entity.objects.filter(id=self.entity_id).exists():
            raise ValidationError({'entity': 'Invalid entity selected'})

        # Validate client exists
        if self.client_id and not Client.objects.filter(id=self.client_id).exists():
            raise ValidationError({'client': 'Invalid client selected'})

        # Validate issuing bank
        if self.issuing_bank and self.issuing_bank not in dict(self.MOROCCAN_BANKS):
            raise ValidationError({'issuing_bank': 'Invalid issuing bank selected'})

        # Validate compensating receipt if specified
        if self.compensating_object_id:
            model = self.compensating_content_type.model_class()
            if not model.objects.filter(id=self.compensating_object_id).exists():
                raise ValidationError({'compensating_receipt': 'Invalid compensating receipt reference'})

class LCN(NegotiableReceipt):
    """LCN-specific implementation."""
    lcn_number = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                r'^\d+$',
                'LCN number must contain only digits.'
            )
        ]
    )
    branch = models.CharField(max_length=100, blank=True)

    def can_be_discounted(self):
        """Check if LCN can be discounted based on due date"""
        if not self.due_date:
            return False
            
        days_to_due = (self.due_date - timezone.now().date()).days
        return 20 <= days_to_due <= 120


    def __str__(self):
        return f"LCN {self.lcn_number} - {self.amount}"

    def clean(self):
        super().clean()
        
        # Validate amount
        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive'})

        # Validate entity exists
        if self.entity_id and not Entity.objects.filter(id=self.entity_id).exists():
            raise ValidationError({'entity': 'Invalid entity selected'})

        # Validate client exists
        if self.client_id and not Client.objects.filter(id=self.client_id).exists():
            raise ValidationError({'client': 'Invalid client selected'})

        # Validate issuing bank
        if self.issuing_bank and self.issuing_bank not in dict(self.MOROCCAN_BANKS):
            raise ValidationError({'issuing_bank': 'Invalid issuing bank selected'})

        # Validate compensating receipt if specified
        if self.compensating_object_id:
            model = self.compensating_content_type.model_class()
            if not model.objects.filter(id=self.compensating_object_id).exists():
                raise ValidationError({'compensating_receipt': 'Invalid compensating receipt reference'})

        # LCN specific validation for due date
        if not self.due_date:
            raise ValidationError({'due_date': 'Due date is required for LCN'})

    class Meta:
        verbose_name = "LCN"
        verbose_name_plural = "LCNs"
        constraints = [
            models.UniqueConstraint(
                fields=['lcn_number', 'issuing_bank', 'entity'],
                name='unique_lcn_number_per_bank_entity'
            )
        ]

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

class Presentation(BaseModel):
    """Represents a collection/discount presentation of negotiable receipts."""
    TYPE_COLLECTION = 'COLLECTION'
    TYPE_DISCOUNT = 'DISCOUNT'
    
    PRESENTATION_TYPES = [
        (TYPE_COLLECTION, 'Collection'),
        (TYPE_DISCOUNT, 'Discount')
    ]

    presentation_type = models.CharField(max_length=10, choices=PRESENTATION_TYPES)
    date = models.DateField()
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    bank_reference = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=25,
        choices=[
            ('pending', 'Pending'),
            ('presented', 'Presented'),
            ('paid', 'Paid'),
            ('rejected', 'Rejected')
        ],
        default='pending'
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

    def __str__(self):
        return f"{self.get_presentation_type_display()} - {self.date}"

    @property
    def receipt_count(self):
        return self.presentation_receipts.count()

    def update_total(self):
        self.total_amount = sum(
            pr.amount for pr in self.presentation_receipts.all()
        )
        self.save()

    def clean(self):
        super().clean()
        self.validate_receipts()

    def validate_receipts(self):
        invalid_receipts = self.presentation_receipts.exclude(
            receipt__status=NegotiableReceipt.STATUS_PORTFOLIO
        )
        if invalid_receipts.exists():
            raise ValidationError('All receipts must be in portfolio status')

    class Meta:
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
        ordering = ['-date', '-created_at']

class PresentationReceipt(BaseModel):
    """Links receipts to presentations."""

    presentation = models.ForeignKey(
        Presentation, 
        on_delete=models.CASCADE,
        related_name='presentation_receipts'
    )
    checkreceipt = models.ForeignKey(
        CheckReceipt, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='check_presentations'
    )
    lcn = models.ForeignKey(
        LCN, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lcn_presentations'
    )
    
    recorded_status = models.CharField(
        max_length=25,
        choices=NegotiableReceipt.RECEIPT_STATUS,
        null=True,
        blank=True,
        help_text="Stores the final status decision made in this presentation"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    immutable = models.BooleanField(default=False)
    forecast_payment_date = models.DateField(null=True, blank=True)
    is_forecasted = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('presentation', 'checkreceipt'),
            ('presentation', 'lcn')
        ]

    def __str__(self):
        receipt = self.checkreceipt or self.lcn
        if receipt:
            return f"Presentation {self.presentation.id} - Receipt {receipt.id}"
        return f"Presentation {self.presentation.id} - No receipt attached"

    def clean(self):
        super().clean()
        if self.checkreceipt and self.lcn:
            raise ValidationError("Cannot have both check and LCN")
        if not self.checkreceipt and not self.lcn:
            raise ValidationError("Must have either check or LCN")
        
        # Get the actual receipt object
        receipt = self.checkreceipt or self.lcn
        
        # Only validate receipt status during initial creation
        if not self.pk:  # If this is a new record
            if getattr(receipt, 'status', None) != 'PORTFOLIO' and getattr(receipt, 'status', None) != 'UNPAID':
                raise ValidationError('Only receipts in portfolio status can be presented')

    def save(self, *args, **kwargs):
        print("\n=== PresentationReceipt save method start ===")
        print(f"Receipt ID: {self.pk}")
        print(f"Is new: {not self.pk}")
        is_new = not self.pk  
        
        self.full_clean()
        super().save(*args, **kwargs)
        self.presentation.update_total()

        receipt = self.checkreceipt or self.lcn
        print(f"Receipt: {receipt}")
        print(f"Presentation type: {self.presentation.presentation_type}")
        print(f"Presentation status: {self.presentation.status}")  
        
        if receipt:
            # Only update status if not in a final state
            if receipt.status not in ['PAID', 'UNPAID', 'COMPENSATED']:
                if self.presentation.presentation_type == 'COLLECTION':
                    print("Setting status to PRESENTED_COLLECTION")
                    receipt._presentation_date = self.presentation.date  # Store temporarily
                    receipt.status = 'PRESENTED_COLLECTION'
                    if is_new:
                        print("Attempting to create forecast...")
                        try:
                            self.create_forecast_statement()
                            print("Forecast statement created successfully")
                        except Exception as e:
                            print(f"Error creating forecast statement: {str(e)}")
                            import traceback
                            print(traceback.format_exc())
                    else:
                        print("Existing presentation - skipping forecast creation")
                else:
                    print("Setting status to PRESENTED_DISCOUNT")
                    receipt._presentation_date = self.presentation.date  # Store temporarily
                    receipt.status = 'PRESENTED_DISCOUNT'
                receipt.save()
            else:
                print(f"Skipping status update - receipt already in final state: {receipt.status}")
            print(f"Final receipt status: {receipt.status}")
        print("=== PresentationReceipt save method end ===\n")

    def create_forecast_statement(self):
        """Create forecast statement for this presentation"""
        print("\n=== Creating Forecast Statement ===")
        receipt = self.checkreceipt or self.lcn
        presentation = self.presentation

        # For LCNs, use presentation date if due date is later
        if isinstance(receipt, LCN) and receipt.due_date > presentation.date:
            effective_date = presentation.date
        else:
            effective_date = presentation.date

        # Calculate business days to add
        days_to_skip = 1 if receipt.issuing_bank == presentation.bank_account.bank else 2
        forecast_date = self._calculate_business_day(effective_date, days_to_skip)

        # Check if this is a representation
        if isinstance(receipt, CheckReceipt):
            previous_presentations = receipt.check_presentations.exclude(id=self.id).exists()
        else:
            previous_presentations = receipt.lcn_presentations.exclude(id=self.id).exists()

        ForecastStatement.objects.create(
            bank_account=presentation.bank_account,
            date=forecast_date,
            label=f"Expected payment of {receipt.__class__.__name__} #{receipt.get_receipt_number()}",
            credit=receipt.amount,
            reference=f"Pres. #{presentation.bank_reference}",
            source_type=receipt.__class__.__name__.lower(),
            source_id=receipt.id,
        )

    def _calculate_business_day(self, start_date, days):
        """Calculate business day skipping weekends"""
        current_date = start_date
        while days > 0:
            current_date += timedelta(days=1)
            # Skip weekends
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)
            days -= 1
        return current_date

    class Meta:
        verbose_name = "Presentation Receipt"
        verbose_name_plural = "Presentation Receipts"
        unique_together = [
            ('presentation', 'checkreceipt'),
            ('presentation', 'lcn')
        ]

class ReceiptHistory(BaseModel):
    # Generic Foreign Key to support both Check and LCN receipts
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    receipt = GenericForeignKey('content_type', 'object_id')
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('status_changed', 'Status Changed'),
        ('presented_collection', 'Presented for Collection'),
        ('presented_discount', 'Presented for Discount'),
        ('compensating_assigned', 'Compensating Receipt Assigned'),
        ('compensated', 'Compensation Allocated'),
        ('unpaid', 'Marked as Unpaid'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected by Bank')
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    business_date = models.DateTimeField(null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='receipt_history'
    )
    
    class Meta:
        ordering = ['-business_date', '-timestamp']
        verbose_name = "Receipt History"
        verbose_name_plural = "Receipt Histories"

    def record_history(self, action, old_value=None, new_value=None, notes=None, user=None, business_date=None):
        """Record a history event"""
        content_type = ContentType.objects.get_for_model(self)
        
        ReceiptHistory.objects.create(
            content_type=content_type,
            object_id=self.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            user=user,
            business_date=business_date or timezone.now()
        )

    def __str__(self):
        return f"{self.receipt} - {self.action} at {self.timestamp}"

    def formatted_business_date(self):
        """Return formatted business date"""
        return self.business_date.strftime('%d/%m/%Y') if self.business_date else None

    def formatted_created_at(self):
        """Return formatted timestamp"""
        return self.created_at.strftime('%d/%m/%Y %H:%M:%S')

class ClientSale(BaseModel):
    SALE_TYPES = [
        ('BRICKS', 'Bricks'),
        ('TRANSPORT', 'Transport'),
    ]

    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    month = models.IntegerField()
    notes = models.TextField(blank=True)
    sale_type = models.CharField(max_length=10, choices=SALE_TYPES, default='BRICKS')

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.year:
            self.year = self.date.year
        if not self.month:
            self.month = self.date.month
        super().save(*args, **kwargs)


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
        print("\n=== Getting IR Accounting Entries ===")
        ir_declarations = IRDeclaration.objects.filter(
            status='paid',
        )

        if start_date:
            ir_declarations = ir_declarations.filter(payment_date__gte=start_date)
        if end_date:
            ir_declarations = ir_declarations.filter(payment_date__lte=end_date)

        print(f"Found {ir_declarations.count()} paid IR declarations")

        for declaration in ir_declarations:
            try:
                config = IRConfiguration.objects.first()
                if not config:
                    continue
                    
                bank_account = config.domiciliation_bank
                    
                # Payment entry in bank journal
                entries.extend([
                    {
                        'date': declaration.payment_date,
                        'label': f"IR Payment {declaration.period_month:02d}/{declaration.period_year}",
                        'debit': declaration.tax_amount,
                        'credit': None,
                        'account_code': config.accounting_code,
                        'reference': f"IR-{declaration.period_month:02d}-{declaration.period_year}",
                        'journal_code': bank_account.journal_number,
                        'source_type': 'ir_declaration',
                        'source_id': declaration.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': declaration.payment_date,
                        'label': f"IR Payment {declaration.period_month:02d}/{declaration.period_year}",
                        'debit': None,
                        'credit': declaration.tax_amount,
                        'account_code': bank_account.accounting_number,
                        'reference': f"IR-{declaration.period_month:02d}-{declaration.period_year}",
                        'journal_code': bank_account.journal_number,
                        'source_type': 'ir_declaration',
                        'source_id': declaration.id,
                        'pair_index': len(entries) // 2
                    }
                ])
                    
            except Exception as e:
                print(f"Error processing IR accounting entries: {str(e)}")
                continue
        
        print("\n=== Getting Stamp Rights Accounting Entries ===")
        stamp_rights = StampRightDeclaration.objects.filter(
            status='paid'
        )

        if start_date:
            stamp_rights = stamp_rights.filter(payment_date__gte=start_date)
        if end_date:
            stamp_rights = stamp_rights.filter(payment_date__lte=end_date)

        print(f"Found {stamp_rights.count()} paid stamp rights declarations")

        for declaration in stamp_rights:
            try:
                config = StampRightConfiguration.get_config()
                if not config:
                    continue
                        
                bank_account = config.domiciliation_bank
                
                # Payment entry in bank journal
                entries.extend([
                    {
                        'date': declaration.payment_date,
                        'label': f"Stamp Rights Payment {declaration.period_month:02d}/{declaration.period_year}",
                        'debit': declaration.tax_amount,
                        'credit': None,
                        'account_code': config.accounting_code,
                        'reference': f"SR-{declaration.period_month:02d}-{declaration.period_year}",
                        'journal_code': bank_account.journal_number,
                        'source_type': 'stamp_right_declaration',
                        'source_id': declaration.id,
                        'pair_index': len(entries) // 2
                    },
                    {
                        'date': declaration.payment_date,
                        'label': f"Stamp Rights Payment {declaration.period_month:02d}/{declaration.period_year}",
                        'debit': None,
                        'credit': declaration.tax_amount,
                        'account_code': bank_account.accounting_number,
                        'reference': f"SR-{declaration.period_month:02d}-{declaration.period_year}",
                        'journal_code': bank_account.journal_number,
                        'source_type': 'stamp_right_declaration',
                        'source_id': declaration.id,
                        'pair_index': len(entries) // 2
                    }
                ])  
            except Exception as e:
                print(f"Error processing stamp rights accounting entries: {str(e)}")
                continue
        

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

class CustomBankRecord(BaseModel):
    """
    Custom bank record that can be manually added by users
    to appear in both bank statements and accounting entries.
    """
    bank_account = models.ForeignKey(
        'BankAccount', 
        on_delete=models.CASCADE,
        related_name='custom_records'
    )
    date = models.DateField()
    bank_label = models.CharField(
        max_length=255,
        help_text="Label that will appear on the bank statement"
    )
    accounting_label = models.CharField(
        max_length=255,
        help_text="Label that will appear in accounting entries"
    )
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    debit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Amount to debit (outgoing)"
    )
    credit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Amount to credit (incoming)"
    )
    
    account_code = models.CharField(
        max_length=10,
        help_text="Accounting code for this entry"
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='custom_bank_records'
    )

    def clean(self):
        super().clean()
        if not (self.debit or self.credit):
            raise ValidationError("Either debit or credit amount must be provided")
        if self.debit and self.credit:
            raise ValidationError("Only one of debit or credit can be provided")

    def __str__(self):
        amount = self.debit or self.credit
        return f"Custom Record: {self.bank_label} - {amount}"

    class Meta:
        ordering = ['-date', '-created_at']

class InterBankTransfer(BaseModel):
    """
    Tracks transfers between bank accounts and their related records.
    """
    from_bank = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        related_name='outgoing_transfers'
    )
    to_bank = models.ForeignKey(
        'BankAccount', 
        on_delete=models.PROTECT,
        related_name='incoming_transfers'
    )
    date = models.DateField()
    label = models.CharField(max_length=255, default="Interbank Transfer")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Transfer from {self.from_bank} to {self.to_bank} on {self.date}"

class TransferredRecord(BaseModel):
    """
    Links original statement records to their transfer.
    """
    transfer = models.ForeignKey(
        InterBankTransfer, 
        on_delete=models.CASCADE,
        related_name='transferred_records'
    )
    # Source type and id for the original record
    source_type = models.CharField(max_length=50)  # 'cash_receipt', 'transfer_receipt', 'presentation_receipt'
    source_id = models.UUIDField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    original_date = models.DateField()
    original_label = models.CharField(max_length=255)
    original_reference = models.CharField(max_length=100)

    class Meta:
        unique_together = ['source_type', 'source_id']  # Prevent double transfers

    def __str__(self):
        return f"Transferred record {self.source_type}:{self.source_id}"
    
class BankFeeType(BaseModel):
    """Defines bank fee types and their accounting codes"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)  # For reference/initials
    accounting_code = models.CharField(max_length=5)  # Fee account code
    vat_code = models.CharField(max_length=5)  # VAT account code
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class BankFeeTransaction(BaseModel):
    """Records bank fee transactions"""
    bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)
    fee_type = models.ForeignKey(BankFeeType, on_delete=models.PROTECT)
    date = models.DateField()
    related_presentation = models.ForeignKey(
        'Presentation', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    raw_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=10.00,
        null=True,
        blank=True
    )
    vat_included = models.BooleanField(default=False)
    vat_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
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
        ],
        help_text="VAT Declaration period (MM-YYYY)"
    )

    def calculate_amounts(self):
        """Calculate VAT and total amounts based on settings"""
        if not self.vat_rate or self.vat_rate == 0:
            self.vat_amount = Decimal('0.00')
            self.total_amount = self.raw_amount
        elif self.vat_included:
            # If VAT included, calculate backwards
            vat_multiplier = (self.vat_rate / 100) + 1
            self.raw_amount = self.total_amount / vat_multiplier
            self.vat_amount = self.total_amount - self.raw_amount
        else:
            # Calculate VAT and total from raw amount
            self.vat_amount = self.raw_amount * (self.vat_rate / 100)
            self.total_amount = self.raw_amount + self.vat_amount

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.calculate_amounts()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fee_type.name} - {self.date}"

# Add initial fee types
INITIAL_FEE_TYPES = [
    {
        'name': 'Account Management Fee',
        'code': 'AMF',
        'accounting_code': '61411',
        'vat_code': '34551'
    },
    {
        'name': 'Statement Fee',
        'code': 'STF',
        'accounting_code': '61412',
        'vat_code': '34551'
    },
    {
        'name': 'Check Processing Fee',
        'code': 'CPF',
        'accounting_code': '61413',
        'vat_code': '34551'
    },
    {
        'name': 'Transfer Commission',
        'code': 'TRC',
        'accounting_code': '61414',
        'vat_code': '34551'
    },
    {
        'name': 'Check Book Fee',
        'code': 'CBF',
        'accounting_code': '61415',
        'vat_code': '34551'
    },
    {
        'name': 'Payment Rejection Fee',
        'code': 'PRF',
        'accounting_code': '61416',
        'vat_code': '34551'
    },
    {
        'name': 'Check Discount Commission',
        'code': 'CDC',
        'accounting_code': '61417',
        'vat_code': '34551'
    },
    {
        'name': 'LCN Discount Commission',
        'code': 'LDC',
        'accounting_code': '61418',
        'vat_code': '34551'
    }
]

class CompensationRecord(BaseModel):
    """Tracks compensation relationships and amounts"""
    
    # The unpaid receipt being compensated
    compensated_content_type = models.ForeignKey(ContentType, related_name='compensated_records', on_delete=models.CASCADE)
    compensated_id = models.UUIDField()
    compensated_receipt = GenericForeignKey('compensated_content_type', 'compensated_id')
    
    # The receipt doing the compensation
    compensator_content_type = models.ForeignKey(ContentType, related_name='compensator_records', on_delete=models.CASCADE)
    compensator_id = models.UUIDField()
    compensator_receipt = GenericForeignKey('compensator_content_type', 'compensator_id')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=False)  # True for cash/transfer, False for negotiables until paid
    
    def clean(self):
        print(f"\n=== Validating CompensationRecord ===")
        print(f"Compensated: {self.compensated_receipt}")
        print(f"Compensator: {self.compensator_receipt}")
        print(f"Amount: {self.amount}")
        
        if self.amount <= 0:
            raise ValidationError("Compensation amount must be positive")
            
        # Check if amount exceeds remaining
        remaining = self.compensated_receipt.amount
        for record in CompensationRecord.objects.filter(
            compensated_content_type=self.compensated_content_type,
            compensated_id=self.compensated_id,
            is_active=True
        ):
            remaining -= record.amount
            
        if self.amount > remaining:
            raise ValidationError(f"Amount {self.amount} exceeds remaining {remaining}")

    def get_compensation_status(self):
        """Get total compensated amount and remaining"""
        print(f"\n=== Getting Compensation Status for {self.__class__.__name__} #{self.get_receipt_number()} ===")
        
        records = CompensationRecord.objects.filter(
            compensated_content_type=ContentType.objects.get_for_model(self),
            compensated_id=self.id,
            is_active=True
        )
        
        total = sum(r.amount for r in records)
        remaining = self.amount - total
        
        print(f"Total compensated: {total}")
        print(f"Remaining: {remaining}")
        
        return {
            'total_compensated': total,
            'remaining': remaining
        }


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

            
class ContractProduct(BaseModel):
    """Product for a contract"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reduction_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ['contract', 'product']

class ContractInvoice(BaseModel):
    """Links generated invoices to their contract periods"""
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    invoice = models.OneToOneField('Invoice', on_delete=models.PROTECT, related_name='contract_invoice')
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        unique_together = [
            ['contract', 'period_start', 'period_end']
        ]

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
    


# VAT Management
class VATConfiguration(BaseModel):
    """Global VAT configuration settings"""
    declaration_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month for VAT declaration (1-28)"
    )
    domiciliation_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='vat_declarations'
    )
    invoiced_vat_account = models.CharField(
        max_length=5,
        default='4300',
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ]
    )
    deducted_vat_account = models.CharField(
        max_length=5,
        default='4400',
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ]
    )
    journal = models.CharField(
        max_length=2,
        default='06',
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ]
    )

    default_forecast_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('400000.00'),
        help_text="Default amount for VAT forecasts"
    )

    @classmethod
    def get_config(cls):
        """Get or create VAT configuration"""
        config = VATConfiguration.objects.first()
        if not config:
            raise ValidationError("VAT Configuration must be set up")
        return config

    @classmethod
    def initialize(cls, declaration_day, domiciliation_bank, invoiced_vat_account, deducted_vat_account, journal, default_forecast_amount):
        """Initialize or update VAT configuration"""
        print("\n=== Initializing VAT Configuration ===")
        
        config = cls.objects.first()
        if config:
            print("Updating existing configuration")
            config.declaration_day = declaration_day
            config.domiciliation_bank = domiciliation_bank
            config.invoiced_vat_account = invoiced_vat_account
            config.deducted_vat_account = deducted_vat_account
            config.journal = journal
            config.default_forecast_amount = default_forecast_amount
            config.save()
        else:
            print("Creating new configuration")
            config = cls.objects.create(
                declaration_day=declaration_day,
                domiciliation_bank=domiciliation_bank,
                invoiced_vat_account=invoiced_vat_account,
                deducted_vat_account=deducted_vat_account,
                journal=journal,
                default_forecast_amount=default_forecast_amount
            )
            
        # Generate initial forecasts
        VATDeclaration.generate_forecasts()
        return config

    def clean(self):
        super().clean()
        if self.pk and VATConfiguration.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one VAT configuration can exist")

    def save(self, *args, **kwargs):
        print("\n=== Saving VAT Configuration ===")
        print(f"Declaration day: {self.declaration_day}")
        print(f"Bank: {self.domiciliation_bank}")
        
        if not self.pk and VATConfiguration.objects.exists():
            raise ValidationError("Only one VAT configuration can exist")
        
        super().save(*args, **kwargs)

class VATDeclarationManager(Manager):
    def get_pending_declarations(self):
        """Get declarations ready for processing"""
        today = timezone.now().date()
        return self.filter(
            status=VATDeclaration.DRAFT,
            due_date__lte=today
        ).order_by('due_date')
        
    def get_future_declarations(self):
        """Get all future declarations"""
        today = timezone.now().date()
        return self.filter(
            Q(period_year__gt=today.year) |
            Q(period_year=today.year, period_month__gt=today.month)
        ).order_by('period_year', 'period_month')

class VATDeclaration(BaseModel):
    """Monthly VAT declaration"""
    DRAFT = 'draft'
    DECLARED = 'declared'
    PAID = 'paid'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (DECLARED, 'Declared'),
        (PAID, 'Paid')
    ]

    period_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    period_year = models.IntegerField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    total_invoiced_vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_deducted_vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    forecast = models.OneToOneField(
        'ForecastStatement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vat_declaration'
    )
    objects = VATDeclarationManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['period_month', 'period_year'],
                name='unique_vat_period'
            )
        ]
        ordering = ['-period_year', '-period_month']

    def __str__(self):
        return f"VAT Declaration {self.id} for {self.period_month}/{self.period_year}"

    def get_config(self):
        """Get VAT configuration"""
        return VATConfiguration.get_config()

    def update_forecast(self):
        """Update or create forecast for this declaration"""
        print(f"\n=== Updating Forecast for {self.period_month}/{self.period_year} ===")
        
        config = self.get_config()
        
        # Only generate forecast for draft declarations
        if self.status != self.DRAFT:
            print("Declaration not in draft status, skipping forecast")
            return
            
        # Calculate expected VAT amounts
        total_expected_vat = Decimal('0.00')
        
        # Try to estimate from historical data
        previous_declarations = VATDeclaration.objects.filter(
            status=self.PAID
        ).order_by('-period_year', '-period_month')[:3]
        
        if previous_declarations:
            # Average of last 3 declarations
            total_expected_vat = sum(
                d.total_invoiced_vat - d.total_deducted_vat 
                for d in previous_declarations
            ) / len(previous_declarations)
            print(f"Estimated from historical average: {total_expected_vat}")
        
        # Get or create forecast
        if self.forecast:
            print("Updating existing forecast")
            forecast = self.forecast
            forecast.amount = total_expected_vat
            forecast.save()
        else:
            print("Creating new forecast")
            forecast = ForecastStatement.objects.create(
                bank_account=config.domiciliation_bank,
                date=self.due_date,
                label=f"Expected VAT Payment {self.period_month:02d}/{self.period_year}",
                debit=total_expected_vat if total_expected_vat > 0 else None,
                credit=abs(total_expected_vat) if total_expected_vat < 0 else None,
                reference=f"VAT-{self.period_month:02d}-{self.period_year}",
                source_type='vat_declaration',
                source_id=self.id
            )
            self.forecast = forecast
            self.save()
    
    def calculate_invoiced_vat(self):
        """Calculate VAT from paid receipts in this period"""
        print("\n=== Calculating Invoiced VAT ===")
        print(f"Period: {self.period_month}/{self.period_year}")
        
        period_start = datetime.date(self.period_year, self.period_month, 1)
        period_end = datetime.date(
            self.period_year + (self.period_month == 12),
            (self.period_month % 12) + 1,
            1
        ) - timedelta(days=1)
        
        print(f"Period range: {period_start} to {period_end}")
        total_vat = Decimal('0.00')
        
        # For TransferReceipts & CashReceipts - use operation_date
        print("\nProcessing transfers...")
        transfers = TransferReceipt.objects.filter(
            operation_date__range=(period_start, period_end),
            vat_declared=False
        ).select_related('entity')
        
        for transfer in transfers:
            vat_amount = transfer.amount / Decimal('6')
            print(f"Transfer #{transfer.transfer_reference}: VAT = {vat_amount}")
            
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=transfer.id,
                vat_rate=Decimal('20.00'),
                vat_amount=vat_amount,
                original_amount=transfer.amount,
                credit_amount=Decimal('0.00')
            )
            
            transfer.vat_declared = True
            transfer.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            transfer.save()
            
            total_vat += vat_amount
        
        print("\nProcessing cash receipts...")
        cash_receipts = CashReceipt.objects.filter(
            operation_date__range=(period_start, period_end),
            vat_declared=False
        ).select_related('entity')
        
        for receipt in cash_receipts:
            vat_amount = receipt.amount / Decimal('6')
            print(f"Cash Receipt #{receipt.reference_number}: VAT = {vat_amount}")
            
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=receipt.id,
                vat_rate=Decimal('20.00'),
                vat_amount=vat_amount,
                original_amount=receipt.amount,
                credit_amount=Decimal('0.00')
            )
            
            receipt.vat_declared = True
            receipt.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            receipt.save()
            
            total_vat += vat_amount

        # For Checks and LCNs - use presentation history
        presentations = Presentation.objects.all().prefetch_related(
            'presentation_receipts__checkreceipt',
            'presentation_receipts__lcn'
        )

        for pres in presentations:
            for pr in pres.presentation_receipts.all():
                receipt = pr.checkreceipt or pr.lcn
                if not receipt:
                    continue

                if pr.recorded_status != 'PAID':
                    continue

                # Get payment date from history
                payment_history = ReceiptHistory.objects.filter(
                    content_type=ContentType.objects.get_for_model(receipt.__class__),
                    object_id=receipt.id,
                    action='status_changed',
                    new_value__status='PAID'
                ).order_by('-business_date').first()

                payment_date = (payment_history.business_date.date() 
                    if payment_history and payment_history.business_date 
                    else pres.date)

                if not (period_start <= payment_date <= period_end):
                    continue

                if receipt.vat_declared:
                    continue

                print(f"\nProcessing {receipt.__class__.__name__} #{receipt.get_receipt_number()}")
                print(f"Payment date: {payment_date}")

                vat_amount = receipt.amount / Decimal('6')
                print(f"VAT amount: {vat_amount}")

                VATDeclarationDetail.objects.create(
                    declaration=self,
                    source_type='receipt',
                    source_id=receipt.id,
                    vat_rate=Decimal('20.00'),
                    vat_amount=vat_amount,
                    original_amount=receipt.amount,
                    credit_amount=Decimal('0.00')
                )

                receipt.vat_declared = True
                receipt.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
                receipt.save()

                total_vat += vat_amount

        print(f"\nTotal invoiced VAT: {total_vat}")
        return total_vat

    def calculate_deducted_vat(self):
        """Calculate VAT from paid invoices in this period and non-deducted from previous periods"""
        print("\n=== Calculating Deducted VAT ===")
        print(f"Period: {self.period_month}/{self.period_year}")
        
        period_start = datetime.date(self.period_year, self.period_month, 1)
        period_end = datetime.date(
            self.period_year + (self.period_month == 12),
            (self.period_month % 12) + 1,
            1
        ) - timedelta(days=1)
        
        total_deducted = Decimal('0.00')
        
        # Process Check payments
        print("\nProcessing check payments...")
        checks = Check.objects.filter(
            Q(
                paid_at__range=(period_start, period_end),
                vat_declared=False
            ) | Q(
                vat_declared=False,
                paid_at__lt=period_start
            )
        ).select_related('cause', 'checker__bank_account')
        
        for check in checks:
            if not check.cause or check.cause.non_deductible_vat:
                print(f"Skipping check {check.position} - non-deductible")
                continue
                
            vat_details = check.cause.calculate_payment_vat(check.amount)
            print(f"\nCheck {check.position} VAT details:", vat_details)
            
            # Create detail records for each VAT rate
            for rate, details in vat_details.items():
                VATDeclarationDetail.objects.create(
                    declaration=self,
                    source_type='invoice_check',
                    source_id=check.id,
                    vat_rate=rate,
                    vat_amount=details['vat'],
                    original_amount=details['amount'],
                    credit_amount=Decimal('0.00')
                )
                total_deducted += details['vat']
            
            # Mark check as declared
            check.vat_declared = True
            check.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            check.save()

        # Process DirectDebit payments
        print("\nProcessing direct debit payments...")
        direct_debits = DirectDebit.objects.filter(
            Q(
                processed_date__range=(period_start, period_end),
                vat_declared=False
            ) | Q(
                vat_declared=False,
                processed_date__lt=period_start
            )
        ).select_related('invoice__invoice')
        
        for debit in direct_debits:
            invoice = debit.invoice.invoice
            if not invoice or invoice.non_deductible_vat:
                print(f"Skipping debit {debit.id} - non-deductible")
                continue
            
            vat_details = invoice.calculate_payment_vat(debit.amount)
            print(f"\nDirect Debit {debit.id} VAT details:", vat_details)
            
            # Create detail records for each VAT rate
            for rate, details in vat_details.items():
                VATDeclarationDetail.objects.create(
                    declaration=self,
                    source_type='invoice_direct_debit',
                    source_id=debit.id,
                    vat_rate=rate,
                    vat_amount=details['vat'],
                    original_amount=details['amount'],
                    credit_amount=Decimal('0.00')
                )
                total_deducted += details['vat']
            
            # Mark direct debit as declared
            debit.vat_declared = True
            debit.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            debit.save()
        
        bank_fees = BankFeeTransaction.objects.filter(
            Q(
                date__range=(period_start, period_end)
            ) | Q(
                date__lt=period_start
            )
        ).select_related('fee_type')
        
        for fee in bank_fees:
            if fee.vat_amount > 0:
                print(f"\nProcessing fee: {fee.fee_type.name}")
                print(f"VAT amount: {fee.vat_amount}")
                    
                VATDeclarationDetail.objects.create(
                    declaration=self,
                    source_type='bank_fee',
                    source_id=fee.id,
                    vat_rate=fee.vat_rate,
                    vat_amount=fee.vat_amount,
                    original_amount=fee.raw_amount,
                    credit_amount=Decimal('0.00')
                )
                
                total_deducted += fee.vat_amount
                print(f"Running total: {total_deducted}")

        print("\nProcessing cash payments...")
        cash_payments = CashPayment.objects.filter(
            Q(
                payment_date__range=(period_start, period_end),
                vat_declared=False
            ) | Q(
                vat_declared=False,
                payment_date__lt=period_start
            )
        ).select_related('invoice')

        for payment in cash_payments:
            if not payment.invoice or payment.invoice.non_deductible_vat:
                print(f"Skipping payment {payment.id} - non-deductible")
                continue
                
            vat_details = payment.invoice.calculate_payment_vat(payment.amount)
            print(f"\nCash Payment {payment.reference} VAT details:", vat_details)
            
            # Create detail records for each VAT rate
            for rate, details in vat_details.items():
                VATDeclarationDetail.objects.create(
                    declaration=self,
                    source_type='cash_payment',
                    source_id=payment.id,
                    vat_rate=rate,
                    vat_amount=details['vat'],
                    original_amount=details['amount'],
                    credit_amount=Decimal('0.00')
                )
                total_deducted += details['vat']
            
            # Mark payment as declared
            payment.vat_declared = True
            payment.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            payment.save()

            
        print(f"\nTotal deducted VAT: {total_deducted}")
        return total_deducted

    def process_declaration(self):
        """Calculate and store VAT details"""
        print("\n=== Processing VAT Declaration ===")
        print(f"Declaration ID: {self.id}")
        print(f"Period: {self.period_month}/{self.period_year}")
        
        if self.status != self.DRAFT:
            print("Declaration not in draft status - skipping")
            raise ValidationError("Can only process draft declarations")
        
        print("\nResetting previously declared items...")
        details = self.details.all()
        for detail in details:
            if detail.source_type == 'receipt':
                for model in [CheckReceipt, LCN, TransferReceipt, CashReceipt]:
                    try:
                        item = model.objects.get(id=detail.source_id)
                        if item.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                            print(f"Resetting declaration status for {model.__name__} #{item.get_receipt_number()}")
                            item.vat_declared = False
                            item.vat_declaration_period = None
                            item.save()
                    except model.DoesNotExist:
                        continue
            elif detail.source_type in ['invoice_check', 'invoice_direct_debit']:
                for model in [Check, DirectDebit]:
                    try:
                        item = model.objects.get(id=detail.source_id)
                        if item.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                            print(f"Resetting declaration status for payment {item.id}")
                            item.vat_declared = False
                            item.vat_declaration_period = None
                            item.save()
                    except model.DoesNotExist:
                        continue

        print("Clearing existing details...")
        self.details.all().delete()

        print("\nCalculating invoiced VAT...")
        self.total_invoiced_vat = self.calculate_invoiced_vat()
        print(f"Total invoiced VAT: {self.total_invoiced_vat}")
        
        print("\nCalculating deducted VAT...")
        self.total_deducted_vat = self.calculate_deducted_vat()
        print(f"Total deducted VAT: {self.total_deducted_vat}")
        
        self.save()

    @classmethod
    def generate_forecasts(cls):
        """Generate and maintain rolling 12-month VAT forecasts"""
        print("\n=== Generating VAT Forecasts ===")
        
        config = VATConfiguration.objects.first()
        if not config:
            print("No VAT configuration found")
            return
            
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        print(f"Current date: {today}")
        print(f"Current config: {config.declaration_day=}, {config.default_forecast_amount=}")
        print(f"Generating forecasts from {current_month}/{current_year}")
        
        # Delete obsolete forecasts
        obsolete_forecasts = ForecastStatement.objects.filter(
            source_type='vat_declaration',
            date__lt=today,
            is_processed=False
        )
        if obsolete_forecasts.exists():
            print(f"Deleting {obsolete_forecasts.count()} obsolete forecasts")
            obsolete_forecasts.delete()
        
        # Get all existing future forecasts
        existing_forecasts = ForecastStatement.objects.filter(
            source_type='vat_declaration',
            date__gte=today,
            is_processed=False
        ).order_by('date')
        
        print(f"Found {existing_forecasts.count()} existing future forecasts")
        
        # Calculate how many months we need to generate
        months_needed = 12 - existing_forecasts.count()
        
        if months_needed <= 0:
            print("Already have enough forecasts")
            return
            
        # Get last forecast date or start from today
        last_date = existing_forecasts.last().date if existing_forecasts.exists() else today
        
        print(f"Generating {months_needed} new forecasts from {last_date}")
        
        # Generate new forecasts
        current_date = last_date
        for _ in range(months_needed):
            # Move to next month - using a safer method to handle month transitions
            if current_date.month == 12:
                next_date = datetime.date(current_date.year + 1, 1, 1)
            else:
                next_date = datetime.date(current_date.year, current_date.month + 1, 1)
                
            # Adjust for declaration day - try to use the specified day
            try:
                last_day_of_month = calendar.monthrange(next_date.year, next_date.month)[1]
                day_to_use = min(config.declaration_day, last_day_of_month)
                forecast_date = next_date.replace(day=day_to_use)
            except ValueError:
                # Fallback - use the last day of the month
                forecast_date = next_date.replace(day=calendar.monthrange(next_date.year, next_date.month)[1])
                
            # Skip weekends
            while forecast_date.weekday() >= 5:
                forecast_date += timedelta(days=1)
                
            print(f"\nCreating forecast for {forecast_date}")
            
            # Check if declaration exists for this period
            declaration = cls.objects.filter(
                period_month=next_date.month,
                period_year=next_date.year
            ).first()
            
            if declaration:
                print(f"Found existing declaration for {next_date.month}/{next_date.year}")
                source_id = declaration.id
                amount = declaration.total_invoiced_vat - declaration.total_deducted_vat
            else:
                print(f"Using default amount for {next_date.month}/{next_date.year}")
                source_id = uuid.uuid4()  # Temporary ID
                amount = config.default_forecast_amount
                
            # Create forecast
            ForecastStatement.objects.create(
                bank_account=config.domiciliation_bank,
                date=forecast_date,
                label=f"Expected VAT Payment {next_date.month:02d}/{next_date.year}",
                debit=amount if amount > 0 else None,
                credit=abs(amount) if amount < 0 else None,
                reference=f"VAT-{next_date.month:02d}-{next_date.year}",
                source_type='vat_declaration',
                source_id=source_id,
                amount=amount
            )
            print(f"Created forecast: {amount} on {forecast_date}")
            
            current_date = next_date

    def declare(self):
        """Mark declaration as declared and create forecast"""
        print("\n=== Declaring VAT ===")
        
        if not self.is_processed:
            raise ValidationError("Declaration must be processed before declaring")
            
        if self.status != self.DRAFT:
            raise ValidationError("Can only declare draft declarations")
        
        config = VATConfiguration.objects.first()
        if not config:
            raise ValidationError("VAT Configuration required")
        
        # Create forecast for VAT payment
        net_vat = self.total_invoiced_vat - self.total_deducted_vat
        
        if net_vat > 0:  # Only create forecast if VAT is payable
            print(f"Creating forecast for VAT payment: {net_vat}")
            forecast = ForecastStatement.objects.create(
                bank_account=config.domiciliation_bank,
                date=self.due_date,
                label=f"VAT Payment for {self.period_month:02d}/{self.period_year}",
                debit=net_vat,
                reference=f"VAT-{self.period_month:02d}-{self.period_year}",
                source_type='vat_declaration',
                source_id=self.id,
                amount=net_vat
            )
            self.forecast = forecast
        
        self.status = self.DECLARED
        self.save()

    def mark_as_paid(self, payment_date):
        """Mark declaration as paid"""
        print(f"\n=== Marking VAT Declaration {self.period_month}/{self.period_year} as Paid ===")
        print(f"Payment date: {payment_date}")
        
        if not self.is_processed:
            raise ValidationError("Declaration must be processed before payment")
            
        if self.status != self.DECLARED:
            raise ValidationError("Can only pay declared VAT declarations")
        
        if payment_date < self.due_date:
            print(f"Payment date {payment_date} cannot be before due date {self.due_date}")
            raise ValidationError("Payment date cannot be before due date")
        
        self.payment_date = payment_date
        self.status = self.PAID
        
        # Mark forecast as processed if exists
        if self.forecast:
            print(f"Marking forecast {self.forecast.id} as processed")
            self.forecast.is_processed = True
            self.forecast.save()
        
        self.save()
        print(f"Declaration marked as paid successfully")
    
    def mark_as_rejected(self, rejection_date):
        """Mark declaration as rejected"""
        print(f"\n=== Marking VAT Declaration {self.period_month}/{self.period_year} as Rejected ===")
        print(f"Rejection date: {rejection_date}")
        
        if not self.is_processed:
            raise ValidationError("Declaration must be processed before rejection")
            
        if self.status != self.DECLARED:
            raise ValidationError("Can only reject declared VAT declarations")
        
        self.status = self.DRAFT
        
        if self.forecast:
            print(f"Unmarking forecast {self.forecast.id}")
            self.forecast.is_processed = False
            self.forecast.save()
        
        self.save()
        print(f"Declaration marked as rejected")

    @classmethod
    def update_forecasts(cls):
        """Update all future VAT forecasts"""
        print("\n=== Updating VAT Forecasts ===")
        
        today = timezone.now().date()
        
        # Get all future declarations
        future_declarations = cls.objects.filter(
            Q(period_year__gt=today.year) |
            Q(period_year=today.year, period_month__gt=today.month)
        ).order_by('period_year', 'period_month')
        
        print(f"Found {future_declarations.count()} future declarations")
        
        # Ensure we have at least 12 months of forecasts
        if not future_declarations.exists():
            print("No future declarations found, generating initial forecasts")
            cls.generate_forecasts()
        else:
            last_declaration = future_declarations.last()
            months_ahead = 12 - future_declarations.count()
            
            if months_ahead > 0:
                print(f"Generating {months_ahead} additional months")
                current_month = last_declaration.period_month
                current_year = last_declaration.period_year
                
                for _ in range(months_ahead):
                    if current_month == 12:
                        current_month = 1
                        current_year += 1
                    else:
                        current_month += 1
                        
                    declaration, created = cls.objects.get_or_create(
                        period_month=current_month,
                        period_year=current_year
                    )
                    
                    if created:
                        print(f"Created declaration for {current_month}/{current_year}")

    def can_be_deleted(self):
        """Check if declaration can be deleted"""
        print(f"\n=== Checking if VAT Declaration {self.id} can be deleted ===")
        print(f"Status: {self.status}")
        
        if self.status != self.DRAFT:
            print("Cannot delete: Status is not DRAFT")
            return False
        
        print("Declaration can be deleted")
        return True

    def delete(self, *args, **kwargs):
        """Override delete to handle cleanup"""
        if not self.can_be_deleted():
            raise ValidationError("Cannot delete this declaration")
            
        with transaction.atomic():
            # Revert Receipt VAT marks
            receipt_details = self.details.filter(source_type='receipt')
            for detail in receipt_details:
                for model in [CheckReceipt, LCN, TransferReceipt, CashReceipt]:
                    try:
                        receipt = model.objects.get(id=detail.source_id)
                        if receipt.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                            receipt.vat_declared = False
                            receipt.vat_declaration_period = None
                            receipt.save()
                    except model.DoesNotExist:
                        continue

            # Revert Check payment VAT marks
            check_details = self.details.filter(source_type='invoice_check')
            for detail in check_details:
                try:
                    check = Check.objects.get(id=detail.source_id)
                    if check.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                        check.vat_declared = False
                        check.vat_declaration_period = None
                        check.save()
                except Check.DoesNotExist:
                    continue

            # Revert Direct Debit VAT marks
            debit_details = self.details.filter(source_type='invoice_direct_debit')
            for detail in debit_details:
                try:
                    debit = DirectDebit.objects.get(id=detail.source_id)
                    if debit.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                        debit.vat_declared = False
                        debit.vat_declaration_period = None
                        debit.save()
                except DirectDebit.DoesNotExist:
                    continue

            # Revert Bank Fee VAT marks
            fee_details = self.details.filter(source_type='bank_fee')
            for detail in fee_details:
                try:
                    fee = BankFeeTransaction.objects.get(id=detail.source_id)
                    if fee.vat_declaration_period == f"{self.period_month:02d}-{self.period_year}":
                        fee.vat_declared = False
                        fee.vat_declaration_period = None
                        fee.save()
                except BankFeeTransaction.DoesNotExist:
                    continue

            # Delete details and forecast
            self.details.all().delete()
            if self.forecast:
                self.forecast.delete()
                
            # Call parent delete
            super().delete(*args, **kwargs)


    def clean(self):
        super().clean()
        if self.status != self.DRAFT and not self.is_processed:
            raise ValidationError("Declaration must be processed before being declared or paid")

    def save(self, *args, **kwargs):
        print("\n=== Saving VAT Declaration ===")
        print(f"Period: {self.period_month}/{self.period_year}")
        print(f"Status: {self.status}")
        print(f"Is Processed: {self.is_processed}")
        print(f"Total Invoiced VAT: {self.total_invoiced_vat}")
        print(f"Total Deducted VAT: {self.total_deducted_vat}")

        is_new = not self.pk
        print(f"Is new declaration: {is_new}")

        # Calculate due date if not set
        if not self.due_date:
            config = VATConfiguration.objects.first()
            if not config:
                raise ValidationError("VAT Configuration must exist before creating declarations")
            
            # Set to declaration day of next month
            self.due_date = datetime.date(
                self.period_year + (self.period_month == 12),
                (self.period_month % 12) + 1,
                min(config.declaration_day, calendar.monthrange(
                    self.period_year + (self.period_month == 12),
                    (self.period_month % 12) + 1
                )[1])
            )
            
            # Skip weekends
            while self.due_date.weekday() >= 5:
                self.due_date += timedelta(days=1)
        
        # Save declaration
        super().save(*args, **kwargs)
        
        # Handle forecasts
        if self.is_processed:
            print("\nUpdating forecasts for processed declaration")
            
            # Delete any existing forecasts for this period
            ForecastStatement.objects.filter(
                source_type='vat_declaration',
                source_id=self.id,
                is_processed=False
            ).delete()
            
            # Create new forecast with actual amount
            net_amount = self.total_invoiced_vat - self.total_deducted_vat
            
            if net_amount != 0:
                print(f"Creating new forecast with actual amount: {net_amount}")
                ForecastStatement.objects.create(
                    bank_account=VATConfiguration.get_config().domiciliation_bank,
                    date=self.due_date,
                    label=f"VAT Payment {self.period_month:02d}/{self.period_year}",
                    debit=net_amount if net_amount > 0 else None,
                    credit=abs(net_amount) if net_amount < 0 else None,
                    reference=f"VAT-{self.period_month:02d}-{self.period_year}",
                    source_type='vat_declaration',
                    source_id=self.id,
                    amount=net_amount
                )
            
            # Ensure we maintain 12 months of forecasts
            print("\nGenerating forecasts after save")
            self.__class__.generate_forecasts()

class VATDeclarationDetail(BaseModel):
    """Individual entries in VAT declaration"""
    declaration = models.ForeignKey(
        VATDeclaration,
        on_delete=models.CASCADE,
        related_name='details'
    )
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('receipt', 'Receipt Payment'),
            ('invoice_check', 'Invoice Check Payment'),
            ('invoice_direct_debit', 'Invoice Direct Debit')
        ]
    )
    source_id = models.UUIDField()
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_deducted = models.BooleanField(default=False)
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="VAT rate for this entry"
    )
    original_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Original amount before credits"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Credit note amount"
    )
    
    def __str__(self):
        return f"VAT Detail {self.source_type} - {self.vat_amount}"

    def clean(self):
        super().clean()
        if self.declaration.status != VATDeclaration.DRAFT:
            raise ValidationError("Cannot modify details of a declared VAT declaration")
        
    def _store_receipt_details(self):
        """Store VAT details for paid receipts"""
        print("\n=== Storing Receipt VAT Details ===")
        
        period_start = datetime.date(self.period_year, self.period_month, 1)
        period_end = datetime.date(
            self.period_year + (self.period_month == 12),
            (self.period_month % 12) + 1,
            1
        ) - timedelta(days=1)
        
        # Process CheckReceipts
        check_receipts = CheckReceipt.objects.filter(
            status='PAID',
            paid_date__range=(period_start, period_end)
        )
        
        for receipt in check_receipts:
            vat_amount = receipt.amount / Decimal('6')
            print(f"Check Receipt #{receipt.check_number}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=receipt.id,
                vat_amount=vat_amount,
                is_deducted=False
            )
        
        # Process LCNs
        lcns = LCN.objects.filter(
            status='PAID',
            paid_date__range=(period_start, period_end)
        )
        
        for lcn in lcns:
            vat_amount = lcn.amount / Decimal('6')
            print(f"LCN #{lcn.lcn_number}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=lcn.id,
                vat_amount=vat_amount,
                is_deducted=False
            )

        # Process TransferReceipts
        transfers = TransferReceipt.objects.filter(
            operation_date__range=(period_start, period_end)
        )
        
        for transfer in transfers:
            vat_amount = transfer.amount / Decimal('6')
            print(f"Transfer #{transfer.transfer_reference}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=transfer.id,
                vat_amount=vat_amount,
                is_deducted=False
            )

        # Process CashReceipts
        cash_receipts = CashReceipt.objects.filter(
            operation_date__range=(period_start, period_end)
        )
        
        for receipt in cash_receipts:
            vat_amount = receipt.amount / Decimal('6')
            print(f"Cash Receipt #{receipt.reference_number}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='receipt',
                source_id=receipt.id,
                vat_amount=vat_amount,
                is_deducted=False
            )

    def _store_payment_details(self):
        """Store VAT details for invoice payments"""
        print("\n=== Storing Payment VAT Details ===")
        
        period_start = datetime.date(self.period_year, self.period_month, 1)
        period_end = datetime.date(
            self.period_year + (self.period_month == 12),
            (self.period_month % 12) + 1,
            1
        ) - timedelta(days=1)
        
        # Process Check payments
        checks = Check.objects.filter(
            Q(
                paid_at__range=(period_start, period_end),
                vat_declared=False
            ) | Q(
                vat_declared=False,
                paid_at__lt=period_start
            )
        ).select_related('cause')
        
        for check in checks:
            if not check.cause or check.cause.non_deductible_vat:
                continue
                
            payment_percentage = (check.amount / check.cause.total_amount) * Decimal('100.00')
            vat_amount = (
                check.cause.total_tax_amount * 
                (payment_percentage / Decimal('100.00')) *
                #(check.cause.vat_deduction_rate / Decimal('100.00'))
                Decimal('100.00') / Decimal('100.00')
            )
            
            print(f"Check {check.position} for invoice {check.cause.ref}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='invoice_check',
                source_id=check.id,
                vat_amount=vat_amount,
                is_deducted=True
            )
            
            # Mark check as declared
            check.vat_declared = True
            check.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            check.save()

        # Process DirectDebit payments
        direct_debits = DirectDebit.objects.filter(
            Q(
                processed_date__range=(period_start, period_end),
                vat_declared=False
            ) | Q(
                vat_declared=False,
                processed_date__lt=period_start
            )
        ).select_related('invoice__invoice')
        
        for debit in direct_debits:
            invoice = debit.invoice.invoice
            if not invoice or invoice.non_deductible_vat:
                continue
                
            payment_percentage = (debit.amount / invoice.total_amount) * Decimal('100.00')
            vat_amount = (
                invoice.total_tax_amount * 
                (payment_percentage / Decimal('100.00')) *
                (invoice.vat_deduction_rate / Decimal('100.00'))
            )
            
            print(f"Direct Debit for invoice {invoice.ref}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='invoice_direct_debit',
                source_id=debit.id,
                vat_amount=vat_amount,
                is_deducted=True
            )
            
            # Mark direct debit as declared
            debit.vat_declared = True
            debit.vat_declaration_period = f"{self.period_month:02d}-{self.period_year}"
            debit.save()
        
        # Process bank fees
        bank_fees = BankFeeTransaction.objects.filter(
            date__range=(period_start, period_end)
        ).select_related('fee_type')
        
        for fee in bank_fees:
            vat_amount = fee.vat_amount
            print(f"Bank Fee #{fee.id}: VAT = {vat_amount}")
            VATDeclarationDetail.objects.create(
                declaration=self,
                source_type='bank_fee',
                source_id=fee.id,
                vat_amount=vat_amount,
                is_deducted=False
            )


    def mark_as_paid(self, payment_date):
        """Mark declaration as paid"""
        print(f"\n=== Marking VAT Declaration {self.period_month}/{self.period_year} as Paid ===")
        
        if not self.is_processed:
            raise ValidationError("Declaration must be processed before payment")
            
        if self.status != self.DECLARED:
            raise ValidationError("Can only pay declared VAT declarations")
        
        if payment_date < self.due_date:
            raise ValidationError("Payment date cannot be before due date")
        
        self.payment_date = payment_date
        self.status = self.PAID
        
        # Mark forecast as processed if exists
        if self.forecast:
            self.forecast.is_processed = True
            self.forecast.save()
            print(f"Marked forecast {self.forecast.id} as processed")
        
        self.save()


class PayConfiguration(BaseModel):
    """Global configuration for pay/salary management"""
    print("\n=== PayConfiguration Model ===")
    
    PERIOD_MONTHLY = 'monthly'
    PERIOD_CHOICES = [
        (PERIOD_MONTHLY, 'Monthly'),
    ]
    
    generation_day = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month to generate declaration (1-28)"
    )
    periodicity = models.CharField(
        max_length=20, 
        choices=PERIOD_CHOICES,
        default=PERIOD_MONTHLY
    )
    account_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ],
        help_text="Main account code for pay operations"
    )
    domiciliation_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='pay_declarations'
    )
    journal_code = models.CharField(
        max_length=2,
        default='07',
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ]
    )
    
    def clean(self):
        super().clean()
        if self.pk and PayConfiguration.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one pay configuration can exist")
            
    def save(self, *args, **kwargs):
        print("\n=== Saving PayConfiguration ===")
        print(f"Generation day: {self.generation_day}")
        print(f"Bank: {self.domiciliation_bank}")
        
        if not self.pk and PayConfiguration.objects.exists():
            raise ValidationError("Only one pay configuration can exist")
            
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create pay configuration"""
        config = PayConfiguration.objects.first()
        if not config:
            raise ValidationError("Pay Configuration must be set up")
        return config

    def get_next_generation_date(self, from_date=None):
        """Calculate next declaration generation date"""
        print(f"\n=== Getting next generation date from {from_date} ===")
        if not from_date:
            from_date = timezone.now().date()

        # Start with the generation day in current month
        next_date = from_date.replace(day=min(self.generation_day, 28))
        
        # If we've passed this month's generation day, move to next month
        if from_date.day > self.generation_day:
            next_date = next_date + relativedelta(months=1)
            
        print(f"Next generation date: {next_date}")
        return next_date

    def __str__(self):
        return f"Pay Configuration (Generation Day: {self.generation_day})"

class PayItem(BaseModel):
    """Template for pay declaration items"""
    print("\n=== PayItem Model ===")
    
    description = models.CharField(max_length=255)
    account_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ]
    )
    default_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_debit = models.BooleanField(
        default=True,
        help_text="If True, amount is recorded as debit; if False, as credit"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.description} ({self.account_code})"

    class Meta:
        ordering = ['description']

class PayDeclaration(BaseModel):
    """Monthly pay declaration"""
    print("\n=== PayDeclaration Model ===")
    
    STATUS_DRAFT = 'draft'
    STATUS_DECLARED = 'declared'
    STATUS_PAID = 'paid'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_DECLARED, 'Declared'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected')
    ]
    
    period_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    period_year = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    forecast = models.OneToOneField(
        'ForecastStatement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pay_declaration'
    )
    paid_by_check = models.BooleanField(
        default=False,
        help_text="If True, paid by check instead of direct debit"
    )
    payment_check = models.ForeignKey(
        'Check',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='pay_declarations'
    )
    direct_debit = models.OneToOneField(
        'DirectDebit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pay_declaration'
    )
    rejection_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    def clean(self):
        super().clean()
        # Ensure payment method consistency
        if self.paid_by_check and self.direct_debit:
            raise ValidationError("Declaration cannot have both check and direct debit")
        if self.paid_by_check and not self.check and self.status == self.STATUS_PAID:
            raise ValidationError("Check payment requires check reference")
            
    def save(self, *args, **kwargs):
        print(f"\n=== Saving PayDeclaration for {self.period_month}/{self.period_year} ===")
        print(f"Status: {self.status}")
        print(f"Total: {self.total_amount}")
        
        # Calculate due date on first save
        if not self.pk and not self.due_date:
            config = PayConfiguration.get_config()
            # Set to generation day of this period
            self.due_date = date(
                self.period_year,  
                self.period_month,
                min(config.generation_day, calendar.monthrange(
                    self.period_year, self.period_month
                )[1])
            )
            
            # Skip weekends
            while self.due_date.weekday() >= 5:
                self.due_date += timedelta(days=1)
                
            print(f"Calculated due date: {self.due_date}")
            
        super().save(*args, **kwargs)

    def mark_as_paid(self, payment_date):
        """Mark declaration as paid and handle related records"""
        print(f"\n=== Marking declaration {self.period_month}/{self.period_year} as paid ===")
        print(f"Payment date: {payment_date}")
        
        if self.status == self.STATUS_PAID:
            return
            
        self.payment_date = payment_date
        self.status = self.STATUS_PAID
        
        # Mark forecast as processed
        if self.forecast:
            self.forecast.is_processed = True
            self.forecast.save()
            print(f"Marked forecast {self.forecast.id} as processed")
            
        self.save()
        
    def mark_as_rejected(self, rejection_date, reason):
        """Mark declaration as rejected"""
        print(f"\n=== Marking declaration {self.period_month}/{self.period_year} as rejected ===")
        print(f"Rejection date: {rejection_date}")
        print(f"Reason: {reason}")
        
        if self.status == self.STATUS_REJECTED:
            return
            
        self.status = self.STATUS_REJECTED
        self.rejection_reason = reason
        
        if self.forecast:
            self.forecast.is_processed = False
            self.forecast.save()
            print(f"Unmarked forecast {self.forecast.id}")
            
        self.save()

    def __str__(self):
        return f"Pay Declaration {self.period_month}/{self.period_year}"

    class Meta:
        ordering = ['-period_year', '-period_month']
        constraints = [
            models.UniqueConstraint(
                fields=['period_month', 'period_year'],
                name='unique_pay_period'
            )
        ]

class PayDeclarationItem(BaseModel):
    """Individual items in a pay declaration"""
    print("\n=== PayDeclarationItem Model ===")
    
    declaration = models.ForeignKey(
        PayDeclaration,
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(max_length=255)
    account_code = models.CharField(
        max_length=5,
        validators=[
            RegexValidator(r'^\d{4,5}$', 'Account code must be 4-5 digits')
        ]
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_debit = models.BooleanField(default=True)
    template_item = models.ForeignKey(
        PayItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='declaration_items'
    )
    
    def clean(self):
        super().clean()
        # If declaration is paid, total mustn't change
        if (self.declaration.status == PayDeclaration.STATUS_PAID and 
            self.pk and self.amount != self.__class__.objects.get(pk=self.pk).amount):
            raise ValidationError("Cannot modify amounts of paid declaration")

    def __str__(self):
        return f"{self.description} ({self.amount})"

    class Meta:
        ordering = ['description']

class BrickType(BaseModel):
    """Defines different types of bricks available for production"""
    name = models.CharField(max_length=100, unique=True)
    industrial_code = models.CharField(max_length=50, unique=True)
    length = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    width = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    height = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    bricks_per_wagon = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def get_current_prices(self):
        """Get current bulk and packaged prices"""
        bulk_price = self.price_history.filter(
            is_packaged=False,
            effective_date__lte=timezone.now()
        ).order_by('-effective_date').first()

        packaged_price = self.price_history.filter(
            is_packaged=True,
            effective_date__lte=timezone.now()
        ).order_by('-effective_date').first()

        return {
            'bulk_price': bulk_price.price if bulk_price else None,
            'packaged_price': packaged_price.price if packaged_price else None
        }

    def __str__(self):
        return f"{self.name} ({self.industrial_code})"

class BrickPriceHistory(BaseModel):
    """Tracks price changes for bricks over time"""
    brick_type = models.ForeignKey(
        BrickType, 
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_packaged = models.BooleanField(
        help_text="True for packaged bricks, False for bulk"
    )
    effective_date = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-effective_date']
        get_latest_by = 'effective_date'

class ProductionBatch(BaseModel):
    """Records daily production data for each brick type"""
    production_date = models.DateField()
    vpower = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Manual override for calculated VPower"
    )
    calculated_vpower = models.PositiveIntegerField(
        help_text="Automatically calculated industrial power (minutes)"
    )
    notes = models.TextField(blank=True)

    def calculate_vpower(self):
        """Calculate VPower based on total wagons produced"""
        total_wagons = sum(detail.wagons_produced for detail in self.brick_productions.all())
        if total_wagons == 0:
            return 0
        return int((24 * 60) / (total_wagons * 3))

    def save(self, *args, **kwargs):
        self.calculated_vpower = self.calculate_vpower()
        super().save(*args, **kwargs)

    @property
    def effective_vpower(self):
        """Returns manual VPower if set, otherwise calculated value"""
        return self.vpower if self.vpower is not None else self.calculated_vpower

    class Meta:
        ordering = ['-production_date']

    @property
    def total_production(self):
        return sum(prod.total_bricks_produced for prod in self.brick_productions.all())

class BrickProduction(BaseModel):
    """Records production details for each brick type in a batch"""
    production_batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='brick_productions'
    )
    brick_type = models.ForeignKey(
        'BrickType',
        on_delete=models.PROTECT
    )
    wagons_produced = models.PositiveIntegerField()
    miscellaneous_adjustment = models.IntegerField(
        default=0,
        help_text="Positive or negative adjustment to account for production anomalies"
    )
    bricks_packaged = models.PositiveIntegerField(default=0)
    bulk_price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    packaged_price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    @property
    def total_bricks_produced(self):
        """Calculate total bricks produced, including miscellaneous adjustments"""
        try:
            wagons = int(self.wagons_produced)
            bricks_per_wagon = int(self.brick_type.bricks_per_wagon)
            misc_adj = int(self.miscellaneous_adjustment)
            
            base_production = wagons * bricks_per_wagon
            return base_production + misc_adj
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating total_bricks_produced: {str(e)}")
            # Default to zero if calculation fails
            return 0

    @property
    def available_for_packaging(self):
        """Calculate bricks available for packaging"""
        try:
            total = int(self.total_bricks_produced)
            packaged = int(self.bricks_packaged)
            return total - packaged
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating available_for_packaging: {str(e)}")
            return 0

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Get values as integers
        total = int(self.total_bricks_produced)
        packaged = int(self.bricks_packaged)
        
        if packaged > total:
            raise ValidationError({
                'bricks_packaged': 'Cannot package more bricks than produced'
            })

    def save(self, *args, **kwargs):
        if not self.bulk_price_at_time or not self.packaged_price_at_time:
            prices = self.brick_type.get_current_prices()
            self.bulk_price_at_time = prices['bulk_price']
            self.packaged_price_at_time = prices['packaged_price']
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['production_batch', 'brick_type']

class BrickStock(BaseModel):
    """Tracks current stock levels for each brick type"""
    brick_type = models.OneToOneField(
        BrickType, 
        on_delete=models.CASCADE,
        related_name='stock'
    )
    bulk_quantity = models.PositiveIntegerField(default=0)
    packaged_quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def update_stock(self, bulk_change=0, packaged_change=0):
        """
        Update stock levels, ensuring they don't go negative
        Returns tuple of (success, message)
        """
        new_bulk = self.bulk_quantity + bulk_change
        new_packaged = self.packaged_quantity + packaged_change
        
        if new_bulk < 0:
            return False, f"Insufficient bulk stock ({self.bulk_quantity})"
        if new_packaged < 0:
            return False, f"Insufficient packaged stock ({self.packaged_quantity})"
            
        self.bulk_quantity = new_bulk
        self.packaged_quantity = new_packaged
        self.save()
        return True, "Stock updated successfully"

    def __str__(self):
        return f"{self.brick_type.name} Stock"

class LoadingRecord(BaseModel):
    """Records brick loading operations"""
    brick_type = models.ForeignKey(BrickType, on_delete=models.PROTECT)
    loading_date = models.DateField()
    bulk_quantity = models.PositiveIntegerField(default=0)
    packaged_quantity = models.PositiveIntegerField(default=0)
    bulk_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    packaged_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Get prices effective on loading date
        prices = self.brick_type.get_current_prices()
        self.bulk_price = prices['bulk_price']
        self.packaged_price = prices['packaged_price']
        
        # Update stock
        stock = BrickStock.objects.get(brick_type=self.brick_type)
        success, message = stock.update_stock(
            bulk_change=-self.bulk_quantity,
            packaged_change=-self.packaged_quantity
        )
        
        if not success:
            raise ValueError(message)
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-loading_date']

    @property
    def total_value(self):
        bulk_value = self.bulk_quantity * self.bulk_price
        packaged_value = self.packaged_quantity * self.packaged_price
        return bulk_value + packaged_value

class LoadingRecord(BaseModel):
    """Records a loading operation on a specific date"""
    loading_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-loading_date']
        verbose_name = "Loading Record"
        verbose_name_plural = "Loading Records"

    def __str__(self):
        return f"Loading on {self.loading_date}"

class LoadingItem(BaseModel):
    """Records details of loaded items in a loading record"""
    loading_record = models.ForeignKey(
        LoadingRecord,
        on_delete=models.CASCADE,
        related_name='items'
    )
    brick_type = models.ForeignKey(
        BrickType,
        on_delete=models.PROTECT
    )
    bulk_quantity = models.PositiveIntegerField(default=0)
    packaged_quantity = models.PositiveIntegerField(default=0)
    breakage = models.PositiveIntegerField(default=0)
    bulk_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    packaged_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['brick_type__name']
        unique_together = ['loading_record', 'brick_type']
        
    def __str__(self):
        return f"{self.brick_type.name} - Bulk: {self.bulk_quantity}, Packaged: {self.packaged_quantity}"

class DailyProductionMetrics(BaseModel):
    """Tracks daily production metrics including industrial power (VPower)"""
    production_date = models.DateField(unique=True)
    calculated_vpower = models.PositiveIntegerField(
        help_text="Automatically calculated industrial power (minutes)"
    )
    manual_vpower = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Manually set industrial power, overrides calculated value"
    )
    notes = models.TextField(blank=True)

    @property
    def vpower(self):
        """Returns manual VPower if set, otherwise calculated value"""
        return self.manual_vpower if self.manual_vpower is not None else self.calculated_vpower

    def calculate_vpower(self):
        """Calculate VPower based on total wagons produced"""
        # Get all production batches for this date
        daily_batches = ProductionBatch.objects.filter(production_date=self.production_date)
        total_wagons = sum(batch.wagons_produced for batch in daily_batches)
        
        if total_wagons == 0:
            return 0
            
        # VPower formula: (24 hours * 60 minutes) / (total wagons * 3)
        self.calculated_vpower = int((24 * 60) / (total_wagons * 3))
        return self.calculated_vpower

    def save(self, *args, **kwargs):
        if not self.calculated_vpower:
            self.calculate_vpower()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-production_date']
        verbose_name = "Daily Production Metrics"
        verbose_name_plural = "Daily Production Metrics"


class EnergyType(BaseModel):
    """Defines different types of energy used in production"""
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=50)  # e.g., kWh, ton, liter
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def get_current_price(self):
        """Get current energy price"""
        current_price = self.price_history.filter(
            effective_date__lte=timezone.now()
        ).order_by('-effective_date').first()
        return current_price.price if current_price else None

    def __str__(self):
        return f"{self.name} ({self.unit})"

    class Meta:
        verbose_name = "Energy Type"
        verbose_name_plural = "Energy Types"

class EnergyPriceHistory(BaseModel):
    """Tracks price changes for energy types over time"""
    energy_type = models.ForeignKey(
        EnergyType,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    effective_date = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-effective_date']
        get_latest_by = 'effective_date'

class ProductionEnergy(BaseModel):
    """Records energy consumption for a production batch"""
    production_batch = models.ForeignKey(
        'ProductionBatch',
        on_delete=models.CASCADE,
        related_name='energy_consumption'
    )
    energy_type = models.ForeignKey(
        'EnergyType',
        on_delete=models.PROTECT
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def save(self, *args, **kwargs):
        if not self.price_at_time:
            self.price_at_time = self.energy_type.get_current_price()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['production_batch', 'energy_type']

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

    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('SIGNATURE_MISMATCH', 'Signature Mismatch'),
        ('TECHNICAL_ERROR', 'Technical Error'),
        ('BANK_ERROR', 'Bank Processing Error'),
        ('OTHER', 'Other')
    ]

    declaration_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload declaration receipt"
    )

    payment_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload payment receipt"
    )
    
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
    rejection_cause = models.CharField(
        max_length=20,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True,
        help_text="Reason for rejection"
    )
    rejection_notes = models.TextField(
        blank=True,
        help_text="Additional notes about rejection"
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
        
        # Delete ALL existing forecasts for this period (important new step)
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
        
        
        print("IR declaration marked as paid")

    def mark_as_rejected(self, rejection_date=None, rejection_cause=None, rejection_notes=None):
        """Mark declaration as rejected with cause and notes"""
        print(f"\n=== Marking IR declaration {self.period_month}/{self.period_year} as rejected ===")
        
        self.status = 'rejected'
        self.rejection_date = rejection_date or timezone.now().date()
        self.payment_date = None
        
        # Store rejection cause and notes
        if rejection_cause:
            self.rejection_cause = rejection_cause
        if rejection_notes:
            self.rejection_notes = rejection_notes
        
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



class StampRightConfiguration(BaseModel):
    """Configuration for Stamp Rights tax management"""
    accounting_code = models.CharField(
        max_length=10,
        default='44526',  # Adjusted from IR code
        validators=[
            RegexValidator(r'^\d{4,10}$', 'Account code must be 4-10 digits')
        ],
        help_text="Accounting code for Stamp Rights operations"
    )
    journal_code = models.CharField(
        max_length=2,
        default='06',  # Adjusted from IR code
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ]
    )
    domiciliation_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='stamp_rights_declarations',
        help_text="Bank account used for Stamp Rights payments"
    )
    default_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Default Stamp Rights amount for forecasts"
    )
    declaration_day = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month when Stamp Rights declarations are due"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.25'),
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('10.00'))],
        help_text="Tax rate percentage for Stamp Rights"
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
        help_text="Frequency of Stamp Rights declarations"
    )

    @classmethod
    def get_config(cls):
        """Get or create Stamp Rights configuration"""
        config = StampRightConfiguration.objects.first()
        if not config:
            raise ValidationError("Stamp Rights Configuration must be set up")
        return config

    def __str__(self):
        return f"Stamp Rights Configuration (Bank: {self.domiciliation_bank.bank})"

    class Meta:
        verbose_name = "Stamp Rights Configuration"
        verbose_name_plural = "Stamp Rights Configuration"


class StampRightDeclaration(BaseModel):
    """Stamp Rights declaration"""
    STATUS_CHOICES = [
        ('declared', 'Declared'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected')
    ]

    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('SIGNATURE_MISMATCH', 'Signature Mismatch'),
        ('TECHNICAL_ERROR', 'Technical Error'),
        ('BANK_ERROR', 'Bank Processing Error'),
        ('OTHER', 'Other')
    ]

    declaration_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload declaration receipt"
    )

    payment_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload payment receipt"
    )

    period_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    period_year = models.PositiveSmallIntegerField()
    invoices_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total amount of invoices paid in cash"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total Stamp Rights tax amount"
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
    rejection_cause = models.CharField(
        max_length=20,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True,
        help_text="Reason for rejection"
    )
    rejection_notes = models.TextField(
        blank=True,
        help_text="Additional notes about rejection"
    )
    forecast = models.ForeignKey(
        'ForecastStatement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stamp_right_declaration'
    )

    def save(self, *args, **kwargs):
        print("\n=== Saving StampRightDeclaration ===")
        print(f"Period: {self.period_month}/{self.period_year}")
        
        # Calculate tax amount based on rate from configuration
        config = StampRightConfiguration.get_config()
        if not self.tax_amount or self.tax_amount == 0:
            # Calculate tax amount and round up to the nearest integer
            raw_tax_amount = (self.invoices_amount * config.tax_rate) / Decimal('100.0')
            self.tax_amount = Decimal(math.ceil(raw_tax_amount))
            print(f"Calculated tax amount: {self.tax_amount} (rounded up from {raw_tax_amount}, rate: {config.tax_rate}%)")
        
        
        if not self.due_date:
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
        print("\n=== Updating Stamp Rights Forecast ===")
        
        # Delete old forecast if exists
        if self.forecast:
            print(f"Deleting old forecast: {self.forecast.id}")
            self.forecast.delete()
            self.forecast = None
        
        # Don't create forecast for paid or rejected declarations
        if self.status in ['paid', 'rejected']:
            print(f"Not creating forecast for {self.status} declaration")
            return
        
        # Delete ALL existing forecasts for this period
        existing_forecasts = ForecastStatement.objects.filter(
            bank_account=StampRightConfiguration.get_config().domiciliation_bank,
            label__icontains=f"{self.period_month:02d}/{self.period_year}",
            source_type="stamp_right_declaration",
            is_processed=False
        )
        
        if existing_forecasts.exists():
            print(f"Deleting {existing_forecasts.count()} existing forecasts for period {self.period_month:02d}/{self.period_year}")
            existing_forecasts.delete()

        # Create new forecast
        config = StampRightConfiguration.get_config()
        
        forecast = ForecastStatement.objects.create(
            bank_account=config.domiciliation_bank,
            date=self.due_date,
            label=f"Stamp Rights Payment {self.period_month:02d}/{self.period_year}",
            debit=self.tax_amount,
            reference=f"SR-{self.period_month:02d}-{self.period_year}",
            source_type="stamp_right_declaration",
            source_id=self.id,
            amount=self.tax_amount
        )
        
        self.forecast = forecast
        print(f"Created new forecast: {forecast.id}")
        
        # Generate next year's forecasts
        self._generate_future_forecasts()

    def _generate_future_forecasts(self):
        """Generate forecasts for the next periods"""
        print("\n=== Generating Future Stamp Rights Forecasts ===")
        
        config = StampRightConfiguration.get_config()
        
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
            if StampRightDeclaration.objects.filter(
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
                    source_type="stamp_right_declaration",
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
                    label=f"Stamp Rights Forecast {current_month:02d}/{current_year}",
                    debit=config.default_amount,
                    reference=f"SR-{current_month:02d}-{current_year}",
                    source_type="stamp_right_declaration",
                    source_id=uuid.uuid4(),
                    amount=config.default_amount
                )
                print(f"Created forecast for {current_month}/{current_year}")
                
            except Exception as e:
                print(f"Error creating forecast for {current_month}/{current_year}: {str(e)}")

    def mark_as_paid(self, payment_date=None):
        """Mark declaration as paid"""
        print(f"\n=== Marking Stamp Rights declaration {self.period_month}/{self.period_year} as paid ===")
        
        self.status = 'paid'
        self.payment_date = payment_date or timezone.now().date()
        self.rejection_date = None
        
        # Update forecast (will be deleted)
        self._update_forecast()
        self.save()
        
        
        print("Stamp Rights declaration marked as paid")

    def mark_as_rejected(self, rejection_date=None, rejection_cause=None, rejection_notes=None):
        """Mark declaration as rejected with cause and notes"""
        print(f"\n=== Marking Stamp Rights declaration {self.period_month}/{self.period_year} as rejected ===")
        
        self.status = 'rejected'
        self.rejection_date = rejection_date or timezone.now().date()
        self.payment_date = None
        
        # Store rejection cause and notes
        if rejection_cause:
            self.rejection_cause = rejection_cause
        if rejection_notes:
            self.rejection_notes = rejection_notes
        
        # Update forecast (will be deleted)
        self._update_forecast()
        self.save()
        
        print("Stamp Rights declaration marked as rejected")


    def __str__(self):
        return f"Stamp Rights Declaration {self.period_month:02d}/{self.period_year}"

    class Meta:
        ordering = ['-period_year', '-period_month']
        verbose_name = "Stamp Rights Declaration"
        verbose_name_plural = "Stamp Rights Declarations"


class OtherTaxConfiguration(BaseModel):
    """Configuration for other taxes like Professional and Communal taxes"""
    
    TAX_TYPE_CHOICES = [
        ('professional', 'Professional Tax'),
        ('communal', 'Communal Tax'),
    ]
    
    tax_type = models.CharField(
        max_length=20,
        choices=TAX_TYPE_CHOICES,
        unique=True,
        help_text="Type of tax"
    )
    
    accounting_code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(r'^\d{4,10}$', 'Account code must be 4-10 digits')
        ],
        help_text="Accounting code for tax operations"
    )
    
    journal_code = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(r'^\d{2}$', 'Journal must be exactly 2 digits')
        ],
        help_text="Journal code for accounting entries"
    )
    
    domiciliation_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='other_tax_configurations',
        null=True,
        blank=True,
        help_text="Bank account used for tax payments if using direct debit"
    )

    forecast_bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='other_tax_forecasts',
        null=True,
        blank=True,
        help_text="Bank account used for tax payment forecasts"
    )
    
    default_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Default tax amount for forecasts"
    )
    
    due_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month when the tax is due"
    )
    
    due_day = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month when tax declarations are due"
    )
    
    fines_accounting_code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(r'^\d{4,10}$', 'Account code must be 4-10 digits')
        ],
        help_text="Accounting code for tax fines"
    )
    
    @classmethod
    def get_config(cls, tax_type):
        """Get config for specific tax type"""
        print(f"\n=== Getting {tax_type} Tax Configuration ===")
        config = cls.objects.filter(tax_type=tax_type).first()
        if not config:
            raise ValidationError(f"{tax_type.title()} Tax Configuration must be set up")
        return config
    
    def __str__(self):
        return f"{self.get_tax_type_display()} Configuration"

    class Meta:
        verbose_name = "Other Tax Configuration"
        verbose_name_plural = "Other Tax Configurations"


class OtherTaxDeclaration(BaseModel):
    """Declaration for other taxes like Professional and Communal"""
    
    TAX_TYPE_CHOICES = [
        ('professional', 'Professional Tax'),
        ('communal', 'Communal Tax'),
    ]
    
    STATUS_CHOICES = [
        ('declared', 'Declared'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('direct_debit', 'Direct Debit'),
        ('check', 'Check'),
        ('lcn', 'LCN'),
        ('cash', 'Cash'),
    ]
    
    REJECTION_CAUSES = [
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('ACCOUNT_CLOSED', 'Account Closed/Frozen'),
        ('SIGNATURE_MISMATCH', 'Signature Mismatch'),
        ('TECHNICAL_ERROR', 'Technical Error'),
        ('BANK_ERROR', 'Bank Processing Error'),
        ('OTHER', 'Other')
    ]
    
    tax_type = models.CharField(
        max_length=20,
        choices=TAX_TYPE_CHOICES,
        help_text="Type of tax"
    )
    
    year = models.PositiveSmallIntegerField(
        help_text="Tax year"
    )
    
    reference = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique reference for this declaration"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total tax amount"
    )
    
    due_date = models.DateField(
        help_text="Date when the tax is due"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='declared'
    )
    
    payment_method = models.CharField(
        max_length=15,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Method used to pay the tax"
    )
    
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the tax was paid"
    )
    
    rejection_cause = models.CharField(
        max_length=20,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True,
        help_text="Reason for rejection"
    )
    
    rejection_notes = models.TextField(
        blank=True,
        help_text="Additional notes about rejection"
    )
    
    rejection_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the payment was rejected"
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
        related_name='other_tax_declaration'
    )
    
    # Document fields
    tax_notice_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload tax notice document"
    )
    
    payment_receipt_document = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        null=True,
        blank=True,
        help_text="Upload payment receipt document"
    )
    
    # For balance tracking
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount already paid"
    )

    checks = GenericRelation(
        'Check',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='other_tax_declaration'
    )

    @property
    def grand_total(self):
        """Get total amount including fines"""
        # Base amount remaining
        base_remaining = self.amount - self.paid_amount
        
        # Add unpaid fines
        fines_total = sum(fine.amount for fine in self.fines.filter(paid=False))
        
        return base_remaining + fines_total
        
    def save(self, *args, **kwargs):
        print("\n=== Saving OtherTaxDeclaration ===")
        print(f"Type: {self.tax_type}")
        print(f"Year: {self.year}")
        print(f"Amount: {self.amount}")
        print(f"Update fields: {kwargs.get('update_fields')}")
        
        # Skip forecast updates if we're just updating payment fields
        update_fields = kwargs.get('update_fields')
        super().save(*args, **kwargs)

        # Generate reference if not set
        if not self.reference:
            # Generate reference in format: TAXTYPE-YEAR-SEQ
            tax_type_prefix = self.tax_type.upper()[:3]  # First 3 letters of tax type
            year = str(self.year)
            # Get count of existing declarations for this type and year
            seq = OtherTaxDeclaration.objects.filter(
                tax_type=self.tax_type,
                year=self.year
            ).count() + 1
            self.reference = f"{tax_type_prefix}-{year}-{seq:03d}"
        
        # Calculate due date if not set
        if not self.due_date:
            config = OtherTaxConfiguration.get_config(self.tax_type)
            day = config.due_day
            month = config.due_month
            
            # Create date with specified day, or last day of month if out of range
            last_day = calendar.monthrange(self.year, month)[1]
            if day > last_day:
                self.due_date = datetime.date(self.year, month, last_day)
            else:
                self.due_date = datetime.date(self.year, month, day)
            
            print(f"Set due date to {self.due_date}")
        
        # Update status based on paid_amount
        if self.paid_amount >= self.amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        
        # Create forecast only if not paid   
        if self.status != 'paid':
            self._update_forecast()
        else:
            print("Declaration is paid, skipping forecast creation")
            # Delete any existing forecasts for paid declarations
            if hasattr(self, 'forecast') and self.forecast:
                print(f"Deleting existing forecast for paid declaration: {self.forecast.id}")
                self.forecast.delete()
                self.forecast = None
        
        if not update_fields or 'paid_amount' not in update_fields:
            self.calculate_payment_status()
        
        super().save(*args, **kwargs)
    
    def _update_forecast(self):
        """Update or create forecast for this declaration"""
        print("\n=== Updating Tax Forecast ===")
        
        # Double check - don't create forecast for paid declarations
        if self.status == 'paid':
            print(f"Not creating forecast for paid declaration")
            # Delete any existing forecast for this declaration
            if self.forecast:
                print(f"Deleting forecast for paid declaration: {self.forecast.id}")
                self.forecast.delete()
                self.forecast = None
            return
        
        # Delete old forecast if exists
        if self.forecast:
            print(f"Deleting old forecast: {self.forecast.id}")
            self.forecast.delete()
            self.forecast = None
        
        # Get config
        config = OtherTaxConfiguration.get_config(self.tax_type)
        
        # Determine which bank to use
        bank_to_use = None
        if self.payment_method == 'direct_debit' and config.domiciliation_bank:
            bank_to_use = config.domiciliation_bank
        elif config.forecast_bank:
            bank_to_use = config.forecast_bank
        
        # Make sure bank is configured
        if not bank_to_use:
            print(f"No bank configured for {self.tax_type} forecasts")
            return
        print("Current year: ", self.year)
        
        # Delete existing forecasts only for THIS declaration (not all of same type)
        existing_forecasts = ForecastStatement.objects.filter(
            source_type=f"{self.tax_type}_tax",
            source_id=self.id,
            is_processed=False
        )
        
        if existing_forecasts.exists():
            print(f"Deleting {existing_forecasts.count()} existing forecasts for this declaration")
            existing_forecasts.delete()
        
        # Get remaining amount including unpaid fines using the remaining_amount property
        remaining_amount = self.remaining_amount
        
        # Create new forecast
        if remaining_amount > 0:
            forecast = ForecastStatement.objects.create(
                bank_account=bank_to_use,
                date=self.due_date,
                label=f"{self.tax_type.title()} Tax {self.year}",
                debit=remaining_amount,
                reference=f"{self.tax_type[:3].upper()}-{self.year}",
                source_type=f"{self.tax_type}_tax",
                source_id=self.id,
                amount=remaining_amount
            )
            
            self.forecast = forecast
            print(f"Created new forecast: {forecast.id}")
        
        # Only generate future forecast if current declaration is not paid
        if self.status != 'paid':
            self._generate_future_forecast()
        else:
            print("Skipping future forecast generation for paid declaration")
    
    def _generate_future_forecast(self):
        """Generate forecast for the next tax year"""
        print("\n=== Generating Future Tax Forecast ===")
        
        config = OtherTaxConfiguration.get_config(self.tax_type)
        next_year = self.year + 1
        
        # Check if declaration already exists for next year
        if OtherTaxDeclaration.objects.filter(
            tax_type=self.tax_type,
            year=next_year
        ).exists():
            print(f"Declaration already exists for {next_year}, skipping")
            return
        
        # Determine which bank to use
        bank_to_use = config.forecast_bank or config.domiciliation_bank
        if not bank_to_use:
            print(f"No bank configured for {self.tax_type} forecasts")
            return
            
        # Calculate due date for next year
        day = config.due_day
        month = config.due_month
        last_day = calendar.monthrange(next_year, month)[1]
        if day > last_day:
            due_date = datetime.date(next_year, month, last_day)
        else:
            due_date = datetime.date(next_year, month, day)
        
        # Check for existing forecasts for next year more carefully
        existing_forecast = ForecastStatement.objects.filter(
            source_type=f"{self.tax_type}_tax",
            label__icontains=f"{next_year}",
            is_processed=False
        ).first()
        
        if existing_forecast:
            print(f"Forecast already exists for {next_year}, skipping creation")
            return
        
        # Create forecast with default amount
        forecast = ForecastStatement.objects.create(
            bank_account=bank_to_use,
            date=due_date,
            label=f"{self.tax_type.title()} Tax Forecast {next_year}",
            debit=config.default_amount,
            reference=f"{self.tax_type[:3].upper()}-{next_year}",
            source_type=f"{self.tax_type}_tax",
            source_id=uuid.uuid4(),
            amount=config.default_amount
        )
        
        print(f"Created forecast for next year {next_year}")
    
    def get_linked_checks(self):
        """Get all checks linked to this tax declaration"""
        from .models import Check  # Import here to avoid circular imports
        return Check.objects.filter(
            is_tax_payment=True,
            tax_declaration_type='other_tax',
            tax_declaration_id=self.id
        ).select_related('checker', 'checker__bank_account')
    
    def calculate_payment_status(self):
        """Recalculate payment status based on linked checks"""
        checks = self.get_linked_checks()
        paid_checks = checks.filter(status='paid')
        
        # Calculate total paid amount from checks
        paid_amount = sum(check.amount for check in paid_checks)
        
        # Update fields
        self.paid_amount = paid_amount
        
        # Update status
        if paid_amount >= self.amount:
            self.status = 'paid'
        elif paid_amount > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'declared'
            
        self.save(update_fields=['paid_amount', 'status'])
        
        return self.status
        
    def get_payment_summary(self):
        """Get summary of payments for this tax declaration"""
        checks = self.get_linked_checks()
        
        total_checks = checks.count()
        paid_checks = checks.filter(status='paid').count()
        pending_checks = checks.exclude(status__in=['paid', 'cancelled', 'rejected']).count()
        
        total_amount = sum(check.amount for check in checks)
        paid_amount = sum(check.amount for check in checks.filter(status='paid'))
        pending_amount = sum(check.amount for check in checks.exclude(status__in=['paid', 'cancelled', 'rejected']))
            
        return {
            'total_checks': total_checks,
            'paid_checks': paid_checks,
            'pending_checks': pending_checks,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount
        }
        
    def add_payment(self, amount, payment_method, payment_date=None, check_reference=None):
        """Add a payment to the declaration"""
        print(f"\n=== Adding Payment to {self.tax_type.title()} Tax {self.year} ===")
        print(f"Amount: {amount}")
        print(f"Method: {payment_method}")
        print(f"Check reference: {check_reference}")
        
        if not payment_date:
            payment_date = timezone.now().date()
        
        # Update paid amount
        self.paid_amount += amount
        
        # Update payment details
        self.payment_method = payment_method
        self.payment_date = payment_date
        
        # Update status
        if self.paid_amount >= self.amount:
            self.status = 'paid'
        else:
            self.status = 'partially_paid'
        
        # Save with specific fields to avoid triggering forecast updates
        self.save(update_fields=['paid_amount', 'payment_method', 'payment_date', 'status'])
        self._update_forecast()
        
        # Process fines payment if the base amount is fully paid
        if self.paid_amount >= self.amount:
            available_for_fines = amount - (self.amount - (self.paid_amount - amount))
            if available_for_fines > 0:
                unpaid_fines = self.fines.filter(paid=False).order_by('fine_date')
                for fine in unpaid_fines:
                    if available_for_fines >= fine.amount:
                        fine.paid = True
                        fine.payment_date = payment_date
                        fine.save()
                        available_for_fines -= fine.amount
                        print(f"Marked fine {fine.id} as paid")
                    else:
                        break
        
        return True
    
    def mark_as_rejected(self, rejection_date=None, rejection_cause=None, rejection_notes=None):
        """Mark declaration as rejected with cause and notes"""
        print(f"\n=== Marking {self.tax_type.title()} Tax {self.year} as rejected ===")
        
        self.status = 'rejected'
        self.rejection_date = rejection_date or timezone.now().date()
        
        # Store rejection cause and notes
        if rejection_cause:
            self.rejection_cause = rejection_cause
        if rejection_notes:
            self.rejection_notes = rejection_notes
        
        # Update forecast
        if self.payment_method == 'direct_debit':
            self._update_forecast()
        
        self.save()
        
        print("Tax declaration marked as rejected")
    
    @property
    def remaining_amount(self):
        """Get remaining amount to pay"""
        # Start with base tax amount remaining
        base_remaining = self.amount - self.paid_amount
        
        # Add unpaid fines amount
        unpaid_fines_total = Decimal('0.00')
        for fine in self.fines.filter(paid=False):
            unpaid_fines_total += fine.amount
        
        return base_remaining + unpaid_fines_total

    @property
    def payment_status(self):
        """Calculate payment status based on paid amount vs total amount"""
        if self.paid_amount >= self.amount:
            return 'paid'
        elif self.paid_amount > 0:
            return 'partially_paid'
        else:
            return 'declared'
    
    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.year}"
    
    class Meta:
        ordering = ['-year', '-created_at']
        verbose_name = "Other Tax Declaration"
        verbose_name_plural = "Other Tax Declarations"


class TaxFine(BaseModel):
    """Fine entry for tax declarations"""
    
    declaration = models.ForeignKey(
        OtherTaxDeclaration, 
        on_delete=models.CASCADE,
        related_name='fines'
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Fine amount"
    )
    
    fine_date = models.DateField(
        default=timezone.now,
        help_text="Date when the fine was applied"
    )
    
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference number or code for the fine"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description or reason for the fine"
    )
    
    paid = models.BooleanField(
        default=False,
        help_text="Whether the fine has been paid"
    )
    
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the fine was paid"
    )
    
    def save(self, *args, **kwargs):
        """Override save to update declaration"""
        super().save(*args, **kwargs)
        
        self.declaration._update_forecast()
    
    def __str__(self):
        return f"Fine {self.amount} for {self.declaration}"
    
    class Meta:
        verbose_name = "Tax Fine"
        verbose_name_plural = "Tax Fines"