import uuid

from django.core.mail import send_mail
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape

from colossus.campaigns.models import Campaign, Email, Link
from colossus.core.models import Token
from colossus.lists.models import MailingList
from colossus.utils import get_client_ip

from . import constants


class Subscriber(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(_('email address'), max_length=255)
    name = models.CharField(_('name'), max_length=150, blank=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.PROTECT, related_name='subscribers')
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    update_date = models.DateTimeField(_('updated'), default=timezone.now)
    status = models.PositiveSmallIntegerField(_('status'), default=constants.PENDING, choices=constants.STATUS_CHOICES)
    optin_ip_address = models.GenericIPAddressField(_('opt-in IP address'), unpack_ipv4=True, blank=True, null=True)
    optin_date = models.DateTimeField(_('opt-in date'), default=timezone.now)
    confirm_ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    confirm_date = models.DateTimeField(_('confirm date'), null=True, blank=True)
    last_seen_ip_address = models.GenericIPAddressField(_('last seen IP address'), unpack_ipv4=True, blank=True, null=True)
    last_seen_date = models.DateTimeField(_('last seen date'), null=True, blank=True)
    tokens = GenericRelation(Token)

    class Meta:
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
        unique_together = (('email', 'mailing_list',),)

    def __str__(self):
        return self.email

    @transaction.atomic()
    def confirm_subscription(self, request):
        self.status = constants.SUBSCRIBED
        self.confirm_ip_address = get_client_ip(request)
        self.confirm_date = timezone.now()
        self.save()
        self.log_activity(activity_type='subscribed')
        self.tokens.filter(description='confirm_subscription').delete()

    @transaction.atomic()
    def unsubscribe(self, request, campaign=None):
        self.status = constants.UNSUBSCRIBED
        self.save()
        self.log_activity(activity_type='unsubscribed', campaign=campaign)

    def send_mail(self, subject, message, from_email=None, **kwargs):
        """Send an email to this subscriber."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def log_activity(self, **kwargs):
        kwargs.update({'subscriber': self})
        activity = Activity.objects.create(**kwargs)
        return activity

    def get_activities(self, **filter_kwargs):
        return self.activities \
            .select_related('subscriber__mailing_list', 'email__campaign', 'link') \
            .filter(**filter_kwargs) \
            .order_by('-date')


class Activity(models.Model):
    activity_type = models.CharField(_('type'), max_length=30, db_index=True)
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
        text = ''
        if self.activity_type == 'subscribed':
            text = '<strong>Subscribed</strong> to the list.'
            text = '''
            <div class="jumbotron text-center">
                <i data-feather="user-plus" stroke-width="1" class="text-muted" height="64px" width="64px"></i>
                <h4>Subscribed to the List %s</h4>
                <p class="text-muted mb-0">on %s</p>
            </div>
            ''' % (self.subscriber.mailing_list.name, self.date.strftime('%b %d, %Y'))
        elif self.activity_type == 'unsubscribed':
            if self.campaign is not None:
                url = self.campaign.get_absolute_url()
                name = self.campaign.name
                text = '<strong>Unsubscribed</strong> via <a href="%s">%s</a>.' % (url, name)
            else:
                text = '<strong>Unsubscribed</strong>.'
        elif self.activity_type == 'open':
            url = self.email.campaign.get_absolute_url()
            name = self.email.campaign.name
            text = '<strong>Opened</strong> the email <a href="%s">%s</a>.' % (url, name)
        else:
            text = self.activity_type
        return mark_safe(text)
