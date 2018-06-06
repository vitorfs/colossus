from django.utils.translation import gettext_lazy as _

PENDING = 1
SUBSCRIBED = 2
UNSUBSCRIBED = 3
CLEANED = 4

STATUS_LABELS = {
    PENDING: _('Pending'),
    SUBSCRIBED: _('Subscribed'),
    UNSUBSCRIBED: _('Unsubscribed'),
    CLEANED: _('Cleaned'),
}

STATUS_CHOICES = tuple(STATUS_LABELS.items())
