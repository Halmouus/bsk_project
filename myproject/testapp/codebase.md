# base.py

```py
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

```

# forms.py

```py
from django import forms
from django.core.exceptions import ValidationError
from .models import (Invoice, InvoiceProduct, Product, CheckReceipt, LCN, CashReceipt, TransferReceipt, 
    Presentation, PresentationReceipt, MOROCCAN_BANKS)
from django.forms.models import inlineformset_factory
from decimal import Decimal

class CheckReceiptForm(forms.ModelForm):
    class Meta:
        model = CheckReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month',
            'due_date', 'check_number', 'issuing_bank', 'branch',
            'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'issuing_bank': forms.Select(choices=MOROCCAN_BANKS)
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit compensates to rejected, uncompensated checks
        self.fields['compensates'].queryset = CheckReceipt.objects.filter(
            status=CheckReceipt.STATUS_REJECTED
        ).exclude(
            status=CheckReceipt.STATUS_COMPENSATED
        )

class LCNForm(forms.ModelForm):
    class Meta:
        model = LCN
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month',
            'due_date', 'lcn_number', 'issuing_bank',
            'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'issuing_bank': forms.Select(choices=MOROCCAN_BANKS)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit compensates to rejected, uncompensated LCNs
        self.fields['compensates'].queryset = LCN.objects.filter(
            status=LCN.STATUS_REJECTED
        ).exclude(
            status=LCN.STATUS_COMPENSATED
        )

class CashReceiptForm(forms.ModelForm):
    class Meta:
        model = CashReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'reference_number', 'credited_account', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TransferReceiptForm(forms.ModelForm):
    class Meta:
        model = TransferReceipt
        fields = [
            'client', 'entity', 'operation_date', 'amount',
            'client_year', 'client_month', 'bank_account',
            'transfer_reference', 'credited_account', 
            'transfer_date', 'notes'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'transfer_date': forms.DateInput(attrs={'type': 'date'}),
        }
```


# models.py

```py
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, MinLengthValidator, MaxLengthValidator
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
            
            # Previous Sales (by actual date)
            prev_sales = self.clientsale_set.filter(date__lt=current_date)
            previous_balance = sum(sale.amount for sale in prev_sales)

            # Previous Checks and LCNs - based on presentations
            for receipt_class in [CheckReceipt, LCN]:
                prev_receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('client', 'entity')

                for receipt in prev_receipts:
                    # Get all presentations for this receipt
                    if isinstance(receipt, CheckReceipt):
                        presentations = receipt.check_presentations.select_related('presentation').all()
                    else:
                        presentations = receipt.lcn_presentations.select_related('presentation').all()
                    
                    # Process each presentation's effect on balance
                    for pres in presentations:
                        if pres.presentation.date < current_date:
                            # Credit for presentation
                            previous_balance -= receipt.amount
                            
                            # Debit if unpaid after this presentation
                            if receipt.status == 'UNPAID' and receipt.updated_at < current_date:
                                previous_balance += receipt.amount

            # Previous Cash/Transfers (these can't be unpaid)
            for receipt_class in [CashReceipt, TransferReceipt]:
                prev_receipts = receipt_class.objects.filter(
                    client=self
                ).filter(
                    Q(client_year__lt=year) | 
                    Q(client_year=year, client_month__lt=month)
                ).select_related('entity')
                previous_balance -= sum(receipt.amount for receipt in prev_receipts)

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
                            'date': history.timestamp.date(),
                            'type': f'{type_name}_REVERSAL',
                            'description': f'Reversal of {type_name} {receipt.get_receipt_number()} - '
                                        f'{history.notes if history.notes else "Unpaid"}',
                            'debit': history.new_value.get("amount", receipt.amount),  # Include the unpaid amount
                            'credit': None,
                            'actual_date': history.timestamp.date()
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
    phone_number = models.CharField(max_length=20, blank=True, null=True)
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

    RECEIPT_STATUS = [
        (STATUS_PORTFOLIO, 'In Portfolio'),
        (STATUS_PRESENTED_COLLECTION, 'Presented for Collection'),
        (STATUS_PRESENTED_DISCOUNT, 'Presented for Discount'),
        (STATUS_DISCOUNTED, 'Discounted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPENSATED, 'Compensated'),
        (STATUS_UNPAID, 'Unpaid') 
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
        max_length=20, 
        choices=RECEIPT_STATUS,
        default=STATUS_PORTFOLIO
    )

    compensates = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='compensated_by'
    )

    rejection_cause = models.CharField(
        max_length=50,
        choices=REJECTION_CAUSES,
        null=True,
        blank=True
    )    

    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )

    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )
    
    compensation_date = models.DateTimeField(
        null=True,
        blank=True
    )    

    class Meta:
        abstract = True

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
        return not hasattr(self, 'presentation') or self.presentation is None

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
        if not self.compensating_receipt:
            return None
            
        if isinstance(self.compensating_receipt, CashReceipt):
            return f"Compensated by cash payment (Ref: {self.compensating_receipt.reference_number or 'N/A'})"
        elif isinstance(self.compensating_receipt, TransferReceipt):
            return f"Compensated by bank transfer (Ref: {self.compensating_receipt.transfer_reference})"
        else:
            return (f"Compensated by {self.compensating_receipt.__class__.__name__.replace('Receipt', '')} "
                f"#{self.compensating_receipt.get_receipt_number()} "
                f"({self.compensating_receipt.entity.name})")

    def mark_as_unpaid(self, cause):
        """Mark receipt as unpaid with a cause"""
        if self.status not in ['REJECTED', 'PRESENTED_COLLECTION', 'PRESENTED_DISCOUNT', 'DISCOUNTED']:
            raise ValidationError("Only rejected or presented receipts can be marked as unpaid")
        
        self.status = self.STATUS_UNPAID
        self.rejection_cause = cause
        self.save()

    def compensate_with(self, compensating_receipt):
        """Set up compensation relationship"""
        if self.status != self.STATUS_UNPAID:
            raise ValidationError("Only unpaid receipts can be compensated")
            
        if compensating_receipt.amount < self.amount:
            raise ValidationError("Compensating receipt amount must be greater than or equal to unpaid amount")

        self.compensating_receipt = compensating_receipt
        
        # If cash/transfer, mark as compensated immediately
        if isinstance(compensating_receipt, (CashReceipt, TransferReceipt)):
            self.status = self.STATUS_COMPENSATED
            self.compensation_date = timezone.now()
            self.record_history(
                action='status_changed',
                old_value={'status': self.STATUS_UNPAID},
                new_value={'status': self.STATUS_COMPENSATED},
                notes=f'Compensated by {compensating_receipt.__class__.__name__} {compensating_receipt.id}'
            )
        else:
            # For checks/LCNs, just record that a compensating receipt was assigned
            self.record_history(
                action='compensation_assigned',
                new_value={
                    'compensating_type': compensating_receipt.__class__.__name__,
                    'compensating_id': str(compensating_receipt.id)
                },
                notes=f'Assigned {compensating_receipt.__class__.__name__} #{compensating_receipt.get_receipt_number()} as compensating receipt'
            )
            
        self.save()

    def handle_compensation_payment(self):
        """Called when a compensating negotiable receipt is paid"""
        if self.status == self.STATUS_UNPAID and self.compensating_receipt:
            old_status = self.status
            self.status = self.STATUS_COMPENSATED
            self.compensation_date = timezone.now()
            
            self.record_history(
                action='status_changed',
                old_value={'status': old_status},
                new_value={'status': self.STATUS_COMPENSATED},
                notes=f'Status changed to compensated as compensating receipt was paid'
            )
            self.save()

    def update_compensated_receipts(self):
            """
            When this receipt is paid, update any receipts it compensates
            """
            # Find all receipts that this receipt compensates
            compensated_checks = CheckReceipt.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id,
                status=self.STATUS_UNPAID
            )
            
            compensated_lcns = LCN.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id,
                status=self.STATUS_UNPAID
            )

            # Update the status of all compensated receipts
            current_time = timezone.now()
            
            for receipt in list(compensated_checks) + list(compensated_lcns):
                receipt.status = self.STATUS_COMPENSATED
                receipt.compensation_date = current_time
                receipt.save()

    def record_history(self, action, old_value=None, new_value=None, notes=None, user=None):
        """
        Record a history event for the negotiable receipt
        """
        content_type = ContentType.objects.get_for_model(self)

        
        
        ReceiptHistory.objects.create(
            content_type=content_type,
            object_id=self.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            user=user
        )

    def delete(self, *args, **kwargs):
        # If this receipt is compensating any unpaid receipts and is still in PORTFOLIO
        if self.status == self.STATUS_PORTFOLIO:
            # Find any receipts this one was supposed to compensate
            compensated_checks = CheckReceipt.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id
            )
            compensated_lcns = LCN.objects.filter(
                compensating_content_type=ContentType.objects.get_for_model(self),
                compensating_object_id=self.id
            )
            
            # Clean up the compensated receipts
            for receipt in list(compensated_checks) + list(compensated_lcns):
                receipt.record_history(
                    action='compensation_cancelled',
                    notes=f'Compensating receipt {self.__class__.__name__} #{self.get_receipt_number()} was deleted'
                )
                receipt.compensating_receipt = None
                receipt.save()

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            self.record_history(
                action='created',
                notes=f'Receipt created with status {self.get_status_display()}'
            )
        else:
            try:
                old_instance = type(self).objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    # Check if this is a discount update
                    if self.status == 'DISCOUNTED':
                        # Get the presentation info
                        if hasattr(self, 'check_presentations'):
                            presentation = self.check_presentations.last().presentation
                        else:
                            presentation = self.lcn_presentations.last().presentation
                            
                        self.record_history(
                            action='status_changed',
                            old_value={'status': old_instance.status},
                            new_value={
                                'status': self.status,
                                'presentation_id': str(presentation.id),
                                'bank_account': presentation.bank_account.get_bank_display(),
                                'date': presentation.date.strftime('%Y-%m-%d')
                            },
                            notes=f'Discounted at {presentation.bank_account.get_bank_display()}'
                        )
                    else:
                        self.record_history(
                            action='status_changed',
                            old_value={'status': old_instance.status},
                            new_value={'status': self.status},
                            notes=f'Status changed from {old_instance.status} to {self.status}'
                        )
            except type(self).DoesNotExist:
                pass
                
            super().save(*args, **kwargs)

class CheckReceipt(NegotiableReceipt):
    """Check-specific implementation."""
    check_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Check {self.check_number} - {self.amount}"

    class Meta:
        verbose_name = "Check"
        verbose_name_plural = "Checks"

class LCN(NegotiableReceipt):
    """LCN-specific implementation."""
    lcn_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"LCN {self.lcn_number} - {self.amount}"

    def clean(self):
        super().clean()
        if not self.due_date:
            raise ValidationError("Due date is required for LCN")

    class Meta:
        verbose_name = "LCN"
        verbose_name_plural = "LCNs"

class CashReceipt(Receipt):
    """Cash receipt implementation."""
    reference_number = models.CharField(max_length=50, blank=True)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='cash_receipts'
    )

    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )
    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )

    def get_compensated_receipt(self):
        """Returns the receipt that this cash/transfer is compensating"""
        # Check for checks first
        compensated_check = CheckReceipt.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        if compensated_check:
            return compensated_check
            
        # Check for LCNs
        compensated_lcn = LCN.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        return compensated_lcn
    
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

class TransferReceipt(Receipt):
    """Bank transfer implementation."""
    transfer_reference = models.CharField(max_length=100)
    credited_account = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        related_name='transfer_receipts'
    )
    transfer_date = models.DateField(default=timezone.now)
    compensating_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_compensating'
    )
    compensating_object_id = models.UUIDField(null=True, blank=True)
    compensating_receipt = GenericForeignKey(
        'compensating_content_type', 
        'compensating_object_id'
    )

    def get_compensated_receipt(self):
        """Returns the receipt that this cash/transfer is compensating"""
        # Check for checks first
        compensated_check = CheckReceipt.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        if compensated_check:
            return compensated_check
            
        # Check for LCNs
        compensated_lcn = LCN.objects.filter(
            compensating_content_type=ContentType.objects.get_for_model(self.__class__),
            compensating_object_id=self.id
        ).first()
        
        return compensated_lcn
    
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
        max_length=20,
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
        max_length=20,
        choices=NegotiableReceipt.RECEIPT_STATUS,
        null=True,
        blank=True,
        help_text="Stores the final status decision made in this presentation"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    immutable = models.BooleanField(default=False)

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
        self.full_clean()
        super().save(*args, **kwargs)
        self.presentation.update_total()

        # Update receipt status based on presentation type
        receipt = self.checkreceipt or self.lcn
        if receipt:  # Add check to ensure receipt exists
            if self.presentation.presentation_type == Presentation.TYPE_COLLECTION:
                receipt.status = 'PRESENTED_COLLECTION'
            else:
                receipt.status = 'PRESENTED_DISCOUNT'
            receipt.save()

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
        ('compensated', 'Compensated'),
        ('unpaid', 'Marked as Unpaid'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected by Bank')
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
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
        ordering = ['-timestamp']
        verbose_name = "Receipt History"
        verbose_name_plural = "Receipt Histories"

    def __str__(self):
        return f"{self.receipt} - {self.action} at {self.timestamp}"

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
```

# signals.py

```py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Check

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Create a Profile for new users
        Profile.objects.create(user=instance)
    else:
        # Save the Profile if it already exists
        if hasattr(instance, 'profile'):
            instance.profile.save()


@receiver(post_save, sender=Check)
def update_invoice_payment_status(sender, instance, **kwargs):
    if instance.cause:
        instance.cause.update_payment_status()


@receiver(post_save, sender=Check)
def update_checker_status(sender, instance, **kwargs):
    if instance.checker:
        instance.checker.update_status()


```

