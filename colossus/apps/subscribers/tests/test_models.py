from django.test import override_settings

from colossus.apps.campaigns.tests.factories import EmailFactory, LinkFactory
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Subscriber
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SubscriberOpenEmailTests(TestCase):
    def setUp(self):
        mailing_list = MailingListFactory()
        self.email = EmailFactory()
        self.subscriber_1 = SubscriberFactory(mailing_list=mailing_list)
        self.subscriber_1.create_activity(ActivityTypes.SENT, email=self.email)  # mock email sent activity
        self.subscriber_2 = SubscriberFactory(mailing_list=mailing_list)
        self.subscriber_2.create_activity(ActivityTypes.SENT, email=self.email)  # mock email sent activity

    def test_open_rate_updated(self):
        self.assertEqual(0.0, self.subscriber_1.open_rate)
        self.subscriber_1.open(self.email)
        self.subscriber_1.refresh_from_db()
        self.subscriber_1.mailing_list.refresh_from_db()
        self.assertEqual(1.0, self.subscriber_1.open_rate)
        # two subscribers, one with open_rate = 1.0 other with open_rate = 0.0, expected mailing list open_rate = 0.5
        self.assertEqual(0.5, self.subscriber_1.mailing_list.open_rate)

    def test_open_email_once(self):
        self.subscriber_1.open(self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(1, self.email.campaign.unique_opens_count)
        self.assertEqual(1, self.email.campaign.total_opens_count)
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(1, self.email.total_opens_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_open_email_twice(self):
        self.subscriber_1.open(self.email)
        self.subscriber_1.open(self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(1, self.email.campaign.unique_opens_count)
        self.assertEqual(2, self.email.campaign.total_opens_count)
        self.assertEqual(1, self.email.unique_opens_count)
        self.assertEqual(2, self.email.total_opens_count)
        self.assertEqual(2, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_two_subscribers_open_email_once(self):
        self.subscriber_1.open(self.email)
        self.subscriber_2.open(self.email)
        self.email.refresh_from_db()
        self.email.campaign.refresh_from_db()
        self.assertEqual(2, self.email.campaign.unique_opens_count)
        self.assertEqual(2, self.email.campaign.total_opens_count)
        self.assertEqual(2, self.email.unique_opens_count)
        self.assertEqual(2, self.email.total_opens_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.OPENED).count())
        self.assertEqual(1, self.subscriber_2.activities.filter(activity_type=ActivityTypes.OPENED).count())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SubscriberClickLinkTests(TestCase):
    def setUp(self):
        mailing_list = MailingListFactory()
        self.link = LinkFactory()
        self.subscriber_1 = SubscriberFactory(mailing_list=mailing_list)
        self.subscriber_1.create_activity(ActivityTypes.SENT, email=self.link.email)  # mock email sent activity
        self.subscriber_2 = SubscriberFactory(mailing_list=mailing_list)
        self.subscriber_2.create_activity(ActivityTypes.SENT, email=self.link.email)  # mock email sent activity

    def test_click_rate_update(self):
        self.assertEqual(0.0, self.subscriber_1.click_rate)
        self.subscriber_1.click(self.link)
        self.subscriber_1.refresh_from_db()
        self.subscriber_1.mailing_list.refresh_from_db()
        self.assertEqual(1.0, self.subscriber_1.click_rate)
        # two subscribers, one with click_rate = 1.0 other with click_rate = 0.0 expected mailing list click_rate = 0.5
        self.assertEqual(0.5, self.subscriber_1.mailing_list.click_rate)

    def test_click_link_once(self):
        self.subscriber_1.click(self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(1, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(1, self.link.total_clicks_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())

    def test_click_link_twice(self):
        self.subscriber_1.click(self.link)
        self.subscriber_1.click(self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(2, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())

    def test_two_subscribers_click_link_once(self):
        self.subscriber_1.click(self.link)
        self.subscriber_2.click(self.link)
        self.link.refresh_from_db()
        self.link.email.campaign.refresh_from_db()
        self.assertEqual(2, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(2, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(1, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())
        self.assertEqual(1, self.subscriber_2.activities.filter(activity_type=ActivityTypes.CLICKED).count())

    def test_click_two_links_same_email(self):
        link_2 = LinkFactory(email=self.link.email)
        self.subscriber_1.click(self.link)
        self.subscriber_1.click(link_2)

        self.link.refresh_from_db()
        link_2.refresh_from_db()
        self.link.email.campaign.refresh_from_db()

        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)

        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(1, self.link.total_clicks_count)
        self.assertEqual(1, link_2.unique_clicks_count)
        self.assertEqual(1, link_2.total_clicks_count)

        self.assertEqual(2, self.subscriber_1.activities.filter(activity_type=ActivityTypes.CLICKED).count())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SubscriberClickLinkForceOpenTests(TestCase):
    def setUp(self):
        mailing_list = MailingListFactory()
        self.link = LinkFactory()
        self.subscriber = SubscriberFactory(mailing_list=mailing_list)
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.link.email)  # mock email sent activity

    def test_click_without_open(self):
        """
        Test clicking on a link without opening the email first
        The `click` method should enforce the email opening
        """
        self.subscriber.click(self.link)

        # refresh models
        self.link.refresh_from_db()
        self.link.email.refresh_from_db()
        self.link.email.campaign.refresh_from_db()

        # checks for click counts
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(1, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(1, self.link.total_clicks_count)
        self.assertEqual(1, self.subscriber.activities.filter(activity_type=ActivityTypes.CLICKED).count())

        # checks for open counts
        self.assertEqual(1, self.link.email.campaign.unique_opens_count)
        self.assertEqual(1, self.link.email.campaign.total_opens_count)
        self.assertEqual(1, self.link.email.unique_opens_count)
        self.assertEqual(1, self.link.email.total_opens_count)
        self.assertEqual(1, self.subscriber.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_click_twice_without_open(self):
        """
        Test clicking on a link twice without opening the email first
        Only the first `click` method should trigger the email opening

        """
        self.subscriber.click(self.link)  # trigger `open` method
        self.subscriber.click(self.link)  # this time it should not trigger the `open` method

        # refresh models
        self.link.refresh_from_db()
        self.link.email.refresh_from_db()
        self.link.email.campaign.refresh_from_db()

        # checks for click counts
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(2, self.subscriber.activities.filter(activity_type=ActivityTypes.CLICKED).count())

        # checks for open counts
        self.assertEqual(1, self.link.email.campaign.unique_opens_count)
        self.assertEqual(1, self.link.email.campaign.total_opens_count)
        self.assertEqual(1, self.link.email.unique_opens_count)
        self.assertEqual(1, self.link.email.total_opens_count)
        self.assertEqual(1, self.subscriber.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_open_once_click_twice(self):
        """
        Test opening email and clicking on a link twice
        """
        self.subscriber.click(self.link)
        self.subscriber.open(self.link.email)
        self.subscriber.click(self.link)

        # refresh models
        self.link.refresh_from_db()
        self.link.email.refresh_from_db()
        self.link.email.campaign.refresh_from_db()

        # checks for click counts
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(2, self.subscriber.activities.filter(activity_type=ActivityTypes.CLICKED).count())

        # checks for open counts
        self.assertEqual(1, self.link.email.campaign.unique_opens_count)
        self.assertEqual(2, self.link.email.campaign.total_opens_count)
        self.assertEqual(1, self.link.email.unique_opens_count)
        self.assertEqual(2, self.link.email.total_opens_count)
        self.assertEqual(2, self.subscriber.activities.filter(activity_type=ActivityTypes.OPENED).count())

    def test_open_twice_click_twice(self):
        """
        Test opening email and clicking on a link twice
        """
        self.subscriber.open(self.link.email)
        self.subscriber.click(self.link)
        self.subscriber.open(self.link.email)
        self.subscriber.click(self.link)

        # refresh models
        self.link.refresh_from_db()
        self.link.email.refresh_from_db()
        self.link.email.campaign.refresh_from_db()

        # checks for click counts
        self.assertEqual(1, self.link.email.campaign.unique_clicks_count)
        self.assertEqual(2, self.link.email.campaign.total_clicks_count)
        self.assertEqual(1, self.link.unique_clicks_count)
        self.assertEqual(2, self.link.total_clicks_count)
        self.assertEqual(2, self.subscriber.activities.filter(activity_type=ActivityTypes.CLICKED).count())

        # checks for open counts
        self.assertEqual(1, self.link.email.campaign.unique_opens_count)
        self.assertEqual(2, self.link.email.campaign.total_opens_count)
        self.assertEqual(1, self.link.email.unique_opens_count)
        self.assertEqual(2, self.link.email.total_opens_count)
        self.assertEqual(2, self.subscriber.activities.filter(activity_type=ActivityTypes.OPENED).count())


class SubscriberUpdateOpenRateTests(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.email = EmailFactory()

    def test_open_rate_persistence(self):
        self.assertEqual(0.0, Subscriber.objects.get(pk=self.subscriber.pk).open_rate)
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.subscriber.update_open_rate()
        self.assertEqual(1.0, Subscriber.objects.get(pk=self.subscriber.pk).open_rate)

    def test_division_by_zero(self):
        """
        Test if the the code is handling division by zero.
        There should never be an OPENED activity without a SENT activity (thus not being possible to have a
        division by zero). But just in case.
        """
        self.assertEqual(0.0, self.subscriber.update_open_rate())

    def test_update_open_rate_distinct_count(self):
        """
        Test if the update count is only considering distinct open entries
        """
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.assertEqual(1.0, self.subscriber.update_open_rate())

    def test_open_without_sent(self):
        """
        Test open count without sent activity
        This should not happen under normal circumstances
        """
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.assertEqual(0.0, self.subscriber.update_open_rate())

    def test_sent_without_open(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.assertEqual(0.0, self.subscriber.update_open_rate())

    def test_update_open_rate_50_percent(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.assertEqual(0.5, self.subscriber.update_open_rate())

    def test_round_percentage(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.OPENED, email=self.email)
        self.assertEqual(0.3333, self.subscriber.update_open_rate())


class SubscriberUpdateClickRateTests(TestCase):
    def setUp(self):
        self.subscriber = SubscriberFactory()
        self.email = EmailFactory()
        self.link = LinkFactory(email=self.email)

    def test_click_rate_persistence(self):
        self.assertEqual(0.0, Subscriber.objects.get(pk=self.subscriber.pk).click_rate)
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.subscriber.update_click_rate()
        self.assertEqual(1.0, Subscriber.objects.get(pk=self.subscriber.pk).click_rate)

    def test_division_by_zero(self):
        """
        Test if the the code is handling division by zero.
        There should never be an OPENED activity without a SENT activity (thus not being possible to have a
        division by zero). But just in case.
        """
        self.assertEqual(0.0, self.subscriber.update_click_rate())

    def test_update_click_rate_distinct_count(self):
        """
        Test if the update count is only considering distinct open entries
        """
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.assertEqual(1.0, self.subscriber.update_click_rate())

    def test_open_without_sent(self):
        """
        Test open count without sent activity
        This should not happen under normal circumstances
        """
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.assertEqual(0.0, self.subscriber.update_click_rate())

    def test_sent_without_open(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.assertEqual(0.0, self.subscriber.update_click_rate())

    def test_update_click_rate_50_percent(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.assertEqual(0.5, self.subscriber.update_click_rate())

    def test_round_percentage(self):
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=EmailFactory())
        self.subscriber.create_activity(ActivityTypes.SENT, email=self.email)
        self.subscriber.create_activity(ActivityTypes.CLICKED, email=self.email, link=self.link)
        self.assertEqual(0.3333, self.subscriber.update_click_rate())
