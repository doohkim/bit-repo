# Generated by Django 2.2.20 on 2021-05-03 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('up_bits', '0015_auto_20210503_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='upbitexchange',
            name='up_discrepancy_rate',
            field=models.FloatField(default=0.0, verbose_name='괴리율 정도'),
        ),
    ]
