from django.urls import resolve, reverse

from colossus.apps.core import views
from colossus.test.testcases import AuthenticatedTestCase, TestCase


class CoreLoginRequiredTests(TestCase):
    """
    Test if all the urls from core's app are protected with login_required decorator
    Perform a GET request to all urls. The expected outcome is a redirection to the login page.
    """
    def test_redirection(self):
        patterns = [
            'dashboard',
            'settings',
        ]
        for url_name in patterns:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                response = self.client.get(url)
                self.assertRedirectsLoginRequired(response, url)


class DashboardViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('dashboard')
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve('/')
        self.assertEqual(view.func, views.dashboard)

    def test_response_context(self):
        context = self.response.context
        self.assertEqual('dashboard', context['menu'])
