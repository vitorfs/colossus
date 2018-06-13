import uuid

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.subscribers import constants as subscribers_constants


class MailingList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    subscribers_count = models.PositiveIntegerField(_('subscribers'), default=0)
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    date_created = models.DateTimeField(_('created'), auto_now_add=True)
    contact_email_address = models.EmailField(_('contact email address'), blank=True)
    website_url = models.URLField(_('website URL'), blank=True, help_text=_('Where did people opt in to this list?'))
    campaign_default_from_name = models.CharField(_('default from name'), max_length=100, blank=True)
    campaign_default_from_email = models.EmailField(_('default from email address'), blank=True)
    campaign_default_email_subject = models.CharField(_('default subject'), max_length=150, blank=True)
    enable_recaptcha = models.BooleanField(_('enable reCAPTCHA'), default=False)

    class Meta:
        verbose_name = _('list')
        verbose_name_plural = _('lists')
        db_table = 'mailing_lists'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mailing:list', kwargs={'pk': self.pk})

    def get_active_subscribers(self):
        return self.subscribers.filter(status=subscribers_constants.SUBSCRIBED)

    def update_subscribers_count(self):
        self.subscribers_count = self.get_active_subscribers().count()
        self.save()
