from django.utils.translation import gettext_lazy as _


class CampaignTypes:
    REGULAR = 1
    AUTOMATED = 2
    AB_TEST = 3

    LABELS = {
        REGULAR: _('Regular'),
        AUTOMATED: _('Automated'),
        AB_TEST: _('A/B Test'),
    }

    CHOICES = tuple(LABELS.items())


class CampaignStatus:
    SENT = 1
    SCHEDULED = 2
    DRAFT = 3
    TRASH = 4

    LABELS = {
        SENT: _('Sent'),
        SCHEDULED: _('Scheduled'),
        DRAFT: _('Draft'),
        TRASH: _('Trashed'),
    }

    CHOICES = tuple(LABELS.items())
