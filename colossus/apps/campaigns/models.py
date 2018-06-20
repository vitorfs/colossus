import uuid
import json

from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bs4 import BeautifulSoup

from colossus.apps.lists.models import MailingList
from colossus.apps.templates.models import EmailTemplate

from . import constants
from .markup import get_template_variables, get_template_blocks
from .tasks import send_campaign_task


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
    recipients_count = models.PositiveIntegerField(default=0)
    track_opens = models.BooleanField(_('track opens'), default=True)
    track_clicks = models.BooleanField(_('track clicks'), default=True)
    unique_opens_count = models.PositiveIntegerField(default=0)
    unique_clicks_count = models.PositiveIntegerField(default=0)
    total_opens_count = models.PositiveIntegerField(default=0)
    total_clicks_count = models.PositiveIntegerField(default=0)

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

    def send(self):
        send_campaign_task.delay(self.pk)
        self.recipients_count = self.mailing_list.get_active_subscribers().count()
        self.send_date = timezone.now()
        self.status = constants.SENT
        self.save()

    def can_send(self):
        for email in self.emails.all():
            if not email.can_send():
                return False
        else:
            return True


class Email(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name=_('campaign'), related_name='emails')
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        verbose_name=_('email template'),
        related_name='emails',
        null=True,
        blank=True
    )
    template_content = models.TextField(_('email template content'), blank=True)
    from_email = models.EmailField(_('email address'))
    from_name = models.CharField(_('name'), max_length=100, blank=True)
    subject = models.CharField(_('subject'), max_length=150)
    preview = models.CharField(_('preview'), max_length=150, blank=True)
    content = models.TextField(_('content'))
    content_text = models.TextField(_('content'))
    content_blocks = models.TextField(_('blocks'))

    __blocks = None

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')

    def __str__(self):
        return self.subject

    def get_from(self):
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email

    def get_base_template(self):
        """
        Retuns a Django template using `template_content` field.
        Fallback to default basic template defined by EmailTemplate.
        """
        if self.template_content:
            template = Template(self.template_content)
        else:
            template_string = EmailTemplate.objects.default_content()
            template = Template(template_string)
        return template

    def set_blocks(self):
        old_blocks = self.get_blocks()
        new_blocks = dict()
        template = self.get_base_template()
        template_blocks_names = get_template_blocks(template)
        for name in template_blocks_names:
            inherited_content = ''
            if name in old_blocks.keys():
                inherited_content = old_blocks[name]
            new_blocks[name] = inherited_content
        self.content_blocks = json.dumps(new_blocks)
        self.__blocks = new_blocks

    def load_blocks(self):
        try:
            blocks = json.loads(self.content_blocks)
        except (TypeError, json.JSONDecodeError):
            blocks = {'content': ''}
        return blocks

    def get_blocks(self):
        if self.__blocks is None:
            self.__blocks = self.load_blocks()
        return self.__blocks

    def checklist(self):
        _checklist = {
            'recipients': False,
            'from': False,
            'subject': False,
            'content': False,
            'unsub': False,
            'plaintext': False
        }

        if self.campaign.mailing_list is not None and self.campaign.mailing_list.get_active_subscribers().exists():
            _checklist['recipients'] = True

        if self.from_email:
            _checklist['from'] = True

        if self.subject:
            _checklist['subject'] = True

        if self.content:
            _checklist['content'] = True
            html_template = Template(self.content)
            html_variables = get_template_variables(html_template)
            text_template = Template(self.content_text)
            text_variables = get_template_variables(text_template)

            _checklist['unsub'] = ('unsub' in html_variables and 'unsub' in text_variables)
            _checklist['plaintext'] = (self.content_text != '')
        return _checklist

    def can_send(self):
        checklist = self.checklist()
        for value in checklist.values():
            if not value:
                return False
        else:
            return True

    def render(self, template_string, context_dict):
        template = Template(template_string)
        context = Context(context_dict)
        return template.render(context)

    def render_html(self, context_dict):
        return self.render(self.content, context_dict)

    def render_text(self, context_dict):
        return self.render(self.content_text, context_dict)

    def enable_tracking(self):
        soup = BeautifulSoup(self.content, 'html5lib')
        for index, a in enumerate(soup.findAll('a')):
            href = a.attrs['href']
            url = href.strip()
            if url.lower().startswith('http://') or url.lower().startswith('https://'):
                link, created = Link.objects.get_or_create(email=self, url=url, index=index)
                current_site = get_current_site(request=None)
                protocol = 'http'
                domain = current_site.domain
                # We cannot use django.urls.reverse here because part of the kwargs
                # will be processed during the sending campaign (including the `subscriber_uuid`)
                # With the `{{ uuid }}` we are introducing an extra django template variable
                # which will be later used to replace with the subscriber's uuid.
                track_url = '%s://%s/track/click/%s/{{ uuid }}/' % (protocol, domain, link.uuid)
                a.attrs['href'] = track_url
        self.content = str(soup)


class Link(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    unique_clicks_count = models.PositiveIntegerField(default=0)
    total_clicks_count = models.PositiveIntegerField(default=0)
    index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _('link')
        verbose_name_plural = _('links')

    def __str__(self):
        return self.url
