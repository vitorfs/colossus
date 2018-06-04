from django.urls import path, include

from . import views


app_name = 'mailing'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('unsubscribe/<uuid:mailing_list_uuid>/<uuid:subscriber_uuid>/', views.SubscribeView.as_view(), name='unsubscribe'),
    path('profile/<uuid:mailing_list_uuid>/<uuid:subscriber_uuid>/', views.SubscribeView.as_view(), name='profile'),
    path('track/click/', views.SubscribeView.as_view(), name='click'),
    path('track/open/', views.SubscribeView.as_view(), name='open'),
]
