from django.utils.translation import gettext_lazy as _


REGULAR = 1
AUTOMATED = 2
AB_TEST = 3

CAMPAIGN_TYPE_LABELS = {
    REGULAR: _('Regular'),
    AUTOMATED: _('Automated'),
    AB_TEST: _('A/B Test'),
}

CAMPAIGN_TYPE_CHOICES = tuple(CAMPAIGN_TYPE_LABELS.items())


SENT = 1
SCHEDULED = 2
DRAFT = 3
TRASH = 4

STATUS_LABELS = {
    SENT: _('Sent'),
    SCHEDULED: _('Scheduled'),
    DRAFT: _('Draft'),
    TRASH: _('Trashed'),
}

STATUS_CHOICES = tuple(STATUS_LABELS.items())
