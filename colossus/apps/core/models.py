from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


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
        db_table = 'colossus_tokens'


class Option(models.Model):
    key = models.CharField(_('key'), max_length=50, unique=True)
    value = models.TextField(_('value'), blank=True)

    class Meta:
        verbose_name = _('option')
        verbose_name_plural = _('options')
        db_table = 'colossus_options'

    def __str__(self):
        if len(self.value) > 30:
            value = '%s...' % self.value[:30]
        else:
            value = self.value
        return '%s=%s' % (self.key, value)


class Country(models.Model):
    code = models.CharField(_('country code'), max_length=2, unique=True)
    name = models.CharField(_('name'), max_length=200)

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')
        db_table = 'colossus_countries'

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('country'),
        related_name='cities'
    )
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
        db_table = 'colossus_cities'

    def __str__(self):
        return self.name
