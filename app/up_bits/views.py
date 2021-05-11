import pytz
from django.shortcuts import render
from sklearn.linear_model import LinearRegression
import datetime
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from config.global_variable import selected_coin_kind
from up_bits.models import UpBitMarket


def binance_buy_exchange_view(request):
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
            binance_df = pd.DataFrame(binance_obj.values('candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                                                         'binance_discrepancy_rate')
                                      .distinct('candle_date_time_kst')[::2])

            binance_df = binance_df.rename(
                columns={binance_df.columns[0]: "binance_date", binance_df.columns[1]: "binance_close_price",
                         binance_df.columns[2]: "binance_expected_revenue_rate",
                         binance_df.columns[3]: "binance_discrepancy_rate"}
            )
            up_df = pd.DataFrame(up_obj.values('candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                                               'up_discrepancy_rate').distinct('candle_date_time_kst')[::2])

            up_df = up_df.rename(
                columns={up_df.columns[0]: "up_date", up_df.columns[1]: "up_close_price",
                         up_df.columns[2]: "up_expected_revenue_rate", up_df.columns[3]: "up_discrepancy_rate"}
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
            binance_degree_of_discrepancy = (df['binance_discrepancy_rate'][0] - df[
                'binance_discrepancy_rate'].mean()) / df['binance_discrepancy_rate'].std()
            analytics_data_dict['binance_degree_of_discrepancy'] = binance_degree_of_discrepancy
            up_x = df['up_close_price'].values.reshape(-1, 1)
            up_y = df['up_date'].values.reshape(-1, 1)
            up_line_fitter = LinearRegression()
            try:
                up_line_fitter.fit(up_x, up_y)
                analytics_data_dict['up_coef'] = up_line_fitter.coef_[0][0]
            except Exception as e:
                message = e
                analytics_data_dict['up_coef'] = message

            binance_x = df['binance_close_price'].values.reshape(-1, 1)
            binance_y = df['binance_date'].values.reshape(-1, 1)
            binance_line_fitter = LinearRegression()
            try:
                binance_line_fitter.fit(binance_x, binance_y)
                # 가격 추세(매도)
                # 업비트가 매소거래소 => 매도거래소(바이낸스) 현재가 - 추세값
                # up_price_trend = df['binance_close_price'][0] - (
                #         binance_line_fitter.coef_ * 60) + binance_line_fitter.intercept_
                analytics_data_dict['binance_coef'] = binance_line_fitter.coef_[0][0]
                # analytics_data_dict['up_price_trend'] = up_price_trend[0][0]
            except Exception as e:
                message = e
                analytics_data_dict['binance_coef'] = message
            binance_first_obj = binance_obj.first()
            analytics_data_dict['binance_date'] = df['binance_date'][0]
            analytics_data_dict['up_date'] = df['up_date'][0]
            up_first_obj = up_obj.first()
            analytics_data_dict['binance_expected_revenue_rate'] = binance_first_obj.expected_revenue_rate
            analytics_data_dict[
                'transaction_price'] = binance_first_obj.transaction_price + up_first_obj.transaction_price
            each_coin_analytics_dict[coin_name] = analytics_data_dict
    expected_df = pd.DataFrame(each_coin_analytics_dict).transpose()
    cut_index = expected_df[(expected_df['binance_expected_revenue_rate'] <= 0) | (expected_df['up_coef'] <= 0)].index
    expected_ddf = expected_df.drop(cut_index)

    expected_ddf['total'] = \
        (expected_ddf['binance_expected_revenue_rate'] / expected_ddf['binance_expected_revenue_rate'].max() * 0.4) + \
        (expected_ddf['binance_degree_of_discrepancy'] / expected_ddf['binance_degree_of_discrepancy'].max() * 0.143) + \
        (expected_ddf['binance_coef'] / expected_ddf['binance_coef'].max() * 0.057) + \
        (expected_ddf['up_coef'] / expected_ddf['up_coef'].max() * 0.029) + \
        (expected_ddf['transaction_price'] / expected_ddf['transaction_price'].max() * 0.17)

    result_index = pd.to_numeric(expected_ddf['total']).idxmax(axis=0)
    context = {
        'coin': result_index,
        "result": each_coin_analytics_dict[result_index]
    }
    return render(request, 'market/binance_buy_exchange.html', context)


def analytics_view(request):
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
            binance_df = pd.DataFrame(binance_obj.values('candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                                                         'binance_discrepancy_rate')
                                      .distinct('candle_date_time_kst')[::2])

            binance_df = binance_df.rename(
                columns={binance_df.columns[0]: "binance_date", binance_df.columns[1]: "binance_close_price",
                         binance_df.columns[2]: "binance_expected_revenue_rate",
                         binance_df.columns[3]: "binance_discrepancy_rate"}
            )
            up_df = pd.DataFrame(up_obj.values('candle_date_time_kst', 'close_price', 'expected_revenue_rate',
                                               'up_discrepancy_rate').distinct('candle_date_time_kst')[::2])

            up_df = up_df.rename(
                columns={up_df.columns[0]: "up_date", up_df.columns[1]: "up_close_price",
                         up_df.columns[2]: "up_expected_revenue_rate", up_df.columns[3]: "up_discrepancy_rate"}
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

            # 업비트가 매수 거래소 바이낸스가 매도 거래소 일 경우
            # 6시간 데이터 괴리율의 정도
            # (현재 괴리율 - 6시간 평균 괴리율) / 표준편차
            up_degree_of_discrepancy = (df['up_discrepancy_rate'][0] - df['up_discrepancy_rate'].mean()) / df[
                'up_discrepancy_rate'].std()
            analytics_data_dict['up_degree_of_discrepancy'] = up_degree_of_discrepancy
            # 업비트가 매수 거래소 바이낸스가 매도 거래소 일 경우
            # 가격 추세
            binance_x = df['binance_close_price'].values[:30].reshape(-1, 1)
            binance_y = df['binance_date'].values[:30].reshape(-1, 1)
            binance_line_fitter = LinearRegression()
            try:
                binance_line_fitter.fit(binance_x, binance_y)
                analytics_data_dict['binance_coef'] = binance_line_fitter.coef_[0][0]
                # 가격 추세(매도)
                # 업비트가 매소거래소 => 매도거래소(바이낸스) 현재가 - 추세값
                # up_price_trend = df['binance_close_price'][0] - (
                #         binance_line_fitter.coef_ * 60) + binance_line_fitter.intercept_
                # analytics_data_dict['up_price_trend'] = up_price_trend[0][0]
            except Exception as e:
                message = e
                analytics_data_dict['binance_coef'] = message

            try:
                binance_line_fitter6 = LinearRegression()
                binance_x6 = df['binance_close_price'].values.reshape(-1, 1)
                binance_y6 = df['binance_date'].values.reshape(-1, 1)
                binance_line_fitter6.fit(binance_x6, binance_y6)
                analytics_data_dict['binance_coef6'] = binance_line_fitter6.coef_[0][0]
            except Exception as e:
                message = e
                analytics_data_dict['binance_coef6'] = message

            up_first_obj = up_obj.first()
            analytics_data_dict['up_deposit_status'] = up_first_obj.deposit_status
            analytics_data_dict['up_withdraw_enable'] = up_first_obj.withdraw_status
            analytics_data_dict['up_expected_revenue_rate'] = up_first_obj.expected_revenue_rate
            analytics_data_dict['up_close_price'] = up_first_obj.close_price
            # 바이낸스가 매수 거래소 업비트가 매도 거래소 일 경우

            # 6시간 데이터 괴리율의 정도
            # (현재 괴리율 - 6시간 평균 괴리율) / 표준편차
            # binance_degree_of_discrepancy = (df['binance_discrepancy_rate'][0] - df[
            #     'binance_discrepancy_rate'].mean()) / df['binance_discrepancy_rate'].std()
            #
            up_x = df['up_close_price'].values[:30].reshape(-1, 1)
            up_y = df['up_date'].values[:30].reshape(-1, 1)
            up_line_fitter = LinearRegression()

            try:
                up_line_fitter.fit(up_x, up_y)
                #  바이낸스가 매소거래소 => 매도거래소(업비트) 현재가 - 추세값
                # binance_price_trend = df['up_close_price'][0]-(up_line_fitter.coef_ * 60) + up_line_fitter.intercept_
                analytics_data_dict['up_coef'] = up_line_fitter.coef_[0][0]
            #
            #     # analytics_data_dict['binance_intercept'] = up_line_fitter.intercept_[0][0]
            #     # 매도 거래소 업비트의 가격 추세
            #     # analytics_data_dict['binance_price_trend'] = binance_price_trend
            except Exception as e:
                message = e
                analytics_data_dict['up_coef'] = message

            # 바이낸스의 괴리율 정도
            binance_first_obj = binance_obj.first()

            analytics_data_dict['binance_deposit_status'] = binance_first_obj.deposit_status
            analytics_data_dict['binance_withdraw_enable'] = binance_first_obj.withdraw_status
            analytics_data_dict['binance_close_price'] = binance_first_obj.close_price
            # analytics_data_dict['binance_degree_of_discrepancy'] = binance_degree_of_discrepancy
            analytics_data_dict['binance_date'] = binance_first_obj.candle_date_time_kst
            analytics_data_dict['up_date'] = up_first_obj.candle_date_time_kst
            # 바이낸스의 기대 수익률
            # analytics_data_dict['binance_expected_revenue_rate'] = binance_first_obj.expected_revenue_rate
            analytics_data_dict[
                'transaction_price'] = binance_first_obj.transaction_price + up_first_obj.transaction_price
            each_coin_analytics_dict[coin_name] = analytics_data_dict

    expected_df = pd.DataFrame(each_coin_analytics_dict).transpose()
    cut_index = expected_df[(expected_df['up_expected_revenue_rate'] <= 0) | (expected_df['binance_coef'] <= 0)
                            | (expected_df['binance_deposit_status'] is False)
                            | (expected_df['binance_withdraw_enable'] is False)
                            | (expected_df['up_deposit_status'] is False)
                            | (expected_df['up_withdraw_enable'] is False)].index
    expected_ddf = expected_df.drop(cut_index)
    # 업비트 기대수익률 * 40% + 업비트 괴리율 정도 * 14.3% +  업비트 회귀계수 * 5.7% +
    # 바이낸스(매도거래소) 회귀계수 * 2.9% + 거래대금 * 17%
    expected_ddf['total'] = \
        (expected_ddf['up_expected_revenue_rate'] / expected_ddf['up_expected_revenue_rate'].max() * 0.4) + \
        (expected_ddf['up_degree_of_discrepancy'] / expected_ddf['up_degree_of_discrepancy'].max() * 0.143) + \
        (expected_ddf['up_coef'] / expected_ddf['up_coef'].max() * 0.057) + \
        (expected_ddf['binance_coef'] / expected_ddf['binance_coef'].max() * 0.029) + \
        (expected_ddf['transaction_price'] / expected_ddf['transaction_price'].max() * 0.17)

    result_index = pd.to_numeric(expected_ddf['total']).idxmax(axis=0)

    context = {
        'coin': result_index,
        "result": each_coin_analytics_dict[result_index]
    }
    return render(request, 'market/analytics_view.html', context)
