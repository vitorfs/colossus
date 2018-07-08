import factory

from colossus.apps.campaigns.models import Campaign


class CampaignFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'campaign_{n}')

    class Meta:
        model = Campaign
