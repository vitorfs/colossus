from colossus.apps.accounts.forms import UserForm
from colossus.apps.accounts.tests.factories import UserFactory
from colossus.test.testcases import TestCase


class UserFormTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'timezone': 'Europe/Helsinki'
        }

    def test_invalid_timezone(self):
        self.data['timezone'] = 'xxx'
        form = UserForm(instance=self.user, data=self.data)
        self.assertFalse(form.is_valid())

    def test_valid_timezone(self):
        form = UserForm(instance=self.user, data=self.data)
        self.assertTrue(form.is_valid())
