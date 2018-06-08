from django.urls import path

from . import views


app_name = 'emailtemplates'


urlpatterns = [
    path('', views.EmailTemplateListView.as_view(), name='emailtemplates'),
    path('add/', views.EmailTemplateCreateView.as_view(), name='emailtemplate_add'),
    path('<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='emailtemplate_edit')
]
