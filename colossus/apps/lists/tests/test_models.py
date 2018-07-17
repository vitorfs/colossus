from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.constants import Status
from colossus.apps.subscribers.tests.factories import SubscriberFactory
from colossus.test.testcases import TestCase

from .factories import MailingListFactory


class MailingListUpdateSubscribersCountTests(TestCase):
    def setUp(self):
        self.mailing_list = MailingListFactory()

    def test_update_subscribers_count_persistence(self):
        self.assertEqual(0, MailingList.objects.get(pk=self.mailing_list.pk).subscribers_count)
        SubscriberFactory(mailing_list=self.mailing_list, status=Status.SUBSCRIBED)
        self.mailing_list.update_subscribers_count()
        self.assertEqual(1, MailingList.objects.get(pk=self.mailing_list.pk).subscribers_count)

    def test_subscribed_count(self):
        SubscriberFactory(mailing_list=self.mailing_list, status=Status.SUBSCRIBED)
        self.assertEqual(1, self.mailing_list.update_subscribers_count())

    def test_subscribed_count_5_subscribers(self):
        SubscriberFactory.create_batch(5, mailing_list=self.mailing_list, status=Status.SUBSCRIBED)
        self.assertEqual(5, self.mailing_list.update_subscribers_count())

    def test_pending_count(self):
        SubscriberFactory(mailing_list=self.mailing_list, status=Status.PENDING)
        self.assertEqual(0, self.mailing_list.update_subscribers_count())

    def test_unsubscribed_count(self):
        SubscriberFactory(mailing_list=self.mailing_list, status=Status.UNSUBSCRIBED)
        self.assertEqual(0, self.mailing_list.update_subscribers_count())

    def test_cleaned_count(self):
        SubscriberFactory(mailing_list=self.mailing_list, status=Status.CLEANED)
        self.assertEqual(0, self.mailing_list.update_subscribers_count())


class MailingListUpdateOpenRateTests(TestCase):
    def setUp(self):
        self.mailing_list = MailingListFactory()
        SubscriberFactory(mailing_list=self.mailing_list, open_rate=1.0)
        SubscriberFactory(mailing_list=self.mailing_list, open_rate=0.0)

    def test_update_open_rate(self):
        self.assertEqual(0.5, self.mailing_list.update_open_rate())

    def test_persistence(self):
        self.mailing_list.update_open_rate()
        self.assertEqual(0.5, MailingList.objects.get(pk=self.mailing_list.pk).open_rate)

    def test_round_percentage(self):
        SubscriberFactory(mailing_list=self.mailing_list, open_rate=0.0)
        self.assertEqual(0.3333, self.mailing_list.update_open_rate())


class MailingListUpdateClickRateTests(TestCase):
    def setUp(self):
        self.mailing_list = MailingListFactory()
        SubscriberFactory(mailing_list=self.mailing_list, click_rate=1.0)
        SubscriberFactory(mailing_list=self.mailing_list, click_rate=0.0)

    def test_update_click_rate(self):
        self.assertEqual(0.5, self.mailing_list.update_click_rate())

    def test_persistence(self):
        self.mailing_list.update_click_rate()
        self.assertEqual(0.5, MailingList.objects.get(pk=self.mailing_list.pk).click_rate)

    def test_round_percentage(self):
        SubscriberFactory(mailing_list=self.mailing_list, click_rate=0.0)
        self.assertEqual(0.3333, self.mailing_list.update_click_rate())
