from django.urls import path, include


urlpatterns = [
    path('accounts/', include(('django.contrib.auth.urls', 'auth'), namespace='accounts')),
    path('mailing/', include('colosseum.mailing.urls', namespace='mailing')),
]
