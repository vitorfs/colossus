from django.urls import reverse

from colossus.test import ColossusTestCase


class CampaignListViewLoginRequired(ColossusTestCase):
    def setUp(self):
        self.url = reverse('campaigns:campaigns')
        self.response = self.client.get(self.url)

    def test_redirection(self):
        self.assertRedirectsLoginRequired(self.response, self.url)
