from rest_framework import viewsets

from red_cards.models import Card
from red_cards.serializers import CardSerializer


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    filterset_fields = (
        'uuid',
        'user',             # идентификатор пользователя
        'event_uuid',       # идентификатор мероприятия
        'type',             # тип карточки
        'status',           # статус карточки
        # '',     # start_time (начало промежутка времени изменения последнего статуса карточки)
        # '',     # end_time (конец промежутка времени последнего изменения статуса)

    )


