from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.lists.models import MailingList


class Campaign(models.Model):
    REGULAR = 1
    AUTOMATED = 2
    AB_TEST = 3
    CAMPAIGN_TYPE_CHOICES = (
        (REGULAR, _('Regular')),
        (AUTOMATED, _('Automated')),
        (AB_TEST, _('A/B Test')),
    )

    SENT = 1
    SCHEDULED = 2
    DRAFT = 3
    TRASH = 4
    STATUS_CHOICES = (
        (SENT, _('Sent')),
        (SCHEDULED, _('Scheduled')),
        (DRAFT, _('Draft')),
        (TRASH, _('Trashed')),
    )

    name = models.CharField(_('name'), max_length=100)
    campaign_type = models.PositiveSmallIntegerField(_('type'), choices=CAMPAIGN_TYPE_CHOICES, default=REGULAR)
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        verbose_name=_('mailing list'),
        related_name='campaigns',
        null=True,
        blank=True
    )
    status = models.PositiveSmallIntegerField(_('status'), choices=STATUS_CHOICES, default=DRAFT)
    send_date = models.DateTimeField(_('send date'), null=True, blank=True)

    __cached_email = None

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.status in (Campaign.DRAFT, Campaign.SCHEDULED):
            return reverse('campaigns:campaign_edit', kwargs={'pk': self.pk})
        return reverse('campaigns:campaign_detail', kwargs={'pk': self.pk})

    @property
    def email(self):
        if not self.__cached_email and self.campaign_type == Campaign.REGULAR:
            try:
                self.__cached_email, created = Email.objects.get_or_create(campaign=self)
            except Email.MultipleObjectsReturned:
                self.__cached_email = self.emails.order_by('id').first()
        return self.__cached_email


class Email(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name=_('campaign'), related_name='emails')
    from_email = models.EmailField(_('email address'))
    from_name = models.CharField(_('name'), max_length=100, blank=True)
    subject = models.CharField(_('subject'), max_length=150)
    preview = models.CharField(_('preview'), max_length=150, blank=True)
    content = models.TextField(_('content'))

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')

    def __str__(self):
        return self.subject

    def get_from(self):
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email
