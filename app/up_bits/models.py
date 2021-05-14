from django.db import models

import datetime
from datetime import timedelta


class UpBitMarket(models.Model):
    coin = models.CharField('코인 종류', max_length=10, unique=True)
    up_bit_withdraw_fee = models.FloatField('업비트출금수수로', default=0.0)
    up_bit_deposit_fee = models.FloatField('업비트입금수수료', default=0.0)
    up_bit_minimum_with_draw_amount = models.FloatField('업비트최소출금액', blank=True, null=True, default=0.0)
    binance_withdraw_fee = models.FloatField('바이낸스출금수수로', default=0.0)
    binance_deposit_fee = models.FloatField('바이낸스입금수수료', default=0.0)
    binance_minimum_with_draw_amount = models.FloatField('바이낸스최소출금액', null=True, blank=True, default=0.0)

    class Meta:
        ordering = ['-pk']
        verbose_name = '업비트 마켓 정보'
        verbose_name_plural = '%s 목록' % verbose_name
        # unique_together = ('paygouser', 'order_number', '')

    def __str__(self):
        return f'코인 : {self.coin} | 수수료 {self.up_bit_withdraw_fee}'


class UpBitExchange(models.Model):
    market = models.ForeignKey(UpBitMarket, on_delete=models.PROTECT, help_text="마켓")
    full_name = models.CharField('코인-거래소', max_length=20, null=True, blank=True)
    english_name = models.CharField('코인 영어이름', max_length=50, null=True, blank=True)
    korean_name = models.CharField('한국 코인 이름', max_length=50, null=True, blank=True)
    withdraw_status = models.BooleanField('출금 상태', default=False)
    deposit_status = models.BooleanField('입금 상태', default=False)
    candle_date_time_kst = models.DateTimeField('코인 거래된 시간', )
    bit_coin_value = models.FloatField('비트코인 가격', default=0)
    expected_revenue_rate = models.FloatField('기대수익률', default=0.0)
    up_discrepancy_rate = models.FloatField('괴리율 정도', default=0.0)
    open_price = models.FloatField('시가', )
    high_price = models.FloatField('고가', )
    low_price = models.FloatField('저가', )
    close_price = models.FloatField('종가', )
    volume = models.FloatField('거래량', )
    transaction_price = models.FloatField('거래대금', default=0.0)

    class Meta:
        ordering = ['-candle_date_time_kst']
        verbose_name = '업비트 코인 시세가 '
        verbose_name_plural = '%s 목록' % verbose_name

    def __str__(self):
        return f'MARKET: {self.full_name} | CLOSE PRICE: {self.close_price}'

    @property
    def deposit_amount(self):
        date_time_now = datetime.datetime.now() + timedelta(hours=9) - timedelta(minutes=1)
        datetime_now_before_one_minute = datetime.datetime(date_time_now.year,
                                                           date_time_now.month,
                                                           date_time_now.day,
                                                           date_time_now.hour,
                                                           date_time_now.minute)
        up_bit_exchange_before_one_minute = UpBitExchange.objects.filter(
            candle_date_time_kst=datetime_now_before_one_minute).filter(english_name=self.english_name)[0]
        market_info = up_bit_exchange_before_one_minute.market
        # 매수가
        close_price = up_bit_exchange_before_one_minute.close_price
        # 거래수수료율 = 매수거래소에서의 거래수수료율(정률)
        percentage = 0.9975
        # 당초BTC보유량
        bit_coin_value = up_bit_exchange_before_one_minute.bit_coin_value
        init_have_btc_amount = 1000000 / bit_coin_value
        # ALT 매수량 = 당초 BTC 보유량 * (1-거래수수료율) / 매수가
        alt_purchase_price = init_have_btc_amount * percentage / close_price
        # 출금수수료 = 매수거래소에서의 해당 해당코인의 출금 수수료(정액)
        withdraw_fee = market_info.up_bit_withdraw_fee
        # ALT 입금량 = ALT 매수량 - 출금수수료
        alt_deposit_amount = alt_purchase_price - withdraw_fee
        # 매도거래소
        # 매도거래소에서의거래수수료율(정률) 바이낸스 출금수수료
        binance_percentage = 0.999
        # 매도가 = 매도거래소에서의 해당코인 시장가
        bit_exchange = market_info.bitfinanceexchange_set.filter(candle_date_time_kst=datetime_now_before_one_minute)
        if not bit_exchange:
            return f'업비트에 있는 {up_bit_exchange_before_one_minute.full_name} 코인이 바이낸스에 존재 하지 않는다'
        bit_price = bit_exchange[0].close_price
        # 최종 BTC 보유량 = ALT 입금량 * (1 - 거래수수료율) * 매도가
        final_have_btc_coin = alt_deposit_amount * binance_percentage * bit_price
        # ((최종BTC 보유량 / 당초BTC보유량) -1) *100
        proposed_get_money = ((final_have_btc_coin / init_have_btc_amount) - 1) * 100
        return proposed_get_money


class UpExchange(models.Model):
    market = models.ForeignKey(UpBitMarket, on_delete=models.CASCADE, help_text="마켓")
    full_name = models.CharField('코인-거래소', max_length=20, null=True, blank=True)
    english_name = models.CharField('코인 영어이름', max_length=50, null=True, blank=True)
    korean_name = models.CharField('한국 코인 이름', max_length=50, null=True, blank=True)
    withdraw_status = models.BooleanField('출금 상태', default=False)
    deposit_status = models.BooleanField('입금 상태', default=False)
    candle_date_time_kst = models.DateTimeField('코인 거래된 시간', )
    bit_coin_value = models.FloatField('비트코인 가격', default=0)
    expected_revenue_rate = models.FloatField('기대수익률', default=0.0)
    discrepancy_rate = models.FloatField('괴리율 정도', default=0.0)
    open_price = models.FloatField('시가', )
    high_price = models.FloatField('고가', )
    low_price = models.FloatField('저가', )
    close_price = models.FloatField('종가', )
    volume = models.FloatField('거래량', )
    transaction_price = models.FloatField('거래대금', default=0.0)

    class Meta:
        ordering = ['-candle_date_time_kst']
        verbose_name = '업비트 코인 시세가 '
        verbose_name_plural = '%s 목록' % verbose_name

    def __str__(self):
        return f'MARKET: {self.full_name} | CLOSE PRICE: {self.close_price}'
