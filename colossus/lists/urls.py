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
            path('<int:subscriber_pk>/edit/', views.SubscriberUpdateView.as_view(), name='edit_subscriber'),
            path('<int:subscriber_pk>/delete/', views.SubscriberDeleteView.as_view(), name='delete_subscriber')
        ])),
        path('forms/', include([
            path('', views.SubscriptionFormsView.as_view(), name='subscription_forms'),
            path('editor/', views.FormsEditorView.as_view(), name='forms_editor'),
        ])),
        path('settings/', views.MailingListSettingsView.as_view(), name='settings'),
        path('charts/subscriptions-summary/', views.charts_subscriptions_summary, name='charts_subscriptions_summary')
    ])),
]
