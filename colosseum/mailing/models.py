import uuid

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class MailingList(models.Model):
    name = models.CharField(_('name'), max_length=100)
    subscribers_count = models.PositiveIntegerField(_('subscribers'), default=0)
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    date_created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('list')
        verbose_name_plural = _('lists')
        db_table = 'mailing_lists'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mailing:list', kwargs={'pk': self.pk})


class Subscriber(models.Model):
    PENDING = 1
    SUBSCRIBED = 2
    UNSUBSCRIBED = 3
    CLEANED = 4
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (SUBSCRIBED, 'Subscribed'),
        (UNSUBSCRIBED, 'Unsubscribed'),
        (CLEANED, 'Cleaned'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(_('email address'), max_length=255)
    name = models.CharField(_('name'), max_length=150, blank=True)
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    date_subscribed = models.DateTimeField(_('subscribed'), null=True, blank=True)
    date_updated = models.DateTimeField(_('updated'), auto_now=True)
    date_created = models.DateTimeField(_('created'), auto_now_add=True)
    status = models.PositiveSmallIntegerField(_('status'), default=PENDING, choices=STATUS_CHOICES)
    optin_ip_address = models.GenericIPAddressField(_('opt-in IP address'), unpack_ipv4=True, blank=True, null=True)
    confirm_ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.PROTECT, related_name='subscribers')

    class Meta:
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')

    def __str__(self):
        return self.email


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
