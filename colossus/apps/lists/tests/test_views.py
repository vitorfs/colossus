from django.urls import reverse

from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.tests.factories import (
    SubscriberFactory, TagFactory,
)
from colossus.test.testcases import AuthenticatedTestCase


class TagTestCase(AuthenticatedTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mailing_list = MailingListFactory()
        cls.tags = TagFactory.create_batch(2, mailing_list=cls.mailing_list)


class TagListViewTests(TagTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('lists:tags', kwargs={'pk': self.mailing_list.pk})
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_response_context(self):
        context = self.response.context
        self.assertEqual(2, len(context['tags']))

    def test_html_content(self):
        contents = list()

        for tag in self.tags:
            edit_url = reverse('lists:delete_tag', kwargs={'pk': tag.mailing_list.pk, 'tag_pk': tag.pk})
            delete_url = reverse('lists:delete_tag', kwargs={'pk': tag.mailing_list.pk, 'tag_pk': tag.pk})
            contents.append('href="{0}"'.format(edit_url))
            contents.append('href="{0}"'.format(delete_url))

        for content in contents:
            with self.subTest(content=content):
                self.assertContains(self.response, content)


class BulkTagSubscribersViewTests(TagTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('lists:bulk_tag', kwargs={'pk': self.mailing_list.pk})
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_response_context(self):
        context = self.response.context
        self.assertIn('form', context)


class BulkTagSubscribersViewSuccessTests(TagTestCase):
    def setUp(self):
        super().setUp()
        self.subscriber = SubscriberFactory(mailing_list=self.mailing_list, email='john@example.com')
        self.tag = self.tags[0]
        self.url = reverse('lists:bulk_tag', kwargs={'pk': self.mailing_list.pk})
        self.response = self.client.post(self.url, {
            'tag': self.tag.pk,
            'emails': self.subscriber.email
        })

    def test_redirection(self):
        """
        A successful form submission should redirect the user back to
        the tag listing view
        """
        url = reverse('lists:tags', kwargs={'pk': self.mailing_list.pk})
        self.assertRedirects(self.response, url)

    def test_subscriber_tag(self):
        self.assertTrue(self.subscriber.tags.filter(pk=self.tag.pk).exists())
