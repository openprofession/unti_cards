import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from app_django.settings import LOGOUT_REDIRECT
from red_cards.api import XLEApi, UploadsApi, AttendanceApi
from red_cards.models import Event
from red_cards.utils import update_events_data, update_enrolls_data
from django.utils.translation import ugettext_lazy as _
from . import models
from django.contrib.auth.views import logout_then_login as base_logout
from django.contrib.auth.mixins import LoginRequiredMixin, \
    PermissionRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

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
        leader_id=request.user.leader_id or None
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
        current_user = self.request.user
        if not current_user.is_anonymous:
            if current_user.is_assistant:
                return True
        #   #
        return super(RolePermissionMixin, self).has_permission()


class AddCardAdminFormView(RolePermissionMixin, LoginRequiredMixin, FormView):

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


def api_test_all(request):
    test = {}
    xle1 = XLEApi().get_attendance()
    xle2 = XLEApi().get_timetable(date=datetime.date(2019, 7, 12))
    xle3 = XLEApi().get_enrolls(event_uuid='edc82d79-d6d1-4d07-81cc-6d426e6845fa')
    test['xle_timetable'] = {'system': 'XLE', 'method': 'xle_timetable', 'datetime': now, 'status': 'OK', 'result': len(xle2)}
    test['xle_enrolls'] = {'system': 'XLE', 'method': 'xle_enrolls', 'datetime': now, 'status': 'OK', 'result': len(xle3)}
    upl1 = UploadsApi().get_attendance()
    upl2 = UploadsApi().check_user_trace(event_id='cd602dd7-4fef-440b-82bf-013b5817e3dd')

    #test['upl_attendance'] = {'system': 'UPLOADS', 'method': 'upl_attendance', 'datetime': now, 'status': 'OK', 'result': upl1['count']}
    test['upl_user_trace'] = {'system': 'UPLOADS', 'method': 'upl_user_trace', 'datetime': now, 'status': 'OK', 'result': len(upl2)}
    # print(upl1['count'])
    # print(upl2)

    att1 = AttendanceApi().get_attendance_event('4f46d075-f56b-4e84-b4e6-2e1be0a9bdf7')
    test['att_attendance_event'] = {'system': 'ATTENDANCE', 'method': 'att_attendance_event', 'datetime': now, 'status': 'OK', 'result': len(att1)}

    return render(request, template_name='test_api.html', context={'test': test})


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
        required=False,
        min_length=2,
        max_length=1000,
    )

    tag = forms.ModelChoiceField(
        label=_('тег'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('выберите тег'),
        }),
        queryset=models.AppealTag.objects.all(),
        empty_label=_('без тега'),
        required=False,
    )

    file = forms.FileField(
        label=_('Выберите файл'),
        label_suffix='',
        widget=forms.FileInput(),
        required=False,
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
            tag=self.cleaned_data.get('tag'),
            file=self.cleaned_data.get('file'),

        )
        return new_appeal

    def clean(self):
        if 'file' in self.cleaned_data:
            file = self.cleaned_data['file']
            # content_type = content.content_type.split('/')[0]
            # if content_type not in settings.CONTENT_TYPES:
            #     raise forms.ValidationError(_('File type is not supported'))
            #
            if file:
                if file.size > MAX_UPLOAD_SIZE:
                    raise forms.ValidationError(_(
                        'Максимальный размер файла %s. Текущий размер файла %s'
                    ) % (
                        filesizeformat(MAX_UPLOAD_SIZE),
                        filesizeformat(file.size)
                    ))
        #   #   #
        return super(AppealForm, self).clean()

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
                return redirect(request.get_full_path())
            #
            if int(self.request.user.leader_id) != int(card.leader_id):
                # only own car can be challenge
                raise HttpResponseForbidden
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
            return redirect(request.get_full_path())
        #
        # if appeal.status in (
        #         appeal.STATUS_APPROVED, appeal.STATUS_REJECTED
        # ):
        #     messages.error(
        #         request, 'Данная заявка закрыта.'
        #     )
        #     return redirect(request.get_full_path())
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
            return redirect(request.get_full_path())
        #

        return redirect(request.get_full_path())


