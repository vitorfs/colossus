from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'colossus.apps.accounts'

    def ready(self):
        try:
            import colossus.apps.accounts.signals  # noqa F401
        except ImportError:
            pass
