from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import LedgerLine, Payment, OEMPayment, Expense
from core.services import LedgerService


class Command(BaseCommand):
    help = 'Rebuild ledger_lines from historical payments, OEM payments, and expenses.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview how many ledger lines would be recreated without touching the database.',
        )
        parser.add_argument(
            '--truncate-only',
            action='store_true',
            help='Clear existing ledger lines without replaying historical data.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        truncate_only = options['truncate_only']

        if dry_run and truncate_only:
            self.stdout.write(self.style.WARNING('Running in dry-run mode. Ledger will not be truncated.'))

        if LedgerLine.objects.exists():
            msg = f"About to {'simulate ' if dry_run else ''}truncate {LedgerLine.objects.count()} ledger lines."
            self.stdout.write(self.style.WARNING(msg))

        if not dry_run:
            with transaction.atomic():
                LedgerLine.objects.all().delete()

        if truncate_only:
            self.stdout.write(self.style.SUCCESS('Ledger truncation complete.' if not dry_run else 'Dry run complete.'))
            return

        totals = {
            'payments': 0,
            'oem_payments': 0,
            'expenses': 0,
        }

        totals['payments'] = self._replay_queryset(
            Payment.objects.order_by('payment_date', 'created_at').select_related('invoice__billing'),
            LedgerService.build_payment_effect,
            dry_run,
            label='payments',
        )

        totals['oem_payments'] = self._replay_queryset(
            OEMPayment.objects.order_by('payment_date', 'created_at').select_related('invoice__billing'),
            LedgerService.build_oem_payment_effect,
            dry_run,
            label='OEM payments',
        )

        totals['expenses'] = self._replay_queryset(
            Expense.objects.order_by('incurred_date', 'created_at').select_related('university'),
            LedgerService.build_expense_effect,
            dry_run,
            label='expenses',
        )

        total_lines = sum(totals.values())
        summary_msg = (
            f"Rebuild {'simulated' if dry_run else 'finished'}: "
            f"{totals['payments']} payment lines, "
            f"{totals['oem_payments']} OEM payment lines, "
            f"{totals['expenses']} expense lines."
        )
        self.stdout.write(self.style.SUCCESS(summary_msg))
        self.stdout.write(self.style.SUCCESS(f"Total ledger lines {'to be created' if dry_run else 'created'}: {total_lines}"))

    def _replay_queryset(self, queryset, effect_builder, dry_run, label):
        created = 0
        count = queryset.count()
        if count == 0:
            self.stdout.write(f"No {label} found to replay.")
            return created

        self.stdout.write(f"Processing {count} {label}...")

        for obj in queryset.iterator():
            effect = effect_builder(obj)
            if not effect or not effect.entries:
                continue

            if dry_run:
                created += len(effect.entries)
            else:
                created += len(LedgerService.record_effect(effect))

        return created

