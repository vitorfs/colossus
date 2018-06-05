from django.urls import path, include

from . import views


app_name = 'campaigns'


urlpatterns = [
    path('', views.CampaignListView.as_view(), name='campaigns'),
]