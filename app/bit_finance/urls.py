from django.urls import path

from bit_finance.views import test_expected_table_view, check_data_view

urlpatterns = [

    path('raw/', check_data_view),
    path('expected/', test_expected_table_view)
]
