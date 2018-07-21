from django.utils import timezone

import factory

from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.models import Activity, Subscriber


class SubscriberFactory(factory.DjangoModelFactory):
    email = factory.Sequence(lambda n: f'subscriber_{n}@colossusmail.com')
    mailing_list = factory.SubFactory(MailingListFactory)

    class Meta:
        model = Subscriber
        django_get_or_create = ('email',)


class ActivityFactory(factory.DjangoModelFactory):
    date = timezone.now()
    ip_address = '127.0.0.1'
    subscriber = factory.SubFactory(SubscriberFactory)

    class Meta:
        model = Activity