# templates/bank/bank_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid px-4"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Bank Accounts</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#bankAccountModal"> <i class="fas fa-plus"></i> New Bank Account </button> </div> <!-- Accounts Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Bank</th> <th>Account Number</th> <th>Type</th> <th>City</th> <th>Status</th> <th>Current Account</th> <th>Check Discount</th> <th>LCN Discount</th> <th>Actions</th> </tr> </thead> <tbody> <tbody> {% for account in accounts %} <tr> <td>{{ account.get_bank_display }}</td> <td>{{ account.account_number }}</td> <td>{{ account.get_account_type_display }}</td> <td>{{ account.city }}</td> <td> <span class="badge {% if account.is_active %}badge-success{% else %}badge-danger{% endif %}"> {{ account.is_active|yesno:"Active,Inactive" }} </span> </td> <td> <span class="badge {% if account.is_current %}badge-primary{% else %}badge-secondary{% endif %}"> {{ account.is_current|yesno:"Yes,No" }} </span> </td> <td> {% if account.has_check_discount_line %} <span class="badge badge-info"> {{ account.check_discount_line_amount|default:0|floatformat:2 }} MAD </span> {% else %} <span class="badge badge-secondary">No</span> {% endif %} </td> <td> {% if account.has_lcn_discount_line %} <span class="badge badge-info"> {{ account.lcn_discount_line_amount|default:0|floatformat:2 }} MAD </span> {% else %} <span class="badge badge-secondary">No</span> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-primary" onclick="editBankAccount('{{ account.id }}')"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger" onclick="deleteBankAccount('{{ account.id }}')"> <i class="fas fa-trash"></i> </button> </div> </td> <td style="display:none"> Check line: {{ account.get_available_check_discount_line }} LCN line: {{ account.get_available_lcn_discount_line }} Raw check amount: {{ account.check_discount_line_amount }} Raw lcn amount: {{ account.lcn_discount_line_amount }} </td> </tr> {% empty %} <tr> <td colspan="9" class="text-center">No bank accounts found</td> </tr> {% endfor %} </tbody> </table> </div> </div> </div> </div> <!-- Bank Account Modal --> <div class="modal fade" id="bankAccountModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title" id="modalTitle">New Bank Account</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="bankAccountForm"> {% csrf_token %} <input type="hidden" id="accountId"> <!-- Basic Information --> <div class="card mb-3"> <div class="card-header"> Basic Information </div> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Bank</label> <select class="form-control" id="bank" required> {% for code, name in bank_choices %} <option value="{{ code }}">{{ name }}</option> {% endfor %} </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Account Number</label> <input type="text" class="form-control" id="accountNumber" required> </div> </div> </div> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label>Accounting Number</label> <input type="text" class="form-control" id="accountingNumber" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>Journal Number</label> <input type="text" class="form-control" id="journalNumber" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label>City</label> <input type="text" class="form-control" id="city" required> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Account Type</label> <select class="form-control" id="accountType" required> <option value="national">National</option> <option value="international">International</option> </select> </div> </div> <div class="col-md-6"> <div class="form-check mt-4"> <input type="checkbox" class="form-check-input" id="isActive" checked> <label class="form-check-label">Active Account</label> </div> <div class="form-check"> <input type="checkbox" class="form-check-input" id="isCurrent"> <label class="form-check-label">Current Account</label> </div> </div> </div> </div> </div> <!-- Financial Parameters --> <div class="card mb-3"> <div class="card-header"> Financial Parameters </div> <div class="card-body"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Bank Overdraft</label> <input type="number" class="form-control" id="bankOverdraft" step="0.01" min="0"> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Overdraft Fee (%)</label> <input type="number" class="form-control" id="overdraftFee" step="0.01" min="0"> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-check mb-2"> <input type="checkbox" class="form-check-input" id="hasCheckDiscountLine"> <label class="form-check-label">Has Check Discount Line</label> </div> <div class="form-group check-discount-amount d-none"> <label>Check Discount Line Amount</label> <input type="number" class="form-control" id="checkDiscountLineAmount" step="0.01" min="0"> </div> </div> <div class="col-md-6"> <div class="form-check mb-2"> <input type="checkbox" class="form-check-input" id="hasLcnDiscountLine"> <label class="form-check-label">Has LCN Discount Line</label> </div> <div class="form-group lcn-discount-amount d-none"> <label>LCN Discount Line Amount</label> <input type="number" class="form-control" id="lcnDiscountLineAmount" step="0.01" min="0"> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Stamp Fee per Receipt</label> <input type="number" class="form-control" id="stampFeePerReceipt" step="0.01" min="0"> </div> </div> </div> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveBankAccount">Save</button> </div> </div> </div> </div> {% endblock %} {% block extra_js %} <script> const BankAccountManager = { init() { this.bindEvents(); this.setupValidation(); }, bindEvents() { $('#saveBankAccount').on('click', () => this.saveBankAccount()); // Toggle discount line amount inputs $('#hasCheckDiscountLine').change(function() { $('.check-discount-amount').toggleClass('d-none', !this.checked); if (this.checked) { $('#checkDiscountLineAmount').prop('required', true); } else { $('#checkDiscountLineAmount').prop('required', false).val(''); } }); $('#hasLcnDiscountLine').change(function() { $('.lcn-discount-amount').toggleClass('d-none', !this.checked); if (this.checked) { $('#lcnDiscountLineAmount').prop('required', true); } else { $('#lcnDiscountLineAmount').prop('required', false).val(''); } }); // Reset form on modal close $('#bankAccountModal').on('hidden.bs.modal', () => { this.resetForm(); }); }, setupValidation() { const form = document.getElementById('bankAccountForm'); // Add validation for numeric fields ['bankOverdraft', 'overdraftFee', 'checkDiscountLineAmount', 'lcnDiscountLineAmount', 'stampFeePerReceipt'].forEach(id => { const input = document.getElementById(id); input.addEventListener('input', () => { const value = parseFloat(input.value); if (value < 0) { input.setCustomValidity('Value must be positive'); } else { input.setCustomValidity(''); } }); }); }, async saveBankAccount() { const form = document.getElementById('bankAccountForm'); if (!form.checkValidity()) { form.reportValidity(); return; } const data = { bank: $('#bank').val(), account_number: $('#accountNumber').val(), accounting_number: $('#accountingNumber').val(), journal_number: $('#journalNumber').val(), city: $('#city').val(), account_type: $('#accountType').val(), is_active: $('#isActive').prop('checked'), is_current: $('#isCurrent').prop('checked'), bank_overdraft: $('#bankOverdraft').val() || null, overdraft_fee: $('#overdraftFee').val() || null, has_check_discount_line: $('#hasCheckDiscountLine').prop('checked'), check_discount_line_amount: $('#hasCheckDiscountLine').prop('checked') ? $('#checkDiscountLineAmount').val() : null, has_lcn_discount_line: $('#hasLcnDiscountLine').prop('checked'), lcn_discount_line_amount: $('#hasLcnDiscountLine').prop('checked') ? $('#lcnDiscountLineAmount').val() : null, stamp_fee_per_receipt: $('#stampFeePerReceipt').val() || null }; const id = $('#accountId').val(); const url = id ? `/testapp/bank-accounts/${id}/edit/` : '/testapp/bank-accounts/create/'; const method = id ? 'POST' : 'POST'; try { const response = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const result = await response.json(); if (response.ok) { $('#bankAccountModal').modal('hide'); showToast('Success', result.message); location.reload(); } else { showToast('Error', result.message); } } catch (error) { showToast('Error', 'Failed to save bank account'); console.error('Error:', error); } }, resetForm() { const form = document.getElementById('bankAccountForm'); form.reset(); $('#accountId').val(''); $('#modalTitle').text('New Bank Account'); $('.check-discount-amount, .lcn-discount-amount').addClass('d-none'); $('#checkDiscountLineAmount, #lcnDiscountLineAmount').prop('required', false); } }; // Initialize when document is ready $(document).ready(function() { BankAccountManager.init(); }); // Global functions for edit and delete function editBankAccount(id) { fetch(`/testapp/bank-accounts/${id}/edit/`) .then(response => response.json()) .then(data => { $('#accountId').val(id); $('#modalTitle').text('Edit Bank Account'); // Fill in the form $('#bank').val(data.bank); $('#accountNumber').val(data.account_number); $('#accountingNumber').val(data.accounting_number); $('#journalNumber').val(data.journal_number); $('#city').val(data.city); $('#accountType').val(data.account_type); $('#isActive').prop('checked', data.is_active); $('#isCurrent').prop('checked', data.is_current); $('#bankOverdraft').val(data.bank_overdraft); $('#overdraftFee').val(data.overdraft_fee); $('#hasCheckDiscountLine').prop('checked', data.has_check_discount_line).trigger('change'); $('#checkDiscountLineAmount').val(data.check_discount_line_amount); $('#hasLcnDiscountLine').prop('checked', data.has_lcn_discount_line).trigger('change'); $('#lcnDiscountLineAmount').val(data.lcn_discount_line_amount); $('#stampFeePerReceipt').val(data.stamp_fee_per_receipt); $('#bankAccountModal').modal('show'); }) .catch(error => { showToast('Error', 'Failed to load bank account details'); console.error('Error:', error); }); } function deleteBankAccount(id) { if (!confirm('Are you sure you want to delete this bank account?')) { return; } fetch(`/testapp/bank-accounts/${id}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }) .then(response => response.json()) .then(result => { if (result.status === 'success') { showToast('Success', result.message); location.reload(); } else { showToast('Error', result.message); } }) .catch(error => { showToast('Error', 'Failed to delete bank account'); console.error('Error:', error); }); } function showToast(title, message) { // Implementation remains the same as before } </script> {% endblock %}
```

# templates/bank/partials/accounts_table.html

```html
{% for account in accounts %} <tr> <td> <div class="d-flex align-items-center"> <span class="bank-logo {{ account.bank|lower }}"></span> <span class="ml-2">{{ account.get_bank_display }}</span> </div> </td> <td>{{ account.account_number }}</td> <td>{{ account.journal_number }}</td> <td>{{ account.city }}</td> <td> <span class="badge {% if account.account_type == 'national' %}badge-primary{% else %}badge-info{% endif %}"> {{ account.get_account_type_display }} </span> </td> <td> <span class="badge {% if account.is_active %}badge-success{% else %}badge-danger{% endif %}"> {{ account.is_active|yesno:"Active,Inactive" }} </span> </td> <td>{{ account.created_at|date:"d/m/Y" }}</td> <td> {% if account.is_active %} <button class="btn btn-sm btn-danger deactivate-account" data-account-id="{{ account.id }}" {% if account.has_active_checkers %}disabled{% endif %} title="{% if account.has_active_checkers %}Cannot deactivate: Has active checkers{% endif %}"> <i class="fas fa-times"></i> </button> {% endif %} </td> </tr> {% endfor %}
```

# templates/base.html

```html
<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>{% block title %}BSK Management{% endblock %}</title> <!-- CSS --> <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet"> <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet"> <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet"> <link href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css" rel="stylesheet"> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"> <!-- Custom Styles --> <style> :root { --primary-color: #2563eb; --sidebar-width: 250px; --topbar-height: 60px; --transition-speed: 0.3s; } body { min-height: 100vh; background-color: #f8fafc; padding-top: var(--topbar-height) } /* Sidebar Styling */ #sidebar { width: var(--sidebar-width); height: 100vh; position: fixed; left: 0; top: 0; background: #1e293b; transition: transform var(--transition-speed); z-index: 1000; } #sidebar.collapsed { transform: translateX(-100%); } #sidebar .nav-link { color: #e2e8f0; padding: 0.8rem 1rem; transition: all var(--transition-speed); } #sidebar .nav-link:hover { background: rgba(255, 255, 255, 0.1); transform: translateX(5px); } #sidebar .nav-link.active { background: var(--primary-color); color: white; } /* Dropdown menu styling */ .nav-dropdown { background: rgba(255, 255, 255, 0.05); } .nav-dropdown .nav-link { padding-left: 2.5rem !important; font-size: 0.9rem; opacity: 0.9; } .nav-item-parent > .nav-link { display: flex; justify-content: space-between; align-items: center; } .nav-item-parent > .nav-link::after { content: '\f107'; font-family: 'Font Awesome 5 Free'; font-weight: 900; transition: transform 0.3s; } .nav-item-parent > .nav-link[aria-expanded="true"]::after { transform: rotate(180deg); } .collapse { transition: all 0.3s ease; } /* Main Content */ #main-content { margin-left: var(--sidebar-width); padding-top: var(--topbar-height); transition: margin var(--transition-speed); padding: 20px; margin-top: 0; } #main-content.expanded { margin-left: 0; } /* Topbar */ #topbar { height: var(--topbar-height); background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); position: fixed; top: 0; right: 0; left: var(--sidebar-width); z-index: 999; transition: left var(--transition-speed); } #topbar.expanded { left: 0; } /* Modal Animations */ .modal.fade .modal-dialog { transform: scale(0.8); transition: transform var(--transition-speed); } .modal.show .modal-dialog { transform: scale(1); } .modal { z-index: 1050; } /* Toast Animations */ .toast { position: fixed; top: 20px; right: 20px; z-index: 1050; animation: slideIn 0.3s ease-out; } @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } } /* Card Hover Effects */ .card { transition: transform 0.2s, box-shadow 0.2s; } .card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); } /* Button Hover Effects */ .btn { transition: all 0.2s; } .btn:hover { transform: translateY(-1px); } /* Table Row Hover */ .table-hover tbody tr { transition: background-color 0.2s; } /* Select2 Styling */ .select2-container--default .select2-selection--single { height: 38px; border: 1px solid #ced4da; border-radius: 0.375rem; } .select2-container--default .select2-selection--single .select2-selection__rendered { line-height: 38px; } /* Ensure dropdowns appear above other elements */ .dropdown-menu { z-index: 1000; } /* Keep autocomplete dropdown above other elements */ .ui-autocomplete { z-index: 2000; .timeline-item { opacity: 0; } .timeline-item.animate__animated { opacity: 1; } /* Custom animation for loading spinner */ @keyframes modalFadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } } .modal.show .modal-dialog { animation: modalFadeIn 0.3s ease-out; } /* Enhance timeline visuals */ .timeline-content:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); transform: translateY(-2px); transition: all 0.3s ease; } .timeline-marker::after { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: white; border-radius: 50%; } } </style> <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script> <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script> </head> <body> <!-- Sidebar --> <nav id="sidebar"> <div class="d-flex flex-column h-100"> <div class="p-3 text-center"> <h5 class="text-white mb-0">BSK Management</h5> </div> <ul class="nav flex-column mt-2"> <li class="nav-item"> <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" href="{% url 'home' %}"> <i class="fas fa-home me-2"></i> Dashboard </a> </li> <!-- Business Operations Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'business' in request.path %}active{% endif %}" data-toggle="collapse" href="#businessSubmenu" role="button" aria-expanded="false" aria-controls="businessSubmenu"> <span><i class="fas fa-briefcase me-2"></i> Business Operations</span> </a> <div class="collapse nav-dropdown" id="businessSubmenu"> <a class="nav-link {% if 'supplier' in request.path %}active{% endif %}" href="{% url 'supplier-list' %}"> <i class="fas fa-truck me-2"></i> Suppliers </a> <a class="nav-link {% if 'product' in request.path %}active{% endif %}" href="{% url 'product-list' %}"> <i class="fas fa-box-open me-2"></i> Products </a> <a class="nav-link {% if 'invoice' in request.path %}active{% endif %}" href="{% url 'invoice-list' %}"> <i class="fas fa-file-invoice-dollar me-2"></i> Invoices </a> </div> </li> <!-- Clients Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'client' in request.path %}active{% endif %}" data-toggle="collapse" href="#clientSubmenu" role="button" aria-expanded="false" aria-controls="clientSubmenu"> <span><i class="fas fa-users me-2"></i> Clients</span> </a> <div class="collapse nav-dropdown" id="clientSubmenu"> <a class="nav-link {% if 'receipt' in request.path %}active{% endif %}" href="{% url 'receipt-list' %}"> <i class="fas fa-receipt me-2"></i> Receipts </a> <a class="nav-link {% if 'client_management' in request.path %}active{% endif %}" href="{% url 'client_management' %}"> <i class="fas fa-address-card me-2"></i> Clients </a> <a class="nav-link {% if 'sale-list' in request.path %}active{% endif %}" href="{% url 'sale-list' %}"> <i class="fas fa-shopping-cart me-2"></i> Sales </a> <a class="nav-link {% if 'presentation' in request.path %}active{% endif %}" href="{% url 'presentation-list' %}"> <i class="fas fa-file-powerpoint me-2"></i> Presentations </a> </div> </li> <!-- Financial Management Section --> <li class="nav-item nav-item-parent"> <a class="nav-link {% if 'financial' in request.path %}active{% endif %}" data-toggle="collapse" href="#financialSubmenu" role="button" aria-expanded="false" aria-controls="financialSubmenu"> <span><i class="fas fa-money-bill-wave me-2"></i> Financial Management</span> </a> <div class="collapse nav-dropdown" id="financialSubmenu"> <a class="nav-link {% if 'bank-account' in request.path %}active{% endif %}" href="{% url 'bank-account-list' %}"> <i class="fas fa-university me-2"></i> Bank Accounts </a> <a class="nav-link {% if 'checks' in request.path %}active{% endif %}" href="{% url 'check-list' %}"> <i class="fas fa-money-check me-2"></i> Checks </a> <a class="nav-link {% if 'checkers' in request.path %}active{% endif %}" href="{% url 'checker-list' %}"> <i class="fas fa-user-shield me-2"></i> Checkers </a> </div> </li> <!-- Bottom Section --> <div class="mt-auto p-3"> <div class="dropdown"> <button class="btn btn-dark dropdown-toggle w-100" type="button" data-bs-toggle="dropdown"> <i class="fas fa-user-circle me-2"></i> {{ request.user.username }} </button> <ul class="dropdown-menu dropdown-menu-dark w-100"> <li> <a class="dropdown-item" href="{% url 'profile' %}"> <i class="fas fa-id-card me-2"></i> Profile </a> </li> <li><hr class="dropdown-divider"></li> <li> <a class="dropdown-item text-danger" href="{% url 'logout' %}"> <i class="fas fa-sign-out-alt me-2"></i> Logout </a> </li> </ul> </div> </div> </div> </nav> <!-- Topbar --> <nav id="topbar" class="px-4 d-flex align-items-center"> <button id="sidebar-toggle" class="btn btn-link"> <i class="fas fa-bars"></i> </button> <div class="ms-auto d-flex align-items-center"> <div class="dropdown"> <button class="btn btn-link dropdown-toggle" type="button" data-bs-toggle="dropdown"> <i class="fas fa-bell"></i> <span class="badge bg-danger">3</span> </button> <ul class="dropdown-menu dropdown-menu-end"> <li><h6 class="dropdown-header">Notifications</h6></li> <li><a class="dropdown-item" href="#">New invoice added</a></li> <li><a class="dropdown-item" href="#">Payment received</a></li> <li><a class="dropdown-item" href="#">Check due today</a></li> </ul> </div> </div> </nav> <!-- Main Content --> <main id="main-content" class="p-4"> {% block content %}{% endblock %} </main> <!-- Scripts --> <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.min.js"></script> <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script> <script> $(document).ready(function() { // Sidebar Toggle $('#sidebar-toggle').click(function() { $('#sidebar').toggleClass('collapsed'); $('#main-content').toggleClass('expanded'); $('#topbar').toggleClass('expanded'); }); // Initialize Select2 $('.select2').select2({ theme: 'bootstrap' }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); // Keep submenu open if a child is active if ($('#clientSubmenu .nav-link.active').length) { $('#clientSubmenu').addClass('show'); $('#clientSubmenu').prev('.nav-link').attr('aria-expanded', 'true'); } }); // Toast function function showToast(message, type = 'success') { const toast = ` <div class="toast align-items-center text-white bg-${type}" role="alert"> <div class="d-flex"> <div class="toast-body">${message}</div> <button type="button" class="close ml-2 mb-1" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> </div> `; const toastContainer = $('<div>', { class: 'position-fixed', style: 'top: 20px; right: 20px; z-index: 1060;' }).html(toast); $('body').append(toastContainer); toastContainer.find('.toast').toast({ delay: 3000 }).toast('show'); toastContainer.find('.toast').on('hidden.bs.toast', function() { toastContainer.remove(); }); } </script> {% block extra_js %}{% endblock %} </body> </html>
```

# templates/client/client_card.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>{{ client.name }} - Client Card</h2> <!-- Period Selection --> <div class="d-flex gap-2"> <form class="form-inline" method="get"> <select name="year" class="form-control mr-2"> {% for year_choice in years %} <option value="{{ year_choice }}" {% if year_choice == selected_year %}selected{% endif %}> {{ year_choice }} </option> {% endfor %} </select> <select name="month" class="form-control mr-2"> {% for month_num, month_name in months %} <option value="{{ month_num }}" {% if month_num == selected_month %}selected{% endif %}> {{ month_name }} </option> {% endfor %} </select> <button type="submit" class="btn btn-primary">Apply</button> </form> </div> </div> <!-- Summary Cards --> <div class="row mb-4"> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Debit</h5> <p class="card-text text-danger h4">{{ total_debit|floatformat:2 }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Total Credit</h5> <p class="card-text text-success h4">{{ total_credit|floatformat:2 }}</p> </div> </div> </div> <div class="col-md-4"> <div class="card"> <div class="card-body"> <h5 class="card-title">Balance</h5> <p class="card-text h4 {% if final_balance > 0 %}text-danger{% else %}text-success{% endif %}"> {{ final_balance|floatformat:2 }} </p> </div> </div> </div> </div> <!-- Transactions Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Description</th> <th class="text-right">Debit</th> <th class="text-right">Credit</th> <th class="text-right">Balance</th> </tr> </thead> <tbody> {% for t in transactions %} <tr {% if t.type == 'BALANCE' %}class="table-info"{% endif %}> <td>{{ t.date|date:"Y-m-d" }}</td> <td>{{ t.description }}</td> <td class="text-right text-danger"> {% if t.debit %}{{ t.debit|floatformat:2 }}{% endif %} </td> <td class="text-right text-success"> {% if t.credit %}{{ t.credit|floatformat:2 }}{% endif %} </td> <td class="text-right {% if t.balance > 0 %}text-danger{% else %}text-success{% endif %}"> {{ t.balance|floatformat:2 }} </td> </tr> {% empty %} <tr> <td colspan="5" class="text-center">No transactions found for this period</td> </tr> {% endfor %} </tbody> </table> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Auto-submit form when selection changes $('select[name="year"], select[name="month"]').change(function() { $(this).closest('form').submit(); }); }); </script> {% endblock %}
```

# templates/client/client_management.html

