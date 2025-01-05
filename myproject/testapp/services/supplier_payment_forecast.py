from datetime import datetime, timedelta
import traceback
from django.utils import timezone
from ..models import ForecastStatement, Check

class SupplierPaymentForecastService:
    @classmethod
    def create_forecast(cls, payment):
        """Create forecast statement for a supplier payment"""
        print("\n=== Creating Supplier Payment Forecast ===")
        print(f"Payment ID: {payment.id}")
        print(f"Payment Type: {payment.__class__.__name__}")
        print(f"Due Date: {payment.payment_due}")
        
        try:
            # Calculate forecast date
            forecast_date = cls._calculate_forecast_date(payment)
            print(f"Calculated forecast date: {forecast_date}")
            
            # Check for existing forecast
            existing_forecast = ForecastStatement.objects.filter(
                source_type=f"supplier_{payment.__class__.__name__.lower()}",
                source_id=payment.id,
                is_processed=False
            ).first()
            
            if existing_forecast:
                print(f"Updating existing forecast {existing_forecast.id}")
                existing_forecast.date = forecast_date
                existing_forecast.debit = payment.amount
                existing_forecast.save()
                return existing_forecast
                
            print("Creating new forecast")
            forecast = ForecastStatement.objects.create(
                bank_account=payment.checker.bank_account,
                date=forecast_date,
                label=f"Expected payment to {payment.beneficiary.name}",
                debit=payment.amount,
                reference=f"Payment #{payment.position}",
                source_type=f"supplier_{payment.__class__.__name__.lower()}",
                source_id=payment.id
            )
            print(f"Created forecast {forecast.id}")
            return forecast
            
        except Exception as e:
            print(f"Error in create_forecast: {str(e)}")
            print(traceback.format_exc())
            raise

    @classmethod
    def _calculate_forecast_date(cls, payment):
        """Calculate the forecast date based on payment type and supplier settings"""
        # Start with payment due date
        base_date = payment.payment_due
        
        # Get delay based on payment type
        delay = payment.beneficiary.delay_check if isinstance(payment, Check) else payment.beneficiary.delay_lcn
        
        # Add delay and skip weekends
        current_date = base_date
        while delay > 0 or current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            # Only count non-weekend days for delay
            if current_date.weekday() < 5:
                delay -= 1
        
        return current_date

    @classmethod
    def process_payment_status(cls, payment, status):
        """Handle payment status changes"""
        forecast = ForecastStatement.objects.filter(
            source_type=f"supplier_{payment.__class__.__name__.lower()}",
            source_id=payment.id,
            is_processed=False
        ).first()
        
        if not forecast:
            return
            
        if status == 'paid':
            # Mark forecast as processed
            forecast.is_processed = True
            forecast.save()
        elif status == 'unpaid':
            # Remove forecast
            forecast.delete()