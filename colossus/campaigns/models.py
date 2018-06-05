from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.lists.models import MailingList


class Campaign(models.Model):
    REGULAR = 1
    AUTOMATED = 2
    CAMPAIGN_TYPE_CHOICES = (
        (REGULAR, _('Regular')),
        (AUTOMATED, _('Automated')),
    )

    SENT = 1
    SCHEDULED = 2
    DRAFT = 3
    TRASH = 4
    STATUS_CHOICES = (
        (SENT, _('Sent')),
        (SCHEDULED, _('Scheduled')),
        (DRAFT, _('Draft')),
        (TRASH, _('Trashed')),
    )

    name = models.CharField(_('name'), max_length=100)
    campaign_type = models.PositiveSmallIntegerField(_('type'), choices=CAMPAIGN_TYPE_CHOICES, default=REGULAR)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='campaigns',
        null=True,
        blank=True
    )
    status = models.PositiveSmallIntegerField(_('status'), choices=STATUS_CHOICES, default=DRAFT)

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.status in (Campaign.DRAFT, Campaign.SCHEDULED):
            return reverse('campaigns:campaign_edit', kwargs={'pk': self.pk})
        return reverse('campaigns:campaign_detail', kwargs={'pk': self.pk})

