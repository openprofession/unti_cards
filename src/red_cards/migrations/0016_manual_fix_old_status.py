# Created by jen on Sat Jul 13 17:43:16 UTC 2019

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0015_auto_20190713_2042'),
    ]

    def fix_status(apps, schema_editor):
        """
            https://stackoverflow.com/questions/39739439/django-insert-default-data-after-migrations
        """
        from ..models import Card, Status
        for card in Card.objects.all():
            last_status = card.get_status()
            if last_status:
                card.current_status = last_status
                card.save()
            else:
                card.set_status(
                    system=Status.SYSTEM_UNDEFINED,
                    name=Status.NAME_INITIATED,
                )
        #

    operations = [
        migrations.RunPython(fix_status),
    ]
