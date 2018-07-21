import json
import re
import uuid

from django.apps import apps
from django.contrib.sites.shortcuts import get_current_site
from django.db import models, transaction
from django.db.models import Count
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext, gettext_lazy as _

from bs4 import BeautifulSoup

from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.templates.models import EmailTemplate
from colossus.apps.templates.utils import get_template_blocks

from .constants import CampaignStatus, CampaignTypes
from .tasks import send_campaign_task, update_rates_after_campaign_deletion


class Campaign(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(_('name'), max_length=100)
    campaign_type = models.PositiveSmallIntegerField(
        _('type'),
        choices=CampaignTypes.CHOICES,
        default=CampaignTypes.REGULAR
    )
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='campaigns',
        null=True,
        blank=True
    )
    status = models.PositiveSmallIntegerField(
        _('status'),
        choices=CampaignStatus.CHOICES,
        default=CampaignStatus.DRAFT,
        db_index=True
    )
    send_date = models.DateTimeField(_('send date'), null=True, blank=True, db_index=True)
    create_date = models.DateTimeField(_('create date'), auto_now_add=True)
    update_date = models.DateTimeField(_('update date'), default=timezone.now)
    recipients_count = models.PositiveIntegerField(default=0)
    track_opens = models.BooleanField(_('track opens'), default=True)
    track_clicks = models.BooleanField(_('track clicks'), default=True)
    unique_opens_count = models.PositiveIntegerField(_('unique opens'), default=0, editable=False)
    total_opens_count = models.PositiveIntegerField(_('total opens'), default=0, editable=False)
    unique_clicks_count = models.PositiveIntegerField(_('unique clicks'), default=0, editable=False)
    total_clicks_count = models.PositiveIntegerField(_('total clicks'), default=0, editable=False)
    open_rate = models.FloatField(_('opens'), default=0.0, editable=False)
    click_rate = models.FloatField(_('clicks'), default=0.0, editable=False)

    __cached_email = None

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')
        db_table = 'colossus_campaigns'

    def __str__(self):
        return self.name

    def get_absolute_url(self) -> str:
        if self.can_edit:
            return reverse('campaigns:campaign_edit', kwargs={'pk': self.pk})
        return reverse('campaigns:campaign_detail', kwargs={'pk': self.pk})

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)
        update_rates_after_campaign_deletion.delay(self.mailing_list_id)

    @property
    def is_ongoing(self) -> bool:
        return self.status in (CampaignStatus.SCHEDULED,)

    @property
    def can_edit(self) -> bool:
        return self.status in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED)

    @property
    def can_send(self) -> bool:
        for email in self.emails.all():
            if not email.can_send:
                return False
        else:
            return True

    @property
    def email(self):
        if not self.__cached_email and self.campaign_type == CampaignTypes.REGULAR:
            try:
                self.__cached_email, created = Email.objects.get_or_create(campaign=self)
            except Email.MultipleObjectsReturned:
                self.__cached_email = self.emails.order_by('id').first()
        return self.__cached_email

    @transaction.atomic
    def send(self):
        self.recipients_count = self.mailing_list.get_active_subscribers().count()
        self.send_date = timezone.now()
        self.status = CampaignStatus.SENT
        for email in self.emails.select_related('template').all():
            if email.template is not None:
                email.template.last_used_date = timezone.now()
                email.template.last_used_campaign_id = self.pk
                email.template.save()
        self.save()
        send_campaign_task.delay(self.pk)

    @transaction.atomic
    def replicate(self):
        copy = gettext(' (copy)')
        slice_at = 100 - len(copy)
        name = '%s%s' % (self.name[:slice_at], copy)

        replicated_campaign = Campaign.objects.create(
            name=name,
            campaign_type=self.campaign_type,
            mailing_list=self.mailing_list,
            status=CampaignStatus.DRAFT,
        )

        replicated_emails = list()

        for email in self.emails.all():
            replicated_email = Email(
                campaign=replicated_campaign,
                template=email.template,
                template_content=email.template_content,
                from_email=email.from_email,
                from_name=email.from_name,
                subject=email.subject,
                preview=email.preview,
                content=email.content,
                content_html=email.content_html,
                content_text=email.content_text
            )
            replicated_emails.append(replicated_email)

        Email.objects.bulk_create(replicated_emails)
        return replicated_campaign

    def update_clicks_count_and_rate(self) -> tuple:
        Activity = apps.get_model('subscribers', 'Activity')
        qs = Activity.objects.filter(email__campaign=self, activity_type=ActivityTypes.CLICKED) \
            .values('subscriber_id') \
            .order_by('subscriber_id') \
            .aggregate(unique_count=Count('subscriber_id', distinct=True), total_count=Count('subscriber_id'))
        self.unique_clicks_count = qs['unique_count']
        self.total_clicks_count = qs['total_count']
        try:
            self.click_rate = self.unique_clicks_count / self.recipients_count
        except ZeroDivisionError:
            self.click_rate = 0.0
        self.save(update_fields=['unique_clicks_count', 'total_clicks_count', 'click_rate'])
        return (self.unique_clicks_count, self.total_clicks_count, self.click_rate)

    def update_opens_count_and_rate(self) -> tuple:
        Activity = apps.get_model('subscribers', 'Activity')
        qs = Activity.objects.filter(email__campaign=self, activity_type=ActivityTypes.OPENED) \
            .values('subscriber_id') \
            .order_by('subscriber_id') \
            .aggregate(unique_count=Count('subscriber_id', distinct=True), total_count=Count('subscriber_id'))
        self.unique_opens_count = qs['unique_count']
        self.total_opens_count = qs['total_count']
        try:
            self.open_rate = self.unique_opens_count / self.recipients_count
        except ZeroDivisionError:
            self.open_rate = 0.0
        self.save(update_fields=['unique_opens_count', 'total_opens_count', 'open_rate'])
        return (self.unique_opens_count, self.total_opens_count, self.open_rate)


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
    content = models.TextField(_('content'), blank=True)
    content_html = models.TextField(_('content HTML'), blank=True)
    content_text = models.TextField(_('content plain text'), blank=True)
    unique_opens_count = models.PositiveIntegerField(_('unique opens'), default=0, editable=False)
    total_opens_count = models.PositiveIntegerField(_('total opens'), default=0, editable=False)
    unique_clicks_count = models.PositiveIntegerField(_('unique clicks'), default=0, editable=False)
    total_clicks_count = models.PositiveIntegerField(_('total clicks'), default=0, editable=False)

    __blocks = None
    __base_template = None
    __child_template_string = None

    BASE_TEMPLATE_VAR = 'base_template'

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')
        db_table = 'colossus_emails'

    def __str__(self):
        return self.subject

    @property
    def base_template(self) -> Template:
        if self.__base_template is None:
            self.__base_template = Template(self.template_content)
        return self.__base_template

    @property
    def child_template_string(self) -> str:
        if self.__child_template_string is None:
            self.__child_template_string = self.build_child_template_string()
        return self.__child_template_string

    def set_template_content(self):
        if self.template is None:
            self.template_content = EmailTemplate.objects.default_content()
        else:
            self.template_content = self.template.content

    def get_from(self) -> str:
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email

    def get_base_template(self) -> Template:
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

    def set_blocks(self, blocks=None):
        if blocks is None:
            old_blocks = self.get_blocks()
            blocks = dict()
            template = self.get_base_template()
            template_blocks = get_template_blocks(template)
            for block_name, block_content in template_blocks.items():
                inherited_content = block_content
                if block_name in old_blocks.keys():
                    old_block_content = old_blocks.get(block_name, '').strip()
                    if old_block_content:
                        inherited_content = old_blocks[block_name]
                blocks[block_name] = inherited_content
        self.content = json.dumps(blocks)
        self.__blocks = blocks

    def load_blocks(self) -> dict:
        try:
            blocks = json.loads(self.content)
        except (TypeError, json.JSONDecodeError):
            blocks = {'content': ''}
        return blocks

    def get_blocks(self) -> dict:
        if self.__blocks is None:
            self.__blocks = self.load_blocks()
        return self.__blocks

    def checklist(self) -> dict:
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

            # Generate a random string and pass it to the render function
            # as if it was the unsubscribe url. If we can find this token in the
            # rendered template, we can say the unsubscribe url will be rendered.
            # Not 100% guranteed, as the end user can still bypass it (e.g.
            # changing visibility with html).
            token = get_random_string(50)
            rendered_template = self.render({'unsub': token})
            _checklist['unsub'] = token in rendered_template

            _checklist['plaintext'] = (self.content_text != '')
        return _checklist

    @property
    def can_send(self) -> bool:
        checklist = self.checklist()
        for value in checklist.values():
            if not value:
                return False
        else:
            return True

    def build_child_template_string(self) -> str:
        """
        Build a valid Django template string with `extends` block tag
        on top and representation of each content blocks, constructed
        from the JSON object.
        """
        virtual_template = ['{%% extends %s %%}' % self.BASE_TEMPLATE_VAR, ]
        blocks = self.get_blocks()
        for block_key, block_content in blocks.items():
            if block_content:
                virtual_template.append('{%% block %s %%}\n%s\n{%% endblock %%}' % (block_key, block_content))
        return '\n\n'.join(virtual_template)

    def _render(self, template_string, context_dict) -> str:
        template = Template(template_string)
        context = Context(context_dict)
        return template.render(context)

    def render(self, context_dict) -> str:
        context_dict.update({self.BASE_TEMPLATE_VAR: self.base_template})
        return self._render(self.child_template_string, context_dict)

    def _enable_click_tracking(self, html, start_index=0):
        urls = re.findall(r'(?i)(href=["\']?)(https?://[^"\' >]+)', html)
        index = 0
        for index, data in enumerate(urls):
            href = data[0]
            url = data[1]
            link, created = Link.objects.get_or_create(email=self, url=url, index=(start_index + index))
            current_site = get_current_site(request=None)
            protocol = 'http'
            domain = current_site.domain
            # We cannot use django.urls.reverse here because part of the kwargs
            # will be processed during the sending campaign (including the `subscriber_uuid`)
            # With the `{{ uuid }}` we are introducing an extra django template variable
            # which will be later used to replace with the subscriber's uuid.
            track_url = '%s://%s/track/click/%s/{{uuid}}/' % (protocol, domain, link.uuid)
            html = re.sub(r'(?i)href=["\']?%s' % url, '%s%s' % (href, track_url), html, 1)
        return html, (index + 1)

    def enable_click_tracking(self):
        self.template_content, index = self._enable_click_tracking(self.template_content)
        blocks = self.get_blocks()
        for key, html in blocks.items():
            blocks[key], index = self._enable_click_tracking(html, index)
        self.set_blocks(blocks)

    def enable_open_tracking(self):
        current_site = get_current_site(request=None)
        protocol = 'http'
        domain = current_site.domain
        track_url = '%s://%s/track/open/%s/{{uuid}}/' % (protocol, domain, self.uuid)
        soup = BeautifulSoup(self.template_content, 'html5lib')
        img_tag = soup.new_tag('img', src=track_url, height='1', width='1')
        soup.find('body').append(img_tag)
        self.template_content = str(soup)

    def update_clicks_count(self) -> tuple:
        qs = self.activities.filter(activity_type=ActivityTypes.CLICKED) \
            .values('subscriber_id') \
            .order_by('subscriber_id') \
            .aggregate(unique_count=Count('subscriber_id', distinct=True), total_count=Count('subscriber_id'))
        self.unique_clicks_count = qs['unique_count']
        self.total_clicks_count = qs['total_count']
        self.save(update_fields=['unique_clicks_count', 'total_clicks_count'])
        return (self.unique_clicks_count, self.total_clicks_count)

    def update_opens_count(self) -> tuple:
        qs = self.activities.filter(activity_type=ActivityTypes.OPENED) \
            .values('subscriber_id') \
            .order_by('subscriber_id') \
            .aggregate(unique_count=Count('subscriber_id', distinct=True), total_count=Count('subscriber_id'))
        self.unique_opens_count = qs['unique_count']
        self.total_opens_count = qs['total_count']
        self.save(update_fields=['unique_opens_count', 'total_opens_count'])
        return (self.unique_opens_count, self.total_opens_count)


class Link(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    unique_clicks_count = models.PositiveIntegerField(default=0, editable=False)
    total_clicks_count = models.PositiveIntegerField(default=0, editable=False)
    index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _('link')
        verbose_name_plural = _('links')
        db_table = 'colossus_links'

    def __str__(self):
        return self.url

    def update_clicks_count(self) -> tuple:
        qs = self.activities.values('subscriber_id').order_by('subscriber_id').aggregate(
            unique_count=Count('subscriber_id', distinct=True),
            total_count=Count('subscriber_id')
        )
        self.unique_clicks_count = qs['unique_count']
        self.total_clicks_count = qs['total_count']
        self.save(update_fields=['unique_clicks_count', 'total_clicks_count'])
        return (self.unique_clicks_count, self.total_clicks_count)
