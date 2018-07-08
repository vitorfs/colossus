from django.test import TestCase
from django.urls import reverse


class ColossusTestCase(TestCase):

    def assertRedirectsLoginRequired(self, response, url, status_code=302,
                                     target_status_code=200, msg_prefix='',
                                     fetch_redirect_response=True):
        login_url = reverse('accounts:login')
        next_url = f'{login_url}?next={url}'
        return self.assertRedirects(response, next_url, status_code, target_status_code, msg_prefix,
                                    fetch_redirect_response)
