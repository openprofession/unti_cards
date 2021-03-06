# Generated by Django 2.2.2 on 2019-07-06 14:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0009_auto_20190705_2106'),
    ]

    operations = [
        migrations.AddField(
            model_name='appeal',
            name='date_assign',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date assign to executive'),
        ),
        migrations.AddField(
            model_name='appeal',
            name='date_finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date finished'),
        ),
        migrations.AddField(
            model_name='appeal',
            name='executive',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Executive'),
        ),
        migrations.AlterField(
            model_name='appeal',
            name='status',
            field=models.CharField(choices=[('new', 'New'), ('in_work', 'In work'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='new', max_length=255, verbose_name='status'),
        ),
    ]
