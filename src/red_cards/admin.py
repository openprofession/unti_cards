from django.contrib import admin

from . import models
from django.contrib.auth.admin import UserAdmin, Group, GroupAdmin
from django.utils.translation import ugettext_lazy as _

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
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name',
        'leader_id',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'is_assistant',
    )

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


@reg_admin_model(models.Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        '_status',
        'type',
        'reason',
        'source',
        'leader_id',
        'incident_dt',
        'event_uuid',
        'place_uuid',
        'last_status'
    )
    search_fields = (
        'leader_id',
        'reason',
        'description',
    )
    list_filter = (
        'type',
        'last_status'
    )
    list_per_page = 500

    def _status(self, obj):
        assert isinstance(obj, models.Card)
        status = obj.get_status()
        if status:
            status = status.name
        else:
            status = 'not set'
        #
        return status

    #
    _status.short_description = 'status'


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
    list_display_links = (
        'card',
        'user',
    )
    list_filter = (
        'system',
        'name',
        'is_public',
        'change_dt',
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
        'tag',
    )
    list_display_links = (
        'card',
        'tag',
    )
    list_filter = (
        'status',
        'create_dt',
        'tag',
    )
    search_fields = (
        'description',
    )


@reg_admin_model(models.AppealComment)
class AppealCommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'appeal',
    )
    list_display_links = (
        'appeal',
    )
    search_fields = (
        'text',
    )
    list_filter = (
        'date',
    )


@reg_admin_model(models.AppealTag)
class AppealTagAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name_hash',
        'name',
    )
    search_fields = (
        'name_hash',
        'name',
    )
    readonly_fields = (
        'name_hash',
    )
