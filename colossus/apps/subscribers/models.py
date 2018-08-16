import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from colossus.apps.campaigns.models import Campaign, Email, Link
from colossus.apps.core.models import City, Token
from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.tasks import (
    update_click_rate, update_open_rate,
    update_rates_after_subscriber_deletion, update_subscriber_location,
)
from colossus.utils import get_client_ip

from .activities import render_activity
from .constants import ActivityTypes, Status, TemplateKeys
from .subscription_settings import SUBSCRIPTION_FORM_TEMPLATE_SETTINGS


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

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
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

    def get_email(self):
        if self.name:
            return '%s <%s>' % (self.name, self.email)
        return self.email

    @transaction.atomic()
    def confirm_subscription(self, request):
        ip_address = get_client_ip(request)
        self.status = Status.SUBSCRIBED
        self.confirm_ip_address = ip_address
        self.confirm_date = timezone.now()
        self.save()
        self.create_activity(ActivityTypes.SUBSCRIBED, ip_address=ip_address)
        self.tokens.filter(description='confirm_subscription').delete()

    @transaction.atomic()
    def unsubscribe(self, request, campaign=None):
        self.status = Status.UNSUBSCRIBED
        self.save()
        self.create_activity(ActivityTypes.UNSUBSCRIBED, campaign=campaign, ip_address=get_client_ip(request))

    def send_mail(self, subject, message, from_email=None, **kwargs):
        """Send an email to this subscriber."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

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
        activity = self.create_activity(ActivityTypes.OPENED, email=email, ip_address=ip_address)
        if ip_address is not None:
            update_subscriber_location.delay(ip_address, self.pk, activity.pk)
        update_open_rate.delay(self.pk, email.pk)

    def click(self, link, ip_address=None):
        activity = self.create_activity(ActivityTypes.CLICKED, link=link, email=link.email, ip_address=ip_address)
        if ip_address is not None:
            self.last_seen_date = timezone.now()
            self.last_seen_ip_address = ip_address
            self.save(update_fields=['last_seen_date', 'last_seen_ip_address'])
            update_subscriber_location.delay(ip_address, self.pk, activity.pk)
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
    send_email = models.BooleanField(_('send final confirmation email?'), default=True)
    from_email = models.EmailField(_('from email address'))
    from_name = models.CharField(_('from name'), max_length=100, blank=True)
    subject = models.CharField(_('email subject'), max_length=150, blank=True)
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

    def get_default_content(self):
        content_template_name = self.settings['default_content']
        html = render_to_string(content_template_name, {'mailing_list': self.mailing_list})
        return html
