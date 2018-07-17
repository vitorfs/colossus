from django.test import RequestFactory
from django.urls import reverse

from colossus.apps.campaigns.tests.factories import EmailFactory, LinkFactory
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory


class SubscriberTestCase(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.factory = RequestFactory()


class SubscriberOpenEmailTests(TestCase):
    def setUp(self):
        factory = RequestFactory()
        self.email = EmailFactory()
        self.subscriber_1 = SubscriberFactory()
        self.request_1 = factory.get(reverse('subscribers:open', kwargs={
            'email_uuid': self.email.uuid,
            'subscriber_uuid': self.subscriber_1.uuid
        }))
        self.subscriber_2 = SubscriberFactory()
        self.request_2 = factory.get(reverse('subscribers:open', kwargs={
            'email_uuid': self.email.uuid,
            'subscriber_uuid': self.subscriber_2.uuid
        }))

    def test_open_email_once(self):
        self.subscriber_1.open(self.request_1, self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(1, self.email.campaign.unique_opens_count)
        self.assertEqual(1, self.email.campaign.total_opens_count)
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(1, self.email.total_opens_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_open_email_twice(self):
        self.subscriber_1.open(self.request_1, self.email)
        self.subscriber_1.open(self.request_1, self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(1, self.email.campaign.unique_opens_count)
        self.assertEqual(2, self.email.campaign.total_opens_count)
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(2, self.email.total_opens_count)
        self.assertEqual(2, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_two_subscribers_open_email_once(self):
        self.subscriber_1.open(self.request_1, self.email)
        self.subscriber_2.open(self.request_2, self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(2, self.email.campaign.unique_opens_count)
        self.assertEqual(2, self.email.campaign.total_opens_count)
        self.assertEqual(2, self.email.unique_opens_count)
        self.assertEqual(2, self.email.total_opens_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())
        self.assertEqual(1, self.subscriber_2.activities.filter(activity_type=ActivityTypes.OPENED).count())


class SubscriberClickLinkTests(TestCase):
    def setUp(self):
        factory = RequestFactory()
        self.link = LinkFactory()
        self.subscriber_1 = SubscriberFactory()
        self.request_1 = factory.get(reverse('subscribers:click', kwargs={
            'link_uuid': self.link.uuid,
            'subscriber_uuid': self.subscriber_1.uuid
        }))
        self.subscriber_2 = SubscriberFactory()
        self.request_2 = factory.get(reverse('subscribers:click', kwargs={
            'link_uuid': self.link.uuid,
            'subscriber_uuid': self.subscriber_2.uuid
        }))

    def test_click_link_once(self):
        self.subscriber_1.click(self.request_1, self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(1, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(1, self.link.total_clicks_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())

    def test_click_link_twice(self):
        self.subscriber_1.click(self.request_1, self.link)
        self.subscriber_1.click(self.request_1, self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(2, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())

    def test_two_subscribers_click_link_once(self):
        self.subscriber_1.click(self.request_1, self.link)
        self.subscriber_2.click(self.request_2, self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(2, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(2, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())
        self.assertEqual(1, self.subscriber_2.activities.filter(activity_type=ActivityTypes.CLICKED).count())
