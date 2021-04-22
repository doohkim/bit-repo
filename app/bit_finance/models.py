from django.db import models


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
