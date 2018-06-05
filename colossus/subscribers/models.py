import uuid

from django.core.mail import send_mail
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from colossus.core.models import Token
from colossus.lists.models import MailingList
from colossus.utils import get_client_ip


class Subscriber(models.Model):
    PENDING = 1
    SUBSCRIBED = 2
    UNSUBSCRIBED = 3
    CLEANED = 4
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (SUBSCRIBED, 'Subscribed'),
        (UNSUBSCRIBED, 'Unsubscribed'),
        (CLEANED, 'Cleaned'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(_('email address'), max_length=255)
    name = models.CharField(_('name'), max_length=150, blank=True)
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    date_subscribed = models.DateTimeField(_('subscribed'), null=True, blank=True)
    date_updated = models.DateTimeField(_('updated'), auto_now=True)
    date_created = models.DateTimeField(_('created'), auto_now_add=True)
    status = models.PositiveSmallIntegerField(_('status'), default=PENDING, choices=STATUS_CHOICES)
    optin_ip_address = models.GenericIPAddressField(_('opt-in IP address'), unpack_ipv4=True, blank=True, null=True)
    confirm_ip_address = models.GenericIPAddressField(_('confirm IP address'), unpack_ipv4=True, blank=True, null=True)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.PROTECT, related_name='subscribers')
    tokens = GenericRelation(Token)

    class Meta:
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
        unique_together = (('email', 'mailing_list',),)

    def __str__(self):
        return self.email

    @transaction.atomic()
    def confirm_subscription(self, request):
        self.date_subscribed = timezone.now()
        self.status = Subscriber.SUBSCRIBED
        self.confirm_ip_address = get_client_ip(request)
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
