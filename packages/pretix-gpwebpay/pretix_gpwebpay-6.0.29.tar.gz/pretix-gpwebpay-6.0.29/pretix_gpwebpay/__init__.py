"""
GPWebPay payment provider plugin for Pretix.

This package provides integration with GPWebPay payment gateway for Pretix
event ticketing system.
"""
__version__ = '6.0.29'

# Import PretixPluginMeta from apps for entry point registration
from .apps import PluginApp

PretixPluginMeta = PluginApp.PretixPluginMeta

# Backward compatibility for older Pretix/Django that rely on default_app_config
default_app_config = 'pretix_gpwebpay.apps.PluginApp'
