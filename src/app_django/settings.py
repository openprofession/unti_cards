"""
Django settings for app_django project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'cgju4#-d_ewl!vt$t=!hh+0!jpqk+teyo$kwl1v(6$boob2st='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', ]

# Application definition

INSTALLED_APPS = [
    'social_django',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_core',
    'django_filters',
    'rest_framework',
    'rest_framework_api_key',
    'red_cards',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # "social_django.middleware.SocialAuthExceptionMiddleware",
    'app_django.middleware.CustomSocialAuthMiddleware',
]


ROOT_URLCONF = 'app_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = 'app_django.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    # https://florimondmanca.github.io/djangorestframework-api-key/guide/
    # https://florimondmanca.github.io/djangorestframework-api-key/guide/#setting-permissions
    # https://www.django-rest-framework.org/api-guide/permissions/
    # "DEFAULT_PERMISSION_CLASSES": [
    #     "rest_framework_api_key.permissions.HasAPIKey",
    # ]
    'DATETIME_FORMAT': "%Y-%m-%d %H:%M",  # YYYY-MM-DD hh:mm
}
# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("MYSQL_DATABASE"),
        'USER': os.getenv("MYSQL_USER"),
        'PASSWORD': os.getenv("MYSQL_PASSWORD"),
        'HOST': os.getenv("DB_NAME"),
        'PORT': 3306,
        'OPTIONS': {'charset': 'utf8'},
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# https://docs.djangoproject.com/en/2.2/ref/settings/#datetime-input-formats
# from django.conf.global_settings import DATETIME_INPUT_FORMATS

AUTH_USER_MODEL = 'red_cards.User'


SSO_UNTI_URL = os.getenv("SSO_UNTI_URL")

SOCIAL_AUTH_UNTI_KEY = os.getenv("SOCIAL_AUTH_UNTI_KEY")
SOCIAL_AUTH_UNTI_SECRET = os.getenv("SOCIAL_AUTH_UNTI_SECRET")

AUTHENTICATION_BACKENDS = (
    'app_django.auth.UNTIBackend',
    'django.contrib.auth.backends.ModelBackend',
)
# название тега, по которому приложение понимает, что пользователь ассистент
ASSISTANT_TAGS_NAME = ['assistant', 'island_assistant']

