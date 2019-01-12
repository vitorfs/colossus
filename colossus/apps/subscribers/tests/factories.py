from django.utils import timezone

import factory

from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.constants import Status, TemplateKeys
from colossus.apps.subscribers.models import (
    Activity, Domain, Subscriber, SubscriptionFormTemplate, Tag,
)


class DomainFactory(factory.DjangoModelFactory):
    name = '@colossusmail.com'

    class Meta:
        model = Domain
        django_get_or_create = ('name',)


class SubscriberFactory(factory.DjangoModelFactory):
    email = factory.Sequence(lambda n: f'subscriber_{n}@colossusmail.com')
    domain = factory.SubFactory(DomainFactory)
    mailing_list = factory.SubFactory(MailingListFactory)
    status = Status.SUBSCRIBED
    last_sent = timezone.now()

    class Meta:
        model = Subscriber
        django_get_or_create = ('email',)


class ActivityFactory(factory.DjangoModelFactory):
    date = timezone.now()
    ip_address = '127.0.0.1'
    subscriber = factory.SubFactory(SubscriberFactory)

    class Meta:
        model = Activity


class SubscriptionFormTemplateFactory(factory.DjangoModelFactory):
    key = TemplateKeys.SUBSCRIBE_FORM
    mailing_list = factory.SubFactory(MailingListFactory)

    class Meta:
        model = SubscriptionFormTemplate
        django_get_or_create = ('key',)


class TagFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'tag_{n}')
    mailing_list = factory.SubFactory(MailingListFactory)

    class Meta:
        model = Tag
        django_get_or_create = ('name',)