class AppealListFilterForm(forms.Form):

    # По статусу: Не просмотрено, На рассмотрении, Принято, Отказ
    status = forms.ChoiceField(
        label=_('Выберите статус апеляции'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('По статусу'),
        }),
        # AppealListFilterForm(initial={'status': models.Appeal.STATUS_NEW})
        choices=(
            (models.Appeal.STATUS_NEW,          _('Не просмотрено')),
            (models.Appeal.STATUS_IN_WORK,      _('На рассмотрении')),
            (models.Appeal.STATUS_APPROVED,     _('Принято')),
            (models.Appeal.STATUS_REJECTED,     _('Отказ')),
            ('all', _('все')),
        ),
        # initial=models.Appeal.STATUS_NEW,
        required=False,
    )

    new_messages = forms.ChoiceField(
        label=_('Есть новые соообщения'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('По сообщениям'),
        }),
        choices=(
            ('only_new',            _('есть новые сообщения')),
            ('has_comments',        _('есть сообщения')),
            ('no_comments',         _('без сообщений')),
            ('all', _('все')),
        ),
        required=False,
    )

    tag = forms.ModelChoiceField(
        label=_('по тегу'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('по тегу'),
        }),
        queryset=models.AppealTag.objects.all(),
        empty_label=_('все'),
        required=False,
    )

    def full_clean(self):
        super(AppealListFilterForm, self).full_clean()
        for k in self.cleaned_data:
            if self.cleaned_data[k] == 'all':
                self.cleaned_data[k] = None
        #   #


class AppealListView(RolePermissionMixin, ExecutiveMixin, BaseAppealsView):
    template_name = 'red_cards/appeal_list.html'

    def get_context_data(self, **kwargs):
        context = super(AppealListView, self).get_context_data(**kwargs)
        appeals = models.Appeal.objects.all().order_by(
            '-create_dt'
        )

        all_users = models.User.objects.filter(
            leader_id__isnull=False,
        ).filter(
            leader_id__in=models.Card.objects.filter(
                uuid__in=models.Appeal.objects.all().values('card__uuid')
            ).values('leader_id'),
        ).order_by(
            'first_name', 'last_name', 'username'
        ).all()
        # Вывод статистики: - общая без учета фильтров
        #       Не просмотрено,
        #       На рассмотрении,
        #       Принято,
        #       Отказ,
        #       C новыми сообщениями

        appeals_stats = {
            'new':          appeals.filter(status=models.Appeal.STATUS_NEW).count(),
            'in_work':      appeals.filter(status=models.Appeal.STATUS_IN_WORK).count(),
            'approved':     appeals.filter(status=models.Appeal.STATUS_APPROVED).count(),
            'rejected':     appeals.filter(status=models.Appeal.STATUS_REJECTED).count(),
            'has_new_messages':     appeals.filter(
                    id__in=models.AppealComment.objects.exclude(
                        seen_by_users=self.request.user
                    ).values('appeal')
                ).count(),
        }

        # status = STATUS_NEW by default
        _data = self.request.GET.dict()
        # ----------------------^^^^^^ IMPORTANT or will be list instead value
        if 'status' not in _data:
            _data['status'] = models.Appeal.STATUS_NEW
        #
        filters_form = AppealListFilterForm(_data)

        if filters_form.is_valid():
            filters = filters_form.cleaned_data
            if filters.get('status', ''):
                appeals = appeals.filter(status=filters['status'])
            #
            if filters.get('tag', ''):
                appeals = appeals.filter(tag=filters['tag'])
            #
            if filters.get('new_messages', '') == 'no_comments':
                appeals = appeals.exclude(
                    id__in=models.AppealComment.objects.values('appeal')
                )
            #
            if filters.get('new_messages', '') == 'has_comments':
                appeals = appeals.filter(
                    id__in=models.AppealComment.objects.values('appeal')
                )
            #
            if filters.get('new_messages', '') == 'only_new':
                appeals = appeals.filter(
                    id__in=models.AppealComment.objects.exclude(
                        seen_by_users=self.request.user
                    ).values('appeal')
                )
            #
        #
        _selected_user = self.request.GET.get('user', '')
        selected_leader_id = _selected_user.split(' ', 1)[0].strip('L')
        selected_user = models.User.objects.filter(
            leader_id=selected_leader_id
        ).first()
        if selected_user:
            appeals = appeals.filter(
                card__uuid__in=models.Card.objects.filter(
                    leader_id=selected_user.leader_id
                ).all()
            ).all()
        #

        context.update({
            'selected_user':          selected_user,
            'all_users':          all_users,
            'appeals':          appeals,
            'filters_form':     filters_form,
            'appeals_stats':    appeals_stats,
        })
        return context

    def post(self, request, *args, **kwargs):
        if not super(AppealListView, self).has_permission():
            return self.handle_no_permission()
        #
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


