from django.core import mail
from django.test import override_settings

from colossus.apps.campaigns.api import get_test_email_context
from colossus.apps.campaigns.constants import CampaignStatus
from colossus.apps.campaigns.tests.factories import (
    CampaignFactory, EmailFactory,
)
from colossus.apps.lists.models import MailingList
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity, Subscriber
from colossus.apps.subscribers.tests.factories import SubscriberFactory
from colossus.test.testcases import TestCase
from colossus.utils import get_absolute_url


class GetTestEmailContextTests(TestCase):
    def test_context_data(self):
        actual = get_test_email_context()
        expected = {
            'sub': '#',
            'unsub': '#',
            'name': '<< Test Name >>',
            'uuid': '[SUBSCRIBER_UUID]'
        }
        self.assertDictEqual(actual, expected)

    def test_context_data_override(self):
        expected = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
            'uuid': '4'
        }
        actual = get_test_email_context(**expected)
        self.assertDictEqual(actual, expected)

    def test_context_data_partial_override(self):
        data = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
        }
        actual = get_test_email_context(**data)
        expected = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
            'uuid': '[SUBSCRIBER_UUID]'
        }
        self.assertDictEqual(actual, expected)

    def test_context_data_inclusion(self):
        actual = get_test_email_context(TEST_INCLUSION_KEY='**TEST**')
        expected = {
            'sub': '#',
            'unsub': '#',
            'name': '<< Test Name >>',
            'uuid': '[SUBSCRIBER_UUID]',
            'TEST_INCLUSION_KEY': '**TEST**'
        }
        self.assertDictEqual(actual, expected)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SendCampaignTests(TestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list = MailingListFactory()
        self.subscribers = SubscriberFactory.create_batch(10, mailing_list=self.mailing_list)
        self.campaign = CampaignFactory(mailing_list=self.mailing_list, track_clicks=True, track_opens=True)
        self.email = EmailFactory(
            campaign=self.campaign,
            from_email='john@doe.com',
            from_name='John Doe',
            subject='Test email subject',
        )
        self.email.set_template_content()
        email_content = {
            'content': '<p>Hi there!</p><p>Test email body.</p><a href="https://google.com">google</a>'
        }
        self.email.set_blocks(email_content)
        self.email.save()
        self.campaign.send()

    def test_setup(self):
        self.assertEqual(MailingList.objects.count(), 1)
        self.assertEqual(self.mailing_list.subscribers.count(), 10)
        self.assertEqual(self.mailing_list.campaigns.count(), 1)
        self.assertEqual(self.campaign.emails.count(), 1)

    def test_campaign_status(self):
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, CampaignStatus.SENT)

    def test_subscribers_last_sent(self):
        for subscriber in self.subscribers:
            subscriber.refresh_from_db()
            with self.subTest(subscriber=subscriber):
                self.assertIsNotNone(subscriber.last_sent)

    def test_activity_sent_created(self):
        activities_count = Activity.objects.filter(activity_type=ActivityTypes.SENT).count()
        self.assertEqual(activities_count, 10)

    def test_emails_sent(self):
        self.assertEqual(len(mail.outbox), 10, 'Campaign must send 1 email for each subscriber.')

    def test_emails_contents(self):
        for email in mail.outbox:
            with self.subTest(email=email):
                self.assertEqual(email.subject, 'Test email subject')
                subscriber = Subscriber.objects.get(email=email.to[0])
                unsubscribe_url = get_absolute_url('subscribers:unsubscribe', {
                    'mailing_list_uuid': self.mailing_list.uuid,
                    'subscriber_uuid': subscriber.uuid,
                    'campaign_uuid': self.campaign.uuid
                })
                text_body = email.body
                html_body, mimetype = email.alternatives[0]
                self.assertIn(unsubscribe_url, text_body, 'Email plain text body must contain unsubscribe link.')
                self.assertIn('/track/click/', text_body, 'Email plain text body must contain track click links.')
                self.assertNotIn('/track/open/', text_body, 'Email plain text body must NOT contain track open pixel.')
                self.assertIn(unsubscribe_url, html_body, 'Email HTML body must contain unsubscribe link.')
                self.assertIn('/track/click/', html_body, 'Email HTML body must contain track click links.')
                self.assertIn('/track/open/', html_body, 'Email HTML body must contain track open pixel.')
