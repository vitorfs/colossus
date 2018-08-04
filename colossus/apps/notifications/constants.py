from django.utils.translation import gettext_lazy as _


class Actions:
    IMPORT_COMPLETED = 1
    CAMPAIGN_SENT = 2

    LABELS = {
        IMPORT_COMPLETED: _('Subscribers import completed'),
        CAMPAIGN_SENT: _('Campaign sent')
    }

    CHOICES = tuple(LABELS.items())
