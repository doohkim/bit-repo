# Generated by Django 2.2.20 on 2021-04-20 01:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UpBitCoinExchange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('market', models.CharField(max_length=10, verbose_name='시장 거래소')),
                ('kind', models.CharField(max_length=20, verbose_name='코인 종류')),
                ('english_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='코인 영어이름')),
                ('korean_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='한국 코인 이름')),
                ('candle_date_time_kst', models.DateTimeField(verbose_name='코인 거래된 시간')),
                ('open_price', models.FloatField(verbose_name='시가')),
                ('high_price', models.FloatField(verbose_name='고가')),
                ('low_price', models.FloatField(verbose_name='저가')),
                ('close_price', models.FloatField(verbose_name='종가')),
                ('volume', models.FloatField(verbose_name='종가')),
            ],
            options={
                'verbose_name': '업비트 코인 현재가 ',
                'verbose_name_plural': '업비트 코인 현재가  목록',
                'ordering': ['-candle_date_time_kst'],
            },
        ),
    ]
