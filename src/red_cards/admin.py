from django.contrib import admin

from . import models
from django.contrib.auth.admin import UserAdmin, Group, GroupAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from app_django.tools import print_seconds
from django.utils import timezone


# class RequestAdminMixin:
#     def get_queryset(self, request):
#         assert isinstance(self, admin.ModelAdmin)
#         setattr(self, '_request', request)
#         qs = super(RequestAdminMixin, self).get_queryset(request)
#         return qs
#
#     @property
#     def request(self):
#         return getattr(self, '_request', None)


# class CustomUserAdmin(UserAdmin):
#     """"""
#     list_display = (
#         'username', 'email', 'first_name', 'last_name',
#         'is_assistant',
#         'unti_id',
#         'leader_id',
#     )


class CustomUserAdmin(UserAdmin):
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('sso'), {'fields': ('is_assistant', 'unti_id', 'leader_id', )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'is_assistant',
        'unti_id',
        'leader_id',
    )

    #
#


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
admin.site.register(models.User, CustomUserAdmin)


def reg_admin_model(model):
    def _proxy(model_admin):
        admin.site.register(model, model_admin)
        return model_admin

    return _proxy


class TypeCardFilter(SimpleListFilter):
    title = _('Тип карточки')  
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        choices = []
        for card_type, verbose in models.Card.TYPE_CHOICES:
            count = models.Card.objects.filter(type=card_type).count()
            if count > 0:
                verbose = '{} ({})'.format(verbose, count)
            #
            choices.append(
                (card_type, verbose)
            )
        #
        return choices

    def queryset(self, request, queryset):
        choice = self.value()
        if choice is None:
            return queryset
        #
        return queryset.filter(
            type=choice,
        )


# Красная карточка пользователя в актуальном статусе published
# через 24 часа с момент создания статуса published
# переходит в статус issued


class StatusCardFilter(SimpleListFilter):
    title = _('Последний статус')
    parameter_name = 'last_status'

    def lookups(self, request, model_admin):
        choices = []
        for status_name, verbose in models.Status.NAME_CHOICES:
            count = models.Card.objects.filter(status__name=status_name).count()
            if count > 0:
                verbose = '{} ({})'.format(verbose, count)
            #
            choices.append(
                (status_name, verbose)
            )
        #
        return choices

    def queryset(self, request, queryset):
        choice = self.value()
        if choice is None:
            return queryset
        #
        return queryset.filter(
            status__name=choice,
        )

    # status__change_dt__lte = timezone.now() - timezone.timedelta(hours=24)


class ChangeDtFilter(SimpleListFilter):
    title = _('Время последнего изменения статуса (минимум)')
    parameter_name = 'change_dt'

    def lookups(self, request, model_admin):
        choices = []
        for status_name, verbose in models.Status.NAME_CHOICES:
            count = models.Card.objects.filter(status__name=status_name).count()
            if count > 0:
                verbose = '{} ({})'.format(verbose, count)
            #
            choices.append(
                (status_name, verbose)
            )
        #
        return (
            ('30m',     _('30 минут назад или раньше')),
            ('1h',      _('1 час назад')),
            # ('2h',      _('2 часа')),
            ('4h',      _('4 часа назад')),
            ('8h',      _('8 часов назад')),
            ('12h',     _('12 часов назад')),
            ('24h',     _('24 часа назад')),
            ('2d',      _('2 дня назад')),
            ('10d',     _('10 дней назад')),
        )

    def queryset(self, request, queryset):
        choice = self.value()
        if choice is None:
            return queryset
        #
        date = timezone.now() - {
            '30m':  timezone.timedelta(minutes=30),
            '1h':   timezone.timedelta(hours=1),
            '2h':   timezone.timedelta(hours=2),
            '4h':   timezone.timedelta(hours=4),
            '8h':   timezone.timedelta(hours=8),
            '12h':  timezone.timedelta(hours=12),
            '24h':  timezone.timedelta(hours=24),
            '2d':   timezone.timedelta(days=2),
            '10d':  timezone.timedelta(days=10),
        }[choice]
        return queryset.filter(
            status__change_dt__lte=date,
        )

    #



@reg_admin_model(models.Card)
class CardAdmin(admin.ModelAdmin):
    list_filter = (
        TypeCardFilter,
        StatusCardFilter,
        ChangeDtFilter,
    )
    list_display = (
        'uuid',
        '_status',
        '_change_status_dt',
        '_change_status_dt_indent',
        'type',
        'reason',
        'source',
        'leader_id',
        'incident_dt',
        # 'event_uuid',
        # 'place_uuid',
        # 'last_status',
        # 'status',
    )

    actions = (
        'delete_selected',
        'set_status_issued',
        'set_status_published',
    )

    def _status(self, obj):
        assert isinstance(obj, models.Card)
        status = obj.get_status()
        if status:
            return status.name
        else:
            return '-'
        #

    #
    _status.short_description = 'status'

    def _change_status_dt(self, obj):
        assert isinstance(obj, models.Card)
        status = obj.get_status()
        if status:
            return status.change_dt
        else:
            return '-'
        #

    _change_status_dt.short_description = 'change dt'

    def _change_status_dt_indent(self, obj):
        assert isinstance(obj, models.Card)
        status = obj.get_status()
        if status:
            indent = timezone.now() - status.change_dt
            return print_seconds(indent.total_seconds(), format='%dd %Hh %Mm')
        else:
            return '-'
        #

    _change_status_dt_indent.short_description = 'dt indent'

    def set_status_issued(self, request, queryset):
        total_handled = 0
        for card in queryset:
            card.set_status(
                name=models.Status.NAME_ISSUED,
                system=models.Status.SYSTEM_CARDS_TRANSFORM,
                user=request.user,
            )
            total_handled += 1
        #

        messages.success(
            request, 'Успешно обработано {} карточек'.format(total_handled)
        )

    set_status_issued.short_description = _(
        'Установить у выбранных статус : Issued ')

    def set_status_published(self, request, queryset):
        total_handled = 0
        for card in queryset:
            card.set_status(
                name=models.Status.NAME_PUBLISHED,
                system=models.Status.SYSTEM_CARDS_TRANSFORM,
                user=request.user,
            )
            total_handled += 1
        #

        messages.success(
            request, 'Успешно обработано {} карточек'.format(total_handled)
        )

    set_status_published.short_description = _(
        'Установить у выбранных статус : Published ')


@reg_admin_model(models.Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'card',
        'user',
        'change_dt',
        'system',
        'name',
        'is_public',
    )
    readonly_fields = (
        'is_public',
        'user',
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()


@reg_admin_model(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'title',
        'capacity',
        'place_title',
        'type_title',
        'start_dt',
        'end_dt',
        'created_at',
        'updated_at'

    )


@reg_admin_model(models.EventEnroll)
class EventEnrollAdmin(admin.ModelAdmin):
    list_display = (
        'event_uuid',
        'unti_id',
        'created_dt',
        'created_at',
        'updated_at'
    )


@reg_admin_model(models.Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = (
        'description',
        'file',
        'create_dt',
        'status',
        'card',
    )
