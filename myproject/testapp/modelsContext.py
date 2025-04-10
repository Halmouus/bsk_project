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
                            source_id=self.tax_declaration_id,
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

        # Handle tax payment processing when marked as paid
        if self.status == 'paid' and self.is_tax_payment and self.tax_declaration_id and self.tax_declaration_type:
            print(f"\n=== Processing Tax Payment ===")
            print(f"Tax declaration type: {self.tax_declaration_type}")
            print(f"Tax declaration ID: {self.tax_declaration_id}")
            print(f"Amount: {self.amount}")
            
            try:
                # Process different tax types
                if self.tax_declaration_type == 'other_tax':
                            tax = OtherTaxDeclaration.objects.get(id=self.tax_declaration_id)
                            
                            # Debug information 
                            print(f"Current tax state - amount: {tax.amount}, paid: {tax.paid_amount}")
                            print(f"Fines: {[{'id': str(fine.id), 'amount': fine.amount, 'paid': fine.paid} for fine in tax.fines.all()]}")
                            
                            # Add payment with specific check reference
                            tax.add_payment(
                                self.amount, 
                                'check', 
                                self.paid_at.date() if self.paid_at else None,
                                check_reference=f"{self.checker.bank_account.bank}-{self.position}"
                            )
                            if tax.paid_amount >= tax.amount:
                                tax.status = 'paid'
                            # If partially paid but not fully paid
                            elif tax.paid_amount > 0:
                                tax.status = 'partially_paid'
                            tax.save()
                            # Log updated tax state
                            print(f"Updated tax state - amount: {tax.amount}, paid: {tax.paid_amount}")
                            
                            # Update fines status if part of the payment was for fines
                            unpaid_fines = tax.fines.filter(paid=False)
                            if unpaid_fines.exists() and tax.paid_amount >= tax.amount:
                                # All base amount is paid, so remaining payment goes to fines
                                remaining = self.amount - (tax.amount - tax.paid_amount)
                                if remaining > 0:
                                    for fine in unpaid_fines:
                                        if remaining >= fine.amount:
                                            fine.paid = True
                                            fine.payment_date = self.paid_at.date() if self.paid_at else timezone.now().date()
                                            fine.save()
                                            remaining -= fine.amount
                                            print(f"Marked fine {fine.id} as paid")
                                        else:
                                            break
                            
                            print(f"Updated OtherTaxDeclaration payment: {tax.id}")
                elif self.tax_declaration_type == 'ir':
                    tax = IRDeclaration.objects.get(id=self.tax_declaration_id)
                    tax.payment_method = 'check'
                    tax.payment_date = self.paid_at.date() if self.paid_at else None
                    tax.status = 'paid'
                    tax.save()
                    print(f"Updated IRDeclaration payment: {tax.id}")
                elif self.tax_declaration_type == 'stamp_right':
                    tax = StampRightDeclaration.objects.get(id=self.tax_declaration_id)
                    tax.payment_method = 'check'
                    tax.payment_date = self.paid_at.date() if self.paid_at else None
                    tax.status = 'paid'
                    tax.save()
                    print(f"Updated StampRightDeclaration payment: {tax.id}")
                elif self.tax_declaration_type == 'vat':
                    from .models import VATDeclaration  # Import here to avoid circular imports
                    tax = VATDeclaration.objects.get(id=self.tax_declaration_id)
                    tax.payment_date = self.paid_at.date() if self.paid_at else None
                    tax.status = 'paid'
                    tax.save()
                    print(f"Updated VATDeclaration payment: {tax.id}")
            except Exception as e:
                print(f"Error updating tax payment status: {str(e)}")
                print(traceback.format_exc())
            
            # If check is paid and it's a tax payment, delete the associated forecast
            if (self.status == 'paid' or self.status == 'rejected') and self.is_tax_payment and self.tax_declaration_id and self.tax_declaration_type:
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
                
                source_type = None
                if self.tax_declaration_type == 'other_tax':
                    try:
                        tax = OtherTaxDeclaration.objects.get(id=self.tax_declaration_id)
                        source_type = forecast_type_mapping['other_tax'].get(
                            tax.tax_type,
                            forecast_type_mapping['other_tax']['default']
                        )
                    except Exception as e:
                        print(f"[Check Save] Error getting tax type: {str(e)}")
                        # Try all possible tax types
                        processed_count = 0
                        for tax_type in ['communal_tax', 'professional_tax', 'other_tax']:
                            count = ForecastStatement.objects.filter(
                                source_type=tax_type,
                                source_id=self.tax_declaration_id,
                                is_processed=False
                            ).update(is_processed=True)
                            processed_count += count
                            if count > 0:
                                print(f"[Check Save] Marked {count} {tax_type} forecasts as processed")
                        
                        if processed_count > 0:
                            print(f"[Check Save] Total forecasts marked as processed: {processed_count}")
                        return  # Return here to avoid double-processing
                else:
                    source_type = forecast_type_mapping.get(self.tax_declaration_type)
                    
                if source_type:
                    try:
                        # Mark all forecasts for this tax declaration as processed
                        processed_count = ForecastStatement.objects.filter(
                            source_type=source_type,
                            source_id=self.tax_declaration_id,
                            is_processed=False
                        ).update(is_processed=True)
                        print(f"[Check Save] Marked {processed_count} {source_type} forecasts as processed for tax declaration {self.tax_declaration_id}")
                    except Exception as e:
                        print(f"[Check Save] Error marking forecasts as processed for tax: {str(e)}")

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
                    # Don't let forecast errors prevent check creation
                    pass
            
        if self.payment_due and self.is_tax_payment and self.tax_declaration_id and self.tax_declaration_type and self.status != 'cancelled':
            print(f"\n[Check Save] Tax payment forecast handling START")
            print(f"[Check Save] Check ID: {self.pk}")
            print(f"[Check Save] Status: {self.status}")
            print(f"[Check Save] Payment due: {self.payment_due}")
            print(f"[Check Save] Is tax payment: {self.is_tax_payment}")
            print(f"[Check Save] Tax declaration ID: {self.tax_declaration_id}")
            print(f"[Check Save] Tax declaration type: {self.tax_declaration_type}")
            
            # Delete ALL forecasts related to this tax declaration ID regardless of source_type
            try:
                all_deleted = ForecastStatement.objects.filter(
                    source_id=self.tax_declaration_id,
                    is_processed=False
                ).delete()[0]
                print(f"[Check Save] Deleted {all_deleted} forecasts for tax declaration {self.tax_declaration_id}")
            except Exception as e:
                print(f"[Check Save] Error deleting forecasts: {str(e)}")
            
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
            
            source_type = None
            display_name = "Tax"
            
            if self.tax_declaration_type == 'other_tax':
                try:
                    tax = OtherTaxDeclaration.objects.get(id=self.tax_declaration_id)
                    tax_type = tax.tax_type
                    print(f"[Check Save] Found tax record, type: {tax_type}")
                    
                    source_type = forecast_type_mapping['other_tax'].get(
                        tax_type,
                        forecast_type_mapping['other_tax']['default']
                    )
                    print(f"[Check Save] Mapped to source_type: {source_type}")
                    
                    display_name = f"{tax.get_tax_type_display()} Tax"
                except Exception as e:
                    print(f"[Check Save] Error getting tax type: {str(e)}")
                    # Don't create forecast if tax declaration doesn't exist
                    print(f"[Check Save] Skipping forecast creation since declaration doesn't exist")
                    return
            else:
                source_type = forecast_type_mapping.get(self.tax_declaration_type)
                if self.tax_declaration_type == 'vat':
                    display_name = "VAT"
                elif self.tax_declaration_type == 'ir':
                    display_name = "IR"
                elif self.tax_declaration_type == 'stamp_right':
                    display_name = "Stamp Rights"
            
            if source_type:
                # Prepare forecast date
                forecast_date = self.payment_due
                print(f"[Check Save] Will create forecast with date: {forecast_date}")
                
                try:
                    print(f"[Check Save] Creating {source_type} forecast")
                    
                    # Create tax-specific forecast
                    forecast = ForecastStatement.objects.create(
                        bank_account=self.checker.bank_account,
                        date=forecast_date,
                        label=f"{display_name} Payment",
                        debit=self.amount,
                        amount=self.amount,
                        reference=f"{display_name} Payment #{self.position}",
                        source_type=source_type,  # Use tax-specific source type
                        source_id=self.tax_declaration_id  # Point to the tax declaration
                    )
                    
                    print(f"[Check Save] Tax forecast created successfully:")
                    print(f"  - ID: {forecast.id}")
                    print(f"  - Source type: {forecast.source_type}")
                    print(f"  - Source ID: {forecast.source_id}")
                    print(f"  - Date: {forecast.date}")
                    print(f"  - Amount: {forecast.amount}")
                except Exception as e:
                    print(f"[Check Save] Error creating tax forecast: {str(e)}")
                    print(traceback.format_exc())
            
            print(f"[Check Save] Tax payment forecast handling END\n")
        
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
    
    def save(self, *args, **kwargs):
        print("\n=== Saving OtherTaxDeclaration ===")
        print(f"Type: {self.tax_type}")
        print(f"Year: {self.year}")
        print(f"Amount: {self.amount}")
        
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
        
        # Create forecast   
        if self.status != 'paid':
            self._update_forecast()
        
        if kwargs.get('update_fields') != ['paid_amount', 'status']:
            self.calculate_payment_status()
        
        super().save(*args, **kwargs)
    
    def _update_forecast(self):
        """Update or create forecast for this declaration"""
        print("\n=== Updating Tax Forecast ===")
        
        # Delete old forecast if exists
        if self.forecast:
            print(f"Deleting old forecast: {self.forecast.id}")
            self.forecast.delete()
            self.forecast = None
        
        # Don't create forecast for paid declarations
        if self.status == 'paid':
            print(f"Not creating forecast for paid declaration")
            return
        
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
        
        # Delete ALL existing forecasts for this tax type, including current and ALL future years
        existing_forecasts = ForecastStatement.objects.filter(
            source_type=f"{self.tax_type}_tax",
            date__gte=datetime.date(self.year, 1, 1),  # From January 1st of current year
            is_processed=False
        )
        
        if existing_forecasts.exists():
            print(f"Deleting {existing_forecasts.count()} existing forecasts for this tax type")
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
        
        # Generate next year's forecast
        self._generate_future_forecast()
    
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
        
        # Check for ANY existing forecasts for next year, using more comprehensive checks
        existing_forecast = ForecastStatement.objects.filter(
            source_type=f"{self.tax_type}_tax",
            date__year=next_year,
            is_processed=False
        ).first()
        
        if existing_forecast:
            print(f"Forecast already exists for {next_year}, deleting and recreating")
            existing_forecast.delete()
        
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
        
    def add_payment(self, amount, payment_method, payment_date=None):
        """Add a payment to the declaration"""
        print(f"\n=== Adding Payment to {self.tax_type.title()} Tax {self.year} ===")
        print(f"Amount: {amount}")
        print(f"Method: {payment_method}")
        
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
        
        self.save()
        
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
        return f"{self.get_tax_type_display()} {self.year}"
    
    class Meta:
        ordering = ['-year']
        unique_together = ['tax_type', 'year']
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
        
        # Update declaration forecast if fine is not paid and using direct debit
        if not self.paid and self.declaration.payment_method == 'direct_debit':
            self.declaration._update_forecast()
    
    def __str__(self):
        return f"Fine {self.amount} for {self.declaration}"
    
    class Meta:
        verbose_name = "Tax Fine"
        verbose_name_plural = "Tax Fines"