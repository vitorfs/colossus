from django.urls import path

from . import views

app_name = 'templates'


urlpatterns = [
    path('', views.EmailTemplateListView.as_view(), name='emailtemplates'),
    path('add/', views.EmailTemplateCreateView.as_view(), name='emailtemplate_add'),
    path('<int:pk>/', views.email_template_editor, name='emailtemplate_editor'),
    path('<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='emailtemplate_edit'),
    path('<int:pk>/preview/', views.email_template_preview, name='emailtemplate_preview'),
    path('<int:pk>/autosave/', views.email_template_autosave, name='emailtemplate_autosave'),
    path('<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='emailtemplate_delete')
]
