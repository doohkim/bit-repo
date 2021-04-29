from django.shortcuts import render
from sklearn.linear_model import LinearRegression
import datetime
import numpy
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from bit_finance.models import BitFinanceExchange
from up_bits.models import UpBitExchange, UpBitMarket

date_time_now = timezone.now() + timezone.timedelta(hours=3) - timezone.timedelta(minutes=1)
date_time_now_one_minute_ago = timezone.now() + timezone.timedelta(hours=9) - timezone.timedelta(minutes=1)
datetime_now_before_one_minute = datetime.datetime(date_time_now_one_minute_ago.year,
                                                   date_time_now_one_minute_ago.month,
                                                   date_time_now_one_minute_ago.day,
                                                   date_time_now_one_minute_ago.hour,
                                                   date_time_now_one_minute_ago.minute)
datetime_now_six_hours_ago = datetime.datetime(date_time_now.year,
                                               date_time_now.month,
                                               date_time_now.day,
                                               date_time_now.hour,
                                               date_time_now.minute)


def data_view(request):
    each_coin_standard_deviation_dict = dict()
    for market_query in UpBitMarket.objects.all():
        coin_name = market_query.coin
        up_bit_query_set_list = UpBitExchange.objects.filter(full_name='BTC' + '-' + coin_name)
        bit_finance_query_set_list = BitFinanceExchange.objects.filter(english_name=coin_name + '/' + 'BTC')

        if bit_finance_query_set_list and up_bit_query_set_list:
            up_bit_query_set_list = up_bit_query_set_list.filter(candle_date_time_kst__gte=date_time_now)
            bit_finance_query_set_list = bit_finance_query_set_list.filter(
                Q(candle_date_time_kst__gte=datetime_now_six_hours_ago),
                Q(candle_date_time_kst__lte=datetime_now_before_one_minute))
        else:
            continue

        each_coin_price_dict_all_time = dict()

        each_up_bit_coin_price_list_all_time = list()
        each_binance_coin_price_list_all_time = list()
        for query in up_bit_query_set_list:
            up_bit_current_price = query.close_price
            each_up_bit_coin_price_list_all_time.append(up_bit_current_price)

        for query in bit_finance_query_set_list:
            binance_current_price = query.close_price
            each_binance_coin_price_list_all_time.append(binance_current_price)

        ################################################마지막 정답

        # binance_df = pd.DataFrame(list(bit_finance_query_set_list.values('candle_date_time_kst', 'close_price')))
        # binance_df.rename(columns={binance_df[0]: "binance_date", binance_df[1]: "binance_close_price"})
        # up_df = pd.DataFrame(list(up_bit_query_set_list.values('candle_date_time_kst', 'close_price')))
        # up_df.rename(columns={up_df[0]: "up_date", up_df[1]: "up_close_price"})
        #
        # df = pd.concat([binance_df, up_df], axis=1)
        #
        # df['upbit_discrepancy'] = df['binance_close_price'] / df['up_close_price']
        # df['binance_reverse_discrepancy'] = df['up_close_price'] / df['binance_close_price']
        # # 괴리율 컬럼
        # degree_of_discrepancy = (df['upbit_discrepancy'][0] - df['upbit_discrepancy'].mean()) / df[
        #     'upbit_discrepancy'].std()
        #
        # x = df['binance_close_price'].values.reshape(-1, 1)
        # y = df['binance_date']
        # fit = LinearRegression().fit(x, y)
        # # 절편 fit.intercept_
        # # 기울기 fit.coef_
        # price_trend = df['binance_close_price'][0] - (fit.coef_ * 60) + fit.intercept_
        # each_coin_price_dict_all_time['degree_of_discrepancy'] = degree_of_discrepancy
        # each_coin_price_dict_all_time['price_trend'] = price_trend
        # each_coin_standard_deviation_dict[market_query.coin] = each_coin_price_dict_all_time

        #####################################3


        # 두개 개수가 같으면 zip 사용함
        # risk_rate_list = list()
        # reverse_risk_rate_list = list()
        # for up_query, binance_query in zip(up_bit_query_set_list, bit_finance_query_set_list):
        #     #         # 매수가 / 매도가
        #     #         risk_rate_list.append(up_query.close_price / binance_query.close_price)
        #     # 매도가 / 매수가
        #     reverse_risk_rate_list.append(binance_query.close_price / up_query.close_price)
        up_current_close_price = up_bit_query_set_list.first().close_price
        # degree_of_discrepancy = (up_current_close_price - numpy.mean(risk_rate_list)) / numpy.std(
        #     each_up_bit_coin_price_list_all_time)
        # each_coin_standard_deviation_dict['degree_of_discrepancy'] = degree_of_discrepancy

        # 평균 구하기
        up_bit_mean_num = numpy.mean(each_up_bit_coin_price_list_all_time)
        up_bit_std_num = numpy.std(each_up_bit_coin_price_list_all_time)
        each_coin_price_dict_all_time['up_mean'] = up_bit_mean_num
        each_coin_price_dict_all_time['up_standard_deviation'] = up_bit_std_num

        binance_mean_num = numpy.mean(each_binance_coin_price_list_all_time)
        binance_std_num = numpy.std(each_binance_coin_price_list_all_time)
        each_coin_price_dict_all_time['binance_mean'] = binance_mean_num
        each_coin_price_dict_all_time['binance_standard_deviation'] = binance_std_num

        each_coin_standard_deviation_dict[market_query.coin] = each_coin_price_dict_all_time

    context = {
        'each_coin_data' : each_coin_standard_deviation_dict
    }
    return render(request, 'data/post.html', context)
