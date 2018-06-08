from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class EmailTemplate(models.Model):
    name = models.CharField(_('name'), max_length=100)
    content = models.TextField(blank=True)
    create_date = models.DateTimeField(_('create date'), auto_now_add=True)
    update_date = models.DateTimeField(_('update date'), default=timezone.now)

    class Meta:
        verbose_name = _('email template')
        verbose_name_plural = _('email templates')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('templates:emailtemplate_edit', kwargs={'pk': self.pk})
