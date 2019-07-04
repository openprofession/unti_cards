from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Count
from . import models


def home(request):
    if request.user.is_active is False:
        url = reverse('social:begin', kwargs=dict(
            backend='unti'
        ))
        return HttpResponseRedirect(url)
    #
    user = request.user
    sql = """
        SELECT card.*, st.* from red_cards_status  as st
        INNER JOIN red_cards_card as card
        ON card.uuid = st.card_id
        WHERE card.leader_id={}
        AND st.change_dt = (
            SELECT MAX(change_dt) 
            FROM red_cards_status as st2 
            WHERE st2.card_id = st.card_id
        )
        {}
        ORDER BY st.change_dt
        ;
    """
    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    # published(карточка 2 на странице),
    # consideration(карточка 1),
    # issued(карточка 3)
    statuses_bad = models.Status.objects.raw(sql.format(
        user.leader_id,
        '''
            AND card.type IN ('{red}', '{yellow}')
            AND 
            (
                (
                    card.type= '{red}'
                    AND
                    st.name IN ('{published}', '{consideration}', '{issued}')
                )OR(
                    card.type= '{yellow}'
                    AND
                    st.name= '{issued}'
                )
            )
        '''.format(
            red=models.Card.TYPE_RED,
            yellow=models.Card.TYPE_YELLOW,

            published=models.Status.NAME_PUBLISHED,
            consideration=models.Status.NAME_CONSIDERATION,
            issued=models.Status.NAME_ISSUED,
        )
    ))

    issued_cards = (
        s.card for s in statuses_bad
        if s.card.type == models.Card.TYPE_RED
            and s.name == models.Status.NAME_ISSUED
    )
    issued_cards = list(issued_cards)
    max_issued_cards = 5
    issued_cards_empty_cunt = max_issued_cards - len(issued_cards)
    if issued_cards_empty_cunt < 0:
        issued_cards_empty_cunt = 0
    #
    issued_cards_empty = []
    if issued_cards_empty_cunt >= 1:
        issued_cards_empty = list(range(0, issued_cards_empty_cunt))
    #

    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    statuses_good = models.Status.objects.raw(sql.format(
        user.leader_id,
        '''
            AND card.type = '{green}'
            AND st.name = '{issued}'
        '''.format(
            green=models.Card.TYPE_GREEN,
            issued=models.Status.NAME_ISSUED,
        )
    ))

    good_cards = (
        s.card for s in statuses_good
        if s.card.type == models.Card.TYPE_GREEN
            and s.name == models.Status.NAME_ISSUED
    )
    good_cards = list(good_cards)

    statuses_good_empty = []
    _max_cards = 5
    statuses_good_empty_count = _max_cards - len(good_cards)
    if statuses_good_empty_count < 0:
        statuses_good_empty_count = 0
    #
    if statuses_good_empty_count >= 1:
        statuses_good_empty = list(range(0, statuses_good_empty_count))
    #
    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    return render(request, template_name="home.html", context=dict(
        statuses_bad=statuses_bad,
        issued_cards=issued_cards,
        issued_cards_empty=issued_cards_empty,

        statuses_good=statuses_good,
        statuses_good_empty=statuses_good_empty,
    ))

