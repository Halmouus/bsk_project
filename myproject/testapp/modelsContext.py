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