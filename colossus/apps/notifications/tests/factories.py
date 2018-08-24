import factory

from colossus.apps.accounts.tests.factories import UserFactory
from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification


class NotificationFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    action = Actions.IMPORT_COMPLETED

    class Meta:
        model = Notification
