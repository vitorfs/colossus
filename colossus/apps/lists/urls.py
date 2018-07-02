from django.urls import include, path

from . import views

app_name = 'mailing'


urlpatterns = [
    path('', views.MailingListListView.as_view(), name='lists'),
    path('add/', views.MailingListCreateView.as_view(), name='new_list'),
    path('<int:pk>/', include([
        path('', views.MailingListDetailView.as_view(), name='list'),
        path('subscribers/', include([
            path('', views.SubscriberListView.as_view(), name='subscribers'),
            path('add/', views.SubscriberCreateView.as_view(), name='new_subscriber'),

            path('import/', views.ImportSubscribersView.as_view(), name='import_subscribers'),
            path('import/csv/', views.SubscriberImportView.as_view(), name='csv_import_subscribers'),
            path('import/csv/<int:import_pk>/', views.ColumnsMappingView.as_view(), name='columns_mapping'),
            path('import/csv/<int:import_pk>/download/', views.download_subscriber_import, name='download_subscriber_import'),
            path('import/paste/', views.PasteEmailsImportSubscribersView.as_view(), name='paste_import_subscribers'),

            path('<int:subscriber_pk>/edit/', views.SubscriberUpdateView.as_view(), name='edit_subscriber'),
            path('<int:subscriber_pk>/delete/', views.SubscriberDeleteView.as_view(), name='delete_subscriber')
        ])),
        path('forms/', include([
            path('', views.SubscriptionFormsView.as_view(), name='subscription_forms'),
            path('editor/', views.FormsEditorView.as_view(), name='forms_editor'),
            path('editor/design/', views.CustomizeDesignView.as_view(), name='customize_design'),
            path('editor/<str:form_key>/', views.SubscriptionFormTemplateUpdateView.as_view(), name='edit_form_template'),  # noqa
            path('editor/<str:form_key>/preview/', views.PreviewFormTemplateView.as_view(), name='preview_form_template'),  # noqa
        ])),
        path('settings/', include([
            path('', views.ListSettingsView.as_view(), name='settings'),
            path('subscription/', views.SubscriptionSettingsView.as_view(), name='subscription_settings'),
            path('defaults/', views.CampaignDefaultsView.as_view(), name='defaults'),
            path('smtp/', views.SMTPCredentialsView.as_view(), name='smtp'),
        ])),
        path('charts/subscriptions-summary/', views.charts_subscriptions_summary, name='charts_subscriptions_summary')
    ])),
]
