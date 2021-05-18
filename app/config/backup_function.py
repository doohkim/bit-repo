from datetime import timezone, datetime

import pytz
from django.db.models import Q

from config.global_variable import selected_coin_kind
from up_bits.models import UpBitMarket


def edit_6hours_data():
    date_time_now = timezone.now() + timezone.timedelta(hours=3) - timezone.timedelta(minutes=1)
    date_time_now_one_minute_ago = timezone.now() + timezone.timedelta(hours=9) - timezone.timedelta(minutes=1)
    datetime_now_before_one_minute = datetime.datetime(date_time_now_one_minute_ago.year,
                                                       date_time_now_one_minute_ago.month,
                                                       date_time_now_one_minute_ago.day,
                                                       date_time_now_one_minute_ago.hour,
                                                       date_time_now_one_minute_ago.minute, tzinfo=pytz.UTC)
    datetime_now_six_hours_ago = datetime.datetime(date_time_now.year,
                                                   date_time_now.month,
                                                   date_time_now.day,
                                                   date_time_now.hour,
                                                   date_time_now.minute, tzinfo=pytz.UTC)
    for coin_name in selected_coin_kind.values():

        market_obj = UpBitMarket.objects.get(coin=coin_name)
        up_obj = market_obj.upbitexchange_set.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
        )
        binance_obj = market_obj.bitfinanceexchange_set.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
        )

        up_bit_withdraw_fee = market_obj.up_bit_withdraw_fee
        binance_withdraw_fee = market_obj.binance_withdraw_fee

        for u_obj, b_obj in zip(up_obj, binance_obj):
            # 비트코인 시세
            up_bit_coin_value = u_obj.bit_coin_value
            binance_bit_coin_value = b_obj.bit_coin_value

            # 거래 수수로율
            binance_percentage = 0.999
            up_percentage = 0.9975

            # 매수가
            binance_close_price = b_obj.close_price
            up_close_price = u_obj.close_price
            # 당초 BTC 보유량
            up_init_have_btc_amount = 300000 / up_bit_coin_value
            binance_init_have_btc_amount = 300000 / binance_bit_coin_value
            # ALT 매수량 = 당초 BTC 보유량 * (1-거래수수료율) / 매수가
            up_alt_purchase_price = up_init_have_btc_amount * up_percentage / up_close_price
            binance_alt_purchase_price = binance_init_have_btc_amount * binance_percentage / binance_close_price

            # ALT입금량
            up_alt_deposit_amount = up_alt_purchase_price - up_bit_withdraw_fee
            binance_alt_deposit_amount = binance_alt_purchase_price - binance_withdraw_fee
            # ALT입금량 * (1-거래수수료율) * 매도가
            up_final_have_btc_coin = up_alt_deposit_amount * binance_percentage * binance_close_price
            binance_final_have_btc_coin = binance_alt_deposit_amount * up_percentage * up_close_price
            # ((최종BTC 보유량 / 당초BTC보유량) -1) *100
            up_expected_revenue_rate = ((up_final_have_btc_coin / up_init_have_btc_amount) - 1) * 100
            binance_expected_revenue_rate = ((binance_final_have_btc_coin / binance_init_have_btc_amount) - 1) * 100

            u_obj.expected_revenue_rate = up_expected_revenue_rate
            b_obj.expected_revenue_rate = binance_expected_revenue_rate
            u_obj.save()
            b_obj.save()
    return zip(b_obj, u_obj)
