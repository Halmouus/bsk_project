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
