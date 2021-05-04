from django.db import models

import datetime
from datetime import timedelta

from up_bits.models import UpBitMarket

date_time_now = datetime.datetime.now() + timedelta(hours=9) - timedelta(minutes=1)
datetime_now_before_one_minute = datetime.datetime(date_time_now.year,
                                                   date_time_now.month,
                                                   date_time_now.day,
                                                   date_time_now.hour,
                                                   date_time_now.minute)


class BitFinanceCoinExchange(models.Model):
    market = models.CharField('시장 거래소', max_length=10)
    kind = models.CharField('코인 종류', max_length=20)
    english_name = models.CharField('코인 영어이름', max_length=50, null=True, blank=True)
    korean_name = models.CharField('한국 코인 이름', max_length=50, null=True, blank=True)
    candle_date_time_kst = models.DateTimeField('코인 거래된 시간', )
    open_price = models.FloatField('시가', )
    high_price = models.FloatField('고가', )
    low_price = models.FloatField('저가', )
    close_price = models.FloatField('종가', )
    volume = models.FloatField('종가', )

    class Meta:
        ordering = ['-candle_date_time_kst']
        verbose_name = '바이낸스 코인 현재가 '
        verbose_name_plural = '%s 목록' % verbose_name

    def __str__(self):
        return f'MARKET: {self.english_name} | CLOSE PRICE: {self.close_price}'


class BitFinanceExchange(models.Model):
    market = models.ForeignKey(UpBitMarket, on_delete=models.PROTECT, help_text="마켓")
    full_name = models.CharField('코인-거래소', max_length=50, null=True, blank=True)
    english_name = models.CharField('코인 영어이름', max_length=50, null=True, blank=True)
    korean_name = models.CharField('한국 코인 이름', max_length=50, null=True, blank=True)
    withdraw_status = models.BooleanField('출금 상태', default=False)
    deposit_status = models.BooleanField('입금 상태', default=False)
    candle_date_time_kst = models.DateTimeField('코인 거래된 시간', )
    bit_coin_value = models.FloatField('비트코인 가격', default=0)
    expected_revenue_rate = models.FloatField('기대수익률', default=0.0)
    binance_discrepancy_rate = models.FloatField('괴리율 정도', default=0.0)
    open_price = models.FloatField('시가', )
    high_price = models.FloatField('고가', )
    low_price = models.FloatField('저가', )
    close_price = models.FloatField('종가', )
    volume = models.FloatField('거래량', )

    class Meta:
        ordering = ['-candle_date_time_kst']
        verbose_name = '바이낸스 코인 시세가 '
        verbose_name_plural = '%s 목록' % verbose_name

    def __str__(self):
        return f'MARKET: {self.english_name} | CLOSE PRICE: {self.close_price}'

    @property
    def deposit_amount(self):
        bit_exchange_before_one_minute = BitFinanceExchange.objects.filter(
            candle_date_time_kst=datetime_now_before_one_minute).filter(english_name=self.english_name)[0]
        market_info = bit_exchange_before_one_minute.market
        # 매수가
        close_price = bit_exchange_before_one_minute.close_price
        binance_percentage = 0.999
        # 바이낸스 비트코인 가격
        bit_coin_value = bit_exchange_before_one_minute.bit_coin_value
        init_have_btc_amount = 1000000 / bit_coin_value
        alt_purchase_price = init_have_btc_amount * binance_percentage / close_price
        withdraw_fee = market_info.binance_withdraw_fee

        # ALT 매수량 - 출금수수료
        alt_deposit_amount = alt_purchase_price - withdraw_fee
        upbit_percentage = 0.9975
        upbit_exchange = market_info.upbitexchange_set.filter(candle_date_time_kst=datetime_now_before_one_minute)
        if not upbit_exchange:
            return f'바이낸스에 있는 {bit_exchange_before_one_minute.korean_name} 코인이 업비트에 존재 하지 않는다'
        upbit_price = upbit_exchange[0].close_price
        final_have_btc_coin = alt_deposit_amount * upbit_percentage * upbit_price
        proposed_get_money = ((final_have_btc_coin / init_have_btc_amount) - 1) * 100
        return proposed_get_money

    @property
    def discrepancy_rate(self):

        bit_exchange_before_one_minute = BitFinanceExchange.objects.filter(
            candle_date_time_kst=datetime_now_before_one_minute).filter(english_name=self.english_name)[0]
        binance_current_coin_value = bit_exchange_before_one_minute.close_price
        up_bit_query_set = bit_exchange_before_one_minute.market.upbitexchange_set.filter(
            candle_date_time_kst=datetime_now_before_one_minute)
        # print(up_bit_query_set)
        if not up_bit_query_set:
            return f'바이낸스에 있는 {bit_exchange_before_one_minute.korean_name} 코인이 업비트에 존재 하지 않는다'
        up_bit_current_coin_value = up_bit_query_set[0].close_price
        # 업비트 / 바이낸스
        return up_bit_current_coin_value / binance_current_coin_value
