

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
            date__range=(period_start, period_end)
        ).select_related('fee_type')

        print(f"\nProcessing {bank_fees.count()} bank fees")
        
        for fee in bank_fees:
            if fee.vat_amount > 0:
                print(f"\nProcessing fee: {fee.fee_type.name}")
                print(f"VAT amount: {fee.vat_amount}")
                
                self._store_payment_details(
                    fee.id,
                    'bank_fee',
                    fee.date,
                    fee.reference,
                    fee.fee_type.name,
                    fee.raw_amount,
                    fee.vat_amount,
                    fee.vat_rate
                )
                
                total_deducted += fee.vat_amount
                print(f"Running total: {total_deducted}")
            
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
            # Move to next month
            if current_date.month == 12:
                next_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_date = current_date.replace(month=current_date.month + 1)
                
            # Adjust for declaration day
            try:
                forecast_date = next_date.replace(day=min(config.declaration_day, calendar.monthrange(next_date.year, next_date.month)[1]))
            except ValueError:
                # If day is invalid (e.g., February 30), use last day of month
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

