from colossus.apps.campaigns.tests.factories import (
    CampaignFactory, EmailFactory, LinkFactory,
)
from colossus.apps.subscribers.activities import render_activity
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.tests.factories import ActivityFactory
from colossus.test.testcases import TestCase


class RenderActivityTests(TestCase):
    def setUp(self):
        self.campaign = CampaignFactory()
        self.email = EmailFactory(campaign=self.campaign)
        self.link = LinkFactory(email=self.email)

    def test_render_activity_without_renderer(self):
        """
        Test if the render_activity function is handling all keys in the ActivityTypes
        If a new key is added to ActivityTypes and the render_activity is not aware, this test
        will fail by raise an KeyError exception.
        """
        for activity_type in ActivityTypes.LABELS.keys():
            with self.subTest(activity_type=activity_type):
                activity = ActivityFactory(activity_type=activity_type, email=self.email, link=self.link)
                activity.activity_type = activity_type
                self.assertNotEqual('', render_activity(activity))
