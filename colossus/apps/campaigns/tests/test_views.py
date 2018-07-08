from django.urls import reverse

from colossus.test.factories import UserFactory
from colossus.test.testcases import TestCase

from .factories import CampaignFactory


class CampaignListViewSuccessTests(TestCase):
    def setUp(self):
        self.campaigns = CampaignFactory.create_batch(5)
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
