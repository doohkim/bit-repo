from django.contrib import admin
from import_export import resources

from .models import UpBitCoinExchange
from import_export.admin import ImportExportModelAdmin


class UpBitCoinExchangeResource(resources.ModelResource):
    class Meta:
        model = UpBitCoinExchange


class UpBitCoinExchangeAdmin(ImportExportModelAdmin):
    resource_class = UpBitCoinExchangeResource


admin.site.register(UpBitCoinExchange, UpBitCoinExchangeAdmin)