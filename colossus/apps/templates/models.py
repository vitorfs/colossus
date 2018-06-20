from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.loader import get_template


class EmailTemplateManager(models.Manager):
    @classmethod
    def default_content(cls):
        default_content = get_template('templates/default_email_template_content.html')
        content = default_content.template.source
        return content


class EmailTemplate(models.Model):
    name = models.CharField(_('name'), max_length=100)
    content = models.TextField(blank=True)
    create_date = models.DateTimeField(_('create date'), auto_now_add=True)
    update_date = models.DateTimeField(_('update date'), default=timezone.now)
    last_used_date = models.DateTimeField(_('last used'), null=True, blank=True)

    objects = EmailTemplateManager()

    class Meta:
        verbose_name = _('email template')
        verbose_name_plural = _('email templates')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and not self.content:
            self.content = self.__class__.objects.default_content()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('templates:emailtemplate_editor', kwargs={'pk': self.pk})
