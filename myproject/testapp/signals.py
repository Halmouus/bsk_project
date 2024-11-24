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