class AppealTagForm(forms.Form):
    FORM_NAME = 'appeal_tag'

    form_name = forms.CharField(
        widget=forms.HiddenInput,
        initial=FORM_NAME,
    )

    appeal = forms.IntegerField(
        widget=forms.HiddenInput,
    )

    tag = forms.ModelChoiceField(
        label=_('Выберите тег апеляции'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('тег апеляции'),
        }),
        queryset=models.AppealTag.objects.all(),
        empty_label=_('без тега'),
        required=False,
    )

    def save(self):
        appeal = models.Appeal.objects.filter(
            id=self.cleaned_data.get('appeal')
        ).first()
        if appeal:
            appeal.tag = self.cleaned_data.get('tag')
            appeal.save()
        #
        return appeal


class AppealDetailAdminView(RolePermissionMixin, ExecutiveMixin, BaseAppealsView):
    template_name = 'red_cards/appeal_detail_admin.html'

    def has_permission(self):
        # return super(AppealDetailAdminView, self).has_permission()
        return True

    def get_appeal(self, **kwargs):
        appeal = getattr(self, '_appeal', None)
        if not appeal:
            appeal = ArgsAppealDetailAdminView(kwargs).get_appeal()
        #
        if not appeal:
            raise Http404
        #
        assert isinstance(appeal, models.Appeal)
        setattr(self, '_appeal', appeal)
        return appeal

    def _has_permission_for_appeal(self, **kwargs):
        if super(AppealDetailAdminView, self).has_permission():
            return True
        #
        if self.request.user.is_anonymous:
            return False
        #
        appeal = self.get_appeal(**kwargs)
        if int(appeal.card.leader_id) == int(self.request.user.leader_id):
            return True  # allow access for owner
        #
        return False

    def get_context_data(self, **kwargs):
        context = super(AppealDetailAdminView, self).get_context_data(**kwargs)
        appeal = self.get_appeal(**kwargs)

        if not self._has_permission_for_appeal(**kwargs):
            return self.handle_no_permission()
        #
        appeal_tag_form = AppealTagForm(initial={
            'appeal': appeal.pk,
            'tag': appeal.tag,
        })
        comment_form = getattr(self, '_comment_form', AppealCommentForm())
        #
        comments = appeal.get_comments()
        for comment in comments:
            assert isinstance(comment, models.AppealComment)
            if self.request.user not in comment.seen_by_users.all():
                comment.seen_by_users.add(self.request.user)
        #   #
        context.update({
            'card':             appeal.card,
            'appeal':           appeal,
            'comment_form':     comment_form,
            'comments':         comments,

            'appeal_tag_form':  appeal_tag_form,
        })
        return context

    def post(self, request, *args, **kwargs):
        if not self._has_permission_for_appeal(**kwargs):
            return self.handle_no_permission()
        #
        # ------------------------------------------------------------ #

        form_name = self.request.POST.get('form_name')
        if form_name == 'comment':
            # if appeal.status not in (
            #         appeal.STATUS_NEW,
            #         appeal.STATUS_IN_WORK,
            # ):
            #     return redirect(request.get_full_path())
            #
            comment_form = AppealCommentForm(
                data=self.request.POST,
                files=self.request.FILES,
            )
            setattr(self, '_comment_form', comment_form)
            context = self.get_context_data(**kwargs)
            appeal = context['appeal']
            if comment_form.is_valid():
                comment_form.save(request.user, appeal)
                return redirect(request.get_full_path())
            #
            # return redirect(request.get_full_path())
            return self.get(request, *args, **kwargs)
        #   #

        # ------------------------------------------------------------ #
        if not super(AppealDetailAdminView, self).has_permission():
            return self.handle_no_permission()
        #
        if form_name == AppealTagForm.FORM_NAME:
            form = AppealTagForm(data=self.request.POST)
            if form.is_valid():
                form.save()
            #
            return redirect(request.get_full_path())
        if form_name == 'executive':
            self.handle_executive(request, *args, **kwargs)
            return redirect(request.get_full_path())
        elif form_name == 'manage':
            appeal = models.Appeal.objects.filter(
                pk=self.request.POST.get('appeal')
            ).first()
            if appeal is None:
                messages.error(request, 'Заявка не найдена в базе данных')
                return redirect(request.get_full_path())
            #
            assert isinstance(appeal, models.Appeal)
            if request.user != appeal.executive:
                messages.error(request, 'Заявку рассматривает другой модератор')
                return redirect(request.get_full_path())
            #

            # if appeal.status != appeal.STATUS_IN_WORK:
            #     messages.error(request, 'Заявка уже закрыта')
            #     return redirect(request.get_full_path())
            #

            action = self.request.POST.get('action')
            if action == 'accept':
                appeal.accept(request.user)
            elif action == 'reject':
                appeal.reject(request.user)
            else:
                return redirect(request.get_full_path())  # if hacker
            #
            return redirect(request.get_full_path())
        else:
            return redirect(request.get_full_path())
        #


