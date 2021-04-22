import ccxt
from django.core.management.base import BaseCommand


def search_binance_api():
    binance = ccxt.binance()
    market = binance.fetch_tickers()

    for kinds in market:
        # symbol (가상화폐 이름 / 거래되는 시장)
        print('가상화폐 이름 / 거래되는 시장:       ', market[kinds]['symbol'])
        # 현재시간
        print('현재시간:                           ', market[kinds]['datetime'])
        # 고가
        print('고가:                               ', market[kinds]['high'])
        # 저가
        print('저가:                               ', market[kinds]['low'])
        # 시가
        print('시가:                               ', market[kinds]['open'])
        # 종가
        print('종가:                               ', market[kinds]['close'])
        # 매도 1호가
        print('매도 1호가:                          ', market[kinds]['ask'])
        # 매도 1호가 물량
        print('매도 1호가 물량:                     ', market[kinds]['askVolume'])
        # 매수 1호가
        print('매수 1호가:                          ', market[kinds]['bid'])
        # 매수 1호가 물량
        print('매수 1호가 물량:                     ', market[kinds]['bidVolume'])
        # 거래량 정확 x
        print('거래량:                              ', market[kinds]['info']['count'])
        print('거래량:                              ', market[kinds]['info']['volume'])
        print('거래량:                              ', market[kinds]['info']['quoteVolume'])
        print('=============================================================================')


class Command(BaseCommand):
    help = 'Insert book tuple into database'

    def handle(self, *args, **options):

        search_binance_api()
        self.stdout.write(self.style.SUCCESS('Successfully closed poll'))
