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