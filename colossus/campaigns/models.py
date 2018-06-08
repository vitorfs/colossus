import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.utils import timezone

from colossus.lists.models import MailingList

from . import constants
from .markup import get_template_variables


class Campaign(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(_('name'), max_length=100)
    campaign_type = models.PositiveSmallIntegerField(
        _('type'),
        choices=constants.CAMPAIGN_TYPE_CHOICES,
        default=constants.REGULAR
    )
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='campaigns',
        null=True,
        blank=True
    )
    status = models.PositiveSmallIntegerField(_('status'), choices=constants.STATUS_CHOICES, default=constants.DRAFT)
    send_date = models.DateTimeField(_('send date'), null=True, blank=True)
    create_date = models.DateTimeField(_('create date'), auto_now_add=True)
    update_date = models.DateTimeField(_('update date'), default=timezone.now)

    __cached_email = None

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.status in (constants.DRAFT, constants.SCHEDULED):
            return reverse('campaigns:campaign_edit', kwargs={'pk': self.pk})
        return reverse('campaigns:campaign_detail', kwargs={'pk': self.pk})

    @property
    def email(self):
        if not self.__cached_email and self.campaign_type == constants.REGULAR:
            try:
                self.__cached_email, created = Email.objects.get_or_create(campaign=self)
            except Email.MultipleObjectsReturned:
                self.__cached_email = self.emails.order_by('id').first()
        return self.__cached_email


class Email(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name=_('campaign'), related_name='emails')
    from_email = models.EmailField(_('email address'))
    from_name = models.CharField(_('name'), max_length=100, blank=True)
    subject = models.CharField(_('subject'), max_length=150)
    preview = models.CharField(_('preview'), max_length=150, blank=True)
    content = models.TextField(_('content'))
    content_text = models.TextField(_('content'))

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')

    def __str__(self):
        return self.subject

    def get_from(self):
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email

    def checklist(self):
        _checklist = {
            'recipients': False,
            'from': False,
            'subject': False,
            'unsub': False,
            'plaintext': False
        }
        if self.content:
            html_template = Template(self.content)
            html_variables = get_template_variables(html_template)
            text_template = Template(self.content_text)
            text_variables = get_template_variables(text_template)

            _checklist['unsub'] = ('unsub' in html_variables and 'unsub' in text_variables)
            _checklist['plaintext'] = (self.content_text != '')
        return _checklist

    def _render(self, template, subscriber):
        t = Template(template)
        if subscriber is not None:
            context = {
                'name': subscriber.name,
                'unsub': reverse('subscribers:unsubscribe', kwargs={
                    'mailing_list_uuid': self.campaign.mailing_list.uuid,
                    'subscriber_uuid': subscriber.uuid,
                    'campaign_uuid': self.campaign.uuid
                })
            }
        else:
            # If subscriber is None, consider it as test data
            context = {
                'name': '<< Test Name >>',
                'unsub': 'http://127.0.0.1:8000/'
            }
        c = Context(context)
        return t.render(c)

    def render_html(self, subscriber):
        return self._render(self.content, subscriber)

    def render_text(self, subscriber):
        return self._render(self.content_text, subscriber)


class Link(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('link')
        verbose_name_plural = _('links')

    def __str__(self):
        return self.url
