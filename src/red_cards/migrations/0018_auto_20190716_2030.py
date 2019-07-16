# Generated by Django 2.2.2 on 2019-07-16 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0017_appealcomment_seen_by_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='system',
            field=models.CharField(choices=[('cards-assistant', 'Cards-assistant'), ('cards-consideration', 'Cards-consideration'), ('cards-appeal', 'Cards-appeal'), ('cards-deactivate', 'Cards-deactivate'), ('api', 'Api'), ('leader', 'Leader'), ('cards-transform', 'Cards-transform'), ('cards-repayment', 'Cards-repayment'), ('cards-issue', 'Cards-issue'), ('experiments', 'Experiments')], max_length=255, verbose_name='System'),
        ),
    ]
