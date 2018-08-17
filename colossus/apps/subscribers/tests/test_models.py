from django.core import mail
from django.test import override_settings

from colossus.apps.campaigns.tests.factories import EmailFactory, LinkFactory
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.constants import ActivityTypes, TemplateKeys
from colossus.apps.subscribers.exceptions import FormTemplateIsNotEmail
from colossus.apps.subscribers.models import Subscriber
from colossus.apps.subscribers.subscription_settings import (
    SUBSCRIPTION_FORM_TEMPLATE_SETTINGS,
)
from colossus.test.testcases import TestCase

from .factories import SubscriberFactory, SubscriptionFormTemplateFactory


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


class SubscriptionFormTemplateTests(TestCase):
    def setUp(self):
        super().setUp()
        mailing_list = MailingListFactory(name='Test List')
        self.form_template = SubscriptionFormTemplateFactory(key=TemplateKeys.SUBSCRIBE_FORM,
                                                             mailing_list=mailing_list)

    def test_str(self):
        self.assertEqual('Subscribe form', str(self.form_template))

    def test_settings(self):
        settings = SUBSCRIPTION_FORM_TEMPLATE_SETTINGS['subscribe']
        self.assertEqual(self.form_template.settings, settings)

    def test_is_email(self):
        self.assertFalse(self.form_template.is_email)

    def test_get_default_content(self):
        html = self.form_template.get_default_content()
        self.assertHTMLEqual(html, '<h5 class="card-title">Subscribe to our mailing list</h5>')

    def test_get_default_subject_failure(self):
        with self.assertRaises(FormTemplateIsNotEmail):
            self.form_template.get_default_subject()

    def test_get_default_subject(self):
        self.form_template.key = TemplateKeys.WELCOME_EMAIL
        self.assertEqual(self.form_template.get_default_subject(), 'Subscription Confirmed')

    def test_get_from_email(self):
        self.form_template.from_email = 'john@doe.com'
        self.assertEqual(self.form_template.get_from_email(), 'john@doe.com')

    def test_get_from_email_with_name(self):
        self.form_template.from_name = 'John Doe'
        self.form_template.from_email = 'john@doe.com'
        self.assertEqual(self.form_template.get_from_email(), 'John Doe <john@doe.com>')

    def test_render_template_subscribe_form(self):
        self.form_template.load_defaults()
        html = self.form_template.render_template()
        self.assertIn('Test List', html)
        self.assertIn('Subscribe to our mailing list', html)
        self.assertIn('<form', html)
        self.assertIn('Subscribe to list', html)


class SubscriptionFormTemplateLoadDefaultsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list = MailingListFactory(
            campaign_default_from_name='Jonh Doe',
            campaign_default_from_email='john@doe.com'
        )

    def test_load_defaults_email(self):
        form_template = SubscriptionFormTemplateFactory(
            key=TemplateKeys.WELCOME_EMAIL,
            mailing_list=self.mailing_list,
            content_html='test_content',
            redirect_url='test_url',
            send_email=True,
            subject='test_subject',
            from_name='test_name',
            from_email='test@from_email.com',
        )
        form_template.load_defaults()
        self.assertHTMLEqual(form_template.content_html,
                             '<div>Your subscription to our list has been confirmed.</div>')
        self.assertEqual(form_template.subject, 'Subscription Confirmed')
        self.assertEqual(form_template.redirect_url, '')
        self.assertFalse(form_template.send_email)
        self.assertEqual(form_template.from_name, 'Jonh Doe')
        self.assertEqual(form_template.from_email, 'john@doe.com')

    def test_load_defaults(self):
        form_template = SubscriptionFormTemplateFactory(
            key=TemplateKeys.SUBSCRIBE_FORM,
            mailing_list=self.mailing_list,
            content_html='test_content',
            redirect_url='test_url',
            send_email=True,
            subject='test_subject',
            from_name='test_name',
            from_email='test@from_email.com',
        )
        form_template.load_defaults()
        self.assertHTMLEqual(form_template.content_html, '<h5 class="card-title">Subscribe to our mailing list</h5>')
        self.assertEqual(form_template.subject, '')
        self.assertEqual(form_template.redirect_url, '')
        self.assertFalse(form_template.send_email)
        self.assertEqual(form_template.from_name, '')
        self.assertEqual(form_template.from_email, '')


class SubscriptionFormTemplateConfirmEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list = MailingListFactory(
            name='Newsletter List',
            campaign_default_from_name='Jonh Doe',
            campaign_default_from_email='john@doe.com'
        )
        form_template = SubscriptionFormTemplateFactory(
            key=TemplateKeys.CONFIRM_EMAIL,
            mailing_list=self.mailing_list,
        )
        form_template.load_defaults()
        form_template.content_html = '__customcontent__'
        form_template.send('test@example.com', {'confirm_link': '__confirmlink__'})
        self.email = mail.outbox[0]

    def test_email_sent(self):
        self.assertEqual(len(mail.outbox), 1)

    def test_email_subject(self):
        self.assertEqual('Please Confirm Subscription', self.email.subject)

    def test_confirm_link_in_email_body(self):
        self.assertIn('__confirmlink__', self.email.body)

    def test_list_name_in_email_body(self):
        self.assertIn('Newsletter List', self.email.body)

    def test_custom_content_in_email_body(self):
        self.assertIn('__customcontent__', self.email.body)

    def test_email_to(self):
        self.assertEqual(['test@example.com', ], self.email.to)

    def test_email_from(self):
        self.assertEqual('Jonh Doe <john@doe.com>', self.email.from_email)


class SubscriptionFormTemplateWelcomeEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list = MailingListFactory(
            campaign_default_from_name='Jonh Doe',
            campaign_default_from_email='john@doe.com',
            contact_email_address='maria@example.com'
        )
        form_template = SubscriptionFormTemplateFactory(
            key=TemplateKeys.WELCOME_EMAIL,
            mailing_list=self.mailing_list,
        )
        form_template.load_defaults()
        form_template.content_html = '__customcontent__'
        form_template.send('test@example.com')
        self.email = mail.outbox[0]

    def test_email_sent(self):
        self.assertEqual(len(mail.outbox), 1)

    def test_email_subject(self):
        self.assertEqual('Subscription Confirmed', self.email.subject)

    def test_custom_content_in_email_body(self):
        self.assertIn('__customcontent__', self.email.body)

    def test_contact_email_in_email_body(self):
        self.assertIn('maria@example.com', self.email.body)

    def test_unsubscribe_link_in_email_body(self):
        self.assertIn('/unsubscribe/%s/' % self.mailing_list.uuid, self.email.body)

    def test_email_to(self):
        self.assertEqual(['test@example.com', ], self.email.to)

    def test_email_from(self):
        self.assertEqual('Jonh Doe <john@doe.com>', self.email.from_email)


class SubscriptionFormTemplateGoodbyeEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list = MailingListFactory(
            name='***Test List***',
            campaign_default_from_name='Jonh Doe',
            campaign_default_from_email='john@doe.com',
            contact_email_address='maria@example.com'
        )
        form_template = SubscriptionFormTemplateFactory(
            key=TemplateKeys.GOODBYE_EMAIL,
            mailing_list=self.mailing_list,
        )
        form_template.load_defaults()
        form_template.content_html = '__customcontent__'
        form_template.send('test@example.com')
        self.email = mail.outbox[0]

    def test_email_sent(self):
        self.assertEqual(len(mail.outbox), 1)

    def test_email_subject(self):
        self.assertEqual('You are now unsubscribed', self.email.subject)

    def test_custom_content_in_email_body(self):
        self.assertIn('__customcontent__', self.email.body)

    def test_contact_email_in_email_body(self):
        self.assertIn('maria@example.com', self.email.body)

    def test_subscribe_link_in_email_body(self):
        self.assertIn('/subscribe/%s/' % self.mailing_list.uuid, self.email.body)

    def test_list_name_in_email_body(self):
        self.assertIn('***Test List***', self.email.body)

    def test_email_to(self):
        self.assertEqual(['test@example.com', ], self.email.to)

    def test_email_from(self):
        self.assertEqual('Jonh Doe <john@doe.com>', self.email.from_email)
