import sys

from django.core.management import BaseCommand

from colossus.apps.subscribers.models import Subscriber
from colossus.utils import get_location


class Command(BaseCommand):
    help = 'Update subscriber location information based on confirm IP address ' \
           'field or last seen IP address, if available.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all', action='store_true',
            help='Force update all subscribers information. By default it only update those with location = None.',
        )

    def handle(self, *args, **options):
        all = options['all']

        queryset = Subscriber.objects.exclude(confirm_ip_address=None)

        if not all:
            queryset = queryset.filter(location=None)

        updated = 0

        for subscriber in queryset:
            ip_address = subscriber.last_seen_ip_address
            if ip_address is None:
                ip_address = subscriber.confirm_ip_address
            location = get_location(ip_address)
            if location is not None:
                subscriber.location = location
                subscriber.save(update_fields=['location'])
                if updated % 100 == 0:
                    sys.stdout.write('\n')
                sys.stdout.write('.')
                sys.stdout.flush()
                updated += 1

        if updated > 0:
            self.stdout.write(
                self.style.SUCCESS('\nSuccessfully updated location for %s subscribers.' % updated)
            )
        else:
            self.stdout.write(
                self.style.WARNING('Could not find any new information. Nothing changed.')
            )
