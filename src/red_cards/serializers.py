from rest_framework import serializers
from django.conf import settings
from . import models
from red_cards.models import Card
from django.utils.translation import ugettext_lazy as _


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        # fields = '__all__'

        fields = (
            'uuid',
            'type',             #
            'reason',           #
            'description',
            'source',           #
            'leader_id',        #
            'incident_dt',
            'event_uuid',
            'place_uuid',
            'status',
            'last_status',
        )
        read_only_fields = (
            'uuid',
            'status',
        )
    #
    status = serializers.SerializerMethodField(
        source='get_status',
        help_text=_('статус карточки, string, допустимые значения: '
                    '[“initiated”, “published”, “consideration”, “issued”, '
                    '“eliminated”]'),
    )

    def get_status(self, obj):
        status = models.Status.objects.filter(
            card=obj
        ).filter(
            is_public=True
        ).order_by('-change_dt').first()

        result = {
            'name': 'undefined',
        }

        if status:
            result.update({
                'name': status.name,
                'date': status.change_dt.strftime(
                    settings.REST_FRAMEWORK['DATETIME_FORMAT']
                ),
                # 'system':       status.system,
            })
        #
        return result

    def create(self, validated_data):
        # 2. post запрос на создание
        # красной или желтой карточки - создаются в статусе initiated,
        # если зеленая - то после создания сразу переходит в published

        return super(CardSerializer, self).create(validated_data)

