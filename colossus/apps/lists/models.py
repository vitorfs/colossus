import csv
import json
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from colossus.apps.lists.constants import ImportStatus, ImportStrategies
from colossus.apps.subscribers.constants import Status, TemplateKeys
from colossus.storage import PrivateMediaStorage

User = get_user_model()


class MailingList(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('list short URL'), max_length=100, unique=True)
    subscribers_count = models.PositiveIntegerField(_('subscribers'), default=0)
    open_rate = models.FloatField(_('opens'), default=0.0)
    click_rate = models.FloatField(_('clicks'), default=0.0)
    date_created = models.DateTimeField(_('created'), auto_now_add=True)
    contact_email_address = models.EmailField(_('contact email address'), blank=True)
    website_url = models.URLField(_('website URL'), blank=True, help_text=_('Where did people opt in to this list?'))
    campaign_default_from_name = models.CharField(_('default from name'), max_length=100, blank=True)
    campaign_default_from_email = models.EmailField(_('default from email address'), blank=True)
    campaign_default_email_subject = models.CharField(_('default subject'), max_length=150, blank=True)
    enable_recaptcha = models.BooleanField(_('enable reCAPTCHA'), default=False)
    recaptcha_site_key = models.CharField(_('site key'), max_length=100, blank=True)
    recaptcha_secret_key = models.CharField(_('secret key'), max_length=100, blank=True)
    list_manager = models.EmailField(
        _('list manager'),
        blank=True,
        help_text=_('Email address to handle subscribe/unsubscribe requests.'
                    'It can be a real email address or an automated route to handle callbacks/webhooks.')
    )

    smtp_host = models.CharField(_('host'), max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(_('port'), blank=True, null=True)
    smtp_username = models.CharField(_('username'), max_length=200, blank=True)
    smtp_password = models.CharField(_('password'), max_length=200, blank=True)
    smtp_use_tls = models.BooleanField(_('use TLS'), default=True)
    smtp_use_ssl = models.BooleanField(_('use SSL'), default=False)
    smtp_timeout = models.PositiveIntegerField(_('timeout'), blank=True, null=True)
    smtp_ssl_keyfile = models.TextField(_('SSL keyfile'), blank=True)
    smtp_ssl_certfile = models.TextField(_('SSL certfile'), blank=True)

    forms_custom_css = models.TextField(
        _('custom CSS'),
        help_text=_('Custom CSS will be applied to all subscription form pages.'),
        blank=True
    )
    forms_custom_header = models.TextField(
        _('custom header'),
        help_text=_('Header displayed on all subscription form pages. Accepts HTML.'
                    'If empty, the name of the mailing list will be used.'),
        blank=True
    )

    class Meta:
        verbose_name = _('list')
        verbose_name_plural = _('lists')
        db_table = 'colossus_mailing_lists'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mailing:subscribers', kwargs={'pk': self.pk})

    def get_active_subscribers(self):
        return self.subscribers.filter(status=Status.SUBSCRIBED)

    def update_subscribers_count(self) -> int:
        self.subscribers_count = self.get_active_subscribers().count()
        self.save(update_fields=['subscribers_count'])
        return self.subscribers_count

    def update_click_rate(self) -> float:
        qs = self.get_active_subscribers() \
            .exclude(last_sent=None) \
            .aggregate(Avg('click_rate'))
        self.click_rate = round(qs.get('click_rate__avg', 0.9), 4)
        self.save(update_fields=['click_rate'])
        return self.click_rate

    def update_open_rate(self) -> float:
        qs = self.get_active_subscribers() \
            .exclude(last_sent=None) \
            .aggregate(Avg('open_rate'))
        self.open_rate = round(qs.get('open_rate__avg', 0.0), 4)
        self.save(update_fields=['open_rate'])
        return self.open_rate

    def update_open_and_click_rate(self):
        qs = self.get_active_subscribers() \
            .exclude(last_sent=None) \
            .aggregate(
            open=Avg('open_rate'),
            click=Avg('click_rate')
        )
        self.open_rate = round(qs.get('open', 0.0), 4)
        self.click_rate = round(qs.get('click', 0.0), 4)
        self.save(update_fields=['open_rate', 'click_rate'])

    def _get_form_template(self, form_template_key: str):
        form_template, created = self.forms_templates.get_or_create(key=form_template_key)
        if created:
            form_template.load_defaults()
        return form_template

    def get_subscribe_form_template(self):
        return self._get_form_template(TemplateKeys.SUBSCRIBE_FORM)

    def get_subscribe_thank_you_page_template(self):
        return self._get_form_template(TemplateKeys.SUBSCRIBE_THANK_YOU_PAGE)

    def get_confirm_email_template(self):
        return self._get_form_template(TemplateKeys.CONFIRM_EMAIL)

    def get_confirm_thank_you_page_template(self):
        return self._get_form_template(TemplateKeys.CONFIRM_THANK_YOU_PAGE)

    def get_welcome_email_template(self):
        return self._get_form_template(TemplateKeys.WELCOME_EMAIL)

    def get_unsubscribe_form_template(self):
        return self._get_form_template(TemplateKeys.UNSUBSCRIBE_FORM)

    def get_unsubscribe_success_page_template(self):
        return self._get_form_template(TemplateKeys.UNSUBSCRIBE_SUCCESS_PAGE)

    def get_goodbye_email_template(self):
        return self._get_form_template(TemplateKeys.GOODBYE_EMAIL)


class SubscriberImport(models.Model):
    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        related_name='subscribers_imports',
        verbose_name=_('mailing list')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='subscribers_imports',
        verbose_name=_('user')
    )
    upload_date = models.DateTimeField(_('upload date'), auto_now_add=True)
    file = models.FileField(
        _('CSV file'),
        upload_to='uploads',
        storage=PrivateMediaStorage()
    )
    columns_mapping = models.TextField(_('columns mapping'), blank=True)
    subscriber_status = models.PositiveSmallIntegerField(
        _('assign status to subscriber'),
        default=Status.SUBSCRIBED,
        choices=Status.CHOICES
    )
    status = models.PositiveSmallIntegerField(
        _('status'),
        default=ImportStatus.PENDING,
        choices=ImportStatus.CHOICES
    )
    size = models.PositiveIntegerField(_('size'), default=0)
    strategy = models.PositiveSmallIntegerField(
        _('import strategy'),
        choices=ImportStrategies.CHOICES,
        default=ImportStrategies.UPDATE_OR_CREATE,
        help_text=_('The email address will be used as the main subscriber identifier to determine if they are '
                    'already on the list.')
    )

    __cached_headings = None

    class Meta:
        verbose_name = _('subscribers import')
        verbose_name_plural = _('subscribers imports')
        db_table = 'colossus_subscribers_imports'

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)
        self.file.delete(save=False)

    def set_columns_mapping(self, columns_mapping):
        self.columns_mapping = json.dumps(columns_mapping)

    def get_columns_mapping(self):
        try:
            columns_mapping = json.loads(self.columns_mapping)
        except (TypeError, json.JSONDecodeError):
            columns_mapping = dict()
        return {int(key): value for key, value in columns_mapping.items()}

    def get_headings(self):
        if self.__cached_headings is None:
            with open(self.file.path, 'r') as csvfile:
                reader = csv.reader(csvfile)
                csv_headings = next(reader)
                self.__cached_headings = csv_headings
        return self.__cached_headings

    def get_str_headings(self):
        return ', '.join(self.get_headings())

    def get_rows(self, limit=None):
        rows = list()
        with open(self.file.path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            # skip header
            next(reader)
            for index, row in enumerate(reader):
                if index == limit:
                    break
                rows.append(row)
        return rows

    def get_preview(self):
        return self.get_rows(limit=10)

    def set_size(self, save=True):
        with open(self.file.path, 'r') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            self.size = sum(1 for row in reader)
        if save:
            self.save(update_fields=['size'])
