from django.core.exceptions import ValidationError
from django.db import transaction

def create_check(
    checker,
    position,
    creation_date,
    beneficiary,
    cause,
    payment_due,
    amount,
    observation
):
    """
    Create a check with validation and transactional safety.

    Args:
        checker (Checker): The associated checker instance.
        position (int): The position for the check.
        creation_date (date): The creation date for the check.
        beneficiary (Supplier): The supplier to whom the check is issued.
        cause (Invoice): The invoice causing the check.
        payment_due (date): The payment due date for the check.
        amount (Decimal): The amount of the check.
        observation (str): Additional notes or observations.

    Returns:
        Check: The created Check instance.

    Raises:
        ValidationError: If validation fails.
    """
    # Validate duplicate position
    if checker.checks.filter(position=position).exists():
        raise ValidationError(f"Position {position} is already used.")

    # Validate range
    if position < checker.starting_page or position > checker.final_page:
        raise ValidationError(
            f"Position must be between {checker.starting_page} and {checker.final_page}."
        )

    # Transaction to ensure atomicity
    with transaction.atomic():
        check = Check.objects.create(
            checker=checker,
            position=position,
            creation_date=creation_date,
            beneficiary=beneficiary,
            cause=cause,
            payment_due=payment_due,
            amount=amount,
            observation=observation
        )

        # Update checker's current position
        next_position = checker.current_position + 1
        if next_position <= checker.final_page:
            checker.current_position = next_position
            checker.save()

    return check
