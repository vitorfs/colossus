from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('user'), related_name='notifications')
    text = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        db_table = 'colossus_notifications'

    def __str__(self):
        return self.text
