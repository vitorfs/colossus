from django.urls import reverse

from colossus.apps.accounts.tests.factories import UserFactory
from colossus.apps.campaigns.models import Campaign
from colossus.test.testcases import TestCase

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


class CampaignListViewSuccessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        CampaignFactory.create_batch(5)

    def setUp(self):
        self.campaigns = Campaign.objects.all()
        self.user = UserFactory(username='alex')
        self.client.login(username='alex', password='123')
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
