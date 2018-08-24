from django.test import TestCase as DjangoTestCase
from django.urls import reverse

from colossus.apps.accounts.tests.factories import UserFactory


class TestCase(DjangoTestCase):
    def assertRedirectsLoginRequired(self, response, url, status_code=302,
                                     target_status_code=200, msg_prefix='',
                                     fetch_redirect_response=True):
        login_url = reverse('login')
        next_url = f'{login_url}?next={url}'
        return self.assertRedirects(response, next_url, status_code, target_status_code, msg_prefix,
                                    fetch_redirect_response)


class AuthenticatedTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='123')