```html
{% extends 'base.html' %} {% load static %} {% block extra_css %} <link rel="stylesheet" href="{% static 'css/client.css' %}"> {% endblock %} {% block content %} <div class="container-fluid px-4"> <div class="row mt-4"> <div class="col"> <!-- Tabs Navigation --> <ul class="nav nav-tabs nav-fill border-0" id="clientTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active custom-tab" id="clients-tab" data-toggle="tab" href="#clients" role="tab"> <i class="fas fa-users me-2"></i> Clients </a> </li> <li class="nav-item"> <a class="nav-link custom-tab" id="entities-tab" data-toggle="tab" href="#entities" role="tab"> <i class="fas fa-building me-2"></i> Entities </a> </li> </ul> <!-- Tabs Content --> <div class="tab-content mt-4" id="clientTabsContent"> <!-- Clients Tab --> <div class="tab-pane fade show active" id="clients" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-users text-primary me-2"></i> Clients Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#clientModal"> <i class="fas fa-plus-circle me-2"></i> Add New Client </button> </div> <!-- Clients Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="clientsTable"> <thead class="bg-light"> <tr> <th>Client Code</th> <th>Name</th> <th>Created At</th> <th>Actions</th> </tr> </thead> <tbody id="clientsTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> <!-- Entities Tab --> <div class="tab-pane fade" id="entities" role="tabpanel"> <!-- Header --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-building text-primary me-2"></i> Entities Management </h2> <button type="button" class="btn btn-primary btn-lg shadow-sm rounded-pill" data-toggle="modal" data-target="#entityModal"> <i class="fas fa-plus-circle me-2"></i> Add New Entity </button> </div> <!-- Entities Table --> <div class="card shadow-sm"> <div class="card-body"> <div class="table-responsive"> <table class="table table-hover" id="entitiesTable"> <thead class="bg-light"> <tr> <th>Name</th> <th>ICE Code</th> <th>Accounting Code</th> <th>City</th> <th>Phone</th> <th>Actions</th> </tr> </thead> <tbody id="entitiesTableBody"> <!-- Populated by JavaScript --> </tbody> </table> </div> </div> </div> </div> </div> </div> </div> </div> {% include 'client/components/client_modal.html' %} {% include 'client/components/entity_modal.html' %} <script> console.log('Initializing client management module...'); // Validation configurations const ValidationConfig = { clientCode: { minLength: 5, maxLength: 10, pattern: /^\d+$/, messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 10 digits' } }, iceCode: { length: 15, pattern: /^\d+$/, inputPattern: /[0-9]/, // Add this - for single digit validation messages: { pattern: 'Only digits are allowed', length: 'Must be exactly 15 digits' } }, accountingCode: { minLength: 5, maxLength: 7, pattern: /^\d+$/, // Just check for digits initially messages: { pattern: 'Only digits are allowed', minLength: 'Must be at least 5 digits', maxLength: 'Cannot exceed 7 digits' } }, name: { pattern: /^[a-zA-Z\s]+$/, messages: { pattern: 'Only letters and spaces allowed' } } }; class FormValidator { constructor(formId, config) { this.form = document.getElementById(formId); this.config = config; console.log(`Initializing validator for form: ${formId}`); this.setupValidation(); } setupValidation() { const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { console.log(`Setting up validation for: ${input.id}`); this.setupInputValidation(input); }); } setupInputValidation(input) { const validationType = input.dataset.validate; const rules = this.config[validationType]; // Real-time validation input.addEventListener('input', (e) => { console.log(`Input event on ${input.id}`); this.validateInput(input, rules); }); // Blur validation input.addEventListener('blur', (e) => { console.log(`Blur event on ${input.id}`); this.validateInput(input, rules, true); }); // Prevent invalid characters input.addEventListener('keypress', (e) => { if (rules.pattern && !String.fromCharCode(e.charCode).match(rules.pattern)) { e.preventDefault(); } }); // Prevent invalid characters and enforce length input.addEventListener('keypress', (e) => { // Check max length for ICE code if (validationType === 'iceCode' && input.value.length >= 15) { e.preventDefault(); return; } // Special handling for first character of accounting code if (validationType === 'accountingCode') { if (input.value.length === 0 && e.key !== '3') { e.preventDefault(); return; } if (input.value.length >= 7) { e.preventDefault(); return; } } // Use inputPattern for digit validation if (!e.key.match(rules.inputPattern)) { e.preventDefault(); } }); } validateInput(input, rules, isBlur = false) { const value = input.value.trim(); let isValid = true; let message = ''; // Add validating class during check input.classList.add('is-validating'); // Required field validation if (input.required && !value) { isValid = false; message = 'This field is required'; this.updateValidationUI(input, false, message); return false; } // Special validation for accounting code if (input.dataset.validate === 'accountingCode') { if (!value.startsWith('3')) { isValid = false; message = 'Must start with 3'; } } // Uniqueness check for client_code and accounting_code on blur if (isBlur && (input.id === 'clientCode' || input.id === 'accountingCode' || input.id === 'iceCode')) { fetch(`/testapp/api/validate/${input.id}/${value}/`) .then(response => response.json()) .then(data => { if (!data.available) { isValid = false; message = `This ${input.id.replace('Code', ' code')} already exists`; this.updateValidationUI(input, false, message, true); } }) .catch(error => { console.error(`Error checking ${input.id} uniqueness:`, error); }); } // Pattern validation if (rules.pattern && !value.match(rules.pattern)) { isValid = false; message = rules.messages.pattern; } // Length validation if (rules.length && value.length !== rules.length) { isValid = false; message = rules.messages.length; } if (rules.minLength && value.length < rules.minLength) { isValid = false; message = rules.messages.minLength; } if (rules.maxLength && value.length > rules.maxLength) { isValid = false; message = rules.messages.maxLength; } // Update UI with validation result setTimeout(() => { input.classList.remove('is-validating'); this.updateValidationUI(input, isValid, message, isBlur); this.checkFormValidity(); }, 300); return isValid; } checkFormValidity() { let isValid = true; const formId = this.formId; const form = document.querySelector(`#${formId}:not(.d-none), #${formId}:not(.hide)`); if (!form) { console.debug(`Form ${formId} not found or not visible`); return true; } const inputs = form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { // Check for empty required fields if (input.required && !input.value.trim()) { isValid = false; return; } // Check for validation state if (input.classList.contains('is-invalid') || (input.required && !input.classList.contains('is-valid'))) { isValid = false; return; } }); // Update save button state const saveButton = form.querySelector('button[type="submit"]'); if (saveButton) { saveButton.disabled = !isValid; console.debug(`Form ${formId} validity: ${isValid}`); } return isValid; } updateValidationUI(input, isValid, message, isBlur) { const feedback = input.nextElementSibling; if (isValid) { input.classList.remove('is-invalid'); input.classList.add('is-valid'); if (feedback && feedback.classList.contains('invalid-feedback')) { feedback.classList.remove('show'); } } else if (isBlur || input.value.length > 0) { input.classList.remove('is-valid'); input.classList.add('is-invalid'); if (feedback) { feedback.textContent = message; feedback.classList.add('show'); } } } validateForm() { let isValid = true; const inputs = this.form.querySelectorAll('input[data-validate]'); inputs.forEach(input => { const validationType = input.dataset.validate; const rules = this.config[validationType]; if (!this.validateInput(input, rules, true)) { isValid = false; } }); return isValid; } } // Client Management class class ClientManagement { constructor() { console.log('Initializing ClientManagement'); this.initializeValidators(); this.bindEvents(); this.loadClients(); this.loadEntities(); } initializeValidators() { this.clientValidator = new FormValidator('clientForm', ValidationConfig); this.entityValidator = new FormValidator('entityForm', ValidationConfig); } // Event Binding bindEvents() { $('#saveClientBtn').on('click', () => this.saveClient()); $('#saveEntityBtn').on('click', () => this.saveEntity()); // Reset forms on modal close $('#clientModal').on('hidden.bs.modal', () => this.resetForm('clientForm')); $('#entityModal').on('hidden.bs.modal', () => this.resetForm('entityForm')); // Tab change handlers $('#clientTabs a[data-toggle="tab"]').on('shown.bs.tab', (e) => { if (e.target.id === 'clients-tab') { this.loadClients(); } else { this.loadEntities(); } }); } // Client Operations async loadClients() { console.log('Loading clients...'); try { const response = await fetch('/testapp/api/clients/'); const data = await response.json(); const tbody = $('#clientsTableBody'); tbody.empty(); data.clients.forEach(client => { const formattedDate = this.formatDate(client.created_at); tbody.append(` <tr class="fade-in"> <td>${client.client_code}</td> <td>${client.name}</td> <td>${formattedDate}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editClient('${client.id}', '${client.name}', '${client.client_code}')"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger me-2" onclick="window.clientManagement.deleteClient('${client.id}')"> <i class="fas fa-trash"></i> </button> <a href="/testapp/clients/${client.id}/card/" class="btn btn-sm btn-outline-info"> <i class="fas fa-chart-line me-1"></i> Sales Card </a> </td> </tr> `); console.log('Client loaded:', client, formattedDate); }); } catch (error) { console.error('Error loading clients:', error); this.showToast('Error', 'Failed to load clients'); } } async saveClient() { console.log('Saving client...'); if (!this.clientValidator.validateForm()) { console.log('Client form validation failed'); return; } const formData = { name: $('#clientName').val().trim(), client_code: $('#clientCode').val().trim() }; const id = $('#clientId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/clients/${id}/update/` : '/testapp/api/clients/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Client saved successfully:', result); $('#clientModal').modal('hide'); await this.loadClients(); this.showToast('Success', 'Client saved successfully'); } } catch (error) { console.error('Error saving client:', error); this.showToast('Error', error.message); } } editClient(id, name, client_code) { console.log('Editing client:', id); $('#clientId').val(id); $('#clientName').val(name); $('#clientCode').val(client_code); $('#clientModalTitle .title-text').text('Edit Client'); $('#clientModal').modal('show'); } async deleteClient(id) { if (!confirm('Are you sure you want to delete this client?')) { return; } try { const response = await this.sendRequest( `/testapp/api/clients/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadClients(); this.showToast('Success', 'Client deleted successfully'); } } catch (error) { console.error('Error deleting client:', error); this.showToast('Error', error.message); } } // Entity Operations async loadEntities() { console.log('Loading entities...'); try { const response = await fetch('/testapp/api/entities/'); const data = await response.json(); const tbody = $('#entitiesTableBody'); tbody.empty(); data.entities.forEach(entity => { tbody.append(` <tr class="fade-in"> <td>${entity.name}</td> <td>${entity.ice_code}</td> <td>${entity.accounting_code}</td> <td>${entity.city || '-'}</td> <td>${entity.phone_number || '-'}</td> <td> <button class="btn btn-sm btn-outline-primary me-2" onclick="window.clientManagement.editEntity('${entity.id}', ${JSON.stringify(entity)})"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-outline-danger" onclick="window.clientManagement.deleteEntity('${entity.id}')"> <i class="fas fa-trash"></i> </button> </td> </tr> `); }); } catch (error) { console.error('Error loading entities:', error); this.showToast('Error', 'Failed to load entities'); } } async saveEntity() { console.log('Saving entity...'); if (!this.entityValidator.validateForm()) { console.log('Entity form validation failed'); return; } const formData = { name: $('#entityName').val().trim(), ice_code: $('#iceCode').val().trim(), accounting_code: $('#accountingCode').val().trim(), city: $('#city').val().trim(), phone_number: $('#phoneNumber').val().trim() }; const id = $('#entityId').val(); const method = id ? 'PUT' : 'POST'; const url = id ? `/testapp/api/entities/${id}/update/` : '/testapp/api/entities/create/'; try { const response = await this.sendRequest(url, method, formData); if (response.ok) { const result = await response.json(); console.log('Entity saved successfully:', result); $('#entityModal').modal('hide'); await this.loadEntities(); this.showToast('Success', 'Entity saved successfully'); } } catch (error) { console.error('Error saving entity:', error); this.showToast('Error', error.message); } } editEntity(id, entityData) { console.log('Editing entity:', id); $('#entityId').val(id); $('#entityName').val(entityData.name); $('#iceCode').val(entityData.ice_code); $('#accountingCode').val(entityData.accounting_code); $('#city').val(entityData.city || ''); $('#phoneNumber').val(entityData.phone_number || ''); $('#entityModalTitle .title-text').text('Edit Entity'); $('#entityModal').modal('show'); } async deleteEntity(id) { if (!confirm('Are you sure you want to delete this entity?')) { return; } try { const response = await this.sendRequest( `/testapp/api/entities/${id}/delete/`, 'DELETE' ); if (response.ok) { await this.loadEntities(); this.showToast('Success', 'Entity deleted successfully'); } } catch (error) { console.error('Error deleting entity:', error); this.showToast('Error', error.message); } } // Utility Methods formatDate(dateString) { if (!dateString) return '-'; try { const date = new Date(dateString); return date.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }); } catch (e) { console.error('Error formatting date:', e); return dateString; } } async sendRequest(url, method, data = null) { const options = { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value } }; if (data && method !== 'GET') { options.body = JSON.stringify(data); } const response = await fetch(url, options); if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'Request failed'); } return response; } resetForm(formId) { console.log(`Resetting form: ${formId}`); const form = document.getElementById(formId); form.reset(); const inputs = form.querySelectorAll('.form-control'); inputs.forEach(input => { input.classList.remove('is-valid', 'is-invalid', 'is-validating'); const feedback = input.nextElementSibling; if (feedback) { feedback.classList.remove('show'); } }); // Reset titles if (formId === 'clientForm') { $('#clientModalTitle .title-text').text('Add New Client'); $('#clientId').val(''); } else { $('#entityModalTitle .title-text').text('Add New Entity'); $('#entityId').val(''); } } showToast(title, message) { // You can replace this with your preferred notification library alert(`${title}: ${message}`); } } // Initialize when document is ready document.addEventListener('DOMContentLoaded', () => { console.log('Initializing client management module'); window.clientManagement = new ClientManagement(); }); </script> {% endblock %}
```

# templates/client/components/client_modal.html

```html
<!-- Client Modal --> <div class="modal fade" id="clientModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="clientModalTitle"> <i class="fas fa-user-plus me-2"></i> <span class="title-text"> Add New Client</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="clientForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="clientId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="clientName" class="form-label"> <i class="fas fa-signature me-2"></i> Client Name </label> <input type="text" class="form-control" id="clientName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- Client Code Field --> <div class="form-group mb-4"> <label for="clientCode" class="form-label"> <i class="fas fa-hashtag me-2"></i> Client Code </label> <input type="text" class="form-control" id="clientCode" data-validate="clientCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Enter a unique code (5-10 digits) </small> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i> Cancel </button> <button type="button" class="btn btn-primary" id="saveClientBtn"> <i class="fas fa-save me-2"></i> Save Client </button> </div> </div> </div> </div>
```

# templates/client/components/entity_modal.html

```html
<!-- Entity Modal --> <div class="modal fade" id="entityModal" tabindex="-1" role="dialog"> <div class="modal-dialog modal-dialog-centered" role="document"> <div class="modal-content"> <div class="modal-header bg-primary text-white"> <h5 class="modal-title" id="entityModalTitle"> <i class="fas fa-building me-2"></i> <span class="title-text"> Add New Entity</span> </h5> <button type="button" class="close text-white" data-dismiss="modal"> <span>&times;</span> </button> </div> <div class="modal-body"> <form id="entityForm" class="needs-validation" novalidate> {% csrf_token %} <input type="hidden" id="entityId"> <!-- Name Field --> <div class="form-group mb-4"> <label for="entityName" class="form-label"> <i class="fas fa-signature me-2"></i> Entity Name </label> <input type="text" class="form-control" id="entityName" data-validate="name" required> <div class="invalid-feedback"></div> </div> <!-- ICE Code Field --> <div class="form-group mb-4"> <label for="iceCode" class="form-label"> <i class="fas fa-fingerprint me-2"></i> ICE Code </label> <input type="text" class="form-control" id="iceCode" data-validate="iceCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must be exactly 15 digits </small> </div> <!-- Accounting Code Field --> <div class="form-group mb-4"> <label for="accountingCode" class="form-label"> <i class="fas fa-calculator me-2"></i> Accounting Code </label> <input type="text" class="form-control" id="accountingCode" data-validate="accountingCode" required> <div class="invalid-feedback"></div> <small class="text-muted"> Must start with 3 and be 5-7 digits long </small> </div> <!-- Optional Fields --> <div class="row"> <div class="col-md-6"> <div class="form-group mb-4"> <label for="city" class="form-label"> <i class="fas fa-city me-2"></i> City </label> <input type="text" class="form-control" id="city"> </div> </div> <div class="col-md-6"> <div class="form-group mb-4"> <label for="phoneNumber" class="form-label"> <i class="fas fa-phone me-2"></i> Phone Number </label> <input type="tel" class="form-control" id="phoneNumber"> </div> </div> </div> </form> </div> <div class="modal-footer bg-light"> <button type="button" class="btn btn-secondary" data-dismiss="modal"> <i class="fas fa-times me-2"></i> Cancel </button> <button type="button" class="btn btn-primary" id="saveEntityBtn"> <i class="fas fa-save me-2"></i> Save Entity </button> </div> </div> </div> </div>
```

# templates/client/sale_list.html

```html
{% extends 'base.html' %} {% block content %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Client Sales</h2> <button class="btn btn-primary" data-toggle="modal" data-target="#saleModal"> <i class="fas fa-plus"></i> New Sale </button> </div> <!-- Sales Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Type</th> <th>Amount</th> <th>Notes</th> </tr> </thead> <tbody> {% for sale in sales %} <tr> <td>{{ sale.date|date:"Y-m-d" }}</td> <td>{{ sale.client.name }}</td> <td>{{ sale.get_sale_type_display }}</td> <td class="text-right">{{ sale.amount|floatformat:2 }}</td> <td>{{ sale.notes }}</td> </tr> {% empty %} <tr> <td colspan="4" class="text-center">No sales recorded yet</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Sale Modal --> <div class="modal fade" id="saleModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Record New Sale</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="saleForm"> {% csrf_token %} <div class="form-group"> <label for="client">Client</label> <input type="text" class="form-control" id="client" placeholder="Search client..." required> <input type="hidden" id="client_id" name="client" required> </div> <div class="form-group"> <label for="date">Date</label> <input type="date" class="form-control" id="date" name="date" value="{% now 'Y-m-d' %}" required> </div> <div class="form-group"> <label for="sale_type">Sale Type</label> <select class="form-control" id="sale_type" name="sale_type" required> <option value="BRICKS">Bricks</option> <option value="TRANSPORT">Transport</option> </select> </div> <div class="form-group"> <label for="amount">Amount</label> <input type="number" class="form-control" id="amount" name="amount" step="0.01" min="0.01" required> </div> <div class="form-group"> <label for="notes">Notes</label> <textarea class="form-control" id="notes" name="notes" rows="2"></textarea> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="saveSale">Save</button> </div> </div> </div> </div> {% endblock %} {% block extra_js %} <script> $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 2, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Handle form submission $('#saveSale').click(function() { const form = $('#saleForm'); $.ajax({ url: "{% url 'create-sale' %}", method: 'POST', data: form.serialize(), success: function(response) { $('#saleModal').modal('hide'); showToast('Sale recorded successfully'); location.reload(); }, error: function(xhr) { showToast(xhr.responseJSON.message, 'error'); } }); }); }); </script> {% endblock %}
```

# templates/home.html

```html
{% extends 'base.html' %} {% block title %}Home - MyProject{% endblock %} {% block content %} <h1>Welcome to MyProject!</h1> <p>This is the home page.</p> {% endblock %}
```

# templates/login.html

```html
{% extends 'base.html' %} {% block title %}Login - MyProject{% endblock %} {% block content %} <div class="container"> <h2>Login</h2> <form method="post"> {% csrf_token %} <div class="form-group"> <label for="username">Username:</label> <input type="text" id="username" name="username" class="form-control" required> </div> <div class="form-group"> <label for="password">Password:</label> <input type="password" id="password" name="password" class="form-control" required> </div> <button type="submit" class="btn btn-primary">Login</button> </form> </div> {% endblock %}
```

# templates/presentation/available_receipts.html

```html
<div class="receipt-container"> <!-- Summary info --> <div class="alert alert-info"> <strong>Selected:</strong> <span id="selectedCount">0</span> receipts <strong class="ml-3">Total Amount:</strong> <span id="selectedAmount">0.00</span> MAD </div> <!-- Receipts table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input" id="selectAll"> <label class="custom-control-label" for="selectAll"></label> </div> </th> <th>Reference</th> <th>Entity</th> <th>Issue Date</th> <th>Due Date</th> <th>Amount</th> <th>Days to Due</th> </tr> </thead> <tbody> {% for receipt in receipts %} <!-- In available_receipts.html --> <tr> <td> <div class="custom-control custom-checkbox"> <input type="checkbox" class="custom-control-input receipt-checkbox" id="receipt{{ receipt.id }}" value="{{ receipt.id }}" data-amount="{{ receipt.amount }}"> <label class="custom-control-label" for="receipt{{ receipt.id }}"></label> </div> </td> <td>{{ receipt.get_receipt_number }}</td> <td>{{ receipt.entity.name }}</td> <td>{{ receipt.operation_date|date:"Y-m-d" }}</td> <td>{{ receipt.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ receipt.amount|floatformat:2 }}</td> <td> <span class="badge badge-{{ receipt.status|lower }}"> {{ receipt.get_status_display }} </span> {% if receipt.status == 'UNPAID' and receipt.last_presentation_date %} <br> <small class="text-muted"> Previously presented on {{ receipt.last_presentation_date|date:"Y-m-d" }} </small> {% endif %} </td> </tr> {% endfor %} </tbody> </table> </div> </div> <script> $(document).ready(function() { // Handle select all checkbox $('#selectAll').change(function() { $('.receipt-checkbox').prop('checked', $(this).prop('checked')); updateSelection(); }); // Handle individual checkboxes $('.receipt-checkbox').change(function() { updateSelection(); // Update select all checkbox state $('#selectAll').prop('checked', $('.receipt-checkbox').length === $('.receipt-checkbox:checked').length); }); function updateSelection() { const selected = $('.receipt-checkbox:checked'); $('#selectedCount').text(selected.length); const totalAmount = selected.toArray() .reduce((sum, checkbox) => sum + parseFloat($(checkbox).data('amount')), 0); $('#selectedAmount').text(totalAmount.toFixed(2)); // Enable/disable save button based on selection $('#savePresentation').prop('disabled', selected.length === 0); } }); </script>
```

# templates/presentation/presentation_detail_modal.html

```html
{% load presentation_filters %} <!-- Debug info --> {% comment %} Available filters: {{ presentation_filters }} {% endcomment %} <!-- Test filter directly --> {% with test_status='pending' %} Raw status: {{ test_status }} Filtered status: {{ test_status|status_badge }} {% endwith %} <div id="presentation-container" data-presentation-id="{{ presentation.id }}"> <div class="modal-header"> <h5 class="modal-title"> {{ presentation.get_presentation_type_display }} Presentation Details </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Presentation Info --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <p><strong>Date:</strong> {{ presentation.date|date:"Y-m-d" }}</p> <p><strong>Bank Account:</strong> {{ presentation.bank_account }}</p> <p><strong>Total Amount:</strong> {{ presentation.total_amount|floatformat:2 }}</p> </div> <div class="col-md-6 d-flex flex-column"> {% if presentation.status == 'pending' %} <div class="form-group"> <label>Bank Reference</label> <input type="text" class="form-control" id="bankReference" value="{{ presentation.bank_reference }}" required> </div> <div class="form-group"> <label>Status</label> <select class="form-control" id="presentationStatus"> <option value="presented">Presented</option> <option value="discounted">Discounted</option> <option value="rejected">Rejected</option> </select> </div> {% else %} <p><strong>Bank Reference:</strong> {{ presentation.bank_reference }}</p> <p><strong>Status:</strong> <span class="badge badge-{{ presentation.status|status_badge }}"> {{ presentation.get_status_display }} </span> </p> {% endif %} <p><strong>Notes:</strong> {{ presentation.notes|default:"No notes" }}</p> </div> </div> </div> </div> <!-- Receipts Table --> <h6>Presented Receipts</h6> <div class="table-responsive"> <table class="table table-sm"> <thead> <tr> <th>Type</th> <th>Reference</th> <th>Entity</th> <th>Client</th> <th>Due Date</th> <th class="text-right">Amount</th> <th>Status</th> {% if presentation.status == 'presented' %} <th>New Status</th> {% endif %} </tr> </thead> <tbody> {% for receipt in presentation.presentation_receipts.all %} <tr> <td> {% if receipt.checkreceipt %} <i class="fas fa-money-check"></i> Check {% else %} <i class="fas fa-file-invoice-dollar"></i> LCN {% endif %} </td> <td> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.check_number }} <br><small class="text-muted">{{ receipt.checkreceipt.get_issuing_bank_display }}</small> {% else %} {{ receipt.lcn.lcn_number }} <br><small class="text-muted">{{ receipt.lcn.get_issuing_bank_display }}</small> {% endif %} </td> <td> <strong> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.entity.name }} {% else %} {{ receipt.lcn.entity.name }} {% endif %} </strong> <br> <small class="text-muted"> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.entity.ice_code }} {% else %} {{ receipt.lcn.entity.ice_code }} {% endif %} </small> </td> <td> <small> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.client.name }} {% else %} {{ receipt.lcn.client.name }} {% endif %} </small> </td> <td> {% if receipt.checkreceipt %} {{ receipt.checkreceipt.due_date|date:"Y-m-d" }} {% else %} {{ receipt.lcn.due_date|date:"Y-m-d" }} {% endif %} </td> <td class="text-right">{{ receipt.amount|floatformat:2 }}</td> <td> {% if receipt.checkreceipt %} <span class="badge badge-{{ receipt.checkreceipt.status|status_badge }}"> {{ receipt.checkreceipt.get_status_display }} </span> {% if receipt.checkreceipt.status == 'UNPAID' and receipt.checkreceipt.rejection_cause %} <br><small class="text-danger">{{ receipt.checkreceipt.get_rejection_cause_display}}</small> {% endif %} {% if receipt.checkreceipt.compensation_info %} <br><small class="text-muted">{{ receipt.checkreceipt.compensation_info }}</small> {% endif %} {% else %} <span class="badge badge-{{ receipt.lcn.status|status_badge }}"> {{ receipt.lcn.get_status_display }} </span> {% if receipt.lcn.status == 'UNPAID' and receipt.lcn.rejection_cause %} <br><small class="text-danger">{{ receipt.lcn.get_rejection_cause_display }}</small> {% endif %} {% if receipt.lcn.compensation_info %} <br><small class="text-muted">{{ receipt.lcn.compensation_info }}</small> {% endif %} {% endif %} </td> {% if presentation.status == 'presented' or presentation.status == 'discounted' %} <td> <select class="form-control form-control-sm receipt-status" data-receipt-id="{{ receipt.id }}" {% if receipt.recorded_status %}disabled{% endif %}> <option value="">Pending</option> <option value="paid" {% if receipt.recorded_status == 'PAID' or receipt.checkreceipt.status == 'PAID' or receipt.lcn.status == 'PAID' %}selected{% endif %}>Paid</option> <option value="unpaid" {% if receipt.recorded_status == 'UNPAID' or receipt.checkreceipt.status == 'UNPAID' or receipt.lcn.status == 'UNPAID' %}selected{% endif %}>Unpaid</option> </select> </td> {% endif %} </tr> {% endfor %} </tbody> <tfoot> <tr class="font-weight-bold"> <td colspan="5" class="text-right">Total:</td> <td class="text-right">{{ presentation.total_amount|floatformat:2 }}</td> <td colspan="2"></td> </tr> </tfoot> </table> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> {% if presentation.status == 'pending' %} <button type="button" class="btn btn-primary" onclick="updatePresentation('{{ presentation.id }}')"> Update Status </button> {% endif %} {% if presentation.status == 'presented' or presentation.status == 'discounted' %} <button type="button" class="btn btn-primary" onclick="updateReceiptStatuses('{{ presentation.id }}')"> Update Statuses </button> {% endif %} </div> <!-- Unpaid Cause Modal --> <div class="modal fade" id="unpaidCauseModal" tabindex="-1"> <div class="modal-dialog"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title">Rejection Cause</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="form-group"> <label for="rejectionCause">Select Cause</label> <select class="form-control" id="rejectionCause" required> <option value="">Select a cause...</option> {% for cause, label in rejection_causes %} <option value="{{ cause }}">{{ label }}</option> {% endfor %} </select> </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-primary" id="confirmCause">Confirm</button> </div> </div> </div> </div> </div> <script> const presentationId = '{{ presentation.id }}'; console.log("Presentation ID:", presentationId); function updatePresentation(id) { const bankRef = $('#bankReference').val(); if (!bankRef) { showError('Bank reference is required'); return; } const data = { bank_reference: bankRef, status: $('#presentationStatus').val() }; $.ajax({ url: `/testapp/presentations/${id}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, contentType: 'application/json', data: JSON.stringify(data), success: function(response) { location.reload(); }, error: function(xhr) { showError(xhr.responseJSON?.message || 'Update failed'); } }); } // Handle receipt status changes // Handle receipt status updates function updateReceiptStatuses(presentationId) { console.log('Updating receipt statuses for presentation:', presentationId); const receiptStatuses = {}; let hasChanges = false; let pendingUnpaidStatus = null; // Debug info for all receipt status selects $('.receipt-status').each(function() { const $select = $(this); console.log('Found receipt status select:', { receiptId: $select.data('receipt-id'), currentValue: $select.val(), disabled: $select.prop('disabled'), options: Array.from($select.find('option')).map(opt => ({ value: opt.value, text: opt.text, selected: opt.selected })) }); }); $('.receipt-status').each(function() { const $select = $(this); const receiptId = $select.data('receipt-id'); const status = $select.val(); console.log('Processing receipt:', { receiptId: receiptId, newStatus: status, previousStatus: $select.data('previous-status') }); if (status === 'unpaid') { pendingUnpaidStatus = { receiptId: receiptId, $select: $select }; console.log('Found pending unpaid status:', pendingUnpaidStatus); return false; // Break the loop } if (status) { receiptStatuses[receiptId] = status; hasChanges = true; console.log(`Adding status update for receipt ${receiptId}:`, status); } }); if (pendingUnpaidStatus) { console.log('Showing unpaid cause modal for:', pendingUnpaidStatus); $('#unpaidCauseModal').modal('show').data('pendingStatus', pendingUnpaidStatus); return; } if (!hasChanges) { console.log('No status changes detected'); showToast('No status changes to update', 'info'); return; } console.log('Submitting status updates:', receiptStatuses); submitStatusUpdates(presentationId, receiptStatuses); } function submitStatusUpdates(presentationId, receiptStatuses) { console.log('Submitting status updates:', { presentationId: presentationId, statuses: receiptStatuses, url: `/testapp/presentations/${presentationId}/edit/` }); $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value, 'Content-Type': 'application/json' }, data: JSON.stringify({ receipt_statuses: receiptStatuses }), success: function(response) { console.log('Status update response:', response); // Update UI to reflect changes Object.entries(receiptStatuses).forEach(([receiptId, status]) => { const $select = $(`.receipt-status[data-receipt-id="${receiptId}"]`); console.log(`Updating UI for receipt ${receiptId}:`, { status: status, select: $select.length ? 'found' : 'not found' }); if ($select.length) { $select.prop('disabled', true) .val(status); // Update the badge in the status column const $statusCell = $select.closest('tr').find('td:nth-last-child(2)'); const statusClass = status === 'paid' ? 'badge-success' : 'badge-danger'; $statusCell.html(`<span class="badge ${statusClass}">${status.toUpperCase()}</span>`); } }); showToast('Receipt statuses updated successfully', 'success'); // Reload after a short delay to ensure UI is updated setTimeout(() => { location.reload(); }, 1000); }, error: function(xhr) { console.error('Status update failed:', { status: xhr.status, response: xhr.responseText }); try { const error = JSON.parse(xhr.responseText); showToast(error.message || 'Failed to update statuses', 'error'); } catch (e) { showToast('Failed to update statuses', 'error'); } } }); } // Handle unpaid cause confirmation $('#confirmCause').click(function() { console.log('Confirming unpaid cause'); const cause = $('#rejectionCause').val(); console.log('Selected cause:', cause); if (!cause) { console.log('No cause selected'); showError('Please select a rejection cause'); return; } const pendingStatus = $('#unpaidCauseModal').data('pendingStatus'); console.log('Pending status data:', pendingStatus); if (!pendingStatus || !pendingStatus.receiptId) { console.error('Missing pending status data'); showError('Missing receipt information'); return; } const receiptStatuses = { [pendingStatus.receiptId]: { status: 'unpaid', cause: cause } }; console.log('Submitting unpaid status update:', receiptStatuses); submitStatusUpdates(presentationId, receiptStatuses); $('#unpaidCauseModal').modal('hide'); }); function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } function showError(message) { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-danger text-white"> <strong class="mr-auto">Error</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .html(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', function() { container.remove(); }); } </script>
```

# templates/presentation/presentation_list.html

```html
{% extends 'base.html' %} {% load presentation_filters %} {% block content %} {% csrf_token %} <div class="container-fluid"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2>Presentations</h2> <div class="btn-group"> <button class="btn btn-primary dropdown-toggle" data-toggle="dropdown"> <i class="fas fa-plus"></i> New Presentation </button> <div class="dropdown-menu dropdown-menu-right"> <a class="dropdown-item" href="#" onclick="startPresentation('check')"> <i class="fas fa-money-check"></i> Present Checks </a> <a class="dropdown-item" href="#" onclick="startPresentation('lcn')"> <i class="fas fa-file-invoice-dollar"></i> Present LCNs </a> </div> </div> </div> <!-- Filter Section --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-3"> <select class="form-control" id="typeFilter"> <option value="">All Types</option> <option value="COLLECTION">Collection</option> <option value="DISCOUNT">Discount</option> </select> </div> <div class="col-md-3"> <select class="form-control" id="statusFilter"> <option value="">All Status</option> <option value="pending">Pending</option> <option value="presented">Presented</option> <option value="paid">Paid</option> <option value="rejected">Rejected</option> </select> </div> <div class="col-md-3"> <select class="form-control" id="bankFilter"> <option value="">All Banks</option> {% for account in bank_accounts %} <option value="{{ account.id }}"> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> <div class="col-md-3"> <input type="text" class="form-control" id="searchPresentation" placeholder="Search by reference..."> </div> </div> </div> </div> <!-- Presentations Table --> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Type</th> <th>Bank Account</th> <th>Bank Reference</th> <th>Total Amount</th> <th>Receipt Count</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for presentation in presentations %} <tr> <td>{{ presentation.date|date:"Y-m-d" }}</td> <td>{{ presentation.get_presentation_type_display }}</td> <td>{{ presentation.bank_account.bank }} - {{ presentation.bank_account.account_number }}</td> <td>{{ presentation.bank_reference|default:"-" }}</td> <td class="text-right">{{ presentation.total_amount|floatformat:2 }}</td> <td class="text-center">{{ presentation.receipt_count }}</td> <td> <span class="badge badge-{{ presentation.status|status_badge }}"> {{ presentation.get_status_display }} </span> </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewPresentation('{{ presentation.id }}')"> <i class="fas fa-eye"></i> </button> <button class="btn btn-sm btn-primary" onclick="editPresentation('{{ presentation.id }}')" {% if presentation.status == 'paid' %}disabled{% endif %}> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger" onclick="deletePresentation('{{ presentation.id }}')" {% if presentation.status != 'pending' %}disabled{% endif %}> <i class="fas fa-trash"></i> </button> </div> </td> </tr> {% empty %} <tr> <td colspan="8" class="text-center">No presentations found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Create/Edit Presentation Modal --> <div class="modal fade" id="presentationModal" tabindex="-1"> <div class="modal-dialog modal-xl"> <div class="modal-content"> <div class="modal-header"> <h5 class="modal-title"> <span id="modalTitleText">Create Presentation</span> </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <form id="presentationForm"> <!-- Step indicator --> <div class="mb-4"> <div class="progress"> <div class="progress-bar" role="progressbar" style="width: 0%"></div> </div> <div class="d-flex justify-content-between mt-2"> <span class="step-indicator active">1. Basic Info</span> <span class="step-indicator">2. Select Receipts</span> <span class="step-indicator">3. Review</span> </div> </div> <!-- Step 1: Basic Info --> <div id="step1" class="step-content"> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Presentation Type</label> <select class="form-control" id="presentationType" required> <option value="COLLECTION">Collection</option> <option value="DISCOUNT">Discount</option> </select> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Bank Account</label> <select class="form-control" id="bankAccount" required> {% for account in bank_accounts %} <option value="{{ account.id }}"> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label>Date</label> <input type="date" class="form-control" id="presentationDate" value="{% now 'Y-m-d' %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label>Notes</label> <textarea class="form-control" id="presentationNotes" rows="1"></textarea> </div> </div> </div> </div> <!-- Discount Line Information (Only shown if type is DISCOUNT) --> <div class="discount-info d-none mb-3"> <h6 class="card-subtitle mb-3">Discount Line Information</h6> <div class="row"> <div class="col-md-3"> <div class="card text-white bg-info mb-3"> <div class="card-body"> <h5 class="card-title">Total Discount Line</h5> <p class="card-text"> <span id="totalDiscountLine">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-success mb-3"> <div class="card-body"> <h5 class="card-title">Used Amount</h5> <p class="card-text"> <span id="usedDiscountAmount">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-warning mb-3"> <div class="card-body"> <h5 class="card-title">Available Amount</h5> <p class="card-text"> <span id="availableDiscountAmount">0.00</span> MAD </p> </div> </div> </div> <div class="col-md-3"> <div class="card text-white bg-primary mb-3"> <div class="card-body"> <h5 class="card-title">Selected Amount</h5> <p class="card-text"> <span id="selectedDiscountAmount">0.00</span> MAD </p> </div> </div> </div> </div> <div class="alert alert-danger d-none" id="discountLineExceededAlert"> The selected amount exceeds the available discount line. </div> </div> <!-- Step 2: Receipt Selection --> <div id="step2" class="step-content d-none"> <div class="receipt-selection-container"> <!-- Receipts will be loaded here --> </div> </div> <!-- Step 3: Review --> <div id="step3" class="step-content d-none"> <div class="review-summary"> <!-- Summary will be populated dynamically --> </div> </div> </form> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="button" class="btn btn-info" id="prevStep" style="display: none"> <i class="fas fa-arrow-left"></i> Previous </button> <button type="button" class="btn btn-primary" id="nextStep"> Next <i class="fas fa-arrow-right"></i> </button> <button type="button" class="btn btn-success" id="savePresentation" style="display: none"> <i class="fas fa-save"></i> Create Presentation </button> </div> </div> </div> </div> <!-- View Presentation Modal --> <div class="modal fade" id="viewPresentationModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Content will be loaded dynamically --> </div> </div> </div> {% endblock %} {% block extra_js %} <script> function showError(error) { console.error(error); alert('An error occurred: ' + error); } function showSuccess(message) { console.log(message); alert('Succes!: ' + message); } const PresentationManager = { currentStep: 1, totalSteps: 3, receiptType: null, selectedReceipts: [], init() { this.bindEvents(); this.setupValidation(); }, discountInfo: { available: 0, total: 0, used: 0, selected: 0 }, async loadDiscountInfo(bankAccountId) { if (!bankAccountId) return; try { const response = await fetch(`/testapp/presentations/discount-info/${bankAccountId}/?type=${this.receiptType}`); const data = await response.json(); this.discountInfo = { available: parseFloat(data.available_amount), total: parseFloat(data.total_amount), used: parseFloat(data.used_amount), selected: 0 }; this.updateDiscountDisplay(); } catch (error) { console.error('Failed to load discount information:', error); } }, updateDiscountDisplay() { const discountCard = $('.discount-info'); const presentationType = $('#presentationType').val(); if (presentationType === 'DISCOUNT') { discountCard.removeClass('d-none'); $('#totalDiscountLine').text(this.discountInfo.total.toFixed(2)); $('#usedDiscountAmount').text(this.discountInfo.used.toFixed(2)); $('#availableDiscountAmount').text(this.discountInfo.available.toFixed(2)); $('#selectedDiscountAmount').text(this.discountInfo.selected.toFixed(2)); const exceededAlert = $('#discountLineExceededAlert'); if (this.discountInfo.selected > this.discountInfo.available) { exceededAlert.removeClass('d-none'); $('#nextStep, #savePresentation').prop('disabled', true); } else { exceededAlert.addClass('d-none'); this.validateCurrentStep(); } } else { discountCard.addClass('d-none'); } }, bindEvents() { $('#nextStep').on('click', () => this.nextStep()); $('#prevStep').on('click', () => this.previousStep()); $('#savePresentation').on('click', () => this.savePresentation()); }, setupValidation() { $('#presentationForm input[required], #presentationForm select[required]') .on('input change', () => this.validateCurrentStep()); $('#presentationType, #bankAccount').on('change', () => { if ($('#presentationType').val() === 'DISCOUNT') { this.loadDiscountInfo($('#bankAccount').val()); } else { $('.discount-info').addClass('d-none'); } }); }, startPresentation(type) { this.receiptType = type; this.currentStep = 1; this.selectedReceipts = []; // Update modal title $('#modalTitleText').text(`Create ${type.toUpperCase()} Presentation`); // Reset form $('#presentationForm')[0].reset(); // Show first step this.showStep(1); // Show modal $('#presentationModal').modal('show'); }, async loadAvailableReceipts() { try { const response = await $.get('/testapp/presentations/available-receipts/', { type: this.receiptType }); $('.receipt-selection-container').html(response.html); this.initializeReceiptSelection(); } catch (error) { showError('Failed to load available receipts'); } }, initializeReceiptSelection() { $('.receipt-checkbox').on('change', () => { this.updateSelectionSummary(); if ($('#presentationType').val() === 'DISCOUNT') { this.discountInfo.selected = Array.from($('.receipt-checkbox:checked')) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); this.updateDiscountDisplay(); } }); $('#selectAll').on('change', (e) => { $('.receipt-checkbox').prop('checked', e.target.checked); this.updateSelectionSummary(); if ($('#presentationType').val() === 'DISCOUNT') { this.discountInfo.selected = e.target.checked ? Array.from($('.receipt-checkbox')) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0) : 0; this.updateDiscountDisplay(); } }); }, updateSelectionSummary() { const selected = $('.receipt-checkbox:checked'); const count = selected.length; const total = Array.from(selected) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); $('#selectedCount').text(count); $('#selectedAmount').text(total.toFixed(2)); // Enable/disable next button based on selection $('#nextStep').prop('disabled', count === 0); }, validateCurrentStep() { let isValid = true; if (this.currentStep === 1) { // Check required fields in step 1 $('#step1 [required]').each(function() { if (!$(this).val()) { isValid = false; return false; // break } }); } else if (this.currentStep === 2) { // Check if at least one receipt is selected isValid = $('.receipt-checkbox:checked').length > 0; } $('#nextStep').prop('disabled', !isValid); return isValid; }, updateProgressBar() { const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100; $('.progress-bar').css('width', `${progress}%`); // Update step indicators $('.step-indicator').removeClass('active'); $(`.step-indicator:nth-child(${this.currentStep})`).addClass('active'); }, showStep(step) { $('.step-content').addClass('d-none'); $(`#step${step}`).removeClass('d-none'); // Update buttons $('#prevStep').toggle(step > 1); $('#nextStep').toggle(step < this.totalSteps); $('#savePresentation').toggle(step === this.totalSteps); // Load receipts if moving to step 2 if (step === 2) { this.loadAvailableReceipts(); } else if (step === 3) { this.showReviewStep(); } this.currentStep = step; this.updateProgressBar(); this.validateCurrentStep(); }, showReviewStep() { const selected = $('.receipt-checkbox:checked'); const count = selected.length; const total = Array.from(selected) .reduce((sum, cb) => sum + parseFloat($(cb).data('amount')), 0); const summary = ` <div class="card"> <div class="card-body"> <h6 class="card-subtitle mb-2 text-muted">Presentation Summary</h6> <dl class="row mb-0"> <dt class="col-sm-4">Type</dt> <dd class="col-sm-8">${$('#presentationType option:selected').text()}</dd> <dt class="col-sm-4">Bank Account</dt> <dd class="col-sm-8">${$('#bankAccount option:selected').text()}</dd> <dt class="col-sm-4">Date</dt> <dd class="col-sm-8">${$('#presentationDate').val()}</dd> <dt class="col-sm-4">Receipts</dt> <dd class="col-sm-8">${count} ${this.receiptType}(s)</dd> <dt class="col-sm-4">Total Amount</dt> <dd class="col-sm-8">${total.toFixed(2)} MAD</dd> </dl> </div> </div> `; $('.review-summary').html(summary); }, nextStep() { if (this.validateCurrentStep()) { this.showStep(this.currentStep + 1); } }, previousStep() { if (this.currentStep > 1) { this.showStep(this.currentStep - 1); } }, async savePresentation() { try { const data = { presentation_type: $('#presentationType').val(), date: $('#presentationDate').val(), bank_account: $('#bankAccount').val(), notes: $('#presentationNotes').val(), receipt_type: this.receiptType, receipt_ids: $('.receipt-checkbox:checked').map(function() { return $(this).val(); }).get() }; console.log('Sending data:', data); const response = await $.ajax({ url: '/testapp/presentations/create/', method: 'POST', contentType: 'application/json', data: JSON.stringify(data) }); if (response.status === 'success') { $('#presentationModal').modal('hide'); showSuccess('Presentation created successfully'); location.reload(); } else { showError(response.message); } } catch (error) { console.error('Creation error:', error); const errorMessage = error.responseJSON?.message || 'Failed to create presentation'; showError(errorMessage); } } }; async function viewPresentation(id) { try { const response = await $.get(`/testapp/presentations/${id}/`); $('#viewPresentationModal .modal-content').html(response); $('#viewPresentationModal').modal('show'); } catch (error) { showError('Failed to load presentation details'); } } async function editPresentation(id) { try { const data = { bank_reference: $('#bankReference').val(), status: $('#presentationStatus').val(), notes: $('#presentationNotes').val() // If you have this field }; console.log('Sending edit request:', { id: id, data: data, url: `/testapp/presentations/${id}/edit/` }); const response = await fetch(`/testapp/presentations/${id}/edit/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify(data) }); const responseData = await response.json(); console.log('Edit response:', responseData); if (!response.ok) { throw new Error(responseData.message || 'Failed to edit presentation'); } showSuccess('Presentation updated successfully'); $('#viewPresentationModal').modal('hide'); location.reload(); } catch (error) { console.error('Edit error:', error); showError(error.message || 'Failed to edit presentation'); } } async function deletePresentation(id) { console.log('Delete initiated for presentation:', id); try { if (!confirm('Are you sure you want to delete this presentation?')) { console.log('Delete cancelled by user'); return; } const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; console.log('CSRF token obtained:', csrfToken ? 'Yes' : 'No'); const response = await fetch(`/testapp/presentations/${id}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' } }); console.log('Delete response status:', response.status); const data = await response.json(); console.log('Delete response data:', data); if (response.ok) { showSuccess('Presentation deleted successfully'); location.reload(); } else { throw new Error(data.message || 'Failed to delete presentation'); } } catch (error) { console.error('Delete error:', error); showError(error.message || 'Failed to delete presentation'); } } // Initialize on document ready $(document).ready(function() { PresentationManager.init(); }); // Global function to start presentation creation function startPresentation(type) { PresentationManager.startPresentation(type); } // Handle receipt status updates $(document).on('click', '.update-receipt-status', function() { const $button = $(this); const receiptId = $button.data('receipt-id'); if (!confirm('This action cannot be undone. Continue?')) { return; } console.log('Updating receipt status:', receiptId); $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, contentType: 'application/json', data: JSON.stringify({ receipt_id: receiptId, receipt_status: 'paid' }), success: function(response) { console.log('Status updated:', response); $button.prop('disabled', true).text('Paid'); }, error: function(xhr) { console.error('Update failed:', xhr.responseText); showToast('Failed to update status', 'error'); } }); }); </script> {% endblock %}
```

```html
{% extends 'base.html' %} {% block title %}Profile{% endblock %} {% block content %} <h1>Profile Page</h1> <p>First Name: {{ user.first_name }}</p> <p>Last Name: {{ user.last_name }}</p> <p>Email: {{ user.email }}</p> {% endblock %}
```

# templates/receipt/receipt_form_modal.html

```html
<!-- Debug Info --> <div style="display:none"> Receipt type from context: {{ receipt_type }} Is transfer? {% if receipt_type == 'transfer' %}Yes{% else %}No{% endif %} </div> <!-- Modal Header --> <div class="modal-header"> <h5 class="modal-title"> {% if receipt_type == 'check' %} <i class="fas fa-money-check"></i> {% elif receipt_type == 'lcn' %} <i class="fas fa-file-invoice-dollar"></i> {% elif receipt_type == 'cash' %} <i class="fas fa-money-bill"></i> {% else %} <i class="fas fa-exchange-alt"></i> {% endif %} {{ title }} </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <!-- Modal Body --> <div class="modal-body"> <form id="receiptForm" method="post" action="{% if receipt %}{% url 'receipt-edit' receipt_type receipt.id %}{% else %}{% url 'receipt-create' receipt_type %}{% endif %}"> {% csrf_token %} <!-- Common Fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="client">Client</label> <input type="text" class="form-control" id="client" name="client_display" placeholder="Search for a client..." required value="{% if receipt %}{{ receipt.client.name }}{% endif %}"> <input type="hidden" id="client_id" name="client" value="{% if receipt %}{{ receipt.client.id }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="entity">Entity</label> <input type="text" class="form-control" id="entity" name="entity_display" placeholder="Search for an entity..." required value="{% if receipt %}{{ receipt.entity.name }}{% endif %}"> <input type="hidden" id="entity_id" name="entity" value="{% if receipt %}{{ receipt.entity.id }}{% endif %}" required> </div> </div> </div> <div class="row"> <div class="col-md-4"> <div class="form-group"> <label for="operation_date">Operation Date</label> <input type="date" class="form-control" id="operation_date" name="operation_date" value="{% if receipt %}{{ receipt.operation_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}" required> </div> </div> <div class="col-md-4"> <div class="form-group"> <label for="client_year">Year</label> <select class="form-control" id="client_year" name="client_year" required> {% for year in year_choices %} <option value="{{ year }}" {% if receipt and receipt.client_year == year or year == current_year %}selected{% endif %}>{{ year }}</option> {% endfor %} </select> </div> </div> <div class="col-md-4"> <div class="form-group"> <label for="client_month">Month</label> <select class="form-control" id="client_month" name="client_month" required> {% for month in month_choices %} <option value="{{ month.0 }}" {% if receipt and receipt.client_month == month.0 or month.0 == current_month %}selected{% endif %}>{{ month.1 }}</option> {% endfor %} </select> </div> </div> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="amount">Amount</label> <input type="number" class="form-control" id="amount" name="amount" value="{% if receipt %}{{ receipt.amount }}{% endif %}" step="0.01" min="0.01" required> </div> </div> </div> {% if receipt_type == 'check' %} <!-- Check-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="check_number">Check Number</label> <input type="text" class="form-control" id="check_number" name="check_number" value="{% if receipt %}{{ receipt.check_number }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="due_date">Due Date</label> <input type="date" class="form-control" id="due_date" name="due_date" value="{% if receipt %}{{ receipt.due_date|date:'Y-m-d' }}{% endif %}" required> </div> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="issuingBank">Issuing Bank</label> <input type="text" class="form-control" id="issuingBank" name="issuing_bank_display" placeholder="Select bank..." required value="{% if receipt %}{{ receipt.get_issuing_bank_display }}{% endif %}"> <input type="hidden" id="issuingBankCode" name="issuing_bank" value="{% if receipt %}{{ receipt.issuing_bank }}{% endif %}"> </div> </div> <div class="form-group"> <label>Compensate Unpaid Receipt</label> <input type="text" id="compensate-receipt-autocomplete" class="form-control" name="compensates"> <input type="hidden" id="compensate-receipt-id" name="compensates"> </div> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="branch">Branch</label> <input type="text" class="form-control" id="branch" name="branch" value="{% if receipt %}{{ receipt.branch }}{% endif %}"> </div> </div> </div> {% endif %} {% if receipt_type == 'lcn' %} <!-- LCN-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="lcn_number">LCN Number</label> <input type="text" class="form-control" id="lcn_number" name="lcn_number" value="{% if receipt %}{{ receipt.lcn_number }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="due_date">Due Date</label> <input type="date" class="form-control" id="due_date" name="due_date" value="{% if receipt %}{{ receipt.due_date|date:'Y-m-d' }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="issuingBank">Issuing Bank</label> <input type="text" class="form-control" id="issuingBank" name="issuing_bank_display" placeholder="Select bank..." required value="{% if receipt %}{{ receipt.get_issuing_bank_display }}{% endif %}"> <input type="hidden" id="issuingBankCode" name="issuing_bank" value="{% if receipt %}{{ receipt.issuing_bank }}{% endif %}"> </div> </div> <div class="form-group col-md-6"> <label>Compensate Unpaid Receipt</label> <input type="text" id="compensate-receipt-autocomplete" class="form-control" name="compensates"> <input type="hidden" id="compensate-receipt-id" name="compensates"> </div> </div> {% endif %} {% if receipt_type == 'cash' or receipt_type == 'transfer' %} <!-- Cash/Transfer-specific fields --> <div class="row"> <div class="col-md-12"> <div class="form-group"> <label for="credited_account">Credited Account</label> <select class="form-control" id="credited_account" name="credited_account" required> {% for account in bank_accounts %} <option value="{{ account.id }}" {% if receipt and receipt.credited_account.id == account.id %}selected{% endif %}> {{ account.bank }} - {{ account.account_number }} </option> {% endfor %} </select> </div> </div> </div> <div class="form-group"> <label>Compensate Unpaid Receipt</label> <input type="text" id="compensate-receipt-autocomplete" class="form-control" name="compensates"> <input type="hidden" id="compensate-receipt-id" name="compensates"> </div> </div> {% endif %} {% if receipt_type == 'transfer' %} <!-- Transfer-specific fields --> <div class="row"> <div class="col-md-6"> <div class="form-group"> <label for="transfer_reference">Transfer Reference</label> <input type="text" class="form-control" id="transfer_reference" name="transfer_reference" value="{% if receipt %}{{ receipt.transfer_reference }}{% endif %}" required> </div> </div> <div class="col-md-6"> <div class="form-group"> <label for="transfer_date">Transfer Date</label> <input type="date" class="form-control" id="transfer_date" name="transfer_date" value="{% if receipt %}{{ receipt.transfer_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}" required> </div> </div> </div> <div class="form-group"> <label>Compensate Unpaid Receipt</label> <input type="text" id="compensate-receipt-autocomplete" class="form-control" name="compensates"> <input type="hidden" id="compensate-receipt-id" name="compensates"> </div> </div> {% endif %} <div class="form-group"> <label for="notes">Notes</label> <textarea class="form-control" id="notes" name="notes" rows="2">{% if receipt %}{{ receipt.notes }}{% endif %}</textarea> </div> </form> </div> <!-- Modal Footer --> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button> <button type="submit" class="btn btn-primary" form="receiptForm">Save Receipt</button> </div> <!-- Initialize autocomplete --> <script> console.log('Form loaded for receipt type:', '{{ receipt_type }}'); $(document).ready(function() { // Initialize client autocomplete $("#client").autocomplete({ minLength: 0, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 0, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Bank selection using jQuery UI autocomplete const banksList = [ {% for code, name in bank_choices %} { label: '{{ name }}', value: '{{ code }}' }, {% endfor %} ]; $("#issuingBank").autocomplete({ source: banksList, minLength: 0, // Show all options even without typing select: function(event, ui) { $("#issuingBank").val(ui.item.label); $("#issuingBankCode").val(ui.item.value); return false; } }).focus(function() { // Show all options when field is focused $(this).autocomplete("search", ""); }); // Add dropdown indicator and click handler $("#issuingBank").after('<span class="bank-dropdown-toggle"><i class="fas fa-chevron-down"></i></span>'); $(".bank-dropdown-toggle").click(function() { $("#issuingBank").focus(); }); $("#compensate-receipt-autocomplete").autocomplete({ source: function(request, response) { console.log('Unpaid Receipt search term:', request.term); $.ajax({ url: "{% url 'unpaid-receipt-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Unpaid Receipt data received:', data); response($.map(data.results, function(item) { return { label: item.description, value: item.description, // Display full description id: item.id }; })); }, error: function(xhr, status, error) { console.error('Unpaid Receipt autocomplete error:', error); console.log('XHR response:', xhr.responseText); } }); }, minLength: 0, select: function(event, ui) { console.log('Unpaid Receipt selected:', ui.item); $("#compensate-receipt-id").val(ui.item.id); $("#compensate-receipt-autocomplete").val(ui.item.label); $("#compensation-details").html(` Selected Receipt: ${ui.item.label} `); }, change: function(event, ui) { console.log('Unpaid Receipt change event triggered'); if (!ui.item) { $("#compensate-receipt-id").val(''); $("#compensate-receipt-autocomplete").val(''); $("#compensation-details").empty(); } } }); // Initialize tooltips $('[data-toggle="tooltip"]').tooltip(); // Enhanced status badges with tooltips function updateStatusBadge($element, status, details) { const badge = $('<span>') .addClass(`badge badge-${status.toLowerCase()}`) .text(status); if (details) { badge.attr('data-toggle', 'tooltip') .attr('data-html', 'true') .attr('title', details); } $element.html(badge); badge.tooltip(); } // Add bulk action support let selectedReceipts = new Set(); // Add checkboxes for bulk actions $('.receipt-table').find('tbody tr').each(function() { const $tr = $(this); const receiptId = $tr.data('receipt-id'); const $checkbox = $('<input>', { type: 'checkbox', class: 'receipt-checkbox', 'data-receipt-id': receiptId }); $tr.prepend($('<td>').append($checkbox)); }); // Bulk action handlers $('.receipt-checkbox').on('change', function() { const receiptId = $(this).data('receipt-id'); if (this.checked) { selectedReceipts.add(receiptId); } else { selectedReceipts.delete(receiptId); } updateBulkActionButtons(); }); function updateBulkActionButtons() { const hasSelected = selectedReceipts.size > 0; $('.bulk-action-btn').prop('disabled', !hasSelected); } // Add number formatting function formatCurrency(amount) { return new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(amount); } // Update all amount displays $('.amount-display').each(function() { const amount = $(this).data('amount'); $(this).text(formatCurrency(amount)); }); }); </script> <style> .bank-dropdown-toggle { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); cursor: pointer; } .ui-autocomplete { max-height: 200px; overflow-y: auto; overflow-x: hidden; z-index: 9999; /* Scrollbar styles */ scrollbar-width: thin; scrollbar-color: #0b4d71 #f1f1f1; -webkit-overflow-scrolling: touch; -ms-overflow-style: -ms-autohiding-scrollbar; } .ui-autocomplete::-webkit-scrollbar { width: 6px; } .ui-autocomplete::-webkit-scrollbar-track { background: #f1f1f1; } .ui-autocomplete::-webkit-scrollbar-thumb { background: #888; } .ui-autocomplete::-webkit-scrollbar-thumb:hover { background: #555; } </style>
```

# templates/receipt/receipt_list.html

```html
{% extends 'base.html' %} {% load presentation_filters %} <!-- Debug info --> {% comment %} Available filters: {{ presentation_filters }} {% endcomment %} {% block content %} <div class="container-fluid px-4"> <!-- Header Section --> <div class="d-flex justify-content-between align-items-center mb-4"> <h2 class="mb-0"> <i class="fas fa-receipt text-primary me-2"></i> Receipts Management </h2> <div class="btn-group"> <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"> <i class="fas fa-plus-circle"></i> New Receipt </button> <div class="dropdown-menu"> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="check"> <i class="fas fa-money-check"></i> Check </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="lcn"> <i class="fas fa-file-invoice-dollar"></i> LCN </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="cash"> <i class="fas fa-money-bill"></i> Cash </a> <a class="dropdown-item" href="#" data-toggle="modal" data-target="#receiptModal" data-type="transfer"> <i class="fas fa-exchange-alt"></i> Transfer </a> </div> </div> </div> <!-- Tabs Navigation --> <ul class="nav nav-tabs" id="receiptTabs" role="tablist"> <li class="nav-item"> <a class="nav-link active" id="checks-tab" data-toggle="tab" href="#checks" role="tab"> <i class="fas fa-money-check"></i> Checks </a> </li> <li class="nav-item"> <a class="nav-link" id="lcns-tab" data-toggle="tab" href="#lcns" role="tab"> <i class="fas fa-file-invoice-dollar"></i> LCNs </a> </li> <li class="nav-item"> <a class="nav-link" id="cash-tab" data-toggle="tab" href="#cash" role="tab"> <i class="fas fa-money-bill"></i> Cash </a> </li> <li class="nav-item"> <a class="nav-link" id="transfers-tab" data-toggle="tab" href="#transfers" role="tab"> <i class="fas fa-exchange-alt"></i> Transfers </a> </li> </ul> <!-- Tab Content --> <div class="tab-content mt-4" id="receiptTabsContent"> <!-- Checks Tab Content --> <div class="tab-pane fade show active" id="checks" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>Check Number</th> <th>Issuing Bank</th> <th>Due Date</th> <th>Amount</th> <th>Bank Issued To</th> <th>Presentation</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for check in receipts.checks %} <tr class="status-{{ check.status|lower }}"> <td>{{ check.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ check.entity.name }}</strong><br> <small class="text-muted">{{ check.entity.ice_code }}</small> </td> <td> <small>{{ check.client.name }}</small> </td> <td>{{ check.check_number }}</td> <td>{{ check.get_issuing_bank_display }}</td> <td>{{ check.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ check.amount|floatformat:2 }}</td> <!-- Bank Issued To column --> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=check.check_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ check.status|status_badge }}"> {{ check.get_status_display }} </span> {% if check.status == 'UNPAID' and check.rejection_cause %} <br><small class="text-danger">{{ check.get_rejection_cause_display }}</small> {% with last_pres=check.check_presentations.last %} {% if last_pres %} <br><small class="text-muted">Represented on {{ last_pres.presentation.date|date:"Y-m-d" }}</small> {% endif %} {% endwith %} {% endif %} {% if check.compensation_info %} <br><small class="text-muted">{{ check.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('check', '{{ check.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=check.check_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="check" data-action="edit" data-id="{{ check.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="check" data-id="{{ check.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No checks found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- LCNs Tab Content --> <div class="tab-pane fade" id="lcns" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Entity</th> <th>Client</th> <th>LCN Number</th> <th>Issuing Bank</th> <th>Due Date</th> <th>Amount</th> <th>Bank Issued To</th> <th>Presentation</th> <th>Status</th> <th>Actions</th> </tr> </thead> <tbody> {% for lcn in receipts.lcns %} <tr class="status-{{ lcn.status|lower }}"> <td>{{ lcn.operation_date|date:"Y-m-d" }}</td> <td> <strong>{{ lcn.entity.name }}</strong><br> <small class="text-muted">{{ lcn.entity.ice_code }}</small> </td> <td> <small>{{ lcn.client.name }}</small> </td> <td>{{ lcn.lcn_number }}</td> <td>{{ lcn.get_issuing_bank_display }}</td> <td>{{ lcn.due_date|date:"Y-m-d" }}</td> <td class="text-right">{{ lcn.amount|floatformat:2 }}</td> <!-- Bank Issued To column --> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_account.bank }} - {{ pres.presentation.bank_account.account_number }} {% else %} - {% endif %} {% endwith %} </td> <td> {% with pres=lcn.lcn_presentations.first %} {% if pres %} {{ pres.presentation.bank_reference }} at {{ pres.presentation.date|date:"d/m/Y" }}<br> <span class="badge badge-{{ pres.presentation.status|status_badge }}"> {{ pres.presentation.get_status_display }} </span> {% else %} - {% endif %} {% endwith %} </td> <td> <span class="badge badge-{{ lcn.status|status_badge }}"> {{ lcn.get_status_display }} </span> {% if lcn.status == 'UNPAID' and lcn.rejection_cause %} <br><small class="text-danger">{{ lcn.get_rejection_cause_display }}</small> {% endif %} {% if lcn.compensation_info %} <br><small class="text-muted">{{ lcn.compensation_info }}</small> {% endif %} </td> <td> <div class="btn-group"> <button class="btn btn-sm btn-info" onclick="viewReceiptTimeline('lcn', '{{ lcn.id }}')"> <i class="fas fa-history"></i> </button> {% with pres=lcn.lcn_presentations.first %} {% if not pres %} <button class="btn btn-sm btn-primary" data-toggle="modal" data-target="#receiptModal" data-type="lcn" data-action="edit" data-id="{{ lcn.id }}"> <i class="fas fa-edit"></i> </button> <button class="btn btn-sm btn-danger delete-receipt" data-type="lcn" data-id="{{ lcn.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} {% endwith %} </div> </td> </tr> {% empty %} <tr> <td colspan="11" class="text-center">No LCNs found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Cash Tab --> <div class="tab-pane fade" id="cash" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Reference</th> <th>Credited Account</th> <th>Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for cash in receipts.cash %} <tr> <td>{{ cash.operation_date|date:"Y-m-d" }}</td> <td>{{ cash.client.name }}</td> <td>{{ cash.reference_number }}</td> <td>{{ cash.credited_account.bank }} - {{ cash.credited_account.account_number }}</td> <td class="text-right">{{ cash.amount|floatformat:2 }}</td> <td> <div class="btn-group"> {% if cash.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="cash" data-action="edit" data-id="{{ cash.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if cash.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="cash" data-id="{{ cash.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </div> </td> </tr> {% empty %} <tr> <td colspan="6" class="text-center">No cash receipts found</td> </tr> {% endfor %} </tbody> </table> </div> </div> <!-- Transfers Tab --> <div class="tab-pane fade" id="transfers" role="tabpanel"> <div class="table-responsive"> <table class="table table-hover"> <thead> <tr> <th>Date</th> <th>Client</th> <th>Transfer Reference</th> <th>Transfer Date</th> <th>Credited Account</th> <th>Amount</th> <th>Actions</th> </tr> </thead> <tbody> {% for transfer in receipts.transfers %} <tr> <td>{{ transfer.operation_date|date:"Y-m-d" }}</td> <td>{{ transfer.client.name }}</td> <td>{{ transfer.transfer_reference }}</td> <td>{{ transfer.transfer_date|date:"Y-m-d" }}</td> <td>{{ transfer.credited_account.bank }} - {{ transfer.credited_account.account_number }}</td> <td class="text-right">{{ transfer.amount|floatformat:2 }}</td> <td> <div class="btn-group"> {% if transfer.can_edit %} <button class="btn btn-sm btn-info" data-toggle="modal" data-target="#receiptModal" data-type="transfer" data-action="edit" data-id="{{ transfer.id }}"> <i class="fas fa-edit"></i> </button> {% endif %} {% if transfer.can_delete %} <button class="btn btn-sm btn-danger delete-receipt" data-type="transfer" data-id="{{ transfer.id }}"> <i class="fas fa-trash"></i> </button> {% endif %} </div> </td> </tr> {% empty %} <tr> <td colspan="7" class="text-center">No transfers found</td> </tr> {% endfor %} </tbody> </table> </div> </div> </div> </div> </div> <!-- Receipt Modal --> <div class="modal fade" id="receiptModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Modal content will be loaded dynamically --> </div> </div> </div> <!-- Timeline Modal --> <div class="modal fade" id="timelineModal" tabindex="-1"> <div class="modal-dialog modal-lg"> <div class="modal-content"> <!-- Content will be loaded dynamically --> </div> </div> </div> <style> /* Status Badge Colors */ .badge-portfolio { background-color: #6c757d; } .badge-presented_collection, .badge-presented_discount { background-color: #17a2b8; } .badge-paid { background-color: #28a745; } .badge-unpaid { background-color: #dc3545; } .badge-compensated { background-color: #fd7e14; } /* Orange color for compensated */ /* Row Status Highlighting */ tr.status-paid { background-color: rgba(40, 167, 69, 0.1); } /* Light green */ tr.status-unpaid { background-color: rgba(220, 53, 69, 0.1); } /* Light red */ tr.status-compensated { background-color: rgba(253, 126, 20, 0.1); } /* Light orange */ /* Maintain hover effect with status background */ .table-hover tbody tr:hover { background-color: rgba(0, 0, 0, 0.075) !important; } </style> <script> console.log("Extra JS loaded"); $(document).ready(function() { $('#receiptModal').on('show.bs.modal', function(e) { const button = $(e.relatedTarget); const type = button.data('type'); const action = button.data('action'); const id = button.data('id'); let url = ''; if (action === 'edit') { url += `edit/${type}/${id}/`; } else { url += `create/${type}/`; } // Load modal content $.get(url, function(data) { $('#receiptModal .modal-content').html(data); initializeForm(); if (action === 'edit') { // Set form action URL for edit $('#receiptForm').attr('action', url); // Initialize Select2 with pre-selected values if (data.client) { const clientOption = new Option(data.client.text, data.client.id, true, true); $('#client').append(clientOption).trigger('change'); } if (data.entity) { const entityOption = new Option(data.entity.text, data.entity.id, true, true); $('#entity').append(entityOption).trigger('change'); } } }); }); // Handle form submission for both create and edit $(document).on('submit', '#receiptForm', function(e) { e.preventDefault(); const form = $(this); // Create FormData object and append transfer fields manually let formData = new FormData(form[0]); if ($('#transfer_reference').length) { formData.append('transfer_reference', $('#transfer_reference').val()); formData.append('transfer_date', $('#transfer_date').val()); } // Convert FormData to URLSearchParams for jQuery const data = new URLSearchParams(formData).toString(); $.ajax({ url: form.attr('action'), type: 'POST', data: data, success: function(response) { if (response.status === 'success') { $('#receiptModal').modal('hide'); showToast(response.message, 'success'); location.reload(); } else { showFormErrors(form, response.errors); } }, error: function(xhr) { try { const errors = JSON.parse(xhr.responseText); showFormErrors(form, errors); } catch (e) { showToast('An error occurred while saving the receipt.', 'error'); } } }); }); function showFormErrors(form, errors) { // Clear previous errors form.find('.is-invalid').removeClass('is-invalid'); form.find('.invalid-feedback').remove(); // Show new errors Object.keys(errors).forEach(field => { const input = form.find(`[name="${field}"]`); const error = errors[field].join(' '); input.addClass('is-invalid'); input.after(`<div class="invalid-feedback">${error}</div>`); }); } function showToast(message, type = 'success') { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-${type} text-white"> <strong class="mr-auto">Notification</strong> <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast"> <span aria-hidden="true">&times;</span> </button> </div> <div class="toast-body">${message}</div> </div> `; const toastContainer = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>'); toastContainer.html(toast); $('body').append(toastContainer); $('.toast').toast('show'); // Remove toast after it's hidden $('.toast').on('hidden.bs.toast', function() { $(this).closest('.toast-container').remove(); }); } }); // Initialize form elements after modal load function initializeForm() { console.log('Initializing form with autocomplete...'); console.log('Client input exists:', $('#client').length); console.log('Entity input exists:', $('#entity').length); // Initialize client autocomplete $("#client").autocomplete({ minLength: 0, source: function(request, response) { console.log('Client search term:', request.term); $.ajax({ url: "{% url 'client-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Client data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Client autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Client selected:', ui.item); $("#client").val(ui.item.label); $("#client_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Client input focused'); }); // Initialize entity autocomplete $("#entity").autocomplete({ minLength: 0, source: function(request, response) { console.log('Entity search term:', request.term); $.ajax({ url: "{% url 'entity-autocomplete' %}", dataType: "json", data: { term: request.term }, success: function(data) { console.log('Entity data received:', data); response($.map(data.results, function(item) { return { label: item.text, value: item.id }; })); }, error: function(xhr, status, error) { console.error('Entity autocomplete error:', error); } }); }, select: function(event, ui) { console.log('Entity selected:', ui.item); $("#entity").val(ui.item.label); $("#entity_id").val(ui.item.value); return false; } }).on('focus', function() { console.log('Entity input focused'); }); // Add some basic styling to autocomplete dropdown $(".ui-autocomplete").addClass("dropdown-menu").css({ 'max-height': '200px', 'overflow-y': 'auto', 'overflow-x': 'hidden', 'z-index': '9999' }); } function initializeBankAutocomplete() { const banksList = [ {% for code, name in bank_choices %} { label: '{{ name }}', value: '{{ code }}' }, {% endfor %} ]; $("#issuingBank").autocomplete({ source: banksList, minLength: 0, select: function(event, ui) { $("#issuingBank").val(ui.item.label); $("#issuingBankCode").val(ui.item.value); return false; } }).focus(function() { $(this).autocomplete("search", ""); }); // Add dropdown indicator if (!$("#issuingBank").next('.bank-dropdown-toggle').length) { $("#issuingBank").after('<span class="bank-dropdown-toggle"><i class="fas fa-chevron-down"></i></span>'); $(".bank-dropdown-toggle").click(function() { $("#issuingBank").focus(); }); } } // Modify the modal show event handler $('#receiptModal').on('show.bs.modal', function(e) { const button = $(e.relatedTarget); const type = button.data('type'); const action = button.data('action'); const id = button.data('id'); let url = ''; if (action === 'edit') { url = `edit/${type}/${id}/`; } else { url = `create/${type}/`; } $.get(url, function(data) { $('#receiptModal .modal-content').html(data); initializeForm(); initializeBankAutocomplete(); // Add this line }); }); // Handle delete $('.delete-receipt').click(function() { if (confirm('Are you sure you want to delete this receipt?')) { const type = $(this).data('type'); const id = $(this).data('id'); $.ajax({ url: `/testapp/receipts/delete/${type}/${id}/`, type: 'POST', headers: { 'X-CSRFToken': '{{ csrf_token }}' }, success: function() { location.reload(); }, error: function() { alert('Error deleting receipt'); } }); } }); // Keyboard shortcuts $(document).keydown(function(e) { // Only trigger if no modal is open and no input is focused if ($('.modal:visible').length === 0 && !$(document.activeElement).is('input, textarea, select')) { let receiptType = null; if (e.altKey) { switch(e.key.toLowerCase()) { case 'c': // Alt + C for Check receiptType = 'check'; break; case 'l': // Alt + L for LCN receiptType = 'lcn'; break; case 'e': // Alt + M for Cash (Money) receiptType = 'cash'; break; case 'v': // Alt + T for Transfer receiptType = 'transfer'; break; } if (receiptType) { e.preventDefault(); const url = "{% url 'receipt-create' 'TYPE' %}".replace('TYPE', receiptType); const modal = $('#receiptModal'); modal.modal('show'); modal.find('.modal-content').load(url, function() { setTimeout(function() { initializeForm(); }, 100); }); } } } }); // Handle presentation status update function updatePresentation(id) { const bankRef = $('#bankReference').val(); if (!bankRef) { showError('Bank reference is required'); return; } $.ajax({ url: `/testapp/presentations/${id}/edit/`, method: 'POST', contentType: 'application/json', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, data: JSON.stringify({ bank_reference: bankRef, status: $('#presentationStatus').val() }), success: () => location.reload(), error: xhr => showError(xhr.responseJSON?.message || 'Update failed') }); } // Handle receipt status update $(document).on('change', '.receipt-status', function() { const $select = $(this); const receiptId = $select.data('receipt-id'); const newStatus = $select.val(); if (!confirm('This status change is irreversible. Continue?')) { $select.val($select.find('option').not(':selected').val()); return; } $.ajax({ url: `/testapp/presentations/${presentationId}/edit/`, method: 'POST', contentType: 'application/json', headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, data: JSON.stringify({ receipt_id: receiptId, receipt_status: newStatus }), success: () => { $select.prop('disabled', true); location.reload(); }, error: xhr => { showError(xhr.responseJSON?.message || 'Status update failed'); $select.val($select.find('option').not(':selected').val()); } }); }); function viewReceiptTimeline(receiptType, receiptId) { console.log(`Loading timeline for ${receiptType} ${receiptId}`); // Show loading state in modal $('#timelineModal').modal('show'); $('#timelineModal .modal-content').html(` <div class="modal-body text-center"> <div class="spinner-border text-primary" role="status"> <span class="sr-only">Loading...</span> </div> <p class="mt-2">Loading timeline...</p> </div> `); // Load timeline content $.ajax({ url: `/testapp/receipts/${receiptType}/${receiptId}/timeline/`, method: 'GET', success: function(response) { $('#timelineModal .modal-content').html(response); // Initialize any tooltips or popovers $('#timelineModal [data-toggle="tooltip"]').tooltip(); $('#timelineModal [data-toggle="popover"]').popover(); // Add animation classes to timeline items $('.timeline-item').each(function(index) { $(this) .addClass('animate__animated animate__fadeInLeft') .css('animation-delay', `${index * 0.1}s`); }); }, error: function(xhr) { let errorMessage = 'Failed to load timeline'; try { const response = JSON.parse(xhr.responseText); errorMessage = response.message || errorMessage; } catch(e) {} $('#timelineModal .modal-content').html(` <div class="modal-header"> <h5 class="modal-title">Error</h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <div class="alert alert-danger"> ${errorMessage} </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> </div> `); } }); } // Optional: Add helper function for formatting dates in timeline function formatTimelineDate(dateString) { const date = new Date(dateString); return new Intl.DateTimeFormat('fr-MA', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date); } // Add modal cleanup on hide $('#timelineModal').on('hidden.bs.modal', function() { $(this).find('.modal-content').html(''); }); // Optional: Add keyboard shortcut to close modal $(document).keydown(function(e) { if (e.key === 'Escape' && $('#timelineModal').hasClass('show')) { $('#timelineModal').modal('hide'); } }); function showError(message) { const toast = ` <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000"> <div class="toast-header bg-danger text-white"> <strong class="mr-auto">Error</strong> <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button> </div> <div class="toast-body">${message}</div> </div> `; const container = $('<div class="toast-container position-fixed top-0 right-0 p-3"></div>') .append(toast) .appendTo('body'); $('.toast').toast('show').on('hidden.bs.toast', () => container.remove()); } // Add tooltip hints for shortcuts $('[data-toggle="modal"][data-target="#receiptModal"]').each(function() { const type = $(this).data('type'); let shortcut = ''; switch(type) { case 'check': shortcut = 'Alt+C'; break; case 'lcn': shortcut = 'Alt+L'; break; case 'cash': shortcut = 'Alt+M'; break; case 'transfer': shortcut = 'Alt+T'; break; } if (shortcut) { $(this).attr('title', `${$(this).text().trim()} (${shortcut})`); } }); </script> {% endblock %}
```

# templates/receipt/receipt_timeline_modal.html

```html
<!-- templates/receipt/receipt_timeline_modal.html --> <div class="modal-header"> <h5 class="modal-title"> {% if receipt.check_number %} <i class="fas fa-money-check me-2"></i>Check #{{ receipt.check_number }} {% else %} <i class="fas fa-file-invoice-dollar me-2"></i>LCN #{{ receipt.lcn_number }} {% endif %} History </h5> <button type="button" class="close" data-dismiss="modal">&times;</button> </div> <div class="modal-body"> <!-- Receipt Summary --> <div class="card mb-4"> <div class="card-body"> <div class="row"> <div class="col-md-6"> <p><strong>Entity:</strong> {{ receipt.entity.name }}</p> <p><strong>Client:</strong> {{ receipt.client.name }}</p> <p><strong>Amount:</strong> {{ receipt.amount|floatformat:2 }}</p> </div> <div class="col-md-6"> <p><strong>Status:</strong> <span class="badge badge-{{ receipt.status|lower }}"> {{ receipt.get_status_display }} </span> </p> <p><strong>Created:</strong> {{ receipt.created_at|date:"d/m/Y H:i" }}</p> <p><strong>Due Date:</strong> {{ receipt.due_date|date:"d/m/Y" }}</p> </div> </div> </div> </div> <!-- Timeline --> <div class="timeline"> {% for event in history %} <div class="timeline-item"> <div class="timeline-marker {% if event.action == 'status_changed' %}bg-primary {% elif event.action == 'presented' %}bg-info {% elif event.action == 'compensated' %}bg-warning {% elif event.action == 'compensation_paid' %}bg-success {% else %}bg-secondary{% endif %}"> </div> <div class="timeline-content"> <div class="d-flex justify-content-between"> <h6 class="mb-0">{{ event.get_action_display }}</h6> <small class="text-muted">{{ event.timestamp|date:"d/m/Y H:i" }}</small> </div> <p class="mb-0">{{ event.notes }}</p> {% if event.action == 'status_changed' %} <small class="text-muted"> Changed from <span class="badge badge-{{ event.old_value.status|lower }}"> {{ event.old_value.status }} </span> to <span class="badge badge-{{ event.new_value.status|lower }}"> {{ event.new_value.status }} </span> </small> {% endif %} {% if event.user %} <small class="text-muted d-block">by {{ event.user.get_full_name|default:event.user.username }}</small> {% endif %} </div> </div> {% empty %} <p class="text-center text-muted">No history available</p> {% endfor %} </div> </div> <div class="modal-footer"> <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> </div> <style> .timeline { position: relative; padding-left: 3rem; margin-bottom: 3rem; } .timeline::before { content: ''; position: absolute; left: 11px; top: 0; height: 100%; width: 2px; background-color: #e9ecef; } .timeline-item { position: relative; margin-bottom: 2rem; } .timeline-marker { position: absolute; left: -3rem; width: 24px; height: 24px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 2px #e9ecef; } .timeline-content { background: #f8f9fa; border-radius: 0.3rem; padding: 1rem; position: relative; } .timeline-content::before { content: ''; position: absolute; left: -0.5rem; top: 0.75rem; width: 0.5rem; height: 0.5rem; background: inherit; transform: rotate(45deg); } /* Status Badge Colors */ .badge-portfolio { background-color: #6c757d; color: white; } .badge-presented { background-color: #17a2b8; color: white; } .badge-presented_discount { background-color: #e437d3; color: white; } .badge-paid { background-color: #28a745; color: white; } .badge-discounted { background-color: #1032dc; color: white; } .badge-unpaid { background-color: #dc3545; color: white; } .badge-compensated { background-color: #fd7e14; color: white; } </style>
```

# templatetags/accounting_filters.py

```py
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def sum_debit(entries):
    return sum(entry['debit'] or 0 for entry in entries)

@register.filter
def sum_credit(entries):
    return sum(entry['credit'] or 0 for entry in entries)

@register.filter
def space_thousands(value):
    """
    Formats a number with spaces as thousand separators and 2 decimal places
    Example: 1234567.89 becomes 1 234 567.89
    """
    if value is None:
        return ''
    
    # Format to 2 decimal places first
    formatted = floatformat(value, 2)
    
    # Split the number into integer and decimal parts
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
    else:
        integer_part, decimal_part = formatted, '00'

    # Add space thousand separators to integer part
    int_with_spaces = ''
    for i, digit in enumerate(reversed(integer_part)):
        if i and i % 3 == 0:
            int_with_spaces = ' ' + int_with_spaces
        int_with_spaces = digit + int_with_spaces

    return f'{int_with_spaces}.{decimal_part}'
```

# templatetags/check_tags.py

```py
from django import template

register = template.Library()

@register.filter
def status_badge(status):
    return {
        'pending': 'secondary',
        'delivered': 'warning',
        'paid': 'success',
        'cancelled': 'danger',
        'unpaid': 'danger'
    }.get(status, 'secondary')
```

# templatetags/custom_filters.py

```py
from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def status_badge(status):
    """
    Convert status to a bootstrap badge class
    """
    status_map = {
        'pending': 'badge-secondary',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'in_progress': 'badge-warning',
        'completed': 'badge-primary'
    }
    return status_map.get(status, 'badge-light')

```

# templatetags/presentation_filters.py

```py
from django import template
import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.filter
def status_badge(status):
    """Returns appropriate badge class for presentation status"""
    # Convert status to lowercase for consistent mapping
    original_status = str(status)
    status = original_status.lower()
    
    logger.debug(f"status_badge filter called with original status: {original_status}")
    
    result = {
        'pending': 'secondary',
        'presented': 'info',
        'paid': 'success',
        'rejected': 'danger',
        'unpaid': 'danger',
        'portfolio': 'primary',
        'presented_collection': 'info',
        'presented_discount': 'info',
        'discounted': 'success',
        
        # Explicitly map uppercase statuses
        'UNPAID': 'danger',
        'PAID': 'success',
        'REJECTED': 'danger',
        'PRESENTED_COLLECTION': 'info',
        'PRESENTED_DISCOUNT': 'info',
        'DISCOUNTED': 'success',
    }.get(original_status, status)  # Try original status first, then fallback to lowercase
    
    logger.debug(f"Returning badge class: {result}")
    return result
```

# urls.py

```py
from django.urls import path, include
from . import views

from .views_bank import (
    BankAccountListView, BankAccountCreateView, 
    BankAccountDeactivateView, BankAccountFilterView, BankAccountUpdateView, BankAccountDeleteView,
    bank_account_autocomplete
)

from .views_receipts import (
    ReceiptListView, ReceiptCreateView, ReceiptUpdateView, ReceiptDeleteView, ReceiptDetailView, client_autocomplete,
    entity_autocomplete, unpaid_receipt_autocomplete, ReceiptStatusUpdateView, UnpaidReceiptsView, ReceiptTimelineView,)

from .views_client import (
    client_management,
    list_clients,
    create_client,
    update_client,
    delete_client,
    validate_field,
    ClientSaleListView,
    create_sale,
    ClientCardView
)
from .views_entity import (
    list_entities, create_entity, update_entity, delete_entity
)
from .views_presentation import (
    PresentationListView, PresentationCreateView, PresentationUpdateView, PresentationDeleteView,
    PresentationDetailView, AvailableReceiptsView, DiscountInfoView
)


urlpatterns = [
    path('', views.home, name='home'),  # Home view
    path('profile/', views.profile, name='profile'),  # Profile view

    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/create/', BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<uuid:pk>/edit/', BankAccountUpdateView.as_view(), name='bank-account-edit'),
    path('bank-accounts/<uuid:pk>/delete/', BankAccountDeleteView.as_view(), name='bank-account-delete'),
    path('bank-accounts/<uuid:pk>/deactivate/', 
         BankAccountDeactivateView.as_view(), name='bank-account-deactivate'),
    path('bank-accounts/filter/', 
         BankAccountFilterView.as_view(), name='bank-account-filter'),
    path('bank-accounts/', bank_account_autocomplete, name='bank_account_autocomplete'),

    # Client Management Page
    path('client-management/', client_management, name='client_management'),
    
    # Client API endpoints
    path('api/clients/', list_clients, name='list_clients'),
    path('api/clients/create/', create_client, name='create_client'),
    path('api/clients/<uuid:client_id>/update/', update_client, name='update_client'),
    path('api/clients/<uuid:client_id>/delete/', delete_client, name='delete_client'),
    path('api/validate/<str:field>/<str:value>/', validate_field, name='validate-field'),
    
    # Entity API endpoints
    path('api/entities/', list_entities, name='list_entities'),
    path('api/entities/create/', create_entity, name='create_entity'),
    path('api/entities/<uuid:entity_id>/update/', update_entity, name='update_entity'),
    path('api/entities/<uuid:entity_id>/delete/', delete_entity, name='delete_entity'),

    path('client/sales/', ClientSaleListView.as_view(), name='sale-list'),
    path('client/sales/create/', create_sale, name='create-sale'),
    path('clients/<uuid:pk>/card/', ClientCardView.as_view(), name='client-card'),
    path('client/autocomplete/', client_autocomplete, name='client-autocomplete'),

    # Receipt URLs
    path('receipts/', ReceiptListView.as_view(), name='receipt-list'),
    path('receipts/create/<str:receipt_type>/', ReceiptCreateView.as_view(), name='receipt-create'),
    path('receipts/edit/<str:receipt_type>/<uuid:pk>/', ReceiptUpdateView.as_view(), name='receipt-edit'),
    path('receipts/delete/<str:receipt_type>/<uuid:pk>/', ReceiptDeleteView.as_view(), name='receipt-delete'),
    path('receipts/details/<str:receipt_type>/<uuid:pk>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipts/unpaid/', UnpaidReceiptsView.as_view(), name='unpaid-receipts'),
    path('receipts/<str:receipt_type>/<uuid:pk>/status/', ReceiptStatusUpdateView.as_view(), 
        name='receipt-status-update'),
    path('receipts/<str:receipt_type>/<uuid:pk>/timeline/', 
        ReceiptTimelineView.as_view(), 
         name='receipt-timeline'),

    # Autocomplete endpoints for form fields
    path('receipts/client/autocomplete', client_autocomplete, name='client-autocomplete'),
    path('receipts/entity/autocomplete', entity_autocomplete, name='entity-autocomplete'),
    path('receipts/unpaid/autocomplete', unpaid_receipt_autocomplete, name='unpaid-receipt-autocomplete'),

    # Presentation URLs
    path('presentations/', PresentationListView.as_view(), name='presentation-list'),
    path('presentations/create/', PresentationCreateView.as_view(), name='presentation-create'),
    path('presentations/<uuid:pk>/', PresentationDetailView.as_view(), name='presentation-detail'),
    path('presentations/<uuid:pk>/edit/', PresentationUpdateView.as_view(), name='presentation-edit'),
    path('presentations/<uuid:pk>/delete/', PresentationDeleteView.as_view(), name='presentation-delete'),
    path('presentations/available-receipts/', AvailableReceiptsView.as_view(), name='available-receipts'),
    path('presentations/discount-info/<uuid:bank_account_id>/', 
        DiscountInfoView.as_view(), name='presentation-discount-info'),
    

]


```

# views_bank.py

```py
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import BankAccount
from django.contrib import messages
import json
from django.core.exceptions import ValidationError
from decimal import Decimal

class BankAccountListView(ListView):
    model = BankAccount
    template_name = 'bank/bank_list.html'
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = BankAccount.BANK_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters if any
        bank = self.request.GET.get('bank')
        if bank:
            queryset = queryset.filter(bank=bank)
            
        account_type = self.request.GET.get('type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(is_active=status == 'active')
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(account_number__icontains=search)
            
        return queryset

class BankAccountCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    data[field] = Decimal(str(data[field]))
                else:
                    data[field] = None
            
            # Create bank account
            account = BankAccount.objects.create(
                bank=data['bank'],
                account_number=data['account_number'],
                accounting_number=data['accounting_number'],
                journal_number=data['journal_number'],
                city=data['city'],
                account_type=data['account_type'],
                is_active=data.get('is_active', True),
                is_current=data.get('is_current', False),
                bank_overdraft=data['bank_overdraft'],
                overdraft_fee=data['overdraft_fee'],
                has_check_discount_line=data.get('has_check_discount_line', False),
                check_discount_line_amount=data['check_discount_line_amount'],
                has_lcn_discount_line=data.get('has_lcn_discount_line', False),
                lcn_discount_line_amount=data['lcn_discount_line_amount'],
                stamp_fee_per_receipt=data['stamp_fee_per_receipt']
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account created successfully',
                'id': str(account.id)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountUpdateView(View):
    def get(self, request, pk):
        account = get_object_or_404(BankAccount, pk=pk)
        return JsonResponse({
            'id': str(account.id),
            'bank': account.bank,
            'account_number': account.account_number,
            'accounting_number': account.accounting_number,
            'journal_number': account.journal_number,
            'city': account.city,
            'account_type': account.account_type,
            'is_active': account.is_active,
            'is_current': account.is_current,
            'bank_overdraft': str(account.bank_overdraft) if account.bank_overdraft else None,
            'overdraft_fee': str(account.overdraft_fee) if account.overdraft_fee else None,
            'has_check_discount_line': account.has_check_discount_line,
            'check_discount_line_amount': str(account.check_discount_line_amount) if account.check_discount_line_amount else None,
            'has_lcn_discount_line': account.has_lcn_discount_line,
            'lcn_discount_line_amount': str(account.lcn_discount_line_amount) if account.lcn_discount_line_amount else None,
            'stamp_fee_per_receipt': str(account.stamp_fee_per_receipt) if account.stamp_fee_per_receipt else None
        })

    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            data = json.loads(request.body)
            
            # Convert decimal fields
            decimal_fields = [
                'bank_overdraft', 'overdraft_fee', 
                'check_discount_line_amount', 'lcn_discount_line_amount',
                'stamp_fee_per_receipt'
            ]
            
            for field in decimal_fields:
                if data.get(field):
                    setattr(account, field, Decimal(str(data[field])))
                else:
                    setattr(account, field, None)
            
            # Update other fields
            account.bank = data['bank']
            account.account_number = data['account_number']
            account.accounting_number = data['accounting_number']
            account.journal_number = data['journal_number']
            account.city = data['city']
            account.account_type = data['account_type']
            account.is_active = data.get('is_active', True)
            account.is_current = data.get('is_current', False)
            account.has_check_discount_line = data.get('has_check_discount_line', False)
            account.has_lcn_discount_line = data.get('has_lcn_discount_line', False)
            
            account.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountDeleteView(View):
    def post(self, request, pk):
        try:
            account = get_object_or_404(BankAccount, pk=pk)
            account.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Bank account deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class BankAccountDeactivateView(View):
    def post(self, request, pk):
        try:
            account = BankAccount.objects.get(pk=pk)
            
            # Check for active checkers
            if account.checker_set.filter(is_active=True).exists():
                return JsonResponse(
                    {'error': 'Cannot deactivate account with active checkers'}, 
                    status=400
                )
            
            account.is_active = False
            account.save()
            
            return JsonResponse({'message': 'Account deactivated successfully'})
            
        except BankAccount.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class BankAccountFilterView(View):
    def get(self, request):
        try:
            # Start with all accounts
            queryset = BankAccount.objects.all()
            print("Initial QuerySet Count:", queryset.count())  # Debug log
            
            # Apply bank filter
            bank = request.GET.get('bank')
            if bank:
                print("Filter by bank:", bank)  # Debug log
                queryset = queryset.filter(bank=bank)

            # Apply account type filter
            account_type = request.GET.get('type')
            if account_type:
                print("Filter by account type:", account_type)  # Debug log
                queryset = queryset.filter(account_type=account_type)

            # Apply status filter
            status = request.GET.get('status')
            if status:
                print("Filter by status:", status)  # Debug log
                queryset = queryset.filter(is_active=status == 'active')

            # Apply search filter
            search = request.GET.get('search')
            if search:
                print("Filter by search term:", search)  # Debug log
                queryset = queryset.filter(account_number__icontains=search)

            # Final count before rendering
            print("Filtered QuerySet Count:", queryset.count())  # Debug log

            # Render rows
            html = render_to_string(
                'bank/partials/accounts_table.html',
                {'accounts': queryset},
                request=request
            )
            
            return JsonResponse({'html': html})
            
        except Exception as e:
            print("Error in filter view:", str(e))  # Debug log
            return JsonResponse({'error': str(e)}, status=500)



def bank_account_autocomplete(request):
    search_term = request.GET.get('search', '')
    accounts = BankAccount.objects.filter(account_number__icontains=search_term)[:10]
    results = [
        {
            "label": f"{account.bank} [{account.account_number}]",
            "value": account.id,
            "bank": account.bank
        }
        for account in accounts
    ]
    return JsonResponse(results, safe=False)
```

# views_client.py

```py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from .models import Client, Entity, ClientSale
import json
import logging
from django.views.generic import ListView, DetailView
from django.utils import timezone
import calendar
from django.db.models import Q

# Configure logger
logger = logging.getLogger(__name__)

def client_management(request):
    """Main view for client management interface"""
    logger.info("Accessing client management page")
    return render(request, 'client/client_management.html')

@require_http_methods(["GET"])
def list_clients(request):
    """API endpoint to list all clients"""
    logger.debug("Fetching client list")
    try:
        clients = Client.objects.all()
        data = [{
            'id': str(c.id),
            'name': c.name,
            'client_code': c.client_code
        } for c in clients]
        logger.info(f"Successfully fetched {len(data)} clients")
        return JsonResponse({'clients': data})
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_client(request):
    """API endpoint to create a new client"""
    logger.debug("Creating new client")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Validate client code format
        client_code = data.get('client_code', '').strip()
        if not client_code.isdigit() or len(client_code) < 5 or len(client_code) > 10:
            raise ValidationError("Invalid client code format")
        
        # Check for duplicate client code
        if Client.objects.filter(client_code=client_code).exists():
            raise ValidationError("Client code already exists")
        
        client = Client.objects.create(
            name=data['name'],
            client_code=client_code
        )
        logger.info(f"Successfully created client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        }, status=201)
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_client(request, client_id):
    """API endpoint to update a client"""
    logger.debug(f"Updating client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Update fields
        client.name = data['name']
        if 'client_code' in data:
            new_code = data['client_code'].strip()
            if not new_code.isdigit() or len(new_code) < 5 or len(new_code) > 10:
                raise ValidationError("Invalid client code format")
            if Client.objects.filter(client_code=new_code).exclude(id=client_id).exists():
                raise ValidationError("Client code already exists")
            client.client_code = new_code
            
        client.save()
        logger.info(f"Successfully updated client: {client.name}")
        
        return JsonResponse({
            'id': str(client.id),
            'name': client.name,
            'client_code': client.client_code
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_client(request, client_id):
    """API endpoint to delete a client"""
    logger.debug(f"Deleting client {client_id}")
    try:
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        logger.info(f"Successfully deleted client: {client.name}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def validate_field(request, field, value):
    """API endpoint to validate unique fields"""
    logger.debug(f"Validating {field}: {value}")
    
    # Handle empty values
    if not value or value.strip() == '':
        return JsonResponse({'error': 'Value cannot be empty'}, status=400)
    
    try:
        if field == 'clientCode':
            if not (5 <= len(value) <= 10):
                return JsonResponse({'error': 'Client code must be between 5 and 10 digits'}, status=400)
            exists = Client.objects.filter(client_code=value).exists()
        elif field == 'accountingCode':
            if not (5 <= len(value) <= 7):
                return JsonResponse({'error': 'Accounting code must be between 5 and 7 digits'}, status=400)
            if not value.startswith('3'):
                return JsonResponse({'error': 'Accounting code must start with 3'}, status=400)
            exists = Entity.objects.filter(accounting_code=value).exists()
        elif field == 'iceCode':
            if len(value) != 15:
                return JsonResponse({'error': 'ICE code must be exactly 15 digits'}, status=400)
            exists = Entity.objects.filter(ice_code=value).exists()
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        return JsonResponse({'available': not exists})
    except Exception as e:
        logger.error(f"Error validating {field}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    
class ClientSaleListView(ListView):
    template_name = 'client/sale_list.html'
    model = ClientSale
    context_object_name = 'sales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = timezone.now().year
        context['current_month'] = timezone.now().month
        context['month_choices'] = [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]
        return context

@require_http_methods(["POST"])
def create_sale(request):
    try:
        data = request.POST
        sale = ClientSale.objects.create(
            client_id=data['client'],
            date=data['date'],
            amount=data['amount'],
            year=int(data.get('year') or data['date'][:4]),
            month=int(data.get('month') or data['date'][5:7]),
            notes=data.get('notes', ''),
            sale_type=data['sale_type']
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Sale recorded successfully',
            'id': str(sale.id)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

class ClientCardView(DetailView):
    model = Client
    template_name = 'client/client_card.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get year and month from query params or use current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        try:
            year = int(year)
            month = int(month)
        except (TypeError, ValueError):
            year = timezone.now().year
            month = timezone.now().month

        # Get transactions for period
        transactions = self.object.get_transactions(year, month)
        
        context.update({
            'transactions': transactions,
            'selected_year': year,
            'selected_month': month,
            'years': range(2024, timezone.now().year + 1),
            'months': [
                (i, calendar.month_name[i]) 
                for i in range(1, 13)
            ],
            'total_debit': sum(t['debit'] or 0 for t in transactions),
            'total_credit': sum(t['credit'] or 0 for t in transactions),
            'final_balance': transactions[-1]['balance'] if transactions else 0,
        })
        
        return context
    
def client_autocomplete(request):
    term = request.GET.get('term', '')
    clients = Client.objects.filter(
        Q(name__icontains=term) |
        Q(client_code__icontains=term)
    )[:10]

    results = [{
        'id': str(client.id),
        'value': str(client.id),
        'label': f"{client.name} ({client.client_code})"
    } for client in clients]

    return JsonResponse(results, safe=False)
```

# views_entity.py

```py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Entity, Client
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def list_entities(request):
    """API endpoint to list all entities"""
    logger.debug("Fetching entity list")
    try:
        entities = Entity.objects.all()
        data = [{
            'id': str(e.id),
            'name': e.name,
            'ice_code': e.ice_code,
            'accounting_code': e.accounting_code,
            'city': e.city,
            'phone_number': e.phone_number
        } for e in entities]
        logger.info(f"Successfully fetched {len(data)} entities")
        return JsonResponse({'entities': data})
    except Exception as e:
        logger.error(f"Error fetching entities: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_entity(request):
    """API endpoint to create a new entity"""
    logger.debug("Creating new entity")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")

        # Validate ICE code
        ice_code = data.get('ice_code', '').strip()
        if not ice_code.isdigit() or len(ice_code) != 15:
            raise ValidationError("Invalid ICE code format")

        # Validate accounting code
        accounting_code = data.get('accounting_code', '').strip()
        if not accounting_code.startswith('3') or not accounting_code.isdigit() or \
           len(accounting_code) < 5 or len(accounting_code) > 7:
            raise ValidationError("Invalid accounting code format")

        # Check for duplicates
        if Entity.objects.filter(ice_code=ice_code).exists():
            raise ValidationError("ICE code already exists")
        if Entity.objects.filter(accounting_code=accounting_code).exists():
            raise ValidationError("Accounting code already exists")

        entity = Entity.objects.create(
            name=data['name'],
            ice_code=ice_code,
            accounting_code=accounting_code,
            city=data.get('city', ''),
            phone_number=data.get('phone_number', '')
        )
        logger.info(f"Successfully created entity: {entity.name}")

        return JsonResponse({
            'id': str(entity.id),
            'name': entity.name,
            'ice_code': entity.ice_code,
            'accounting_code': entity.accounting_code,
            'city': entity.city,
            'phone_number': entity.phone_number
        }, status=201)

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_entity(request, entity_id):
    """API endpoint to update an entity"""
    logger.debug(f"Updating entity {entity_id}")
    try:
        entity = get_object_or_404(Entity, id=entity_id)
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")

        # Validate ICE code if provided
        if 'ice_code' in data:
            ice_code = data['ice_code'].strip()
            if not ice_code.isdigit() or len(ice_code) != 15:
                raise ValidationError("Invalid ICE code format")
            if Entity.objects.filter(ice_code=ice_code).exclude(id=entity_id).exists():
                raise ValidationError("ICE code already exists")
            entity.ice_code = ice_code

        # Validate accounting code if provided
        if 'accounting_code' in data:
            accounting_code = data['accounting_code'].strip()
            if not accounting_code.startswith('3') or not accounting_code.isdigit() or \
               len(accounting_code) < 5 or len(accounting_code) > 7:
                raise ValidationError("Invalid accounting code format")
            if Entity.objects.filter(accounting_code=accounting_code).exclude(id=entity_id).exists():
                raise ValidationError("Accounting code already exists")
            entity.accounting_code = accounting_code

        # Update other fields
        entity.name = data.get('name', entity.name)
        entity.city = data.get('city', entity.city)
        entity.phone_number = data.get('phone_number', entity.phone_number)

        entity.save()
        logger.info(f"Successfully updated entity: {entity.name}")

        return JsonResponse({
            'id': str(entity.id),
            'name': entity.name,
            'ice_code': entity.ice_code,
            'accounting_code': entity.accounting_code,
            'city': entity.city,
            'phone_number': entity.phone_number
        })

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_entity(request, entity_id):
    """API endpoint to delete an entity"""
    logger.debug(f"Deleting entity {entity_id}")
    try:
        entity = get_object_or_404(Entity, id=entity_id)
        entity.delete()
        logger.info(f"Successfully deleted entity: {entity.name}")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error deleting entity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    

@require_http_methods(["GET"])
def validate_field(request, field, value):
    """API endpoint to validate unique fields"""
    logger.debug(f"Validating {field}: {value}")
    
    # Handle empty values
    if not value or value.strip() == '':
        return JsonResponse({'error': 'Value cannot be empty'}, status=400)
    
    try:
        if field == 'clientCode':
            if not (5 <= len(value) <= 10):
                return JsonResponse({'error': 'Client code must be between 5 and 10 digits'}, status=400)
            exists = Client.objects.filter(client_code=value).exists()
        elif field == 'accountingCode':
            if not (5 <= len(value) <= 7):
                return JsonResponse({'error': 'Accounting code must be between 5 and 7 digits'}, status=400)
            if not value.startswith('3'):
                return JsonResponse({'error': 'Accounting code must start with 3'}, status=400)
            exists = Entity.objects.filter(accounting_code=value).exists()
        elif field == 'iceCode':
            if len(value) != 15:
                return JsonResponse({'error': 'ICE code must be exactly 15 digits'}, status=400)
            exists = Entity.objects.filter(ice_code=value).exists()
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        return JsonResponse({'available': not exists})
    except Exception as e:
        logger.error(f"Error validating {field}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
```

# views_presentation.py

```py
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Presentation, PresentationReceipt, CheckReceipt, LCN, BankAccount, ReceiptHistory
from django.contrib.contenttypes.models import ContentType
import json
import traceback
from decimal import Decimal

class PresentationListView(ListView):
    """
    Display a list of all presentations with filtering capabilities.
    """
    model = Presentation
    template_name = 'presentation/presentation_list.html'
    context_object_name = 'presentations'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add bank accounts for the filter dropdown
        context['bank_accounts'] = BankAccount.objects.filter(is_active=True)
        return context

@method_decorator(csrf_exempt, name='dispatch')
class PresentationCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            print("Parsed JSON data:", data)

            with transaction.atomic():
                # Create the presentation
                presentation = Presentation.objects.create(
                    presentation_type=data['presentation_type'],
                    date=data['date'],
                    bank_account_id=data['bank_account'],
                    notes=data.get('notes', '')
                )
                print("Created presentation:", presentation)

                # Add receipts to the presentation
                receipt_type = data['receipt_type']
                receipt_ids = data['receipt_ids']
                print(f"Adding {receipt_type} receipts:", receipt_ids)

                for receipt_id in receipt_ids:
                    try:
                        # Get the correct receipt model
                        ReceiptModel = CheckReceipt if receipt_type == 'check' else LCN
                        receipt = ReceiptModel.objects.get(id=receipt_id)
                        
                        print(f"Processing receipt: {receipt}, Status: {receipt.status}")

                        # Verify receipt is in portfolio status
                        if receipt.status != 'PORTFOLIO' and receipt.status != 'UNPAID':
                            raise ValidationError(f"Receipt {receipt} is not in portfolio status")

                        # Create presentation receipt with proper field name
                        field_name = 'checkreceipt' if receipt_type == 'check' else 'lcn'
                        kwargs = {
                            'presentation': presentation,
                            'checkreceipt' if receipt_type == 'check' else 'lcn': receipt,
                            'amount': receipt.amount
                        }
                        
                        print(f"Creating presentation receipt with kwargs:", kwargs)
                        presentation_receipt = PresentationReceipt.objects.create(**kwargs)
                        receipt.bank_account = BankAccount.objects.get(id=data['bank_account'])
                        receipt.save()
                        print(f"Created presentation receipt: {presentation_receipt}")

                    except Exception as e:
                        import traceback
                        traceback.print_exc()

                        print(f"Error processing receipt {receipt_id}: {str(e)}")
                        raise

            return JsonResponse({
                'status': 'success',
                'message': 'Presentation created successfully',
                'id': str(presentation.id)
            })

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Error in presentation creation: {type(e).__name__} - {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Failed to create presentation: {str(e)}"
            }, status=400)

class PresentationDetailView(View):
    def get(self, request, pk):
        print("\n=== Starting PresentationDetailView.get ===")
        try:
            print(f"Looking for presentation with pk: {pk}")
            presentation = get_object_or_404(Presentation, pk=pk)
            print(f"Found presentation: {presentation}")
            
            print("Fetching related receipts...")
            receipts = presentation.presentation_receipts.all().select_related(
                'checkreceipt__client',
                'lcn__client',
                'checkreceipt__bank_account',
                'lcn__bank_account'
            )
            print(f"Found {receipts.count()} receipts")

            # Debug template loading
            print("\nChecking template tags:")
            from django.template import engines
            django_engine = engines['django']
            try:
                print("Available template tag libraries:", django_engine.template_libraries)
            except Exception as e:
                print(f"Error accessing template libraries: {e}")

            context = {
                'presentation': presentation,
                'receipts': receipts,
                'rejection_causes': CheckReceipt.REJECTION_CAUSES,
                'total_amount': sum(receipt.amount for receipt in receipts)
            }
            print("\nContext prepared:", context)
            
            try:
                print("\nAttempting to render template...")
                rendered = render(
                    request, 
                    'presentation/presentation_detail_modal.html',
                    context
                )
                print("Template rendered successfully")
                return rendered
            except Exception as template_error:
                import traceback
                print("\nTemplate rendering error:")
                print(traceback.format_exc())
                raise template_error

        except Exception as e:
            import traceback
            print("\n=== Error in PresentationDetailView ===")
            print(traceback.format_exc())
            print("=======================================")
            return JsonResponse({
                'status': 'error',
                'message': f"Detail view error: {str(e)}",
                'traceback': traceback.format_exc()
            }, status=400)

def handle_receipt_status(receipt, new_status):
        if new_status == 'paid':
            receipt.status = 'PAID'
        elif new_status == 'unpaid':
            receipt.status = 'UNPAID'
        receipt.save()

@method_decorator(csrf_exempt, name='dispatch')
class PresentationUpdateView(View):
    def post(self, request, pk):
        print("\n=== Starting presentation edit ===")
        try:
            data = json.loads(request.body)
            print(f"Parsed data: {data}")
            print(f"Request headers: {dict(request.headers)}")
            
            with transaction.atomic():
                presentation = get_object_or_404(Presentation, pk=pk)
                print(f"Found presentation: {presentation.__dict__}")

                if presentation.status == 'pending':
                    # Handle initial status change
                    if not data.get('bank_reference'):
                        print("Error: Missing bank reference")
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Bank reference is required'
                        }, status=400)
                    
                    print(f"Updating presentation status from pending to {data['status']}")
                    presentation.bank_reference = data['bank_reference']
                    presentation.status = data['status']

                    # If status is being set to 'discounted', update all receipts
                    if data['status'] == 'discounted':
                        for pr in presentation.presentation_receipts.all():
                            receipt = pr.checkreceipt or pr.lcn
                            if receipt:
                                receipt.status = 'DISCOUNTED'
                                receipt.save()

                    presentation.save()
                    print("Presentation updated successfully")

                elif (presentation.status == 'presented' or presentation.status == 'discounted'):
                    if 'receipt_statuses' in data:
                        receipt_statuses = data['receipt_statuses']
                        print(f"Processing {len(receipt_statuses)} receipt status updates: {receipt_statuses}")
                        
                        for receipt_id, new_status in receipt_statuses.items():
                            print(f"\nProcessing receipt {receipt_id}:")
                            print(f"New status data: {new_status}")
                            
                            if not new_status:
                                print("Skipping empty status update")
                                continue
                                
                            try:
                                presentation_receipt = PresentationReceipt.objects.get(
                                    id=receipt_id,
                                    presentation=presentation
                                )
                                print(f"Found presentation receipt: {presentation_receipt.__dict__}")
                                
                                receipt = presentation_receipt.checkreceipt or presentation_receipt.lcn
                                print(f"Associated receipt: {receipt.__dict__ if receipt else None}")
                                
                                if receipt and receipt.status not in ['PAID', 'UNPAID', 'COMPENSATED']:
                                    status_value = new_status['status'] if isinstance(new_status, dict) else new_status
                                    print(f"Processing status update to {status_value}")
                                    
                                    if status_value == 'unpaid':
                                        cause = new_status.get('cause') if isinstance(new_status, dict) else None
                                        print(f"Processing unpaid status with cause: {cause}")
                                        if not cause:
                                            raise ValidationError("Rejection cause required for unpaid status")
                                        # Add this line after successful unpaid update
                                        presentation_receipt.recorded_status = 'UNPAID'
                                        presentation_receipt.save()
                                        receipt.mark_as_unpaid(cause)
                                    else:
                                        print(f"Updating status to: {status_value.upper()}")
                                        # Add this line after successful paid update
                                        presentation_receipt.recorded_status = status_value.upper()
                                        presentation_receipt.save()
                                        receipt.status = status_value.upper()
                                        receipt.save()
                                        
                                        if status_value.upper() == 'PAID':
                                            print("Receipt marked as paid, updating compensated receipts")
                                            receipt.update_compensated_receipts()
                                    
                                    print("Status update completed successfully")
                                else:
                                    print(f"Skipping receipt with status: {receipt.status if receipt else 'None'}")

                            except PresentationReceipt.DoesNotExist:
                                print(f"Error: Receipt {receipt_id} not found in presentation {pk}")
                                continue
                            except Exception as e:
                                print(f"Error processing receipt {receipt_id}: {str(e)}")
                                print(traceback.format_exc())
                                raise
                
                print("Presentation update completed successfully")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Presentation updated successfully'
                })

        except Exception as e:
            print("=== Error in presentation edit ===")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)    
   
@method_decorator(csrf_exempt, name='dispatch')
class PresentationDeleteView(View):
    """
    Handle deletion of presentations, resetting the status of associated receipts.
    """
    def post(self, request, pk):
            print(f"Delete request received for presentation {pk}")
            try:
                with transaction.atomic():
                    presentation = get_object_or_404(Presentation, pk=pk)
                    
                    # Only allow deletion of pending presentations
                    if presentation.status != 'pending':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Only pending presentations can be deleted'
                        }, status=400)
                    
                    # Get all related receipts before deletion
                    related_receipts = []
                    for pr in presentation.presentation_receipts.all():
                        receipt = pr.checkreceipt or pr.lcn
                        if receipt:
                            related_receipts.append(receipt)

                    # Delete presentation-related history entries for all receipts
                    content_types = ContentType.objects.get_for_model(CheckReceipt), ContentType.objects.get_for_model(LCN)
                    for receipt in related_receipts:
                        ReceiptHistory.objects.filter(
                            content_type__in=content_types,
                            object_id=receipt.id,
                            new_value__contains=str(presentation.id)  # Look for presentation ID in the new_value JSON
                        ).delete()
                        
                        # Reset receipt status back to PORTFOLIO
                        receipt.status = 'PORTFOLIO'
                        receipt.save()
                    
                    # Delete the presentation
                    presentation.delete()
                    print(f"Presentation {pk} deleted successfully")

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Presentation deleted successfully'
                    })

            except Presentation.DoesNotExist:
                print(f"Presentation {pk} not found")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Presentation not found'
                }, status=404)
            except Exception as e:
                print(f"Error deleting presentation {pk}: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to delete presentation: {str(e)}'
                }, status=500)

class AvailableReceiptsView(View):
    """
    Return a list of receipts available for presentation (in portfolio status).
    """
    def get(self, request):
        receipt_type = request.GET.get('type')
        
        if receipt_type == 'check':
            receipts = CheckReceipt.objects.filter(
                status__in=[
                    CheckReceipt.STATUS_PORTFOLIO,
                    CheckReceipt.STATUS_UNPAID
                ]
            ).select_related('client', 'entity')
        else:  # lcn
            receipts = LCN.objects.filter(
                status__in=[
                    LCN.STATUS_PORTFOLIO,
                    LCN.STATUS_UNPAID
                ]
            ).select_related('client', 'entity')
        
        # Get presentation info for unpaid receipts
        for receipt in receipts:
            if receipt.status == 'UNPAID':
                if receipt_type == 'check':
                    presentation = receipt.check_presentations.order_by('-presentation__date').first()
                else:
                    presentation = receipt.lcn_presentations.order_by('-presentation__date').first()
                
                if presentation:
                    receipt.last_presentation_date = presentation.presentation.date

        html = render_to_string('presentation/available_receipts.html', {
            'receipts': receipts
        }, request=request)
        
        return JsonResponse({'html': html})

class DiscountInfoView(View):
    def get(self, request, bank_account_id):
        try:
            bank_account = get_object_or_404(BankAccount, id=bank_account_id)
            receipt_type = request.GET.get('type', 'check')
            
            if receipt_type == 'check':
                available = bank_account.get_available_check_discount_line()
                total = bank_account.check_discount_line_amount or Decimal('0.00')
            else:
                available = bank_account.get_available_lcn_discount_line()
                total = bank_account.lcn_discount_line_amount or Decimal('0.00')
            
            used = total - available
            
            return JsonResponse({
                'total_amount': str(total),
                'used_amount': str(used),
                'available_amount': str(available)
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)
```

```py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product
from .forms import ProductForm
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.db import models
from django.views.generic.edit import DeleteView
from django.contrib import messages

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        product = self.get_object()
        print("Current VAT rate:", product.vat_rate)  # Debug print
        print("Form VAT rate:", form.initial.get('vat_rate'))  # Debug print
        return form

    def get_initial(self):
        initial = super().get_initial()
        product = self.get_object()
        print("Initial VAT rate:", product.vat_rate)  # Debug print
        initial['vat_rate'] = product.vat_rate
        return initial

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoiceproduct_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoiceproduct_set.count()} invoice(s).')
            return redirect('product-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete product. It is referenced by one or more invoices.')
            return redirect('product-list')


# AJAX view for creating a new Product
@method_decorator(csrf_exempt, name='dispatch')
class ProductAjaxCreateView(View):
    def post(self, request):
        try:
            name = request.POST.get('name')
            # Check for existing product with same name
            if Product.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'error': f'A product with the name "{name}" already exists.'
                }, status=400)

            product = Product.objects.create(
                name=name,
                fiscal_label=request.POST.get('fiscal_label'),
                is_energy=request.POST.get('is_energy') == 'true',
                expense_code=request.POST.get('expense_code'),
                vat_rate=request.POST.get('vat_rate')
            )
            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(product.id)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailsView(View):
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            return JsonResponse({
                'expense_code': product.expense_code,
                'vat_rate': str(product.vat_rate)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


```

# views_receipts.py

```py
from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import calendar
from .models import CheckReceipt, LCN, CashReceipt, TransferReceipt, BankAccount, Client, Entity, ReceiptHistory, MOROCCAN_BANKS
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
import traceback


class ReceiptListView(ListView):
    template_name = 'receipt/receipt_list.html'
    context_object_name = 'receipts'

    def get_queryset(self):
        print("\n=== Getting Receipt Queryset ===")
        checks = CheckReceipt.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'check_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {checks.count()} checks")
        
        lcns = LCN.objects.select_related(
            'client', 'entity'
        ).prefetch_related(
            'lcn_presentations__presentation__bank_account'
        ).all()
        print(f"Fetched {lcns.count()} LCNs")

        # Debug presentation info
        for check in checks:
            pres = check.check_presentations.first()
            if pres:
                print(f"Check {check.id} presentation: {pres.presentation.id}")
                print(f"Bank: {pres.presentation.bank_account}")

        return {
            'checks': checks,
            'lcns': lcns,
            'cash': CashReceipt.objects.select_related('client', 'entity', 'bank_account','credited_account').all(),
            'transfers': TransferReceipt.objects.select_related('client', 'entity', 'bank_account','credited_account').all()
        }

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptCreateView(View):
    def get(self, request, receipt_type):
        print(f"Loading form for receipt type: {receipt_type}")
        if receipt_type not in ['check', 'lcn', 'cash', 'transfer']:
            return JsonResponse({'error': 'Invalid receipt type'}, status=400)

        # Get current date info
        today = timezone.now()
        current_year = today.year
        current_month = today.month

        # Generate year choices (current year and 2 years back)
        year_choices = range(current_year - 2, current_year + 1)

        # Generate month choices
        month_choices = [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ]

        # Get active bank accounts
        bank_accounts = BankAccount.objects.filter(is_active=True)

        context = {
            'receipt_type': receipt_type,
            'title': f'New {receipt_type.title()} Receipt',
            'year_choices': year_choices,
            'month_choices': month_choices,
            'current_year': current_year,
            'current_month': current_month,
            'bank_accounts': bank_accounts,
            'bank_choices': MOROCCAN_BANKS, 
        }
        print(f"Context receipt_type: {context['receipt_type']}") 
        rendered = render(request, 'receipt/receipt_form_modal.html', context)
        print(f"Form HTML contains transfer fields: {'transfer_date' in rendered.content.decode()}")  # Debug
        return rendered
    
    def post(self, request, receipt_type):
        print("POST request received:")
        print("Receipt type:", receipt_type)
        print("Raw POST data:", request.body)
        data = request.POST.dict()
        print("POST data:", request.POST)
        print("transfer_date value:", request.POST.get('transfer_date'))
        print("transfer_reference value:", request.POST.get('transfer_reference'))
        
        try:
            data = request.POST.dict()

            compensates_id = data.pop('compensates', None)

            # Convert amount to Decimal
            data['amount'] = Decimal(data['amount'].replace(',', ''))
            
            # Common fields for all receipt types
            common_fields = {
                'client_id': data['client'],
                'entity_id': data['entity'],
                'operation_date': data['operation_date'],
                'amount': data['amount'],
                'client_year': data['client_year'],
                'client_month': data['client_month'],
                'notes': data.get('notes', '')
            }

            if receipt_type == 'check':
                receipt = CheckReceipt.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    check_number=data['check_number'],
                    branch=data.get('branch', '')
                )
            
            elif receipt_type == 'lcn':
                receipt = LCN.objects.create(
                    **common_fields,
                    issuing_bank=data['issuing_bank'],
                    due_date=data['due_date'],
                    lcn_number=data['lcn_number'],
                )
            
            elif receipt_type == 'cash':
                receipt = CashReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    bank_account_id=data['credited_account'],
                    reference_number=data.get('reference_number', '')
                )
            
            elif receipt_type == 'transfer':
                receipt = TransferReceipt.objects.create(
                    **common_fields,
                    credited_account_id=data['credited_account'],
                    bank_account_id=data['credited_account'],
                    transfer_reference=data.get('transfer_reference', ''),
                    transfer_date=data.get('transfer_date')
                )

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid receipt type'
                }, status=400)
            
            # Handle compensation if selected
            if compensates_id:
                # Find the unpaid receipt
                unpaid_receipt = None
                try:
                    unpaid_receipt = CheckReceipt.objects.get(
                        id=compensates_id, 
                        status=CheckReceipt.STATUS_UNPAID
                    )
                except CheckReceipt.DoesNotExist:
                    try:
                        unpaid_receipt = LCN.objects.get(
                            id=compensates_id, 
                            status=LCN.STATUS_UNPAID
                        )
                    except LCN.DoesNotExist:
                        pass
                
                if unpaid_receipt:
                    unpaid_receipt.compensate_with(receipt)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} created successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptUpdateView(View):
    def get(self, request, receipt_type, pk):
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        try:
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            
            # Get current date info for form
            today = timezone.now()
            year_choices = range(today.year - 2, today.year + 1)
            month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
            bank_accounts = BankAccount.objects.filter(is_active=True)

            context = {
                'receipt_type': receipt_type,
                'receipt': receipt,
                'title': f'Edit {receipt_type.title()}',
                'year_choices': year_choices,
                'month_choices': month_choices,
                'bank_accounts': bank_accounts,
                'client': {
                    'id': str(receipt.client.id),
                    'text': f"{receipt.client.name} ({receipt.client.client_code})"
                },
                'entity': {
                    'id': str(receipt.entity.id),
                    'text': f"{receipt.entity.name} ({receipt.entity.ice_code})"
                },
                'bank_choices': MOROCCAN_BANKS,
            }

            return render(request, 'receipt/receipt_form_modal.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, receipt_type, pk):
        import traceback
        try:
            data = request.POST.dict()
            print(f"Received data for {receipt_type} update:", data)
            
            model_map = {
                'check': CheckReceipt,
                'lcn': LCN,
                'cash': CashReceipt,
                'transfer': TransferReceipt
            }
            
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Update common fields
            receipt.client_id = data['client']
            receipt.entity_id = data['entity']
            receipt.operation_date = data['operation_date']
            receipt.amount = data['amount']
            receipt.client_year = data['client_year']
            receipt.client_month = data['client_month']
            receipt.notes = data.get('notes', '')

            # Update type-specific fields
            if receipt_type in ['check', 'lcn']:
                receipt.issuing_bank = data['issuing_bank']  # Set issuing bank
                receipt.due_date = data['due_date']
                if receipt_type == 'check':
                    receipt.check_number = data['check_number']
                    receipt.branch = data.get('branch', '')
                else:
                    receipt.lcn_number = data['lcn_number']
            else:  # cash or transfer
                receipt.credited_account_id = data['credited_account']
                receipt.bank_account_id = data['credited_account'] 
                if receipt_type == 'transfer':  
                    receipt.transfer_reference = data['transfer_reference'] 
                    receipt.transfer_date = data['transfer_date']

            receipt.save()
            print(f"{receipt_type} updated successfully:", receipt)

            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} updated successfully',
                'id': str(receipt.id)
            })

        except Exception as e:
            print("Error in receipt update:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDeleteView(View):
    def post(self, request, receipt_type, pk):
        try:
            model_map = {
                'check': CheckReceipt,
                'lcn': LCN,
                'cash': CashReceipt,
                'transfer': TransferReceipt
            }
            
            receipt = get_object_or_404(model_map[receipt_type], pk=pk)
            
            # Check if receipt can be deleted
            if receipt_type in ['check', 'lcn']:
                presentations = receipt.check_presentations.all() if receipt_type == 'check' else receipt.lcn_presentations.all()
                if presentations.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Cannot delete receipt that is part of a presentation'
                    }, status=400)

            receipt.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'{receipt_type.title()} deleted successfully'
            })
        except Exception as e:
            print("Error in receipt deletion:")
            print(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ReceiptDetailView(View):
    def get(self, request, receipt_type, pk):
        # Map receipt types to their corresponding models
        model_map = {
            'check': CheckReceipt,
            'lcn': LCN,
            'cash': CashReceipt,
            'transfer': TransferReceipt
        }
        
        # Get the appropriate model
        model = model_map.get(receipt_type)
        if not model:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid receipt type'
            }, status=400)
        
        # Get the receipt instance
        try:
            receipt = model.objects.select_related(
                'client',
                'entity',
                'bank_account'
            ).get(pk=pk)
            
            # Build context based on receipt type
            context = {
                'receipt': receipt,
                'receipt_type': receipt_type,
                'client': receipt.client,
                'entity': receipt.entity,
                'bank_account': receipt.bank_account,
                'common_fields': {
                    'Operation Date': receipt.operation_date,
                    'Amount': receipt.amount,
                    'Client Year': receipt.client_year,
                    'Client Month': calendar.month_name[receipt.client_month],
                    'Notes': receipt.notes or 'No notes'
                }
            }
            
            # Add type-specific fields
            if receipt_type in ['check', 'lcn']:
                context['specific_fields'] = {
                    'Due Date': receipt.due_date,
                    'Status': receipt.get_status_display() if hasattr(receipt, 'get_status_display') else receipt.status
                }
                if receipt_type == 'check':
                    context['specific_fields'].update({
                        'Check Number': receipt.check_number,
                        'Bank Name': receipt.bank_name,
                        'Branch': receipt.branch or 'N/A'
                    })
                else:  # LCN
                    context['specific_fields'].update({
                        'LCN Number': receipt.lcn_number,
                        'Issuing Bank': receipt.issuing_bank
                    })
            else:  # cash or transfer
                context['specific_fields'] = {
                    'Credited Account': receipt.credited_account.account_number
                }
                if receipt_type == 'cash':
                    context['specific_fields']['Reference Number'] = receipt.reference_number or 'N/A'
                else:  # transfer
                    context['specific_fields'].update({
                        'Transfer Reference': receipt.transfer_reference,
                        'Transfer Date': receipt.transfer_date
                    })
            
            # Render the template
            html = render_to_string('receipt/receipt_detail_modal.html', context)
            return JsonResponse({
                'status': 'success',
                'html': html
            })
            
        except model.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Receipt not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptStatusUpdateView(View):
    """Handle receipt status updates including unpaid marking"""
    def post(self, request, receipt_type, pk):
        try:
            data = json.loads(request.body)
            model = CheckReceipt if receipt_type == 'check' else LCN
            receipt = get_object_or_404(model, pk=pk)
            
            status = data.get('status')
            cause = data.get('cause')
            
            if status == 'unpaid':
                if not cause:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Rejection cause is required'
                    }, status=400)
                receipt.mark_as_unpaid(cause)
            else:
                receipt.status = status
                receipt.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Receipt status updated to {status}'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class UnpaidReceiptsView(View):
    """API endpoint to list unpaid receipts for compensation selection"""
    def get(self, request):
        search = request.GET.get('search', '')
        
        # Query both check and LCN models for unpaid receipts
        unpaid_checks = CheckReceipt.objects.filter(
            status=CheckReceipt.STATUS_UNPAID,
            compensating_receipt__isnull=True
        ).select_related('entity')
        
        unpaid_lcns = LCN.objects.filter(
            status=LCN.STATUS_UNPAID,
            compensating_receipt__isnull=True
        ).select_related('entity')
        
        if search:
            unpaid_checks = unpaid_checks.filter(
                Q(check_number__icontains=search) |
                Q(entity__name__icontains=search)
            )
            unpaid_lcns = unpaid_lcns.filter(
                Q(lcn_number__icontains=search) |
                Q(entity__name__icontains=search)
            )
        
        # Format results
        results = []
        for check in unpaid_checks:
            results.append({
                'id': str(check.id),
                'type': 'Check',
                'number': check.check_number,
                'entity': check.entity.name,
                'amount': float(check.amount),
                'date': check.operation_date.strftime('%Y-%m-%d'),
                'url': reverse('receipt-detail', kwargs={'receipt_type': 'check', 'pk': check.id})
            })
            
        for lcn in unpaid_lcns:
            results.append({
                'id': str(lcn.id),
                'type': 'LCN',
                'number': lcn.lcn_number,
                'entity': lcn.entity.name,
                'amount': float(lcn.amount),
                'date': lcn.operation_date.strftime('%Y-%m-%d'),
                'url': reverse('receipt-detail', kwargs={'receipt_type': 'lcn', 'pk': lcn.id})
            })
            
        return JsonResponse({
            'items': results,
            'has_more': False  # Implement pagination if needed
        })
    
