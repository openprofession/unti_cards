from rest_framework import serializers

from red_cards.models import Card


class CardSerializer(serializers.ModelSerializer):
    """
        Карточки (красная, желтая, зеленая)
    """
    class Meta:
        model = Card
        fields = '__all__'
