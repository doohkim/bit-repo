import pytz
from django.shortcuts import render
from sklearn.linear_model import LinearRegression
import datetime
import numpy
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from bit_finance.models import BitFinanceExchange
from config.global_variable import selected_coin_kind
from up_bits.models import UpBitExchange, UpBitMarket

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


def analytics_view(request):
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
                                                         'binance_discrepancy_rate')[::2])

            binance_df = binance_df.rename(
                columns={binance_df.columns[0]: "binance_date", binance_df.columns[1]: "binance_close_price",
                         binance_df.columns[2]: "binance_expected_revenue_rate",
                         binance_df.columns[3]: "binance_discrepancy_rate"}
            )
            up_df = pd.DataFrame(
                up_obj.values('candle_date_time_kst', 'close_price', 'expected_revenue_rate', 'up_discrepancy_rate')
                [::2]
            )

            up_df = up_df.rename(
                columns={up_df.columns[0]: "up_date", up_df.columns[1]: "up_close_price",
                         up_df.columns[2]: "up_expected_revenue_rate", up_df.columns[3]: "up_discrepancy_rate"}
            )
            df = pd.concat([binance_df, up_df], axis=1)
            # 업비트가 매수 거래소 바이낸스가 매도 거래소 일 경우

            # 6시간 데이터 괴리율의 정도
            # (현재 괴리율 - 6시간 평균 괴리율) / 표준편차
            up_degree_of_discrepancy = (df['up_discrepancy_rate'][0] - df['up_discrepancy_rate'].mean()) / df[
                'up_discrepancy_rate'].std()
            # 업비트가 매수 거래소 바이낸스가 매도 거래소 일 경우
            # 가격 추세
            binance_x = df['binance_close_price'].values.reshape(-1, 1)
            binance_y = df['binance_date'].values.reshape(-1, 1)
            binance_line_fitter = LinearRegression()
            binance_line_fitter.fit(binance_x, binance_y)
            # 가격 추세(매도)
            # 업비트가 매소거래소 => 매도거래소(바이낸스) 현재가 - 추세값
            up_price_trend = df['binance_close_price'][0] - (
                    binance_line_fitter.coef_ * 60) + binance_line_fitter.intercept_
            analytics_data_dict['up_degree_of_discrepancy'] = up_degree_of_discrepancy
            analytics_data_dict['up_price_trend'] = up_price_trend[0][0]
            analytics_data_dict['up_expected_revenue_rate'] = up_obj.first().expected_revenue_rate

            # 바이낸스가 매수 거래소 업비트가 매도 거래소 일 경우

            # 6시간 데이터 괴리율의 정도
            # (현재 괴리율 - 6시간 평균 괴리율) / 표준편차
            binance_degree_of_discrepancy = (df['binance_discrepancy_rate'][0] - df[
                'binance_discrepancy_rate'].mean()) / df['binance_discrepancy_rate'].std()

            up_x = df['up_close_price'].values.reshape(-1, 1)
            up_y = df['up_date'].values.reshape(-1, 1)
            up_line_fitter = LinearRegression()



            # up_line_fitter.fit(up_x, up_y)
            # 바이낸스가 매소거래소 => 매도거래소(업비트) 현재가 - 추세값
            # binance_price_trend = df['up_close_price'][0] - (up_line_fitter.coef_ * 60) + up_line_fitter.intercept_
            # 매도 거래소 업비트의 가격 추세
            # analytics_data_dict['binance_price_trend'] = binance_price_trend[0][0]



            # 바이낸스의 괴리율 정도
            analytics_data_dict['binance_degree_of_discrepancy'] = binance_degree_of_discrepancy
            analytics_data_dict['binance_date'] = df['binance_date'][0]
            analytics_data_dict['up_date'] = df['up_date'][0]
            # 바이낸스의 기대 수익률
            analytics_data_dict['binance_expected_revenue_rate'] = binance_obj.first().expected_revenue_rate
            each_coin_analytics_dict[coin_name] = analytics_data_dict
    context = {
        "each_coin_analytics_dict": each_coin_analytics_dict,
    }
    return render(request, 'market/analytics_view.html', context)


