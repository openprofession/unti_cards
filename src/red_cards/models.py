from django.db import models
from django.utils.translation import ugettext_lazy as _
import uuid
"""
https://openprofessions.atlassian.net/browse/DEVUNTI-2

"""
# User = get_user_model()

# from rest_framework_api_key.models import AbstractAPIKey


class Card(models.Model):
    class Meta:
        verbose_name = _('Card')
        verbose_name_plural = _('Cards')
    #

    uuid = models.UUIDField(
        # идентификатор карточки в системе, integer
        # UUID карточки мы генерируем сами
        verbose_name=_('uuid'),
        help_text=_('идентификатор карточки в системе, string'),
        # max_length=255,
        primary_key=True,
        unique=True,
        null=False, blank=False,
        editable=False,
        default=uuid.uuid4,
    )

    TYPE_RED = 'red'
    TYPE_YELLOW = 'yellow'
    TYPE_GREEN = 'green'
    TYPE_CHOICES = (
        (TYPE_RED,      _('Red')),
        (TYPE_YELLOW,   _('Yellow')),
        (TYPE_GREEN,    _('Green')),
    )
    type = models.CharField(        # тип карточки, string,  допустимые значения:  [“red”, “yellow”, “green”]
        verbose_name=_('Type'),
        help_text=_('тип карточки, string, допустимые значения: [“red”, “yellow”, “green”]'),
        choices=TYPE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    reason = models.TextField(      # причина выдачи карточки, string
        verbose_name=_('Reason'),
        help_text=_('причина выдачи карточки, string'),
        max_length=512,
        null=False, blank=False,

    )

    # source - источник выдачи карточки, string,  допустимые значения
    # [“Cards”, “Leader”, “Experiments”]
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
        help_text=_('источник выдачи карточки, string, допустимые значения '
                    '[“Cards”, “Leader”, “Experiments”]'),
        choices=SOURCE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    leader_id = models.IntegerField(                # идентификатор пользователя в Leader Id, integer
        verbose_name=_('Leader'),                   # кому выдана карточка
        help_text=_('идентификатор пользователя в Leader Id, integer'),
        # max_length=255,
        null=False, blank=False,
    )

    # incident_dt - время нарушения, дата в формате “YYYY-MM-DD hh:mm”
    incident_dt = models.DateTimeField(
        verbose_name=_('Incident date'),
        help_text=_('время нарушения, string, дата в формате “YYYY-MM-DD hh:mm”'),
        null=False, blank=False,
    )

    event_uuid = models.CharField(                  # идентификатор мероприятия из Labs, string
        verbose_name=_('Event uuid'),
        help_text=_('идентификатор мероприятия из Labs, string'),
        max_length=255,
        null=True, blank=True,
    )
    place_uuid = models.CharField(                  # идентификатор места проведения мероприятия из Labs, string
        verbose_name=_('идентификатор места проведения мероприятия из Labs, string'),
        max_length=255,
        null=True, blank=True,
    )

    def __str__(self):
        return '{}'.format(self.uuid)

    def save(self, *args, **kwargs):
        super(Card, self).save(*args, **kwargs)
        Status.objects.create(
            card=self,
            system=Status.SYSTEM_CARDS,
            name=Status.NAME_INITIATED,
            is_public=True,
        )


class Status(models.Model):
    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')
    #

    card = models.ForeignKey(
        Card,
        verbose_name=_('card'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )

    change_dt = models.DateTimeField(               # время изменения статуса
        verbose_name=_('Date change'),
        null=False, blank=False,
        auto_now_add=True,
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

    # статус карточки, string,  допустимые значения:
    # [“initiated”, “published”, “consideration”, “issued”, “eliminated”]

    NAME_INITIATED = "initiated"
    NAME_PUBLISHED = "published"
    NAME_CONSIDERATION = "consideration"
    NAME_ISSUED = "issued"
    NAME_ELIMINATED = "eliminated"

    NAME_APPROVED = "approved"
    NAME_REJECTED = "rejected"
    NAME_RECOMMENDED = "recommended"

    PRIVATE_STATUSES = (
        NAME_APPROVED,
        NAME_REJECTED,
        NAME_RECOMMENDED,
    )

    NAME_CHOICES = (
        (NAME_INITIATED,        _("Initiated")),
        (NAME_PUBLISHED,        _("Published")),
        (NAME_CONSIDERATION,    _("Consideration")),
        (NAME_ISSUED,           _("Issued")),
        (NAME_ELIMINATED,       _("Eliminated")),

        (NAME_APPROVED,         _("Approved")),
        (NAME_REJECTED,         _("Rejected")),
        (NAME_RECOMMENDED,      _("Recommended")),
    )
    name = models.CharField(
        verbose_name=_('Name'),
        choices=NAME_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    # description = models.TextField(
    #     verbose_name=_('Description'),
    #     null=True, blank=True,
    # )

    is_public = models.BooleanField(
        verbose_name=_('is public'),
        default=False,
    )

    def save(self, *args, **kwargs):
        if self.name in self.PRIVATE_STATUSES:
            self.is_public = False
        #

    def __str__(self):
        return '{}:{}'.format(self.card, self.name)

