# Generated by Django 2.2.20 on 2021-05-10 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('up_bits', '0017_auto_20210504_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='upbitexchange',
            name='transaction_price',
            field=models.FloatField(default=0.0, verbose_name='거래대금'),
        ),
    ]
