from django.contrib import admin

from . import models


def reg_admin_model(model):
    def _proxy(model_admin):
        admin.site.register(model, model_admin)
        return model_admin
    return _proxy


@reg_admin_model(models.Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'name',
        # 'description',
    )


@reg_admin_model(models.Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'type',
        'reason',
        'source',
        'user',
        'incident_dt',
        'event_uuid',
        'place_uuid',
    )


@reg_admin_model(models.StatusChange)
class StatusChangeAdmin(admin.ModelAdmin):
    list_display = (
        'card',
        'status',
        'change_dt',
        'system',
        'user',
    )

