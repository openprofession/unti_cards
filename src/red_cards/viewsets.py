from rest_framework import viewsets

from red_cards.models import Card
from red_cards.serializers import CardSerializer


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer