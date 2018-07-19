from django.test import override_settings
from django.urls import reverse

from colossus.apps.campaigns.tests.factories import EmailFactory, LinkFactory
from colossus.apps.subscribers.constants import ActivityTypes
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
