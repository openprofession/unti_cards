from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

"""
https://openprofessions.atlassian.net/browse/DEVUNTI-2

"""
User = get_user_model()

# from rest_framework_api_key.models import AbstractAPIKey


class Status(models.Model):
    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')
    #

    uuid = models.CharField(
        # 123e4567-e89b-12d3-a456-426655440000
        verbose_name=_('uuid'),
        max_length=255,
        unique=True,
        null=False, blank=False,
    )

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        null=True, blank=True,
    )

    description = models.TextField(
        verbose_name=_('Description'),
        null=True, blank=True,
    )

    def __str__(self):
        return '{}'.format(self.uuid)


class Card(models.Model):
    class Meta:
        verbose_name = _('Card')
        verbose_name_plural = _('Cards')
    #

    uuid = models.CharField(
        verbose_name=_('uuid'),
        max_length=255,
        unique=True,
        null=False, blank=False,
    )

    TYPE_RED = 'red'
    TYPE_YELLOW = 'yellow'
    TYPE_GREEN = 'green'
    TYPE_CHOICES = (
        (TYPE_RED,      _('Red')),
        (TYPE_YELLOW,   _('Yellow')),
        (TYPE_GREEN,    _('Green')),
    )
    type = models.CharField(
        verbose_name=_('Type'),
        choices=TYPE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    reason = models.TextField(
        verbose_name=_('Reason'),
        max_length=512,
        null=False, blank=False,

    )

    SOURCE_CARDS = 'cards'
    SOURCE_LEADER = 'leader'
    SOURCE_EXPERIMENTS = 'experiments'
    SOURCE_CHOICES = (
        (SOURCE_CARDS,          _('Cards')),
        (SOURCE_LEADER,         _('Leader')),
        (SOURCE_EXPERIMENTS,    _('Experiments')),
    )
    source = models.CharField(
        verbose_name=_('Source'),
        choices=SOURCE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    status = models.ManyToManyField(
        Status,
        verbose_name=_('Status'),
        blank=True,
    )

    user = models.ForeignKey(
        User,
        verbose_name=_('Leader'),                   # кому выдана карточка
        on_delete=models.PROTECT,
        null=False, blank=False,
    )

    incident_dt = models.DateTimeField(
        verbose_name=_('Incident date'),
        null=False, blank=False,
    )

    event_uuid = models.CharField(
        verbose_name=_('Event uuid'),
        max_length=255,
        null=True, blank=True,
    )
    place_uuid = models.CharField(
        verbose_name=_('Place uuid'),
        max_length=255,
        null=True, blank=True,
    )

    def __str__(self):
        return '{}'.format(self.uuid)


class StatusChange(models.Model):
    class Meta:
        verbose_name = _('Status change')
        verbose_name_plural = _('Status change')
    #

    card = models.ForeignKey(
        Card,
        verbose_name=_('card'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )
    status = models.ForeignKey(
        Status,
        verbose_name=_('status'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )

    change_dt = models.DateTimeField(               # время изменения статуса
        verbose_name=_('Date change'),
        null=False, blank=False,
    )

    SYSTEM_CARDS = 'cards'
    SYSTEM_LEADER = 'leader'
    SYSTEM_EXPERIMENTS = 'experiments'
    SYSTEM_CHOICES = (
        (SYSTEM_CARDS,          _('Cards')),
        (SYSTEM_LEADER,         _('Leader')),
        (SYSTEM_EXPERIMENTS,    _('Experiments')),
    )
    system = models.CharField(                      # источник изменения статуса
        verbose_name=_('System'),
        choices=SYSTEM_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    user = models.ForeignKey(                       # кто изменил статус
        User,
        verbose_name=_('user'),
        on_delete=models.PROTECT,
        null=True, blank=True,
    )

    def __str__(self):
        return '{}:{}'.format(self.card, self.status)
