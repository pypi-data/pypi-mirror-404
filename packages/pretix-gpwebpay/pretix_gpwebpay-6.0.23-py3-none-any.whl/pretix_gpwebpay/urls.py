"""
URL configuration for GPWebPay payment provider.

Defines routes for handling payment gateway callbacks:
- return: User redirect after payment completion
- notify: Server-to-server notification (IPN)
"""
from django.urls import path
from . import views

urlpatterns = [
    path('gpwebpay/redirect/<str:order>/<int:payment>/<str:hash>/', views.RedirectView.as_view(), name='redirect'),
    path('gpwebpay/return/<str:order>/<int:payment>/<str:hash>/', views.ReturnView.as_view(), name='return'),
    path('gpwebpay/notify/<str:order>/<int:payment>/<str:hash>/', views.NotifyView.as_view(), name='notify'),
]
