import hashlib
import uuid
from urllib.parse import urlencode

from django.contrib.contenttypes.fields import GenericRelation
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import html2text

from colossus.apps.campaigns.models import Campaign, Email, Link
from colossus.apps.core.models import City, Token
from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.exceptions import (
    FormTemplateIsNotEmail, FormTemplateIsNotForm,
)
from colossus.apps.subscribers.tasks import (
    update_click_rate, update_open_rate,
    update_rates_after_subscriber_deletion, update_subscriber_location,
)
from colossus.utils import get_absolute_url, get_client_ip

from .activities import render_activity
from .constants import ActivityTypes, Status, TemplateKeys
from .subscription_settings import SUBSCRIPTION_FORM_TEMPLATE_SETTINGS


class Tag(models.Model):
    name = models.SlugField()
    description = models.TextField(blank=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        unique_together = (('name', 'mailing_list'),)
        db_table = 'colossus_tags'

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('lists:edit_tag', kwargs={'pk': self.mailing_list_id, 'tag_pk': self.pk})

    def clean(self):
        super().clean()
        self.name = slugify(self.name)


class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = _('domain')
        verbose_name_plural = _('domains')
        db_table = 'colossus_domains'

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        self.name = self.name.lower()


class SubscriberManager(models.Manager):
    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing the domain part of it.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = email_name + '@' + domain_part.lower()
        return email

    def create_subscriber(self, email, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        subscriber = self.model(email=email, **extra_fields)
        subscriber.save(using=self._db)
        return subscriber


class Subscriber(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(_('email address'), max_length=255)
    domain = models.ForeignKey(
        Domain,
        on_delete=models.PROTECT,
        verbose_name=_('domain'),
        related_name='subscribers'
    )
    name = models.CharField(_('name'), max_length=150, blank=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.PROTECT, related_name='subscribers')
    open_rate = models.FloatField(_('opens'), default=0.0, editable=False)
    click_rate = models.FloatField(_('clicks'), default=0.0, editable=False)
    update_date = models.DateTimeField(_('updated'), default=timezone.now)
    status = models.PositiveSmallIntegerField(_('status'), default=Status.PENDING, choices=Status.CHOICES)
    optin_ip_address = models.GenericIPAddressField(_('opt-in IP address'), unpack_ipv4=True, blank=True, null=True)
    optin_date = models.DateTimeField(_('opt-in date'), default=timezone.now)
    confirm_ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    confirm_date = models.DateTimeField(_('confirm date'), null=True, blank=True)
    last_seen_ip_address = models.GenericIPAddressField(
        _('last seen IP address'),
        unpack_ipv4=True,
        blank=True,
        null=True
    )
    last_seen_date = models.DateTimeField(_('last seen date'), null=True, blank=True)
    location = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('location'),
        related_name='subscribers',
    )
    last_sent = models.DateTimeField(_('last campaign sent date'), null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='subscribers', verbose_name=_('tags'), blank=True)
    tokens = GenericRelation(Token)

    objects = SubscriberManager()

    __status = None

    class Meta:
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
        unique_together = (('email', 'mailing_list',),)
        db_table = 'colossus_subscribers'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status = self.status
        self.__email = self.email

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse('lists:edit_subscriber', kwargs={'pk': self.mailing_list_id, 'subscriber_pk': self.pk})

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.__email != self.email:
            email_name, domain_part = self.email.rsplit('@', 1)
            domain_name = '@' + domain_part
            email_domain, created = Domain.objects.get_or_create(name=domain_name)
            self.domain = email_domain
            if update_fields is not None and 'domain' not in update_fields:
                update_fields.append('domain')
            self.__email = self.email

        super().save(force_insert, force_update, using, update_fields)

        if self.__status != self.status:
            self.mailing_list.update_subscribers_count()
            self.__status = self.status

    def delete(self, using=None, keep_parents=False):
        email_ids = list(self.activities.filter(activity_type=ActivityTypes.SENT).values_list('email_id', flat=True))
        link_ids = list(self.activities.filter(activity_type=ActivityTypes.CLICKED)
                        .values_list('link_id', flat=True)
                        .order_by('link_id')
                        .distinct())
        super().delete(using, keep_parents)
        update_rates_after_subscriber_deletion.delay(self.mailing_list_id, email_ids, link_ids)

    def get_gravatar_url(self):
        email = self.email.lower().encode('utf-8')
        default = 'mm'
        size = 128
        url = 'https://www.gravatar.com/avatar/{md5}?{params}'.format(
            md5=hashlib.md5(email).hexdigest(),
            params=urlencode({'d': default, 's': str(size)})
        )
        return url

    def get_email(self):
        if self.name:
            return '%s <%s>' % (self.name, self.email)
        return self.email

    def confirm_subscription(self, request):
        ip_address = get_client_ip(request)

        with transaction.atomic():
            self.status = Status.SUBSCRIBED
            self.confirm_ip_address = ip_address
            self.last_seen_ip_address = ip_address
            self.confirm_date = timezone.now()
            self.save()
            self.create_activity(ActivityTypes.SUBSCRIBED, ip_address=ip_address)
            self.tokens.filter(description='confirm_subscription').delete()

        update_subscriber_location.delay(ip_address, self.pk)

        welcome_email = self.mailing_list.get_welcome_email_template()
        if welcome_email.send_email:
            welcome_email.send(self.get_email())

    def unsubscribe(self, request, campaign=None):
        ip_address = get_client_ip(request)

        with transaction.atomic():
            self.status = Status.UNSUBSCRIBED
            self.last_seen_ip_address = ip_address
            self.save()
            self.create_activity(ActivityTypes.UNSUBSCRIBED, campaign=campaign, ip_address=ip_address)

        update_subscriber_location.delay(ip_address, self.pk)

        goodbye_email = self.mailing_list.get_goodbye_email_template()
        if goodbye_email.send_email:
            goodbye_email.send(self.get_email())

    def create_activity(self, activity_type, **activity_kwargs):
        activity_kwargs.update({
            'subscriber': self,
            'activity_type': activity_type
        })
        activity = Activity.objects.create(**activity_kwargs)
        return activity

    def get_activities(self, **filter_kwargs):
        return self.activities \
            .select_related('subscriber__mailing_list', 'email__campaign', 'link') \
            .filter(**filter_kwargs) \
            .order_by('-date')

    def open(self, email, ip_address=None):
        """
        For the open tracking we may not consider the IP address because it is
        not reliable under some circumstances. In many case the overwhelming
        majority of users use gmail. The reason why the IP address is not
        reliable is because gmail caches the 1x1 pixel used to track opens, and
        when the user open the email, it will load the image from their servers,
        so it will inflate the number of opens from United States/Montain View.

        What we do instead is to use the subscriber's last seen location, which
        may be the location where he/she subscribed in the first place, or the
        place where he/she was when clicked in a link in a previous email.

        If the same user clicks on a link after opening the email, we will
        adjust the location based on the information we gather on the click
        event.

        :param email: campaigns.Email instance that the user opened
        :param ip_address: Optional client IP address
        """
        if ip_address is not None:
            self.create_activity(ActivityTypes.OPENED, email=email, ip_address=ip_address)
            update_subscriber_location.delay(ip_address, self.pk)
        else:
            self.create_activity(ActivityTypes.OPENED, email=email, location=self.location)
        update_open_rate.delay(self.pk, email.pk)

    def click(self, link, ip_address=None):
        self.create_activity(ActivityTypes.CLICKED, link=link, email=link.email, ip_address=ip_address)
        if ip_address is not None:
            self.last_seen_date = timezone.now()
            self.last_seen_ip_address = ip_address
            self.save(update_fields=['last_seen_date', 'last_seen_ip_address'])

            # Update all open activities without IP address with the click activity IP address
            self.activities \
                .filter(activity_type=ActivityTypes.OPENED, email=link.email, ip_address=None) \
                .update(ip_address=ip_address)
            update_subscriber_location.delay(ip_address, self.pk)
        update_click_rate.delay(self.pk, link.pk)

    def update_open_rate(self) -> float:
        count = self.activities.values('email_id', 'activity_type').aggregate(
            sent=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.SENT)),
            opened=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.OPENED)),
        )
        try:
            self.open_rate = round(count['opened'] / count['sent'], 4)
        except ZeroDivisionError:
            self.open_rate = 0.0
        finally:
            self.save(update_fields=['open_rate'])
        return self.open_rate

    def update_click_rate(self) -> float:
        count = self.activities.values('email_id', 'activity_type').aggregate(
            sent=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.SENT)),
            clicked=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.CLICKED)),
        )
        try:
            self.click_rate = round(count['clicked'] / count['sent'], 4)
        except ZeroDivisionError:
            self.click_rate = 0.0
        finally:
            self.save(update_fields=['click_rate'])
        return self.click_rate

    def update_open_and_click_rate(self):
        count = self.activities.values('email_id', 'activity_type').aggregate(
            sent=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.SENT)),
            opened=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.OPENED)),
            clicked=Count('email_id', distinct=True, filter=Q(activity_type=ActivityTypes.CLICKED)),
        )
        try:
            self.open_rate = round(count['opened'] / count['sent'], 4)
            self.click_rate = round(count['clicked'] / count['sent'], 4)
        except ZeroDivisionError:
            self.open_rate = 0.0
            self.click_rate = 0.0
        self.save(update_fields=['open_rate', 'click_rate'])


