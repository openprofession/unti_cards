# coding: utf-8
import django_filters

from rest_framework import viewsets
from rest_framework import mixins

from red_cards.models import Card, Status
from red_cards.serializers import CardSerializer

from django.utils.translation import ugettext_lazy as _

from rest_framework.permissions import IsAuthenticated


class ListingFilter(django_filters.FilterSet):
    class Meta:
        model = Card
        fields = (
            'uuid',
            'reason',
            'source',
            'last_status',
            'leader_id',        # идентификатор пользователя
            'event_uuid',       # идентификатор мероприятия
            'type',             # тип карточки
            'start_time',       # start_time (начало промежутка времени изменения последнего статуса карточки)
            'end_time',         # end_time (конец промежутка времени последнего изменения статуса)

        )
    #

    # @classmethod
    # def filter_for_field(cls, field, field_name, lookup_expr='exact'):
    #     filter = super(ListingFilter, cls).filter_for_field(field, field_name, lookup_expr)
    #     filter.extra['help_text'] = field.help_text
    #     return filter

    start_time = django_filters.DateTimeFilter(
        method='_last_status_min',
        help_text=_('начало промежутка времени, string, дата в формате '
                    '“YYYY-MM-DD hh:mm”'),
    )
    end_time = django_filters.DateTimeFilter(
        method='_last_status_max',
        help_text=_('конец промежутка времени, string, дата в формате '
                    '“YYYY-MM-DD hh:mm”'),
    )

    def _last_status_min(self, queryset, field_name, value):
        # https://stackoverflow.com/questions/24414926/using-custom-methods-in-filter-with-django-rest-framework
        # https://stackoverflow.com/questions/37183943/django-how-to-filter-by-date-with-django-rest-framework
        # https://stackoverflow.com/questions/11508744/django-models-filter-by-foreignkey
        return queryset.filter(status__change_dt__gte=value)

    def _last_status_max(self, queryset, field_name, value):
        return queryset.filter(status__change_dt__lte=value)


class CardViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
        Карточки
    """
    # permission_classes = (HasAPIKey, )
    permission_classes = (IsAuthenticated, )

    queryset = Card.objects.exclude(
        last_status__in=Status.PRIVATE_STATUSES
    ).all()
    serializer_class = CardSerializer
    # filter_backends = (DjangoFilterBackend,)
    filter_class = ListingFilter
