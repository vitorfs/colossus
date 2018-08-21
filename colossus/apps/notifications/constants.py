from django.utils.translation import gettext_lazy as _


class Actions:
    IMPORT_COMPLETED = 1
    IMPORT_ERRORED = 2
    CAMPAIGN_SENT = 3

    ITEMS = {
        IMPORT_COMPLETED: {
            'label': _('Subscribers import completed'),
            'icon': 'fas fa-user-check',
            'message': _('Subscribers import completed with success!'),
        },
        IMPORT_ERRORED: {
            'label': _('Subscribers import failed'),
            'icon': 'fas fa-user-times',
        },
        CAMPAIGN_SENT: {
            'label': _('Campaign sent'),
            'icon': 'fas fa-paper-plane'
        }
    }

    CHOICES = tuple([(key, options['label']) for key, options in ITEMS.items()])