class AppealCommentForm(forms.Form):
    text = forms.CharField(
        label=_('Описание'),
        label_suffix='',
        widget=forms.Textarea(attrs={
            'placeholder': _('Опишите, что произошло...'),
        }),
        min_length=1,
        max_length=1000,
    )

    file = forms.FileField(
        label=_('Выберите файл'),
        label_suffix='',
        widget=forms.FileInput(),
        required=False,
    )

    def save(self, user, appeal):
        comment = models.AppealComment.objects.create(
            user=user,
            appeal=appeal,
            file=self.cleaned_data.get('file'),
            text=self.cleaned_data.get('text'),
        )
        return comment

    def clean(self):
        if 'file' in self.cleaned_data:
            file = self.cleaned_data['file']
            # content_type = content.content_type.split('/')[0]
            # if content_type not in settings.CONTENT_TYPES:
            #     raise forms.ValidationError(_('File type is not supported'))
            #
            if file:
                if file.size > MAX_UPLOAD_SIZE:
                    raise forms.ValidationError(_(
                        'Максимальный размер файла %s. Текущий размер файла %s'
                    ) % (
                        filesizeformat(MAX_UPLOAD_SIZE),
                        filesizeformat(file.size)
                    ))
        #   #   #
        return super(AppealCommentForm, self).clean()
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

class SearchUserCardsFilterForm(forms.Form):
    STATUS_ALL = '_all'

    def full_clean(self):
        super(SearchUserCardsFilterForm, self).full_clean()
        for k in self.cleaned_data:
            if self.cleaned_data[k] == self.STATUS_ALL:
                self.cleaned_data[k] = None
        #   #

    STATUS_ACTIVE = '_active'
    status = forms.ChoiceField(
        label=_('Выберите статус карточки'),
        label_suffix='',
        widget=forms.Select(attrs={
            'title': _('По статусу'),
        }),
        choices=(
            (STATUS_ACTIVE,                     _('Активные')),
            (models.Status.NAME_ELIMINATED,     _('Деактивирована')),
            (models.Status.NAME_PUBLISHED,      _('Можно оспорить')),
            (models.Status.NAME_ISSUED,         _('Выдана')),
            (models.Status.NAME_CONSIDERATION,  _('Оспорена - на рассмотрении')),
            (STATUS_ALL,                        _('Показать все')),
        ),
        required=False,
    )
    type = forms.ChoiceField(
        label=_('Тип карточки'),
        widget=forms.Select(attrs={
            'title': _('По типу'),
        }),
        choices=(
            *models.Card.TYPE_CHOICES,
            (STATUS_ALL,                        _('Показать все')),
        ),
        required=False,
        # initial=models.Card.TYPE_RED,
    )


