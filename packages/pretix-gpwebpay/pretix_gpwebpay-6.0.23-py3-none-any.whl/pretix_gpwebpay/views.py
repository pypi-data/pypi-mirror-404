"""
Views for handling GPWebPay payment gateway callbacks.

This module provides views for processing user redirects and server-to-server
notifications from the GPWebPay payment gateway, including signature verification
and payment status updates.
"""
import logging
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import escape
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_scopes import scopes_disabled
from pretix.base.models import Order, OrderPayment
from pretix.base.services import quotas

logger = logging.getLogger(__name__)

def _safe_order_url(order_obj: Order) -> str:
    if hasattr(order_obj, 'get_abandon_url'):
        return order_obj.get_abandon_url()
    if hasattr(order_obj, 'get_absolute_url'):
        return order_obj.get_absolute_url()
    try:
        return reverse('presale:event.order', kwargs={
            'organizer': order_obj.event.organizer.slug,
            'event': order_obj.event.slug,
            'order': order_obj.code,
            'secret': order_obj.secret,
        })
    except Exception:
        return '/'

def _collect_params(request: HttpRequest) -> dict:
    params = {}
    for key in request.GET.keys():
        params[key] = request.GET.get(key)
    for key in request.POST.keys():
        params[key] = request.POST.get(key)
    return params


def _is_success(prcode: str, srcode: str) -> bool:
    return str(prcode).strip() == '0' and str(srcode).strip() == '0'


