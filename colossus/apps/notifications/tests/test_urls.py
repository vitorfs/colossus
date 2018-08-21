from django.urls import resolve, reverse

from colossus.apps.notifications import views
from colossus.test.testcases import TestCase


class NotificationsURLSTests(TestCase):
    def test_notification_list_view_resolves(self):
        view = resolve('/notifications/')
        self.assertEqual(view.func.view_class, views.NotificationListView)

    def test_notification_list_view_reverse(self):
        url = reverse('notifications:notifications')
        self.assertEqual('/notifications/', url)

    def test_notification_detail_view_resolves(self):
        view = resolve('/notifications/1/')
        self.assertEqual(view.func.view_class, views.NotificationDetailView)

    def test_notification_detail_view_reverse(self):
        url = reverse('notifications:notification_detail', kwargs={'pk': 1})
        self.assertEqual('/notifications/1/', url)

    def test_unread_resolves(self):
        view = resolve('/notifications/unread/')
        self.assertEqual(view.func, views.unread)

    def test_unread_reverse(self):
        url = reverse('notifications:unread')
        self.assertEqual('/notifications/unread/', url)
