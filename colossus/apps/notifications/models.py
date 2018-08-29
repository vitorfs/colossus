import json

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.renderers import (
    render_campaign_sent, render_import_completed, render_import_errored,
    render_list_cleaned,
)

User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('user'), related_name='notifications')
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name=_('content type'),
        blank=True,
        null=True
    )
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey()
    action = models.PositiveSmallIntegerField(_('action'), choices=Actions.CHOICES)
    text = models.TextField(_('text'), blank=True)
    date = models.DateTimeField(_('date'), auto_now_add=True)
    is_seen = models.BooleanField(_('seen status'), default=False)
    is_read = models.BooleanField(_('read status'), default=False)

    __data = None

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        db_table = 'colossus_notifications'

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('notifications:notification_detail', kwargs={'pk': self.pk})

    @property
    def data(self):
        if self.__data is None:
            self.__data = json.loads(self.text)
        return self.__data

    def render(self):
        renderers = {
            Actions.IMPORT_COMPLETED: render_import_completed,
            Actions.IMPORT_ERRORED: render_import_errored,
            Actions.CAMPAIGN_SENT: render_campaign_sent,
            Actions.LIST_CLEANED: render_list_cleaned
        }
        renderer_function = renderers[self.action]
        return renderer_function(self)
