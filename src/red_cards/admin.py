from django.contrib import admin

from . import models
from django.contrib.auth.admin import UserAdmin, Group, GroupAdmin


class CustomUserAdmin(UserAdmin):
    """"""
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_assistant',
        'unti_id',
        'leader_id',
    )


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
    )

    def _status(self, obj):
        assert isinstance(obj, models.Card)
        status = models.Status.objects.filter(
            card=obj
        ).order_by(
            '-change_dt',
        ).first()
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
        'card',
        'change_dt',
        'system',
        # 'leader_id',
        'name',
        'is_public',
    )
    readonly_fields = (
        'is_public',
    )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
