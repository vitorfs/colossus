from django.core import mail
from django.test import override_settings
from django.urls import reverse

from colossus.apps.campaigns.tests.factories import EmailFactory, LinkFactory
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.constants import ActivityTypes, Status
from colossus.apps.subscribers.forms import UnsubscribeForm
from colossus.apps.subscribers.models import Activity
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TrackOpenTests(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.email = EmailFactory()
        self.url = reverse('subscribers:open', kwargs={
            'email_uuid': self.email.uuid,
            'subscriber_uuid': self.subscriber.uuid
        })
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response['Content-Type'], 'image/png')

    def test_subscriber_opened_email(self):
        self.assertTrue(Activity.objects.filter(activity_type=ActivityTypes.OPENED).exists())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TrackClickTests(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.link = LinkFactory()
        self.url = reverse('subscribers:click', kwargs={
            'link_uuid': self.link.uuid,
            'subscriber_uuid': self.subscriber.uuid
        })
        self.response = self.client.get(self.url)

    def test_redirection(self):
        self.assertRedirects(self.response, self.link.url, fetch_redirect_response=False)

    def test_subscriber_clicked_link(self):
        self.assertTrue(Activity.objects.filter(activity_type=ActivityTypes.CLICKED).exists())


@override_settings(RATELIMIT_ENABLE=False)
class TestPostUnsubscribeManualSuccessful(TestCase):
    def setUp(self):
        super().setUp()
        self.subscriber = SubscriberFactory(status=Status.SUBSCRIBED)
        self.url = reverse('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': self.subscriber.mailing_list.uuid
        })
        self.response = self.client.post(self.url, data={
            'email': self.subscriber.email
        })
        self.subscriber.refresh_from_db()

    def test_unsubscribed(self):
        self.assertEqual(self.subscriber.status, Status.UNSUBSCRIBED)

    def test_goodbye_email_sent(self):
        """
        Test if the goodbye email is sent.
        The goodbye email should be sent even if it's disabled for cases where
        the unsubscription came from the manual unsubscribe.
        """
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual([self.subscriber.email], email.to)
        self.assertEqual('You are now unsubscribed', email.subject)

    def test_redirect(self):
        url = reverse('subscribers:goodbye', kwargs={
            'mailing_list_uuid': self.subscriber.mailing_list.uuid
        })
        self.assertRedirects(self.response, url)


@override_settings(RATELIMIT_ENABLE=False)
class TestPostUnsubscribeManualInvalid(TestCase):
    def setUp(self):
        super().setUp()
        self.subscriber = SubscriberFactory(status=Status.SUBSCRIBED)
        url = reverse('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': self.subscriber.mailing_list.uuid
        })
        self.response = self.client.post(url, data={})

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_no_email_sent(self):
        self.assertEqual(len(mail.outbox), 0)


@override_settings(RATELIMIT_ENABLE=False)
class TestGetUnsubscribeManual(TestCase):
    def setUp(self):
        super().setUp()
        mailing_list = MailingListFactory()
        url = reverse('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': mailing_list.uuid
        })
        self.response = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, UnsubscribeForm)

    def test_form_inputs(self):
        self.assertContains(self.response, '<input', 2)
        self.assertContains(self.response, 'type="email"', 1)
        self.assertContains(self.response, 'type="submit"', 1)


@override_settings(RATELIMIT_ENABLE=False)
class TestGetUnsubscribeManualCustomTemplate(TestCase):
    def setUp(self):
        super().setUp()
        mailing_list = MailingListFactory()
        url = reverse('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': mailing_list.uuid
        })
        form_template = mailing_list.get_unsubscribe_form_template()
        form_template.content_html = '__customtemplate__'
        form_template.save()
        self.response = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_custom_template(self):
        self.assertContains(self.response, '__customtemplate__')
