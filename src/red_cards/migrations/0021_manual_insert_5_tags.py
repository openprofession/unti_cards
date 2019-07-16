# Created by jen on Tue Jul 16 11:21:55 UTC 2019

from django.db import migrations
# https://docs.djangoproject.com/en/2.2/ref/migration-operations/#writing-your-own
from django.db.migrations.operations.base import Operation

from ..models import AppealTag


class Add5TagsOperation(Operation):
    _tags = (
            'нет на острове',
            'болезнь',
            'уехал по уваж. причине',
            'неточность системы',
            'иное',
        )

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        for tag_name in self._tags:
            AppealTag.objects.create(name=tag_name)
        #

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        for tag_name in self._tags:
            tag = AppealTag.objects.filter(
                name_hash=AppealTag.gen_hash(tag_name)
            ).first()
            if tag:
                tag.delete()
        #


class Migration(migrations.Migration):

    dependencies = [
        ('red_cards', '0020_appeal_tag'),
    ]

    operations = [
        Add5TagsOperation(),
    ]
