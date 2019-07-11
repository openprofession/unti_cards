# Generated by Django 2.2.2 on 2019-07-11 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0014_auto_20190710_0235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='system',
            field=models.CharField(choices=[('cards-assistant', 'Cards-assistant'), ('cards-consideration', 'Cards-consideration'), ('cards-appeal', 'Cards-appeal'), ('api', 'Api'), ('leader', 'Leader'), ('cards-transform', 'Cards-transform'), ('cards-repayment', 'Cards-repayment'), ('experiments', 'Experiments'), ('cards-moderator', 'Cards-moderator'), ('undefined', 'Undefined')], max_length=255, verbose_name='System'),
        ),
    ]