# In views_receipts.py - add the following class

class ReceiptTimelineView(View):
    def get(self, request, receipt_type, pk):
        try:
            # Get the receipt
            if receipt_type == 'check':
                receipt = get_object_or_404(CheckReceipt, pk=pk)
            else:
                receipt = get_object_or_404(LCN, pk=pk)

            # Get the receipt's history
            content_type = ContentType.objects.get_for_model(receipt)
            history = ReceiptHistory.objects.filter(
                content_type=content_type,
                object_id=receipt.id
            ).select_related('user')

            context = {
                'receipt': receipt,
                'history': history,
            }

            return render(request, 'receipt/receipt_timeline_modal.html', context)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

def client_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    clients = Client.objects.filter(
        Q(name__icontains=search) | 
        Q(client_code__icontains=search)
    )[:10]

    results = [{
        'id': str(client.id),
        'text': f"{client.name} ({client.client_code})"
    } for client in clients]
    print(f"results({len(results)}): {results}")

    return JsonResponse({'results': results})


def entity_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    entities = Entity.objects.filter(
        Q(name__icontains=search) | 
        Q(ice_code__icontains=search)
    )[:10]

    results = [{
        'id': str(entity.id),
        'text': f"{entity.name} ({entity.ice_code})"
    } for entity in entities]
    print(f"results({len(results)}): {results}")
    return JsonResponse({'results': results})

