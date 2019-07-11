from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from app_django.settings import LOGOUT_REDIRECT
from red_cards.models import Event
from red_cards.utils import update_events_data, update_enrolls_data
from django.utils.translation import ugettext_lazy as _
from . import models
from django.contrib.auth.views import logout_then_login as base_logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.core.paginator import Paginator

from django.views.generic import FormView, TemplateView

from django import forms


class HelpView(TemplateView):
    template_name = 'help.html'


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
    eliminated_cards = models.Card.objects.filter(
        last_status=models.Status.NAME_ELIMINATED,
        leader_id=request.user.leader_id
    )
    # ------------------------------------------------------------------------ #
    return render(request, template_name="home.html", context=dict(
        statuses_bad=statuses_bad,
        issued_cards=issued_cards,
        issued_cards_empty=issued_cards_empty,

        statuses_good=statuses_good,
        statuses_good_empty=statuses_good_empty,
        eliminated_cards=eliminated_cards
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
        required=False,
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

    def save(self, user):
        assert isinstance(user, models.User)

        card_type = self.cleaned_data.get('type')

        if card_type == models.Card.TYPE_RED:
            status = models.Status.NAME_PUBLISHED
        elif card_type in (
                models.Card.TYPE_YELLOW,
                models.Card.TYPE_GREEN,
        ):
            status = models.Status.NAME_ISSUED
        else:
            status = models.Status.NAME_INITIATED
        #

        new_card = models.Card.objects.create(
            type=card_type,
            reason=self.cleaned_data.get('reason'),
            description=self.cleaned_data.get('description'),
            source=models.Card.SOURCE_LEADER,
            incident_dt=self.cleaned_data.get('date'),
            leader_id=self.cleaned_data.get('leader_id'),

            system=models.Status.SYSTEM_CARDS_ASSISTANT,
            status=status,
            user=user,
        )

        return new_card


class RolePermissionMixin(PermissionRequiredMixin):
    permission_required = (
        'is_staff',
    )

    def has_permission(self):
        if self.request.user and not self.request.user.is_anonymous:
            if self.request.user.is_assistant:
                return True
        #   #
        return super(RolePermissionMixin, self).has_permission()


class AddCardAdminFormView(RolePermissionMixin, LoginRequiredMixin, FormView):

    template_name = 'selected-form.html'
    form_class = AddCardForm

    def get_context_data(self, **kwargs):
        context = super(AddCardAdminFormView, self).get_context_data(**kwargs)
        user = models.User.objects.get(leader_id=self.kwargs['leader_id'])
        assert isinstance(user, models.User)
        form = context['form']
        assert isinstance(form, AddCardForm)
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
        assert isinstance(form, AddCardForm)
        if form.is_valid():

            card = form.save(request.user)
            assert isinstance(card, models.Card)
            messages.success(
                request, 'Карточка успешно добавлена "{}"'.format(card.reason)
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


# ############################################################################ #

class BaseAppealsView(
    LoginRequiredMixin,
    TemplateView,
):
    """   """


class AppealForm(forms.Form):
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

    def save(self, card, user):
        # https://docs.djangoproject.com/en/2.2/topics/http/file-uploads/
        # https://stackoverflow.com/questions/1718429/file-does-not-upload-from-web-form-in-django

        new_appeal = models.Appeal.create_new_appeal(
            user=user,
            card=card,
            description=self.cleaned_data.get('description'),
            file=self.cleaned_data.get('file'),

        )
        return new_appeal


class ArgsAppealsFormView(forms.Form):
    # user = forms.ChoiceField(required=True)
    card = forms.UUIDField(required=True)


class AppealsFormView(FormView, BaseAppealsView):
    form_class = AppealForm
    template_name = 'red_cards/appeal_form.html'  # "%s/%s%s.html"

    def get_context_data(self, **kwargs):
        context = super(AppealsFormView, self).get_context_data(**kwargs)

        # ------------------------------------------------------------ #
        params = ArgsAppealsFormView(self.request.GET)
        if not params.is_valid():
            raise Http404
        #
        params = params.cleaned_data
        card = models.Card.objects.get(uuid=params['card'])
        status = card.get_status()
        assert isinstance(status, models.Status)

        #
        if int(self.request.user.leader_id) != int(card.leader_id):
            # only own car can be challenge
            raise HttpResponseForbidden
        #
        # ------------------------------------------------------------ #
        form = context['form']
        assert isinstance(form, AppealForm)
        form.fields['card'].initial = card.uuid
        # ------------------------------------------------------------ #
        context.update({
            'card': card,
        })

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        assert isinstance(form, AppealForm)
        if form.is_valid():
            card = models.Card.objects.get(uuid=form.cleaned_data.get('card'))

            if card.get_status().name != models.Status.NAME_PUBLISHED:
                messages.error(request, 'Карточка уже оспорена')
                return self.get(request, *args, **kwargs)
            #

            appeal = form.save(card, request.user)
            assert isinstance(appeal, models.Appeal)
            # messages.success(
            #     request, 'Апеляция успешно добавлена {}'.format(appeal)
            # )

            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        #

    def get_success_url(self):
        return reverse('appeals-add-success')


class SuccessAppealsFormView(BaseAppealsView):
    template_name = 'red_cards/appeal_form_success.html'  # "%s/%s%s.html"


class ExecutiveMixin:
    """
        для модераторов
        взять аппеляцию на рассмотрение
    """
    def handle_executive(self, request, *args, **kwargs):
        appeal_id = self.request.POST.get('appeal')
        appeal = models.Appeal.objects.filter(pk=appeal_id).first()
        if not appeal:
            messages.error(
                request, 'Заявка не найденна в базе данных.'
            )
            return self.get(request, *args, **kwargs)
        #
        if appeal.status in (
                appeal.STATUS_APPROVED, appeal.STATUS_REJECTED
        ):
            messages.error(
                request, 'Данная заявка закрыта.'
            )
            return self.get(request, *args, **kwargs)
        #
        action = self.request.POST.get('action')
        if action == 'assign':
            appeal.assign(request.user)
            messages.success(
                request, 'Заявка успешно оформлена на {}'.format(
                    request.user.get_full_name()
                )
            )
        elif action == 'free':
            appeal.free()

            messages.success(
                request, '{} теперь больше не расматривает заявку.'.format(
                    request.user.get_full_name()
                )
            )
        else:
            return self.get(request, *args, **kwargs)
        #

        return self.get(request, *args, **kwargs)


class AppealListView(RolePermissionMixin, ExecutiveMixin, BaseAppealsView):
    template_name = 'red_cards/appeal_list.html'

    def get_context_data(self, **kwargs):
        context = super(AppealListView, self).get_context_data(**kwargs)
        appeals = models.Appeal.objects.all().order_by(
            '-create_dt'
        )
        context.update({
            'appeals': appeals,
        })
        return context

    def post(self, request, *args, **kwargs):
        return self.handle_executive(request, *args, **kwargs)


class ArgsAppealDetailAdminView(forms.Form):
    pk = forms.IntegerField(required=True)

    def get_appeal(self):
        if not self.is_valid():
            return None
        #
        return models.Appeal.objects.filter(
            pk=self.cleaned_data.get('pk')
        ).first()


class AppealDetailAdminView(RolePermissionMixin, ExecutiveMixin, BaseAppealsView):
    template_name = 'red_cards/appeal_detail_admin.html'

    def get_context_data(self, **kwargs):
        context = super(AppealDetailAdminView, self).get_context_data(**kwargs)
        appeal = ArgsAppealDetailAdminView(kwargs).get_appeal()
        context.update({
            'card': appeal.card,
            'appeal': appeal,
        })
        return context

    def post(self, request, *args, **kwargs):
        form_name = self.request.POST.get('form_name')
        if form_name == 'executive':
            return self.handle_executive(request, *args, **kwargs)
        elif form_name == 'manage':
            appeal = models.Appeal.objects.filter(
                pk=self.request.POST.get('appeal')
            ).first()
            if appeal is None:
                messages.error(request, 'Заявка не найдена в базе данных')
                return self.get(request, *args, **kwargs)
            #
            assert isinstance(appeal, models.Appeal)
            if request.user != appeal.executive:
                messages.error(request, 'Заявку рассматривает другой модератор')
                return self.get(request, *args, **kwargs)
            #

            if appeal.status != appeal.STATUS_IN_WORK:
                messages.error(request, 'Заявка уже закрыта')
                return self.get(request, *args, **kwargs)
            #

            action = self.request.POST.get('action')
            if action == 'accept':
                appeal.accept(request.user)
            elif action == 'reject':
                appeal.reject(request.user)
            else:
                return self.get(request, *args, **kwargs)  # if hacker
            #
            return self.get(request, *args, **kwargs)
        else:
            return self.get(request, *args, **kwargs)
        #


# ############################################################################ #

class SearchView(RolePermissionMixin, TemplateView):
    template_name = 'selection-page.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        all_users = models.User.objects.filter(
            leader_id__isnull=False,
        ).order_by(
            'first_name', 'last_name', 'username'
        ).all()
        selected_users = []

        selected_user = self.request.GET.get('user', None)
        if selected_user:
            selected_user = selected_user.split(' ', 1)[0].strip('L')
            selected_user = models.User.objects.filter(
                leader_id=selected_user
            ).first()
        #
        if selected_user:
            selected_users.append(selected_user)
        #

        # _page_id = self.request.GET.get('page', 1)
        # paginator = Paginator(all_users, 10)
        # page_users = paginator.get_page(_page_id)
        # #

        # by_search = True
        # if not selected_users:
        #     selected_users = page_users
        #     by_search = False
        # #

        context.update({
            'all_users':        all_users,
            'selected_users':   selected_users,
            # 'by_search':        by_search,
        })
        return context

# ############################################################################ #


class RecommendedCardsFilterForm(forms.Form):
    status = forms.ChoiceField(
        label=_('Выберите статус карточки'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('По статусу'),
        }),
        choices=(
            (models.Status.NAME_APPROVED,       _('Одобрена')),
            (models.Status.NAME_REJECTED,       _('Отклонена')),
            (models.Status.NAME_PUBLISHED,      _('Опубликована')),
            (models.Status.NAME_CONSIDERATION,  _('На рассмотрении')),
            (models.Status.NAME_ELIMINATED,     _('Деактивирована')),
            ('',       _('Показать все')),
        ),
        required=False,
    )
    DATE_NEW = 'new'
    DATE_OLD = 'old'
    date = forms.ChoiceField(
        label=_('Выберите время изменения карточки'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('По дате'),
        }),
        choices=(
            (DATE_NEW, _('Сначала новые записи')),
            (DATE_OLD, _('Сначала старые записи')),
            ('',       _('Показать все')),
        ),
        required=False,
    )


