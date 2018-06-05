from django.db import models
from django.utils.translation import gettext_lazy as _

from colossus.lists.models import MailingList


class Campaign(models.Model):
    REGULAR = 1
    AUTOMATED = 2
    CAMPAIGN_TYPE_CHOICES = (
        (REGULAR, _('Regular')),
        (AUTOMATED, _('Automated')),
    )
    name = models.CharField(_('name'), max_length=100)
    campaign_type = models.PositiveSmallIntegerField(_('type'), choices=CAMPAIGN_TYPE_CHOICES, default=REGULAR)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='campaigns'
    )

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')

    def __str__(self):
        return self.name
