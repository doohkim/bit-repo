from django.utils import timezone

import datetime
from datetime import timedelta
import pytz

from bit_finance.models import BitFinanceExchange
from up_bits.models import UpBitMarket, UpBitExchange
from config.settings.base import SECRETS_FULL

import ccxt
from binance.client import Client
import pandas as pd


def binance_data():
    binance = ccxt.binance()
    markets = binance.fetch_tickers()
    objects = list()
    bit_coin_value = markets['BTC/BKRW']['close']

    BINANCE_KEY = SECRETS_FULL['BINANCE_KEY']
    binance_access_key = BINANCE_KEY['access_key']
    binance_secret_key = BINANCE_KEY['secret_key']
    client = Client(binance_access_key, binance_secret_key)
    assetDetail_data = client.get_asset_details()

    assetDetail = assetDetail_data['assetDetail']

    date_time_now = timezone.now() + timezone.timedelta(hours=9)
    datetime_now = datetime.datetime(date_time_now.year,
                                     date_time_now.month,
                                     date_time_now.day,
                                     date_time_now.hour,
                                     date_time_now.minute, tzinfo=pytz.UTC)

    datetime_before_one_minute = timezone.now() + timezone.timedelta(hours=9) - timezone.timedelta(minutes=1)
    datetime_now_before_one_minute = datetime.datetime(datetime_before_one_minute.year,
                                                       datetime_before_one_minute.month,
                                                       datetime_before_one_minute.day,
                                                       datetime_before_one_minute.hour,
                                                       datetime_before_one_minute.minute, tzinfo=pytz.UTC)

    for symbol in markets:
        time_string = markets[symbol]['datetime'][:16]
        datetime_data = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M') + timedelta(hours=9)
        datetime_data = datetime.datetime(datetime_data.year, datetime_data.month, datetime_data.day,
                                          datetime_data.hour, datetime_data.minute)

        #     BTC 거래소
        market_name = symbol.split('/')[1]
        #     coin 종류
        coin_kind_name = symbol.split('/')[0]
        english_name = market_name + '-' + coin_kind_name
        if 'BTC/BKRW' != symbol and 'BTC' != market_name:
            continue

        try:
            asset_withdraw_enable_dict = assetDetail[coin_kind_name]
            depositStatus = asset_withdraw_enable_dict['depositStatus']
            withdrawFee = asset_withdraw_enable_dict['withdrawFee']
            withdrawStatus = asset_withdraw_enable_dict['withdrawStatus']
        except Exception as e:
            print('withdraw Exception')
            depositStatus = False
            withdrawFee = 0
            withdrawStatus = False
            continue

        if datetime_data != datetime_now:
            datetime_data = datetime_now

        try:
            obj, _ = UpBitMarket.objects.get_or_create(coin=coin_kind_name)
        except Exception as e:
            print('market model create Exception', e)
            obj, _ = UpBitMarket.objects.get_or_create(
                coin=coin_kind_name,
                up_bit_withdraw_fee=0.0,
                up_bit_deposit_fee=0.0,
                up_bit_minimum_with_draw_amount=0.0,
                binance_withdraw_fee=0.0,
                binance_deposit_fee=0.0,
                binance_minimum_with_draw_amount=0.0
            )
        up_bit_obj = BitFinanceExchange(
            market=obj,
            english_name=english_name,
            candle_date_time_kst=datetime_data,
            bit_coin_value=bit_coin_value,
            deposit_status=depositStatus,
            withdraw_status=withdrawStatus,
            open_price=markets[symbol]['open'],
            low_price=markets[symbol]['low'],
            high_price=markets[symbol]['high'],
            close_price=markets[symbol]['close'],
            volume=markets[symbol]['info']['quoteVolume'],
        )
        objects.append(up_bit_obj)
    BitFinanceExchange.objects.bulk_create(objects)


def selected_coin_list():
    coin_list = list()
    for market in UpBitMarket.objects.all():
        up_obj = UpBitExchange.objects.filter(market=market)
        binance_obj = BitFinanceExchange.objects.filter(market=market)

        if up_obj.exists() and binance_obj.exists():
            print(up_obj.first().market.coin)
            coin_list.append(up_obj.first().market.coin)
        pd.DataFrame(coin_list).to_csv('selected_coin_list_test.csv')
    return coin_list
