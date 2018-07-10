import factory

from colossus.apps.campaigns import models


class CampaignFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'campaign_{n}')

    class Meta:
        model = models.Campaign


class EmailFactory(factory.DjangoModelFactory):
    campaign = factory.SubFactory(CampaignFactory)

    class Meta:
        model = models.Email


class LinkFactory(factory.DjangoModelFactory):
    url = 'https://simpleisbetterthancomplex.com'
    email = factory.SubFactory(EmailFactory)

    class Meta:
        model = models.Link