class RecommendedCardsView(RolePermissionMixin, TemplateView):
    """

    """
    template_name = 'approved.html'

    def get_context_data(self, **kwargs):
        context = super(RecommendedCardsView, self).get_context_data(**kwargs)

        cards = models.Card.objects.filter(
            type__in=(models.Card.TYPE_YELLOW, models.Card.TYPE_RED),
        ).all()

        filters_form = RecommendedCardsFilterForm(self.request.GET)
        if filters_form.is_valid():
            filters = filters_form.cleaned_data
            if filters.get('status', ''):
                cards = cards.filter(last_status=filters['status'])
            #
            if filters.get('date', '') == filters_form.DATE_NEW:
                cards = cards.order_by('-status__change_dt')
            #
            if filters.get('date', '') == filters_form.DATE_OLD:
                cards = cards.order_by('status__change_dt')
            #
        #
        context.update({
            'cards':        cards,
            'filters_form': filters_form,
        })
        return context

    def post(self, request, *args, **kwargs):
        card = models.Card.objects.filter(
            pk=self.request.POST.get('card')
        ).first()
        if card is None:
            messages.error(request, 'Карточка не найдена в базе данных')
            return self.get(request, *args, **kwargs)
        #
        assert isinstance(card, models.Card)
        #

        if card.last_status not in (models.Status.NAME_INITIATED, models.Status.NAME_RECOMMENDED):
            messages.error(request, 'Карточку уже изменина')
            return self.get(request, *args, **kwargs)
        #

        action = self.request.POST.get('action')
        if action == 'accept':
            card.set_status(
                name=models.Status.NAME_PUBLISHED,
                system=models.Status.SYSTEM_CARDS_MODERATOR,
                user=request.user
            )
            messages.success(request, 'Карточка "{}" одобрена'.format(card.reason))
        elif action == 'reject':
            card.set_status(
                name=models.Status.NAME_REJECTED,
                system=models.Status.SYSTEM_CARDS_MODERATOR,
                user=request.user
            )
            messages.success(request, 'Карточка "{}" отклонена'.format(card.reason))

        else:
            return self.get(request, *args, **kwargs)  # if hacker
        #
        return self.get(request, *args, **kwargs)

