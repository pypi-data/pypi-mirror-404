"""
GPWebPay payment provider for Pretix.

This module implements the GPWebPay payment gateway integration for Pretix,
providing secure payment processing with RSA-SHA256 signature verification
according to GPWebPay HTTP API specification v1.19.
"""
import base64
import logging
import os
from collections import OrderedDict
from decimal import Decimal
import urllib.request
import urllib.error
from typing import Dict, Iterable, Optional
from uuid import uuid4
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from django import forms
from django.http import HttpRequest
from django.urls import reverse
from django.conf import settings as django_settings
from django.utils.html import format_html
from django.middleware.csrf import get_token
from django.utils.translation import gettext_lazy as _
from pretix.base.models import OrderPayment, OrderRefund
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.control.forms import ExtFileField

logger = logging.getLogger(__name__)


class GPWebPaySettingsForm(forms.Form):
    """
    Configuration form for GPWebPay payment provider settings.
    
    Collects merchant credentials, key files, and gateway configuration
    required for GPWebPay payment processing.
    """
    merchant_number = forms.CharField(
        label=_('Merchant Number'),
        help_text=_('Your GPWebPay merchant number'),
        required=True,
        max_length=20,
    )
    private_key = ExtFileField(
        label=_('Private Key File'),
        help_text=_('Upload your GPWebPay private key file (.key or .pem format)'),
        required=True,
        ext_whitelist=('.key', '.pem', '.txt', '.der'),
    )
    private_key_password = forms.CharField(
        label=_('Private Key Password'),
        help_text=_('Password for your private key file'),
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    public_key = ExtFileField(
        label=_('GPWebPay Public Key File (Optional)'),
        help_text=_('Upload the GPWebPay public key file for signature verification. If not provided, signature verification will be skipped (less secure).'),
        required=False,
        ext_whitelist=('.key', '.pem', '.txt', '.cer', '.crt', '.cert', '.der'),
    )
    gateway_url = forms.URLField(
        label=_('Gateway URL'),
        help_text=_('Optional production gateway URL. Leave empty to use the default.'),
        required=False,
        initial='https://3dsecure.gpwebpay.com/pgw/order.do',
    )
    ws_url = forms.URLField(
        label=_('WS API URL'),
        help_text=_('Optional production WS endpoint. Leave empty to use the default.'),
        required=False,
        initial='https://3dsecure.gpwebpay.com/pay-ws/v1/PaymentService',
    )
    ws_provider = forms.CharField(
        label=_('WS Provider ID'),
        help_text=_('Payment service provider identifier (4 digits) for GPWebPay WS API'),
        required=True,
        max_length=4,
    )
    deposit_flag = forms.ChoiceField(
        label=_('Deposit flag'),
        help_text=_('Choose immediate capture (1) or authorization-only (0).'),
        required=True,
        choices=(('1', _('Capture immediately')), ('0', _('Authorize only'))),
        initial='1',
    )
    language = forms.CharField(
        label=_('Gateway language (optional)'),
        help_text=_('ISO 639-1 language code for GPWebPay (e.g., en, cs). Leave empty to use browser language.'),
        required=False,
        max_length=5,
    )
    paymethod = forms.CharField(
        label=_('Pay method (optional)'),
        help_text=_('GPWebPay PAYMETHOD code (e.g., CRD, GPAY, APAY, APM-BTR, PAYPAL).'),
        required=False,
        max_length=20,
    )
    paymethods = forms.CharField(
        label=_('Pay methods restriction (optional)'),
        help_text=_('GPWebPay PAYMETHODS restriction string.'),
        required=False,
        max_length=100,
    )
    addinfo = forms.CharField(
        label=_('ADDINFO payload (optional)'),
        help_text=_('Additional info XML sent as ADDINFO (kept as-is, tabs/CR/LF removed).'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
    )
    send_reference_number = forms.BooleanField(
        label=_('Send reference number'),
        help_text=_('Send order code as REFERENCENUMBER when allowed.'),
        required=False,
        initial=True,
    )
    test_mode = forms.BooleanField(
        label=_('Test mode'),
        help_text=_('Enable test mode for development'),
        required=False,
        initial=False,
    )


class GPWebPay(BasePaymentProvider):
    """
    GPWebPay payment provider implementation for Pretix.
    
    Handles payment processing, signature generation, and verification
    according to GPWebPay HTTP API specification v1.19.
    """
    identifier = 'gpwebpay'
    verbose_name = _('GPWebPay')
    public_name = _('GPWebPay')
    abort_pending_allowed = True
    execute_payment_needs_user = True
    PROD_GATEWAY_URL = 'https://3dsecure.gpwebpay.com/pgw/order.do'
    TEST_GATEWAY_URL = 'https://test.3dsecure.gpwebpay.com/pgw/order.do'
    PROD_WS_URL = 'https://3dsecure.gpwebpay.com/pay-ws/v1/PaymentService'
    TEST_WS_URL = 'https://test.3dsecure.gpwebpay.com/pay-ws/v1/PaymentService'

    request_digest_fields = [
        'MERCHANTNUMBER',
        'OPERATION',
        'ORDERNUMBER',
        'AMOUNT',
        'CURRENCY',
        'DEPOSITFLAG',
        'MERORDERNUM',
        'URL',
        'DESCRIPTION',
        'MD',
        'PAYMETHOD',
        'PAYMETHODS',
        'EMAIL',
        'REFERENCENUMBER',
        'ADDINFO',
    ]
    response_digest_fields = [
        'OPERATION',
        'ORDERNUMBER',
        'MERORDERNUM',
        'MD',
        'PRCODE',
        'SRCODE',
        'RESULTTEXT',
        'ADDINFO',
        'TOKEN',
        'EXPIRY',
        'ACSRES',
        'ACCODE',
        'PANPATTERN',
        'DAYTOCAPTURE',
        'TOKENREGSTATUS',
        'ACRC',
        'RRN',
        'PAR',
        'TRACEID',
    ]

    @property
    def settings_form_fields(self):
        # Preserve default fields (_enabled, fees, availability, etc.) and add ours
        fields = OrderedDict(super().settings_form_fields)
        fields.update(GPWebPaySettingsForm.base_fields)
        return fields

    def settings_form_clean(self, cleaned_data):
        """
        Process file uploads and store them as strings.
        
        Pretix's ExtFileField returns a file object that needs to be
        converted to a string for storage in the settings.
        """
        if 'private_key' in cleaned_data and cleaned_data['private_key']:
            file = cleaned_data['private_key']
            if hasattr(file, 'read'):
                file.seek(0)
                try:
                    cleaned_data['private_key'] = file.read().decode('utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    import base64
                    cleaned_data['private_key'] = base64.b64encode(file.read()).decode('utf-8')
                file.seek(0)
        elif not cleaned_data.get('private_key'):
            stored_key = self.settings.get('private_key')
            if stored_key:
                cleaned_data['private_key'] = stored_key

        if 'public_key' in cleaned_data and cleaned_data['public_key']:
            file = cleaned_data['public_key']
            if hasattr(file, 'read'):
                file.seek(0)
                try:
                    cleaned_data['public_key'] = file.read().decode('utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    import base64
                    cleaned_data['public_key'] = base64.b64encode(file.read()).decode('utf-8')
                file.seek(0)
        elif not cleaned_data.get('public_key'):
            stored_key = self.settings.get('public_key')
            if stored_key:
                cleaned_data['public_key'] = stored_key

        return cleaned_data

    def settings_content_render(self, request):
        return """
        <p>Configure your GPWebPay payment gateway settings.</p>
        <p>You need to:</p>
        <ul>
            <li>Obtain your merchant number from GPWebPay</li>
            <li>Upload your private key file (used for signing requests)</li>
            <li>Upload GPWebPay's public key file (optional - used for verifying responses)</li>
            <li>Test mode automatically switches to GPWebPay test endpoints</li>
            <li>Configure the production gateway URL and WS API URL</li>
        </ul>
        <p><strong>Note:</strong> If you don't have GPWebPay's public key, signature verification will be skipped. 
        This is less secure but payments will still work. It's recommended to obtain the public key from GPWebPay support.</p>
        """

    def payment_form_render(self, request, total: Decimal, order=None) -> str:
        """
        Render payment form HTML.
        
        For GPWebPay, customers are redirected immediately to the gateway,
        so no form is displayed.
        """
        return format_html(
            "<p>{}</p>",
            _('You will be redirected to the GPWebPay secure payment gateway to complete your payment.')
        )

    def checkout_confirm_render(self, request, order=None, info_data: dict = None) -> str:
        """
        Render checkout confirmation page HTML.
        
        Displays information about the GPWebPay payment method and
        informs customers they will be redirected to the gateway.
        """
        return format_html(
            "<p><strong>{}</strong></p><p>{}</p>",
            _('GPWebPay Payment'),
            _('You will be redirected to the GPWebPay secure payment gateway to complete your payment.')
        )

    @property
    def test_mode_message(self):
        if self.settings.get('test_mode'):
            return _('GPWebPay is running in test mode; no real money will be moved.')
        return None

    def payment_is_valid_session(self, request):
        """
        Validate payment session.
        
        Returns True as GPWebPay redirects immediately to the gateway
        without requiring session validation.
        """
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment) -> Optional[str]:
        """
        Execute the payment by redirecting to a local view that renders
        the GPWebPay POST form.
        """
        order = payment.order
        if payment.state == OrderPayment.PAYMENT_STATE_CREATED:
            payment.state = OrderPayment.PAYMENT_STATE_PENDING
            payment.save(update_fields=['state'])
        return request.build_absolute_uri(
            reverse('plugins:pretix_gpwebpay:redirect', kwargs={
                'order': order.code,
                'payment': payment.id,
                'hash': payment.order.secret
            })
        )

    def get_gateway_url(self) -> str:
        settings_dict = self.settings
        if settings_dict.get('test_mode'):
            return self.TEST_GATEWAY_URL
        return settings_dict.get('gateway_url') or self.PROD_GATEWAY_URL

    def get_ws_url(self) -> str:
        settings_dict = self.settings
        if settings_dict.get('test_mode'):
            return self.TEST_WS_URL
        return settings_dict.get('ws_url') or self.PROD_WS_URL

    def build_request_params(self, request: HttpRequest, payment: OrderPayment) -> Dict[str, str]:
        order = payment.order
        settings_dict = self.settings
        merchant_number = settings_dict.get('merchant_number', '')
        private_key_data = settings_dict.get('private_key', '')
        private_key_password = settings_dict.get('private_key_password', '')

        if not merchant_number or not private_key_data:
            raise PaymentException(_('GPWebPay is not configured properly.'))

        description = self._sanitize_description(f'Order {order.code}')
        md_value = self._to_ascii(str(payment.id)).strip()
        currency = getattr(order, 'currency', None)
        if not currency and getattr(order, 'event', None):
            currency = getattr(order.event, 'currency', None)
        params = {
            'MERCHANTNUMBER': merchant_number,
            'OPERATION': 'CREATE_ORDER',
            'ORDERNUMBER': str(payment.id),
            'AMOUNT': str(int(payment.amount * 100)),
            'CURRENCY': self._get_currency_code(currency or ''),
            'DEPOSITFLAG': settings_dict.get('deposit_flag', '1'),
            'URL': request.build_absolute_uri(
                reverse('plugins:pretix_gpwebpay:return', kwargs={
                    'order': order.code,
                    'payment': payment.id,
                    'hash': payment.order.secret
                })
            ),
            'DESCRIPTION': description,
            'MD': md_value,
        }
        if order.email:
            params['EMAIL'] = order.email
        paymethod = (settings_dict.get('paymethod') or '').strip()
        if paymethod:
            params['PAYMETHOD'] = paymethod
        paymethods = (settings_dict.get('paymethods') or '').strip()
        if paymethods:
            params['PAYMETHODS'] = paymethods
        lang = self._get_lang_code(request, settings_dict.get('language'))
        if lang:
            params['LANG'] = lang
        if settings_dict.get('send_reference_number', True):
            reference_number = self._reference_number_from_order(order.code)
            if reference_number:
                params['REFERENCENUMBER'] = reference_number
        addinfo = self._sanitize_addinfo(settings_dict.get('addinfo'))
        if addinfo:
            params['ADDINFO'] = addinfo

        try:
            digest = self._generate_digest(params, self.request_digest_fields)
            signature = self._sign_message(digest, private_key_data, private_key_password)
            params['DIGEST'] = signature
        except Exception as e:
            logger.error(f'GPWebPay signing error: {e}', exc_info=True)
            raise PaymentException(_('Error preparing payment request.'))

        return params

    def build_response_digest(self, params: Dict[str, str]) -> str:
        return self._generate_digest(params, self.response_digest_fields)

    def build_response_digest1(self, params: Dict[str, str], merchant_number: str) -> str:
        digest = self.build_response_digest(params)
        if not merchant_number:
            return digest
        if digest:
            return f"{digest}|{merchant_number}"
        return merchant_number

    def payment_refund_supported(self, payment: OrderPayment) -> bool:
        return self._ws_configured()

    def payment_partial_refund_supported(self, payment: OrderPayment) -> bool:
        return self._ws_configured()

    def execute_refund(self, refund: OrderRefund):
        settings_dict = self.settings
        ws_url = self.get_ws_url()
        provider_id = settings_dict.get('ws_provider', '')
        merchant_number = settings_dict.get('merchant_number', '')
        private_key_data = settings_dict.get('private_key', '')
        private_key_password = settings_dict.get('private_key_password', '')
        public_key_data = settings_dict.get('public_key', '')

        if not ws_url or not provider_id or not merchant_number or not private_key_data:
            raise PaymentException(_('GPWebPay WS refund is not configured properly.'))

        payment = refund.payment
        if not payment:
            raise PaymentException(_('GPWebPay refund requires an original payment.'))

        message_id = self._generate_message_id()
        amount = str(int(refund.amount * 100))
        info = payment.info if isinstance(payment.info, dict) else {}
        payment_number = str((info.get('gpwebpay') or {}).get('order_number') or payment.id)

        digest = self._generate_digest({
            'messageId': message_id,
            'provider': provider_id,
            'merchantNumber': merchant_number,
            'paymentNumber': payment_number,
            'amount': amount,
        }, ['messageId', 'provider', 'merchantNumber', 'paymentNumber', 'amount'])
        signature = self._sign_message(digest, private_key_data, private_key_password)

        body = (
            '<v1:processRefund>'
            '<v1:refundRequest>'
            f'<type:messageId>{message_id}</type:messageId>'
            f'<type:provider>{provider_id}</type:provider>'
            f'<type:merchantNumber>{merchant_number}</type:merchantNumber>'
            f'<type:paymentNumber>{payment_number}</type:paymentNumber>'
            f'<type:amount>{amount}</type:amount>'
            f'<type:signature>{signature}</type:signature>'
            '</v1:refundRequest>'
            '</v1:processRefund>'
        )

        response_xml = self._ws_call(ws_url, body, 'processRefund')
        response_data, response_digest = self._parse_ws_response_with_digest(response_xml, 'refundRequestResponse')

        response_signature = response_data.get('signature', '')
        if public_key_data and response_signature:
            if not self._verify_signature(response_digest, response_signature, public_key_data):
                raise PaymentException(_('GPWebPay refund signature verification failed.'))
        elif public_key_data and not response_signature:
            raise PaymentException(_('GPWebPay refund response missing signature.'))

        refund.info = refund.info or {}
        refund.info['gpwebpay'] = {
            'message_id': response_data.get('messageId'),
            'state': response_data.get('state'),
            'status': response_data.get('status'),
            'sub_status': response_data.get('subStatus'),
        }
        refund.save(update_fields=['info'])
        refund.done()

    def refund_control_render(self, request, refund: OrderRefund):
        info = (refund.info or {}).get('gpwebpay', {})
        if not info:
            return ''
        return f"""
        <dl class="dl-horizontal">
            <dt>{_('WS Message ID')}</dt>
            <dd>{info.get('message_id', '')}</dd>
            <dt>{_('WS Status')}</dt>
            <dd>{info.get('status', '')}</dd>
            <dt>{_('WS Substatus')}</dt>
            <dd>{info.get('sub_status', '')}</dd>
        </dl>
        """

    def _ws_configured(self) -> bool:
        settings_dict = self.settings
        return bool(
            self.get_ws_url()
            and settings_dict.get('ws_provider')
            and settings_dict.get('merchant_number')
            and settings_dict.get('private_key')
        )

    def _generate_message_id(self) -> str:
        return uuid4().hex

    def _ws_call(self, ws_url: str, body: str, action: str) -> str:
        envelope = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://gpe.cz/pay/pay-ws/proc/v1" '
            'xmlns:type="http://gpe.cz/pay/pay-ws/proc/v1/type">'
            '<soapenv:Header/>'
            '<soapenv:Body>'
            f'{body}'
            '</soapenv:Body>'
            '</soapenv:Envelope>'
        )

        logger.debug('GPWebPay WS request %s (action=%s)', ws_url, action)
        request = urllib.request.Request(
            ws_url,
            data=envelope.encode('utf-8'),
            headers={
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': action,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode('utf-8')
            except Exception:
                body = ''
            if body:
                logger.error('GPWebPay WS HTTP error %s, returning SOAP fault body', e.code)
                return body
            logger.error('GPWebPay WS HTTP error: %s', e, exc_info=True)
            raise PaymentException(_('GPWebPay WS request failed.'))
        except Exception as e:
            logger.error('GPWebPay WS request failed: %s', e, exc_info=True)
            raise PaymentException(_('GPWebPay WS request failed.'))

    def _parse_ws_response(self, xml_payload: str, response_tag: str) -> Dict[str, str]:
        try:
            root = ET.fromstring(xml_payload)
        except ET.ParseError as e:
            logger.error('GPWebPay WS response parse error: %s', e, exc_info=True)
            raise PaymentException(_('GPWebPay WS response parse failed.'))

        fault = self._find_xml_text(root, 'faultstring')
        if fault:
            detail = self._parse_ws_fault_detail(root)
            detail_msg = ''
            if detail:
                detail_msg = f" (PRCODE={detail.get('primaryReturnCode')}, SRCODE={detail.get('secondaryReturnCode')})"
            logger.error('GPWebPay WS SOAP fault: %s%s', fault, detail_msg)
            raise PaymentException(f"{fault}{detail_msg}")

        response_node = self._find_xml_node(root, response_tag)
        if response_node is None:
            logger.error('GPWebPay WS response missing %s', response_tag)
            raise PaymentException(_('GPWebPay WS response was invalid.'))

        data = {}
        for field in ('messageId', 'state', 'status', 'subStatus', 'signature'):
            value = self._find_xml_text(response_node, field)
            if value not in (None, ''):
                data[field] = value
        return data

    def _parse_ws_response_with_digest(self, xml_payload: str, response_tag: str) -> (Dict[str, str], str):
        try:
            root = ET.fromstring(xml_payload)
        except ET.ParseError as e:
            logger.error('GPWebPay WS response parse error: %s', e, exc_info=True)
            raise PaymentException(_('GPWebPay WS response parse failed.'))

        fault = self._find_xml_text(root, 'faultstring')
        if fault:
            detail = self._parse_ws_fault_detail(root)
            detail_msg = ''
            if detail:
                detail_msg = f" (PRCODE={detail.get('primaryReturnCode')}, SRCODE={detail.get('secondaryReturnCode')})"
            logger.error('GPWebPay WS SOAP fault: %s%s', fault, detail_msg)
            raise PaymentException(f"{fault}{detail_msg}")

        response_node = self._find_xml_node(root, response_tag)
        if response_node is None:
            logger.error('GPWebPay WS response missing %s', response_tag)
            raise PaymentException(_('GPWebPay WS response was invalid.'))

        data: Dict[str, str] = {}
        digest_parts = []
        for child in list(response_node):
            local_name = child.tag.split('}', 1)[-1] if '}' in child.tag else child.tag
            text = (child.text or '').strip() if child.text is not None else None
            if local_name == 'signature':
                if text is not None:
                    data['signature'] = text
                continue
            if text is None:
                continue
            data[local_name] = text
            digest_parts.append(text)

        return data, '|'.join(digest_parts)

    def _parse_ws_fault_detail(self, root: ET.Element) -> Dict[str, str]:
        detail_node = self._find_xml_node(root, 'detail')
        if detail_node is None:
            return {}
        data = {}
        for field in ('primaryReturnCode', 'secondaryReturnCode', 'messageId'):
            value = self._find_xml_text(detail_node, field)
            if value not in (None, ''):
                data[field] = value
        return data

    def _find_xml_text(self, node: ET.Element, local_name: str) -> Optional[str]:
        element = self._find_xml_node(node, local_name)
        if element is None or element.text is None:
            return None
        return element.text.strip()

    def _find_xml_node(self, node: ET.Element, local_name: str) -> Optional[ET.Element]:
        for child in node.iter():
            if child.tag.endswith(f'}}{local_name}') or child.tag == local_name:
                return child
        return None

    def _get_currency_code(self, currency: str) -> str:
        """
        Convert ISO 4217 currency code to GPWebPay numeric format.
        
        Args:
            currency: ISO 4217 currency code (e.g., 'EUR', 'USD')
            
        Returns:
            GPWebPay numeric currency code (defaults to EUR if not found)
        """
        currency_map = {
            'CZK': '203',
            'EUR': '978',
            'USD': '840',
            'GBP': '826',
            'PLN': '985',
            'HUF': '348',
        }
        return currency_map.get(currency.upper(), '978')

    def _generate_digest(self, params: Dict[str, str], fields: Iterable[str]) -> str:
        """
        Generate digest string from parameters according to GPWebPay specification.
        
        The digest format is: MERCHANTNUMBER|OPERATION|ORDERNUMBER|AMOUNT|CURRENCY|
        DEPOSITFLAG|MERORDERNUM|URL|DESCRIPTION|MD
        
        Args:
            params: Dictionary of payment parameters
            
        Returns:
            Digest string with parameters joined by pipe character
        """
        digest_parts = []
        for field in fields:
            if field in params and params[field] not in (None, ''):
                digest_parts.append(str(params[field]))
        return '|'.join(digest_parts)

    def _to_ascii(self, value: str) -> str:
        try:
            import unicodedata
            return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        except Exception:
            return value

    def _sanitize_description(self, description: str) -> str:
        description = self._to_ascii(description).strip()
        return description[:255]

    def _sanitize_addinfo(self, addinfo: Optional[str]) -> Optional[str]:
        if not addinfo:
            return None
        cleaned = addinfo.replace('\r', '').replace('\n', '').replace('\t', '').strip()
        return cleaned or None

    def _get_lang_code(self, request: HttpRequest, configured: Optional[str]) -> Optional[str]:
        if configured:
            return configured.strip().lower()[:5]
        lang = getattr(request, 'LANGUAGE_CODE', '') or ''
        if not lang:
            return None
        return lang.split('-', 1)[0].lower()

    def _reference_number_from_order(self, order_code: str) -> Optional[str]:
        import re
        if re.match(r'^[ #$*+,-./0-9:;=@A-Z^_a-z]+$', order_code):
            return order_code
        return None

    def _sign_message(self, message: str, private_key_data: str, password: Optional[str] = None) -> str:
        """
        Sign a message using RSA private key with SHA-1.
        
        Implements GPWebPay specification: RSA-SHA1 with PKCS1v15 padding.
        The private key must be in PEM format.
        
        Args:
            message: Message to sign
            private_key_data: Private key in PEM format (may be base64-encoded)
            password: Optional password for encrypted private key
            
        Returns:
            Base64-encoded signature
            
        Raises:
            Exception: If key loading or signing fails
        """
        try:
            private_key = self._load_private_key(private_key_data, password)

            signature = private_key.sign(
                message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA1()
            )

            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            logger.error(f'Error signing message: {e}', exc_info=True)
            raise

    def _verify_signature(self, message: str, signature: str, public_key_data: str) -> bool:
        """
        Verify a signature using RSA public key with SHA-1.
        
        Implements GPWebPay specification: RSA-SHA1 with PKCS1v15 padding.
        The public key must be in PEM format.
        
        Args:
            message: Original message that was signed
            signature: Base64-encoded signature to verify
            public_key_data: Public key in PEM format (may be base64-encoded)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            public_key = self._load_public_key(public_key_data)
            signature_bytes = base64.b64decode(signature)

            public_key.verify(
                signature_bytes,
                message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA1()
            )
            return True
        except Exception as e:
            logger.error(f'Error verifying signature: {e}', exc_info=True)
            return False

    def _load_private_key(self, private_key_data: str, password: Optional[str]):
        import base64

        if not private_key_data:
            raise ValueError('Private key data is empty')

        data = private_key_data.strip()
        password_bytes = password.encode('utf-8') if password else None
        if 'BEGIN CERTIFICATE' in data:
            raise ValueError('Provided private key appears to be a certificate')

        def _looks_like_base64(value: str) -> bool:
            if len(value) < 32:
                return False
            for ch in value:
                if ch.isalnum() or ch in '+/=\n\r':
                    continue
                return False
            return True

        def _decode_base64(value: str) -> bytes:
            cleaned = ''.join(value.split())
            padding = '=' * (-len(cleaned) % 4)
            return base64.b64decode(cleaned + padding)

        def _try_load(key_bytes: bytes):
            try:
                return serialization.load_pem_private_key(key_bytes, password=password_bytes)
            except Exception:
                return serialization.load_der_private_key(key_bytes, password=password_bytes)

        if data.startswith('-----BEGIN'):
            return _try_load(data.encode('utf-8'))

        key_path = self._resolve_key_path(data)
        if key_path:
            with open(key_path, 'rb') as f:
                return _try_load(f.read())

        if _looks_like_base64(data):
            try:
                decoded = _decode_base64(data)
                return _try_load(decoded)
            except Exception:
                pass

        return _try_load(data.encode('utf-8'))

    def _load_public_key(self, public_key_data: str):
        import base64

        if not public_key_data:
            raise ValueError('Public key data is empty')

        data = public_key_data.strip()

        def _looks_like_base64(value: str) -> bool:
            if len(value) < 32:
                return False
            for ch in value:
                if ch.isalnum() or ch in '+/=\n\r':
                    continue
                return False
            return True

        def _decode_base64(value: str) -> bytes:
            cleaned = ''.join(value.split())
            padding = '=' * (-len(cleaned) % 4)
            return base64.b64decode(cleaned + padding)

        def _try_load(key_bytes: bytes):
            try:
                return serialization.load_pem_public_key(key_bytes)
            except Exception:
                try:
                    return serialization.load_der_public_key(key_bytes)
                except Exception:
                    return x509.load_pem_x509_certificate(key_bytes).public_key()

        if data.startswith('-----BEGIN'):
            return _try_load(data.encode('utf-8'))

        key_path = self._resolve_key_path(data)
        if key_path:
            with open(key_path, 'rb') as f:
                return _try_load(f.read())

        if _looks_like_base64(data):
            try:
                decoded = _decode_base64(data)
                try:
                    return _try_load(decoded)
                except Exception:
                    return x509.load_der_x509_certificate(decoded).public_key()
            except Exception:
                pass

        return _try_load(data.encode('utf-8'))

    def _resolve_key_path(self, value: str) -> Optional[str]:
        if not value:
            return None
        if value.startswith('file://'):
            value = value[7:]
        if os.path.isabs(value) and os.path.exists(value):
            return value
        candidates = []
        media_root = getattr(django_settings, 'MEDIA_ROOT', None)
        if media_root:
            candidates.append(media_root)
        data_dir = getattr(django_settings, 'DATA_DIR', None)
        if data_dir:
            candidates.append(data_dir)
        candidates.append('/data')
        for base in candidates:
            path = os.path.join(base, value)
            if os.path.exists(path):
                return path
        return None

    def payment_pending_render(self, request, payment: OrderPayment):
        """
        Render HTML for pending payment status.
        
        Args:
            request: HTTP request object
            payment: OrderPayment instance
            
        Returns:
            HTML string to display while payment is pending
        """
        return format_html(
            "<p>{}</p><p>{}</p>",
            _('Your payment is being processed.'),
            _('Please wait...')
        )

    def payment_control_render(self, request, payment: OrderPayment):
        """
        Render payment information in the control panel.
        
        Args:
            request: HTTP request object
            payment: OrderPayment instance
            
        Returns:
            HTML string displaying payment details
        """
        info = payment.info if hasattr(payment, 'info') and isinstance(payment.info, dict) else {}
        ws_info = info.get('gpwebpay_ws', {})
        sync_form = ""
        if self._ws_configured():
            sync_url = reverse('plugins:pretix_gpwebpay:sync', kwargs={
                'order': payment.order.code,
                'payment': payment.id,
                'hash': payment.order.secret
            })
            token = get_token(request)
            sync_form = f"""
            <form method="post" action="{sync_url}" style="margin-top: 10px;">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">
                <button type="submit" class="btn btn-default">{_('Sync status from GPWebPay')}</button>
            </form>
            """
        return f"""
        <dl class="dl-horizontal">
            <dt>{_('Payment ID')}</dt>
            <dd>{payment.id}</dd>
            <dt>{_('Status')}</dt>
            <dd>{payment.state}</dd>
            <dt>{_('WS Status')}</dt>
            <dd>{ws_info.get('status', '')}</dd>
            <dt>{_('WS Substatus')}</dt>
            <dd>{ws_info.get('sub_status', '')}</dd>
        </dl>
        {sync_form}
        """

    def sync_payment_from_ws(self, payment: OrderPayment) -> str:
        settings_dict = self.settings
        ws_url = self.get_ws_url()
        provider_id = settings_dict.get('ws_provider', '')
        merchant_number = settings_dict.get('merchant_number', '')
        private_key_data = settings_dict.get('private_key', '')
        private_key_password = settings_dict.get('private_key_password', '')
        public_key_data = settings_dict.get('public_key', '')

        if not ws_url or not provider_id or not merchant_number or not private_key_data:
            raise PaymentException(_('GPWebPay WS is not configured properly.'))

        message_id = self._generate_message_id()
        payment_number = str(payment.id)

        digest = self._generate_digest({
            'messageId': message_id,
            'provider': provider_id,
            'merchantNumber': merchant_number,
            'paymentNumber': payment_number,
        }, ['messageId', 'provider', 'merchantNumber', 'paymentNumber'])
        signature = self._sign_message(digest, private_key_data, private_key_password)

        body = (
            '<v1:getPaymentDetail>'
            '<v1:paymentDetailRequest>'
            f'<type:messageId>{message_id}</type:messageId>'
            f'<type:provider>{provider_id}</type:provider>'
            f'<type:merchantNumber>{merchant_number}</type:merchantNumber>'
            f'<type:paymentNumber>{payment_number}</type:paymentNumber>'
            f'<type:signature>{signature}</type:signature>'
            '</v1:paymentDetailRequest>'
            '</v1:getPaymentDetail>'
        )

        response_xml = self._ws_call(ws_url, body, 'getPaymentDetail')
        response_data, response_digest = self._parse_ws_response_with_digest(response_xml, 'paymentDetailResponse')

        response_signature = response_data.get('signature', '')
        if public_key_data and response_signature:
            if not self._verify_signature(response_digest, response_signature, public_key_data):
                raise PaymentException(_('GPWebPay WS signature verification failed.'))
        elif public_key_data and not response_signature:
            raise PaymentException(_('GPWebPay WS response missing signature.'))

        status = (response_data.get('status') or '').upper()
        sub_status = (response_data.get('subStatus') or '').upper()

        info = payment.info if isinstance(payment.info, dict) else {}
        info['gpwebpay_ws'] = {
            'message_id': response_data.get('messageId'),
            'state': response_data.get('state'),
            'status': status,
            'sub_status': sub_status,
        }
        payment.info = info
        payment.save(update_fields=['info'])

        success_statuses = {
            'PENDING_CAPTURE',
            'PENDING_SETTLEMENT',
            'PROCESSED',
            'CAPTURED',
            'PENDING_ADJUSTMENT',
            'PARTIAL_PAYMENT',
            'VALID',
        }
        pending_statuses = {
            'PENDING_AUTHORIZATION',
            'CREATED',
        }
        failed_statuses = {
            'UNPAID',
            'EXPIRED',
            'CANCELED',
            'BLOCKED',
            'REVERSED',
            'REFUNDED',
            'CANCELED_BY_MERCHANT',
            'CANCELED_BY_ISSUER',
            'CANCELED_BY_CARDHOLDER',
            'EXPIRED_CARD',
            'EXPIRED_NO_PAYMENT',
        }

        if status in success_statuses:
            if payment.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                payment.confirm()
                return 'confirmed'
            return 'already_confirmed'
        if status in failed_statuses:
            if payment.state in (OrderPayment.PAYMENT_STATE_PENDING, OrderPayment.PAYMENT_STATE_CREATED):
                payment.fail(info={'error': f'WS status {status}'})
                return 'failed'
            return 'already_failed'
        if status in pending_statuses:
            return 'pending'
        return 'unknown'
