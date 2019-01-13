from django.urls import resolve, reverse

from colossus.apps.accounts import forms, views
from colossus.test.testcases import AuthenticatedTestCase, TestCase


class AccountsLoginRequiredTests(TestCase):
    """
    Test if all the urls from accounts' app are protected with login_required decorator
    Perform a GET request to all urls. The expected outcome is a redirection
    to the login page.
    """
    def test_redirection(self):
        patterns = [
            'password_change',
            'password_change_done',
            'profile'
        ]
        for url_name in patterns:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                response = self.client.get(url)
                self.assertRedirectsLoginRequired(response, url)


class ProfileViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        url = reverse('profile')
        self.response = self.client.get(url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves_correct_view(self):
        view = resolve('/accounts/profile/')
        self.assertEqual(view.func.view_class, views.ProfileView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, forms.UserForm)

    def test_html_content(self):
        contents = (
            ('<input type="hidden"', 1),
            ('<input type="text"', 2),
            ('<input type="email"', 1),
            ('<select', 1)
        )
        for content in contents:
            with self.subTest(content=content[0]):
                self.assertContains(self.response, content[0], content[1])


class ProfileViewSuccessTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('profile')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'timezone': 'UTC'
        }
        self.response = self.client.post(self.url, data)

    def test_created_campaign(self):
        self.user.refresh_from_db()
        self.assertEqual('John', self.user.first_name)
        self.assertEqual('Doe', self.user.last_name)
        self.assertEqual('john.doe@example.com', self.user.email)
        self.assertEqual('UTC', self.user.timezone)

    def test_redirection(self):
        self.assertRedirects(self.response, self.url)
