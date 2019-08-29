"""
tests with selenium
https://www.valentinog.com/blog/testing-django/

"""

import pytest

from django.test import TestCase
from django.core import exceptions
from contextlib import contextmanager
from django.contrib.auth import get_user_model
from http import HTTPStatus

from .. import models
from django.urls import reverse

User = get_user_model()

################################################################################


@pytest.mark.django_db
class AddCardsByAssistantTestCase(TestCase):
    r"""
    """

    @property
    def ACCOUNT_DATA_ASSISTANT(self):
        return dict(
            username='alex',
            password='at@OK789',
            email='alex@example.com',
            first_name='Alexandr',
            last_name='Washington',
            is_active=True,
            is_superuser=False,             # <=(!)
            is_staff=False,                 # <=(!)

            is_assistant=True,              # <=(!)

            # leader_id=777,                  # <=(!)
        )

    @property
    def ACCOUNT_DATA_LEADER(self):
        return dict(
            username='Max',
            password='ma@OK789',
            email='max@example.com',
            first_name='Maxim',
            last_name='Ivanov',
            is_active=True,
            is_superuser=False,             # <=(!)
            is_staff=False,                 # <=(!)

            is_assistant=False,              # <=(!)

            leader_id=777,                  # <=(!)
        )

    def setUp(self):
        self.assistant = User.objects.create_user(**self.ACCOUNT_DATA_ASSISTANT)
        self.leader = User.objects.create_user(**self.ACCOUNT_DATA_LEADER)

    def login_as_assistant(self):
        self.client.login(
            username=self.ACCOUNT_DATA_ASSISTANT['username'],
            password=self.ACCOUNT_DATA_ASSISTANT['password'],
        )

    def login_as_leader(self):
        self.client.login(
            username=self.ACCOUNT_DATA_LEADER['username'],
            password=self.ACCOUNT_DATA_LEADER['password'],
        )

    def test_red_cards_go_to_cards_form(self):
        self.login_as_assistant()

        response = self.client.get('/', follow=True)
        cards_form_url = reverse("user-cards")
        self.assertContains(
            response,
            '<a class="header-link" href="%s">Выдать карточку</a>'
            '' % cards_form_url,
            html=True
        )
        response = self.client.get(cards_form_url, follow=True)
        self.assertContains(
            response,
            '<h1 class="section-title">Выберите студента</h1>',
            html=True,
            status_code=HTTPStatus.OK,
        )

    # def test_red_cards_select_user(self):
    #     cards_form_url = reverse("user-cards")
    #     response = self.client.get(cards_form_url, follow=True)
    #     self.assertContains(response, 'L777 Admin Admin')

    def _test_add_card(self, card_type, expected_status):
        self.login_as_assistant()
        response = self.client.post(
            reverse(
                "card-add",
                kwargs=dict(
                    leader_id=self.leader.leader_id,
                )
            ),
            follow=True,
            data=dict(
                reason='Прогул лекции',
                classroom='',
                date='20.01.2019',
                description='Не пришел на лекцию',
                type=card_type,
                leader_id=self.leader.leader_id,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            models.Card.objects.all().count(), 1
        )
        card = models.Card.objects.first()
        card_status = card.get_status()
        assert isinstance(card_status, models.Status)
        self.assertEqual(
            card_status.name, expected_status
        )
        self.assertEqual(
            card_status.system, models.Status.SYSTEM_CARDS_ASSISTANT
        )

    def test_add_red_card(self):
        self._test_add_card(models.Card.TYPE_RED, models.Status.NAME_PUBLISHED)

    def test_add_yellow_card(self):
        self._test_add_card(models.Card.TYPE_YELLOW, models.Status.NAME_ISSUED)

    def test_add_green_card(self):
        self._test_add_card(models.Card.TYPE_GREEN, models.Status.NAME_ISSUED)

    def test_two_yellow_to_one_red(self):
        self.login_as_assistant()
        response = self.client.post(
            reverse(
                "card-add",
                kwargs=dict(
                    leader_id=self.leader.leader_id,
                )
            ),
            follow=True,
            data=dict(
                reason='Прогул лекции',
                classroom='',
                date='20.01.2019',
                description='Не пришел на лекцию',
                type=models.Card.TYPE_YELLOW,
                leader_id=self.leader.leader_id,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            models.Card.objects.all().count(), 1
        )
        # - - -
        response = self.client.post(
            reverse(
                "card-add",
                kwargs=dict(
                    leader_id=self.leader.leader_id,
                )
            ),
            follow=True,
            data=dict(
                reason='Прогул лекции',
                classroom='',
                date='20.01.2019',
                description='Не пришел на лекцию',
                type=models.Card.TYPE_YELLOW,
                leader_id=self.leader.leader_id,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            models.Card.objects.all().count(), 3
        )
        # - - -
        self.assertEqual(
            models.Card.objects.filter(type=models.Card.TYPE_RED).count(), 1
        )
        self.assertEqual(
            models.Card.objects.filter(type=models.Card.TYPE_YELLOW).count(), 2
        )
        for yellow_card in models.Card.objects.filter(
                type=models.Card.TYPE_YELLOW
        ).all():
            assert isinstance(yellow_card, models.Card)
            status = yellow_card.get_status()
            assert isinstance(status, models.Status)
            self.assertEqual(status.name, models.Status.NAME_ELIMINATED)
        #

    def _create_appeal(self):
        self.login_as_assistant()
        response = self.client.post(
            reverse(
                "card-add",
                kwargs=dict(
                    leader_id=self.leader.leader_id,
                )
            ),
            follow=True,
            data=dict(
                reason='Прогул лекции',
                classroom='',
                date='20.01.2019',
                description='Не пришел на лекцию',
                type=models.Card.TYPE_RED,
                leader_id=self.leader.leader_id,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            models.Card.objects.all().count(), 1
        )
        # - - -
        card = models.Card.objects.first()

        # - - -
        self.login_as_leader()
        response = self.client.post(
            reverse("appeals-add"),
            follow=True,
            data=dict(
                description='я был на лекции',
                card=card.uuid,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        # - - -

        card_status = card.get_status()
        assert isinstance(card_status, models.Status)
        self.assertEqual(
            card_status.name, models.Status.NAME_CONSIDERATION
        )
        self.assertEqual(
            card_status.system, models.Status.SYSTEM_CARDS_CONSIDERATION
        )
        # - - -
        self.assertEqual(
            models.Appeal.objects.all().count(), 1
        )
        appeal = models.Appeal.objects.first()
        self.assertEqual(
            appeal.status, models.Appeal.STATUS_NEW
        )
        # - - -
        return appeal

    def test_add_appeal(self):
        appeal = self._create_appeal()
        assert isinstance(appeal, models.Appeal)

    def _appeal_assign(self):
        appeal = self._create_appeal()
        assert isinstance(appeal, models.Appeal)
        self.login_as_assistant()
        response = self.client.post(
            reverse("appeals-detail-admin", kwargs=dict(pk=appeal.pk)),
            follow=True,
            data=dict(
                form_name='executive',
                action='assign',
                appeal=appeal.pk,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        appeal.refresh_from_db()  # important
        self.assertEqual(
            appeal.status, models.Appeal.STATUS_IN_WORK
        )
        # - - -
        card_status = appeal.card.get_status()
        assert isinstance(card_status, models.Status)
        self.assertEqual(
            card_status.name, models.Status.NAME_CONSIDERATION
        )
        self.assertEqual(
            card_status.system, models.Status.SYSTEM_CARDS_CONSIDERATION
        )
        return appeal

    def test_appeal_assign(self):
        self._appeal_assign()

    def test_appeal_free(self):
        appeal = self._appeal_assign()
        assert isinstance(appeal, models.Appeal)
        self.login_as_assistant()
        response = self.client.post(
            reverse("appeals-detail-admin", kwargs=dict(pk=appeal.pk)),
            follow=True,
            data=dict(
                form_name='executive',
                action='free',
                appeal=appeal.pk,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        appeal.refresh_from_db()  # important
        self.assertEqual(
            appeal.status, models.Appeal.STATUS_NEW
        )

    def test_appeal_confirm(self):
        appeal = self._appeal_assign()
        assert isinstance(appeal, models.Appeal)
        self.login_as_assistant()
        response = self.client.post(
            reverse("appeals-detail-admin", kwargs=dict(pk=appeal.pk)),
            follow=True,
            data=dict(
                form_name='manage',
                appeal=appeal.pk,
                action='accept',
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        appeal.refresh_from_db()  # important
        self.assertEqual(
            appeal.status, models.Appeal.STATUS_APPROVED
        )

        card_status = appeal.card.get_status()
        assert isinstance(card_status, models.Status)
        self.assertEqual(
            card_status.name, models.Status.NAME_ELIMINATED
        )
        self.assertEqual(
            card_status.system, models.Status.SYSTEM_CARDS_APPEAL
        )

    def test_appeal_reject(self):
        appeal = self._appeal_assign()
        assert isinstance(appeal, models.Appeal)
        self.login_as_assistant()
        response = self.client.post(
            reverse("appeals-detail-admin", kwargs=dict(pk=appeal.pk)),
            follow=True,
            data=dict(
                form_name='manage',
                action='reject',
                appeal=appeal.pk,
            )
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        appeal.refresh_from_db()  # important
        self.assertEqual(
            appeal.status, models.Appeal.STATUS_REJECTED
        )

        card_status = appeal.card.get_status()
        assert isinstance(card_status, models.Status)
        self.assertEqual(
            card_status.name, models.Status.NAME_ISSUED
        )
        self.assertEqual(
            card_status.system, models.Status.SYSTEM_CARDS_APPEAL
        )

