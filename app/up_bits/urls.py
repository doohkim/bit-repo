from django.urls import path

from up_bits.views import analytics_view, binance_buy_exchange_view, exchange_up_bit_multiple_result, \
    exchange_binance_multiple_result, personal_from_binance_to_up, personal_from_up_to_binance

urlpatterns = [

    path('up/', analytics_view, ),
    path('up/multiple/', exchange_up_bit_multiple_result, ),
    path('binance/', binance_buy_exchange_view, ),
    path('binance/multiple/', exchange_binance_multiple_result),
    path('personal/binance/', personal_from_binance_to_up),
    path('personal/up/', personal_from_up_to_binance),

]
