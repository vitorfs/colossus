import json

from django.http import JsonResponse
from django.urls import reverse

from colossus.apps.accounts.models import User
from colossus.apps.notifications.models import Notification
from colossus.apps.notifications.tests.factories import NotificationFactory
from colossus.test.testcases import AuthenticatedTestCase, TestCase


class NotificationsLoginRequiredTests(TestCase):
    """
    Test if all the urls from notifications' app are protected with
    login_required decorator.
    Perform a GET request to all urls. The expected outcome is a redirection
    to the login page.
    """
    def test_redirection(self):
        patterns = [
            ('notifications', None),
            ('notification_detail', {'pk': 1}),
            ('unread', None),
        ]
        for url_name, kwargs in patterns:
            with self.subTest(url_name=url_name):
                url = reverse(f'notifications:{url_name}', kwargs=kwargs)
                response = self.client.get(url)
                self.assertRedirectsLoginRequired(response, url)


class NotificationListViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        NotificationFactory()
        NotificationFactory.create_batch(5, is_seen=False, user=self.user)
        self.response = self.client.get(reverse('notifications:notifications'))

    def test_setup(self):
        self.assertEqual(6, Notification.objects.count())

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_context(self):
        self.assertIn('notifications', self.response.context)

    def test_notifications_list(self):
        notifications = self.response.context['notifications']
        self.assertEqual(5, len(notifications))

    def test_updated_is_seen_status(self):
        count = self.user.notifications.filter(is_seen=True).count()
        self.assertEqual(5, count)


class NotificationDetailViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.notification = NotificationFactory(user=self.user, is_read=False)
        url = reverse('notifications:notification_detail', kwargs={'pk': self.notification.pk})
        self.response = self.client.get(url)

    def test_setup(self):
        self.assertEqual(1, self.user.notifications.count())

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_context(self):
        self.assertIn('notification', self.response.context)

    def test_updated_is_read_status(self):
        count = self.user.notifications.filter(is_read=True).count()
        self.assertEqual(1, count)


class NotificationDetailViewReadTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        NotificationFactory(user=self.user, is_read=False)
        notification = NotificationFactory(user=self.user, is_read=True)
        url = reverse('notifications:notification_detail', kwargs={'pk': notification.pk})
        self.response = self.client.get(url)

    def test_setup(self):
        self.assertEqual(2, Notification.objects.count())

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_is_read_status(self):
        count = self.user.notifications.filter(is_read=True).count()
        self.assertEqual(1, count)


class NotificationDetailViewAccessTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.notification = NotificationFactory()
        url = reverse('notifications:notification_detail', kwargs={'pk': self.notification.pk})
        self.response = self.client.get(url)

    def test_setup(self):
        self.assertEqual(1, Notification.objects.count())
        self.assertEqual(2, User.objects.count())
        self.assertNotEqual(self.user.pk, self.notification.user.pk)

    def test_status_code(self):
        self.assertEqual(404, self.response.status_code)


class UnreadViewTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        NotificationFactory()  # Add notification belonging to other user
        self.notification = NotificationFactory(user=self.user, is_seen=False)
        url = reverse('notifications:unread')
        self.response = self.client.get(url)

    def test_setup(self):
        self.assertEqual(2, Notification.objects.count())
        self.assertEqual(1, self.user.notifications.count())

    def test_status_code(self):
        self.assertEqual(200, self.response.status_code)

    def test_response_class(self):
        self.assertIsInstance(self.response, JsonResponse)

    def test_response_data(self):
        data = json.loads(self.response.content)
        self.assertIn('html', data)

    def test_updated_is_seen_status(self):
        count = self.user.notifications.filter(is_seen=True).count()
        self.assertEqual(1, count)