def unpaid_receipt_autocomplete(request):
    search = request.GET.get('term', '') or request.GET.get('q', '')
    
    # Search across CheckReceipt and LCN
    unpaid_checks = CheckReceipt.objects.filter(
        status=CheckReceipt.STATUS_UNPAID
    ).filter(
        check_number__icontains=search
    )[:10]
    
    unpaid_lcns = LCN.objects.filter(
        status=LCN.STATUS_UNPAID
    ).filter(
        lcn_number__icontains=search
    )[:10]
    
    # Combine results
    results = []
    
    for check in unpaid_checks:
        results.append({
            'id': str(check.id),
            'text': f"Check #{check.check_number} ({check.entity.name}) - {check.amount} [{check.get_rejection_cause_display() or 'No cause'}]",
            'description': f"Check #{check.check_number} ({check.entity.name}) - {check.amount} [{check.get_rejection_cause_display() or 'No cause'}]"
        })
    
    for lcn in unpaid_lcns:
        results.append({
            'id': str(lcn.id),
            'text': f"LCN #{lcn.lcn_number} ({lcn.entity.name}) - {lcn.amount} [{lcn.get_rejection_cause_display() or 'No cause'}]",
            'description': f"LCN #{lcn.lcn_number} ({lcn.entity.name}) - {lcn.amount} [{lcn.get_rejection_cause_display() or 'No cause'}]"
        })
    
    print(f"Unpaid Receipt results({len(results)}): {results}")
    return JsonResponse({'results': results})
```

# views.py

```py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView


# Create your views here.
def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # Redirect to the profile view after successful login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')  # Render the login template

@never_cache
@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def profile(request):
    return render(request, 'profile.html')  # Use 'profile.html' directly


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Welcome, {form.get_user().first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Custom logout view to prevent back button access after logout
@cache_control(no_cache=True, must_revalidate=True)
def logout_view(request):
    logout(request)
    # Redirect to the login page after logout
    response = HttpResponseRedirect('/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
```
