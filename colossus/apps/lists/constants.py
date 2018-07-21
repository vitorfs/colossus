from django.utils.translation import gettext_lazy as _


class ImportTypes:
    BASIC = 1
    ADVANCED = 2

    LABELS = {
        BASIC: _('Basic'),
        ADVANCED: _('Advanced'),
    }

    CHOICES = tuple(LABELS.items())


class ImportStatus:
    PENDING = 1
    COMPLETED = 2
    ERRORED = 3
    CANCELED = 4

    LABELS = {
        PENDING: _('Pending'),
        COMPLETED: _('Completed'),
        ERRORED: _('Errored'),
        CANCELED: _('Canceled'),
    }

    CHOICES = tuple(LABELS.items())
