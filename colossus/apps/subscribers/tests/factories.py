import factory

from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.subscribers.models import Subscriber


class SubscriberFactory(factory.DjangoModelFactory):
    email = factory.Sequence(lambda n: f'subscriber_{n}@colossusmail.com')
    mailing_list = factory.SubFactory(MailingListFactory)

    class Meta:
        model = Subscriber
