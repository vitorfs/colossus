from django.urls import path, include

from . import views


app_name = 'subscribers'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('goodbye/', views.goodbye, name='goodbye'),
    path('subscribe/<uuid:mailing_list_uuid>/', views.subscribe, name='subscribe'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/', views.confirm_subscription, name='confirm_subscription'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/<str:token>/', views.confirm_double_optin_token, name='confirm_double_optin_token'),
    path('unsubscribe/<uuid:mailing_list_uuid>/', views.unsubscribe_manual, name='unsubscribe_manual'),
    path('unsubscribe/<uuid:mailing_list_uuid>/s/<uuid:subscriber_uuid>/c/<uuid:campaign_uuid>/', views.unsubscribe, name='unsubscribe'),
    path('track/click/e/<uuid:email_uuid>/l/<uuid:link_uuid>/s/<uuid:subscriber_uuid>/', views.track_click, name='click'),
    path('track/open/e/<uuid:email_uuid>/s/<uuid:subscriber_uuid>/', views.track_open, name='open'),
]
