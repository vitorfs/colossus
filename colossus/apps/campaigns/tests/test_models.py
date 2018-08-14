from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from colossus.apps.campaigns import models
from colossus.apps.campaigns.constants import CampaignStatus
from colossus.apps.campaigns.models import Campaign
from colossus.test.testcases import TestCase

from . import factories


class TestCampaign(TestCase):
    def setUp(self):
        self.campaign = Campaign(id=1)

    def test_str(self):
        self.campaign.name = 'Test campaign'
        self.assertEqual(str(self.campaign), 'Test campaign')

    def test_get_absolute_url(self):
        edit_url = reverse('campaigns:campaign_edit', kwargs={'pk': 1})
        detail_url = reverse('campaigns:campaign_detail', kwargs={'pk': 1})
        cases = (
            (CampaignStatus.SENT, detail_url),
            (CampaignStatus.SCHEDULED, edit_url),
            (CampaignStatus.DRAFT, edit_url),
            (CampaignStatus.QUEUED, detail_url),
            (CampaignStatus.DELIVERING, detail_url),
            (CampaignStatus.PAUSED, detail_url),
        )
        for case in cases:
            self.campaign.status = case[0]
            with self.subTest(campaign_status=self.campaign.get_status_display()):
                self.assertEqual(self.campaign.get_absolute_url(), case[1])

    def test_can_edit(self):
        cases = (
            (CampaignStatus.SENT, False),
            (CampaignStatus.SCHEDULED, True),
            (CampaignStatus.DRAFT, True),
            (CampaignStatus.QUEUED, False),
            (CampaignStatus.DELIVERING, False),
            (CampaignStatus.PAUSED, False),
        )
        for case in cases:
            self.campaign.status = case[0]
            with self.subTest(campaign_status=self.campaign.get_status_display()):
                self.assertEqual(self.campaign.can_edit, case[1])


class TestEmailEnableClickTracking(TestCase):
    def setUp(self):
        self.email = factories.EmailFactory()
        self.current_site = get_current_site(request=None)

    def test_not_remove_unsub_markup(self):
        html = '<a href="{{unsub}}">Example Link</a>'
        click_tracking_html, index = self.email._enable_click_tracking(html)
        self.assertIn('{{unsub}}', click_tracking_html)
        self.assertEqual(0, models.Link.objects.count())

    def test_link_finder_regex_valid_links(self):
        """
        Test enable tracking for valid links
        After executing  the _enable_click_tracking method, the code should
        create a Link instance and parse the html switching the urls
        """
        valid_tags = [
            ('http://website1.com', '<a href=%s>Website 1</a>',),  # no " or '
            ('http://website2.com', '<a href="%s">Website 2</a>',),  # using "
            ('http://website3.com', '<a href=\'%s\'>Website 3</a>',),  # using '
            ('HTTP://WEBSITE4.COM', '<a href="%s">WEBSITE 4</a>',),  # all caps
            ('http://website5.com', '<A HREF="%s">Website 5</A>',),  # HREF caps
            ('https://website6.com', '<a href="%s">Website 6</a>',),  # https
            ('https://website7.co.uk', '<a href="%s">Website 7</a>',),  # other domain
            ('https://website8.co.uk:8080', '<a href="%s">Website 8</a>',),  # using port
            ('http://website9.com/some/path/to/some/file.pdf', '<a href="%s">Website 8</a>',),  # long path
            ('HTTPS://WEBSITE10.COM', '<a href="%s">WEBSITE 10</a>',),  # all caps https
            ('http://127.0.0.1', '<a href="%s">IP Address</a>'),  # IP Address
            ('http://0.0.0.0:4200', '<a href="%s">IP Address with port</a>'),  # IP Address with port
            ('https://www.amazon.com/gp/product/198302998X/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=9325&amp;creativeASIN=198302998X&amp;linkCode=as2&amp;tag=vitorfs0b-20&amp;linkId=89931be04c94a3fd8c785b96746dd224', '<a href="%s">REST APIs with Django: Build powerful web APIs with Python and Django</a>')  # noqa
        ]
        for tag in valid_tags:
            with self.subTest(tag=tag[0]):
                a_tag = tag[1] % tag[0]
                html, index = self.email._enable_click_tracking(a_tag)
                self.assertIn(f'://{self.current_site.domain}/track/click/', html)
                self.assertEqual(1, models.Link.objects.filter(url=tag[0]).count())

    def test_link_finder_regex_invalid_links(self):
        """
        Test enable tracking for invalid links
        After executing  the _enable_click_tracking method, the code should
        make no change to the html or create any Link
        """
        invalid_tags = [
            ('{{unsub}}', '<a href="%s">Unsubscribe from this list</a>',),
            ('ftp://somedomain.com/', '<a href="%s">Some ftp link</a>'),
            ('127.0.0.1:8000', '<a href="%s">no http</a>'),
            ('#', '<a href="%s">anchor</a>'),
            ('javascript:void(0);', '<a href="%s">js code</a>'),
            ('http://webiste.com', 'Lorem ipsum %s'),
        ]
        for tag in invalid_tags:
            with self.subTest(tag=tag[0]):
                a_tag = tag[1] % tag[0]
                html, index = self.email._enable_click_tracking(a_tag)
                self.assertEqual(a_tag, html)
                self.assertFalse(models.Link.objects.exists())

    def test_create_different_instances_for_repeated_link(self):
        html_input = '<a href="http://website.com">Website</a><a href="http://website.com">Website</a>'
        html_output, index = self.email._enable_click_tracking(html_input)
        created_links = models.Link.objects.all()
        self.assertEqual(2, created_links.count())
        self.assertEqual(2, index)
        for link in created_links:
            with self.subTest(index=link.index):
                self.assertIn(str(link.uuid), html_output)
