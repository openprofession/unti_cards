# coding: utf-8
import django_filters

from rest_framework import viewsets

from red_cards.models import Card
from red_cards.serializers import CardSerializer

from rest_framework_api_key.permissions import HasAPIKey


class ListingFilter(django_filters.FilterSet):
    class Meta:
        model = Card
        fields = (
            # 'uuid',
            'leader_id',        # идентификатор пользователя
            'event_uuid',       # идентификатор мероприятия
            'type',             # тип карточки
            'start_time',       # start_time (начало промежутка времени изменения последнего статуса карточки)
            'end_time',         # end_time (конец промежутка времени последнего изменения статуса)

        )
    #

    start_time = django_filters.DateTimeFilter(method='_last_status_min')
    end_time = django_filters.DateTimeFilter(method='_last_status_max')

    def _last_status_min(self, queryset, field_name, value):
        # https://stackoverflow.com/questions/24414926/using-custom-methods-in-filter-with-django-rest-framework
        # https://stackoverflow.com/questions/37183943/django-how-to-filter-by-date-with-django-rest-framework
        # https://stackoverflow.com/questions/11508744/django-models-filter-by-foreignkey
        return queryset.filter(status__change_dt__gte=value)

    def _last_status_max(self, queryset, field_name, value):
        return queryset.filter(status__change_dt__lte=value)


class CardViewSet(viewsets.ModelViewSet):
    permission_classes = (HasAPIKey, )

    queryset = Card.objects.all()
    serializer_class = CardSerializer
    # filter_backends = (DjangoFilterBackend,)
    filter_class = ListingFilter