def data_view(request):
    each_coin_standard_deviation_dict = dict()
    # for market_query in UpBitMarket.objects.all():
    #     coin_name = market_query.coin
    #     up_bit_query_set_list = UpBitExchange.objects.filter(full_name='BTC' + '-' + coin_name)
    #     bit_finance_query_set_list = BitFinanceExchange.objects.filter(english_name=coin_name + '/' + 'BTC')
    #
    #     if bit_finance_query_set_list and up_bit_query_set_list:
    #         up_bit_query_set_list = up_bit_query_set_list.filter(candle_date_time_kst__gte=date_time_now)
    #         bit_finance_query_set_list = bit_finance_query_set_list.filter(
    #             Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
    #             Q(candle_date_time_kst__lte=datetime_now_before_one_minute))
    #     else:
    #         continue
    #
    # each_coin_price_dict_all_time = dict()
    #
    #     each_up_bit_coin_price_list_all_time = list()
    #     each_binance_coin_price_list_all_time = list()
    #     for query in up_bit_query_set_list:
    #         up_bit_current_price = query.close_price
    #         each_up_bit_coin_price_list_all_time.append(up_bit_current_price)
    #
    #     for query in bit_finance_query_set_list:
    #         binance_current_price = query.close_price
    #         each_binance_coin_price_list_all_time.append(binance_current_price)

    ################################################마지막 정답
    each_coin_price_dict_all_time = dict()
    for coin_name in selected_coin_kind.values():

        up_bit_query_set_list = UpBitExchange.objects.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
            Q(full_name='BTC' + '-' + coin_name),

        )
        bit_finance_query_set_list = BitFinanceExchange.objects.filter(
            Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
            Q(candle_date_time_kst__lte=datetime_now_before_one_minute),
            Q(english_name=coin_name + '/' + 'BTC'),
        )
        # 시작 시점이 다르기 때문에 데이터가 다르다고 생각함...
        # 내일 부터는 데이터 개수가 같을거라고 생각함 한개당 1440
        if not up_bit_query_set_list or not bit_finance_query_set_list:
            continue

        binance_df = pd.DataFrame(list(bit_finance_query_set_list.values('candle_date_time_kst', 'close_price')[::2]))
        binance_df = binance_df.rename(
            columns={binance_df.columns[0]: "binance_date", binance_df.columns[1]: "binance_close_price"})
        up_df = pd.DataFrame(list(up_bit_query_set_list.values('candle_date_time_kst', 'close_price')[::2]))
        up_df = up_df.rename(columns={up_df.columns[0]: "up_date", up_df.columns[1]: "up_close_price"})
        df = pd.concat([binance_df, up_df], axis=1)

        # 현재 괴리율 ( 매도거래소 현재가 / 매수 거래소 현재가 )
        df['discrepancy'] = df['binance_close_price'] / df['up_close_price']
        # df['binance_reverse_discrepancy'] = df['up_close_price'] / df['binance_close_price']
        # 괴리율 정도
        degree_of_discrepancy = (df['discrepancy'][0] - df['discrepancy'].mean()) / df['discrepancy'].std()

        # 매도거래소(바이낸스) 회귀 계수 구하기
        binance_x = df['binance_close_price'].values.reshape(-1, 1)
        binance_y = df['binance_date'].values.reshape(-1, 1)
        line_fitter = LinearRegression()
        line_fitter.fit(binance_x, binance_y)
        # 절편 line_fitter.intercept_
        # 기울기 line_fitter.coef_
        # 매도거래소(바이낸스) - 가격 추세 값
        price_trend = df['binance_close_price'][0] - (line_fitter.coef_ * 60) + line_fitter.intercept_
        each_coin_price_dict_all_time['degree_of_discrepancy'] = degree_of_discrepancy
        each_coin_price_dict_all_time['price_trend'] = price_trend[0][0]
        each_coin_standard_deviation_dict[coin_name] = each_coin_price_dict_all_time

        #####################################3

        # 두개 개수가 같으면 zip 사용함
        # risk_rate_list = list()
        # reverse_risk_rate_list = list()
        # for up_query, binance_query in zip(up_bit_query_set_list, bit_finance_query_set_list):
        #     #         # 매수가 / 매도가
        #     #         risk_rate_list.append(up_query.close_price / binance_query.close_price)
        #     # 매도가 / 매수가
        #     reverse_risk_rate_list.append(binance_query.close_price / up_query.close_price)
        # up_current_close_price = up_bit_query_set_list.first().close_price
        # degree_of_discrepancy = (up_current_close_price - numpy.mean(risk_rate_list)) / numpy.std(
        #     each_up_bit_coin_price_list_all_time)
        # each_coin_standard_deviation_dict['degree_of_discrepancy'] = degree_of_discrepancy

        # 평균 구하기
        # up_bit_mean_num = numpy.mean(each_up_bit_coin_price_list_all_time)
        # up_bit_std_num = numpy.std(each_up_bit_coin_price_list_all_time)
        # each_coin_price_dict_all_time['up_mean'] = up_bit_mean_num
        # each_coin_price_dict_all_time['up_standard_deviation'] = up_bit_std_num
        #
        # binance_mean_num = numpy.mean(each_binance_coin_price_list_all_time)
        # binance_std_num = numpy.std(each_binance_coin_price_list_all_time)
        # each_coin_price_dict_all_time['binance_mean'] = binance_mean_num
        # each_coin_price_dict_all_time['binance_standard_deviation'] = binance_std_num
        #
        # each_coin_standard_deviation_dict[market_query.coin] = each_coin_price_dict_all_time

    context = {
        'each_coin_data': each_coin_standard_deviation_dict
    }
    return render(request, 'market/analytics_view.html', context)
