from django.contrib import admin

from . import models


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
    )
