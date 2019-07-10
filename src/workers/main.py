# -*- coding: utf-8 -*-
import os
import sys
import time

SELF_DIR = os.path.abspath(os.path.dirname(__file__))


def init_django():
    sys.path.append(os.path.join(SELF_DIR, '..'))

    from app_django.wsgi import application

    return application
#


init_django()
# ############################################################################ #


# ############################################################################ #
from red_cards import models
from django.utils import timezone


def eliminate_cards():
    # Желтая карточка пользователя в актуальном статусе issued
    # через 48 часов после создания (создания статуса issued)
    # переходит в статус eliminated
    yellow_cards = models.Card.objects.filter(
        type=models.Card.TYPE_YELLOW,
        last_status=models.Status.NAME_ISSUED
    ).all()
    for card in yellow_cards:
        status = card.get_status()
        if not status:
            continue
        #
        assert isinstance(status, models.Status)
        if status.change_dt < (timezone.now() - timezone.timedelta(hours=24)):
            print('NAME_ELIMINATED: {}'.format(card))
            card.set_status(
                name=models.Status.NAME_ELIMINATED
            )
    #   #

    # Красная карточка пользователя в актуальном статусе published
    # через 24 часа с момент создания статуса published
    # переходит в статус issued
    red_cards = models.Card.objects.filter(
        type=models.Card.TYPE_RED,
        last_status=models.Status.NAME_PUBLISHED
    ).all()
    for card in red_cards:
        status = card.get_status()
        if not status:
            continue
        #
        assert isinstance(status, models.Status)
        if status.change_dt < (timezone.now() - timezone.timedelta(hours=24)):
            print('NAME_ISSUED: {}'.format(card))
            card.set_status(
                name=models.Status.NAME_ISSUED
            )
    #   #


# ############################################################################ #
def main():
    while True:
        time.sleep(1)
        eliminate_cards()
        print('+')
#


if __name__ == '__main__':
    with open('_worker.temp', 'a+') as file:
        file.write('up: {}'.format(timezone.now()))
    #
    try:
        main()
    except KeyboardInterrupt:
        pass
    #


