import factory

from colossus.apps.accounts.models import User


class UserFactory(factory.DjangoModelFactory):
    """
    User's Factory class. It uses the built-in method `django.contrib.auth.get_user_model` to get User model.
    Default password is: 123
    """
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@colossusmail.com')
    password = factory.PostGenerationMethodCall('set_password', '123')

    class Meta:
        model = User
        django_get_or_create = ('username',)
