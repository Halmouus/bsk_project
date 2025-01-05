from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, MinLengthValidator, MaxLengthValidator
from .base import BaseModel
from datetime import timedelta, datetime
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
from django.db.models import Sum

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

class item(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()    
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

class Supplier(BaseModel):

    numeric_validator = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')
    alphanumeric_validator = RegexValidator(r'^[a-zA-Z0-9 ]*$', 'Only alphanumeric characters are allowed.')

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
        help_text="Number of days to delay check payment forecasts after due date"
    )
    delay_lcn = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of days to delay LCN payment forecasts after due date"
    )

    def clean(self):
        super().clean()
        # Ensure IF code is numeric
        if not self.if_code.isdigit():
            raise ValidationError("IF code must be numeric.")
        # Ensure ICE code has exactly 15 characters
        if len(self.ice_code) != 15:
            raise ValidationError("ICE code must contain exactly 15 characters.")
    
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
    (0.00, '0%'), (7.00, '7%'), (10.00, '10%'), (11.00, '11%'), (14.00, '14%'), (16.00, '16%'), (20.00, '20%')
])
    expense_code = models.CharField(max_length=25, validators=[RegexValidator(r'^[0-9]{5,}$', 'Expense code must be numeric and at least 5 characters long.')])
    is_energy = models.BooleanField(default=False)
    fiscal_label = models.CharField(max_length=255, blank=False)

    class Meta:
        constraints = [
        ]
    def __str__(self):
        return self.name

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

    original_invoice = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='credit_notes'
    )

    def save(self, *args, **kwargs):
        if self.type == 'invoice':  # Only calculate payment_due_date for regular invoices
            if not self.payment_due_date:
                self.payment_due_date = self.date + timedelta(days=self.supplier.delay_convention)
        else:  # For credit notes
            self.payment_due_date = None

        super().save(*args, **kwargs)

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
        return self.raw_amount + self.total_tax_amount
    
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
    

    def clean(self):
        """Custom clean method to validate credit notes"""
        super().clean()
        if self.type == 'credit_note':
            if not self.original_invoice:
                raise ValidationError("Credit note must reference an original invoice")
            if self.original_invoice.type != 'invoice':
                raise ValidationError("Cannot create credit note for another credit note")
            if self.supplier != self.original_invoice.supplier:
                raise ValidationError("Credit note must have same supplier as original invoice")

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
        tax_groups = {}
        
        for invoice_product in self.products.all():
            # Group products by expense code
            key = invoice_product.product.expense_code
            if key not in expense_groups:
                expense_groups[key] = {
                    'products': {},  # Changed to dict to track values
                    'amount': 0,
                    'is_energy': invoice_product.product.is_energy
                }
            # Track product value
            product_value = (
                invoice_product.quantity * 
                invoice_product.unit_price * 
                (1 - invoice_product.reduction_rate / 100) * 
                sign
            )
            expense_groups[key]['products'][invoice_product.product.name] = product_value
            expense_groups[key]['amount'] += product_value

            # Group taxes by rate (unchanged)
            tax_key = invoice_product.vat_rate
            if tax_key not in tax_groups:
                tax_groups[tax_key] = 0
            tax_groups[tax_key] += (product_value * invoice_product.vat_rate / 100)

        # Add expense entries with top 3 products by value
        prefix = "CN -" if self.type == 'credit_note' else ""
        for expense_code, data in expense_groups.items():
            # Sort products by value and get unique names
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

        # Rest of the method remains unchanged
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

        print(f"Looking for allocations with invoice_id: {self.id}")
        allocations = CheckAllocation.objects.filter(invoice_id=self.id)
        print(f"Raw allocations found: {allocations.count()}")
        print("Allocation details:")
        for alloc in allocations:
            print(f"Allocation ID: {alloc.id}")
            print(f"Check ID: {alloc.payment.id if hasattr(alloc, 'payment') else 'No payment'}")
            print(f"Check status: {alloc.payment.status if hasattr(alloc, 'payment') else 'No status'}")

        # Get allocations for this invoice
        valid_allocations = CheckAllocation.objects.filter(
            invoice_id=self.id,
            payment__status__in=['pending', 'delivered', 'paid', 'draft']
        ).select_related('payment')
        print(f"Allocations found: {valid_allocations.count()}")
        print(f"Allocations after status filter: {valid_allocations.count()}")

        # Add allocated amounts to totals
        alloc_pending = sum(a.amount for a in valid_allocations.filter(payment__status='pending'))
        alloc_delivered = sum(a.amount for a in valid_allocations.filter(payment__status='delivered'))
        alloc_paid = sum(a.amount for a in valid_allocations.filter(payment__status='paid'))
        total_allocated = sum(a.amount for a in valid_allocations)

        print(f"Allocated payments - Pending: {alloc_pending}, Delivered: {alloc_delivered}, Paid: {alloc_paid}")

        # Update totals with allocations
        pending_amount += alloc_pending
        delivered_amount += alloc_delivered
        paid_amount += alloc_paid
        total_issued += total_allocated

        net_amount = self.net_amount
        amount_to_issue = net_amount - total_issued
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
            'checks': checks
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
        """Update payment status based on PAID payments only"""
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
        
        # Determine status
        if total_payments >= self.net_amount:
            self.payment_status = 'paid'
        elif total_payments > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'not_paid'
            
        self.save()

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
            MinLengthValidator(10, 'Account number must be at least 10 characters'),
            RegexValidator(r'^\d+$', 'Only numeric characters allowed')
        ]
    )
    accounting_number = models.CharField(
        max_length=10,
        validators=[
            MinLengthValidator(5, 'Accounting number must be at least 5 characters'),
            RegexValidator(r'^\d+$', 'Only numeric characters allowed')
        ]
    )
    journal_number = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(r'^\d{2}$', 'Must be exactly 2 digits')
        ]
    )
    city = models.CharField(max_length=100)
    account_type = models.CharField(max_length=15, choices=ACCOUNT_TYPE)
    is_active = models.BooleanField(default=True)

    is_current = models.BooleanField(
        default=False,
        help_text="Determines if accounting operations are recorded on this account"
    )
    bank_overdraft = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum allowed overdraft amount"
    )
    overdraft_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Fee applied for overdraft usage"
    )
    has_check_discount_line = models.BooleanField(
        default=False,
        help_text="Indicates if this account can discount checks"
    )
    check_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum amount available for check discounting"
    )
    has_lcn_discount_line = models.BooleanField(
        default=False,
        help_text="Indicates if this account can discount LCNs"
    )
    lcn_discount_line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum amount available for LCN discounting"
    )
    stamp_fee_per_receipt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Stamp fee charged per presented receipt"
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

    def clean(self):
        super().clean()
        if self.has_check_discount_line and not self.check_discount_line_amount:
            raise ValidationError({
                'check_discount_line_amount': 'Amount required when check discount line is enabled'
            })
        if self.has_lcn_discount_line and not self.lcn_discount_line_amount:
            raise ValidationError({
                'lcn_discount_line_amount': 'Amount required when LCN discount line is enabled'
            })

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
        validators=[RegexValidator(r'^[A-Z]{1,3}$', 'Must be 1 to 3 uppercase letters.')]
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
                raise ValidationError("Cannot create checker for inactive bank account")
            if self.bank_account.account_type != 'national':
                raise ValidationError("Can only create checkers for national accounts")
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
                print(f"Setting amount_due from cause: {self.cause.total_amount}")
                self.amount_due = self.cause.total_amount
        
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

        # If this is a supplier payment (we'll update it later for non suppliers)
        if self.payment_due:
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
                print(f"Using delay of {delay} days based on checker type {self.checker.type}")
                
                current_date = forecast_date
                while delay > 0 or current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    if current_date.weekday() < 5:  # Only count business days
                        delay -= 1
                        
                print(f"Creating forecast for date: {current_date}")
                
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
            raise ValidationError("Invoice is required for direct invoice payments")
            
        if self.is_supplier_payment and self.cause:
            raise ValidationError("Supplier payments cannot specify a direct cause")
            
        if self.cause and self.cause.supplier != self.beneficiary:
            raise ValidationError("Invoice supplier must match check beneficiary")
            
        # Validate amount for invoice payments
        if not self.is_supplier_payment and self.cause:
            if self.amount > self.cause.amount_available_for_payment:
                raise ValidationError("Amount exceeds invoice's available amount")
            
        if self.paid_at and not self.delivered_at:
            raise ValidationError("Check cannot be marked as paid before delivery")

        # Validate supplier payment allocation before printing
        if self.status == 'printed' and self.is_supplier_payment:
            if self.get_available_amount() > 0:
                raise ValidationError("Supplier payment must be fully allocated before printing")
            
        # Only allow edits to specific fields after draft status
        if self.pk and self.status not in ['draft', 'pending']:
            original = Check.objects.get(pk=self.pk)
            changed_fields = []
            for field in ['beneficiary', 'cause', 'amount', 'position', 'checker']:
                if getattr(self, field) != getattr(original, field):
                    changed_fields.append(field)
            
            if changed_fields:
                raise ValidationError(f"Cannot modify {', '.join(changed_fields)} after check is printed")

        
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
            raise ValidationError("Only delivered or rejected checks can be received")
        
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
                "Cannot replace: Check must be rejected and received, with no existing replacement"
            )

        if not checker.is_active or checker.status == 'completed':
            raise ValidationError("Selected checker is not available for new checks")

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
            raise ValidationError("Can only allocate supplier payments")
            
        # Ensure invoice matches check's beneficiary
        if self.invoice.supplier != self.payment.beneficiary:  
            raise ValidationError("Invoice must belong to check's beneficiary")
            
        # Ensure we don't exceed available amount
        available = self.payment.get_available_amount()  
        if self.amount > available:
            raise ValidationError(
                f"Amount {self.amount} exceeds available amount {available}"
            )
            
        # Ensure we don't exceed invoice's available amount
        if self.amount > self.invoice.amount_available_for_payment:
            raise ValidationError("Amount exceeds invoice's available amount")


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
                message='Name can only contain letters and spaces'
            )
        ]
    )
    
    client_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            MinLengthValidator(5, 'Client code must be at least 5 digits'),
            MaxLengthValidator(10, 'Client code cannot exceed 10 digits'),
            RegexValidator(
                regex=r'^\d+$',
                message='Client code must contain only digits'
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
                        'client_code': 'Client code must be between 5 and 10 digits'
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
                                'description': f'{type_name} {number} {receipt.entity.name} presented for '
                                            f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                            f'on {pres.presentation.date.strftime("%Y-%m-%d")}',
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
                'description': 'Previous Balance',
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
                            'description': f'{type_name} {number} {receipt.entity.name} '
                                        f'({("re" if is_representation else "")}presented for '
                                        f'{"collection" if pres.presentation.presentation_type == "COLLECTION" else "discount"} '
                                        f'on {pres.presentation.date.strftime("%Y-%m-%d")})',
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
                            'description': f'Reversal of {type_name} {receipt.get_receipt_number()} - '
                                        f'{history.notes if history.notes else "Unpaid"}',
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
                    'description': f'{type_name} {receipt.reference_number if hasattr(receipt, "reference_number") else receipt.transfer_reference} {receipt.entity.name}',
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

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
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
                        
                        # Use presentation_date for presentations, unpaid_date for unpaid status
                        business_date = None
                        if self.status in ['PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT']:
                            business_date = getattr(self, '_presentation_date', None)
                        elif self.status == 'UNPAID':
                            business_date = self.unpaid_date
                        elif self.status in ['COMPENSATED', 'PARTIALLY_COMPENSATED']:
                            business_date = getattr(self, '_force_status_date', None)
                        
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
        if isinstance(compensating_receipt, (CashReceipt, TransferReceipt)):
            business_date = compensating_receipt.operation_date
        else:
            # Create a timezone-aware datetime using your existing datetime module setup
            created_date = compensating_receipt.created_at.date()
            business_date = timezone.make_aware(
                datetime.datetime(created_date.year, created_date.month, created_date.day)
            )
        
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
    # Optional: Add document field
    document = models.FileField(upload_to='presentations/', null=True, blank=True)

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

        # Add supplier payments entries
        print("\n=== Getting Supplier Payments ===")
        supplier_payments = Check.objects.filter(
            checker__bank_account=bank_account,
            status='paid'
        ).select_related('checker', 'beneficiary')
        
        print(f"Found {supplier_payments.count()} supplier payments")
        print("Query:", supplier_payments.query)  # Print the actual SQL query
        
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
        
        print("\nFinal entries count:", len(entries))
            
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
        entries = cls.get_statement(bank_account, end_date=date, include_forecasts=False)
        if entries:
            return entries[0]['balance']  # First entry has final balance since they're sorted in reverse
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
                        
                        # Add debit and credit pair for reversal
                        entries.extend([
                            {
                                'date': pres.date,
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
                                'date': pres.date,
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
                        
                        # Add debit and credit pair for other operations
                        entries.extend([
                            {
                                'date': pres.date,
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
                                'date': pres.date,
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

        # Sort entries keeping pairs together
        entries.sort(key=lambda x: (x['date'], x['pair_index']), reverse=True)
        
        return entries

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
        if not self.can_generate_invoice(for_date):
            raise ValidationError("Cannot generate invoice for this date")

        period_start = self.get_period_start_date(for_date)
        period_end = self.get_period_end_date(period_start)

        # Create invoice
        invoice = Invoice.objects.create(
            ref=f"{self.reference}-{period_start.strftime('%Y%m')}",
            date=for_date,
            supplier=self.supplier,
            type='invoice'
        )

        # Add products from contract
        for contract_product in self.products.all():
            InvoiceProduct.objects.create(
                invoice=invoice,
                product=contract_product.product,
                quantity=contract_product.quantity,
                unit_price=contract_product.unit_price,
                reduction_rate=contract_product.reduction_rate,
                vat_rate=contract_product.product.vat_rate
            )

        # Create contract invoice record
        ContractInvoice.objects.create(
            contract=self,
            invoice=invoice,
            period_start=period_start,
            period_end=period_end
        )

        return invoice

    def generate_missing_invoices(self, up_to_date=None):
        """Generate all missing invoices up to the given date"""
        print("\n=== Starting invoice generation ===")
        if not up_to_date:
            up_to_date = timezone.now().date()
        print(f"Generating invoices up to: {up_to_date}")

        current_date = self.start_date
        generated_invoices = []
        print(f"Starting from date: {current_date}")

        while current_date <= up_to_date:
            print(f"Checking date: {current_date}")
            if self.can_generate_invoice(current_date):
                print(f"Generating invoice for: {current_date}")
                try:
                    invoice = self.generate_invoice(current_date)
                    generated_invoices.append(invoice)
                    print(f"Generated invoice: {invoice.ref}")
                except Exception as e:
                    print(f"Error generating invoice: {str(e)}")
                    raise
            
            print("Getting next generation date...")
            current_date = self.get_next_generation_date(current_date)
            print(f"Next date: {current_date}")

        print(f"Generation complete. Created {len(generated_invoices)} invoices")
        return generated_invoices

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

class ContractProduct(BaseModel):
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
    invoice = models.OneToOneField('Invoice', on_delete=models.PROTECT)
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        unique_together = [
            ['contract', 'period_start', 'period_end']
        ]