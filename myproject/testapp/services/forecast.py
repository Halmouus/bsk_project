
from datetime import timedelta
from django.utils import timezone
from ..models import ForecastStatement, CheckReceipt, LCN

class PaymentForecastService:
    @classmethod
    def create_forecast(cls, presentation_receipt):
        """Create forecast statement for a presented receipt"""
        receipt = presentation_receipt.checkreceipt or presentation_receipt.lcn
        bank_account = presentation_receipt.presentation.bank_account
        
        # Calculate forecast date
        if isinstance(receipt, LCN):
            if receipt.due_date > timezone.now().date():
                forecast_date = cls._next_business_day(receipt.due_date)
            else:
                days = 1 if receipt.issuing_bank == bank_account.bank else 2
                forecast_date = cls._next_business_day(presentation_receipt.presentation.date, days)
        else:  # Check
            days = 1 if receipt.issuing_bank == bank_account.bank else 2
            forecast_date = cls._next_business_day(presentation_receipt.presentation.date, days)
        
        # Create forecast statement
        return ForecastStatement.objects.create(
            bank_account=bank_account,
            date=forecast_date,
            label=f"Expected payment of {receipt.__class__.__name__} #{receipt.get_receipt_number()}",
            credit=receipt.amount,  # It's a credit since we expect to receive money
            reference=f"Pres. #{presentation_receipt.presentation.id}",
            source_type=receipt.__class__.__name__.lower(),
            source_id=receipt.id
        )

    @staticmethod
    def _next_business_day(start_date, skip_days=0):
        """Calculate next business day skipping weekends"""
        current_date = start_date
        while skip_days > 0:
            current_date += timedelta(days=1)
            # Skip weekends
            while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                current_date += timedelta(days=1)
            skip_days -= 1
        return current_date