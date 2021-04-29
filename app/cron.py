import uuid
import jwt

from datetime import timedelta
import datetime
from django.utils import timezone
import time
import requests
import json
from binance.client import Client
import ccxt

from bit_finance.models import BitFinanceExchange
from config.global_variable import bits_name_list
from config.settings.base import SECRETS_FULL
from up_bits.models import UpBitMarket, UpBitExchange

date_time_now = timezone.now() + timezone.timedelta(hours=9)
datetime_now = datetime.datetime(date_time_now.year,
                                 date_time_now.month,
                                 date_time_now.day,
                                 date_time_now.hour,
                                 date_time_now.minute)


def search_binance():
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
    time.sleep(0.5)
    for symbol in markets:
        time_string = markets[symbol]['datetime'][:16]
        datetime_data = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M') + timedelta(hours=9)
        datetime_data = datetime.datetime(datetime_data.year, datetime_data.month, datetime_data.day,
                                          datetime_data.hour, datetime_data.minute)
        market_name = symbol.split('/')[1]
        coin_kind_name = symbol.split('/')[0]
        # kind['market'] != 'KRW-BTC' and kind['market'].split('-')[0] != 'BTC':

        if 'BTC/BKRW' != symbol and 'BTC' != market_name:
            continue

        try:
            asset_withdraw_enable_dict = assetDetail[coin_kind_name]
            depositStatus = asset_withdraw_enable_dict['depositStatus']
            # withdrawFee = asset_withdraw_enable_dict['withdrawFee']
            withdrawStatus = asset_withdraw_enable_dict['withdrawStatus']
        except Exception as e:
            print('withdraw Exception', e)
            depositStatus = False
            # withdrawFee = 0
            withdrawStatus = False

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
            english_name=markets[symbol]['symbol'],
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


def single_compare_time_now_with_response_datetime(current_data, time_now_list):
    c_data = current_data[0]
    time_data = datetime.datetime.strptime(c_data['candle_date_time_kst'].replace('T', ' '), '%Y-%m-%d %H:%M:00')
    response_datetime = datetime.datetime(time_data.year, time_data.month, time_data.day, time_data.hour,
                                          time_data.minute)
    if response_datetime != time_now_list:
        c_data['candle_date_time_kst'] = time_now_list
    return c_data


def single_minute_before_5_stamp():
    date_time_now = datetime.datetime.now() + timedelta(hours=9)
    datetime_now = datetime.datetime(
        date_time_now.year,
        date_time_now.month,
        date_time_now.day,
        date_time_now.hour,
        date_time_now.minute
    )
    return datetime_now


