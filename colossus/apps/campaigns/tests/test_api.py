from colossus.apps.campaigns.api import get_test_email_context
from colossus.test.testcases import TestCase


class GetTestEmailContextTests(TestCase):
    def test_context_data(self):
        actual = get_test_email_context()
        expected = {
            'sub': '#',
            'unsub': '#',
            'name': '<< Test Name >>',
            'uuid': '[SUBSCRIBER_UUID]'
        }
        self.assertDictEqual(actual, expected)

    def test_context_data_override(self):
        expected = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
            'uuid': '4'
        }
        actual = get_test_email_context(**expected)
        self.assertDictEqual(actual, expected)

    def test_context_data_partial_override(self):
        data = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
        }
        actual = get_test_email_context(**data)
        expected = {
            'sub': '1',
            'unsub': '2',
            'name': '3',
            'uuid': '[SUBSCRIBER_UUID]'
        }
        self.assertDictEqual(actual, expected)

    def test_context_data_inclusion(self):
        actual = get_test_email_context(TEST_INCLUSION_KEY='**TEST**')
        expected = {
            'sub': '#',
            'unsub': '#',
            'name': '<< Test Name >>',
            'uuid': '[SUBSCRIBER_UUID]',
            'TEST_INCLUSION_KEY': '**TEST**'
        }
        self.assertDictEqual(actual, expected)


class SendCampaignEmailTests(TestCase):
    pass
