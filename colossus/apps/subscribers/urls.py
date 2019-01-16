from django.urls import path

from . import views

app_name = 'subscribers'


urlpatterns = [
    path('manage/', views.manage, name='manage'),
    path('goodbye/<uuid:mailing_list_uuid>/', views.goodbye, name='goodbye'),
    path('subscribe/<uuid:mailing_list_uuid>/', views.subscribe, name='subscribe'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/', views.confirm_subscription, name='confirm_subscription'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/<str:token>/', views.confirm_double_optin_token, name='confirm_double_optin_token'),  # noqa
    path('unsubscribe/<uuid:mailing_list_uuid>/', views.unsubscribe_manual, name='unsubscribe_manual'),
    path('unsubscribe/<uuid:mailing_list_uuid>/<uuid:subscriber_uuid>/<uuid:campaign_uuid>/', views.unsubscribe, name='unsubscribe'),  # noqa
    path('track/open/<uuid:email_uuid>/<uuid:subscriber_uuid>/', views.track_open, name='open'),
    path('track/click/<uuid:link_uuid>/<uuid:subscriber_uuid>/', views.track_click, name='click'),
]
