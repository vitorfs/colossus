from django.urls import include, path

app_name = 'api'

urlpatterns = [
    path('auth/', include('rest_framework.urls')),
    path('lists/', include('colossus.apps.lists.api.urls')),
]
