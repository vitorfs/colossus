import uuid

from django.core.mail import send_mail
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from colossus.core.models import Activity, Token
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
    update_date = models.DateTimeField(_('updated'), auto_now=True)
    status = models.PositiveSmallIntegerField(_('status'), default=constants.PENDING, choices=constants.STATUS_CHOICES)
    optin_ip_address = models.GenericIPAddressField(_('opt-in IP address'), unpack_ipv4=True, blank=True, null=True)
    optin_date = models.DateTimeField(_('opt-in date'), default=timezone.now)
    confirm_ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    confirm_date = models.DateTimeField(_('confirm date'), null=True, blank=True)
    tokens = GenericRelation(Token)
    activities = GenericRelation(Activity)

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
        self.tokens.filter(description='confirm_subscription').delete()

    def send_mail(self, subject, message, from_email=None, **kwargs):
        """Send an email to this subscriber."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class SubscriptionFormTemplate(models.Model):
    name = models.CharField(_('name'), max_length=100)
    is_active = models.BooleanField(_('active status'), default=True)
    content = models.TextField(_('content'), blank=True)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='subscription_form_templates'
    )

    class Meta:
        verbose_name = _('subscription form template')
        verbose_name_plural = _('subscription form templates')
