from django.urls import path

from bit_finance.views import test_expected_table_view, check_data_view, test_expected_bit_to_up_view

urlpatterns = [

    path('raw/', check_data_view),
    path('expected/up/', test_expected_table_view),
    path('expected/binance/', test_expected_bit_to_up_view)
]
