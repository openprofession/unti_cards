# Generated by Django 2.2.2 on 2019-07-02 14:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0007_auto_20190630_1708'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='event_uuid',
            field=models.CharField(blank=True, help_text='идентификатор мероприятия из Labs, string', max_length=255, null=True, verbose_name='Event uuid'),
        ),
        migrations.AlterField(
            model_name='card',
            name='incident_dt',
            field=models.DateTimeField(help_text='время нарушения, string, дата в формате “YYYY-MM-DD hh:mm”', verbose_name='Incident date'),
        ),
        migrations.AlterField(
            model_name='card',
            name='leader_id',
            field=models.IntegerField(help_text='идентификатор пользователя в Leader Id, integer', verbose_name='Leader'),
        ),
        migrations.AlterField(
            model_name='card',
            name='place_uuid',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='идентификатор места проведения мероприятия из Labs, string'),
        ),
        migrations.AlterField(
            model_name='card',
            name='reason',
            field=models.TextField(help_text='причина выдачи карточки, string', max_length=512, verbose_name='Reason'),
        ),
        migrations.AlterField(
            model_name='card',
            name='source',
            field=models.CharField(choices=[('cards', 'Cards'), ('leader', 'Leader'), ('experiments', 'Experiments')], help_text='источник выдачи карточки, string, допустимые значения [“Cards”, “Leader”, “Experiments”]', max_length=255, verbose_name='Source'),
        ),
        migrations.AlterField(
            model_name='card',
            name='type',
            field=models.CharField(choices=[('red', 'Red'), ('yellow', 'Yellow'), ('green', 'Green')], help_text='тип карточки, string, допустимые значения: [“red”, “yellow”, “green”]', max_length=255, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='card',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='идентификатор карточки в системе, string', primary_key=True, serialize=False, unique=True, verbose_name='uuid'),
        ),
        migrations.AlterField(
            model_name='status',
            name='name',
            field=models.CharField(choices=[('initiated', 'Initiated'), ('published', 'Published'), ('consideration', 'Consideration'), ('issued', 'Issued'), ('eliminated', 'Eliminated'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('recommended', 'Recommended')], max_length=255, verbose_name='Name'),
        ),
    ]
