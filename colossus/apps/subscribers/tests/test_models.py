from django.test import RequestFactory
from django.urls import reverse

from colossus.apps.campaigns.tests.factories import EmailFactory
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory


class SubscriberTestCase(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.factory = RequestFactory()


class SubscriberOpenEmailTests(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.email = EmailFactory()
        url = reverse('subscribers:open', kwargs={
            'email_uuid': self.email.uuid,
            'subscriber_uuid': self.subscriber.uuid
        })
        factory = RequestFactory()
        self.request = factory.get(url)

    def test_open_email_once(self):
        self.subscriber.open(self.request, self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(1, self.email.campaign.unique_opens_count)
        self.assertEqual(1, self.email.campaign.total_opens_count)
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(1, self.email.total_opens_count)
        self.assertEqual(1, Activity.objects.filter(activity_type=ActivityTypes.OPENED).count())

    def test_open_email_twice(self):
        pass
