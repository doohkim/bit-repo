from rest_framework import serializers

from search.models import UpBitCandleMinute


class UpBitCandleMinuteSerializer(serializers.ModelSerializer):
    candle_date_time_kst = serializers.DateTimeField(format="%Y-%m-%dT%H:%M", required=True)

    class Meta:
        model = UpBitCandleMinute
        fields = '__all__'
