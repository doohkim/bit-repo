from django.urls import path

from up_bits.views import analytics_view, binance_buy_exchange_view, exchange_up_bit_multiple_result
from up_bits.views.exchange_binance_multi import exchange_binance_multiple_result

urlpatterns = [

    path('up/', analytics_view, ),
    path('up/multiple/', exchange_up_bit_multiple_result, ),
    path('binance/', binance_buy_exchange_view, ),
    path('binance/multiple/', exchange_binance_multiple_result),

]
