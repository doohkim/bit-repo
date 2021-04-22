from django.db import models


class UpBitCandleMinute(models.Model):
    market = models.CharField('마켓명', max_length=30)
    candle_date_time_utc = models.DateTimeField('캔들 기준 시각(UTC 기준)', blank=True, null=True)
    candle_date_time_kst = models.DateTimeField('캔들 기준 시각(KST 기준)',  unique=True)
    opening_price = models.FloatField('시가')
    low_price = models.FloatField('저가')
    high_price = models.FloatField('고가')
    trade_price = models.FloatField('종가')
    volume = models.FloatField('거래량' )
    timestamp = models.CharField('해당 캔들에서 마지막 틱이 저장된 시각', blank=True, null=True, max_length=130)
    candle_acc_trade_price = models.FloatField('누적 거래 금액', blank=True, null=True)
    candle_acc_trade_volume = models.FloatField('누적 거래량', blank=True, null=True)
    unit = models.IntegerField('분 단위(유닌)', blank=True, null=True)
    created_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pk']
        verbose_name = '업비트 현제 시세 분봉'
        verbose_name_plural = '%s 목록' % verbose_name

    def __str__(self):
        return f'[업비트 현제 시세 분봉 ] {self.candle_date_time_kst} | 종가 : {self.trade_price}'
