# Generated by Django 2.2.2 on 2019-07-08 00:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0010_auto_20190706_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]