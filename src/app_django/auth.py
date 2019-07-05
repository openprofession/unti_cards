from django.conf import settings
from social_core.backends.oauth import BaseOAuth2
from social_core.utils import handle_http_errors
from django.contrib.auth import get_user_model

from urllib.parse import urljoin


def update_user(strategy, details, user=None, backend=None, *args, **kwargs):
    # https://stackoverflow.com/questions/24629705/django-using-get-user-model-vs-settings-auth-user-model
    data = kwargs['response']

    email = data['email']
    unti_id = data.get('unti_id')
    leader_id = str(data.get('leader_id') or '')  # todo: need set int for user-model

    User = get_user_model()

    # by unti_id
    if not user:
        if unti_id:
            user = User.objects.filter(unti_id=unti_id).first()
    #   #

    # by leader_id
    if not user:
        if leader_id:
            user = User.objects.filter(leader_id=leader_id).first()
    #   #

    # by email
    if not user:
        user = User.objects.filter(email=email).first()
    #   #

    if user:
        user.email = data['email']
        user.username = data['username']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.second_name = data.get('secondname', '') or ''
        # user.icon = data.get('image') or {}
        tags = data.get('tags') or []
        # user.is_assistant = any(i in tags for i in settings.ASSISTANT_TAGS_NAME)
        user.unti_id = unti_id
        user.leader_id = leader_id
        user.save()
        return {'is_new': False}
    #


class UNTIBackend(BaseOAuth2):
    name = 'unti'
    ID_KEY = 'unti_id'
    AUTHORIZATION_URL = urljoin(settings.SSO_UNTI_URL, 'oauth2/authorize')
    ACCESS_TOKEN_URL = urljoin(settings.SSO_UNTI_URL, 'oauth2/access_token')

    DEFAULT_SCOPE = []
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'

    PIPELINE = (
        'social_core.pipeline.social_auth.social_details',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'app_django.auth.update_user',
        'social_core.pipeline.user.create_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
    )

    skip_email_verification = True

    # def get_redirect_uri(self, state=None):
    #     result = super(UNTIBackend, self).get_redirect_uri()
    #     return quote(result)

    def auth_url(self):
        result = '{}&auth_entry={}'.format(
            super(UNTIBackend, self).auth_url(),
            self.data.get('auth_entry', 'login')
        )
        print(result)
        return result

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        self.strategy.session.setdefault('{}_state'.format(self.name),
                                         self.data.get('state'))
        next_url = getattr(settings, 'SOCIAL_NEXT_URL', '/')
        self.strategy.session.setdefault('next', next_url)
        result = super(UNTIBackend, self).auth_complete(*args, **kwargs)
        return result

    def pipeline(self, pipeline, pipeline_index=0, *args, **kwargs):
        """
        Hack for using in open edx our custom DEFAULT_AUTH_PIPELINE
        """
        self.strategy.session.setdefault('auth_entry', 'register')
        result = super(UNTIBackend, self).pipeline(
            pipeline=self.PIPELINE, pipeline_index=pipeline_index, *args, **kwargs
        )
        return result

    def get_user_details(self, response):
        """ Return user details from SSO account. """
        return response

    def user_data(self, access_token, *args, **kwargs):
        """ Grab user profile information from SSO. """
        result = self.get_json(
            urljoin(settings.SSO_UNTI_URL, 'users/me'),
            params={'access_token': access_token},
            headers={'Authorization': 'Bearer {}'.format(access_token)},
        )
        result['leader_id'] = int(result['leader_id'])
        result['first_name'] = result.pop('firstname')
        result['last_name'] = result.pop('lastname')
        return result

    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token)
        data['access_token'] = access_token
        kwargs.update(data)
        kwargs.update({'response': data, 'backend': self})
        result = self.strategy.authenticate(*args, **kwargs)
        return result

