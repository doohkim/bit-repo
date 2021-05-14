import pytz
from django.shortcuts import render
from sklearn.linear_model import LinearRegression
import datetime
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from config.global_variable import selected_coin_kind
from up_bits.models import UpBitMarket
import numpy as np


def test_expected_table_view(request):
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
    each_coin_analytics_dict = dict()
    for coin_name in selected_coin_kind.values():
        analytics_data_dict = dict()

        market_obj = UpBitMarket.objects.get(coin=coin_name)
        up_obj = market_obj.upbitexchange_set.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
        )
        binance_obj = market_obj.bitfinanceexchange_set.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
        )

        if up_obj.exists() and binance_obj.exists():
            binance_df = pd.DataFrame(
                binance_obj.values('english_name', 'candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                                   'binance_discrepancy_rate').distinct('english_name', 'candle_date_time_kst')[::2])

            binance_df = binance_df.rename(
                columns={'english_name': 'binance_full_name', 'candle_date_time_kst': "binance_date",
                         'close_price': "binance_close_price",
                         'expected_revenue_rate': "binance_expected_revenue_rate",
                         'binance_discrepancy_rate': "binance_discrepancy_rate"}
            )
            up_df = pd.DataFrame(
                up_obj.values('full_name', 'candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                              'up_discrepancy_rate').distinct('full_name', 'candle_date_time_kst')[::2])

            up_df = up_df.rename(
                columns={'full_name': 'up_full_name', 'candle_date_time_kst': "up_date",
                         'close_price': "up_close_price",
                         'expected_revenue_rate': "up_expected_revenue_rate",
                         'up_discrepancy_rate': "up_discrepancy_rate"}
            )
            df = pd.concat([binance_df, up_df], axis=1)

            # null 값 채우기
            up_isnull_index_list = list()
            if df['up_date'].isnull().sum() != 0:
                for index in df[df['up_date'].isnull()].index:
                    up_isnull_index_list.append(index)
                    df['up_date'][index] = df['binance_date'][index]
            binance_isnull_index_list = list()
            if df['binance_date'].isnull().sum() != 0:
                for index in df[df['binance_date'].isnull()].index:
                    binance_isnull_index_list.append(index)
                    df['binance_date'][index] = df['up_date'][index]

            for column, value in df.isnull().sum().items():
                if value != 0:
                    if 'binance' in column:
                        binance_min_index = min(binance_isnull_index_list)
                        df[column].fillna(df[column][binance_min_index - 1], inplace=True)
                    elif 'up' in column:
                        up_min_index = min(up_isnull_index_list)
                        df[column].fillna(df[column][up_min_index - 1], inplace=True)

            # 업비트 괴리율 정도
            up_degree_of_discrepancy = (df['up_discrepancy_rate'][0] - df['up_discrepancy_rate'].mean()) / df[
                'up_discrepancy_rate'].std()
            analytics_data_dict['up_degree_of_discrepancy'] = up_degree_of_discrepancy

            sort_df = df.sort_values('binance_date')
            binance_x = np.arange(1, 31).reshape(-1, 1)
            binance_y = sort_df['binance_close_price'].values[:30].reshape(-1, 1)
            binance_line_fitter = LinearRegression()
            # 바이낸스 1시간 회귀 계수
            try:

                binance_line_fitter.fit(binance_x, binance_y)
                analytics_data_dict['binance_coef'] = binance_line_fitter.coef_[0][0]
            except Exception as e:
                analytics_data_dict['binance_coef'] = e

            binance_x6 = df['binance_close_price'].values.reshape(-1, 1)
            binance_y6 = df['binance_date'].values.reshape(-1, 1)
            binance_line_fitter6 = LinearRegression()

            # 바이낸스 6시간 회귀 계수
            try:

                binance_line_fitter6.fit(binance_x6, binance_y6)
                analytics_data_dict['binance_coef6'] = binance_line_fitter6.coef_[0][0]
            except Exception as e:
                analytics_data_dict['binance_coef6'] = e

            up_first_obj = up_obj.first()
            analytics_data_dict['up_deposit_status'] = up_first_obj.deposit_status
            analytics_data_dict['up_withdraw_enable'] = up_first_obj.withdraw_status
            analytics_data_dict['up_expected_revenue_rate'] = up_first_obj.expected_revenue_rate
            analytics_data_dict['up_close_price'] = up_first_obj.close_price
            analytics_data_dict['up_date'] = up_first_obj.candle_date_time_kst

            # 업비트 1시간 회귀 계수
            try:
                up_x = df['up_close_price'].values[:30].reshape(-1, 1)
                up_y = df['up_date'].values[:30].reshape(-1, 1)
                up_line_fitter = LinearRegression()
                up_line_fitter.fit(up_x, up_y)
                analytics_data_dict['up_coef'] = up_line_fitter.coef_[0][0]

            except Exception as e:
                analytics_data_dict['up_coef'] = e

            binance_first_obj = binance_obj.first()
            analytics_data_dict['binance_deposit_status'] = binance_first_obj.deposit_status
            analytics_data_dict['binance_withdraw_enable'] = binance_first_obj.withdraw_status
            analytics_data_dict['binance_close_price'] = binance_first_obj.close_price
            analytics_data_dict['binance_date'] = binance_first_obj.candle_date_time_kst

            analytics_data_dict[
                'transaction_price'] = binance_first_obj.transaction_price + up_first_obj.transaction_price
            each_coin_analytics_dict[coin_name] = analytics_data_dict
    expected_df = pd.DataFrame(each_coin_analytics_dict).transpose()

    expected_df['scaled_up_expected_revenue_rate'] = expected_df['up_expected_revenue_rate'] / expected_df[
        'up_expected_revenue_rate'].max()
    expected_df['scaled_up_degree_of_discrepancy'] = expected_df['up_degree_of_discrepancy'] / expected_df[
        'up_degree_of_discrepancy'].max()
    expected_df['scaled_up_coef'] = expected_df['up_coef'] / expected_df['up_coef'].max()
    expected_df['scaled_transaction_price'] = expected_df['transaction_price'] / expected_df['transaction_price'].max()
    expected_df['scaled_binance_coef'] = expected_df['binance_coef'] / expected_df['binance_coef'].max()
    expected_df['scaled_binance_coef6'] = expected_df['binance_coef6'] / expected_df['binance_coef6'].max()
    expected_df['total'] = \
        (expected_df['up_expected_revenue_rate'] / expected_df['up_expected_revenue_rate'].max() * 0.4) + \
        (expected_df['up_degree_of_discrepancy'] / expected_df['up_degree_of_discrepancy'].max() * 0.143) + \
        (expected_df['up_coef'] / expected_df['up_coef'].max() * 0.057) + \
        (expected_df['binance_coef'] / expected_df['binance_coef'].max() * 0.029) + \
        (expected_df['transaction_price'] / expected_df['transaction_price'].max() * 0.17)
    data = zip(expected_df.index, expected_df.values)
    context = {
        'data': data,

    }
    return render(request, 'market/test_all_table.html', context)


def check_data_view(request):
    datetime_now_before_one_minute = datetime.datetime(2021, 5, 12, 16, 52, tzinfo=pytz.UTC)
    datetime_now_six_hours_ago = datetime.datetime(2021, 5, 12, 10, 52, tzinfo=pytz.UTC)

    coin_name = request.GET.get('coin', None)

    if coin_name is None:
        coin_name = 'ADA'

    market_obj = UpBitMarket.objects.get(coin=coin_name)
    up_obj = market_obj.upbitexchange_set.filter(
        Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
        Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
    )
    binance_obj = market_obj.bitfinanceexchange_set.filter(
        Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
        Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
    )
    if up_obj.exists() and binance_obj.exists():
        binance_df = pd.DataFrame(
            binance_obj.values('english_name', 'candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                               'binance_discrepancy_rate')
                .distinct('english_name', 'candle_date_time_kst')[::2])

        binance_df = binance_df.rename(
            columns={'english_name': 'binance_full_name', 'candle_date_time_kst': "binance_date",
                     'close_price': "binance_close_price",
                     'expected_revenue_rate': "binance_expected_revenue_rate",
                     'binance_discrepancy_rate': "binance_discrepancy_rate"}
        )
        up_df = pd.DataFrame(
            up_obj.values('full_name', 'candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                          'up_discrepancy_rate').distinct('full_name', 'candle_date_time_kst')[::2])

        up_df = up_df.rename(
            columns={'full_name': 'up_full_name', 'candle_date_time_kst': "up_date",
                     'close_price': "up_close_price",
                     'expected_revenue_rate': "up_expected_revenue_rate",
                     'up_discrepancy_rate': "up_discrepancy_rate"}
        )
        df = pd.concat([binance_df, up_df], axis=1)
        up_degree_of_discrepancy = (df['up_discrepancy_rate'][0] - df['up_discrepancy_rate'].mean()) / df[
            'up_discrepancy_rate'].std()
        sort_df = df.sort_values('binance_date')
        binance_x = np.arange(1, 31).reshape(-1, 1)
        binance_y = sort_df['binance_close_price'].values[:30].reshape(-1, 1)
        binance_line_fitter = LinearRegression()
        try:
            binance_line_fitter.fit(binance_x, binance_y)

            binance_coef = binance_line_fitter.coef_[0][0]
        except Exception as e:
            binance_coef = e

        try:
            binance_line_fitter6 = LinearRegression()
            binance_x6 = np.arange(1, 182).reshape(-1, 1)
            binance_y6 = sort_df['binance_close_price'].values.reshape(-1, 1)
            binance_line_fitter6.fit(binance_x6, binance_y6)
            binance_coef6 = binance_line_fitter6.coef_[0][0]
        except Exception as e:
            binance_coef6 = e

        up_first_obj = up_obj.first()
        up_deposit_status = up_first_obj.deposit_status
        up_withdraw_enable = up_first_obj.withdraw_status
        up_expected_revenue_rate = up_first_obj.expected_revenue_rate
        up_close_price = up_first_obj.close_price
        up_date = up_first_obj.candle_date_time_kst
        try:
            up_x = np.arange(1, 31).reshape(-1, 1)
            up_y = sort_df['up_close_price'].values[:30].reshape(-1, 1)
            up_line_fitter = LinearRegression()
            up_line_fitter.fit(up_x, up_y)
            up_coef = up_line_fitter.coef_[0][0]
        except Exception as e:
            up_coef = e

        binance_first_obj = binance_obj.first()
        binance_deposit_status = binance_first_obj.deposit_status
        binance_withdraw_enable = binance_first_obj.withdraw_status
        binance_close_price = binance_first_obj.close_price
        binance_date = binance_first_obj.candle_date_time_kst
        transaction_price = binance_first_obj.transaction_price + up_first_obj.transaction_price
        context = {
            'coin': coin_name,
            'up_deposit_status': up_deposit_status,
            'up_withdraw_enable': up_withdraw_enable,
            'binance_deposit_status': binance_deposit_status,
            'binance_withdraw_enable': binance_withdraw_enable,
            'up_close_price': up_close_price,
            'binance_close_price': binance_close_price,
            'up_expected_revenue_rate': up_expected_revenue_rate,
            'up_degree_of_discrepancy': up_degree_of_discrepancy,
            'binance_coef': binance_coef,
            'transaction_price': transaction_price,
            'up_coef': up_coef,
            'binance_coef6': binance_coef6,
            'up_date': up_date,
            'binance_date': binance_date,
        }
    return render(request, 'market/test_view.html', context)
