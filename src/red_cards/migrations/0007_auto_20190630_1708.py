# Generated by Django 2.2.2 on 2019-06-30 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0006_auto_20190630_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='leader_id',
            field=models.IntegerField(verbose_name='Leader'),
        ),
    ]
