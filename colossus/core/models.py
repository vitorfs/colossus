from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string


def default_token():
    return get_random_string(50)


class Token(models.Model):
    text = models.CharField(default=default_token, max_length=50, unique=True, editable=False)
    description = models.CharField(max_length=30, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_used = models.DateTimeField(null=True, blank=True)
    expires = models.IntegerField(default=7)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey()

    class Meta:
        verbose_name = _('token')
        verbose_name_plural = _('tokens')


class Option(models.Model):
    key = models.CharField(_('key'), max_length=50, unique=True)
    value = models.TextField(_('value'), blank=True)

    class Meta:
        verbose_name = _('option')
        verbose_name_plural = _('options')

    def __str__(self):
        if len(self.value) > 30:
            value = '%s...' % self.value[:30]
        else:
            value = self.value
        return '%s=%s' % (self.key, value)
