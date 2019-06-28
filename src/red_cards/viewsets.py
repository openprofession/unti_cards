from rest_framework import viewsets

from red_cards.models import Card
from red_cards.serializers import CardSerializer

from django_filters.rest_framework import DjangoFilterBackend
import django_filters


# https://stackoverflow.com/questions/24414926/using-custom-methods-in-filter-with-django-rest-framework
# https://stackoverflow.com/questions/37183943/django-how-to-filter-by-date-with-django-rest-framework
# https://stackoverflow.com/questions/11508744/django-models-filter-by-foreignkey
def last_status_lte(queryset, value, *args, **kwargs):
    return queryset.filter(statuschange__change_dt__lte=value)


class ListingFilter(django_filters.FilterSet):
    class Meta:
        model = Card
        fields = (
            'uuid',
            'user',             # идентификатор пользователя
            'event_uuid',       # идентификатор мероприятия
            'type',             # тип карточки
            'status',           # статус карточки
            'start_time',       # start_time (начало промежутка времени изменения последнего статуса карточки)
            'end_time',         # end_time (конец промежутка времени последнего изменения статуса)

        )

    start_time = django_filters.DateTimeFilter(method='_last_status_min')
    end_time = django_filters.DateTimeFilter(method='_last_status_max')
    # last_status_max = django_filters.DateTimeFilter(field_name="statuschange__change_dt", lookup_type='lte')

    def _last_status_min(self, queryset, field_name, value):
        return queryset.filter(statuschange__change_dt__gte=value)

    def _last_status_max(self, queryset, field_name, value):
        return queryset.filter(statuschange__change_dt__lte=value)


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    # filter_backends = (DjangoFilterBackend,)
    filter_class = ListingFilter


