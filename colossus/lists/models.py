import uuid

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.subscribers import constants as subscribers_constants


class MailingList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
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

    def get_active_subscribers(self):
        return self.subscribers.filter(status=subscribers_constants.SUBSCRIBED)
