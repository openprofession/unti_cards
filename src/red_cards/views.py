from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
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
