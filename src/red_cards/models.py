from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
import uuid
from django.db.models import Count

# User = get_user_model()

# from rest_framework_api_key.models import AbstractAPIKey

from django.contrib.auth.models import (
    AbstractUser,
    UserManager as _UserManager,
)
from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    '''
        python manage.py makemigrations red_cards
    '''

    second_name = models.CharField(max_length=50)

    is_assistant = models.BooleanField(default=False)
    unti_id = models.PositiveIntegerField(
        db_index=True,
        null=True,
        blank=True,
        unique=True,
    )
    leader_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    # leader_id = models.IntegerField(  # todo: set leader_id as IntegerField

    class Meta:
        verbose_name = _(u'Пользователь')
        verbose_name_plural = _(u'Пользователи')

    def __str__(self):
        return '%s %s' % (self.unti_id, self.get_full_name())

    @property
    def fio(self):
        return ' '.join(filter(None, [self.last_name, self.first_name, self.second_name]))

    def get_full_name(self):
        return ' '.join(filter(None, [self.last_name, self.first_name]))


class Status(models.Model):
    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')

    #

    card = models.ForeignKey(
        'Card',
        verbose_name=_('card'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )

    change_dt = models.DateTimeField(  # время изменения статуса
        verbose_name=_('Date change'),
        null=False, blank=False,
        auto_now_add=True,
    )

    SYSTEM_CARDS = 'cards'
    SYSTEM_LEADER = 'leader'
    SYSTEM_EXPERIMENTS = 'experiments'
    SYSTEM_CHOICES = (
        (SYSTEM_CARDS, _('Cards')),
        (SYSTEM_LEADER, _('Leader')),
        (SYSTEM_EXPERIMENTS, _('Experiments')),
    )
    system = models.CharField(  # источник изменения статуса
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
        (NAME_INITIATED, _("Initiated")),
        (NAME_PUBLISHED, _("Published")),
        (NAME_CONSIDERATION, _("Consideration")),
        (NAME_ISSUED, _("Issued")),
        (NAME_ELIMINATED, _("Eliminated")),

        (NAME_APPROVED, _("Approved")),
        (NAME_REJECTED, _("Rejected")),
        (NAME_RECOMMENDED, _("Recommended")),
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
        self.is_public = self.name not in self.PRIVATE_STATUSES
        super(Status, self).save(*args, **kwargs)

    def __str__(self):
        return '{}:{}'.format(self.card, self.name)


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
        (TYPE_RED, _('Красная карточка')),
        (TYPE_YELLOW, _('Желтая карточка')),
        (TYPE_GREEN, _('Зеленая карточка')),
    )
    type = models.CharField(  # тип карточки, string,  допустимые значения:  [“red”, “yellow”, “green”]
        verbose_name=_('Type'),
        help_text=_('тип карточки, string, допустимые значения: [“red”, “yellow”, “green”]'),
        choices=TYPE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    def type_verbose(self):
        return dict(self.TYPE_CHOICES)[self.type]

    reason = models.TextField(  # причина выдачи карточки, string
        verbose_name=_('Reason'),
        help_text=_('причина выдачи карточки, string'),
        max_length=512,
        null=False, blank=False,

    )

    description = models.TextField(
        verbose_name=_('Description'),
        null=True, blank=True,
    )

    # source - источник выдачи карточки, string,  допустимые значения
    # [“Cards”, “Leader”, “Experiments”]
    SOURCE_CARDS = 'cards'
    SOURCE_LEADER = 'leader'
    SOURCE_EXPERIMENTS = 'experiments'
    SOURCE_CHOICES = (
        (SOURCE_CARDS, _('Cards')),
        (SOURCE_LEADER, _('Leader')),
        (SOURCE_EXPERIMENTS, _('Experiments')),
    )
    source = models.CharField(
        verbose_name=_('Source'),
        help_text=_('источник выдачи карточки, string, допустимые значения '
                    '[“Cards”, “Leader”, “Experiments”]'),
        choices=SOURCE_CHOICES,
        max_length=255,
        null=False, blank=False,
    )

    leader_id = models.IntegerField(  # идентификатор пользователя в Leader Id, integer
        verbose_name=_('Leader'),  # кому выдана карточка
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

    event_uuid = models.CharField(  # идентификатор мероприятия из Labs, string
        verbose_name=_('Event uuid'),
        help_text=_('идентификатор мероприятия из Labs, string'),
        max_length=255,
        null=True, blank=True,
    )
    place_uuid = models.CharField(  # идентификатор места проведения мероприятия из Labs, string
        verbose_name=_('идентификатор места проведения мероприятия из Labs, string'),
        max_length=255,
        null=True, blank=True,
    )

    last_status = models.CharField(
        verbose_name=_('Last Status'),
        choices=Status.NAME_CHOICES,
        max_length=255,
        null=False, blank=False,
        default=Status.NAME_INITIATED
    )

    def __str__(self):
        return '{}:{}.L{}'.format(self.type, self.uuid, self.leader_id)

    def save(self, *args, **kwargs):
        super(Card, self).save(*args, **kwargs)
        status = Status.objects.get_or_create(
            card=self,
            system=Status.SYSTEM_CARDS,
            name=Status.NAME_INITIATED,
            is_public=True,
        )
        self.current_status = status

    def get_status(self):
        return Status.objects.filter(
            card=self,
        ).order_by(
            '-change_dt'
        ).first()


class ClassRum(models.Model):
    uuid = models.UUIDField(
        verbose_name=_('uuid'),
        help_text=_('идентификатор аудитории'),
        # max_length=255,
        primary_key=True,
        unique=True,
        null=False, blank=False,
        # editable=False,
        default=uuid.uuid4,
    )

    title = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        null=False, blank=False,
    )


class Appeal(models.Model):
    class Meta:
        verbose_name = _('Appeal')
        verbose_name_plural = _('Appeals')

    #

    description = models.TextField(
        verbose_name=_('Description'),
        null=False, blank=False,
    )
    file = models.FileField(
        verbose_name=_('file'),
        null=True, blank=True,
    )

    create_dt = models.DateTimeField(  # время изменения статуса
        verbose_name=_('Date change'),
        null=False, blank=False,
        auto_now_add=True,
    )

    STATUS_NEW = "new"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_NEW, _("New")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
    )
    status = models.CharField(
        verbose_name=_('status'),
        choices=STATUS_CHOICES,
        max_length=255,
        null=False, blank=False,
        default=STATUS_NEW,
    )
    card = models.ForeignKey(
        Card,
        verbose_name=_('card'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )

    def __str__(self):
        return '{}_{}_{}'.format(
            self.pk, self.status, self.card
        )


class Event(models.Model):
    uuid = models.CharField(max_length=36)
    activity_uuid = models.CharField(max_length=36)
    title = models.CharField(max_length=500)
    capacity = models.CharField(max_length=50)
    place_uuid = models.CharField(max_length=36)
    place_title = models.CharField(max_length=500)
    type_uuid = models.CharField(max_length=36)
    type_title = models.CharField(max_length=500)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EventEnroll(models.Model):
    event_uuid = models.CharField(max_length=36)
    unti_id = models.IntegerField()
    created_dt = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EventAttendance(models.Model):
    event_uuid = models.CharField(max_length=36)
    unti_id = models.IntegerField()
    reliability = models.DecimalField(max_digits=5, decimal_places=3)
    completeness = models.DecimalField(max_digits=5, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(post_save, sender=Status, dispatch_uid="update_last_status")
def update_stock(sender, instance, **kwargs):
    card = instance.card
    card.last_status = instance.name
    card.save()
