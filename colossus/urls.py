from django.conf import settings
from django.urls import path, include


urlpatterns = [
    path('', include('colossus.subscribers.urls', namespace='subscribers')),
    path('accounts/', include(('django.contrib.auth.urls', 'auth'), namespace='accounts')),
    path('lists/', include('colossus.lists.urls', namespace='lists')),
    path('templates/', include('colossus.emailtemplates.urls', namespace='templates')),
    path('campaigns/', include('colossus.campaigns.urls', namespace='campaigns')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
