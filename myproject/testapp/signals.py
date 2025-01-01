from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CheckAllocation, Profile, Check

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

@receiver(post_save, sender=CheckAllocation)
def update_invoice_status_on_allocation(sender, instance, **kwargs):
    instance.invoice.update_payment_status()

@receiver(post_delete, sender=CheckAllocation)
def update_invoice_status_on_deallocation(sender, instance, **kwargs):
    instance.invoice.update_payment_status()