@method_decorator(csrf_exempt, name='dispatch')
class RedirectView(View):
    """
    Render an auto-submitting POST form to the GPWebPay gateway.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_redirect(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_redirect(request, order, payment, hash)

    def _handle_redirect(self, request: HttpRequest, order: str, payment: int, hash: str):
        order_obj = None
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                messages.error(request, _('Payment provider not configured.'))
                return redirect(_safe_order_url(order_obj))

            gateway_url = provider.get_gateway_url()

            params = provider.build_request_params(request, payment_obj)

            inputs = '\n'.join(
                f'<input type="hidden" name="{escape(str(k))}" value="{escape(str(v))}"/>'
                for k, v in params.items()
            )
            html = f"""
            <form id="gpwebpay-form" action="{escape(gateway_url)}" method="post" accept-charset="UTF-8">
                <p>{_('Redirecting to GPWebPay...')}</p>
                <p>{_('If you are not redirected automatically, click the button below.')}</p>
                {inputs}
                <button type="submit">{_('Continue to payment')}</button>
            </form>
            <script src="/static/pretix_gpwebpay/redirect.js"></script>
            """
            return HttpResponse(html)
        except Exception as e:
            logger.error(f'Error preparing GPWebPay redirect: {e}', exc_info=True)
            messages.error(request, _('Error preparing payment request.'))
            if order_obj is not None:
                try:
                    return redirect(_safe_order_url(order_obj))
                except Exception:
                    pass
            return HttpResponseBadRequest('Error preparing payment')


@method_decorator(csrf_exempt, name='dispatch')
class ReturnView(View):
    """
    Handle user redirect return from GPWebPay payment gateway.
    
    Processes the payment response when the customer is redirected back
    from the GPWebPay gateway after completing or canceling payment.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_response(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_response(request, order, payment, hash)

    def _handle_response(self, request: HttpRequest, order: str, payment: int, hash: str):
        """
        Process GPWebPay return response.
        
        Verifies the payment signature, checks payment status codes,
        and updates the payment state accordingly.
        
        Args:
            request: HTTP request containing GPWebPay response parameters
            order: Order code
            payment: Payment ID
            hash: Order secret hash for validation
        """
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            # Get payment provider
            from pretix.base.models import Event
            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                messages.error(request, _('Payment provider not configured.'))
                return redirect(_safe_order_url(order_obj))

            # Get settings
            settings_dict = provider.settings
            public_key_data = settings_dict.get('public_key', '')
            merchant_number = settings_dict.get('merchant_number', '')

            all_params = _collect_params(request)
            operation = all_params.get('OPERATION', '')
            ordernumber = all_params.get('ORDERNUMBER', '')
            merchantnumber = all_params.get('MERCHANTNUMBER', '')
            prcode = all_params.get('PRCODE', '')
            srcode = all_params.get('SRCODE', '')
            resulttext = all_params.get('RESULTTEXT', '')
            digest = all_params.get('DIGEST', '')
            digest1 = all_params.get('DIGEST1', '')
            if ' ' in digest or ' ' in digest1:
                digest = digest.replace(' ', '+')
                digest1 = digest1.replace(' ', '+')

            logger.info(
                'GPWebPay return params: order=%s payment=%s op=%s pr=%s sr=%s state=%s',
                ordernumber, payment_obj.id, operation, prcode, srcode, payment_obj.state
            )

            if ordernumber and str(payment_obj.id) != ordernumber:
                logger.error('GPWebPay order number mismatch: expected %s got %s', payment_obj.id, ordernumber)
                messages.error(request, _('Payment verification failed.'))
                return redirect(_safe_order_url(order_obj))

            if merchantnumber and merchant_number and merchantnumber != merchant_number:
                logger.error('GPWebPay merchant number mismatch: expected %s got %s', merchant_number, merchantnumber)
                messages.error(request, _('Payment verification failed.'))
                return redirect(_safe_order_url(order_obj))

            response_params = {}
            for field in provider.response_digest_fields:
                value = all_params.get(field)
                if value not in (None, ''):
                    response_params[field] = value
            if 'OPERATION' not in response_params:
                response_params['OPERATION'] = operation or 'CREATE_ORDER'

            payment_obj.info = payment_obj.info or {}
            payment_obj.info['gpwebpay_raw'] = all_params
            payment_obj.save(update_fields=['info'])

            if public_key_data:
                if digest1:
                    response_digest = provider.build_response_digest1(response_params, merchant_number)
                    if not provider._verify_signature(response_digest, digest1, public_key_data):
                        logger.error('GPWebPay signature verification failed')
                        messages.error(request, _('Payment verification failed.'))
                        return redirect(_safe_order_url(order_obj))
                elif digest:
                    response_digest = provider.build_response_digest(response_params)
                    if not provider._verify_signature(response_digest, digest, public_key_data):
                        logger.error('GPWebPay signature verification failed')
                        messages.error(request, _('Payment verification failed.'))
                        return redirect(_safe_order_url(order_obj))
                else:
                    logger.error('GPWebPay response missing signature fields')
                    messages.error(request, _('Payment verification failed.'))
                    return redirect(_safe_order_url(order_obj))
            elif digest1 or digest:
                logger.warning('GPWebPay signature provided but public key not configured - skipping verification (less secure)')

            payment_obj.info['gpwebpay'] = {
                'operation': operation,
                'order_number': ordernumber,
                'prcode': prcode,
                'srcode': srcode,
                'resulttext': resulttext,
            }
            payment_obj.save(update_fields=['info'])

            if _is_success(prcode, srcode):
                if payment_obj.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                    try:
                        with scopes_disabled():
                            payment_obj.confirm()
                        logger.info(f'GPWebPay payment {payment} confirmed for order {order}')
                        messages.success(request, _('Payment successful!'))
                        return redirect(_safe_order_url(order_obj))
                    except Exception as e:
                        logger.error('GPWebPay confirm failed for order %s: %s', order, e, exc_info=True)
                        messages.error(request, str(e))
                        return redirect(_safe_order_url(order_obj))
                else:
                    return redirect(_safe_order_url(order_obj))
            else:
                error_msg = resulttext or _('Payment failed.')
                if payment_obj.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                    payment_obj.fail(info={'error': error_msg})
                    logger.warning(f'GPWebPay payment {payment} failed for order {order}: {error_msg}')
                messages.error(request, error_msg)
                return redirect(_safe_order_url(order_obj))

        except Exception as e:
            logger.error(f'Error processing GPWebPay return: {e}', exc_info=True)
            messages.error(request, _('An error occurred while processing your payment.'))
            try:
                return redirect(_safe_order_url(order_obj))
            except:
                return HttpResponseBadRequest('Error processing payment')


@method_decorator(csrf_exempt, name='dispatch')
class NotifyView(View):
    """
    Handle server-to-server notification (IPN) from GPWebPay payment gateway.
    
    Processes asynchronous payment notifications sent by GPWebPay to confirm
    payment status independently of user redirect.
    """

    def get(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_notification(request, order, payment, hash)

    def post(self, request: HttpRequest, order: str, payment: int, hash: str):
        return self._handle_notification(request, order, payment, hash)

    def _handle_notification(self, request: HttpRequest, order: str, payment: int, hash: str):
        """
        Process GPWebPay server notification.
        
        Verifies the notification signature, checks payment status codes,
        and updates the payment state. Returns HTTP 200 OK on success.
        
        Args:
            request: HTTP request containing GPWebPay notification parameters
            order: Order code
            payment: Payment ID
            hash: Order secret hash for validation
        """
        try:
            with scopes_disabled():
                payment_obj = get_object_or_404(
                    OrderPayment,
                    id=payment,
                    order__code=order,
                    order__secret=hash
                )
            order_obj = payment_obj.order
            event = order_obj.event

            # Get payment provider
            from pretix.base.models import Event
            provider = event.get_payment_providers().get('gpwebpay')
            if not provider:
                logger.error('GPWebPay provider not found')
                return HttpResponseBadRequest('Provider not configured')

            # Get settings
            settings_dict = provider.settings
            public_key_data = settings_dict.get('public_key', '')
            merchant_number = settings_dict.get('merchant_number', '')

            all_params = _collect_params(request)
            operation = all_params.get('OPERATION', '')
            ordernumber = all_params.get('ORDERNUMBER', '')
            merchantnumber = all_params.get('MERCHANTNUMBER', '')
            prcode = all_params.get('PRCODE', '')
            srcode = all_params.get('SRCODE', '')
            resulttext = all_params.get('RESULTTEXT', '')
            digest = all_params.get('DIGEST', '')
            digest1 = all_params.get('DIGEST1', '')
            if ' ' in digest or ' ' in digest1:
                digest = digest.replace(' ', '+')
                digest1 = digest1.replace(' ', '+')

            logger.info(
                'GPWebPay notify params: order=%s payment=%s op=%s pr=%s sr=%s state=%s',
                ordernumber, payment_obj.id, operation, prcode, srcode, payment_obj.state
            )

            if ordernumber and str(payment_obj.id) != ordernumber:
                logger.error('GPWebPay order number mismatch: expected %s got %s', payment_obj.id, ordernumber)
                return HttpResponseBadRequest('Invalid order number')

            if merchantnumber and merchant_number and merchantnumber != merchant_number:
                logger.error('GPWebPay merchant number mismatch: expected %s got %s', merchant_number, merchantnumber)
                return HttpResponseBadRequest('Invalid merchant number')

            response_params = {}
            for field in provider.response_digest_fields:
                value = all_params.get(field)
                if value not in (None, ''):
                    response_params[field] = value
            if 'OPERATION' not in response_params:
                response_params['OPERATION'] = operation or 'CREATE_ORDER'

            payment_obj.info = payment_obj.info or {}
            payment_obj.info['gpwebpay_raw'] = all_params
            payment_obj.save(update_fields=['info'])

            if public_key_data:
                if digest1:
                    response_digest = provider.build_response_digest1(response_params, merchant_number)
                    if not provider._verify_signature(response_digest, digest1, public_key_data):
                        logger.error('GPWebPay notification signature verification failed')
                        return HttpResponseBadRequest('Invalid signature')
                elif digest:
                    response_digest = provider.build_response_digest(response_params)
                    if not provider._verify_signature(response_digest, digest, public_key_data):
                        logger.error('GPWebPay notification signature verification failed')
                        return HttpResponseBadRequest('Invalid signature')
                else:
                    logger.error('GPWebPay notification missing signature fields')
                    return HttpResponseBadRequest('Invalid signature')
            elif digest1 or digest:
                logger.warning('GPWebPay notification signature provided but public key not configured - skipping verification (less secure)')

            payment_obj.info = payment_obj.info or {}
            payment_obj.info['gpwebpay'] = {
                'operation': operation,
                'order_number': ordernumber,
                'prcode': prcode,
                'srcode': srcode,
                'resulttext': resulttext,
            }
            payment_obj.save(update_fields=['info'])

            if _is_success(prcode, srcode):
                if payment_obj.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                    try:
                        with scopes_disabled():
                            payment_obj.confirm()
                        logger.info(f'GPWebPay payment {payment} confirmed via notification for order {order}')
                    except Exception as e:
                        logger.error('GPWebPay confirm failed for order %s: %s', order, e, exc_info=True)
                        return HttpResponseBadRequest('Confirm failed')
            else:
                if payment_obj.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                    payment_obj.fail(info={'error': resulttext or 'Payment failed'})
                    logger.warning(f'GPWebPay payment {payment} failed via notification for order {order}')

            return HttpResponse('OK')

        except Exception as e:
            logger.error(f'Error processing GPWebPay notification: {e}', exc_info=True)
            return HttpResponseBadRequest('Error processing notification')

