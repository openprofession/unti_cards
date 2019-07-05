from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from red_cards.api import XLEApi
from red_cards.models import Event
from red_cards.utils import update_events_data, update_enrolls_data
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from . import models
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from django.views.generic import FormView
from django import forms

_sql_get_cards = """
    SELECT card.*, st.* from red_cards_status  as st
    INNER JOIN red_cards_card as card
    ON card.uuid = st.card_id
    WHERE card.leader_id={}
      AND st.change_dt = (SELECT MAX(change_dt) FROM red_cards_status as st2 WHERE st2.card_id = st.card_id)
    ORDER BY st.change_dt
"""


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
    statuses_good = models.Status.objects.raw(_sql_get_cards.format(
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


    """


    Экран 2
(!) 2с - Выберите событие - удаляем поле из шаблона
http://test2.x-webdev.info/selected-form.html


Шапка карточки  - Фамилия Имя выбранного студента, его leader_id, email, кружочками - количество красных карточек студента в статусе issued

Ассистент заполняет форму на создание карточки:

Заголовок: reason (обязательное)

Аудитория: выпадающий список аудиторий (пример формата D2) c поиском, будет список аудиторий смапленный с placeID (порядка 70)

Выберите событие - удаляем поле из шаблона

Выберите дату + добавить время : incident_dt (обязательно)

Введите описание: description

Radio с типом карточки: type (обязательно)

source: assistant

После нажатия Выдать карточку в базе у соответствующего пользователя создается красная карточка в статусе published или желтая/зеленая карточка в статусе issued, ассистенту выпадает подтверждение об успешном создании карточки


    """


def api_test(request, date_txt):
    update_events_data(date_txt)
    return HttpResponse("OK!")


def api_test2(request):
    all_events = Event.objects.all()
    for event in all_events:
        update_enrolls_data(event_uuid=event.uuid)
    return HttpResponse("OK!")
