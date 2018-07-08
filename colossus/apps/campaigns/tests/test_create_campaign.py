from django.urls import resolve, reverse

from colossus.apps.campaigns import forms, models, views
from colossus.test.testcases import AuthenticatedTestCase


class CreateCampaignViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        url = reverse('campaigns:campaign_add')
        self.response = self.client.get(url)

    def test_success_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_url_resolves_correct_view(self):
        view = resolve('/campaigns/add/')
        self.assertEqual(view.func.view_class, views.CampaignCreateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, forms.CreateCampaignForm)


class CreateCampaignValidPostDataTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        url = reverse('campaigns:campaign_add')
        data = {
            'name': 'Email Campaign'
        }
        self.response = self.client.post(url, data)

    def test_created_campaign(self):
        self.assertTrue(models.Campaign.objects.exists())

    def test_redirection(self):
        campaign = models.Campaign.objects.get()
        url = reverse('campaigns:campaign_edit', kwargs={'pk': campaign.pk})
        self.assertRedirects(self.response, url)


class CreateCampaignInvalidPostDataTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        url = reverse('campaigns:campaign_add')
        data = {}
        self.response = self.client.post(url, data)

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_campaign_not_created(self):
        self.assertFalse(models.Campaign.objects.exists())
