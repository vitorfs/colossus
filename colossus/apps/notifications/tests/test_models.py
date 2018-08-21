from colossus.apps.notifications.tests.factories import NotificationFactory
from colossus.test.testcases import TestCase


class NotificationModelTests(TestCase):
    def setUp(self):
        self.notification = NotificationFactory(text='test text')

    def test_to_string(self):
        self.assertEqual('test text', str(self.notification))
