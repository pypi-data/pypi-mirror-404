"""
Signal handlers for GPWebPay payment provider registration.
"""
from django.dispatch import receiver
from pretix.base.signals import register_payment_providers


@receiver(register_payment_providers, dispatch_uid="payment_gpwebpay")
def register_payment_provider(sender, **kwargs):
    """
    Register GPWebPay payment provider with Pretix.
    
    This signal handler is called by Pretix to discover available
    payment providers and registers the GPWebPay provider.
    """
    from .payment import GPWebPay
    return GPWebPay

