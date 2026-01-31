import logging

from celery import shared_task
from django.shortcuts import get_object_or_404
from django_scopes import scopes_disabled
from pretix.base.models import OrderPayment

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def gpwebpay_sync_payment(self, payment_id: int):
    try:
        with scopes_disabled():
            payment_obj = get_object_or_404(OrderPayment, id=payment_id)
        event = payment_obj.order.event
        provider = event.get_payment_providers().get('gpwebpay')
        if not provider:
            return
        provider.sync_payment_from_ws(payment_obj)
    except Exception as e:
        logger.error('GPWebPay WS sync task failed for payment %s: %s', payment_id, e, exc_info=True)
