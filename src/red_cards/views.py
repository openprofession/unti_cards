from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from red_cards.api import XLEApi
from red_cards.models import Event
from red_cards.utils import update_events_data, update_enrolls_data
from . import models


def home(request):
    if request.user.is_active is False:
        url = reverse('social:begin', kwargs=dict(
            backend='unti'
        ))
        return HttpResponseRedirect(url)
    #
    user = request.user
    user_cards = models.Card.objects.filter(
        leader_id=user.leader_id
    ).order_by(
        "-status__change_dt"
    ).filter(
        status__is_public=True,
        status__exact=True,
    ).select_related(
        'status__name'
    ).latest('status', '-status__change_dt').all(
    ).distinct()

    return render(request, template_name="home.html")


def api_test(request, date_txt):
    update_events_data(date_txt)
    return HttpResponse("OK!")


def api_test2(request):
    all_events = Event.objects.all()
    for event in all_events:
        update_enrolls_data(event_uuid=event.uuid)
    return HttpResponse("OK!")
