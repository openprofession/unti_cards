# Generated by Django 2.2.2 on 2019-09-11 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0022_auto_20190911_1853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appeal',
            name='file',
            field=models.FileField(blank=True, max_length=2621440, null=True, upload_to='', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='appealcomment',
            name='file',
            field=models.FileField(blank=True, max_length=2621440, null=True, upload_to='', verbose_name='file'),
        ),
    ]
