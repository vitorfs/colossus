# flake8: noqa

from django.urls import path

from . import views

app_name = 'mailing'


urlpatterns = [
    path('', views.MailingListListView.as_view(), name='lists'),
    path('add/', views.MailingListCreateView.as_view(), name='new_list'),
    path('<int:pk>/', views.MailingListDetailView.as_view(), name='list'),
    path('<int:pk>/locations/<str:country_code>/', views.MailingListCountryReportView.as_view(), name='country_report'),
    path('<int:pk>/subscribers/', views.SubscriberListView.as_view(), name='subscribers'),
    path('<int:pk>/subscribers/add/', views.SubscriberCreateView.as_view(), name='new_subscriber'),
    path('<int:pk>/subscribers/import/', views.ImportSubscribersView.as_view(), name='import_subscribers'),
    path('<int:pk>/subscribers/import/csv/', views.SubscriberImportView.as_view(), name='csv_import_subscribers'),
    path('<int:pk>/subscribers/import/csv/<int:import_pk>/', views.SubscriberImportPreviewView.as_view(), name='import_preview'),
    path('<int:pk>/subscribers/import/csv/<int:import_pk>/queued/', views.SubscriberImportQueuedView.as_view(), name='import_queued'),
    path('<int:pk>/subscribers/import/csv/<int:import_pk>/download/', views.download_subscriber_import, name='download_subscriber_import'),
    path('<int:pk>/subscribers/import/csv/<int:import_pk>/delete/', views.SubscriberImportDeleteView.as_view(), name='delete_subscriber_import'),
    path('<int:pk>/subscribers/import/paste/', views.PasteEmailsImportSubscribersView.as_view(), name='paste_import_subscribers'),
    path('<int:pk>/subscribers/<int:subscriber_pk>/', views.SubscriberDetailView.as_view(), name='subscriber'),
    path('<int:pk>/subscribers/<int:subscriber_pk>/edit/', views.SubscriberUpdateView.as_view(), name='edit_subscriber'),
    path('<int:pk>/subscribers/<int:subscriber_pk>/delete/', views.SubscriberDeleteView.as_view(), name='delete_subscriber'),

    path('<int:pk>/tags/', views.TagListView.as_view(), name='tags'),
    path('<int:pk>/tags/add/', views.TagCreateView.as_view(), name='new_tag'),
    path('<int:pk>/tags/bulk-tag/', views.BulkTagSubscribersView.as_view(), name='bulk_tag'),
    path('<int:pk>/tags/<int:tag_pk>/edit/', views.TagUpdateView.as_view(), name='edit_tag'),
    path('<int:pk>/tags/<int:tag_pk>/delete/', views.TagDeleteView.as_view(), name='delete_tag'),

    path('<int:pk>/forms/', views.SubscriptionFormsView.as_view(), name='subscription_forms'),
    path('<int:pk>/forms/editor/', views.FormsEditorView.as_view(), name='forms_editor'),
    path('<int:pk>/forms/editor/design/', views.CustomizeDesignView.as_view(), name='customize_design'),
    path('<int:pk>/forms/editor/<str:form_key>/', views.SubscriptionFormTemplateUpdateView.as_view(), name='edit_form_template'),
    path('<int:pk>/forms/editor/<str:form_key>/preview/', views.PreviewFormTemplateView.as_view(), name='preview_form_template'),
    path('<int:pk>/forms/editor/<str:form_key>/reset/', views.ResetFormTemplateView.as_view(), name='reset_form_template'),
    path('<int:pk>/settings/', views.ListSettingsView.as_view(), name='settings'),
    path('<int:pk>/settings/subscription/', views.SubscriptionSettingsView.as_view(), name='subscription_settings'),
    path('<int:pk>/settings/defaults/', views.CampaignDefaultsView.as_view(), name='defaults'),
    path('<int:pk>/settings/smtp/', views.SMTPCredentialsView.as_view(), name='smtp'),
    path('<int:pk>/charts/subscriptions/', views.SubscriptionsSummaryChartView.as_view(), name='charts_subscriptions_summary'),
    path('<int:pk>/charts/domains/', views.ListDomainsChartView.as_view(), name='charts_list_domains'),
    path('<int:pk>/charts/locations/', views.ListLocationsChartView.as_view(), name='charts_list_locations'),
]
