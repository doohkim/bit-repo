import pytz
from django.shortcuts import render
from sklearn.linear_model import LinearRegression
import datetime
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from config.global_variable import selected_coin_kind, selected_coins
from up_bits.models import UpBitMarket
import numpy as np


def exchange_binance_multiple_result(request):
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
    for coin_name in selected_coins:
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
            # 6시간 바이낸스 괴리율 정도
            if df['binance_discrepancy_rate'].std() == 0:
                analytics_data_dict['binance_degree_of_discrepancy'] = 0.5
            elif df['binance_discrepancy_rate'].std() != 0:
                binance_degree_of_discrepancy = (df['binance_discrepancy_rate'][0] - df[
                    'binance_discrepancy_rate'].mean()) / df['binance_discrepancy_rate'].std()
                analytics_data_dict['binance_degree_of_discrepancy'] = binance_degree_of_discrepancy
            # 1시간 매도 거래소 회귀 계수
            try:
                up_x = np.arange(1, 31).reshape(-1, 1)
                up_y = df.head(30).sort_values('up_date')['up_close_price'].values.reshape(-1, 1)
                up_line_fitter = LinearRegression()
                up_line_fitter.fit(up_x, up_y)
                analytics_data_dict['up_coef'] = up_line_fitter.coef_[0][0]
            except Exception as e:
                analytics_data_dict['up_coef'] = e

            # 6시간 매도 거래소 회귀 계수
            sort_df = df.sort_values('up_date')
            up_x6 = np.arange(1, len(sort_df) + 1).reshape(-1, 1)
            up_y6 = sort_df['up_close_price'].values.reshape(-1, 1)
            up_line_fitter6 = LinearRegression()
            try:
                up_line_fitter6.fit(up_x6, up_y6)
                analytics_data_dict['up_coef6'] = up_line_fitter6.coef_[0][0]
            except Exception as e:
                # print(e)
                analytics_data_dict['up_coef6'] = e

            # 한시간 매수 거래소 회귀 계수
            try:
                binance_x = np.arange(1, 31).reshape(-1, 1)
                binance_y = df.head(30).sort_values('binance_date')['binance_close_price'].values.reshape(-1, 1)
                binance_line_fitter = LinearRegression()
                binance_line_fitter.fit(binance_x, binance_y)
                analytics_data_dict['binance_coef'] = binance_line_fitter.coef_[0][0]
            except Exception as e:
                # print(e)
                analytics_data_dict['binance_coef'] = e

            binance_first_obj = binance_obj.first()
            analytics_data_dict['binance_deposit_status'] = binance_first_obj.deposit_status
            analytics_data_dict['binance_withdraw_enable'] = binance_first_obj.withdraw_status
            analytics_data_dict['binance_expected_revenue_rate'] = binance_first_obj.expected_revenue_rate
            analytics_data_dict['binance_close_price'] = binance_first_obj.close_price
            analytics_data_dict['binance_date'] = binance_first_obj.candle_date_time_kst

            # 6시간 바이낸스 괴리율 정도
            # binance_degree_of_discrepancy = (df['binance_discrepancy_rate'][0] - df[
            #     'binance_discrepancy_rate'].mean()) / df['binance_discrepancy_rate'].std()
            # analytics_data_dict['binance_degree_of_discrepancy'] = binance_degree_of_discrepancy

            up_first_obj = up_obj.first()
            analytics_data_dict['up_deposit_status'] = up_first_obj.deposit_status
            analytics_data_dict['up_withdraw_enable'] = up_first_obj.withdraw_status
            analytics_data_dict['up_expected_revenue_rate'] = up_first_obj.expected_revenue_rate
            analytics_data_dict['up_close_price'] = up_first_obj.close_price
            analytics_data_dict['up_date'] = up_first_obj.candle_date_time_kst

            analytics_data_dict[
                'transaction_price'] = binance_first_obj.transaction_price + up_first_obj.transaction_price
            each_coin_analytics_dict[coin_name] = analytics_data_dict
    expected_df = pd.DataFrame(each_coin_analytics_dict).transpose()
    if expected_df['up_coef'].max() == 0:
        expected_df['scaled_up_coef'] = 1
    if expected_df['up_coef6'].max() == 0:
        expected_df['scaled_up_coef6'] = 1
    if expected_df['transaction_price'].max() == 0:
        expected_df['scaled_transaction_price'] = 1
    if expected_df['binance_coef'].max() == 0:
        expected_df['scaled_binance_coef'] = 1
    # 100% 보다 낮은 매수 거래소 기대 수익률 분리
    split_expected_main = expected_df[expected_df['binance_expected_revenue_rate'] <= 100]
    # 100% 보다 낮은 매수 거래소 기대 수익률 테이블에서 max 값
    split_expected_main_max_value = split_expected_main['binance_expected_revenue_rate'].max()
    # 100% 보다 낮은 기대 수익률 테이블에서 max 값으로 전체 나누기
    expected_df['scaled_binance_expected_revenue_rate'] = \
        expected_df['binance_expected_revenue_rate'] / split_expected_main_max_value
    # 1.0 보다 큰 수 모두 1로 통일
    expected_df.loc[
        (expected_df.scaled_binance_expected_revenue_rate > 1.0), 'scaled_binance_expected_revenue_rate'] = 1.0

    # 150% 보다 낮은 괴리율 정도 분리
    split_binance_degree_of_discrepancy_main = expected_df[expected_df['binance_degree_of_discrepancy'] <= 1.5]
    # 150% 보다 낮은 괴리율 정도 테이블에서 max 값
    split_binance_degree_of_discrepancy_main_max = \
        split_binance_degree_of_discrepancy_main['binance_degree_of_discrepancy'].max()
    # 150% 보다 낮은 괴리율 정도 테이블에서 max 값으로 전체 나누기
    expected_df['scaled_binance_degree_of_discrepancy'] = \
        expected_df['binance_degree_of_discrepancy'] / split_binance_degree_of_discrepancy_main_max
    # 1.0 보다 큰 수 모두 1로 통일
    expected_df.loc[
        (expected_df.scaled_binance_degree_of_discrepancy > 1.0), 'scaled_binance_degree_of_discrepancy'] = 1.0
    # 1시간 매수거래소 회귀 계수 min 값
    expected_df['scaled_binance_coef'] = expected_df['binance_coef'] / expected_df['binance_coef'].min()
    expected_df['scaled_transaction_price'] = expected_df['transaction_price'] / expected_df['transaction_price'].max()
    expected_df['scaled_up_coef'] = expected_df['up_coef'] / expected_df['up_coef'].max()
    expected_df['scaled_up_coef6'] = expected_df['up_coef6'] / expected_df['up_coef6'].max()

    # SD 매수 거래소 기대수익률 * 40% + SD 매수 거래소 괴리율 정도 * 14.3% + 매도거래소 1시간 회귀 계수 * 5% +
    # SD 매수 거래소 1시간 회귀 계수 * 2.9% + SD 거래대금 * 17%
    expected_df['total'] = (expected_df['scaled_binance_expected_revenue_rate'] * 0.4) + \
                           (expected_df['scaled_binance_degree_of_discrepancy'] * 0.143) + \
                           (expected_df['scaled_up_coef'] * 0.057) + \
                           (expected_df['scaled_binance_coef'] * 0.029) + \
                           (expected_df['scaled_transaction_price'] * 0.17)

    cut_index = expected_df[(expected_df['binance_expected_revenue_rate'] <= 0)
                            | (expected_df['up_coef'] <= 0)
                            | (expected_df['binance_deposit_status'] == False)
                            | (expected_df['binance_withdraw_enable'] == False)
                            | (expected_df['up_deposit_status'] == False)
                            | (expected_df['up_withdraw_enable'] == False)
                            | (expected_df['scaled_binance_expected_revenue_rate'] <= 0)
                            | (expected_df['scaled_binance_coef'] <= 0)
                            | (expected_df['scaled_binance_degree_of_discrepancy'] <= 0)
                            | (expected_df['scaled_up_coef'] <= 0)
                            | (expected_df['scaled_transaction_price'] <= 0)].index
    expected_df = expected_df.drop(cut_index)
    data = zip(expected_df.index, expected_df.values)
    context = {
        'data': data,
        'from': '바이낸스',
        'to': '업비트'
    }

    return render(request, 'market/test_all_table.html', context)
