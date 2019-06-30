from rest_framework import serializers
from django.conf import settings
from . import models
from red_cards.models import Card


class CardSerializer(serializers.ModelSerializer):
    """
        Карточки (красная, желтая, зеленая)
    """
    class Meta:
        model = Card
        # fields = '__all__'

        fields = (
            'uuid',
            'type',             #
            'reason',           #
            'source',           #
            'user',             #
            'incident_dt',
            'event_uuid',
            'place_uuid',
            'status',
        )
        read_only_fields = (
            'uuid',
            'status',
        )
    #
    # https://stackoverflow.com/questions/18396547/django-rest-framework-adding-additional-field-to-modelserializer
    user = serializers.IntegerField(source='leader_id')

    status = serializers.SerializerMethodField(
        source='get_status'
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
