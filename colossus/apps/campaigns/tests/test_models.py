from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from colossus.apps.campaigns import models
from colossus.apps.campaigns.constants import CampaignStatus
from colossus.apps.campaigns.models import Campaign
from colossus.apps.templates.tests.factories import EmailTemplateFactory
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
        scheduled_url = reverse('campaigns:campaign_scheduled', kwargs={'pk': 1})
        detail_url = reverse('campaigns:campaign_detail', kwargs={'pk': 1})
        cases = (
            (CampaignStatus.SENT, detail_url),
            (CampaignStatus.SCHEDULED, scheduled_url),
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
            (CampaignStatus.SCHEDULED, False),
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
        email_template_content = (
            '<!doctype html>'
            '<html>'
            '<body>'
            '{% block content %}'
            '{% endblock %}'
            '{% block footer %}'
            '<div><br></div>'
            '<div><small><a href="{{ unsub }}">Unsubscribe from this list</a>.</small></div>'
            '{% endblock %}'
            '</body>'
            '</html>'
        )
        email_template = EmailTemplateFactory(content=email_template_content)
        self.email = factories.EmailFactory(template=email_template)
        self.email.set_template_content()
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
            ('https://www.amazon.com/gp/product/198302998X/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=9325&amp;creativeASIN=198302998X&amp;linkCode=as2&amp;tag=vitorfs0b-20&amp;linkId=89931be04c94a3fd8c785b96746dd224', '<a href="%s">REST APIs with Django: Build powerful web APIs with Python and Django</a>'),  # noqa
            ('https://simpleisbetterthancomplex.com', '<a href="%s">https://simpleisbetterthancomplex.com</a>')
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

    def test_enable_click_tracking(self):
        blocks = self.email.get_blocks()
        content = (
            '<div>Hello! this is a test email!</div>'
            '<div>With links <a href="http://website.com">Website</a></div>'
            '<div>Go to this website:&nbsp;<a href="https://simpleisbetterthancomplex.com">'
            'https://simpleisbetterthancomplex.com</a></div>'
            '<div>&nbsp;</div>'
            '<div>With links <a href="http://website.com">Website</a></div>'
            '<div>&nbsp;</div>'
            '<div>Or maybe go to <a href="https://google.com">Google</a>.</div>'
        )

        # Duplicate the content both in content block and footer block
        blocks['content'] = content
        blocks['footer'] = content

        self.email.set_blocks(blocks)
        self.email.enable_click_tracking()
        self.assertEqual(8, models.Link.objects.count())
        self.assertEqual(4, models.Link.objects.filter(url='http://website.com').count())
        self.assertEqual(2, models.Link.objects.filter(url='https://simpleisbetterthancomplex.com').count())
        self.assertEqual(2, models.Link.objects.filter(url='https://google.com').count())

        # Test if the index were created correctly when there are multiple blocks
        for index in range(8):
            with self.subTest(index=index):
                self.assertEqual(1, models.Link.objects.filter(index=index).count())


class TestEnableOpenTracking(TestCase):
    def test_valid_html_structure(self):
        email = factories.EmailFactory(template_content=(
            '<!doctype html>'
            '<html>'
            '<body>'
            '</body>'
            '</html>'
        ))
        email.enable_open_tracking()
        self.assertIn('<img', email.template_content)
        self.assertIn('/track/open/', email.template_content)

    def test_valid_html_structure_with_django_template_tags(self):
        email = factories.EmailFactory(template_content=(
            '<!doctype html>'
            '<html>'
            '<body>'
            '{% block content %}'
            '{% endblock %}'
            '{% block footer %}'
            '<div><br></div>'
            '<div><small><a href="{{ unsub }}">Unsubscribe from this list</a>.</small></div>'
            '{% endblock %}'
            '</body>'
            '</html>'
        ))
        email.enable_open_tracking()
        self.assertIn('<img', email.template_content, 1)
        self.assertIn('/track/open/', email.template_content)
        self.assertIn("{% endblock %}<img ", email.template_content)
        self.assertIn('"/></body>', email.template_content)

    def test_invalid_html_structure(self):
        email = factories.EmailFactory(template_content='')
        email.enable_open_tracking()
        self.assertIn('<img', email.template_content)
        self.assertIn('/track/open/', email.template_content)

    def test_invalid_html_structure_django_template_tags(self):
        email = factories.EmailFactory(template_content=(
            'Free text header'
            '{% block content %}'
            '{% endblock %}'
            'Some text'
            '{% block footer %}'
            '<div><br></div>'
            '<div><small><a href="{{ unsub }}">Unsubscribe from this list</a>.</small></div>'
            '{% endblock %}'
        ))
        email.enable_open_tracking()
        self.assertIn('<img', email.template_content)
        self.assertIn('/track/open/', email.template_content)
