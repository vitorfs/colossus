from django.urls import path, include

from . import views


app_name = 'campaigns'


urlpatterns = [
    path('', views.CampaignListView.as_view(), name='campaigns'),
    path('add/', views.CampaignCreateView.as_view(), name='campaign_add'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('<int:pk>/edit/', views.CampaignEditView.as_view(), name='campaign_edit'),
    path('<int:pk>/edit/recipients/', views.CampaignEditRecipientsView.as_view(), name='campaign_edit_recipients'),
    path('<int:pk>/edit/from/', views.CampaignEditFromView.as_view(), name='campaign_edit_from'),
]