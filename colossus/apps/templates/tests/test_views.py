from typing import List

from django.urls import reverse

from colossus.apps.accounts.models import User
from colossus.apps.accounts.tests.factories import UserFactory
from colossus.apps.templates.models import EmailTemplate
from colossus.apps.templates.tests.factories import EmailTemplateFactory
from colossus.test.testcases import TestCase


class EmailTemplateTestCase(TestCase):
    def setUp(self):
        self.templates: List[EmailTemplate] = EmailTemplateFactory.create_batch(5)
        self.user: User = UserFactory(username='alex')
        self.client.login(username='alex', password='123')


class EmailTemplateListViewTests(EmailTemplateTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('templates:emailtemplates')
        self.response = self.client.get(self.url)

    def test_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_response_context(self):
        context = self.response.context
        self.assertIn('templates', context)
        self.assertEqual('templates', context['menu'])
        # The count should be 6 because an initial template is always created
        # automatically by a Signal, after the EmailTemplate table is created.
        self.assertEqual(6, context['total_count'])

    def test_html_content(self):
        contents = map(lambda t: t.name, self.templates)
        for content in contents:
            with self.subTest(content=content):
                self.assertContains(self.response, content)
