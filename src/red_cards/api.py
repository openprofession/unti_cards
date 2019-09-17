import logging

import requests
from django.core.cache import caches

from app_django import settings

DEFAULT_CACHE = caches['default']


class ApiError(Exception):
    pass


class ApiNotFound(ApiError):
    pass


class BadApiResponse(ApiError):
    pass


class BaseApi:
    name = ''
    base_url = ''
    app_token = ''
    authorization = {}

    def add_authorization_to_kwargs(self, kwargs):
        for key, item in self.authorization.items():
            if key in kwargs and isinstance(kwargs[key], dict):
                kwargs[key].update(item)
            else:
                kwargs[key] = item

    def make_request(self, url, method='GET', **kwargs):
        """
        итератор по всем страницам ответа
        """
        url = '{}{}'.format(self.base_url, url)
        page = 1
        total_pages = None
        kwargs.setdefault('timeout', settings.CONNECTION_TIMEOUT)
        self.add_authorization_to_kwargs(kwargs)
        while total_pages is None or page <= total_pages:
            try:
                kwargs['params']['page'] = page
                resp = requests.request(method, url, **kwargs)
                assert resp.ok, 'status_code %s' % resp.status_code
                total_pages = int(resp.headers['X-Pagination-Page-Count'])
                yield resp.json()
                page += 1
            except (ValueError, TypeError, AssertionError):
                logging.exception('Unexpected %s response for url %s' % (self.name, url))
                raise BadApiResponse
            except KeyError:
                logging.error('%s %s response has no header "X-Pagination-Page-Count"' % (self.name, url))
                raise ApiError
            except AssertionError:
                logging.exception('%s connection error' % self.name)
                raise ApiError

    def make_request_no_pagination(self, url, method='GET', **kwargs):
        """
        запрос, не предполагающий пагинацию в ответе
        """
        if not url.startswith(('http://', 'https://')):
            url = '{}{}'.format(self.base_url, url)
        kwargs.setdefault('timeout', settings.CONNECTION_TIMEOUT)
        self.add_authorization_to_kwargs(kwargs)
        try:
            resp = requests.request(method, url, **kwargs)
            assert resp.ok, 'status_code %s' % resp.status_code
            return resp.json()
        except (ValueError, TypeError, AssertionError):
            logging.exception('Unexpected %s response for url %s' % (self.name, url))
            raise BadApiResponse
        except AssertionError:
            logging.exception('%s connection error' % self.name)
            raise ApiError

    def health_check(self):
        try:
            resp = requests.head(self.base_url)
            if resp.status_code < 400:
                return 'ok'
            else:
                logging.error('Health check returned code %s for system %s' % (resp.status_code, self.name))
                return resp.status_code
        except requests.RequestException:
            logging.exception('Health check error for system %s' % self.name)


class XLEApi(BaseApi):
    name = 'xle'
    base_url = settings.XLE_URL.rstrip('/')
    authorization = {'params': {'app_token': getattr(settings, 'XLE_TOKEN', '')}}

    def get_attendance(self):
        return self.make_request_no_pagination('/api/v1/checkin')

    def get_timetable(self, date):
        return self.make_request_no_pagination(
            '/api/v1/timetable/all?context={}&date={}'.format(getattr(settings, 'XLE_CONTEXT', ''), date))

    def get_enrolls(self, event_uuid):
        return self.make_request_no_pagination('/api/v1/timetable?&event_uuid={}'.format(event_uuid))


class LABSApi(BaseApi):
    name = 'labs'
    base_url = settings.LABS_URL.rstrip('/')
    authorization = {'params': {'app_token': getattr(settings, 'LABS_TOKEN', '')}}
    verify = False

    def get_activities(self, date_min=None, date_max=None):
        params = {}
        if date_min:
            params['date_min'] = date_min
        if date_max:
            params['date_max'] = date_max
        return self.make_request_no_pagination('/api/v2/activity', params=params)

    def get_types(self):
        return self.make_request_no_pagination('/api/v2/type')

    def get_contexts(self):
        return self.make_request_no_pagination('/api/v2/context')


class UploadsApi(BaseApi):
    name = 'uploads'
    base_url = settings.UPLOADS_URL.rstrip('/')
    authorization = {'headers': {'x-api-key': getattr(settings, 'UPLOADS_TOKEN', '')}}

    def get_all_user_result(self):
        params = {}
        return self.make_request_no_pagination('/api/all-team-results/', params=params)

    def get_attendance(self):
        return self.make_request_no_pagination('/api/attendance/')

    def check_user_trace(self, event_id):
        params = {}
        params['event_id'] = event_id
        return self.make_request_no_pagination('/api/check-user-trace/', params=params)


class AttendanceApi(BaseApi):
    name = 'attendance'
    base_url = settings.ATTENDANCE_URL
    authorization = {'headers': {'Authorization': 'Token {}'.format(getattr(settings, 'ATTENDANCE_TOKEN', ''))}}

    def get_attendance_event(self, event_id):
        params = {}
        return self.make_request_no_pagination('/api/v0/attendance/event/{}/'.format(event_id), params=params)
