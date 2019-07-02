from django.conf import settings
from social_core.backends.oauth import BaseOAuth2
from social_core.utils import handle_http_errors

from urllib.parse import urljoin


def update_user(strategy, details, user=None, backend=None, *args, **kwargs):
    data = kwargs['response']
    if user:
        user.email = data['email']
        user.username = data['username']
        user.first_name = data['firstname']
        user.last_name = data['lastname']
        user.second_name = data.get('secondname', '') or ''
        # user.icon = data.get('image') or {}
        # tags = data.get('tags') or []
        # user.is_assistant = any(i in tags for i in settings.ASSISTANT_TAGS_NAME)
        # user.unti_id = data.get('unti_id')
        # user.leader_id = data.get('leader_id') or ''
        user.save()
    #


# from social_core.pipeline.user.create_use
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
        'social_core.pipeline.user.create_user',
        'app_django.auth.update_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
    )

    skip_email_verification = True

    def auth_url(self):
        result = '{}&auth_entry={}'.format(
            super(UNTIBackend, self).auth_url(),
            self.data.get('auth_entry', 'login')
        )
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
        return result

    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token)
        data['access_token'] = access_token
        kwargs.update(data)
        kwargs.update({'response': data, 'backend': self})
        result = self.strategy.authenticate(*args, **kwargs)
        return result

_t = '''
self.AUTHORIZATION_URL
'https://sso.u2035test.ru/oauth2/authorize'
self.ACCESS_TOKEN_URL
'https://sso.u2035test.ru/oauth2/access_token'


---------------------------------------
1) открываю страницу redcards.ap8.ru
нажимаю кнопочку "Войти"

2) вызываеться  
    - UNTIBackend.auth_url
    - BaseOAuth2.auth_url
    - BaseOAuth2.auth_params
        print(json.dumps(params, indent=2))
        {
          "client_id": "7907f6bfa95197ddcb1d",
          "redirect_uri": "http://redcards.ap8.ru/complete/unti/",
          "state": "PbOyBLaHkaZUIkow8ksHfpRanEFY10a3",
          "response_type": "code"
        }
    - редирект
    https://sso.u2035test.ru
    /oauth2/authorize
    ?client_id=7907f6bfa95197ddcb1d
    &redirect_uri=http://redcards.ap8.ru/complete/unti/&state=PbOyBLaHkaZUIkow8ksHfpRanEFY10a3&response_type=code&auth_entry=login'



2) попадаю на https://leader-id.ru/login/
сайт просит авторитизироваться
ввожу 
    jen.soft.master@gmail.com  
    7895123qw@

после этого перекидывает сюда 
http://redcards.ap8.ru/
127.0.0.1 - - [02/Jul/2019 21:02:39] "GET /login/unti/?next=http://redcards.ap8.ru HTTP/1.1" 302 -

=============================================
{
  "client_id": "7907f6bfa95197ddcb1d",
  "redirect_uri": "http://redcards.ap8.ru/complete/unti/",
  "state": "PbOyBLaHkaZUIkow8ksHfpRanEFY10a3",
  "response_type": "code"
}

https://sso.u2035test.ru
/oauth2/authorize
?client_id=7907f6bfa95197ddcb1d
&redirect_uri=http://redcards.ap8.ru/complete/unti/&state=PbOyBLaHkaZUIkow8ksHfpRanEFY10a3&response_type=code&auth_entry=login'

---
BaseOAuth2.auth_complete
127.0.0.1 - - [02/Jul/2019 21:11:06] "GET /login/unti/?next=http://redcards.ap8.ru HTTP/1.1" 302 -
BaseOAuth2.auth_complete




================

urlpatterns = [
    # authentication / association
    url(r'^login/(?P<backend>[^/]+){0}$'.format(extra), views.auth,
        name='begin'),
    url(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), views.complete,
        name='complete'),
    # disconnection
    url(r'^disconnect/(?P<backend>[^/]+){0}$'.format(extra), views.disconnect,
        name='disconnect'),
    url(r'^disconnect/(?P<backend>[^/]+)/(?P<association_id>\d+){0}$'
        .format(extra), views.disconnect, name='disconnect_individual'),
]

'''

