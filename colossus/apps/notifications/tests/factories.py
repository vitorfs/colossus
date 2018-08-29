import factory

from colossus.apps.accounts.tests.factories import UserFactory
from colossus.apps.lists.tests.factories import MailingListFactory
from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification


class NotificationFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    action = Actions.IMPORT_COMPLETED
    text = '{"mailing_list_id": 999, "created": 0, "updated": 0, "ignored": 0}'

    class Meta:
        model = Notification

    @factory.post_generation
    def create_mailing_list(self, create, extracted, **kwargs):
        if not create:
            return
        return MailingListFactory(id=999, name='Test List')
