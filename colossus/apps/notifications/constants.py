from django.utils.translation import gettext_lazy as _


class Actions:
    IMPORT_COMPLETED = 1
    IMPORT_ERRORED = 2
    CAMPAIGN_SENT = 3
    LIST_CLEANED = 4

    ITEMS = {
        IMPORT_COMPLETED: {
            'label': _('Subscribers import completed'),
            'icon': 'fas fa-user-check',
        },
        IMPORT_ERRORED: {
            'label': _('Subscribers import failed'),
            'icon': 'fas fa-user-times',
        },
        CAMPAIGN_SENT: {
            'label': _('Campaign sent'),
            'icon': 'fas fa-paper-plane'
        },
        LIST_CLEANED: {
            'label': _('List cleaned'),
            'icon': 'fas fa-broom'
        }
    }

    CHOICES = tuple([(key, options['label']) for key, options in ITEMS.items()])
