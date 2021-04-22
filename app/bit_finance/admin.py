from django.contrib import admin
from import_export import resources

from .models import BitFinanceCoinExchange
from import_export.admin import ImportExportModelAdmin


class BitFinanceResource(resources.ModelResource):
    class Meta:
        model = BitFinanceCoinExchange
        export_order = (
            'id',
            'market',
            'kind',
            'english_name',
            'korean_name',
            'candle_date_time_kst',
            'open_price',
            'high_price',
            'low_price',
            'close_price',
            'volume'
        )


class BitFinanceCoinExchangeAdmin(ImportExportModelAdmin):
    resource_class = BitFinanceResource


admin.site.register(BitFinanceCoinExchange, BitFinanceCoinExchangeAdmin)
