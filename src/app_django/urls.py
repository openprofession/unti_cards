"""app_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import permission_required

from app_django import settings
from app_django.routers import router
from rest_framework.documentation import include_docs_urls

from red_cards import views

urlpatterns = []
if settings.DEBUG:
    # without collect static
    urlpatterns += staticfiles_urlpatterns()
#

urlpatterns += [
                  path('', include('social_django.urls', namespace='social')),
                  path('logout/', views.logout, name='logout'),
                  path('admin/', admin.site.urls),
                  path('api-auth/', include('rest_framework.urls')),
                  path('api-docs/', include_docs_urls(title='DRF: API-docs')),
                  path('api/', include(router.urls)),
                  path('manage/load_events/<date_txt>', views.api_test),
                  path('manage/load_enrolls', views.api_test2),
                  path('', views.home, name='home'),
                  path(
                      'card/add/<str:leader_id>',
                      views.AddCardAdminFormView.as_view(),
                      name='card-add'
                  ),
                  path('appeals/add',
                       views.AppealsFormView.as_view(),
                       name='appeals-add'),
                  path('appeals/add/success',
                       views.SuccessAppealsFormView.as_view(),
                       name='appeals-add-success'),
                  path('appeals',
                       views.AppealListView.as_view(),
                       name='appeals-list'),
                  path('appeals/<str:pk>',
                       views.AppealDetailAdminView.as_view(),
                       name='appeals-detail-admin'),

                  path('users/search',
                       views.SearchView.as_view(),
                       name='users-search'),


              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
