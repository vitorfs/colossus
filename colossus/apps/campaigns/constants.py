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
    QUEUED = 4
    DELIVERING = 5
    PAUSED = 6

    FILTERS = {SENT, SCHEDULED, DRAFT}

    ICONS = {
        SENT: 'fas fa-check',
        SCHEDULED: 'far fa-calendar',
        DRAFT: 'fas fa-pencil-alt'
    }

    LABELS = {
        SENT: _('Sent'),
        SCHEDULED: _('Scheduled'),
        DRAFT: _('Draft'),
        QUEUED: _('Queued'),
        DELIVERING: _('Delivering'),
        PAUSED: _('Paused'),
    }

    CHOICES = tuple(LABELS.items())
