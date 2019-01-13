from colossus.apps.campaigns.forms import CreateCampaignForm
from colossus.apps.campaigns.models import Campaign
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.tests.factories import TagFactory
from colossus.test.testcases import TestCase


class CreateCampaignFormTests(TestCase):
    def setUp(self):
        self.mailing_list_1 = MailingListFactory(name='list_1')
        self.tag_1 = TagFactory(name='tag_1', mailing_list=self.mailing_list_1)
        self.mailing_list_2 = MailingListFactory(name='list_2')
        self.tag_2 = TagFactory(name='tag_2', mailing_list=self.mailing_list_2)

    def test_campaign_creation(self):
        form = CreateCampaignForm({'name': 'Test campaign'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(Campaign.objects.filter(name='Test campaign').exists())

    def test_form_validation(self):
        form = CreateCampaignForm()
        self.assertFalse(form.is_valid())

    def test_campaign_with_list_and_tag(self):
        form = CreateCampaignForm({
            'name': 'Test campaign',
            'mailing_list': self.mailing_list_1.pk,
            'tag': self.tag_1.pk
        })
        self.assertTrue(form.is_valid())
        campaign = form.save()
        self.assertEqual('Test campaign', campaign.name)
        self.assertEqual('list_1', campaign.mailing_list.name)
        self.assertEqual('tag_1', campaign.tag.name)

    def test_campaign_with_list_and_invalid_tag(self):
        """
        The tag should belong to the mailing list
        """
        form = CreateCampaignForm({
            'name': 'Test campaign',
            'mailing_list': self.mailing_list_1.pk,
            'tag': self.tag_2.pk
        })
        self.assertTrue(form.is_valid())
        campaign = form.save()
        self.assertEqual('Test campaign', campaign.name)
        self.assertEqual('list_1', campaign.mailing_list.name)
        self.assertIsNone(campaign.tag)

    def test_campaign_with_tag_and_without_list(self):
        """
        To include a tag the campaign should have a mailing list associated with
        so we can validate if the tag belong to the mailing list
        """
        form = CreateCampaignForm({
            'name': 'Test campaign',
            'mailing_list': '',
            'tag': self.tag_1.pk
        })
        self.assertTrue(form.is_valid())
        campaign = form.save()
        self.assertEqual('Test campaign', campaign.name)
        self.assertIsNone(campaign.mailing_list)
        self.assertIsNone(campaign.tag)
