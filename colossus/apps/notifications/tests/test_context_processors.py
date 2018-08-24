from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from colossus.apps.accounts.tests.factories import UserFactory
from colossus.apps.notifications.context_processors import notifications
from colossus.apps.notifications.models import Notification
from colossus.apps.notifications.tests.factories import NotificationFactory
from colossus.test.testcases import TestCase


class NotificationsContextProcessorTests(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.user = UserFactory()
        self.request.user = self.user
        self.notification = NotificationFactory(user=self.user)

    def test_success(self):
        context = notifications(self.request)
        self.assertIn('notifications_count', context)
        self.assertEqual(1, context['notifications_count'])

    def test_seen_filter(self):
        NotificationFactory(user=self.user, is_seen=True)
        context = notifications(self.request)
        self.assertEqual(2, Notification.objects.count())
        self.assertEqual(1, context['notifications_count'])

    def test_user_not_authenticated(self):
        self.request.user = AnonymousUser()
        context = notifications(self.request)
        self.assertNotIn('notifications_count', context)

    def test_context_processor_enabled(self):
        self.client.login(username=self.user.username, password='123')
        response = self.client.get(reverse('dashboard'))
        self.assertIn('notifications_count', response.context)
        self.assertEqual(1, response.context['notifications_count'])
