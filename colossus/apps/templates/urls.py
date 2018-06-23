from django.urls import path

from . import views

app_name = 'templates'


urlpatterns = [
    path('', views.EmailTemplateListView.as_view(), name='emailtemplates'),
    path('add/', views.EmailTemplateCreateView.as_view(), name='emailtemplate_add'),
    path('<int:pk>/', views.EmailTemplateEditorView.as_view(), name='emailtemplate_editor'),
    path('<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='emailtemplate_edit'),
    path('<int:pk>/preview/', views.preview_email_template, name='emailtemplate_preview'),
    path('<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='emailtemplate_delete')
]
