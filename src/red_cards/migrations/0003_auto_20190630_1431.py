# Generated by Django 2.2.2 on 2019-06-30 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0002_auto_20190628_2007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='uuid',
        ),
        migrations.RemoveField(
            model_name='status',
            name='card',
        ),
        migrations.AlterField(
            model_name='card',
            name='leader_id',
            field=models.IntegerField(unique=True, verbose_name='Leader'),
        ),
    ]
