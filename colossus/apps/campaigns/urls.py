from django.urls import path

from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='campaigns'),
    path('add/', views.CampaignCreateView.as_view(), name='campaign_add'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('<int:pk>/revert-draft/', views.CampaignRevertDraftView.as_view(), name='campaign_revert_draft'),
    path('<int:pk>/scheduled/', views.CampaignScheduledView.as_view(), name='campaign_scheduled'),
    path('<int:pk>/preview/', views.CampaignPreviewView.as_view(), name='campaign_preview'),
    path('<int:pk>/reports/', views.CampaignReportsView.as_view(), name='campaign_reports'),
    path('<int:pk>/reports/locations/', views.CampaignReportsLocationsView.as_view(),
         name='campaign_reports_locations'),
    path('<int:pk>/reports/locations/<str:country_code>/', views.CampaignReportsCountryView.as_view(),
         name='campaign_reports_country'),
    path('<int:pk>/links/', views.CampaignLinksView.as_view(), name='campaign_links'),
    path('<int:pk>/links/<int:link_pk>/edit/', views.LinkUpdateView.as_view(), name='edit_link'),
    path('<int:pk>/edit/', views.CampaignEditView.as_view(), name='campaign_edit'),
    path('<int:pk>/edit/name/', views.CampaignEditNameView.as_view(), name='campaign_edit_name'),
    path('<int:pk>/edit/recipients/', views.CampaignEditRecipientsView.as_view(), name='campaign_edit_recipients'),
    path('<int:pk>/edit/from/', views.CampaignEditFromView.as_view(), name='campaign_edit_from'),
    path('<int:pk>/edit/subject/', views.CampaignEditSubjectView.as_view(), name='campaign_edit_subject'),
    path('<int:pk>/edit/content/', views.campaign_edit_content, name='campaign_edit_content'),
    path('<int:pk>/edit/content/template/', views.CampaignEditTemplateView.as_view(), name='campaign_edit_template'),
    path('<int:pk>/edit/test-email/', views.campaign_test_email, name='campaign_test_email'),
    path('<int:pk>/preview-email/', views.campaign_preview_email, name='campaign_preview_email'),
    path('<int:pk>/send/', views.send_campaign, name='send_campaign'),
    path('<int:pk>/send/done/', views.SendCampaignCompleteView.as_view(), name='send_campaign_complete'),
    path('<int:pk>/replicate/', views.replicate_campaign, name='replicate_campaign'),
    path('<int:pk>/delete/', views.CampaignDeleteView.as_view(), name='delete_campaign'),
    path('<int:pk>/schedule/', views.ScheduleCampaignView.as_view(), name='schedule_campaign'),

    path('ajax/load-list-tags/', views.load_list_tags, name='load_list_tags'),
]
