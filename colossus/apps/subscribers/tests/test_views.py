from django.urls import reverse

from colossus.apps.campaigns.tests.factories import EmailFactory
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory


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

    def test_email_open_count(self):
        self.email.refresh_from_db()
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(1, self.email.total_opens_count)
        self.assertEqual(1, Activity.objects.filter(activity_type=ActivityTypes.OPENED).count())

    def test_email_open_two_times_count(self):
        # Simulate open email again
        self.client.get(self.url)
        self.email.refresh_from_db()
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(2, self.email.total_opens_count)
        self.assertEqual(2, Activity.objects.filter(activity_type=ActivityTypes.OPENED).count())
