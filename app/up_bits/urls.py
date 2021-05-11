from django.contrib import admin
from django.urls import path, include

from up_bits.views import analytics_view, binance_buy_exchange_view

urlpatterns = [

    path('up/', analytics_view, ),
    path('binance/', binance_buy_exchange_view, )
]
