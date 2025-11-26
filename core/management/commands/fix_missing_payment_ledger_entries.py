from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Deprecated command. Use `python manage.py rebuild_ledger` instead.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--university-id',
            type=int,
            help='Ignored. Present for backwards compatibility.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ignored. Present for backwards compatibility.',
        )

    def handle(self, *args, **options):
        raise CommandError(
            "fix_missing_payment_ledger_entries is no longer available. "
            "Run `python manage.py rebuild_ledger` to regenerate append-only ledger lines."
        )

