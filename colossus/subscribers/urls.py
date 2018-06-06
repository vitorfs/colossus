from django.urls import path, include

from . import views


app_name = 'subscribers'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('subscribe/<uuid:mailing_list_uuid>/', views.subscribe, name='subscribe'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/', views.confirm_subscription, name='confirm_subscription'),
    path('subscribe/<uuid:mailing_list_uuid>/confirm/<str:token>/', views.confirm_double_optin_token, name='confirm_double_optin_token'),
    #path('unsubscribe/<uuid:mailing_list_uuid>/<uuid:subscriber_uuid>/', views.SubscribeView.as_view(), name='unsubscribe'),
    #path('profile/<uuid:mailing_list_uuid>/<uuid:subscriber_uuid>/', views.SubscribeView.as_view(), name='profile'),
    #path('track/click/', views.SubscribeView.as_view(), name='click'),
    path('track/open/', views.track_open, name='open'),
]
