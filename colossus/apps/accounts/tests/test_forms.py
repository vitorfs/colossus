from colossus.apps.accounts.forms import AdminUserCreationForm, UserForm
from colossus.apps.accounts.tests.factories import UserFactory
from colossus.test.testcases import TestCase


class AdminUserCreationFormTests(TestCase):
    def test_create_admin(self):
        form = AdminUserCreationForm(data={
            'username': 'john',
            'email': 'john.doe@example.com',
            'password1': 'xxxxx*123',
            'password2': 'xxxxx*123'
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


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
