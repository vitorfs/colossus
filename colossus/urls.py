from django.conf import settings
from django.urls import include, path

from colossus.apps.core import views as core_views

urlpatterns = [
    path('', include('colossus.apps.subscribers.urls', namespace='subscribers')),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('settings/', core_views.SiteUpdateView.as_view(), name='settings'),
    path('accounts/', include(('django.contrib.auth.urls', 'auth'), namespace='accounts')),
    path('lists/', include('colossus.apps.lists.urls', namespace='lists')),
    path('templates/', include('colossus.apps.emailtemplates.urls', namespace='templates')),
    path('campaigns/', include('colossus.apps.campaigns.urls', namespace='campaigns')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
