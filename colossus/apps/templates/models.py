from django.db import models
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from .utils import wrap_blocks


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
    last_used_campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('last used campaign'),
        related_name='+'
    )

    objects = EmailTemplateManager()

    class Meta:
        verbose_name = _('email template')
        verbose_name_plural = _('email templates')
        db_table = 'colossus_email_templates'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and not self.content:
            self.content = self.__class__.objects.default_content()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('templates:emailtemplate_editor', kwargs={'pk': self.pk})

    def html_preview(self):
        html = wrap_blocks(self.content)
        return mark_safe(html)
