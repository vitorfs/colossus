import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.crypto import get_random_string


def default_token():
    return get_random_string(50)


class Token(models.Model):
    EXPIRE = {
        '5MIN': 5 * 60,
        '7DAYS': 7 * 24 * 60 * 60
    }
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
