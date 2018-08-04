import factory

from colossus.apps.templates.models import EmailTemplate


class EmailTemplateFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'campaign_{n}')

    class Meta:
        model = EmailTemplate
