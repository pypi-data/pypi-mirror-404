pretix-gpwebpay
================

GPWebPay payment provider plugin for Pretix.

This plugin provides full integration with the GPWebPay payment gateway for Pretix event ticketing system, implementing secure payment processing with RSA-SHA256 signature verification according to GPWebPay HTTP API specification v1.19.

Features
--------

- Full GPWebPay integration with PKI-based message signing
- Secure payment processing with RSA-SHA256 signatures
- Support for multiple currencies (CZK, EUR, USD, GBP, PLN, HUF)
- Server-to-server notifications (IPN)
- User redirect handling
- Test mode support
- WS API refunds (full and partial)
- Proper error handling and logging

Installation
------------

Install from PyPI::

    pip install pretix-gpwebpay

Or install from source::

    pip install -e /path/to/pretix-gpwebpay

Add the plugin to your Pretix configuration (``pretix.cfg``)::

    [pretix]
    plugins = pretix_gpwebpay

Restart your Pretix instance.

Configuration
-------------

1. Go to your event's payment settings in the Pretix control panel.
2. Enable the GPWebPay payment provider.
3. Configure the following settings:

   - **Merchant Number**: Your GPWebPay merchant number
   - **Private Key File**: Upload your GPWebPay private key file (.key or .pem format)
   - **Private Key Password**: Password for your private key (if required)
   - **GPWebPay Public Key File**: Upload GPWebPay's public key for signature verification (optional but recommended)
   - **Gateway URL**: GPWebPay gateway URL
     - Production: ``https://3dsecure.gpwebpay.com/pgw/order.do``
     - Test: Use the test gateway URL provided by GPWebPay
   - **WS API URL**: GPWebPay Web Services endpoint
     - Production: ``https://3dsecure.gpwebpay.com/pay-ws/v1/PaymentService``
     - Test: ``https://test.3dsecure.gpwebpay.com/pay-ws/v1/PaymentService``
   - **WS Provider ID**: 4-digit provider identifier required for the WS API
   - **Test Mode**: Enable for testing

Requirements
------------

- Pretix >= 4.0.0
- Python >= 3.8
- cryptography >= 3.0.0

Security
--------

This plugin implements GPWebPay's security requirements:

- All payment requests are signed using RSA-SHA256 with your private key
- All payment responses are verified using GPWebPay's public key (if provided)
- Private keys are stored securely in Pretix's configuration
- Message integrity is verified for all transactions

How It Works
------------

1. **Payment Initiation**: When a customer selects GPWebPay, they are redirected to the GPWebPay gateway with a signed payment request.

2. **Payment Processing**: The customer completes payment on GPWebPay's secure gateway.

3. **Return Handling**: After payment, the customer is redirected back to your Pretix instance, where the payment status is verified using GPWebPay's signature.

4. **Server Notification**: GPWebPay also sends a server-to-server notification to confirm the payment status.

Supported Currencies
---------------------

- CZK (Czech Koruna) - Code: 203
- EUR (Euro) - Code: 978
- USD (US Dollar) - Code: 840
- GBP (British Pound) - Code: 826
- PLN (Polish Zloty) - Code: 985
- HUF (Hungarian Forint) - Code: 348

Docker Installation
-------------------

You can install the plugin in a Dockerized Pretix environment::

    FROM pretix/standalone:stable
    USER root
    RUN pip3 install pretix-gpwebpay
    USER pretixuser
    RUN cd /pretix/src && make production

Troubleshooting
---------------

Payment Not Processing
^^^^^^^^^^^^^^^^^^^^^^

- Verify your merchant number is correct
- Check that private and public keys are properly uploaded
- Ensure the gateway URL is correct for your environment (test/production)
- Check Pretix logs for detailed error messages

Signature Verification Failures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Verify you're using the correct public key from GPWebPay
- Ensure private key password is correct (if required)
- Check that key files are in the correct format (PEM)

Currency Issues
^^^^^^^^^^^^^^^

- Verify your currency is supported
- Check that currency codes match GPWebPay's requirements

License
-------

Apache Software License 2.0

Support
-------

For issues related to:

- **Plugin functionality**: Check the Pretix documentation and plugin development guide
- **GPWebPay integration**: Refer to GPWebPay's integration documentation
- **Payment processing**: Contact GPWebPay support

References
----------

- `Pretix Plugin Development Guide <https://docs.pretix.eu/dev/development/api/index.html>`_
- GPWebPay HTTP API Documentation v1.19
- GPWebPay Private Key Management Documentation
