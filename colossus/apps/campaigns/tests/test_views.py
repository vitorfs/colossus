from django.urls import reverse

from colossus.apps.campaigns.models import Campaign
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.tests.factories import TagFactory
from colossus.test.testcases import AuthenticatedTestCase, TestCase

from .factories import CampaignFactory


class CampaignsLoginRequiredTests(TestCase):
    """
    Test if all the urls from campaign's app are protected with login_required decorator
    Perform a GET request to all urls. The expected outcome is a redirection
    to the login page.
    """
    def test_redirection(self):
        patterns = [
            ('campaigns', None),
            ('campaign_add', None),
            ('campaign_detail', {'pk': 1}),
            ('campaign_preview', {'pk': 1}),
            ('campaign_edit', {'pk': 1}),
            ('campaign_edit_recipients', {'pk': 1}),
            ('campaign_edit_from', {'pk': 1}),
            ('campaign_edit_subject', {'pk': 1}),
            ('campaign_edit_content', {'pk': 1}),
            ('campaign_edit_template', {'pk': 1}),
            ('campaign_test_email', {'pk': 1}),
            ('campaign_preview_email', {'pk': 1}),
            ('send_campaign', {'pk': 1}),
            ('send_campaign_complete', {'pk': 1}),
            ('replicate_campaign', {'pk': 1}),
            ('delete_campaign', {'pk': 1}),
            ('schedule_campaign', {'pk': 1}),
        ]
        for url_name, kwargs in patterns:
            with self.subTest(url_name=url_name):
                url = reverse(f'campaigns:{url_name}', kwargs=kwargs)
                response = self.client.get(url)
                self.assertRedirectsLoginRequired(response, url)


class CampaignListViewSuccessTests(AuthenticatedTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        CampaignFactory.create_batch(5)

    def setUp(self):
        super().setUp()
        self.campaigns = Campaign.objects.all()
        self.url = reverse('campaigns:campaigns')
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_response_context(self):
        context = self.response.context
        self.assertEqual('campaigns', context['menu'])
        self.assertEqual(5, context['total_count'])

    def test_html_content(self):
        contents = map(lambda c: c.name, self.campaigns)
        for content in contents:
            with self.subTest(content=content):
                self.assertContains(self.response, content)


class CampaignCreateViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.mailing_list_1 = MailingListFactory(name='list_1')
        self.tag_1 = TagFactory(name='tag_1', mailing_list=self.mailing_list_1)
        self.url = reverse('campaigns:campaign_add')

    def test_initial_data(self):
        url = '{0}?mailing_list={1}&tag={2}'.format(self.url, self.mailing_list_1.pk, self.tag_1.pk)
        response = self.client.get(url)
        form = response.context['form']
        self.assertEqual(form.initial['mailing_list'], self.mailing_list_1.pk)
        self.assertEqual(form.initial['tag'], self.tag_1.pk)

    def test_invalid_initial_data(self):
        url = '{0}?mailing_list=xxx&tag=yyyy'.format(self.url)
        response = self.client.get(url)
        form = response.context['form']
        self.assertEqual(form.initial, {})

    def test_html(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<input type="hidden"', 3)  # csrf_token, mailing_list, tag
        self.assertContains(response, '<input type="text"', 1)  # name tag


class TestCampaignEditRecipientsViewNoneMailingList(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.campaign = CampaignFactory(mailing_list=None)
        self.url = reverse('campaigns:campaign_edit_recipients', kwargs={'pk': self.campaign.pk})
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)
