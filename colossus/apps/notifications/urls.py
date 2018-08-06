from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications, name='notifications'),
]
