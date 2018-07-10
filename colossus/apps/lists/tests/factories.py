import factory

from colossus.apps.lists.models import MailingList


class MailingListFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'mailing_list_{n}')
    slug = factory.Sequence(lambda n: f'mailing-list-{n}')

    class Meta:
        model = MailingList
        django_get_or_create = ('name',)