class Activity(models.Model):
    activity_type = models.PositiveSmallIntegerField(_('type'), choices=ActivityTypes.CHOICES)
    date = models.DateTimeField(_('date'), auto_now_add=True)
    description = models.TextField(_('description'), blank=True)
    ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    location = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('location'),
        related_name='activities',
    )
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='activities')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    email = models.ForeignKey(Email, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    link = models.ForeignKey(Link, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')

    __cached_html = ''

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')
        db_table = 'colossus_activities'

    @property
    def is_subscribed(self):
        return self.activity_type == ActivityTypes.SUBSCRIBED

    @property
    def is_unsubscribed(self):
        return self.activity_type == ActivityTypes.UNSUBSCRIBED

    @property
    def as_html(self):
        if not self.__cached_html:
            self.__cached_html = self.render()
        return self.__cached_html

    def render(self):
        try:
            html = render_activity(self)
            return mark_safe(html)
        except Exception:
            return self.get_activity_type_display()

    def get_formatted_date(self):
        return self.date.strftime('%b %d, %Y %H:%M')


class SubscriptionFormTemplate(models.Model):
    key = models.CharField(_('key'), choices=TemplateKeys.CHOICES, max_length=30, db_index=True)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='forms_templates'
    )
    redirect_url = models.URLField(
        _('redirect URL'),
        blank=True,
        help_text=_('Instead of showing this page, redirect to URL.')
    )
    send_email = models.BooleanField(_('send final confirmation email?'), default=False)
    from_email = models.EmailField(_('from email address'))
    from_name = models.CharField(_('from name'), max_length=100, blank=True)
    subject = models.CharField(_('email subject'), max_length=150)
    content_html = models.TextField(_('content HTML'), blank=True)
    content_text = models.TextField(_('content plain text'), blank=True)

    class Meta:
        verbose_name = _('form template')
        verbose_name_plural = _('form templates')
        db_table = 'colossus_form_templates'

    def __str__(self):
        return self.get_key_display()

    @property
    def settings(self):
        return SUBSCRIPTION_FORM_TEMPLATE_SETTINGS[self.key]

    @property
    def is_email(self) -> bool:
        return self.key in (TemplateKeys.CONFIRM_EMAIL, TemplateKeys.GOODBYE_EMAIL, TemplateKeys.WELCOME_EMAIL)

    @property
    def is_form(self) -> bool:
        return self.key in (TemplateKeys.SUBSCRIBE_FORM, TemplateKeys.UNSUBSCRIBE_FORM)

    def load_defaults(self):
        self.content_html = self.get_default_content()
        self.redirect_url = ''
        self.send_email = False
        if self.is_email:
            self.subject = self.get_default_subject()
            self.from_name = self.mailing_list.campaign_default_from_name
            self.from_email = self.mailing_list.campaign_default_from_email
        else:
            self.subject = ''
            self.from_name = ''
            self.from_email = ''
        self.save()

    def get_default_content(self):
        content_template_name = self.settings['default_content']
        html = render_to_string(content_template_name, {'mailing_list': self.mailing_list})
        return html

    def get_default_subject(self):
        if not self.is_email:
            raise FormTemplateIsNotEmail

        subject_template_name = self.settings['default_subject']
        subject = render_to_string(subject_template_name, {'list_name': self.mailing_list.name})
        subject = ''.join(subject.splitlines())  # remove new lines from subject
        return subject

    def get_form_class(self):
        if not self.is_form:
            raise FormTemplateIsNotForm
        from colossus.apps.subscribers import forms
        form_class_name = self.settings['form']
        form_class = getattr(forms, form_class_name)
        return form_class

    def get_from_email(self):
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email

    def render_template(self, extra_context: dict = None, form_kwargs: dict = None):
        if extra_context is None:
            extra_context = dict()

        unsubscribe_absolute_url = get_absolute_url('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': self.mailing_list.uuid,
        })

        subscribe_absolute_url = get_absolute_url('subscribers:subscribe', kwargs={
            'mailing_list_uuid': self.mailing_list.uuid,
        })

        context = {
            'mailing_list': self.mailing_list,
            'list_name': self.mailing_list.name,
            'content': self.content_html,
            'unsub': unsubscribe_absolute_url,
            'subscribe_link': subscribe_absolute_url,
            'contact_email': self.mailing_list.contact_email_address,
        }

        if self.is_form:
            if form_kwargs is None:
                form_kwargs = dict()

            form_class = self.get_form_class()
            form = form_class(mailing_list=self.mailing_list, **form_kwargs)
            context['form'] = form

        context.update(extra_context)
        content_template_name = self.settings['content_template_name']
        html = render_to_string(content_template_name, context)
        return html

    def send(self, to: str, context: dict = None):
        """
        Send a confirm email/welcome email/goodbye email to a subscriber.
        If the SubscriptionFormTemplate instance is not an email, it will raise
        an FormTemplateIsNotEmail exception.

        :param to: Subscriber email address
        :param context: Extra context to be used during email rendering
        """
        if not self.is_email:
            raise FormTemplateIsNotEmail

        rich_text_message = self.render_template(context)
        plain_text_message = html2text.html2text(rich_text_message, bodywidth=2000)
        email = EmailMultiAlternatives(
            subject=self.subject,
            body=plain_text_message,
            from_email=self.get_from_email(),
            to=[to]
        )
        email.attach_alternative(rich_text_message, 'text/html')
        email.send()
