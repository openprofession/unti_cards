from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
import uuid
from django.utils import timezone
from app_django.tools import print_seconds
from django.db import transaction

# User = get_user_model()


from django.contrib.auth.models import (
    AbstractUser,
)


class User(AbstractUser):
    """
        python manage.py makemigrations red_cards
    """

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
        return ' '.join(filter(None, [
            self.last_name, self.first_name, self.second_name]))

    def get_full_name(self):
        return ' '.join(filter(None, [self.last_name, self.first_name]))

    def count_appeals(self):
        return Appeal.objects.filter(
            card__uuid__in=Card.objects.filter(
                leader_id=self.leader_id,
            ).values('uuid')
        ).count()


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

    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
    SYSTEM_CARDS_ASSISTANT = 'cards-assistant'          # 4 Ассистент выдает карточку
    SYSTEM_CARDS_CONSIDERATION = 'cards-consideration'  # 5 Участник оспаривает карточку
    SYSTEM_CARDS_APPEAL = 'cards-appeal'                # 6 Модератор апрувит/отклоняет оспаривание
    SYSTEM_CARDS_DEACTIVATE = 'cards-deactivate'                # 6 Модератор апрувит/отклоняет оспаривание

    SYSTEM_API = 'api'
    SYSTEM_LEADER = 'leader'
    SYSTEM_CARDS_TRANSFORM = 'cards-transform'
    SYSTEM_CARDS_REPAYMENT = 'cards-repayment'
    SYSTEM_CARDS_ISSUE = 'cards-issue'
    SYSTEM_EXPERIMENTS = 'experiments'
    SYSTEM_CHOICES = (

        (SYSTEM_CARDS_ASSISTANT, _('Cards-assistant')),
        (SYSTEM_CARDS_CONSIDERATION, _('Cards-consideration')),
        (SYSTEM_CARDS_APPEAL, _('Cards-appeal')),
        (SYSTEM_CARDS_DEACTIVATE, _('Cards-deactivate')),

        (SYSTEM_API, _('Api')),
        (SYSTEM_LEADER, _('Leader')),
        (SYSTEM_CARDS_TRANSFORM, _('Cards-transform')),
        (SYSTEM_CARDS_REPAYMENT, _('Cards-repayment')),
        (SYSTEM_CARDS_ISSUE, _('Cards-issue')),
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


class CardManager(models.Manager):
    # https://docs.djangoproject.com/en/2.2/topics/db/managers/#adding-extra-manager-methods
    """   """

    def create(
            self, *,
            type, reason, description=None, source, leader_id,
            incident_dt=None, event_uuid=None, place_uuid=None,
            system=Status.SYSTEM_CARDS_ASSISTANT,
            status=Status.NAME_INITIATED,
            user=None,
            **kwargs

               ):
        """
            создает новую карточку, назначает ей статус
            * save вызываеться и при создании и при обновлении
        :param type:            тип [red, yellow, green]
        :param reason:          причина
        :param description:     описание
        :param source:          источник карточки [cards, leader, experiments]
        :param leader_id:       кому выдана карточка
        :param incident_dt:     время нарушения
        :param event_uuid:      идентификатор мероприятия из Labs
        :param place_uuid:      идентификатор места проведения
        :param system:          источник изменения статуса [
                                    cards, leader, cards-transform, experiments
                                ]
        :param status:          статус карточки [
                                    initiated, published, consideration, issued,
                                    eliminated, approved, rejected, recommended
                                ]
        :param user:            кто изменил статус карточки

        :return:                новую карточку
        """
        new_card = super(CardManager, self).create(
            type=type,
            reason=reason,
            description=description,
            source=source,
            leader_id=leader_id,
            incident_dt=incident_dt,
            event_uuid=event_uuid,
            place_uuid=place_uuid,
            **kwargs
        )
        new_card.set_status(
            user=user,
            system=system,
            name=status,
        )
        return new_card


class Card(models.Model):
    objects = CardManager()

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
    type = models.CharField(
        verbose_name=_('Type'),
        help_text=_('тип карточки, string, допустимые значения: '
                    '[“red”, “yellow”, “green”]'),
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

    leader_id = models.IntegerField(
        verbose_name=_('Leader'),  # кому выдана карточка
        help_text=_('идентификатор пользователя в Leader Id, integer'),
        # max_length=255,
        null=False, blank=False,
    )

    # incident_dt - время нарушения, дата в формате “YYYY-MM-DD hh:mm”
    incident_dt = models.DateTimeField(
        verbose_name=_('Incident date'),
        help_text=_('время нарушения, string, '
                    'дата в формате “YYYY-MM-DD hh:mm”'),
        null=False, blank=False,
    )

    event_uuid = models.CharField(  # идентификатор мероприятия из Labs, string
        verbose_name=_('Event uuid'),
        help_text=_('идентификатор мероприятия из Labs, string'),
        max_length=255,
        null=True, blank=True,
    )
    place_uuid = models.CharField(
        verbose_name=_('идентификатор места проведения мероприятия из Labs, '
                       'string'),
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

    def set_status(
            self, *,
            system, name=Status.NAME_INITIATED,
            user=None,
    ):
        Status.objects.create(
            card=self,
            user=user,
            system=system,
            name=name,
        )

    def get_status(self):
        return Status.objects.filter(
            card=self,
        ).order_by(
            '-change_dt'
        ).first()

    def get_user(self):
        return User.objects.filter(
            leader_id=self.leader_id,
        ).first()

    def get_seconds_for_appellation(self):  # appellation
        status = self.get_status()
        if not status:
            return 0
        #
        assert isinstance(status, Status)
        delay = (
                        status.change_dt + timezone.timedelta(hours=24)
                ) - timezone.now()
        result = int(delay.total_seconds())
        if result < 0:
            result = 0
        #
        return result

    def get_appeal(self):
        return Appeal.objects.filter(
            card=self
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
    STATUS_IN_WORK = "in_work"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_NEW, _("New")),
        (STATUS_IN_WORK, _("In work")),
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

    executive = models.ForeignKey(      # юзер который взял заявку в работу
        User,
        verbose_name=_('Executive'),
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
    date_assign = models.DateTimeField(
        # дата и время, когда обновился Исполнитель
        verbose_name=_('date assign to executive'),
        null=True, blank=True,
    )
    date_finished = models.DateTimeField(
        # дата и время, когда заявка перешла в статус Одобрена/Отклоненаль
        verbose_name=_('date finished'),
        null=True, blank=True,
    )

    card = models.ForeignKey(
        Card,
        verbose_name=_('card'),
        on_delete=models.CASCADE,
        null=False, blank=False,
    )

    @classmethod
    def create_new_appeal(
            cls, *,
            user,
            description, file=None, card
    ):
        new_appeal = cls.objects.create(
            status=cls.STATUS_NEW,
            description=description,
            file=file,
            card=card,
        )
        card.set_status(
            name=Status.NAME_CONSIDERATION,
            system=Status.SYSTEM_CARDS_CONSIDERATION,
            user=user,
        )
        return new_appeal

    def assign(self, user):
        self.executive = user
        self.date_assign = timezone.now()
        self.status = self.STATUS_IN_WORK
        self.save()

    def free(self):
        self.executive = None
        self.date_assign = None
        self.status = self.STATUS_NEW
        self.save()

    def accept(self, user):
        self.card.set_status(
            name=Status.NAME_ELIMINATED,
            system=Status.SYSTEM_CARDS_APPEAL,
            user=user
        )
        self.status = self.STATUS_APPROVED
        self.executive = user
        self.date_finished = timezone.now()
        self.save()

    def reject(self, user):
        self.card.set_status(
            name=Status.NAME_ISSUED,
            system=Status.SYSTEM_CARDS_APPEAL,
            user=user
        )
        self.status = self.STATUS_REJECTED
        self.executive = user
        self.date_finished = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if not self.date_finished:
            if self.status in (
                self.STATUS_APPROVED,
                self.STATUS_REJECTED
            ):
                self.date_finished = timezone.now()
        #   #

        return super(Appeal, self).save(*args, **kwargs)

    def __str__(self):
        return '{}_{}_{}'.format(
            self.pk, self.status, self.card
        )

    def time_for_complete(self):
        _time = (self.create_dt + timezone.timedelta(hours=24)) \
                - timezone.now()
        return _time.total_seconds()

    def time_for_complete_text(self):
        return print_seconds(
            self.time_for_complete(),
            '%Hh %Mm'
        )

    def add_comment(self, text, file=None):
        comment = AppealComment.objects.create(
            text=text,
            file=file,
        )
        return comment

    def get_comments(self):
        return AppealComment.objects.filter(
            appeal=self
        ).order_by('date')

    def get_count_comments(self, user):
        comments = self.get_comments()
        return comments.count()

    def get_count_new_comments(self, user):
        comments = self.get_comments()
        return comments.exclude(
            seen_by_users=user
        ).count()


class AppealComment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False, blank=False,
    )
    date = models.DateTimeField(
        auto_now_add=True,
        null=False, blank=False,
    )
    appeal = models.ForeignKey(
        Appeal,
        on_delete=models.CASCADE,
        null=False, blank=False,
    )
    text = models.TextField(
        verbose_name=_('Description'),
        null=False, blank=False,
    )
    file = models.FileField(
        verbose_name=_('file'),
        null=True, blank=True,
    )

    seen_by_users = models.ManyToManyField(
        User,
        related_name='seen_by_users',
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

    assert isinstance(instance, Status)
    if instance.name in (
            Status.NAME_ELIMINATED,
    ):
        return
    #
    card = instance.card
    #
    if card.type == card.TYPE_YELLOW:
        with transaction.atomic():
            yellow_cards = Card.objects.filter(
                type=Card.TYPE_YELLOW,
                leader_id=card.leader_id,
                last_status=Status.NAME_ISSUED,
            ).all()
            if yellow_cards.count() >= 2:
                red_card_data = {
                    'leader_id': card.leader_id,
                    'type': card.TYPE_RED,
                    'reason': 'Получено две желтые',
                    'description': '',
                    'source': card.SOURCE_CARDS,
                    'incident_dt': timezone.now(),
                }
                for yellow_card in yellow_cards:
                    yellow_card.set_status(
                        name=Status.NAME_ELIMINATED,
                        system=Status.SYSTEM_CARDS_TRANSFORM,
                    )
                    red_card_data['description'] += yellow_card.reason + '\n'
                #
                Card.objects.create(
                    **red_card_data,
                    status=Status.NAME_PUBLISHED,
                    system=Status.SYSTEM_CARDS_TRANSFORM,
                )
    #   #   #
    # if card.type in (
    #         card.TYPE_GREEN,
    #         card.TYPE_RED,
    # ):
    #     with transaction.atomic():
    #         green_cards = Card.objects.filter(
    #             type=Card.TYPE_GREEN,
    #             leader_id=card.leader_id,
    #             last_status=Status.NAME_ISSUED,
    #         ).order_by('incident_dt').all()
    #         red_cards = Card.objects.filter(
    #             type=Card.TYPE_RED,
    #             leader_id=card.leader_id,
    #             last_status=Status.NAME_ISSUED,
    #         ).order_by('incident_dt').all()
    #         for green, red in zip(green_cards, red_cards):
    #             green.set_status(
    #                 name=Status.NAME_ELIMINATED,
    #                 system=Status.SYSTEM_CARDS_REPAYMENT
    #             )
    #             red.set_status(
    #                 name=Status.NAME_ELIMINATED,
    #                 system=Status.SYSTEM_CARDS_REPAYMENT
    #             )
    # #   #   #

