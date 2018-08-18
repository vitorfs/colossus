import uuid

from django.contrib.sites.models import Site
from django.test import override_settings

from colossus.test.testcases import TestCase
from colossus.utils import get_absolute_url


class TestGetAbsoluteURL(TestCase):
    def setUp(self):
        Site.objects.update(domain='example.com')
        Site.objects.clear_cache()
        self.uuid = str(uuid.uuid4())

    def test_get_aboluste_url_http(self):
        url = get_absolute_url('subscribers:subscribe', kwargs={
            'mailing_list_uuid': self.uuid
        })
        self.assertEqual(url, 'http://example.com/subscribe/%s/' % self.uuid)

    @override_settings(COLOSSUS_HTTPS_ONLY=True)
    def test_get_aboluste_url_https(self):
        url = get_absolute_url('subscribers:subscribe', kwargs={
            'mailing_list_uuid': self.uuid
        })
        self.assertEqual(url, 'https://example.com/subscribe/%s/' % self.uuid)

    def test_get_aboluste_url_site_domain(self):
        Site.objects.update(domain='mysite.com')
        Site.objects.clear_cache()
        url = get_absolute_url('login')
        self.assertEqual(url, 'http://mysite.com/accounts/login/')
