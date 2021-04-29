from django.shortcuts import render
import datetime
from datetime import timedelta

from bit_finance.models import BitFinanceExchange


def evaluation_index(request):
    date_time_now = datetime.datetime.now() + timedelta(hours=3) - timedelta(minutes=1)
    datetime_now_before_one_minute = datetime.datetime(date_time_now.year,
                                                       date_time_now.month,
                                                       date_time_now.day,
                                                       date_time_now.hour,
                                                       date_time_now.minute)
    bit_exchange_before_six_hours_age = BitFinanceExchange.objects.filter(
        candle_date_time_kst=datetime_now_before_one_minute
    )
    bit_exchange_before_six_hours_age