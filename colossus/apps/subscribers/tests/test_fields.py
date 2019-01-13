from django import forms

from colossus.apps.subscribers.fields import MultipleEmailField
from colossus.test.testcases import TestCase


class TestForm(forms.Form):
    emails = MultipleEmailField()


class MultipleEmailFieldTests(TestCase):
    def test_cleaned_data(self):
        form = TestForm(data={'emails': 'john@example.com'})
        form.full_clean()
        actual = list(form.cleaned_data['emails'])
        expected = ['john@example.com']
        self.assertEqual(actual, expected)

    def test_cleaned_data_multiple_emails(self):
        form = TestForm(data={'emails': 'john@example.com,alex@example.com'})
        form.full_clean()
        actual = list(form.cleaned_data['emails'])
        expected = ['john@example.com', 'alex@example.com']
        self.assertEqual(actual, expected)

    def test_cleaned_data_multiple_emails_new_line(self):
        form = TestForm(data={'emails': 'john@example.com\nalex@example.com'})
        form.full_clean()
        actual = list(form.cleaned_data['emails'])
        expected = ['john@example.com', 'alex@example.com']
        self.assertEqual(actual, expected)

    def test_cleaned_data_multiple_emails_new_line_and_commas(self):
        form = TestForm(data={'emails': 'john@example.com\nalex@example.com,maria@example.com'})
        form.full_clean()
        actual = list(form.cleaned_data['emails'])
        expected = ['john@example.com', 'alex@example.com', 'maria@example.com']
        self.assertEqual(actual, expected)

    def test_invalid_emails(self):
        form = TestForm(data={'emails': 'xxxx'})
        self.assertFalse(form.is_valid())

    def test_mixed_valid_and_invalid_emails(self):
        form = TestForm(data={'emails': 'john@example.com,xxxx'})
        self.assertFalse(form.is_valid())

    def test_valid_emails(self):
        form = TestForm(data={'emails': 'john@example.com'})
        self.assertTrue(form.is_valid())

    def test_valid_emails_multiple(self):
        form = TestForm(data={'emails': 'john@example.com,alex@example.com'})
        self.assertTrue(form.is_valid())

    def test_normalize_emails(self):
        form = TestForm(data={'emails': 'JOHN@EXAMPLE.COM,ALEX@EXAMPLE.COM'})
        form.full_clean()
        actual = list(form.cleaned_data['emails'])
        expected = ['JOHN@example.com', 'ALEX@example.com']
        self.assertEqual(actual, expected)
