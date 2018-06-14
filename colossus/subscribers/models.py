import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from colossus.campaigns.models import Campaign, Email, Link
from colossus.core.models import Token
from colossus.lists.models import MailingList
from colossus.utils import get_client_ip

from .constants import Status, ActivityTypes, TemplateTypes, Workflows, Keys
from .activities import renderers


class Subscriber(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(_('email address'), max_length=255)
    name = models.CharField(_('name'), max_length=150, blank=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.PROTECT, related_name='subscribers')
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
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
    tokens = GenericRelation(Token)

    __status = None

    class Meta:
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
        unique_together = (('email', 'mailing_list',),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status = self.status

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.__status != self.status:
            self.mailing_list.update_subscribers_count()
            self.__status = self.status

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


class Activity(models.Model):
    activity_type = models.PositiveSmallIntegerField(_('type'), choices=ActivityTypes.CHOICES)
    date = models.DateTimeField(_('date'), auto_now_add=True)
    description = models.TextField(_('description'), blank=True)
    ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='activities')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    email = models.ForeignKey(Email, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    link = models.ForeignKey(Link, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')

    __cached_text = ''

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')

    @property
    def text(self):
        if not self.__cached_text:
            self.__cached_text = self.render_text()
        return self.__cached_text

    def render_text(self):
        renderer = renderers[self.activity_type]
        text = renderer(self)
        return mark_safe(text)

    def get_formatted_date(self):
        return self.date.strftime('%b %d, %Y %H:%M')


class FormTemplate(models.Model):
    key = models.CharField(_('key'), choices=Keys.CHOICES, max_length=30, db_index=True)
    template_type = models.PositiveSmallIntegerField(_('type'), choices=TemplateTypes.CHOICES)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='forms_templates'
    )
    workflow = models.PositiveSmallIntegerField(_('workflow'), choices=Workflows.CHOICES)
    order = models.PositiveSmallIntegerField(_('order'), default=0)
    redirect_url = models.URLField(_('redirect URL'), blank=True)
    is_enabled = models.BooleanField(_('is enabled'), default=True)
    content_html = models.TextField(blank=True)
    content_text = models.TextField(blank=True)

    class Meta:
        verbose_name = _('form template')
        verbose_name_plural = _('forms templates')

    def __str__(self):
        return self.get_key_display()
