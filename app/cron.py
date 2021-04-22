import ccxt
from datetime import timedelta
import datetime
import time
import requests
import json
import pandas as pd

from bit_finance.models import BitFinanceCoinExchange
from config.global_variable import bits_name_list
from up_bits.models import UpBitCoinExchange


def search_binance():
    binance = ccxt.binance()
    markets = binance.fetch_tickers()
    objects = list()
    date_time_now = datetime.datetime.now() + timedelta(hours=9)
    datetime_now = datetime.datetime(date_time_now.year,
                                     date_time_now.month,
                                     date_time_now.day,
                                     date_time_now.hour,
                                     date_time_now.minute)
    for symbol in markets:
        time_string = markets[symbol]['datetime'][:16]
        datetime_data = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M') + timedelta(hours=9)
        datetime_data = datetime.datetime(datetime_data.year, datetime_data.month, datetime_data.day,
                                          datetime_data.hour, datetime_data.minute)
        markets_symbol = markets[symbol]['symbol']
        market_name = markets_symbol.split('/')[1]
        coin_kind_name = markets_symbol.split('/')[0]

        if 'BTC' != market_name:
            continue

        if datetime_data != datetime_now:
            datetime_data = datetime_now

        up_bit_obj = BitFinanceCoinExchange(
            market=market_name,
            kind=coin_kind_name,
            english_name=markets[symbol]['symbol'],
            candle_date_time_kst=datetime_data,
            open_price=markets[symbol]['open'],
            low_price=markets[symbol]['low'],
            high_price=markets[symbol]['high'],
            close_price=markets[symbol]['close'],
            volume=markets[symbol]['info']['quoteVolume'],
        )
        objects.append(up_bit_obj)
    print(objects)
    BitFinanceCoinExchange.objects.bulk_create(objects)


def single_compare_time_now_with_response_datetime(current_data, time_now_list):
    c_data = current_data[0]
    time_data = datetime.datetime.strptime(c_data['candle_date_time_kst'].replace('T', ' '), '%Y-%m-%d %H:%M:00')
    response_datetime = datetime.datetime(time_data.year, time_data.month, time_data.day, time_data.hour,
                                          time_data.minute)
    print(response_datetime)
    if response_datetime != time_now_list:
        c_data['candle_date_time_kst'] = time_now_list
        # c_data['candle_acc_trade_volume'] = 0
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


def bulk_object_create(current_search_list):
    objects = list()
    for data in current_search_list:
        objects.append(UpBitCoinExchange(
            market=data['market'].split('/')[0],
            korean_name=data['korean_name'],
            english_name=data['english_name'],
            kind=data['market'].split('-')[1],
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
    # time_now_list = minute_before_5_stamp()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    current_search_list = list()
    for kind in bits_name_list[:55]:
        if kind['market'] != 'KRW-BTC' and kind['market'].split('-')[0] != 'BTC':
            continue
        querystring = {"market": f"{kind['market']}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(kind)
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
        # five_ea_data_list = compare_time_now_with_response_datetime(current_data, time_now_list)
        print(five_ea_data_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        current_search_list.append(five_ea_data_list)
        time.sleep(1)
    bits_objects = bulk_object_create(current_search_list)
    UpBitCoinExchange.objects.bulk_create(bits_objects)


def search_up_bit_second():
    time_now_list = single_minute_before_5_stamp()
    # time_now_list = minute_before_5_stamp()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    current_search_list = list()
    for kind in bits_name_list[55:110]:
        if kind['market'] != 'KRW-BTC' and kind['market'].split('-')[0] != 'BTC':
            continue
        querystring = {"market": f"{kind['market']}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(kind)
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
        # five_ea_data_list = compare_time_now_with_response_datetime(current_data, time_now_list)
        print(five_ea_data_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        current_search_list.append(five_ea_data_list)
        time.sleep(1)
    bits_objects = bulk_object_create(current_search_list)
    UpBitCoinExchange.objects.bulk_create(bits_objects)


def search_up_bit_third():
    # time_now_list = minute_before_5_stamp()
    time_now_list = single_minute_before_5_stamp()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://api.upbit.com/v1/candles/minutes/1"
    current_search_list = list()
    for kind in bits_name_list[110:]:
        if kind['market'] != 'KRW-BTC' and kind['market'].split('-')[0] != 'BTC':
            continue
        querystring = {"market": f"{kind['market']}", "count": "1"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(kind)
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
        # five_ea_data_list = compare_time_now_with_response_datetime(current_data, time_now_list)
        print(five_ea_data_list)
        five_ea_data_list['english_name'] = kind['english_name']
        five_ea_data_list['korean_name'] = kind['korean_name']
        current_search_list.append(five_ea_data_list)
        time.sleep(1)
    bits_objects = bulk_object_create(current_search_list)
    UpBitCoinExchange.objects.bulk_create(bits_objects)


def backup_data():
    date_time_now = datetime.datetime.now() + timedelta(hours=9)
    now_str = date_time_now.strftime('%Y%m%d')
    up_bit_objects = UpBitCoinExchange.objects.all().values()
    df_upbit = pd.DataFrame(up_bit_objects)
    df_upbit = df_upbit.sort_values(by=['candle_date_time_kst'])
    df_upbit.to_csv(f'upbit_data_{now_str}.csv')

    bit_objects = BitFinanceCoinExchange.objects.all().values()
    df_bit = pd.DataFrame(bit_objects)
    df_bit = df_bit.sort_values(by=['candle_date_time_kst'])
    df_bit.to_csv(f'binance_data{now_str}.csv')

    aday = date_time_now - timedelta(days=1)
    aday_str = aday.strftime('%Y%m%d')
    df_bit_0419_csv = pd.read_csv(f'./data_collect/binance_data_210419_to_{aday_str}.csv')
    df_concat = pd.concat([df_bit_0419_csv, df_bit])
    df_concat.to_csv(f'./data_collect/binance_data_210419_to_{now_str}.csv')

    df_up_bit_0419_csv = pd.read_csv(f'./data_collect/upbit_data_210419_to_{aday_str}.csv')
    df_concat = pd.concat([df_up_bit_0419_csv, df_upbit])
    df_concat.to_csv(f'./data_collect/upbit_data_210419_to_{now_str}.csv')