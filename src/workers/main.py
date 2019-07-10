# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
SELF_DIR = os.path.abspath(os.path.dirname(__file__))

log = logging.getLogger(__name__)


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
            log.info('NAME_ELIMINATED: {}'.format(card))
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
            log.info('NAME_ISSUED: {}'.format(card))
            card.set_status(
                name=models.Status.NAME_ISSUED
            )
    #   #


# ############################################################################ #
def main():
    log.info('start up {}'.format(timezone.now()))
    while True:
        try:
            time.sleep(10)
            log.debug('handle cards {}'.format(timezone.now()))
            eliminate_cards()
            log.debug('sleep +10s {}'.format(timezone.now()))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.error(e)
            time.sleep(60)
#   #   #


if __name__ == '__main__':
    #
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(
        logging.FileHandler(
            filename='worker.log'
        )
    )
    logging.getLogger('').addHandler(logging.StreamHandler(sys.stdout))
    try:
        main()
        #
    except KeyboardInterrupt:
        pass
    #