class SearchUserCardsView(RolePermissionMixin, TemplateView):
    """

    страничка для ассистента где он может
        вбить лидер/фио и
        посмотреть список карточек у юзера в статусах
            published, issued, consideration, eliminated

    надписи по статусам на русском такие:
        published -Можно оспорить
        issued - Выдана
        Consideration - Оспорена. На рассмотрении
        eliminated - Деактивирована

    DOD:
    1. Доступно только ассистенту
    2. Добавлен фильтр по типу карточки -
        Красная, Желтая, Зеленая, Все
        - по умолчанию Красная
    3. Добавлен фильтра по статусу -
        Активные(все кроме eliminated)/
        Деактивированные(eliminated)/
        Все,
        - по умолчанию Активные
    3. Визуальные статусы и кнопки - изменения касаются только красных карточек:
        issued Cards-issue:  визульный статус: Выдана + кнопка Деактивировать
        issued Cards-appeal : Оспаривание отклонено + кнопка Перейти к заявке
        -Consideration system любой: Оспорена-на рассмотрении + кнопка "Перейти к заявке"
        -published system любой: Можно оспорить + кнопка Деактивировать
        -eliminated Cards-appeal: Успешно оспорена + кнопка "Перейти к заявке"
        -eliminated Cards-deactivate: Деактивирована
    """
    template_name = 'selection-page-user-cards.html'

    def get_context_data(self, **kwargs):
        context = super(SearchUserCardsView, self).get_context_data(**kwargs)
        all_users = models.User.objects.filter(
            leader_id__isnull=False,
        ).order_by(
            'first_name', 'last_name', 'username'
        ).all()

        selected_user = self.request.GET.get('user', None)
        if selected_user:
            selected_user = selected_user.split(' ', 1)[0].strip('L')
            selected_user = models.User.objects.filter(
                leader_id=selected_user
            ).first()
        #

        # status = TYPE_RED by default
        _data = self.request.GET.dict()
        # ----------------------^^^^^^ IMPORTANT or will be list instead value
        if 'type' not in _data:
            _data['type'] = models.Card.TYPE_RED
        #
        filters_form = SearchUserCardsFilterForm(_data)

        cards = []
        if selected_user:
            cards = models.Card.objects.filter(
                leader_id=selected_user.leader_id,
                last_status__in=(
                    models.Status.NAME_PUBLISHED,
                    models.Status.NAME_ISSUED,
                    models.Status.NAME_CONSIDERATION,
                    models.Status.NAME_ELIMINATED,
                )
            )

            if filters_form.is_valid():
                filters = filters_form.cleaned_data
                if filters.get('status', ''):
                    if filters['status'] == filters_form.STATUS_ACTIVE:
                        cards = cards.exclude(  # <== (!)
                            last_status=models.Status.NAME_ELIMINATED)
                    else:
                        cards = cards.filter(last_status=filters['status'])
                    #
                if filters.get('type', ''):
                    cards = cards.filter(type=filters['type'])
        #   #   #

        context.update({
            'all_users':        all_users,
            'selected_user':   selected_user,

            'cards':   cards,
            'filters_form':   filters_form,
        })
        return context

    def post(self, request, *args, **kwargs):
        if 'card' not in request.POST:
            return self.get(request, *args, **kwargs)
        #
        card = models.Card.objects.filter(
            uuid=request.POST.get('card')
        ).first()
        if not card:
            return self.get(request, *args, **kwargs)
        #
        card.set_status(
            name=models.Status.NAME_ELIMINATED,
            system=models.Status.SYSTEM_CARDS_DEACTIVATE,
            user=request.user,
        )
        messages.success(request, 'Карточка "{}" успешно деактивированна'.format(
            card.reason
        ))
        return redirect(request.get_full_path())

