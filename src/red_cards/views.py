from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from app_django.settings import LOGOUT_REDIRECT
from red_cards.api import XLEApi
from red_cards.models import Event
from red_cards.utils import update_events_data, update_enrolls_data
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from . import models
from django.contrib.auth.views import logout_then_login as base_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden

from django.views.generic import FormView
from django import forms

_sql_get_cards = """
    SELECT card.*, st.* from red_cards_status  as st
    INNER JOIN red_cards_card as card
    ON card.uuid = st.card_id
    WHERE card.leader_id={}
      AND st.change_dt = (SELECT MAX(change_dt) FROM red_cards_status as st2 WHERE st2.card_id = st.card_id)
    {}
    ORDER BY st.change_dt
"""


def logout(request):
    return base_logout(request, LOGOUT_REDIRECT)


def home(request):
    if request.user.is_active is False:
        url = reverse('social:begin', kwargs=dict(
            backend='unti'
        ))
        return HttpResponseRedirect(url)
    #
    user = request.user
    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    # published(карточка 2 на странице),
    # consideration(карточка 1),
    # issued(карточка 3)
    statuses_bad = models.Status.objects.raw(_sql_get_cards.format(
        getattr(user, 'leader_id') or 1,
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
    statuses_good = models.Status.objects.raw(_sql_get_cards.format(
        getattr(user, 'leader_id') or 1,
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


# ############################################################################ #

# https://stackoverflow.com/questions/5089396/django-form-field-choices-adding-an-attribute
# https://stackoverflow.com/questions/41036216/how-to-render-form-choices-manually


class AddCardForm(forms.Form):
    reason = forms.CharField(
        label=_('Заголовок'),
        label_suffix='',
        widget=forms.TextInput(attrs={
            'placeholder': _('Напишите заголовок'),
        }),
        required=True,
    )
    classroom = forms.ChoiceField(
        label=_('Выберите локацию'),
        label_suffix='',
        widget=forms.Select(attrs={
            'data-live-search=': 'true',
        }),
        choices=(
            ('1', 'Аудитория 1'),
            ('2', 'Аудитория 2'),
            ('3', 'Аудитория 3'),
            ('101', 'Погреб'),
            ('102', 'Кабинет директора'),
        ),
    )
    date = forms.DateTimeField(
        label=_('Выберите дату'),
        label_suffix='',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': _('Дата'),
        }),
        input_formats=[
            '%d.%m.%Y',
        ]
    )
    description = forms.CharField(
        label=_('Введите описание'),
        label_suffix='',
        widget=forms.Textarea(attrs={
            'placeholder': _('Опишите, что произошло...'),
        }),
    )
    type = forms.ChoiceField(
        label=_('Тип карточки'),
        choices=models.Card.TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
    )
    leader_id = forms.IntegerField(
        widget=forms.HiddenInput,
    )

    def save(self):
        obj = models.Card.objects.create(
            type=self.cleaned_data.get('type'),
            reason=self.cleaned_data.get('reason'),
            description=self.cleaned_data.get('description'),
            source=models.Card.SOURCE_LEADER,
            incident_dt=self.cleaned_data.get('date'),
            leader_id=self.cleaned_data.get('leader_id'),
        )
        if obj.type == models.Card.TYPE_RED:
            status = models.Status.NAME_PUBLISHED
        elif obj.type in (
                models.Card.TYPE_YELLOW,
                models.Card.TYPE_GREEN,
        ):
            status = models.Status.NAME_ISSUED
        else:
            status = models.Status.NAME_INITIATED
        #
        new_status = models.Status.objects.create(
            card=obj,
            system=models.Status.SYSTEM_LEADER,
            name=status,
        )
        #

        return obj


class AddCardAdminFormView(LoginRequiredMixin, FormView):
    template_name = 'selected-form.html'
    form_class = AddCardForm

    def get_target_user(self):
        # get_object_or_404(Product, slug=self.kwargs['slug']
        return models.User.objects.get(leader_id=self.kwargs['leader_id'])

    def get_context_data(self, **kwargs):
        context = super(AddCardAdminFormView, self).get_context_data(**kwargs)
        user = self.get_target_user()
        assert isinstance(user, models.User)
        form = context['form']
        form.fields['leader_id'].initial = user.leader_id

        sql = _sql_get_cards.format(
            user.leader_id,
            '''
                AND card.type = '{red}'
                AND st.name = '{issued}'
            '''.format(
                red=models.Card.TYPE_RED,
                issued=models.Status.NAME_ISSUED,
            )
        )
        red_statuses = models.Status.objects.raw(sql)
        issued_cards = (
            s.card for s in red_statuses
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

        context.update({
            'target_user': user,
            'issued_cards': issued_cards,
            'issued_cards_empty': issued_cards_empty,
        })

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():

            card = form.save()
            assert isinstance(card, models.Card)
            messages.success(
                request, 'Карточка успешно добавлена {}'.format(card)
            )

            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        #

    def get_success_url(self):
        return reverse('card-add', kwargs=dict(leader_id=self.kwargs['leader_id']))


def api_test(request, date_txt):
    update_events_data(date_txt)
    return HttpResponse("OK!")


def api_test2(request):
    all_events = Event.objects.all()
    for event in all_events:
        update_enrolls_data(event_uuid=event.uuid)
    return HttpResponse("OK!")


class ChallengeForm(forms.Form):
    """

    """

    description = forms.CharField(
        label=_('Введите описание'),
        label_suffix='',
        widget=forms.Textarea(attrs={
            'placeholder': _('Опишите, что произошло и почему вы не согласны...'),
        }),
        required=True,
    )
    file = forms.FileField(
        label=_('Выберите файл'),
        label_suffix='',
        widget=forms.FileInput(),
        required=False
    )
    card = forms.CharField(
        widget=forms.HiddenInput,
    )

    def save(self):
        # https://docs.djangoproject.com/en/2.2/topics/http/file-uploads/
        # https://stackoverflow.com/questions/1718429/file-does-not-upload-from-web-form-in-django
        card = models.Card.objects.get(uuid=self.cleaned_data.get('card'))
        new_appel = models.Appeal.objects.create(
            description=self.cleaned_data.get('description'),
            status=models.Appeal.STATUS_NEW,
            card=card,
            file=self.cleaned_data.get('file'),
        )
        new_status = models.Status.objects.create(
            card=card,
            name=models.Status.NAME_CONSIDERATION,
            system=models.Status.SYSTEM_LEADER,
        )
        return new_appel


class ArgsChallengeForm(forms.Form):
    # user = forms.ChoiceField(required=True)
    card = forms.UUIDField(required=True)


class ChallengeFormView(LoginRequiredMixin, FormView):
    template_name = 'challenge.html'
    form_class = ChallengeForm

    def get_context_data(self, **kwargs):
        context = super(ChallengeFormView, self).get_context_data(**kwargs)

        # ------------------------------------------------------------ #
        params = ArgsChallengeForm(self.request.GET)
        if not params.is_valid():
            raise Http404
        #
        params = params.cleaned_data
        card = models.Card.objects.get(uuid=params['card'])
        status = card.get_status()
        assert isinstance(status, models.Status)
        if status.name != status.NAME_PUBLISHED:
            raise HttpResponseForbidden
        #
        if int(self.request.user.leader_id) != int(card.leader_id):
            # only own car can be challenge
            raise HttpResponseForbidden
        #
        # ------------------------------------------------------------ #
        form = context['form']
        form.fields['card'].initial = card.uuid
        # ------------------------------------------------------------ #
        context.update({
            'card': card,
        })

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():

            appeal = form.save()
            assert isinstance(appeal, models.Appeal)
            # messages.success(
            #     request, 'Апеляция успешно добавлена {}'.format(appeal)
            # )

            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        #

    def get_success_url(self):
        return reverse('challenge_ready')


def challenge_ready(request):  # ChallengeFormView
    return render(request, template_name="challenge-accepted.html", )
