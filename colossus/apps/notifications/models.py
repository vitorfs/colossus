from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from colossus.apps.notifications.api import render_list_cleaned
from colossus.apps.notifications.constants import Actions

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

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        db_table = 'colossus_notifications'

    def __str__(self):
        return self.text

    def render(self):
        renderers = {
            Actions.IMPORT_COMPLETED: lambda n: n.text,
            Actions.IMPORT_ERRORED: lambda n: n.text,
            Actions.CAMPAIGN_SENT: lambda n: n.text,
            Actions.LIST_CLEANED: render_list_cleaned
        }
        renderer_function = renderers[self.action]
        return renderer_function(self)
