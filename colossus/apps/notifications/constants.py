from django.utils.translation import gettext_lazy as _


class Actions:
    IMPORT_COMPLETED = 1
    IMPORT_ERRORED = 2
    CAMPAIGN_SENT = 3

    LABELS = {
        IMPORT_COMPLETED: _('Subscribers import completed'),
        IMPORT_ERRORED: _('Subscribers import failed'),
        CAMPAIGN_SENT: _('Campaign sent')
    }

    CHOICES = tuple(LABELS.items())