def with_draw_api_request_up_bit():
    UP_BIT_KEY = SECRETS_FULL['UP_BIT_KEY']
    access_key = UP_BIT_KEY['access_key']
    secret_key = UP_BIT_KEY['secret_key']

    server_url = 'https://api.upbit.com'
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
    }
    jwt_token = jwt.encode(payload, secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    res = requests.get(server_url + "/v1/status/wallet", headers=headers)
    print(res.status_code)
    try:
        print('withdraw api ', res.json()[:5])

    except Exception:
        print(Exception)
        print('withdraw api ', res.text[:100])
    print(datetime_now)
    if res.status_code == 401 or res.status_code == 404 or res.status_code == 429:
        return None
    status_withdraw = res.json()
    coin_kind_for_find_dict = dict()
    for i in status_withdraw:
        coin_currency_kind = i['currency']
        coin_kind_for_find_dict[coin_currency_kind] = i

    return coin_kind_for_find_dict


def bulk_up_bit_current_create(current_search_list):
    url = "https://api.upbit.com/v1/candles/minutes/1"
    querystring = {"market": "KRW-BTC", "count": "1"}
    response = requests.request("GET", url, params=querystring)
    bit_coin_value = response.json()[0]['trade_price']

    objects = list()
    for data in current_search_list:
        if data['with_enable'] is not None:
            wallet_state = data['with_enable']
            if wallet_state == 'working':
                withdraw_status = True
                deposit_status = True
            elif wallet_state == 'withdraw_only':
                withdraw_status = True
                deposit_status = False
            elif wallet_state == 'deposit_only':
                withdraw_status = False
                deposit_status = True
            else:
                withdraw_status = False
                deposit_status = False
        else:
            withdraw_status = False
            deposit_status = False

        try:
            obj, _ = UpBitMarket.objects.get_or_create(coin=data['market'].split('-')[1])
        except Exception as e:
            print('bulk up up bit create market ', e)
            obj, _ = UpBitMarket.objects.get_or_create(
                coin=data['market'].split('-')[1],
                up_bit_withdraw_fee=0.0,
                up_bit_deposit_fee=0.0,
                up_bit_minimum_with_draw_amount=0.0,
                binance_withdraw_fee=0.0,
                binance_deposit_fee=0.0,
                binance_minimum_with_draw_amount=0.0
            )

        objects.append(
            UpBitExchange(
                market=obj,
                full_name=data['full_name'],
                korean_name=data['korean_name'],
                english_name=data['english_name'],
                bit_coin_value=bit_coin_value,
                withdraw_status=withdraw_status,
                deposit_status=deposit_status,
                candle_date_time_kst=data['candle_date_time_kst'],
                open_price=data['opening_price'],
                low_price=data['low_price'],
                high_price=data['high_price'],
                close_price=data['trade_price'],
                volume=data['candle_acc_trade_volume'],
            )
        )
    return objects


def search_up_bit_first():
    time_now_list = single_minute_before_5_stamp()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    coin_kind_for_find_dict = with_draw_api_request_up_bit()

    current_search_list = list()
    for kind in bits_name_list[:55]:
        coin_full_name = kind['market']
        coin_exchange_kind_split = coin_full_name.split('-')
        coin_exchange = coin_exchange_kind_split[0]
        coin_kind = coin_exchange_kind_split[1]
        if coin_full_name != 'KRW-BTC' and coin_exchange != 'BTC':
            continue
        querystring = {"market": f"{coin_full_name}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        try:
            current_data = response.json()
        except Exception as e:
            print('first json error', e, response.status_code)
            try:
                current_data = json.loads(response.text)
            except Exception as e:
                print('first text error', e, response.status_code)
                continue

        five_ea_data_list = single_compare_time_now_with_response_datetime(current_data, time_now_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        five_ea_data_list['full_name'] = coin_full_name
        if coin_kind_for_find_dict is not None:
            with_draw_enable = coin_kind_for_find_dict[coin_kind]
            five_ea_data_list['with_enable'] = with_draw_enable['wallet_state']
        else:
            five_ea_data_list['with_enable'] = None
        current_search_list.append(five_ea_data_list)
        time.sleep(1)

    bits_objects = bulk_up_bit_current_create(current_search_list)
    UpBitExchange.objects.bulk_create(bits_objects)


def search_up_bit_second():
    time_now_list = single_minute_before_5_stamp()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    time.sleep(1)
    coin_kind_for_find_dict = with_draw_api_request_up_bit()

    current_search_list = list()
    for kind in bits_name_list[55:110]:
        coin_full_name = kind['market']
        coin_exchange_kind_split = coin_full_name.split('-')
        coin_exchange = coin_exchange_kind_split[0]
        coin_kind = coin_exchange_kind_split[1]

        if coin_full_name != 'KRW-BTC' and coin_exchange != 'BTC':
            continue
        querystring = {"market": f"{coin_full_name}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        try:
            current_data = response.json()
        except Exception as e:
            print('second json error', e, response.status_code)
            try:
                current_data = json.loads(response.text)
            except Exception as e:
                print('second text error', e, response.status_code)
                continue
        five_ea_data_list = single_compare_time_now_with_response_datetime(current_data, time_now_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        five_ea_data_list['full_name'] = coin_full_name
        if coin_kind_for_find_dict is not None:
            with_draw_enable = coin_kind_for_find_dict[coin_kind]
            five_ea_data_list['with_enable'] = with_draw_enable['wallet_state']
        else:
            five_ea_data_list['with_enable'] = None
        current_search_list.append(five_ea_data_list)
        time.sleep(1)
    bits_objects = bulk_up_bit_current_create(current_search_list)
    UpBitExchange.objects.bulk_create(bits_objects)


def search_up_bit_third():
    time_now_list = single_minute_before_5_stamp()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    time.sleep(2)
    coin_kind_for_find_dict = with_draw_api_request_up_bit()

    current_search_list = list()
    for kind in bits_name_list[110:]:
        coin_full_name = kind['market']
        coin_exchange_kind_split = coin_full_name.split('-')
        coin_exchange = coin_exchange_kind_split[0]
        coin_kind = coin_exchange_kind_split[1]
        if coin_full_name != 'KRW-BTC' and coin_exchange != 'BTC':
            continue
        querystring = {"market": f"{coin_full_name}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        try:
            current_data = response.json()
        except Exception as e:
            print('third json error', e, response.status_code)
            try:
                current_data = json.loads(response.text)
            except Exception as e:
                print('third text error', e, response.status_code)
                continue
        five_ea_data_list = single_compare_time_now_with_response_datetime(current_data, time_now_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        five_ea_data_list['full_name'] = coin_full_name
        if coin_kind_for_find_dict is not None:
            with_draw_enable = coin_kind_for_find_dict[coin_kind]
            five_ea_data_list['with_enable'] = with_draw_enable['wallet_state']
        else:
            five_ea_data_list['with_enable'] = None
        current_search_list.append(five_ea_data_list)
        time.sleep(1)
    bits_objects = bulk_up_bit_current_create(current_search_list)
    UpBitExchange.objects.bulk_create(bits_objects)

#
# def backup_data():
#     date_time_now = datetime.datetime.now() + timedelta(hours=9)
#     now_str = date_time_now.strftime('%Y%m%d')
#     up_bit_objects = UpBitCoinExchange.objects.all().values()
#     df_upbit = pd.DataFrame(up_bit_objects)
#     df_upbit = df_upbit.sort_values(by=['candle_date_time_kst'])
#     df_upbit.to_csv(f'upbit_data_{now_str}.csv')
#
#     bit_objects = BitFinanceCoinExchange.objects.all().values()
#     df_bit = pd.DataFrame(bit_objects)
#     df_bit = df_bit.sort_values(by=['candle_date_time_kst'])
#     df_bit.to_csv(f'binance_data{now_str}.csv')
#
#     aday = date_time_now - timedelta(days=1)
#     aday_str = aday.strftime('%Y%m%d')
#     df_bit_0419_csv = pd.read_csv(f'./data_collect/binance_data_210419_to_{aday_str}.csv')
#     df_concat = pd.concat([df_bit_0419_csv, df_bit])
#     df_concat.to_csv(f'./data_collect/binance_data_210419_to_{now_str}.csv')
#
#     df_up_bit_0419_csv = pd.read_csv(f'./data_collect/upbit_data_210419_to_{aday_str}.csv')
#     df_concat = pd.concat([df_up_bit_0419_csv, df_upbit])
#     df_concat.to_csv(f'./data_collect/upbit_data_210419_to_{now_str}.csv')


# def minute_before_5_stamp():
#     time_stamp_list = list()
#     for index in range(5):
#         date_time_now = datetime.datetime.now() + timedelta(hours=9)
#         datetime_minute = date_time_now - timedelta(minutes=index)
#         datetime_now = datetime.datetime(
#             datetime_minute.year,
#             datetime_minute.month,
#             datetime_minute.day,
#             datetime_minute.hour,
#             datetime_minute.minute)
#         time_stamp_list.append(datetime_now)
#     return time_stamp_list
#
#
# def compare_time_now_with_response_datetime(current_data, time_now_list):
#     count = 0
#     five_ea_data_list = list()
#     for c_data, t_data in zip(current_data, time_now_list):
#         time_data = datetime.datetime.strptime(c_data['candle_date_time_kst'].replace('T', ' '), '%Y-%m-%d %H:%M:00')
#         response_datetime = datetime.datetime(time_data.year, time_data.month, time_data.day, time_data.hour,
#                                               time_data.minute)
#         if response_datetime in time_now_list:
#             count += 1
#             continue
#         else:
#             c_data['candle_date_time_kst'] = time_now_list[count]
#             c_data['candle_acc_trade_volume'] = 0
#             count += 1
#         five_ea_data_list.append(c_data)
#     return five_ea_data_list


# def bulk_object_create(current_search_list):
#     objects = list()
#     for data in current_search_list:
#         # obj, _ = UpBitMarket.objects.get_or_create(coin=data['market'].split('-')[0], )
#         objects.append(
#             UpBitCoinExchange(
#                 market=data['market'].split('-')[0],
#                 korean_name=data['korean_name'],
#                 english_name=data['english_name'],
#                 kind=data['market'].split('-')[1],
#                 candle_date_time_kst=data['candle_date_time_kst'],
#                 open_price=data['opening_price'],
#                 low_price=data['low_price'],
#                 high_price=data['high_price'],
#                 close_price=data['trade_price'],
#                 volume=data['candle_acc_trade_volume'],
#
#             )
#         )
#     return objects
