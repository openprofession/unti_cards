# Generated by Django 2.2.2 on 2019-07-05 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0006_appeal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='unti_id',
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
    ]
