# from datetime import timedelta
# import datetime
# from django.utils import timezone
# import time
# from binance.client import Client
# import ccxt
#
# from bit_finance.models import BinanceExchange
# from config.settings.base import SECRETS_FULL
# from up_bits.models import UpBitMarket
#
# date_time_now = timezone.now() + timezone.timedelta(hours=9)
# datetime_now = datetime.datetime(date_time_now.year,
#                                  date_time_now.month,
#                                  date_time_now.day,
#                                  date_time_now.hour,
#                                  date_time_now.minute)
#
# date_time_now = timezone.now() + timezone.timedelta(hours=9) - timezone.timedelta(minutes=1)
# datetime_now_before_one_minute = datetime.datetime(date_time_now.year,
#                                                    date_time_now.month,
#                                                    date_time_now.day,
#                                                    date_time_now.hour,
#                                                    date_time_now.minute)
#
#
# def search_binance():
#     binance = ccxt.binance()
#     markets = binance.fetch_tickers()
#     objects = list()
#
#     bit_coin_value = markets['BTC/BKRW']['close']
#     BINANCE_KEY = SECRETS_FULL['BINANCE_KEY']
#     binance_access_key = BINANCE_KEY['access_key']
#     binance_secret_key = BINANCE_KEY['secret_key']
#     client = Client(binance_access_key, binance_secret_key)
#     assetDetail_data = client.get_asset_details()
#     assetDetail = assetDetail_data['assetDetail']
#     time.sleep(0.5)
#     for symbol in markets:
#         time_string = markets[symbol]['datetime'][:16]
#         datetime_data = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M') + timedelta(hours=9)
#         datetime_data = datetime.datetime(datetime_data.year, datetime_data.month, datetime_data.day,
#                                           datetime_data.hour, datetime_data.minute)
#         market_name = symbol.split('/')[1]
#         coin_kind_name = symbol.split('/')[0]
#
#         if 'BTC/BKRW' != symbol and 'BTC' != market_name:
#             continue
#
#         try:
#             asset_withdraw_enable_dict = assetDetail[coin_kind_name]
#             depositStatus = asset_withdraw_enable_dict['depositStatus']
#             # withdrawFee = asset_withdraw_enable_dict['withdrawFee']
#             withdrawStatus = asset_withdraw_enable_dict['withdrawStatus']
#         except Exception as e:
#             print('withdraw Exception', e)
#             depositStatus = False
#             # withdrawFee = 0
#             withdrawStatus = False
#
#         if datetime_data != datetime_now:
#             datetime_data = datetime_now
#         try:
#             obj, _ = UpBitMarket.objects.get_or_create(coin=coin_kind_name)
#         except Exception as e:
#             print('market model create Exception', e)
#             obj, _ = UpBitMarket.objects.get_or_create(
#                 coin=coin_kind_name,
#                 up_bit_withdraw_fee=0.0,
#                 up_bit_deposit_fee=0.0,
#                 up_bit_minimum_with_draw_amount=0.0,
#                 binance_withdraw_fee=0.0,
#                 binance_deposit_fee=0.0,
#                 binance_minimum_with_draw_amount=0.0
#             )
#
#         up_bit_obj = BinanceExchange(
#             market=obj,
#             english_name=markets[symbol]['symbol'],
#             candle_date_time_kst=datetime_data,
#             bit_coin_value=bit_coin_value,
#             deposit_status=depositStatus,
#             withdraw_status=withdrawStatus,
#             open_price=markets[symbol]['open'],
#             low_price=markets[symbol]['low'],
#             high_price=markets[symbol]['high'],
#             close_price=markets[symbol]['close'],
#             volume=markets[symbol]['info']['quoteVolume'],
#         )
#         objects.append(up_bit_obj)
#     BinanceExchange.objects.bulk_create(objects)
