from django.urls import path, include

from . import views


app_name = 'mailing'


urlpatterns = [
    path('', views.MailingListListView.as_view(), name='lists'),
    path('new/', views.MailingListCreateView.as_view(), name='new_list'),

    path('<int:pk>/', include([
        path('', views.MailingListDetailView.as_view(), name='list'),
        path('subscribers/', views.SubscriberListView.as_view(), name='subscribers'),
    ])),
]
